# ──────────────────────────────────────────────────────────────
# MilkBox AI — Dream Landing Page (+ Milkbot tab, Preflight, Cockpit)
# Drop this file in: streamlit_app.py
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
import streamlit as st

# ──────────────────────────────────────────────────────────────
# Page config (set once, early)
# ──────────────────────────────────────────────────────────────
APP_NAME = "MilkBox AI — Dream Landing Page"
st.set_page_config(page_title=APP_NAME, page_icon="🧰", layout="wide")

# ──────────────────────────────────────────────────────────────
# Env & secrets handling (read-only, with fallbacks)
# ──────────────────────────────────────────────────────────────
# Load .env.local if present (dev convenience)
load_dotenv(".env.local")
load_dotenv(override=True)

# Never assign into st.secrets — it's read-only
OPENAI_API_KEY: str = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY", "")

# Supabase is optional right now — read values if present, else blank
SUPABASE_URL: str = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY: str = st.secrets.get("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY", "")

# ──────────────────────────────────────────────────────────────
# Types
# ──────────────────────────────────────────────────────────────
Payload = Dict[str, Any]
Breakdown = Dict[str, float]

# ──────────────────────────────────────────────────────────────
# Styling helper
# ──────────────────────────────────────────────────────────────
def local_css(file_name: str) -> None:
    """Inject local CSS if the file exists (non-fatal if missing)."""
    path = Path(file_name)
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Apply CSS (safe if file missing)
local_css("assets/custom.css")

# ──────────────────────────────────────────────────────────────
# Global Footer
# ──────────────────────────────────────────────────────────────
def app_footer() -> None:
    st.markdown(
        """
        <hr>
        <p style='text-align:center; font-size:13px; color:gray;'>
            © 2025 Dream Landing — Built by Team MilkBoxAI | Contact: Christo
        </p>
        """,
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────────────────────
# Data dirs & cockpit logs
# ──────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
COCKPIT_DIR = DATA_DIR / "cockpit"
UPLOADS_DIR = DATA_DIR / "uploads"
for p in (DATA_DIR, COCKPIT_DIR, UPLOADS_DIR):
    p.mkdir(parents=True, exist_ok=True)

LOG_DREAM = COCKPIT_DIR / "dream_landing.jsonl"
LOG_MILKBOT = COCKPIT_DIR / "milkbot_chat.jsonl"
LOG_EVENTS = COCKPIT_DIR / "events.jsonl"

def _log(logfile: Path, event: str, payload: dict) -> None:
    """Append a log entry to a JSONL file."""
    logfile.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "payload": payload,
    }
    with logfile.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

@st.cache_data(ttl=60)
def load_recent_logs(path: Path, limit: int = 25) -> List[dict]:
    """Load the most recent cockpit events from JSONL."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()[-limit:]
    return [json.loads(line) for line in lines if line.strip()]

# ──────────────────────────────────────────────────────────────
# Hero Section
# ──────────────────────────────────────────────────────────────
st.markdown(
    """
<div style='text-align:center; margin-top:2rem;'>
    <h1>🚀 Design. Estimate. Launch.</h1>
    <p style='font-size:18px; color:#444;'>
        Turn your ideas into structured projects — fast, accurate, and beautiful.
    </p>
    <div style='margin-top:1.5rem;'>
        <a href="/Wizard" target="_self">
            <button style='padding:12px 24px; background-color:#1E88E5; color:white; border:none; border-radius:8px; font-size:16px;'>Start Wizard</button>
        </a>
        <a href="/About_and_HowTo" target="_self">
            <button style='padding:12px 24px; margin-left:10px; background-color:#E0E0E0; color:#333; border:none; border-radius:8px; font-size:16px;'>Read How-To</button>
        </a>
        <a href="/Summary" target="_self">
            <button style='padding:12px 24px; margin-left:10px; background-color:#4CAF50; color:white; border:none; border-radius:8px; font-size:16px;'>View Summary</button>
        </a>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

st.divider()

# ──────────────────────────────────────────────────────────────
# Milkbot (built-in chat)
# ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are Milkbot: blunt but kind, forward-thinking, Gen-Z witty. "
    "Compliance-first: receipts-first, human-in-the-loop, no hallucinations. "
    "Use clear, step-by-step instructions when asked. Keep answers tight."
)

def milkbot_tab() -> None:
    # Lazy import, so the app still loads if openai isn't installed
    client = None
    model_name = "gpt-4o-mini"

    if OPENAI_API_KEY:
        try:
            from openai import OpenAI  # type: ignore
            client = OpenAI(api_key=OPENAI_API_KEY)
        except Exception as e:
            client = None

    st.subheader("💬 Milkbot")

    if not OPENAI_API_KEY:
        st.info("Add an `OPENAI_API_KEY` in `.streamlit/secrets.toml` to enable chat.", icon="ℹ️")
    elif client is None:
        st.warning("`openai` package not available. Run: `pip install openai`", icon="⚠️")

    if "milkbot_messages" not in st.session_state:
        st.session_state.milkbot_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": "Hey! I’m Milkbot. What do you need built?"},
        ]

    # Show conversation (skip system)
    for msg in st.session_state.milkbot_messages:
        if msg["role"] == "system":
            continue
        with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
            st.markdown(msg["content"])

    user_msg = st.chat_input("Type your request…")
    if not user_msg:
        return

    # Log + append user
    st.session_state.milkbot_messages.append({"role": "user", "content": user_msg})
    _log(LOG_MILKBOT, "user.msg", {"msg": user_msg})

    # Respond
    with st.chat_message("assistant"):
        if client:
            with st.spinner("Thinking…"):
                try:
                    resp = client.chat.completions.create(
                        model=model_name,
                        messages=st.session_state.milkbot_messages,
                        temperature=0.4,
                    )
                    answer = resp.choices[0].message.content or "…"
                except Exception as e:
                    answer = f"Milkbot had an issue talking to the model: {e}"
        else:
            answer = "Milkbot offline. Add `OPENAI_API_KEY` and `pip install openai` to enable chat."
        st.markdown(answer)

    st.session_state.milkbot_messages.append({"role": "assistant", "content": answer})
    _log(LOG_MILKBOT, "assistant.msg", {"msg": answer})

# ──────────────────────────────────────────────────────────────
# Tabs (Dream landing + Milkbot)
# ──────────────────────────────────────────────────────────────
tab_dream, tab_milkbot = st.tabs(["Dream Landing page", "Milkbot"])

with tab_milkbot:
    milkbot_tab()

# Hidden cockpit logs for internal viewing (lightweight)
with st.expander("📊 Cockpit (internal logs)", expanded=False):
    logs = load_recent_logs(LOG_EVENTS)
    if logs:
        for entry in logs:
            st.code(json.dumps(entry))
    else:
        st.info("No cockpit activity yet.")

# ──────────────────────────────────────────────────────────────
# END
# ──────────────────────────────────────────────────────────────
app_footer()
