from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import logging

from database import get_db, init_db, User, SensorReading, IotEvent
from auth import hash_password, verify_password
from simulator import simulate_tick, ROOMS
from ml_models import (
    predict_power, detect_anomaly, retrain,
    predict_power_rf, cluster_readings, get_automation_action
)
from notifications import check_and_notify, send_sms, check_smoke_and_notify

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("smarthome")

# ── Shared in-memory state ────────────────────────────────────────────────────

_state: dict = {}               # UI toggle overrides { room: { appliance: bool } }
_real_sensor_data: dict = {}    # latest ESP32 push   { room: { appliance: {...} } }
_use_real_data: bool = False
_env_data: dict = {}            # latest sensor environment per room
_fridge_door_open: bool = False # reed-switch state from ESP32

# ── Bedroom 1 actuator state — THIS IS WHAT /device/state RETURNS ─────────────
# Keys must exactly match what the ESP32 reads from the JSON:
#   lights_on, ac_on, geyser_on, fridge_on, servo_angle
_device_state: dict = {
    "lights_on":   False,
    "ac_on":       False,
    "geyser_on":   False,   # ← was "fan_on" — renamed to match ESP32
    "fridge_on":   False,
    "servo_angle": 0,
}

# Manual priority for temperature automation.
# If the user turns AC OFF while temperature is still > 30 C,
# the automatic rule will not immediately turn it back ON.
_ac_manual_off_override: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Smart Home Energy API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "SmartHome Energy API is running", "docs": "/docs"}


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


# ── Snapshot helpers ──────────────────────────────────────────────────────────
def _build_snapshot(db: Session) -> dict:
    global _state, _real_sensor_data, _use_real_data, _device_state
    snapshot = simulate_tick(
        state            = _state,
        real_sensor_data = _real_sensor_data if _use_real_data else None,
        device_state     = _device_state,
    )
    for room, rdata in snapshot["rooms"].items():
        for app_name, adata in rdata["appliances"].items():
            db.add(SensorReading(
                timestamp = datetime.utcnow(),
                room      = room,
                appliance = app_name,
                power_w   = adata["power_w"],
                temp_c    = rdata["temperature"],
                is_on     = int(adata["is_on"]),
            ))
    db.commit()
    return snapshot

@app.get("/generate")
def generate(db: Session = Depends(get_db)):
    return _build_snapshot(db)

@app.get("/generate/live")
def generate_live(db: Session = Depends(get_db)):
    return _build_snapshot(db)

@app.get("/data")
def get_data(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(SensorReading).order_by(SensorReading.id.desc()).limit(limit).all()
    return [
        {"id": r.id, "timestamp": r.timestamp.isoformat(),
         "room": r.room, "appliance": r.appliance,
         "power_w": r.power_w, "temp_c": r.temp_c, "is_on": r.is_on}
        for r in reversed(rows)
    ]


# ── ML endpoints ──────────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    current_power: float

@app.post("/predict")
def predict(req: PredictRequest):
    return {"predicted_power": predict_power(req.current_power),
            "is_anomaly": detect_anomaly(req.current_power)}

@app.get("/anomaly")
def anomaly_check(db: Session = Depends(get_db)):
    rows = db.query(SensorReading).order_by(SensorReading.id.desc()).limit(100).all()
    readings = [r.power_w for r in rows if r.power_w > 0]
    if not readings:
        return {"anomalies": []}
    return {"anomalies": [{"power_w": v, "is_anomaly": detect_anomaly(v)} for v in readings[-20:]]}

@app.post("/retrain")
def retrain_models(db: Session = Depends(get_db)):
    rows = db.query(SensorReading).order_by(SensorReading.id.desc()).limit(500).all()
    readings = [r.power_w for r in rows if r.power_w > 0]
    if len(readings) < 10:
        raise HTTPException(400, "Not enough data to retrain")
    return retrain(readings)


# ── What-if simulation ────────────────────────────────────────────────────────
class SimulateRequest(BaseModel):
    current_power:    float
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
    total   = req.current_power + extra_w
    if total < THRESHOLD_LOW:
        level, advice, color = "LOW",    "Energy usage is low.",          "green"
    elif total < THRESHOLD_HIGH:
        level, advice, color = "NORMAL", "System operating efficiently.", "blue"
    else:
        level, color = "HIGH", "red"
        advice = "High load! "
        if "Geyser" in req.extra_appliances:
            advice += "Schedule Geyser during off-peak hours. "
        advice += "Turn off unused ACs."
    hazard  = total > FIRE_THRESHOLD
    anomaly = detect_anomaly(total)
    return {"total_power": round(total, 2), "extra_power": round(extra_w, 2),
            "level": level, "advice": advice, "color": color,
            "hazard_risk": hazard, "anomaly": anomaly, "fire_risk": hazard or anomaly}


# ── Toggle appliance (Appliance Monitoring page) ──────────────────────────────
class ToggleRequest(BaseModel):
    room:      str
    appliance: str
    is_on:     bool

@app.post("/toggle")
def toggle(req: ToggleRequest):
    global _state, _device_state, _ac_manual_off_override
    if req.room not in _state:
        _state[req.room] = {}
    _state[req.room][req.appliance] = req.is_on

    # Mirror into _device_state so ESP32 poll picks it up
    if req.room == "Bedroom 1":
        key_map = {
            "Lamp":   "lights_on",
            "AC":     "ac_on",
            "Geyser": "geyser_on",
            "Fridge": "fridge_on",
        }
        if req.appliance in key_map:
            _device_state[key_map[req.appliance]] = req.is_on

            # Manual OFF always wins over the >30 C automatic AC rule.
            if req.appliance == "AC":
                _ac_manual_off_override = not req.is_on
                if _ac_manual_off_override:
                    log.info("[MANUAL OVERRIDE] User turned AC OFF")
                else:
                    log.info("[MANUAL] User turned AC ON")

            log.info(f"[toggle] {req.appliance} → {req.is_on}  |  state now: {_device_state}")

    plug_result = None
    if req.room == "Living Room" and req.appliance == "Lights":
        plug_result = _control_wipro_plug(req.is_on)
    return {"room": req.room, "appliance": req.appliance,
            "is_on": req.is_on, "plug_control": plug_result}

def _control_wipro_plug(is_on: bool) -> dict:
    try:
        import tinytuya
        plug = tinytuya.OutletDevice(
            dev_id="d7f95761b6a01d2bdclolw", address="192.168.1.48",
            local_key="d;`k?7god6kaKl_{", version="3.3")
        plug.set_socketPersistent(False)
        plug.turn_on() if is_on else plug.turn_off()
        return {"status": "ok", "command": "on" if is_on else "off"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


# ── Real ESP32 sensor push ────────────────────────────────────────────────────
class SensorPushRequest(BaseModel):
    room:             str
    appliance:        str
    power_w:          float
    temp_c:           float
    is_on:            bool
    humidity:         Optional[float] = None
    smoke_ppm:        Optional[float] = None
    smoke_alert:      Optional[bool]  = None
    motion:           Optional[bool]  = None
    fridge_door_open: Optional[bool]  = None

@app.post("/sensor/push")
def sensor_push(req: SensorPushRequest, db: Session = Depends(get_db)):
    """
    Receives live ESP32 sensor readings.

    Temperature automation for Bedroom 1:
      - temp > 30 C: AC turns ON automatically
      - if user manually turns AC OFF, that OFF state wins while temp stays > 30 C
      - once temp returns to <= 30 C, the manual override is cleared
      - if temperature later rises above 30 C again, auto-ON is allowed again
    """
    global _real_sensor_data, _use_real_data, _env_data, _fridge_door_open
    global _device_state, _state, _ac_manual_off_override

    if req.room not in _real_sensor_data:
        _real_sensor_data[req.room] = {}
    _real_sensor_data[req.room][req.appliance] = {
        "power_w": req.power_w,
        "temp_c": req.temp_c,
        "is_on": req.is_on,
    }
    _use_real_data = True

    if req.room not in _env_data:
        _env_data[req.room] = {}
    env = _env_data[req.room]
    env["temp_c"] = req.temp_c
    if req.humidity is not None:
        env["humidity"] = req.humidity
    if req.smoke_ppm is not None:
        env["smoke_ppm"] = req.smoke_ppm
    if req.smoke_alert is not None:
        env["smoke_alert"] = req.smoke_alert
    if req.motion is not None:
        env["motion"] = req.motion
    if req.fridge_door_open is not None:
        _fridge_door_open = req.fridge_door_open
        env["fridge_door_open"] = req.fridge_door_open
        log.info(f"[sensor/push] fridge_door_open = {req.fridge_door_open}")

    # ── Temperature automation ────────────────────────────────────────────────
    if req.room == "Bedroom 1":
        if req.temp_c > 30.0:
            if not _ac_manual_off_override and not _device_state["ac_on"]:
                _device_state["ac_on"] = True
                if "Bedroom 1" not in _state:
                    _state["Bedroom 1"] = {}
                _state["Bedroom 1"]["AC"] = True
                log.info(
                    f"[AUTO] Bedroom 1 temp {req.temp_c:.1f} C > 30 C -> AC ON"
                )
            elif _ac_manual_off_override:
                log.debug(
                    f"[AUTO] Temp {req.temp_c:.1f} C > 30 C, "
                    "but manual AC OFF override is active"
                )
        else:
            # Re-arm automatic control after temperature returns to normal.
            if _ac_manual_off_override:
                log.info(
                    f"[AUTO] Bedroom 1 temp {req.temp_c:.1f} C <= 30 C "
                    "-> manual AC OFF override cleared"
                )
            _ac_manual_off_override = False

    db.add(SensorReading(
        timestamp=datetime.utcnow(),
        room=req.room,
        appliance=req.appliance,
        power_w=req.power_w,
        temp_c=req.temp_c,
        is_on=int(req.is_on),
        humidity=req.humidity,
        smoke_ppm=req.smoke_ppm,
        smoke_alert=int(req.smoke_alert) if req.smoke_alert is not None else None,
        motion=int(req.motion) if req.motion is not None else None,
    ))

    if req.smoke_alert:
        db.add(IotEvent(
            timestamp=datetime.utcnow(),
            event_type="smoke",
            room=req.room,
            value=req.smoke_ppm,
            message=f"Smoke detected in {req.room} (MQ2={req.smoke_ppm})",
        ))

    if req.motion:
        db.add(IotEvent(
            timestamp=datetime.utcnow(),
            event_type="motion",
            room=req.room,
            value=1.0,
            message=f"Motion detected in {req.room}",
        ))

    db.commit()

    return {
        "status": "received",
        "room": req.room,
        "appliance": req.appliance,
        "automation": {
            "temperature": req.temp_c,
            "threshold_c": 30.0,
            "ac_on": _device_state["ac_on"],
            "manual_off_override": _ac_manual_off_override,
        },
    }


# ── Fridge door dedicated endpoint (called by ESP32 on reed-switch change) ────
class FridgeDoorRequest(BaseModel):
    room:             str   = "Bedroom 1"
    fridge_door_open: bool

@app.post("/sensor/fridge-door")
def fridge_door_update(req: FridgeDoorRequest):
    """
    ESP32 calls this immediately when the reed switch changes state.
    Faster than waiting for the next 5-second sensor push.
    """
    global _fridge_door_open, _env_data
    _fridge_door_open = req.fridge_door_open
    if req.room not in _env_data:
        _env_data[req.room] = {}
    _env_data[req.room]["fridge_door_open"] = req.fridge_door_open
    log.info(f"[fridge-door] room={req.room}  fridge_door_open={req.fridge_door_open}")
    return {"status": "ok", "fridge_door_open": req.fridge_door_open}


# ── Device control (Bedroom 1 Control page buttons) ──────────────────────────
class DeviceControlRequest(BaseModel):
    room:   str
    device: str            # lamp | ac | geyser | fridge | servo
    is_on:  Optional[bool] = None
    angle:  Optional[int]  = None

@app.post("/device/control")
def device_control(req: DeviceControlRequest):
    """
    Dashboard POSTs here to change a device.
    Updates _device_state which the ESP32 polls via GET /device/state.
    Manual AC OFF takes priority over automatic temperature control.
    """
    global _device_state, _state, _ac_manual_off_override

    if req.device == "servo":
        angle = 90 if (req.angle or 0) >= 45 else 0
        _device_state["servo_angle"] = angle
        log.info(f"[device/control] servo → angle={angle}  |  state: {_device_state}")
        return {"status": "ok", "device": "servo", "angle": angle}

    key_map = {
        "lamp":   "lights_on",
        "lights": "lights_on",
        "ac":     "ac_on",
        "geyser": "geyser_on",
        "fridge": "fridge_on",
    }
    if req.device not in key_map:
        raise HTTPException(
            400,
            f"Unknown device '{req.device}'. Valid: lamp, ac, geyser, fridge, servo"
        )

    state_key = key_map[req.device]
    _device_state[state_key] = bool(req.is_on)

    # Manual AC control gets priority over the temperature rule.
    if req.device == "ac":
        if req.is_on is False:
            _ac_manual_off_override = True
            log.info("[MANUAL OVERRIDE] User turned AC OFF")
        else:
            _ac_manual_off_override = False
            log.info("[MANUAL] User turned AC ON")

    app_name_map = {
        "lamp":   "Lamp",
        "lights": "Lamp",
        "ac":     "AC",
        "geyser": "Geyser",
        "fridge": "Fridge",
    }
    room = req.room
    if room not in _state:
        _state[room] = {}
    _state[room][app_name_map[req.device]] = bool(req.is_on)

    log.info(
        f"[device/control] {req.device} → {req.is_on}  |  "
        f"state now: {_device_state}"
    )
    return {
        "status": "ok",
        "device": req.device,
        "is_on": req.is_on,
        "device_state": _device_state,
        "ac_manual_off_override": _ac_manual_off_override,
    }


# ── /device/state — polled by ESP32 every 1 s ─────────────────────────────────
@app.get("/device/state")
def device_state_get():
    """
    Returns the current actuator state for Bedroom 1.
    ESP32 reads: lights_on, ac_on, geyser_on, fridge_on, servo_angle
    """
    log.debug(f"[device/state] GET → {_device_state}")
    return {"room": "Bedroom 1", **_device_state}


# ── Sensor meta endpoints ─────────────────────────────────────────────────────
@app.get("/sensor/mode")
def sensor_mode():
    return {"mode": "real" if _use_real_data else "simulation",
            "rooms_reporting": list(_real_sensor_data.keys())}

@app.post("/sensor/reset")
def sensor_reset():
    global _real_sensor_data, _use_real_data, _env_data, _device_state, _fridge_door_open
    global _ac_manual_off_override
    _real_sensor_data = {}
    _env_data         = {}
    _use_real_data    = False
    _fridge_door_open = False
    _ac_manual_off_override = False
    _device_state     = {
        "lights_on":   False,
        "ac_on":       False,
        "geyser_on":   False,
        "fridge_on":   False,
        "servo_angle": 0,
    }
    log.info("[sensor/reset] reset to simulation mode")
    return {"status": "reset to simulation mode"}

@app.get("/sensor/environment")
def sensor_environment():
    return {"environment": _env_data, "fridge_door_open": _fridge_door_open}


# ── IoT events ────────────────────────────────────────────────────────────────
@app.get("/iot/events")
def iot_events(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(IotEvent).order_by(IotEvent.id.desc()).limit(limit).all()
    return [{"id": r.id, "timestamp": r.timestamp.isoformat(),
             "event_type": r.event_type, "room": r.room,
             "value": r.value, "message": r.message}
            for r in reversed(rows)]

@app.post("/sensor/smoke-alert")
def smoke_alert_endpoint(req, db: Session = Depends(get_db)):
    pass  # kept for compatibility

# ── Notifications ──────────────────────────────────────────────────────────────
class NotifyRequest(BaseModel):
    phone_number: str

class TestSMSRequest(BaseModel):
    phone_number: str
    message: Optional[str] = "SmartHome test alert: system working."

@app.post("/notify/check")
def notify_check(req: NotifyRequest, db: Session = Depends(get_db)):
    snapshot = simulate_tick(_state)
    alerts   = check_and_notify(snapshot, req.phone_number)
    return {"total_power": snapshot["total_power"],
            "alerts_triggered": len(alerts), "alerts": alerts}

@app.post("/notify/test")
def notify_test(req: TestSMSRequest):
    return send_sms(req.phone_number, req.message)

@app.get("/notify/status")
def notify_status():
    from notifications import _twilio_ready, ACCOUNT_SID, FROM_NUMBER
    return {"configured": _twilio_ready(),
            "from_number": FROM_NUMBER if _twilio_ready() else "not set",
            "account_sid_prefix": ACCOUNT_SID[:6] + "..." if len(ACCOUNT_SID) > 6 else "not set"}


# ── Advanced ML ───────────────────────────────────────────────────────────────
class RFPredictRequest(BaseModel):
    current_power: float
    temp_c:        float = 28.0
    humidity:      float = 65.0
    hour:          int   = 12

@app.post("/predict/rf")
def predict_rf(req: RFPredictRequest):
    predicted = predict_power_rf(req.current_power, req.temp_c, req.humidity, req.hour)
    return {"predicted_power": predicted, "is_anomaly": detect_anomaly(req.current_power),
            "model": "RandomForest", "features_used": ["power_w","temp_c","humidity","hour"]}

@app.get("/cluster")
def cluster(limit: int = 100, db: Session = Depends(get_db)):
    rows     = db.query(SensorReading).order_by(SensorReading.id.desc()).limit(limit).all()
    readings = [r.power_w for r in rows if r.power_w and r.power_w > 0]
    if len(readings) < 3:
        raise HTTPException(400, "Not enough data for clustering")
    return cluster_readings(readings)

class AutomationRequest(BaseModel):
    temp_c:      float
    motion:      bool  = False
    power_w:     float
    hour:        int   = 12
    smoke_alert: bool  = False

@app.post("/automate")
def automate(req: AutomationRequest):
    return get_automation_action(
        temp=req.temp_c, motion=req.motion, power=req.power_w,
        hour=req.hour, smoke=req.smoke_alert)
