# ──────────────────────────────────────────────────────────────
# MilkBox AI — Dream Landing Page (+ Milkbot tab, Preflight, Cockpit)
# Drop this file in: app.py
# ──────────────────────────────────────────────────────────────

from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Any
import streamlit as st
import json, os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List
from dotenv import load_dotenv

# Inject custom CSS
def local_css(file_name: str):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

Payload = Dict[str, Any]
Breakdown = Dict[str, float]

# ──────────────────────────────────────────────────────────────
# Load local environment (.env.local) into Streamlit secrets
# ──────────────────────────────────────────────────────────────
load_dotenv(".env.local")

# Dynamically merge into Streamlit's secrets dictionary
if "OPENAI_API_KEY" not in st.secrets:
    st.secrets["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

if "SUPABASE_URL" not in st.secrets:
    st.secrets["SUPABASE_URL"] = os.getenv("SUPABASE_URL", "")

if "SUPABASE_ANON_KEY" not in st.secrets:
    st.secrets["SUPABASE_ANON_KEY"] = os.getenv("SUPABASE_ANON_KEY", "")

# Optional helpers (safe if missing)
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except Exception:
    pass

st.set_page_config(page_title="Dream Landing Page", layout="wide")
local_css("assets/custom.css")

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

@st.cache_data(ttl=60)
def load_recent_logs(path: Path, limit: int = 25):
    """Load the most recent cockpit events from JSONL."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()[-limit:]
    return [json.loads(line) for line in lines if line.strip()]

# ──────────────────────────────────────────────────────────────
# Hero Section + Navigation Buttons + Cockpit Logs
# ──────────────────────────────────────────────────────────────
st.markdown("""
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
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# App constants & storage
# ──────────────────────────────────────────────────────────────
APP_NAME = "MilkBox AI — Dream Landing Page"
DATA_DIR = Path("data")
COCKPIT_DIR = DATA_DIR / "cockpit"
UPLOADS_DIR = DATA_DIR / "uploads"
for p in (DATA_DIR, COCKPIT_DIR, UPLOADS_DIR):
    p.mkdir(parents=True, exist_ok=True)

LOG_DREAM = COCKPIT_DIR / "dream_landing.jsonl"
LOG_MILKBOT = COCKPIT_DIR / "milkbot_chat.jsonl"

# ──────────────────────────────────────────────────────────────
# Milkbot (built-in chat)
# ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are Milkbot: blunt but kind, forward-thinking, Gen-Z witty. "
    "Compliance-first: receipts-first, human-in-the-loop, no hallucinations. "
    "Use clear, step-by-step instructions when asked. Keep answers tight."
)

def _log(logfile: Path, event: str, payload: dict):
    """Append a log entry to a JSONL file."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "payload": payload,
    }
    logfile.parent.mkdir(parents=True, exist_ok=True)
    with logfile.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def milkbot_tab():
    from typing import List, Dict
    # OpenAI client (lazy import so app runs even without package)
    client = None
    model_name = "gpt-4o-mini"
    try:
        from openai import OpenAI
        if st.secrets.get("OPENAI_API_KEY"):
            client = OpenAI()
    except Exception:
        client = None

    st.subheader("💬 Milkbot")
    if not client:
        st.info("Set `OPENAI_API_KEY` and install `openai` to chat. `pip install openai`", icon="ℹ️")

    if "milkbot_messages" not in st.session_state:
        st.session_state.milkbot_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": "Hey! I’m Milkbot. What do you need built?"}
        ]

    # Show history (skip system)
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

    # Respond (if client available), else echo fallback
    with st.chat_message("assistant"):
        if client:
            with st.spinner("Thinking…"):
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=st.session_state.milkbot_messages,
                    temperature=0.4,
                )
                answer = resp.choices[0].message.content or "…"
        else:
            answer = "Milkbot offline (no API key). Add OPENAI_API_KEY and `pip install openai`."
        st.markdown(answer)

    st.session_state.milkbot_messages.append({"role": "assistant", "content": answer})
    _log(LOG_MILKBOT, "assistant.msg", {"msg": answer})

st.divider()

# ──────────────────────────────────────────────────────────────
# Page config & tabs
# ──────────────────────────────────────────────────────────────
st.set_page_config(page_title=APP_NAME, page_icon="🧰", layout="wide")
tab_dream, tab_milkbot = st.tabs(["Dream Landing page","Milkbot"])

with tab_milkbot:
    milkbot_tab()

# Hidden cockpit logs for internal viewing
LOG_FILE = Path("data/cockpit/events.jsonl")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

with st.expander("📊 Cockpit (internal logs)", expanded=False):
    logs = load_recent_logs(LOG_FILE)
    if logs:
        for entry in logs:
            st.code(json.dumps(entry))
    else:
        st.info("No cockpit activity yet.")

# ──────────────────────────────────────────────────────────────
# END
# ──────────────────────────────────────────────────────────────
app_footer()