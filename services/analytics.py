"""Statistics helpers for summarizing stored focus sessions.

Sessions are plain dictionaries loaded from ``data/sessions.json``. Each record
follows the canonical storage format::

    {"date": "2026-07-18", "duration": 1500, "score": 92, "pause_count": 1}

where ``date`` is an ISO ``YYYY-MM-DD`` day, ``duration`` is the focused time in
**seconds**, ``score`` is a 0-100 focus score, and ``pause_count`` is how many
times the session was paused. Every helper is tolerant of missing or malformed
fields so a single bad record never breaks a page.
"""

from datetime import date, datetime, timedelta

import pandas as pd


# ---------------------------------------------------------------------------
# Per-session field accessors
# ---------------------------------------------------------------------------
def parse_date(value):
    """Return the calendar date for a session value, or None if unparseable."""

    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def session_seconds(session):
    """Return a session's focused duration in seconds (0 if invalid)."""

    try:
        return max(float(session.get("duration", 0)), 0.0)
    except (TypeError, ValueError):
        return 0.0


def session_minutes(session):
    """Return a session's focused duration in minutes."""

    return session_seconds(session) / 60


def session_score(session):
    """Return a session's focus score (0 if invalid)."""

    try:
        return float(session.get("score", 0))
    except (TypeError, ValueError):
        return 0.0


def session_pauses(session):
    """Return how many times a session was paused (0 if invalid)."""

    try:
        return int(session.get("pause_count", 0))
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# Aggregate statistics
# ---------------------------------------------------------------------------
def total_sessions(sessions):
    """Total number of recorded sessions."""

    return len(sessions)


def total_study_seconds(sessions):
    """Total focused time across all sessions, in seconds."""

    return sum(session_seconds(session) for session in sessions)


def total_study_minutes(sessions):
    """Total focused time across all sessions, in minutes."""

    return total_study_seconds(sessions) / 60


def average_score(sessions):
    """Mean focus score across all sessions (0 when there are none)."""

    if not sessions:
        return 0.0
    return sum(session_score(session) for session in sessions) / len(sessions)


def total_pauses(sessions):
    """Total number of pauses across all sessions."""

    return sum(session_pauses(session) for session in sessions)


def average_pauses(sessions):
    """Mean pauses per session (0 when there are none)."""

    if not sessions:
        return 0.0
    return total_pauses(sessions) / len(sessions)


def sessions_on(sessions, day):
    """Return the sessions recorded on a given calendar day."""

    return [session for session in sessions if parse_date(session.get("date")) == day]


def daily_average_score(sessions, day=None):
    """Mean focus score for a single day (defaults to today)."""

    day = day or date.today()
    todays = sessions_on(sessions, day)
    if not todays:
        return 0.0
    return sum(session_score(session) for session in todays) / len(todays)


def _streak_from_days(days, today):
    """Count consecutive days ending today or yesterday from a set of dates."""

    days = {day for day in days if day is not None}
    if not days:
        return 0

    if today in days:
        cursor = today
    elif (today - timedelta(days=1)) in days:
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def current_streak(sessions, today=None):
    """Consecutive days with at least one session, ending today or yesterday.

    Returns 0 when the most recent session is older than yesterday, so the
    number always reflects an *active* streak rather than the longest ever.
    """

    today = today or date.today()
    days = {parse_date(session.get("date")) for session in sessions}
    return _streak_from_days(days, today)


def streak_from_dates(dates, today=None):
    """Current streak computed from a bare iterable of dates or ISO strings.

    Used when streak history is tracked independently of session records (so
    that deleting sessions does not reset the streak).
    """

    today = today or date.today()
    days = {parse_date(value) for value in dates}
    return _streak_from_days(days, today)


def recent_sessions(sessions, limit=5):
    """Return the most recent sessions, newest first (by date)."""

    ordered = sorted(
        sessions,
        key=lambda session: parse_date(session.get("date")) or date.min,
        reverse=True,
    )
    return ordered[:limit]


def summarize(sessions):
    """Bundle the headline dashboard statistics into a single dict."""

    return {
        "total_sessions": total_sessions(sessions),
        "total_study_seconds": total_study_seconds(sessions),
        "total_study_minutes": total_study_minutes(sessions),
        "average_score": average_score(sessions),
        "today_score": daily_average_score(sessions),
        "current_streak": current_streak(sessions),
        "total_pauses": total_pauses(sessions),
        "average_pauses": average_pauses(sessions),
    }


# ---------------------------------------------------------------------------
# Presentation helpers
# ---------------------------------------------------------------------------
def format_duration(minutes):
    """Format a duration given in minutes into a readable string."""

    if minutes <= 0:
        return "0 min"

    hours = int(minutes // 60)
    remaining_minutes = int(round(minutes % 60))

    if hours and remaining_minutes:
        return f"{hours}h {remaining_minutes}m"
    if hours:
        return f"{hours}h"
    return f"{remaining_minutes} min"


def to_dataframe(sessions):
    """Build a tidy DataFrame of sessions for the chart helpers.

    Returns columns ``Date`` (datetime), ``Duration (min)``, ``Score`` and
    ``Pauses``, with unparseable-date rows dropped and rows sorted oldest-first.
    """

    rows = [
        {
            "Date": parse_date(session.get("date")),
            "Duration (min)": round(session_minutes(session), 1),
            "Score": round(session_score(session), 1),
            "Pauses": session_pauses(session),
        }
        for session in sessions
    ]

    frame = pd.DataFrame(rows, columns=["Date", "Duration (min)", "Score", "Pauses"])
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    frame = frame.dropna(subset=["Date"])
    return frame.sort_values("Date").reset_index(drop=True)
