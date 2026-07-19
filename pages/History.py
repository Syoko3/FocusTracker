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
from services import analytics, report
from services.storage import delete_all_sessions, delete_session, load_sessions


def _session_label(index, session):
    """Build a readable option label for the delete selector."""

    day = analytics.parse_date(session.get("date"))
    day_text = day.isoformat() if day else "Unknown date"
    title = session.get("title", "Focus Session")
    return f"{day_text} — {title} ({analytics.session_score(session):.0f}%)"


def render_export_and_manage(sessions):
    """Render download buttons and delete controls for the stored sessions."""

    st.divider()
    st.subheader("⬇️ Export & Manage")
    st.caption("Download your data or clean it up — deleting sessions never resets your streak.")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download all (PDF)",
            data=report.sessions_to_pdf(sessions),
            file_name="focus_sessions.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "Download all (JSON)",
            data=report.sessions_to_json(sessions),
            file_name="focus_sessions.json",
            mime="application/json",
            use_container_width=True,
        )

    latest = analytics.recent_sessions(sessions, limit=1)
    if latest:
        st.download_button(
            "Download latest session report (PDF)",
            data=report.session_summary_pdf(latest[0]),
            file_name="latest_session_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("**Delete a session**")
    options = list(range(len(sessions)))
    selected_index = st.selectbox(
        "Choose a session to delete",
        options,
        format_func=lambda index: _session_label(index, sessions[index]),
    )
    if st.button("Delete selected session"):
        delete_session(selected_index)
        st.success("Session deleted. Your streak is preserved.")
        st.rerun()

    with st.expander("Delete all sessions"):
        confirm = st.checkbox("Yes, permanently delete all my sessions")
        if st.button("Delete everything", disabled=not confirm):
            delete_all_sessions()
            st.success("All sessions deleted. Your streak is preserved.")
            st.rerun()


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

    render_export_and_manage(sessions)


main()
