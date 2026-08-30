"""Evaluation of "do not touch anything right now" windows.

Excludes never stop a run, they downgrade it to a dry-run: chaotic still selects
a target and logs what it *would* have done. The whole module is pure — it takes
the exclude mapping plus a point in time and returns a human readable reason —
which keeps the calendar logic testable without freezing the system clock.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, time
from typing import Any

DAY_OF_YEAR_FORMAT = "%b%d"
"""Format of ``days_of_year`` entries, e.g. ``Jan01`` or ``Dec24``."""

WEEKDAY_FORMAT = "%a"
"""Format of ``weekdays`` entries, e.g. ``Sat`` or ``Sun``."""

TIME_OF_DAY_FORMAT = "%H:%M"
"""Format of both ends of a ``times_of_day`` range, e.g. ``22:00-08:00``."""


def parse_window(window: str) -> tuple[time, time]:
    """Parse a ``HH:MM-HH:MM`` range into its start and end time.

    Raises:
        ValueError: If the range is malformed.
    """
    start_raw, separator, end_raw = window.partition("-")
    if not separator:
        raise ValueError(f"Invalid time range {window!r}, expected format 'HH:MM-HH:MM'")

    start = datetime.strptime(start_raw.strip(), TIME_OF_DAY_FORMAT).time()
    end = datetime.strptime(end_raw.strip(), TIME_OF_DAY_FORMAT).time()
    return start, end


def in_window(now: time, start: time, end: time) -> bool:
    """Return whether ``now`` falls inside ``start``..``end``, inclusive.

    Ranges that wrap around midnight (``22:00-08:00``) are supported and, unlike
    a naive comparison, cover the minutes right after midnight as well.
    """
    if start <= end:
        return start <= now <= end
    return now >= start or now <= end


def excluded_reason(excludes: Mapping[str, Any], now: datetime | None = None) -> str | None:
    """Return why ``now`` is excluded, or ``None`` when chaos may happen.

    The returned string is meant to be logged verbatim.

    Args:
        excludes: The ``excludes`` block of a config. Supported keys are
            ``days_of_year``, ``weekdays`` and ``times_of_day``; unknown keys are
            ignored so that configs stay forward compatible.
        now: Point in time to evaluate, defaults to the local wall clock.
    """
    moment = now or datetime.now()

    days_of_year = excludes.get("days_of_year") or ()
    today = moment.strftime(DAY_OF_YEAR_FORMAT)
    if today in days_of_year:
        return f"Today '{today}' is in the days_of_year excludes"

    weekdays = excludes.get("weekdays") or ()
    weekday = moment.strftime(WEEKDAY_FORMAT)
    if weekday in weekdays:
        return f"Today '{weekday}' is in the weekdays excludes"

    current_time = moment.time()
    for window in excludes.get("times_of_day") or ():
        start, end = parse_window(window)
        if in_window(current_time, start, end):
            return f"Now '{current_time.strftime(TIME_OF_DAY_FORMAT)}' is in the times_of_day exclude {window}"

    return None
