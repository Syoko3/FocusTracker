"""Local JSON persistence for focus sessions and streak history.

Two files live under ``data/``:

* ``sessions.json`` — the list of recorded session dicts.
* ``streak.json`` — the set of dates that count toward the study streak.

The streak dates are stored separately so that *deleting* sessions never
resets the streak: before a session record is removed, its date is promoted
into ``streak.json`` and kept there.
"""

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_FILE = DATA_DIR / "sessions.json"
STREAK_FILE = DATA_DIR / "streak.json"


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
def load_sessions() -> List[Dict[str, Any]]:
    """Load all saved sessions from the local JSON file."""

    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _write_sessions(sessions: List[Dict[str, Any]]) -> None:
    """Persist the full list of sessions to disk."""

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as handle:
        json.dump(sessions, handle, indent=2)


def save_session(session: Dict[str, Any]) -> Dict[str, Any]:
    """Append a completed session to the local JSON storage file."""

    sessions = load_sessions()
    sessions.append(session)
    _write_sessions(sessions)
    return session


def delete_session(index: int) -> Optional[Dict[str, Any]]:
    """Delete a single session by its position in storage.

    The removed session's date is preserved in the streak history so the
    current streak is unaffected. Returns the removed session, or None if the
    index is out of range.
    """

    sessions = load_sessions()
    if not 0 <= index < len(sessions):
        return None

    removed = sessions.pop(index)
    record_streak_dates([removed.get("date")])
    _write_sessions(sessions)
    return removed


def delete_all_sessions() -> List[Dict[str, Any]]:
    """Delete every stored session, preserving all their streak dates first."""

    sessions = load_sessions()
    record_streak_dates(session.get("date") for session in sessions)
    _write_sessions([])
    return []


# ---------------------------------------------------------------------------
# Streak history
# ---------------------------------------------------------------------------
def load_streak_dates() -> List[str]:
    """Load the persisted set of streak-qualifying ISO date strings."""

    if not STREAK_FILE.exists():
        return []

    try:
        with STREAK_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return []

    if isinstance(data, dict):
        dates = data.get("dates", [])
    elif isinstance(data, list):
        dates = data
    else:
        return []

    return [value for value in dates if isinstance(value, str) and value]


def _write_streak_dates(dates: Iterable[str]) -> None:
    """Persist a de-duplicated, sorted set of streak dates."""

    STREAK_FILE.parent.mkdir(parents=True, exist_ok=True)
    unique_sorted = sorted({value for value in dates if value})
    with STREAK_FILE.open("w", encoding="utf-8") as handle:
        json.dump({"dates": unique_sorted}, handle, indent=2)


def record_streak_dates(dates: Iterable[str]) -> List[str]:
    """Add one or more ISO dates to the persisted streak history."""

    combined = set(load_streak_dates())
    combined.update(value for value in dates if value)
    _write_streak_dates(combined)
    return sorted(combined)


def streak_dates() -> List[str]:
    """All dates counting toward the streak: stored history plus live sessions."""

    session_dates = {
        session.get("date") for session in load_sessions() if session.get("date")
    }
    return sorted(set(load_streak_dates()) | session_dates)
