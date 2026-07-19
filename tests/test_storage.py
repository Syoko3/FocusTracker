"""Tests for services.storage local JSON persistence.

Every test redirects ``storage.DATA_FILE`` to a temporary path so the real
``data/sessions.json`` is never touched.
"""

import json

import pytest

from services import storage


@pytest.fixture
def data_file(tmp_path, monkeypatch):
    """Point storage at an isolated temp file and return its path."""

    path = tmp_path / "nested" / "sessions.json"
    monkeypatch.setattr(storage, "DATA_FILE", path)
    return path


def test_load_returns_empty_when_file_missing(data_file):
    assert not data_file.exists()
    assert storage.load_sessions() == []


def test_load_returns_empty_on_invalid_json(data_file):
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text("{not valid json", encoding="utf-8")
    assert storage.load_sessions() == []


def test_load_returns_empty_when_top_level_is_not_a_list(data_file):
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps({"date": "2026-07-18"}), encoding="utf-8")
    assert storage.load_sessions() == []


def test_load_reads_existing_sessions(data_file):
    sessions = [{"date": "2026-07-18", "duration": 1500, "score": 92, "pause_count": 1}]
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps(sessions), encoding="utf-8")
    assert storage.load_sessions() == sessions


def test_save_creates_file_and_parent_dir(data_file):
    session = {"date": "2026-07-18", "duration": 1500, "score": 92, "pause_count": 1}
    returned = storage.save_session(session)

    assert returned == session
    assert data_file.exists()
    assert storage.load_sessions() == [session]


def test_save_appends_to_existing_sessions(data_file):
    first = {"date": "2026-07-17", "duration": 1800, "score": 87, "pause_count": 2}
    second = {"date": "2026-07-18", "duration": 1500, "score": 92, "pause_count": 1}

    storage.save_session(first)
    storage.save_session(second)

    assert storage.load_sessions() == [first, second]


def test_saved_file_is_valid_json_list(data_file):
    session = {"date": "2026-07-18", "duration": 1500, "score": 92, "pause_count": 1}
    storage.save_session(session)

    on_disk = json.loads(data_file.read_text(encoding="utf-8"))
    assert isinstance(on_disk, list)
    assert on_disk == [session]


# ---------------------------------------------------------------------------
# Deletion + streak preservation
# ---------------------------------------------------------------------------
@pytest.fixture
def storage_files(tmp_path, monkeypatch):
    """Isolate both the sessions and streak files to a temp directory."""

    sessions_path = tmp_path / "sessions.json"
    streak_path = tmp_path / "streak.json"
    monkeypatch.setattr(storage, "DATA_FILE", sessions_path)
    monkeypatch.setattr(storage, "STREAK_FILE", streak_path)
    return sessions_path, streak_path


def make(day, duration=1500, score=90, pauses=1):
    return {"date": day, "duration": duration, "score": score, "pause_count": pauses}


def test_load_streak_dates_empty_when_missing(storage_files):
    assert storage.load_streak_dates() == []


def test_load_streak_dates_empty_on_invalid(storage_files):
    _, streak_path = storage_files
    streak_path.write_text("{bad json", encoding="utf-8")
    assert storage.load_streak_dates() == []


def test_record_streak_dates_dedupes_and_sorts(storage_files):
    storage.record_streak_dates(["2026-07-18", "2026-07-17"])
    storage.record_streak_dates(["2026-07-18", "2026-07-16"])  # 18 repeats
    assert storage.load_streak_dates() == ["2026-07-16", "2026-07-17", "2026-07-18"]


def test_streak_dates_unions_history_and_live_sessions(storage_files):
    storage.save_session(make("2026-07-18"))
    storage.record_streak_dates(["2026-07-10"])  # a date with no live session
    assert storage.streak_dates() == ["2026-07-10", "2026-07-18"]


def test_delete_session_removes_record_and_preserves_its_date(storage_files):
    storage.save_session(make("2026-07-17"))
    storage.save_session(make("2026-07-18"))

    removed = storage.delete_session(0)

    assert removed["date"] == "2026-07-17"
    assert [s["date"] for s in storage.load_sessions()] == ["2026-07-18"]
    # The deleted date survives in the streak history.
    assert "2026-07-17" in storage.load_streak_dates()
    # ...and is still counted by streak_dates().
    assert set(storage.streak_dates()) == {"2026-07-17", "2026-07-18"}


def test_delete_session_out_of_range_returns_none(storage_files):
    storage.save_session(make("2026-07-18"))
    assert storage.delete_session(5) is None
    assert storage.delete_session(-1) is None
    assert len(storage.load_sessions()) == 1


def test_delete_all_sessions_clears_but_keeps_streak_dates(storage_files):
    for day in ("2026-07-16", "2026-07-17", "2026-07-18"):
        storage.save_session(make(day))

    storage.delete_all_sessions()

    assert storage.load_sessions() == []
    assert storage.load_streak_dates() == ["2026-07-16", "2026-07-17", "2026-07-18"]
    # Even with zero sessions, the streak dates remain available.
    assert storage.streak_dates() == ["2026-07-16", "2026-07-17", "2026-07-18"]


def test_deleting_all_sessions_does_not_reset_the_streak(storage_files):
    from datetime import date

    from services import analytics

    today = date(2026, 7, 18)
    for day in ("2026-07-16", "2026-07-17", "2026-07-18"):
        storage.save_session(make(day))

    before = analytics.streak_from_dates(storage.streak_dates(), today=today)
    storage.delete_all_sessions()
    after = analytics.streak_from_dates(storage.streak_dates(), today=today)

    assert before == 3
    assert after == before  # streak is preserved through deletion
