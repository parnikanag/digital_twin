"""
simulator.py
────────────
Simulates sensor ticks for all rooms EXCEPT Bedroom 1.
Bedroom 1 is driven exclusively by real ESP32 hardware.

ROOMS defines the full house layout.  simulate_tick() respects the
_real_sensor_data / _device_state injected by main.py so that
Bedroom 1 always reflects live hardware values.
"""

import random
from datetime import datetime

# ── House layout ──────────────────────────────────────────────────────────────
# Bedroom 1 appliances match the physical hardware:
#   Lights  → GPIO5  LED
#   AC      → GPIO18 LED
#   Fan     → GPIO19 LED   (servo on GPIO13 tracked separately)
ROOMS = {
    "Bedroom 1": {
        "base_temp": 24.0,
        "real": True,          # ← driven by live ESP32 data
        "appliances": {
            "Lamp":   {"type": "continuous", "base_w": 40,   "on": False},
            "AC":     {"type": "continuous", "base_w": 1200, "on": False},
            "Geyser": {"type": "occasional", "base_w": 2000, "on": False},
        },
    },
    "Living Room": {
        "base_temp": 26.0,
        "real": False,
        "appliances": {
            "AC":       {"type": "continuous", "base_w": 1500, "on": True},
            "TV":       {"type": "moderate",   "base_w": 120,  "on": True},
            "Iron Box": {"type": "occasional", "base_w": 1000, "on": False},
            "Lights":   {"type": "continuous", "base_w": 60,   "on": True},
        },
    },
    "Bedroom 2": {
        "base_temp": 24.5,
        "real": False,
        "appliances": {
            "AC":     {"type": "continuous", "base_w": 1200, "on": False},
            "Lights": {"type": "continuous", "base_w": 40,   "on": True},
        },
    },
    "Kitchen": {
        "base_temp": 28.0,
        "real": False,
        "appliances": {
            "Fridge":    {"type": "continuous", "base_w": 150,  "on": True},
            "Grinder":   {"type": "occasional", "base_w": 500,  "on": False},
            "Mixer":     {"type": "occasional", "base_w": 400,  "on": False},
            "Microwave": {"type": "occasional", "base_w": 1200, "on": False},
            "Lights":    {"type": "continuous", "base_w": 50,   "on": True},
        },
    },
    "Washroom": {
        "base_temp": 27.0,
        "real": False,
        "appliances": {
            "Geyser": {"type": "occasional", "base_w": 2000, "on": False},
            "Lights": {"type": "continuous", "base_w": 30,   "on": True},
        },
    },
    "Utility": {
        "base_temp": 25.0,
        "real": False,
        "appliances": {
            "Washing Machine": {"type": "occasional", "base_w": 500, "on": False},
            "Lights":          {"type": "continuous", "base_w": 30,  "on": True},
        },
    },
}

OCCASIONAL_PROB = 0.15   # 15 % chance an occasional appliance turns on per tick

REAL_ROOM = "Bedroom 1"  # the only room backed by real hardware


def _jitter(val: float, pct: float = 0.05) -> float:
    return round(val * (1 + random.uniform(-pct, pct)), 2)


def simulate_tick(
    state: dict | None = None,
    real_sensor_data: dict | None = None,
    device_state: dict | None = None,
) -> dict:
    """
    Generate one snapshot of the whole house.

    Parameters
    ----------
    state            : toggle overrides from UI  { room: { appliance: bool } }
    real_sensor_data : live push data from ESP32 { room: { appliance: {...} } }
    device_state     : LED/servo state for Bedroom 1
                       { "lights_on": bool, "ac_on": bool,
                         "fan_on": bool, "servo_angle": int }
    """
    snapshot = {"timestamp": datetime.utcnow().isoformat(), "rooms": {}}

    for room, cfg in ROOMS.items():
        room_data = {"temperature": 0.0, "total_power": 0.0, "appliances": {}}
        total_w   = 0.0
        temps     = []

        # ── Bedroom 1: use real ESP32 data ────────────────────────────────────
        if cfg["real"] and real_sensor_data and room in real_sensor_data:
            rd        = real_sensor_data[room]
            dev       = device_state or {}
            app_map   = {
                "Lamp":   dev.get("lights_on", False),
                "AC":     dev.get("ac_on",     False),
                "Geyser": dev.get("fan_on",    False),
            }
            base_temp = rd.get(next(iter(rd), None), {}).get("temp_c", cfg["base_temp"])

            for app, acfg in cfg["appliances"].items():
                is_on  = app_map.get(app, False)
                power  = _jitter(acfg["base_w"]) if is_on else 0.0
                total_w += power
                room_data["appliances"][app] = {
                    "power_w": round(power, 2),
                    "is_on":   is_on,
                    "type":    acfg["type"],
                }

            # Temperature comes from live DHT22
            real_temp = None
            for v in rd.values():
                if isinstance(v, dict) and v.get("temp_c") is not None:
                    real_temp = v["temp_c"]
                    break
            room_data["temperature"] = round(real_temp, 1) if real_temp else round(cfg["base_temp"], 1)

        # ── All other rooms: simulate ─────────────────────────────────────────
        else:
            for app, acfg in cfg["appliances"].items():
                if state and room in state and app in state[room]:
                    is_on = state[room][app]
                elif acfg["type"] == "occasional":
                    is_on = random.random() < OCCASIONAL_PROB
                else:
                    is_on = acfg["on"]

                power    = _jitter(acfg["base_w"]) if is_on else 0.0
                total_w += power
                room_data["appliances"][app] = {
                    "power_w": round(power, 2),
                    "is_on":   is_on,
                    "type":    acfg["type"],
                }
                if is_on:
                    temps.append(cfg["base_temp"] + total_w / 5000)

            room_data["temperature"] = round(
                (sum(temps) / len(temps)) if temps else cfg["base_temp"], 1
            )

        room_data["total_power"] = round(total_w, 2)
        snapshot["rooms"][room]  = room_data

    snapshot["total_power"] = round(
        sum(r["total_power"] for r in snapshot["rooms"].values()), 2
    )
    return snapshot
