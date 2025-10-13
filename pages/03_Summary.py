import streamlit as st
import json, base64, qrcode
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone
import uuid, os

def app_footer():
    st.markdown("""
        <hr>
        <p style='text-align:center; font-size:13px; color:gray;'>
            © 2025 Dream Landing — Built by Team MilkBoxAI | Contact: Christo
        </p>
    """, unsafe_allow_html=True)

def qr_png_base64(text: str) -> str:
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

LOG_PATH = Path("data/cockpit/events.jsonl")
os.makedirs(LOG_PATH.parent, exist_ok=True)

def _log(event, payload=None):
    evt = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "user": "local-dev",
        "tool": "dream-landing",
        "action": event,
        "payload": payload or {},
        "session": str(uuid.uuid4()),
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evt) + "\n")

st.title("📋 Project Summary & Export")
st.markdown("Review your current project summary and export options.")

summary = {
    "title": st.session_state.get("answers", {}).get("title", "Untitled"),
    "goal": st.session_state.get("answers", {}).get("goal", ""),
    "estimated_cost_r": st.session_state.get("total_cost", 0),
}

st.code(json.dumps(summary, indent=2, ensure_ascii=False))

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("📋 Copy Summary"):
        st.success("Copied to clipboard (simulated).")
        _log("summary.copy", summary)
with col2:
    if st.button("📱 Generate QR Code"):
        img_b64 = qr_png_base64(json.dumps(summary))
        st.image("data:image/png;base64," + img_b64, caption="Scan to view summary")
        _log("summary.qr_generated", summary)

app_footer()