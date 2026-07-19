# FocusTracker

- Created by Sohdai Yokokawa
- Project for Midnight Hackathon

---

## App Overview

Many productivity apps collect personal information, such as study schedules, work hours, daily routines, and time spent on tasks. This information is often uploaded to cloud servers, where users have limited control over how it is stored or analyzed. FocusTracker helps users to improve their focus without sending any of their study data to the external servers.

* User Flow: Open App --> Dashboard --> Start Focus Session --> Study --> End Session --> Calculate Focus Score --> Save Session Locally --> Update Dashboard --> View History & Progress

---

## App Structure

```
FocusTracker/
│
├── app.py                 # Main app
├── requirements.txt
├── .gitignore
│
├── pages/
│   ├── Dashboard.py
│   ├── Focus_Session.py
│   ├── History.py
│   └── Privacy.py
│
├── components/
│   ├── timer.py
│   ├── charts.py
│   ├── cards.py
│   └── sidebar.py
│
├── services/
│   ├── ai.py
│   ├── analytics.py
│   ├── storage.py
│   └── report.py
│
├── data/
│   ├── sessions.json
│   └── streak.json
│
└── tests/
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
