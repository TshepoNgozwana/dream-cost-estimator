# Dream Cost Estimator
Streamlit-based interactive landing page that guides users through a 13-question wizard, calculates a live cost estimate, provides a summary with actionable next steps, and logs user interactions for analysis. Mobile-first design, real-time updates, and clean code practices.

## Use Case:
Ideal for product managers, startups, and internal teams to plan project costs and feature selections without manual calculations.

## Features
13-Question Wizard:
- Collects project details including industry, goal, audience size, AI features, integrations, and budget preferences.

## Real-Time Cost Tally:
Live calculation of estimated project cost based on user inputs.

## Summary Screen:
Displays project info, estimated cost, and selected features. Supports copying to clipboard, generating a QR code, and downloading a .txt summary.

## Cockpit Logging (JSONL):
Append-only logging of key events: page views, wizard start, answer changes, wizard submission, and QR generation.

## Mobile-First Design:
Optimized layout for small screens (iPhone SE ~375px) and desktop.

## Tech Stack

- Python 3.13+
- Streamlit – interactive web UI
- Pydantic – data validation
- Python-Dateutil – date/time management
- qrcode[pil] – QR code generation
- JSONL – append-only logging

## Installation & Setup
1. Clone the Repository
- git clone git@github.com:TshepoNgozwana/dream-cost-estimator.git
- cd dream-cost-estimator

2. Create Virtual Environment
- python -m venv .venv
- .venv\Scripts\activate  # Windows
- source .venv/bin/activate  # macOS/Linux

3. Install Dependencies
- pip install -U pip wheel
- pip install streamlit pydantic python-dateutil qrcode[pil]

4. Environment Variables
- Create .env.local (git-ignored) for API keys or Supabase integration (optional):
- SUPABASE_URL=<your-supabase-url>
- SUPABASE_ANON_KEY=<your-supabase-anon-key>

## Usage
Run the Streamlit app:
- streamlit run streamlit_app.py
- Use the sidebar to navigate between:
1. About / How-To
2. Wizard (13 questions)
3. Summary / QR / Copy
- Fill out the wizard → see live cost updates in sidebar
- Submit wizard → logs saved in data/cockpit/events.jsonl

## Project Structure
- dream-cost-estimator/
- │
- ├─ streamlit_app.py       # Entry point
- ├─ pages/
- │   ├─ 01_About_and_HowTo.py
- │   ├─ 02_Wizard.py
- │   └─ 03_Summary.py
- ├─ data/
- │   └─ cockpit/           # Append-only JSONL logs
- ├─ .venv/                 # Virtual environment
- └─ requirements.txt       # Optional dependency list

## Logging & Analytics
All key user actions are logged in data/cockpit/events.jsonl in JSON Lines format:
- {
  "ts": "2025-10-01T13:00:00+02:00",
  "user": "local-dev",
  "tool": "dream-landing",
  "action": "submit_wizard",
  "payload": {"answers_count": 13, "est_cost": 29.0},
  "session": "<uuid4>",
  "notes": ""
}

## Events captured:
page_view, start_wizard, answer_change, submit_wizard, generate_qr.

## Author
Tshepo Ngozwana