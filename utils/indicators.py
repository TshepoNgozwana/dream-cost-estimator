from typing import Dict, Any

def compute_live_indicators(wizard_answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return simple live indicators shown in the sidebar:
    - cost_tally
    - risk_level
    - ai_needed
    Placeholder logic for now; Tshepo can replace/extend.
    """
    # very basic draft scoring
    base = 29
    auth = 4 if wizard_answers.get("auth") else 0
    payments = 8 if wizard_answers.get("payments") else 0
    ai = 10 if wizard_answers.get("ai") else 0
    integrations = 2 * len(wizard_answers.get("integrations", []))
    content = 3 if wizard_answers.get("need_copy") else 0

    cost = base + auth + payments + ai + min(integrations, 6) + content
    return {
        "cost_tally": cost,
        "risk_level": "low" if cost < 40 else ("med" if cost < 60 else "high"),
        "ai_needed": bool(ai),
    }
