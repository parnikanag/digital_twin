"""
SMS Notification Service using Twilio.
Sends alerts when overheat or overload conditions are detected.
"""
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

ACCOUNT_SID   = os.getenv("TWILIO_ACCOUNT_SID", "")
AUTH_TOKEN    = os.getenv("TWILIO_AUTH_TOKEN", "")
FROM_NUMBER   = os.getenv("TWILIO_FROM_NUMBER", "")
OVERHEAT_TEMP = float(os.getenv("OVERHEAT_TEMP", "30"))
OVERLOAD_W    = float(os.getenv("OVERLOAD_WATTS", "6000"))

# Track sent alerts to avoid spamming (in-memory, resets on restart)
_sent: set = set()


def _twilio_ready() -> bool:
    return (
        ACCOUNT_SID.startswith("AC")
        and len(AUTH_TOKEN) > 10
        and FROM_NUMBER.startswith("+")
    )


def send_sms(to_number: str, message: str) -> dict:
    """Send an SMS via Twilio. Returns status dict."""
    if not _twilio_ready():
        return {"status": "skipped", "reason": "Twilio credentials not configured"}

    if not to_number or not to_number.startswith("+"):
        return {"status": "error", "reason": "Invalid phone number. Use E.164 format e.g. +919876543210"}

    try:
        from twilio.rest import Client
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=FROM_NUMBER,
            to=to_number,
        )
        return {"status": "sent", "sid": msg.sid}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def check_and_notify(snapshot: dict, to_number: str) -> list[dict]:
    """
    Inspect snapshot for alert conditions.
    Sends SMS for new alerts only (deduplication via _sent set).
    Returns list of alert dicts.
    """
    global _sent
    alerts = []

    total_power = snapshot.get("total_power", 0)
    rooms       = snapshot.get("rooms", {})

    # ── Overload check ────────────────────────────────────────────────────────
    if total_power > OVERLOAD_W:
        key = f"overload_{int(total_power // 500) * 500}"
        if key not in _sent:
            msg = (
                f"[SmartHome ALERT] OVERLOAD DETECTED!\n"
                f"Total power: {total_power:.0f} W (limit: {OVERLOAD_W:.0f} W).\n"
                f"Turn off non-essential appliances immediately."
            )
            result = send_sms(to_number, msg)
            _sent.add(key)
            alerts.append({"type": "overload", "message": msg, "sms": result})
    else:
        # Clear overload keys when power drops back to normal
        _sent = {k for k in _sent if not k.startswith("overload_")}

    # ── Overheat check ────────────────────────────────────────────────────────
    for rname, rdata in rooms.items():
        temp = rdata.get("temperature", 0)
        if temp > OVERHEAT_TEMP:
            key = f"overheat_{rname}"
            if key not in _sent:
                msg = (
                    f"[SmartHome ALERT] OVERHEAT in {rname}!\n"
                    f"Temperature: {temp} °C (limit: {OVERHEAT_TEMP} °C).\n"
                    f"Check AC or ventilation."
                )
                result = send_sms(to_number, msg)
                _sent.add(key)
                alerts.append({"type": "overheat", "room": rname, "temp": temp, "sms": result})
        else:
            _sent.discard(f"overheat_{rname}")

    # ── Occasional appliances left on ─────────────────────────────────────────
    for rname, rdata in rooms.items():
        for app, adata in rdata["appliances"].items():
            if adata["is_on"] and adata["type"] == "occasional":
                key = f"lefton_{rname}_{app}"
                if key not in _sent:
                    msg = (
                        f"[SmartHome REMINDER] {app} in {rname} is still ON "
                        f"({adata['power_w']:.0f} W). Turn it off if not needed."
                    )
                    result = send_sms(to_number, msg)
                    _sent.add(key)
                    alerts.append({"type": "left_on", "room": rname, "appliance": app, "sms": result})
            else:
                _sent.discard(f"lefton_{rname}_{app}")

    return alerts
