import streamlit as st
import json, os, uuid, base64
from datetime import datetime, timezone
from pathlib import Path
import openai
from utils.indicators import compute_live_indicators
from streamlit_app import _log, LOG_DREAM

try:
    import qrcode
    from io import BytesIO
    import base64
    HAS_QR = True
except ImportError:
    HAS_QR = False

# ──────────────────────────────────────────────────────────────
# Global Footer
# ──────────────────────────────────────────────────────────────
def app_footer():
    st.markdown("""
        <hr>
        <p style='text-align:center; font-size:13px; color:gray;'>
            © 2025 Dream Landing — Built by Team MilkBoxAI | Contact: Christo
        </p>
    """, unsafe_allow_html=True)

APP_NAME = "dream-landing"
DATA_DIR = Path("data")
COCKPIT_DIR = DATA_DIR / "cockpit"
COCKPIT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DREAM = COCKPIT_DIR / "dream_landing.jsonl"
INTERNAL_MARKUP = 0.50

# ──────────────────────────────────────────────────────────────
# Cockpit logger
# ──────────────────────────────────────────────────────────────
def _log(file: Path, event: str, payload: dict):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "payload": payload or {},
        "app": APP_NAME,
        "version": "1.4"
    }
    # ensure folder present
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# ───────────────────────────────────────────────
# Cost model (3.2 rules)
# ───────────────────────────────────────────────
@st.cache_data
def compute_feature_cost(auth_needed, payments_needed, ai_features, integrations, content_support):
    base = 29.0
    cost = base
    breakdown = {"Base": base}

    if auth_needed:
        cost += 4.0
        breakdown["Auth"] = 4.0
    if payments_needed:
        cost += 8.0
        breakdown["Payments"] = 8.0
    if ai_features and any(a.strip() and a != "None" for a in ai_features):
        cost += 10.0
        breakdown["AI"] = 10.0
    if integrations and any(i != "None" for i in integrations):
        extra = min(2.0 * len([i for i in integrations if i != "None"]), 6.0)
        cost += extra
        breakdown["Integrations"] = extra
    if content_support == "Need copy":
        cost += 3.0
        breakdown["Content Support"] = 3.0

    return {"total": cost, "breakdown": breakdown}

# ───────────────────────────────────────────────
# QR helper
# ───────────────────────────────────────────────
def qr_png_base64(text: str) -> str:
    if not HAS_QR:
        st.warning("QR generation unavailable. Install 'qrcode[pil]' and 'pillow' to enable this feature.")
        return ""
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def _validate_email(email: str) -> bool:
    import re
    return bool(re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email))

# ───────────────────────────────────────────────
# Session defaults
# ───────────────────────────────────────────────
if "answers" not in st.session_state:
    st.session_state.answers = {}

if "total_cost" not in st.session_state:
    st.session_state.total_cost = 29.0  # base

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ───────────────────────────────────────────────
# Indicators update callback + defaults
# ───────────────────────────────────────────────
def update_answers():
    """Read all widget keys from st.session_state, normalise into answers,
    compute indicators, and log to cockpit when changed."""
    A = st.session_state

    answers = {
        "title": A.get("title_input", ""),
        "contact_email": A.get("contact_email_input", ""),
        "industry": A.get("industry_input", "Manufacturing"),
        "goal": A.get("goal_input", "Lead Gen"),
        "audience": A.get("audience_input", "Small <1k"),
        "auth_needed": A.get("auth_input", False),
        "payments_needed": A.get("payments_input", False),
        "ai_features": A.get("ai_features_input", []),
        "integrations": A.get("integrations_input", []),
        "content_support": A.get("content_input", "Have copy"),
        "branding": A.get("branding_input", "Have brand kit"),
        "timeline": A.get("timeline_input", "1 week"),
        "budget": A.get("budget_input", "Entry"),
    }

    # persist canonical answers
    st.session_state["answers"] = answers

    # compute indicators from the canonical answers (ensures same math as cost)
    indicators = compute_live_indicators(answers)

    # compare with previous indicators to avoid duplicate logs
    prev = st.session_state.get("indicators_prev")
    if prev != indicators:
        st.session_state["indicators"] = indicators
        st.session_state["indicators_prev"] = indicators
        # log via existing _log -> LOG_DREAM
        try:
            _log(LOG_DREAM, "indicator.update", indicators)
        except Exception:
            # fall back quietly if logging is not available
            pass
    else:
        # ensure indicators present even if unchanged
        st.session_state.setdefault("indicators", indicators)

# Ensure session defaults for indicators exist
if "indicators" not in st.session_state:
    st.session_state["indicators"] = compute_live_indicators(st.session_state.get("answers", {}))

if "indicators_prev" not in st.session_state:
    st.session_state["indicators_prev"] = None

# ──────────────────────────────────────────────────────────────
# Reset Wizard Fields
# ──────────────────────────────────────────────────────────────
def reset_wizard_fields():
    """Clear all wizard-related session state values."""
    keys_to_clear = [
        "title_input", "contact_email_input", "industry_input", "goal_input",
        "audience_input", "auth_input", "payments_input", "ai_features_input",
        "integrations_input", "content_input", "branding_input",
        "timeline_input", "budget_input"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    # Also clear computed indicators and answers
    st.session_state["answers"] = {}
    st.session_state["last_indicators"] = {}

# ───────────────────────────────────────────────
# Layout
# ───────────────────────────────────────────────
st.title("🧭 Dream Project Wizard")
st.write("Fill all 13 fields. Sidebar updates live with cost estimate.")

# ─── Inputs in main column ───
with st.container():
    st.markdown("### Step 1 · Basics")
    project_name = st.text_input(
        "Project name * (1–60 chars)",
        key="title_input",
        on_change=update_answers,
        placeholder="e.g. My Project"
    )
    contact_email = st.text_input(
        "Contact email *",
        key="contact_email_input",
        on_change=update_answers,
        placeholder="name@example.com"
    )
    industry = st.selectbox(
        "Industry",
        ["Manufacturing", "Retail", "Services", "Education", "Other"],
        key="industry_input",
        on_change=update_answers
    )
    goal = st.selectbox(
        "Primary goal *",
        ["Lead Gen", "E-commerce", "Info", "Booking", "Internal Tool"],
        key="goal_input",
        on_change=update_answers
    )

    st.markdown("### Step 2 · Features")
    audience = st.selectbox(
        "Audience size",
        ["Small <1k", "Growing 1–10k", "Large >10k"],
        key="audience_input",
        on_change=update_answers
    )
    auth_needed = st.checkbox(
        "Auth needed?",
        key="auth_input",
        on_change=update_answers
    )
    payments_needed = st.checkbox(
        "Payments needed?",
        key="payments_input",
        on_change=update_answers
    )
    ai_features = st.multiselect(
        "AI features",
        ["Chatbot", "OCR", "Recommendations", "None"],
        key="ai_features_input",
        on_change=update_answers
    )
    integrations = st.multiselect(
        "Integrations",
        ["Supabase", "Stripe", "Google Sheets", "None"],
        key="integrations_input",
        on_change=update_answers
    )
    content_support = st.selectbox(
        "Content readiness",
        ["Have copy", "Need copy", "Mixed"],
        key="content_input",
        on_change=update_answers
    )

    st.markdown("### Step 3 · Branding & Budget")
    branding = st.selectbox(
        "Branding",
        ["Have brand kit", "Use default"],
        key="branding_input",
        on_change=update_answers
    )
    timeline = st.selectbox(
        "Timeline",
        ["1 week", "2–4 weeks", ">1 month"],
        key="timeline_input",
        on_change=update_answers
    )
    budget = st.selectbox(
        "Budget comfort",
        ["Entry", "Standard", "Premium"],
        key="budget_input",
        on_change=update_answers
    )

    submitted = st.button("✅ Submit Wizard")
    if submitted:
        st.success("Wizard submitted successfully! 🎉")
        reset_wizard_fields()
        st.rerun()

# ──────────────────────────────────────────────────────────────
# Live Indicators Sidebar (driven from session_state)
# ──────────────────────────────────────────────────────────────
with st.sidebar.expander("ℹ️ About Indicators", expanded=False):
    st.markdown("""
    **Indicators Guide**
    - 💰 *Estimated Cost*: Mirrors your feature cost model.
    - 🔺 *Risk Level*: Based on overall project complexity.
    - 🤖 *AI Tools Needed*: Number of AI features selected.
    """)

# ensure indicators exist
indicators = st.session_state.get("indicators", compute_live_indicators(st.session_state.get("answers", {})))

# Display three metrics (use nice formatting)
st.sidebar.metric("💰 Estimated Cost", f"R {indicators['estimated_cost']:.2f}")
st.sidebar.metric("🔺 Risk Level", indicators["risk_level"])
st.sidebar.metric("🤖 AI Tools Needed", indicators["ai_tools_needed"])

app_footer()

# ───────────────────────────────────────────────
# Persisted answers are already kept in st.session_state by the callback.
# Compute live cost from sanctioned answers so it stays in sync with indicators.
# ───────────────────────────────────────────────
answers = st.session_state.get("answers", {})
live_cost = compute_feature_cost(
    answers.get("auth_needed", False),
    answers.get("payments_needed", False),
    answers.get("ai_features", []),
    answers.get("integrations", []),
    answers.get("content_support", "")
)
st.session_state.total_cost = live_cost["total"]

# ───────────────────────────────────────────────
# Sidebar live tally
# ───────────────────────────────────────────────
with st.sidebar:
       st.header("💰 Live Cost Tally")
       for k, v in live_cost["breakdown"].items():
            st.write(f"- {k}: {v:.2f}")
       st.metric("Estimated Total", f"R {live_cost['total']:.2f}")

# ──────────────────────────────────────────────────────────────
# AI Assist Mode (ChatGPT Toggle)
# ──────────────────────────────────────────────────────────────
st.sidebar.divider()
use_ai = st.sidebar.toggle(
    "🤖 AI Assist Mode",
    value=False,
    help="Toggle AI-powered suggestions on or off"
)

if use_ai:
    if "OPENAI_API_KEY" in st.secrets:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        st.sidebar.success("AI Assist Mode is ON – powered by OpenAI")
        user_prompt = st.text_input("💡 Describe what you want to build:")

        if user_prompt:
            with st.spinner("DreamBot is thinking..."):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are DreamBot, an AI builder assistant helping users design landing pages."},
                            {"role": "user", "content": user_prompt},
                        ]
                    )
                    ai_suggestion = response.choices[0].message.content
                    st.subheader("AI Suggestion ✨")
                    st.write(ai_suggestion)
                except Exception as e:
                    st.error(f"AI Assist Error: {e}")
    else:
        st.sidebar.warning("Missing OpenAI API key. Add it to st.secrets before enabling AI Assist Mode.")
else:
    st.sidebar.info("Estimator mode only – no AI used.")

# ──────────────────────────────────────────────────────────────
# AI Assist Disclaimer
# ──────────────────────────────────────────────────────────────
st.markdown("""
<hr style="margin-top:2em;margin-bottom:1em;">
<small>
<b>AI Assist Mode Disclaimer:</b><br>
This feature uses the OpenAI API to generate responses.  
Dream Landing Page is not affiliated with or endorsed by OpenAI.  
All AI outputs are for informational use only and may contain errors.  
© 2025 Milky Roads / MilkBox AI
</small>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# Validation + Logging on submit
# ───────────────────────────────────────────────
if submitted:
    errors = []
    if not (1 <= len(project_name.strip()) <= 60):
        errors.append("❌ Project name must be 1–60 characters.")
    if not _validate_email(contact_email):
        errors.append("❌ Invalid email format.")
    if not goal.strip():
        errors.append("❌ Primary goal is required.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        _log(LOG_DREAM, "submit_wizard", {
            "answers_count": len(st.session_state.answers),
            "est_cost": st.session_state.total_cost,
        })
        st.success("Wizard submitted successfully! Answers saved.")

        st.session_state["ready_for_summary"] = True
