"""
Smart Plug Bridge
=================
Polls Wipro 10A smart plug every 5 seconds using tinytuya
and pushes real power readings to the SmartHome backend.

Run this in a separate terminal:
    python smart_plug_bridge.py
"""

import tinytuya
import requests
import time
import sys
from datetime import datetime

# Configuration
BACKEND       = "http://127.0.0.1:5000"
POLL_INTERVAL = 5

WIPRO_IP      = "192.168.1.48"
WIPRO_ID      = "d7f95761b6a01d2bdclolw"
WIPRO_KEY     = 'd;`k?7god6kaKl_{'
WIPRO_VERSION = "3.3"
WIPRO_ROOM    = "Living Room"
WIPRO_NAME    = "Lights"

def check_backend():
    try:
        r = requests.get(f"{BACKEND}/", timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def connect_plug():
    plug = tinytuya.OutletDevice(
        dev_id    = WIPRO_ID,
        address   = WIPRO_IP,
        local_key = WIPRO_KEY,
        version   = WIPRO_VERSION,
    )
    plug.set_socketPersistent(True)
    return plug

def read_plug(plug):
    try:
        status = plug.status()
        dps    = status.get("dps", {})
        is_on     = bool(dps.get("1",  False))
        power_w   = round(int(dps.get("19", 0)) / 10.0, 1)
        voltage_v = round(int(dps.get("20", 0)) / 10.0, 1)
        current_ma= int(dps.get("18", 0))
        return {"is_on": is_on, "power_w": power_w,
                "voltage_v": voltage_v, "current_ma": current_ma}
    except Exception as e:
        print(f"  [WARN] Read failed: {e}")
        return None

def push_to_backend(power_w, is_on):
    try:
        r = requests.post(
            f"{BACKEND}/sensor/push",
            json={"room": WIPRO_ROOM, "appliance": WIPRO_NAME,
                  "power_w": power_w, "temp_c": 27.0, "is_on": is_on},
            timeout=5,
        )
        return r.status_code == 200
    except Exception as e:
        print(f"  [ERROR] Backend unreachable: {e}")
        return False

def main():
    print("=" * 55)
    print("  SmartHome - Wipro Smart Plug Bridge")
    print("=" * 55)
    print(f"  Plug     : {WIPRO_NAME} ({WIPRO_ROOM})")
    print(f"  Plug IP  : {WIPRO_IP}")
    print(f"  Backend  : {BACKEND}")
    print("=" * 55)

    print("\nChecking backend...", end=" ")
    for attempt in range(10):
        if check_backend():
            print("connected.\n")
            break
        print(f"retry {attempt+1}/10...", end=" ")
        time.sleep(2)
    else:
        print("\n[ERROR] Backend not reachable.")
        sys.exit(1)

    print("Connecting to Wipro plug...", end=" ")
    try:
        plug = connect_plug()
        print("connected.\n")
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

    print(f"Polling every {POLL_INTERVAL}s. Press Ctrl+C to stop.\n")

    while True:
        ts   = datetime.now().strftime("%H:%M:%S")
        data = read_plug(plug)
        if data is None:
            print(f"[{ts}] {WIPRO_NAME} | OFFLINE - retrying...")
            time.sleep(POLL_INTERVAL)
            try:
                plug = connect_plug()
            except Exception:
                pass
            continue

        ok     = push_to_backend(data["power_w"], data["is_on"])
        status = "sent" if ok else "FAILED"
        state  = "ON " if data["is_on"] else "OFF"
        print(f"[{ts}] {WIPRO_NAME:16} | {data['power_w']:7.1f} W | "
              f"{data['voltage_v']:7.1f} V | {data['current_ma']:6} mA | "
              f"{state} | {status}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBridge stopped.")

