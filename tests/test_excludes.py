"""Tests for the exclude window logic."""

from __future__ import annotations

from datetime import datetime, time

import pytest

from chaotic.excludes import excluded_reason, in_window, parse_window


def test_parse_window_returns_both_ends() -> None:
    assert parse_window("22:00-08:00") == (time(22, 0), time(8, 0))


def test_parse_window_tolerates_surrounding_whitespace() -> None:
    assert parse_window(" 09:30 - 17:45 ") == (time(9, 30), time(17, 45))


@pytest.mark.parametrize("window", ["2200", "", "invalid-range", "25:00-08:00"])
def test_parse_window_rejects_garbage(window: str) -> None:
    with pytest.raises(ValueError, match=r"range|time data|unconverted"):
        parse_window(window)


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (time(8, 0), True),  # inclusive lower bound
        (time(12, 0), True),
        (time(17, 0), True),  # inclusive upper bound
        (time(7, 59), False),
        (time(17, 1), False),
    ],
)
def test_in_window_same_day(now: time, expected: bool) -> None:
    assert in_window(now, time(8, 0), time(17, 0)) is expected


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (time(23, 30), True),
        (time(22, 0), True),
        (time(0, 0), True),  # midnight itself, missed by a naive comparison
        (time(0, 0, 30), True),
        (time(7, 59), True),
        (time(8, 0), True),
        (time(8, 1), False),
        (time(12, 0), False),
    ],
)
def test_in_window_wraps_around_midnight(now: time, expected: bool) -> None:
    assert in_window(now, time(22, 0), time(8, 0)) is expected


def test_no_excludes_means_no_reason() -> None:
    assert excluded_reason({}, datetime(2026, 8, 25, 12, 0)) is None


def test_unknown_exclude_keys_are_ignored() -> None:
    assert excluded_reason({"phase_of_moon": ["waxing"]}, datetime(2026, 8, 25, 12, 0)) is None


def test_day_of_year_matches() -> None:
    reason = excluded_reason({"days_of_year": ["Dec24", "Jan01"]}, datetime(2026, 12, 24, 12, 0))
    assert reason is not None
    assert "Dec24" in reason
    assert "days_of_year" in reason


def test_day_of_year_does_not_match_other_days() -> None:
    assert excluded_reason({"days_of_year": ["Dec24"]}, datetime(2026, 12, 25, 12, 0)) is None


def test_weekday_matches() -> None:
    # 2026-08-29 is a Saturday.
    reason = excluded_reason({"weekdays": ["Sat", "Sun"]}, datetime(2026, 8, 29, 12, 0))
    assert reason is not None
    assert "Sat" in reason


def test_weekday_does_not_match_other_days() -> None:
    # 2026-08-25 is a Tuesday.
    assert excluded_reason({"weekdays": ["Sat", "Sun"]}, datetime(2026, 8, 25, 12, 0)) is None


def test_time_of_day_matches_second_window() -> None:
    excludes = {"times_of_day": ["22:00-08:00", "11:00-14:00"]}
    reason = excluded_reason(excludes, datetime(2026, 8, 25, 12, 30))
    assert reason is not None
    assert "11:00-14:00" in reason


def test_time_of_day_just_after_midnight_is_excluded() -> None:
    # Regression: the original implementation started the wrap-around at 00:01,
    # leaving the first minute of the day unprotected.
    assert excluded_reason({"times_of_day": ["22:00-08:00"]}, datetime(2026, 8, 25, 0, 0, 30)) is not None


def test_time_of_day_outside_every_window() -> None:
    excludes = {"times_of_day": ["22:00-08:00", "11:00-14:00"]}
    assert excluded_reason(excludes, datetime(2026, 8, 25, 16, 0)) is None


def test_empty_exclude_lists_are_ignored() -> None:
    excludes: dict[str, object] = {"days_of_year": None, "weekdays": [], "times_of_day": None}
    assert excluded_reason(excludes, datetime(2026, 8, 29, 23, 0)) is None


def test_day_of_year_wins_over_time_of_day() -> None:
    excludes = {"days_of_year": ["Aug25"], "times_of_day": ["11:00-14:00"]}
    reason = excluded_reason(excludes, datetime(2026, 8, 25, 12, 0))
    assert reason is not None
    assert "days_of_year" in reason


def test_defaults_to_now() -> None:
    # Every day of the year is excluded, so whichever "now" is, it matches.
    all_days = [datetime(2026, 1, 1).replace(month=m, day=d).strftime("%b%d") for m in range(1, 13) for d in (1,)]
    excludes = {"days_of_year": all_days, "times_of_day": ["00:00-23:59"]}
    assert excluded_reason(excludes) is not None
