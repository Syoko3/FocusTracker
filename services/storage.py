"""Local JSON persistence helpers for saving focus-session records."""

import json
from pathlib import Path
from typing import Any, Dict, List


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "sessions.json"


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


def save_session(session: Dict[str, Any]) -> Dict[str, Any]:
    """Append a completed session to the local JSON storage file."""

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    sessions = load_sessions()
    sessions.append(session)

    with DATA_FILE.open("w", encoding="utf-8") as handle:
        json.dump(sessions, handle, indent=2)

    return session
