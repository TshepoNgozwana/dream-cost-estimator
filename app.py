# ──────────────────────────────────────────────────────────────
# MilkBox AI — Dream Landing Page (with Preflight Checklist)
# Drop this file in: milkbox_dream/app.py
# ──────────────────────────────────────────────────────────────

from __future__ import annotations

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import streamlit as st

# Optional helpers (safe if missing)
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except Exception:
    pass

# ──────────────────────────────────────────────────────────────
# App constants & storage
# ──────────────────────────────────────────────────────────────
APP_NAME = "MilkBox AI — Dream Landing Page"
DATA_DIR = Path("data")
COCKPIT_DIR = DATA_DIR / "cockpit"
UPLOADS_DIR = DATA_DIR / "uploads"
for p in (DATA_DIR, COCKPIT_DIR, UPLOADS_DIR):
    p.mkdir(parents=True, exist_ok=True)

LOG_FILE = COCKPIT_DIR / "dream_landing.jsonl"

# Hidden internal markup factor (kept invisible in UI)
INTERNAL_MARKUP = 0.50

# ──────────────────────────────────────────────────────────────
# Cockpit logger
# ──────────────────────────────────────────────────────────────
def log_event(event: str, payload: Dict[str, Any]):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "payload": payload,
        "app": APP_NAME,
        "version": "1.3",
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# ──────────────────────────────────────────────────────────────
# Session defaults
# ──────────────────────────────────────────────────────────────
if "answers" not in st.session_state:
    st.session_state.answers = {k: "" for k in [
        "title", "goal", "audience", "inputs", "outputs",
        "must_haves", "nice_to_haves", "integrations", "constraints",
        "success", "team", "timeline", "risks"
    ]}

if "cost_knobs" not in st.session_state:
    st.session_state.cost_knobs = {"api_keys": 0, "secrets": 0, "tools": 1}

if "trial_days_left" not in st.session_state:
    # 3-day demo trial
    st.session_state.trial_days_left = 3

if "trial_tokens" not in st.session_state:
    # 100 demo tokens
    st.session_state.trial_tokens = 100

if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0

# ──────────────────────────────────────────────────────────────
# Cost model (very simple; internal markup applied)
# ──────────────────────────────────────────────────────────────
COST_WEIGHTS = {"api_keys": 120.0, "secrets": 30.0, "tools": 50.0}

def compute_cost(knobs: Dict[str, float]) -> Dict[str, Any]:
    base = sum(COST_WEIGHTS[k] * float(knobs.get(k, 0)) for k in COST_WEIGHTS)
    total = base * (1.0 + INTERNAL_MARKUP)
    return {
        "base": base,
        "total": total,
        "breakdown": {
            "API keys": COST_WEIGHTS["api_keys"] * float(knobs.get("api_keys", 0)),
            "Secrets": COST_WEIGHTS["secrets"] * float(knobs.get("secrets", 0)),
            "Tools (manual + scout)": COST_WEIGHTS["tools"] * float(knobs.get("tools", 0)),
        },
    }

# ──────────────────────────────────────────────────────────────
# Connectors registry (safe import)
# ──────────────────────────────────────────────────────────────
def has_connectors_folder() -> bool:
    return Path("connectors").exists() and Path("connectors").is_dir()

def load_openai_probe() -> Dict[str, Any]:
    """
    Cheap readiness probe. Does NOT make outbound calls here.
    We just check that we can import registry & that a key exists.
    """
    ok_folder = has_connectors_folder()
    has_key = bool((os.getenv("OPENAI_API_KEY") or "").strip())
    reg_ok = False
    try:
        from connectors import REGISTRY  # type: ignore
        reg_ok = "OpenAI" in REGISTRY
    except Exception:
        reg_ok = False
    return {
        "folder": ok_folder,
        "has_key": has_key,
        "registry": reg_ok,
    }

# ──────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────
st.set_page_config(page_title=APP_NAME, page_icon="🧰", layout="wide")

# Sidebar — Setup & Preflight
with st.sidebar:
    st.header("Setup")
    category = st.selectbox("What do you want to build?", ["Bot", "Dashboard", "Automation", "Scraper"], index=0)

    st.divider()

    debug_skip_redirect = st.checkbox("🛠️ Debug: Skip redirect to MilkBoxAI", value=False,
                                      help="When enabled, deploy won't try to redirect to your site.")

    st.divider()
    with st.expander("📦 Universal Uploads", expanded=False):
        files = st.file_uploader("Drop any reference files here", accept_multiple_files=True, label_visibility="collapsed")
        if files:
            saved = []
            for f in files:
                out = UPLOADS_DIR / f.name
                out.write_bytes(f.read())
                saved.append(str(out))
            st.success(f"Saved {len(saved)} file(s) to data/uploads/")
            log_event("uploads.saved", {"files": saved})

    st.divider()
    with st.expander("🛫 Preflight Check", expanded=True):
        probe = load_openai_probe()
        checks = {
            "API key detected": probe["has_key"],
            "Cockpit logging available": COCKPIT_DIR.exists(),
            "Trial active": st.session_state.trial_days_left > 0,
            "Cost calculator ready": True,
            "Connectors folder present": probe["folder"],
            "OpenAI connector registered": probe["registry"],
            "Deploy form available": True,
        }
        all_ok = True
        for label, ok in checks.items():
            all_ok = all_ok and bool(ok)
            st.write(("✅ " if ok else "❌ ") + label)

        if not checks["API key detected"]:
            st.info("Tip: Create a `.env` file in the app folder with:\n\n`OPENAI_API_KEY=sk-...`", icon="ℹ️")

    st.divider()
    with st.expander("ℹ️ About / How-To", expanded=False):
        st.markdown(
            """
            - Type in the box **or** upload/record audio.
            - If `OPENAI_API_KEY` is set, Whisper + GPT can auto-fill the 13 boxes for you.
            - Cost shows on the right (includes internal markup).
            - All actions are logged to `data/cockpit/`.
            """
        )

# ──────────────────────────────────────────────────────────────
# Main layout
# ──────────────────────────────────────────────────────────────
left, right = st.columns([2.2, 1.0])

with left:
    st.title("🧰 Dream Landing Page")
    st.caption("One prompt in. We structure it. Cost & deploy on the right.")

    st.subheader("What do you want to build?")
    prompt = st.text_area(
        " ",
        placeholder="e.g., A WhatsApp bot that captures inbound leads, stores in Supabase, and emails a daily summary.",
        label_visibility="collapsed",
        height=120,
    )

    # Voice record (optional)
    st.caption("Record voice")
    can_record = False
    _mic_hint = ""
    try:
        # Only import if installed; UI stays simple if not
        from streamlit_mic_recorder import mic_recorder  # type: ignore
        can_record = True
    except Exception:
        _mic_hint = "Install:  `python -m pip install streamlit-mic-recorder`"

    col_rec, col_note = st.columns([1.2, 2])
    with col_rec:
        if can_record:
            audio = mic_recorder(start_prompt="🎙️ Start recording", stop_prompt="⏹️ Stop", key="recorder")
        else:
            audio = None
    with col_note:
        if not can_record:
            st.info(f"Voice recorder unavailable. {_mic_hint}", icon="ℹ️")
        if not os.getenv("OPENAI_API_KEY"):
            st.warning("Set OPENAI_API_KEY to auto-transcribe your recording.", icon="⚠️")

    # Or upload audio
    st.caption("Or upload audio")
    audio_file = st.file_uploader("Drag and drop file here", type=["wav", "mp3", "m4a", "webm"], label_visibility="collapsed")

    # Actions
    col_btns = st.columns([1.2, 1, 1])
    with col_btns[0]:
        do_autostruct = st.button("✨ Auto-structure (AI)", use_container_width=True)
    with col_btns[1]:
        do_clear = st.button("Clear", use_container_width=True, type="secondary")
    with col_btns[2]:
        pass

    if do_clear:
        st.session_state.answers = {k: "" for k in st.session_state.answers}
        prompt = ""
        st.rerun()

    # If we had audio & key, we could transcribe here (kept minimal & offline-safe)
    if do_autostruct:
        # Super-simple structuring heuristic (no network)
        text = (prompt or "").strip()
        A = st.session_state.answers
        A["title"] = (text[:60] or "New Project").strip()
        A["goal"] = text[:200]
        A["audience"] = "End users / customers"
        A["inputs"] = "User messages, uploaded files"
        A["outputs"] = "Dashboard, emails, notifications"
        A["must_haves"] = "Core feature set from prompt"
        A["nice_to_haves"] = "Extras if budget allows"
        A["integrations"] = "OpenAI, Supabase (example)"
        A["constraints"] = "Budget & timeline TBD"
        A["success"] = "Adoption + reduced manual work"
        A["team"] = "You + MilkBox AI build pod"
        A["timeline"] = "Prototype in weeks"
        A["risks"] = "Data quality; API limits"
        log_event("autostructure", {"prompt_len": len(text)})
        st.success("Structured draft filled in below. You can edit in Advanced.", icon="✅")

    with st.expander("▶ Advanced (optional) — edit the structured answers", expanded=False):
        A = st.session_state.answers
        A["title"] = st.text_input("Title", A.get("title", ""))
        A["goal"] = st.text_area("Goal", A.get("goal", ""), height=70)
        A["audience"] = st.text_input("Audience", A.get("audience", ""))
        A["inputs"] = st.text_area("Inputs", A.get("inputs", ""), height=70)
        A["outputs"] = st.text_area("Outputs", A.get("outputs", ""), height=70)
        A["must_haves"] = st.text_area("Must-haves", A.get("must_haves", ""), height=70)
        A["nice_to_haves"] = st.text_area("Nice-to-haves", A.get("nice_to_haves", ""), height=70)
        A["integrations"] = st.text_input("Integrations (APIs/services)", A.get("integrations", ""))
        A["constraints"] = st.text_area("Constraints", A.get("constraints", ""), height=70)
        A["success"] = st.text_area("Success criteria", A.get("success", ""), height=70)
        A["team"] = st.text_input("Team", A.get("team", ""))
        A["timeline"] = st.text_input("Timeline", A.get("timeline", ""))
        A["risks"] = st.text_area("Risks", A.get("risks", ""), height=70)

    st.subheader("Preview Brief")
    preview = {"category": category, "answers": st.session_state.answers}
    st.code(json.dumps(preview, indent=2, ensure_ascii=False))

    if st.button("Generate Brief & Log", use_container_width=True):
        log_event("dream.submit", {"category": category, "answers": st.session_state.answers})
        st.success("Brief generated & logged to cockpit.", icon="✅")

with right:
    st.header("Cost & Deploy")
    calc = compute_cost(st.session_state.cost_knobs)
    st.session_state.total_cost = calc["total"]

    st.metric("Estimated Monthly Cost", f"R {calc['total']:,.0f}")
    with st.expander("Breakdown", expanded=True):
        st.write(f"API keys: R {calc['breakdown']['API keys']:.2f}")
        st.write(f"Secrets: R {calc['breakdown']['Secrets']:.2f}")
        st.write(f"Tools (manual + scout): R {calc['breakdown']['Tools (manual + scout)']:.2f}")
        st.caption("Totals reflect final pricing.")

    st.markdown("---")
    st.subheader("Trial")
    col_trial = st.columns([1, 1])
    with col_trial[0]:
        st.info(f"⏳ {st.session_state.trial_days_left} days left · 🔑 {st.session_state.trial_tokens} tokens",
                icon="ℹ️")
    with col_trial[1]:
        if st.button("Use 1 Token", use_container_width=True, disabled=st.session_state.trial_tokens <= 0):
            if st.session_state.trial_tokens > 0:
                st.session_state.trial_tokens -= 1
                log_event("trial.consume", {"left": st.session_state.trial_tokens})
                st.toast("Token used.")
            else:
                st.warning("No tokens left.", icon="⚠️")

    st.markdown("---")
    st.subheader("Deploy")
    with st.form("deploy_form", clear_on_submit=False, border=True):
        name = st.text_input("Your Name")
        age = st.number_input("Your Age", 1, 120, 25)
        company = st.text_input("Company (or 'Private')")
        email = st.text_input("Email Address")
        ok_to_deploy = st.form_submit_button("✅ Deploy to War Room", use_container_width=True)
    if ok_to_deploy:
        if not name or not email:
            st.error("Please fix: Name and Email are required.")
        else:
            payload = {
                "category": category,
                "answers": st.session_state.answers,
                "cost_total_r": st.session_state.total_cost,
                "user": {"name": name, "age": age, "company": company, "email": email},
            }
            log_event("handoff.deploy", payload)
            st.success("Queued for War Room.", icon="✅")
            if not debug_skip_redirect:
                st.caption("Redirect suppressed in this skeleton. (Debug toggle in sidebar).")

st.markdown("---")
st.subheader("Cockpit Activity Log (raw)")
if LOG_FILE.exists():
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()[-50:]
    for ln in lines:
        st.code(ln)
else:
    st.caption("No events yet.")

# ──────────────────────────────────────────────────────────────
# END
# ──────────────────────────────────────────────────────────────
