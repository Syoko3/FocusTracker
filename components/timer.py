"""Reusable timer UI for the focus-session page."""

import time
from datetime import datetime

import streamlit as st

from services import report
from services.ai import calculate_focus_score
from services.storage import save_session


def initialize_timer_state():
    """Initialize the timer state keys needed by the focus-session workflow."""

    defaults = {
        "session_active": False,
        "session_paused": False,
        "session_started_at": None,
        "session_elapsed": 0,
        "pause_count": 0,
        "session_title": "Focus Session",
        "session_completed": False,
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def format_duration(seconds):
    """Format seconds into a mm:ss string."""

    minutes, remainder = divmod(int(seconds), 60)
    return f"{minutes:02d}:{remainder:02d}"


def get_elapsed_seconds():
    """Return the elapsed time for the current session."""

    if not st.session_state.session_active:
        return st.session_state.session_elapsed

    if st.session_state.session_paused:
        return st.session_state.session_elapsed

    if st.session_state.session_started_at is None:
        return st.session_state.session_elapsed

    return int(
        st.session_state.session_elapsed
        + (time.time() - st.session_state.session_started_at)
    )


def start_timer():
    """Start a new focus session and reset the timer values."""

    st.session_state.session_active = True
    st.session_state.session_paused = False
    st.session_state.session_started_at = time.time()
    st.session_state.session_elapsed = 0
    st.session_state.pause_count = 0
    st.session_state.session_completed = False


def pause_timer():
    """Pause the active session and preserve the elapsed time."""

    if not st.session_state.session_active or st.session_state.session_paused:
        return

    st.session_state.session_elapsed = get_elapsed_seconds()
    st.session_state.session_started_at = None
    st.session_state.session_paused = True
    st.session_state.pause_count += 1


def resume_timer():
    """Resume a paused session."""

    if not st.session_state.session_active or not st.session_state.session_paused:
        return

    st.session_state.session_started_at = time.time()
    st.session_state.session_paused = False


def end_timer():
    """End the session, calculate the score, and save it locally."""

    if not st.session_state.session_active and not st.session_state.session_elapsed:
        st.info("Start a session before ending it.")
        return

    elapsed_seconds = get_elapsed_seconds()
    duration_seconds = int(round(elapsed_seconds))
    # The scoring heuristic works in minutes; storage keeps the canonical seconds.
    duration_minutes = max(1, round(duration_seconds / 60, 2))
    score = calculate_focus_score(duration_minutes, st.session_state.pause_count)
    completed_at = datetime.now()

    session_payload = {
        "title": st.session_state.session_title or "Focus Session",
        "date": completed_at.date().isoformat(),
        "timestamp": completed_at.isoformat(),
        "duration": duration_seconds,
        "score": score,
        "pause_count": st.session_state.pause_count,
        "notes": f"Paused {st.session_state.pause_count} times during the session.",
    }

    save_session(session_payload)

    st.session_state.session_active = False
    st.session_state.session_paused = False
    st.session_state.session_started_at = None
    st.session_state.session_elapsed = 0
    st.session_state.session_completed = True
    st.session_state.last_session = session_payload


def render_timer_ui():
    """Render the full timer UI and handle the session workflow."""

    initialize_timer_state()

    session_title = st.text_input(
        "Session title",
        value=st.session_state.session_title,
        placeholder="e.g. Calculus revision",
    )
    st.session_state.session_title = session_title

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Start Session", use_container_width=True):
            start_timer()
    with col2:
        pause_label = "Resume Session" if st.session_state.session_paused else "Pause Session"
        pause_disabled = not st.session_state.session_active
        if st.button(pause_label, use_container_width=True, disabled=pause_disabled):
            if st.session_state.session_paused:
                resume_timer()
            else:
                pause_timer()
    with col3:
        end_disabled = not st.session_state.session_active and not st.session_state.session_elapsed
        if st.button("End Session", use_container_width=True, disabled=end_disabled):
            end_timer()

    st.divider()
    elapsed_seconds = get_elapsed_seconds()
    st.metric("Elapsed Time", format_duration(elapsed_seconds))
    st.metric("Pause Count", st.session_state.pause_count)

    if st.session_state.session_active:
        if st.session_state.session_paused:
            st.info("The session is paused. Press Resume Session to continue.")
        else:
            st.success("Session is running. Stay focused and keep the timer going.")
            time.sleep(1)
            st.rerun()
    elif st.session_state.session_completed and st.session_state.get("last_session"):
        render_completed_session(st.session_state.last_session)
    else:
        st.info("No active session right now. Press Start Session to begin.")


def render_completed_session(session):
    """Show the just-finished session with a downloadable report."""

    st.divider()
    st.success(
        f"Session saved! Score: {session['score']}% "
        f"over {format_duration(session['duration'])}."
    )
    st.download_button(
        "Download this session report (PDF)",
        data=report.session_summary_pdf(session),
        file_name="session_report.pdf",
        mime="application/pdf",
    )
    if st.button("View Dashboard"):
        st.switch_page("pages/Dashboard.py")
