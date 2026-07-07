import random, math
from datetime import datetime

ROOMS = {
    "Living Room": {
        "base_temp": 26.0,
        "appliances": {
            "AC":       {"type": "continuous", "base_w": 1500, "on": True},
            "TV":       {"type": "moderate",   "base_w": 120,  "on": True},
            "Iron Box": {"type": "occasional", "base_w": 1000, "on": False},
            "Lights":   {"type": "continuous", "base_w": 60,   "on": True},
        },
    },
    "Bedroom 1": {
        "base_temp": 24.0,
        "appliances": {
            "AC":     {"type": "continuous", "base_w": 1200, "on": True},
            "Lights": {"type": "continuous", "base_w": 40,   "on": True},
        },
    },
    "Bedroom 2": {
        "base_temp": 24.5,
        "appliances": {
            "AC":     {"type": "continuous", "base_w": 1200, "on": False},
            "Lights": {"type": "continuous", "base_w": 40,   "on": True},
        },
    },
    "Kitchen": {
        "base_temp": 28.0,
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
        "appliances": {
            "Geyser": {"type": "occasional", "base_w": 2000, "on": False},
            "Lights": {"type": "continuous", "base_w": 30,   "on": True},
        },
    },
    "Utility": {
        "base_temp": 25.0,
        "appliances": {
            "Washing Machine": {"type": "occasional", "base_w": 500, "on": False},
            "Lights":          {"type": "continuous", "base_w": 30,  "on": True},
        },
    },
}

OCCASIONAL_PROB = 0.15   # 15% chance occasional appliance turns on each tick


def _jitter(val: float, pct: float = 0.05) -> float:
    return round(val * (1 + random.uniform(-pct, pct)), 2)


def simulate_tick(state: dict | None = None) -> dict:
    """
    Generate one tick of sensor data.
    state: optional dict of {room: {appliance: is_on}} to persist toggle state.
    Returns full snapshot dict.
    """
    snapshot = {"timestamp": datetime.utcnow().isoformat(), "rooms": {}}

    for room, cfg in ROOMS.items():
        room_data = {"temperature": 0.0, "total_power": 0.0, "appliances": {}}
        total_w = 0.0

        for app, acfg in cfg["appliances"].items():
            # Determine on/off
            if state and room in state and app in state[room]:
                is_on = state[room][app]
            else:
                if acfg["type"] == "occasional":
                    is_on = random.random() < OCCASIONAL_PROB
                else:
                    is_on = acfg["on"]

            power = _jitter(acfg["base_w"]) if is_on else 0.0
            total_w += power
            room_data["appliances"][app] = {
                "power_w": round(power, 2),
                "is_on":   is_on,
                "type":    acfg["type"],
            }

        # Temperature rises with load
        temp = _jitter(cfg["base_temp"] + total_w / 5000, 0.02)
        room_data["temperature"] = round(temp, 1)
        room_data["total_power"] = round(total_w, 2)
        snapshot["rooms"][room] = room_data

    snapshot["total_power"] = round(
        sum(r["total_power"] for r in snapshot["rooms"].values()), 2
    )
    return snapshot
