"""Tests for services.report export helpers."""

import csv
import io
import json

import pytest

from services import report


def make_session(day="2026-07-18", duration=1500, score=92, pauses=1, title="Calc"):
    return {
        "date": day,
        "duration": duration,
        "score": score,
        "pause_count": pauses,
        "title": title,
    }


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------
def test_csv_has_header_and_one_row_per_session():
    sessions = [make_session("2026-07-18"), make_session("2026-07-17")]
    rows = list(csv.reader(io.StringIO(report.sessions_to_csv(sessions))))
    assert rows[0] == report.CSV_COLUMNS
    assert len(rows) == 1 + len(sessions)  # header + rows


def test_csv_converts_duration_seconds_to_minutes():
    csv_text = report.sessions_to_csv([make_session(duration=1500, score=92, pauses=1)])
    row = list(csv.DictReader(io.StringIO(csv_text)))[0]
    assert row["Duration (min)"] == "25.0"
    assert row["Score"] == "92"
    assert row["Pauses"] == "1"
    assert row["Title"] == "Calc"


def test_csv_of_empty_sessions_is_header_only():
    rows = list(csv.reader(io.StringIO(report.sessions_to_csv([]))))
    assert rows == [report.CSV_COLUMNS]


def test_csv_handles_missing_fields_gracefully():
    csv_text = report.sessions_to_csv([{}])
    row = list(csv.DictReader(io.StringIO(csv_text)))[0]
    assert row["Date"] == ""
    assert row["Duration (min)"] == "0.0"
    assert row["Score"] == "0"
    assert row["Title"] == "Focus Session"


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------
def test_json_round_trips_to_original_sessions():
    sessions = [make_session("2026-07-18"), make_session("2026-07-17")]
    assert json.loads(report.sessions_to_json(sessions)) == sessions


def test_json_of_empty_sessions():
    assert json.loads(report.sessions_to_json([])) == []


# ---------------------------------------------------------------------------
# Single-session text report
# ---------------------------------------------------------------------------
def test_session_summary_text_contains_key_fields():
    text = report.session_summary_text(make_session(duration=1500, score=92, pauses=1, title="Calc"))
    assert "Calc" in text
    assert "2026-07-18" in text
    assert "25 min" in text  # 1500s formatted from minutes
    assert "92%" in text
    assert "Pauses:   1" in text


def test_session_summary_text_handles_missing_fields():
    text = report.session_summary_text({})
    assert "Focus Session" in text
    assert "Unknown" in text
    assert "0%" in text


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
def test_sessions_pdf_is_valid_pdf_bytes():
    sessions = [make_session("2026-07-18"), make_session("2026-07-17")]
    data = report.sessions_to_pdf(sessions)
    assert isinstance(data, (bytes, bytearray))
    assert data.startswith(b"%PDF-")
    assert data.rstrip().endswith(b"%%EOF")
    assert len(data) > 500


def test_sessions_pdf_embeds_chart_content():
    sessions = [make_session("2026-07-18"), make_session("2026-07-17")]
    data = report.sessions_to_pdf(sessions)
    assert b"/XObject" in data


def test_sessions_pdf_handles_empty_sessions():
    data = report.sessions_to_pdf([])
    assert data.startswith(b"%PDF-")


def test_session_summary_pdf_is_valid_pdf_bytes():
    data = report.session_summary_pdf(make_session())
    assert data.startswith(b"%PDF-")
    assert len(data) > 500


def test_pdf_handles_missing_fields():
    data = report.session_summary_pdf({})
    assert data.startswith(b"%PDF-")


def test_pdf_handles_long_and_unicode_titles():
    sessions = [
        make_session(title="A very long session title " * 5),  # exercises truncation
        make_session(title="復習セッション — naïve café"),        # non-latin1 chars
    ]
    data = report.sessions_to_pdf(sessions)
    assert data.startswith(b"%PDF-")
