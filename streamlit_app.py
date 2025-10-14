# ──────────────────────────────────────────────────────────────
# MilkBox AI — Dream Landing Page (+ Milkbot tab, Preflight, Cockpit)
# Drop this file in: streamlit_app.py
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv
import streamlit as st

# Preflight event logger utility (writes to cockpit/events.jsonl)
from utils.cockpit import write_cockpit_event

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
# Allow .env to override if present (still safe in Codespaces)
load_dotenv(override=True)

def get_secret(key: str, default: str = "") -> str:
    """Safely get secret from st.secrets or environment variable (no writes to st.secrets)."""
    if key in st.secrets:
        return str(st.secrets[key]).strip()
    return os.getenv(key, default).strip()

# Read keys through the helper (keeps st.secrets read-only)
OPENAI_API_KEY: str = get_secret("OPENAI_API_KEY")
SUPABASE_URL: str = get_secret("SUPABASE_URL")
SUPABASE_ANON_KEY: str = get_secret("SUPABASE_ANON_KEY")

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
LOG_EVENTS = COCKPIT_DIR / "events.jsonl"  # write_cockpit_event writes here

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
        except Exception:
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
# Tabs (Dream landing + Milkbot + Preflight)
# ──────────────────────────────────────────────────────────────
tab_dream, tab_milkbot, tab_preflight = st.tabs(["Dream Landing page", "Milkbot", "Preflight"])

with tab_dream:
    st.info("This is the Dream Landing page tab. Use the buttons above to navigate to other sections.", icon="ℹ️")

with tab_milkbot:
    milkbot_tab()

# ──────────────────────────────────────────────────────────────
# Preflight tab – System check and environment validation
# ──────────────────────────────────────────────────────────────
with tab_preflight:
    st.title("🧩 Preflight Check")
    st.caption("Quick system and environment validation before running builds.")

    results: Dict[str, Any] = {}
    results["Python Version"] = os.sys.version.split()[0]
    results["Streamlit Version"] = st.__version__
    results["Working Directory"] = os.getcwd()

    # Check secrets and environment variables
    has_openai_key = bool(
        st.secrets.get("OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
    )
    results["OPENAI_API_KEY loaded"] = has_openai_key

    if has_openai_key:
        st.success("✅ OPENAI_API_KEY is loaded from secrets or env.")
        write_cockpit_event("preflight.ok", {"openai_key": True})
    else:
        st.warning("⚠️ Missing OPENAI_API_KEY in secrets/env.")
        write_cockpit_event("preflight.missing_openai_key", {"openai_key": False})

    st.divider()
    st.subheader("System Information")
    st.json(results)

# ──────────────────────────────────────────────────────────────
# Hidden cockpit logs for internal viewing (lightweight)
# ──────────────────────────────────────────────────────────────
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
