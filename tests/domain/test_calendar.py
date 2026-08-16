"""Unit tests for TradingCalendar."""

from datetime import date
import pytest
from stock_cycle_tracker.domain.calendar import TradingCalendar


def test_weekend_detection():
    cal = TradingCalendar()
    # 2026-08-15 is Saturday, 2026-08-16 is Sunday
    assert cal.is_weekend(date(2026, 8, 15)) is True
    assert cal.is_weekend(date(2026, 8, 16)) is True
    # 2026-08-17 is Monday
    assert cal.is_weekend(date(2026, 8, 17)) is False


def test_holiday_detection():
    cal = TradingCalendar()
    # Republic Day
    assert cal.is_holiday(date(2026, 1, 26)) is True
    # Independence Day
    assert cal.is_holiday(date(2026, 8, 15)) is True
    # Normal day
    assert cal.is_holiday(date(2026, 8, 18)) is False


def test_resolve_annual_occurrence_leap_year():
    cal = TradingCalendar()
    orig_leap = date(2020, 2, 29)

    # 2024 is leap year
    assert cal.resolve_annual_occurrence(orig_leap, 2024) == date(2024, 2, 29)
    # 2025 is not leap year -> Feb 28
    assert cal.resolve_annual_occurrence(orig_leap, 2025) == date(2025, 2, 28)
    # 2026 is not leap year -> Feb 28
    assert cal.resolve_annual_occurrence(orig_leap, 2026) == date(2026, 2, 28)


def test_resolve_next_trading_day_from_weekend():
    cal = TradingCalendar()
    # 10 Jan 2026 is Saturday -> next trading day is Monday 12 Jan 2026
    target = date(2026, 1, 10)
    resolved = cal.resolve_next_trading_day(target)
    assert resolved == date(2026, 1, 12)


def test_resolve_next_trading_day_from_known_list():
    cal = TradingCalendar()
    known_days = [
        date(2026, 1, 9),
        date(2026, 1, 12),
        date(2026, 1, 13),
    ]
    # Request Saturday Jan 10
    resolved = cal.resolve_next_trading_day(date(2026, 1, 10), known_trading_days=known_days)
    assert resolved == date(2026, 1, 12)
