# FocusTracker

- Created by Sohdai Yokokawa
- Project for Midnight Hackathon

---

## App Information

Many productivity apps collect personal information, such as study schedules, work hours, daily routines, and time spent on tasks. This information is often uploaded to cloud servers, where users have limited control over how it is stored or analyzed. FocusTracker helps users to improve their focus without sending any of their study data to the external servers. The user flow is to open the app, then go to the Dashboard page, then go to the focus session page and start the focus session, and then study. After the user ends studying, they click the End Session button, then it calculates the AI focus score, then saves the session locally, then update in the Dashboard page, then the user can view history & progress. They can either download the report of the sessions or delete the sessions.

---

## App Structure

```
FocusTracker/
│
├── app.py                      # Main app
├── conftest.py                 # Pytest configuration
├── requirements.txt            # Needed packages
├── .gitignore
│
├── pages/
│   ├── Dashboard.py            # Focus summaries & recent sessions
│   ├── Focus_Session.py        # Starting, pausing, ending, scoring, and saving sessions
│   └── History.py              # Viewing saved focus sessions and progress charts
│
├── components/
│   ├── timer.py                # Reusable timer UI for the focus-session page
│   ├── charts.py               # Reusable chart helpers for dashboard and history pages
│   ├── cards.py                # Reusable metric card helpers for dashboard-style summaries
│   └── sidebar.py              # Reusable sidebar navigation and quick-settings component
│
├── services/
│   ├── ai.py                   # Local AI-style helpers for estimating a focus score from session behavior
│   ├── analytics.py            # Statistics helpers for summarizing stored focus sessions
│   ├── storage.py              # Local JSON persistence for focus sessions and streak history
│   └── report.py               # Helpers for exporting focus-session reports (PDF, CSV, JSON, plain text)
│
├── data/
│   ├── sessions.json           # The list of recorded session dicts
│   └── streak.json             # The set of dates that count toward the study streak
│
└── tests/                      # Pytests for testing the services/
    ├── test_ai.py
    ├── test_analytics.py
    ├── test_storage.py
    └── test_report.py

```

---

## Setup Instructions

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # MacOS/Linux
.venv\Scripts\activate      # Windows

# Install packages
pip install -r requirements.txt

# Run the app
python -m streamlit run app.py

# Test the app
pytest tests/
```
