# FocusTracker

- Created by Sohdai Yokokawa
- Project for Midnight Hackathon

---

## App Information



---

## App Structure

```
FocusTracker/
│
├── app.py                 # Main app
├── requirements.txt
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
│   ├── storage.py
│   └── analytics.py
│
└── data/
    └── sessions.json

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
streamlit run app.py
```
