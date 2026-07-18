"""History page for viewing saved focus sessions and progress charts."""

import streamlit as st

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
    """Render the history page with a table of past sessions and progress charts."""

    render_sidebar()

    st.title("📚 Session History")
    st.caption("Review your past focus sessions and see how your habits have evolved over time.")

    sessions = load_sessions()
    if not sessions:
        st.info("No session history yet. Complete a focus session to populate this page.")
        return

    st.subheader("🗂️ Past Sessions")
    table_rows = [
        {
            "Date": (analytics.parse_date(session.get("date")) or "Unknown"),
            "Duration": analytics.format_duration(analytics.session_minutes(session)),
            "Score": f"{analytics.session_score(session):.0f}%",
            "Pauses": analytics.session_pauses(session),
        }
        for session in analytics.recent_sessions(sessions, limit=len(sessions))
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    st.divider()

    history_df = analytics.to_dataframe(sessions)
    if not history_df.empty:
        daily_summary = build_daily_summary(history_df)
        weekly_summary = build_weekly_summary(history_df)

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
