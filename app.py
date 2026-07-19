"""Main entry point for the FocusTracker Streamlit application.

This module defines the app-wide navigation (with titled, icon-labelled
sections) and renders the "Home" landing page, which introduces the core
workflow: starting a focus session, reviewing the dashboard, and viewing
session history while keeping data local.
"""

import json
from pathlib import Path

import streamlit as st

from components.cards import render_metric_row
from components.sidebar import render_sidebar


def load_sessions():
    """Load stored focus sessions from the local JSON file.

    Returns:
        list[dict]: A list of saved session dictionaries, or an empty list if the
        data file is missing or invalid.
    """

    data_file = Path("data/sessions.json")
    if not data_file.exists():
        return []

    try:
        with open(data_file, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return []


def render_home_page():
    """Render the landing page content for the main app."""

    render_sidebar()

    sessions = load_sessions()
    total_sessions = len(sessions)
    total_minutes = sum(session.get("duration", 0) for session in sessions) / 60

    if total_sessions > 0:
        average_score = round(
            sum(session.get("score", 0) for session in sessions) / total_sessions
        )
    else:
        average_score = 0

    st.title("🧠 FocusTracker")
    st.caption(
        "AI-powered productivity tracking that keeps your study data private."
    )
    st.divider()

    st.markdown(
        """
    ### Welcome!

    FocusTracker helps students improve their focus without uploading their personal study data. Unlike many productivity apps, all information is processed and stored locally.

    ### Features

    - ⏱️ Focus sessions
    - 🤖 AI focus scoring
    - 📈 Progress dashboard
    - 📚 Session history

    Use the sidebar to start a focus session or view your study history.

    - 🏠 Dashboard
    - ⏱️ Focus Session
    - 📚 History
    - 🔒 Privacy
    """
    )

    st.divider()
    st.subheader("📊 Quick Stats")

    render_metric_row(
        [
            {"title": "Completed Sessions", "value": total_sessions},
            {"title": "Study Time", "value": f"{total_minutes:.0f} min"},
            {"title": "Average Focus Score", "value": f"{average_score}%"},
        ]
    )

    st.divider()
    st.subheader("🔒 Privacy Matters")
    st.success(
        """
    ✔ No login required

    ✔ No cloud storage

    ✔ Data stays on your computer

    ✔ AI scoring happens locally

    ✔ You control your own data
    """
    )

    st.markdown(
        """
    ### How your data is handled

    - **Local-only storage.** Sessions are saved to a JSON file on this device.
    - **No accounts.** Nothing is uploaded, synced, or shared with a server.
    - **Local scoring.** Focus scores are computed on-device, never sent away.
    - **Your control.** Delete the local data file at any time to remove your history.
    """
    )


def main():
    """Configure app navigation and run the selected FocusTracker page."""

    st.set_page_config(page_title="FocusTracker", page_icon="🧠", layout="wide")

    pages = [
        st.Page(render_home_page, title="Home", icon="🏠", default=True),
        st.Page("pages/Dashboard.py", title="Dashboard", icon="📊"),
        st.Page("pages/Focus_Session.py", title="Focus Session", icon="⏱️"),
        st.Page("pages/History.py", title="History", icon="📚"),
    ]

    st.navigation(pages).run()


if __name__ == "__main__":
    main()
