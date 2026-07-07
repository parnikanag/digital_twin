from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from database import get_db, init_db, User, SensorReading
from auth import hash_password, verify_password
from simulator import simulate_tick, ROOMS
from ml_models import predict_power, detect_anomaly, retrain
from notifications import check_and_notify, send_sms

# Shared in-memory appliance state (room -> appliance -> is_on)
_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Smart Home Energy API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


# ── Auth ──────────────────────────────────────────────────────────────────────
class AuthRequest(BaseModel):
    username: str
    password: str


@app.post("/signup")
def signup(req: AuthRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "Username already exists")
    db.add(User(username=req.username, password=hash_password(req.password)))
    db.commit()
    return {"message": "Account created successfully"}


@app.post("/login")
def login(req: AuthRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(401, "Invalid credentials")
    return {"message": "Login successful", "username": user.username}


# ── Sensor simulation ─────────────────────────────────────────────────────────
@app.get("/generate")
def generate(db: Session = Depends(get_db)):
    global _state
    snapshot = simulate_tick(_state)
    for room, rdata in snapshot["rooms"].items():
        for app_name, adata in rdata["appliances"].items():
            db.add(SensorReading(
                timestamp=datetime.utcnow(),
                room=room,
                appliance=app_name,
                power_w=adata["power_w"],
                temp_c=rdata["temperature"],
                is_on=int(adata["is_on"]),
            ))
    db.commit()
    return snapshot


@app.get("/data")
def get_data(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(SensorReading).order_by(SensorReading.id.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "room": r.room,
            "appliance": r.appliance,
            "power_w": r.power_w,
            "temp_c": r.temp_c,
            "is_on": r.is_on,
        }
        for r in reversed(rows)
    ]


# ── ML endpoints ──────────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    current_power: float


@app.post("/predict")
def predict(req: PredictRequest):
    predicted = predict_power(req.current_power)
    anomaly = detect_anomaly(req.current_power)
    return {"predicted_power": predicted, "is_anomaly": anomaly}


@app.get("/anomaly")
def anomaly_check(db: Session = Depends(get_db)):
    rows = db.query(SensorReading).order_by(SensorReading.id.desc()).limit(100).all()
    readings = [r.power_w for r in rows if r.power_w > 0]
    if not readings:
        return {"anomalies": []}
    results = [{"power_w": v, "is_anomaly": detect_anomaly(v)} for v in readings[-20:]]
    return {"anomalies": results}


@app.post("/retrain")
def retrain_models(db: Session = Depends(get_db)):
    rows = db.query(SensorReading).order_by(SensorReading.id.desc()).limit(500).all()
    readings = [r.power_w for r in rows if r.power_w > 0]
    if len(readings) < 10:
        raise HTTPException(400, "Not enough data to retrain")
    return retrain(readings)


# ── What-if simulation ────────────────────────────────────────────────────────
class SimulateRequest(BaseModel):
    current_power: float
    extra_appliances: Optional[list[str]] = []


APPLIANCE_WATTS = {
    "Iron Box": 1000, "Washing Machine": 500, "Microwave": 1200,
    "Geyser": 2000, "Grinder": 500, "Mixer": 400,
    "Extra AC": 1500, "Extra Heater": 1000,
}
THRESHOLD_LOW  = 2000
THRESHOLD_HIGH = 6000
FIRE_THRESHOLD = 8000


@app.post("/simulate")
def simulate_whatif(req: SimulateRequest):
    extra_w = sum(APPLIANCE_WATTS.get(a, 200) for a in req.extra_appliances)
    total = req.current_power + extra_w

    if total < THRESHOLD_LOW:
        level = "LOW"
        advice = "Energy usage is low. Safe to add more appliances."
        color = "green"
    elif total < THRESHOLD_HIGH:
        level = "NORMAL"
        advice = "System operating efficiently."
        color = "blue"
    else:
        level = "HIGH"
        advice = "High load detected! "
        if "Iron Box" in req.extra_appliances or req.current_power > 5000:
            advice += "Avoid using Iron Box while Washing Machine is running. "
        if "Geyser" in req.extra_appliances:
            advice += "Schedule Geyser usage during off-peak hours. "
        advice += "Consider turning off unused ACs."
        color = "red"

    hazard = total > FIRE_THRESHOLD
    anomaly = detect_anomaly(total)

    return {
        "total_power": round(total, 2),
        "extra_power": round(extra_w, 2),
        "level": level,
        "advice": advice,
        "color": color,
        "hazard_risk": hazard,
        "anomaly": anomaly,
        "fire_risk": hazard or anomaly,
    }


# ── Toggle appliance ──────────────────────────────────────────────────────────
class ToggleRequest(BaseModel):
    room: str
    appliance: str
    is_on: bool


@app.post("/toggle")
def toggle(req: ToggleRequest):
    global _state
    if req.room not in _state:
        _state[req.room] = {}
    _state[req.room][req.appliance] = req.is_on
    return {"room": req.room, "appliance": req.appliance, "is_on": req.is_on}


# ── Notification endpoints ────────────────────────────────────────────────────
class NotifyRequest(BaseModel):
    phone_number: str   # E.164 format e.g. +919876543210

class TestSMSRequest(BaseModel):
    phone_number: str
    message: Optional[str] = "SmartHome test alert: Your notification system is working correctly."

@app.post("/notify/check")
def notify_check(req: NotifyRequest, db: Session = Depends(get_db)):
    """Generate a snapshot and send SMS alerts for any active conditions."""
    global _state
    snapshot = simulate_tick(_state)
    alerts = check_and_notify(snapshot, req.phone_number)
    return {
        "total_power": snapshot["total_power"],
        "alerts_triggered": len(alerts),
        "alerts": alerts,
    }

@app.post("/notify/test")
def notify_test(req: TestSMSRequest):
    """Send a test SMS to verify Twilio credentials and phone number."""
    result = send_sms(req.phone_number, req.message)
    return result

@app.get("/notify/status")
def notify_status():
    """Check if Twilio is configured."""
    from notifications import _twilio_ready, ACCOUNT_SID, FROM_NUMBER
    return {
        "configured": _twilio_ready(),
        "from_number": FROM_NUMBER if _twilio_ready() else "not set",
        "account_sid_prefix": ACCOUNT_SID[:6] + "..." if len(ACCOUNT_SID) > 6 else "not set",
    }


# ── Real IoT Sensor Push endpoint ─────────────────────────────────────────────
# Sensors (ESP32, Raspberry Pi, etc.) POST their readings here.
# Once real data arrives, /generate returns it instead of simulated data.

class SensorPushRequest(BaseModel):
    room: str          # Must match room names: "Living Room", "Kitchen", etc.
    appliance: str     # Appliance name: "AC", "Fridge", etc.
    power_w: float     # Current power in Watts
    temp_c: float      # Room temperature in Celsius
    is_on: bool        # Whether the appliance is currently on

# In-memory store of latest real sensor readings
# Structure: { room: { appliance: { power_w, temp_c, is_on } } }
_real_sensor_data: dict = {}
_use_real_data: bool = False   # flips to True once first real reading arrives


@app.post("/sensor/push")
def sensor_push(req: SensorPushRequest, db: Session = Depends(get_db)):
    """
    IoT devices call this endpoint to push live sensor readings.
    Supports ESP8266, ESP32, Raspberry Pi, or any HTTP-capable device.

    Example Arduino/ESP32 code:
        HTTPClient http;
        http.begin("http://YOUR_PC_IP:8000/sensor/push");
        http.addHeader("Content-Type", "application/json");
        String body = "{\\"room\\":\\"Living Room\\",\\"appliance\\":\\"AC\\","
                       "\\"power_w\\":1480.5,\\"temp_c\\":27.3,\\"is_on\\":true}";
        http.POST(body);
    """
    global _real_sensor_data, _use_real_data

    if req.room not in _real_sensor_data:
        _real_sensor_data[req.room] = {}

    _real_sensor_data[req.room][req.appliance] = {
        "power_w": req.power_w,
        "temp_c":  req.temp_c,
        "is_on":   req.is_on,
    }
    _use_real_data = True

    # Also persist to DB
    db.add(SensorReading(
        timestamp = datetime.utcnow(),
        room      = req.room,
        appliance = req.appliance,
        power_w   = req.power_w,
        temp_c    = req.temp_c,
        is_on     = int(req.is_on),
    ))
    db.commit()

    return {"status": "received", "room": req.room, "appliance": req.appliance}


@app.get("/sensor/mode")
def sensor_mode():
    """Returns whether the system is using real sensor data or simulation."""
    return {
        "mode": "real" if _use_real_data else "simulation",
        "rooms_reporting": list(_real_sensor_data.keys()),
    }


@app.post("/sensor/reset")
def sensor_reset():
    """Switch back to simulation mode (clears real sensor data)."""
    global _real_sensor_data, _use_real_data
    _real_sensor_data = {}
    _use_real_data = False
    return {"status": "reset to simulation mode"}


# Override /generate to use real data when available
@app.get("/generate/live")
def generate_live(db: Session = Depends(get_db)):
    """
    Returns real sensor data if any device has pushed readings,
    otherwise falls back to simulation.
    """
    global _state, _real_sensor_data, _use_real_data

    if not _use_real_data:
        # No real sensors connected — use simulation
        return generate(db)

    # Build snapshot from real sensor data
    from simulator import ROOMS as ROOM_DEFS
    snapshot = {"timestamp": datetime.utcnow().isoformat(), "rooms": {}}

    for room, cfg in ROOM_DEFS.items():
        room_data = {"temperature": 0.0, "total_power": 0.0, "appliances": {}}
        total_w = 0.0
        temps = []

        for app, acfg in cfg["appliances"].items():
            real = _real_sensor_data.get(room, {}).get(app)
            if real:
                power = real["power_w"]
                is_on = real["is_on"]
                temps.append(real["temp_c"])
            else:
                # Appliance not yet reporting — fall back to simulation for it
                is_on = _state.get(room, {}).get(app, acfg["on"])
                import random
                power = round(acfg["base_w"] * (1 + random.uniform(-0.05, 0.05)), 2) if is_on else 0.0

            total_w += power
            room_data["appliances"][app] = {
                "power_w": round(power, 2),
                "is_on":   is_on,
                "type":    acfg["type"],
            }

        room_data["temperature"] = round(sum(temps) / len(temps), 1) if temps else round(cfg["base_temp"] + total_w / 5000, 1)
        room_data["total_power"] = round(total_w, 2)
        snapshot["rooms"][room] = room_data

    snapshot["total_power"] = round(
        sum(r["total_power"] for r in snapshot["rooms"].values()), 2
    )
    return snapshot
