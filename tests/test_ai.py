"""Tests for services.ai focus-score heuristic."""

import pytest

from services.ai import calculate_focus_score


def test_baseline_score_with_no_activity():
    # 50 + 0*1.5 - 0*4 = 50
    assert calculate_focus_score(0, 0) == 50


@pytest.mark.parametrize(
    "duration_minutes, pause_count, expected",
    [
        (20, 1, 76),   # 50 + 30 - 4
        (30, 2, 87),   # 50 + 45 - 8
        (10, 0, 65),   # 50 + 15
    ],
)
def test_known_values(duration_minutes, pause_count, expected):
    assert calculate_focus_score(duration_minutes, pause_count) == expected


def test_score_is_clamped_to_100():
    assert calculate_focus_score(100, 0) == 100


def test_score_is_clamped_to_0():
    assert calculate_focus_score(0, 50) == 0


def test_result_is_an_int():
    assert isinstance(calculate_focus_score(25, 1), int)


def test_longer_sessions_score_higher():
    assert calculate_focus_score(40, 0) > calculate_focus_score(10, 0)


def test_more_pauses_score_lower():
    assert calculate_focus_score(30, 5) < calculate_focus_score(30, 0)


@pytest.mark.parametrize("duration, pauses", [(0, 0), (25, 1), (200, 0), (5, 99)])
def test_score_always_within_bounds(duration, pauses):
    score = calculate_focus_score(duration, pauses)
    assert 0 <= score <= 100
