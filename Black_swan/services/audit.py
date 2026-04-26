import datetime


def log_event(trail: list, event: str, data: dict | None = None) -> list:
    entry = {
        "event": event,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }
    if data:
        entry["data"] = data
    return trail + [entry]
