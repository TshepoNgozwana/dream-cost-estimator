import streamlit as st

def app_footer():
    st.markdown("""
        <hr>
        <p style='text-align:center; font-size:13px; color:gray;'>
            © 2025 Dream Landing — Built by Team MilkBoxAI | Contact: Christo
        </p>
    """, unsafe_allow_html=True)

st.set_page_config(page_title="About / How-To")

st.title("ℹ️ About / How-To")
st.markdown("""
### Purpose
This app helps users scope and cost out small web/app ideas — from concept to estimate.

### Quick Start
1. Go to the **Wizard** page.
2. Fill in the 13 questions.
3. See the live cost tally and summary.

### Cost Model
- Base: 29  
- Auth: +4  
- Payments: +8  
- AI: +10 (any AI)  
- Integrations: +2 each (max +6)  
- Content: +3 if “Need copy”.

### Logging
All actions append to `data/cockpit/events.jsonl` for traceability.

### Contact
For project approvals, please contact **Christo Swanepoel (MilkBox)**.
""")

app_footer()