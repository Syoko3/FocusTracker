"""Reusable sidebar navigation and quick-settings component."""

import streamlit as st

from services import analytics
from services.storage import streak_dates


def render_sidebar():
    """Render the app navigation sidebar plus quick goal and streak widgets."""
    
    st.sidebar.subheader("Today's Goal")
    goal_value = st.sidebar.text_input(
        "Goal",
        value=st.session_state.get("today_goal", ""),
        placeholder="Ex: Study 2 hours",
        key="today_goal",
    )
    if goal_value:
        st.sidebar.caption(f"Goal: {goal_value}")
    else:
        st.sidebar.caption("Set your goal for today.")

    streak = analytics.streak_from_dates(streak_dates())
    st.sidebar.metric("Current Streak", f"{streak} day{'s' if streak != 1 else ''}")
