"""Dashboard page for displaying focus summaries and recent sessions."""

import pandas as pd
import streamlit as st

from components.cards import render_metric_row
from components.charts import (
    build_daily_summary,
    build_weekly_summary,
    render_daily_study_chart,
    render_focus_trend_chart,
    render_weekly_progress_chart,
)
from components.sidebar import render_sidebar
from services import analytics
from services.storage import load_sessions


def main():
    """Render the dashboard page with summary metrics and recent sessions."""

    render_sidebar()

    st.title("📊 Dashboard")
    st.caption("A quick snapshot of today's focus performance and your recent sessions.")

    sessions = load_sessions()
    stats = analytics.summarize(sessions)
    streak = stats["current_streak"]

    render_metric_row(
        [
            {"title": "Today's Focus Score", "value": f"{stats['today_score']:.0f}%"},
            {"title": "Total Study Time", "value": analytics.format_duration(stats["total_study_minutes"])},
            {"title": "Number of Sessions", "value": stats["total_sessions"]},
            {"title": "Current Streak", "value": f"{streak} day{'s' if streak != 1 else ''}"},
        ]
    )

    st.divider()
    st.subheader("🕘 Recent Sessions")

    recent = analytics.recent_sessions(sessions, limit=5)
    if recent:
        recent_rows = [
            {
                "Date": (analytics.parse_date(session.get("date")) or "Unknown"),
                "Duration": analytics.format_duration(analytics.session_minutes(session)),
                "Score": f"{analytics.session_score(session):.0f}%",
                "Pauses": analytics.session_pauses(session),
            }
            for session in recent
        ]
        st.dataframe(pd.DataFrame(recent_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No focus sessions have been recorded yet. Start one to see your dashboard fill up.")

    history_df = analytics.to_dataframe(sessions)
    if not history_df.empty:
        daily_summary = build_daily_summary(history_df)
        weekly_summary = build_weekly_summary(history_df)

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 Daily Study Time")
            render_daily_study_chart(daily_summary)
        with col2:
            st.subheader("🎯 Focus Score Trend")
            render_focus_trend_chart(daily_summary)

        st.subheader("📅 Weekly Progress")
        render_weekly_progress_chart(weekly_summary)


main()
