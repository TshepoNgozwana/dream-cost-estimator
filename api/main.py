from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timezone
import os, json, uuid

app = FastAPI(title="Dream Landing API", version="1.0")

LOG_PATH = "data/cockpit/dream_landing.jsonl"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)


def log_event(action: str, payload=None, user: str = "local-dev", session: str | None = None):
    evt = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "user": user,
        "tool": "dream-landing",
        "action": action,
        "payload": payload or {},
        "session": session or str(uuid.uuid4())
    }
    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(evt, ensure_ascii=False) + "\n")


class IdeaRequest(BaseModel):
    idea: str


@app.get("/health")
def health_check():
    log_event("health_check", {"status": "ok"})
    return {"status": "ok"}


@app.post("/spec")
def generate_spec(req: IdeaRequest):
    log_event("generate_spec", {"idea": req.idea})
    return {
        "title": req.idea,
        "inputs": ["idea_text"],
        "outputs": ["spec_json"],
        "notes": "This is a simple hard-coded stub for the trial."
    }
