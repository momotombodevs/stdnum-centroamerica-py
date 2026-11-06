"""Date helpers: calendar validation and a "today" that tests can replace."""

from __future__ import annotations

import calendar
import datetime


def is_valid_date(year: int, month: int, day: int) -> bool:
    """Return ``True`` if the date exists. With ``year=2000`` it accepts February 29."""
    return 1 <= month <= 12 and 1 <= day <= calendar.monthrange(year, month)[1]


def today() -> datetime.date:
    """Return today's local date. Tests replace it with ``monkeypatch``."""
    return datetime.date.today()
