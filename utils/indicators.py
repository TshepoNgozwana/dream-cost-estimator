from typing import Dict, Any
from streamlit_app import compute_feature_cost

def compute_live_indicators(answers: Dict[str, Any]) -> Dict[str, Any]:
    feature_cost = compute_feature_cost(
        auth_needed=answers.get("auth_needed", False),
        payments_needed=answers.get("payments_needed", False),
        ai_features=answers.get("ai_features", []),
        integrations=answers.get("integrations", []),
        content_support=answers.get("content_support", "")
    )

    total_cost = feature_cost["total"]
    breakdown = feature_cost["breakdown"]

    # Risk rule
    if total_cost <= 40:
        risk = "Low"
    elif total_cost <= 55:
        risk = "Medium"
    else:
        risk = "High"

    return {
        "estimated_cost": round(total_cost, 1),
        "risk_level": risk,
        "ai_tools_needed": len(answers.get("ai_features", [])),
        "breakdown": breakdown,
    }
