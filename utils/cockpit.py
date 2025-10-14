import json
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path("data/cockpit/events.jsonl")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def write_cockpit_event(action: str, payload=None, user="local-dev"):
    evt = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "user": user,
        "tool": "dream-landing",
        "action": action,
        "payload": payload or {},
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evt) + "\n")
