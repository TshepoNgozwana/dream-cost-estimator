import streamlit as st
import json
from pathlib import Path

st.markdown("""
<style>
.expanderHeader {
    font-weight: 600;
    color: #0078d4;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Indicators Debug", page_icon="📊", layout="wide")

st.title("📊 Indicators Debug Panel")
st.caption("Quick view of the latest indicator updates from Cockpit logs.")

LOG_PATH = Path("data/cockpit/events.jsonl")

# ──────────────────────────────────────────────────────────────
# Load and Filter Cockpit Events
# ──────────────────────────────────────────────────────────────
def load_indicator_events(limit: int = 10):
    """Load the most recent indicator.update events."""
    if not LOG_PATH.exists():
        return []

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    events = []
    for line in reversed(lines):
        try:
            evt = json.loads(line)
            if evt.get("action") == "indicator.update":
                events.append(evt)
            if len(events) >= limit:
                break
        except json.JSONDecodeError:
            continue
    return events

# ──────────────────────────────────────────────────────────────
# Display Section
# ──────────────────────────────────────────────────────────────
events = load_indicator_events()

if not events:
    st.info("No indicator updates found yet. Interact with the Wizard first to generate logs.")
else:
    st.success(f"Showing {len(events)} most recent indicator updates:")

    for evt in events:
        with st.expander(f"🕒 {evt['ts']}", expanded=False):
            st.json(evt["payload"])


