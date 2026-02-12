from datetime import datetime, timezone
import json
from pathlib import Path

LOG_FILE = Path("data/cockpit/events.jsonl")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def compute_live_indicators(answers: dict, feature_cost: dict) -> dict:
    """Compute live project indicators for cost, risk, and AI use."""
    total_cost = feature_cost.get("total", 0)
    ai_features = answers.get("ai_features", [])
    payments_needed = answers.get("payments_needed")
    auth_needed = answers.get("auth_needed")

    # Risk calculation heuristic
    risk_level = "Low"
    if total_cost > 50 or payments_needed or auth_needed:
        risk_level = "Medium"
    if total_cost > 80 or (payments_needed and ai_features):
        risk_level = "High"

    ai_tools_needed = len(ai_features) if ai_features else 0

    indicators = {
        "estimated_cost": total_cost,
        "risk_level": risk_level,
        "ai_tools_needed": ai_tools_needed,
        "ts": datetime.now(timezone.utc).isoformat()
    }

    # Log cockpit event
    _log_indicator_update(indicators)
    return indicators


def _log_indicator_update(indicators: dict):
    """Append indicator update to cockpit JSONL file."""
    entry = {
        "ts": indicators["ts"],
        "event": "indicator.update",
        "payload": indicators,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
