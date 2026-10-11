"""
SMS Notification Service using Twilio.

Sends alerts when:
- Overheat
- Overload
- Smoke/Gas
- Appliances left ON

Smoke alerts are deduplicated so that repeated ESP32 readings
do not generate repeated SMS messages.
"""

import os
from dotenv import load_dotenv

# Load backend/.env
load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(__file__), ".env")
)

# ─────────────────────────────────────────────────────────────
# Twilio configuration
# ─────────────────────────────────────────────────────────────

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")

# ─────────────────────────────────────────────────────────────
# Alert thresholds
# ─────────────────────────────────────────────────────────────

OVERHEAT_TEMP = float(
    os.getenv("OVERHEAT_TEMP", "30")
)

OVERLOAD_W = float(
    os.getenv("OVERLOAD_WATTS", "6000")
)

# IMPORTANT:
# Your MQ2 readings in normal/clear conditions have been around
# 2300–3300, so 1500 would incorrectly trigger smoke.
#
# Put the threshold in .env so you can change it without
# modifying Python code.
SMOKE_PPM_THRESHOLD = float(
    os.getenv("SMOKE_PPM_THRESHOLD", "3800")
)

# Keep track of alerts already sent.
# This prevents SMS spam while the condition remains active.
_sent = set()


# ─────────────────────────────────────────────────────────────
# Check Twilio configuration
# ─────────────────────────────────────────────────────────────

def _twilio_ready() -> bool:
    return (
        ACCOUNT_SID.startswith("AC")
        and len(AUTH_TOKEN) > 10
        and FROM_NUMBER.startswith("+")
    )


# ─────────────────────────────────────────────────────────────
# Send SMS
# ─────────────────────────────────────────────────────────────

def send_sms(to_number: str, message: str) -> dict:
    """Send an SMS using Twilio."""

    if not _twilio_ready():
        return {
            "status": "skipped",
            "reason": "Twilio credentials not configured"
        }

    if not to_number or not to_number.startswith("+"):
        return {
            "status": "error",
            "reason": (
                "Invalid phone number. "
                "Use E.164 format, e.g. +919876543210"
            )
        }

    try:
        from twilio.rest import Client

        client = Client(
            ACCOUNT_SID,
            AUTH_TOKEN
        )

        msg = client.messages.create(
            body=message,
            from_=FROM_NUMBER,
            to=to_number
        )

        return {
            "status": "sent",
            "sid": msg.sid
        }

    except Exception as e:
        return {
            "status": "error",
            "reason": str(e)
        }


# ─────────────────────────────────────────────────────────────
# Smoke / Gas alert
# ─────────────────────────────────────────────────────────────

def check_smoke_and_notify(
    room: str,
    smoke_ppm: float,
    to_number: str
) -> dict:
    """
    Send an SMS when the MQ2 reading crosses the smoke threshold.

    One SMS is sent when smoke is first detected.
    Further readings do not send additional SMS messages until
    the smoke level returns to normal.
    """

    global _sent

    key = f"smoke_{room}"

    # ─────────────────────────────────────────────────────────
    # Smoke detected
    # ─────────────────────────────────────────────────────────

    if smoke_ppm > SMOKE_PPM_THRESHOLD:

        if key not in _sent:

            msg = (
                f"[SmartHome FIRE ALERT]\n"
                f"SMOKE/GAS DETECTED in {room}!\n"
                f"MQ2 reading: {smoke_ppm:.0f}\n"
                f"Threshold: {SMOKE_PPM_THRESHOLD:.0f}\n"
                f"Please check the room immediately."
            )

            result = send_sms(
                to_number,
                msg
            )

            # Only mark the alert as sent if Twilio actually
            # accepted the message.
            if result.get("status") == "sent":
                _sent.add(key)

            return result

        return {
            "status": "skipped",
            "reason": "Alert already sent for this room"
        }

    # ─────────────────────────────────────────────────────────
    # Smoke cleared
    # ─────────────────────────────────────────────────────────

    else:

        _sent.discard(key)

        return {
            "status": "clear",
            "reason": "Smoke level normal"
        }


# ─────────────────────────────────────────────────────────────
# General alert checking
# ─────────────────────────────────────────────────────────────

def check_and_notify(
    snapshot: dict,
    to_number: str
) -> list[dict]:
    """
    Inspect a snapshot for alert conditions.

    Handles:
    - Overload
    - Overheat
    - Appliances left ON
    - Smoke/Gas

    SMS messages are deduplicated.
    """

    global _sent

    alerts = []

    total_power = snapshot.get(
        "total_power",
        0
    )

    rooms = snapshot.get(
        "rooms",
        {}
    )

    # ─────────────────────────────────────────────────────────
    # OVERLOAD
    # ─────────────────────────────────────────────────────────

    if total_power > OVERLOAD_W:

        key = f"overload_{int(total_power // 500) * 500}"

        if key not in _sent:

            msg = (
                f"[SmartHome ALERT]\n"
                f"OVERLOAD DETECTED!\n"
                f"Total power: {total_power:.0f} W\n"
                f"Limit: {OVERLOAD_W:.0f} W\n"
                f"Turn off non-essential appliances."
            )

            result = send_sms(
                to_number,
                msg
            )

            if result.get("status") == "sent":
                _sent.add(key)

            alerts.append({
                "type": "overload",
                "message": msg,
                "sms": result
            })

    else:

        _sent = {
            k for k in _sent
            if not k.startswith("overload_")
        }

    # ─────────────────────────────────────────────────────────
    # OVERHEAT
    # ─────────────────────────────────────────────────────────

    for rname, rdata in rooms.items():

        temp = rdata.get(
            "temperature",
            0
        )

        if temp > OVERHEAT_TEMP:

            key = f"overheat_{rname}"

            if key not in _sent:

                msg = (
                    f"[SmartHome ALERT]\n"
                    f"OVERHEAT in {rname}!\n"
                    f"Temperature: {temp:.1f} C\n"
                    f"Limit: {OVERHEAT_TEMP:.1f} C\n"
                    f"Check AC or ventilation."
                )

                result = send_sms(
                    to_number,
                    msg
                )

                if result.get("status") == "sent":
                    _sent.add(key)

                alerts.append({
                    "type": "overheat",
                    "room": rname,
                    "temp": temp,
                    "sms": result
                })

        else:

            _sent.discard(
                f"overheat_{rname}"
            )

    # ─────────────────────────────────────────────────────────
    # APPLIANCES LEFT ON
    # ─────────────────────────────────────────────────────────

    for rname, rdata in rooms.items():

        appliances = rdata.get(
            "appliances",
            {}
        )

        for app, adata in appliances.items():

            is_on = adata.get(
                "is_on",
                False
            )

            app_type = adata.get(
                "type",
                ""
            )

            if is_on and app_type == "occasional":

                key = f"lefton_{rname}_{app}"

                if key not in _sent:

                    power = adata.get(
                        "power_w",
                        0
                    )

                    msg = (
                        f"[SmartHome REMINDER]\n"
                        f"{app} in {rname} is still ON.\n"
                        f"Power: {power:.0f} W\n"
                        f"Turn it off if not needed."
                    )

                    result = send_sms(
                        to_number,
                        msg
                    )

                    if result.get("status") == "sent":
                        _sent.add(key)

                    alerts.append({
                        "type": "left_on",
                        "room": rname,
                        "appliance": app,
                        "sms": result
                    })

            else:

                _sent.discard(
                    f"lefton_{rname}_{app}"
                )

    # ─────────────────────────────────────────────────────────
    # SMOKE / GAS
    # ─────────────────────────────────────────────────────────

    environment = snapshot.get(
        "environment",
        {}
    )

    for rname, edata in environment.items():

        smoke_ppm = edata.get(
            "smoke_ppm",
            0
        ) or 0

        smoke_alert = edata.get(
            "smoke_alert",
            False
        )

        if (
            smoke_alert
            or smoke_ppm > SMOKE_PPM_THRESHOLD
        ):

            key = f"smoke_{rname}"

            if key not in _sent:

                msg = (
                    f"[SmartHome FIRE ALERT]\n"
                    f"SMOKE/GAS DETECTED in {rname}!\n"
                    f"MQ2 reading: {smoke_ppm:.0f}\n"
                    f"Threshold: {SMOKE_PPM_THRESHOLD:.0f}\n"
                    f"Check for fire or gas leak immediately."
                )

                result = send_sms(
                    to_number,
                    msg
                )

                if result.get("status") == "sent":
                    _sent.add(key)

                alerts.append({
                    "type": "smoke",
                    "room": rname,
                    "smoke_ppm": smoke_ppm,
                    "sms": result
                })

        else:

            _sent.discard(
                f"smoke_{rname}"
            )

    return alerts