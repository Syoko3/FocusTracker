"""Tests for services.analytics statistics helpers."""

from datetime import date, datetime, timedelta

import pytest

from services import analytics


def make_session(day, duration=1500, score=90, pauses=1):
    """Build a canonical session dict for tests."""

    return {"date": day, "duration": duration, "score": score, "pause_count": pauses}


# ---------------------------------------------------------------------------
# Field accessors
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "value, expected",
    [
        ("2026-07-18", date(2026, 7, 18)),
        ("2026-07-18T09:30:00", date(2026, 7, 18)),  # only the date part is read
        (datetime(2026, 7, 18, 9, 30), date(2026, 7, 18)),
        (date(2026, 7, 18), date(2026, 7, 18)),
        ("not-a-date", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_date(value, expected):
    assert analytics.parse_date(value) == expected


def test_session_seconds_and_minutes():
    session = make_session("2026-07-18", duration=1500)
    assert analytics.session_seconds(session) == 1500.0
    assert analytics.session_minutes(session) == 25.0


@pytest.mark.parametrize("bad", [{}, {"duration": None}, {"duration": "abc"}, {"duration": -5}])
def test_session_seconds_is_non_negative_and_safe(bad):
    assert analytics.session_seconds(bad) >= 0.0


def test_session_score_and_pauses_defaults():
    assert analytics.session_score({}) == 0.0
    assert analytics.session_pauses({}) == 0
    assert analytics.session_score({"score": "oops"}) == 0.0
    assert analytics.session_pauses({"pause_count": "oops"}) == 0


# ---------------------------------------------------------------------------
# Aggregates
# ---------------------------------------------------------------------------
@pytest.fixture
def sessions():
    return [
        make_session("2026-07-18", duration=1500, score=92, pauses=1),
        make_session("2026-07-18", duration=1800, score=88, pauses=2),
        make_session("2026-07-17", duration=1800, score=86, pauses=2),
        make_session("2026-07-16", duration=1200, score=80, pauses=3),
    ]


def test_totals(sessions):
    assert analytics.total_sessions(sessions) == 4
    assert analytics.total_study_seconds(sessions) == 6300
    assert analytics.total_study_minutes(sessions) == 105.0
    assert analytics.total_pauses(sessions) == 8


def test_averages(sessions):
    assert analytics.average_score(sessions) == pytest.approx((92 + 88 + 86 + 80) / 4)
    assert analytics.average_pauses(sessions) == pytest.approx(2.0)


def test_empty_aggregates_do_not_divide_by_zero():
    assert analytics.total_sessions([]) == 0
    assert analytics.total_study_minutes([]) == 0
    assert analytics.average_score([]) == 0.0
    assert analytics.average_pauses([]) == 0.0
    assert analytics.daily_average_score([]) == 0.0
    assert analytics.current_streak([]) == 0


def test_sessions_on_and_daily_average(sessions):
    day = date(2026, 7, 18)
    todays = analytics.sessions_on(sessions, day)
    assert len(todays) == 2
    assert analytics.daily_average_score(sessions, day) == pytest.approx((92 + 88) / 2)


def test_daily_average_score_for_day_with_no_sessions(sessions):
    assert analytics.daily_average_score(sessions, date(2000, 1, 1)) == 0.0


# ---------------------------------------------------------------------------
# Streak
# ---------------------------------------------------------------------------
def test_current_streak_counts_consecutive_days_ending_today():
    today = date(2026, 7, 18)
    sessions = [make_session(d) for d in ("2026-07-18", "2026-07-17", "2026-07-16")]
    assert analytics.current_streak(sessions, today=today) == 3


def test_current_streak_allows_grace_when_last_session_was_yesterday():
    today = date(2026, 7, 18)
    sessions = [make_session("2026-07-17"), make_session("2026-07-16")]
    assert analytics.current_streak(sessions, today=today) == 2


def test_current_streak_is_zero_when_last_session_is_stale():
    today = date(2026, 7, 18)
    sessions = [make_session("2026-07-10"), make_session("2026-07-09")]
    assert analytics.current_streak(sessions, today=today) == 0


def test_current_streak_stops_at_a_gap():
    today = date(2026, 7, 18)
    sessions = [make_session(d) for d in ("2026-07-18", "2026-07-17", "2026-07-15")]
    assert analytics.current_streak(sessions, today=today) == 2


def test_current_streak_deduplicates_same_day_sessions():
    today = date(2026, 7, 18)
    sessions = [make_session("2026-07-18"), make_session("2026-07-18")]
    assert analytics.current_streak(sessions, today=today) == 1


def test_single_session_today_gives_streak_of_one():
    today = date(2026, 7, 18)
    assert analytics.current_streak([make_session("2026-07-18")], today=today) == 1


def test_doing_a_session_today_increments_an_existing_streak():
    today = date(2026, 7, 18)
    # A streak that currently runs through yesterday...
    running = [make_session("2026-07-17"), make_session("2026-07-16")]
    assert analytics.current_streak(running, today=today) == 2
    # ...grows by one the moment today's session is added.
    with_today = running + [make_session("2026-07-18")]
    assert analytics.current_streak(with_today, today=today) == 3


def test_streak_grows_as_consecutive_days_are_added():
    today = date(2026, 7, 18)
    accumulated = []
    # Anchor on today, then extend backwards one consecutive day at a time;
    # each added day should lengthen the active streak by one.
    for days_ago, expected in [(0, 1), (1, 2), (2, 3)]:
        day = (today - timedelta(days=days_ago)).isoformat()
        accumulated.append(make_session(day))
        assert analytics.current_streak(accumulated, today=today) == expected


def test_streak_counts_a_long_unbroken_run():
    today = date(2026, 7, 18)
    sessions = [make_session(f"2026-07-{day:02d}") for day in range(12, 19)]  # 12th–18th
    assert analytics.current_streak(sessions, today=today) == 7


def test_streak_resets_to_one_after_a_missed_day():
    today = date(2026, 7, 18)
    # Worked today, but skipped yesterday (17th), then worked the 16th and 15th.
    sessions = [make_session(d) for d in ("2026-07-18", "2026-07-16", "2026-07-15")]
    assert analytics.current_streak(sessions, today=today) == 1


def test_future_dated_session_does_not_inflate_streak():
    today = date(2026, 7, 18)
    sessions = [make_session("2026-07-19"), make_session("2026-07-18")]
    # Tomorrow's record is ignored; only today counts.
    assert analytics.current_streak(sessions, today=today) == 1


def test_missing_today_does_not_increment_yesterdays_streak():
    today = date(2026, 7, 18)
    # No session today; the streak is preserved at yesterday's length, not grown.
    sessions = [make_session("2026-07-17"), make_session("2026-07-16"), make_session("2026-07-15")]
    assert analytics.current_streak(sessions, today=today) == 3


# ---------------------------------------------------------------------------
# streak_from_dates (streak tracked independently of session records)
# ---------------------------------------------------------------------------
def test_streak_from_dates_accepts_iso_strings():
    today = date(2026, 7, 18)
    dates = ["2026-07-18", "2026-07-17", "2026-07-16"]
    assert analytics.streak_from_dates(dates, today=today) == 3


def test_streak_from_dates_accepts_date_objects():
    today = date(2026, 7, 18)
    dates = [date(2026, 7, 18), date(2026, 7, 17)]
    assert analytics.streak_from_dates(dates, today=today) == 2


def test_streak_from_dates_matches_current_streak_for_same_days():
    today = date(2026, 7, 18)
    days = ["2026-07-18", "2026-07-17", "2026-07-15"]
    sessions = [make_session(day) for day in days]
    assert analytics.streak_from_dates(days, today=today) == analytics.current_streak(
        sessions, today=today
    )


def test_streak_from_dates_empty_is_zero():
    assert analytics.streak_from_dates([], today=date(2026, 7, 18)) == 0


def test_streak_from_dates_ignores_unparseable_values():
    today = date(2026, 7, 18)
    dates = ["2026-07-18", "not-a-date", None, "2026-07-17"]
    assert analytics.streak_from_dates(dates, today=today) == 2


# ---------------------------------------------------------------------------
# Recent + summarize
# ---------------------------------------------------------------------------
def test_recent_sessions_orders_newest_first_and_limits(sessions):
    recent = analytics.recent_sessions(sessions, limit=2)
    assert len(recent) == 2
    assert analytics.parse_date(recent[0]["date"]) == date(2026, 7, 18)


def test_summarize_bundles_expected_keys(sessions):
    summary = analytics.summarize(sessions)
    assert set(summary) == {
        "total_sessions",
        "total_study_seconds",
        "total_study_minutes",
        "average_score",
        "today_score",
        "current_streak",
        "total_pauses",
        "average_pauses",
    }
    assert summary["total_sessions"] == 4
    assert summary["total_pauses"] == 8


# ---------------------------------------------------------------------------
# Presentation helpers
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "minutes, expected",
    [
        (0, "0 min"),
        (-5, "0 min"),
        (30, "30 min"),
        (60, "1h"),
        (90, "1h 30m"),
        (125, "2h 5m"),
    ],
)
def test_format_duration(minutes, expected):
    assert analytics.format_duration(minutes) == expected


def test_to_dataframe_shape_and_bad_row_dropping():
    sessions = [
        make_session("2026-07-16", duration=1500, score=90),
        make_session("2026-07-18", duration=1800, score=88),
        make_session("not-a-date"),  # dropped
    ]
    frame = analytics.to_dataframe(sessions)

    assert list(frame.columns) == ["Date", "Duration (min)", "Score", "Pauses"]
    assert len(frame) == 2  # bad-date row dropped
    # sorted oldest-first
    assert frame.iloc[0]["Date"].date() == date(2026, 7, 16)
    assert frame.iloc[-1]["Date"].date() == date(2026, 7, 18)
    assert frame.iloc[0]["Duration (min)"] == 25.0


def test_to_dataframe_is_empty_for_no_sessions():
    frame = analytics.to_dataframe([])
    assert frame.empty
    assert list(frame.columns) == ["Date", "Duration (min)", "Score", "Pauses"]
