"""Trading calendar and non-trading-day resolver for Indian Equity Markets."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Container, Iterable, Optional, Sequence, Set


class TradingCalendar:
    """
    Handles trading day validation and non-trading day resolution.
    Follows Indian market conventions (NSE/BSE).
    """

    # Common standard fixed/observed Indian market holidays (sample set for offline resolution)
    DEFAULT_STANDARD_HOLIDAYS: Set[tuple[int, int]] = {
        (1, 26),   # Republic Day
        (8, 15),   # Independence Day
        (10, 2),   # Gandhi Jayanti
        (5, 1),    # Maharashtra Day
        (12, 25),  # Christmas
    }

    def __init__(self, holidays: Optional[Iterable[date]] = None) -> None:
        self._explicit_holidays: Set[date] = set(holidays or [])

    def is_weekend(self, dt: date) -> bool:
        """Returns True if date is Saturday (5) or Sunday (6)."""
        return dt.weekday() in (5, 6)

    def is_holiday(self, dt: date) -> bool:
        """Returns True if date is a known fixed or explicit market holiday."""
        if dt in self._explicit_holidays:
            return True
        return (dt.month, dt.day) in self.DEFAULT_STANDARD_HOLIDAYS

    def is_trading_day(self, dt: date, known_trading_days: Optional[Container[date]] = None) -> bool:
        """
        Determines if date is a trading day.
        If known_trading_days is provided (from actual market OHLC), checks membership.
        Otherwise uses weekend + holiday checks.
        """
        if known_trading_days is not None:
            return dt in known_trading_days
        return not self.is_weekend(dt) and not self.is_holiday(dt)

    def resolve_annual_occurrence(self, orig_date: date, target_year: int) -> date:
        """
        Derives the calendar date in target_year for an original research date.
        Handles leap-year (29 Feb -> 28 Feb in non-leap years).
        """
        month = orig_date.month
        day = orig_date.day

        # Handle Feb 29 in non-leap year
        if month == 2 and day == 29:
            is_leap = (target_year % 4 == 0 and target_year % 100 != 0) or (target_year % 400 == 0)
            if not is_leap:
                return date(target_year, 2, 28)

        return date(target_year, month, day)

    def resolve_next_trading_day(
        self,
        target_date: date,
        known_trading_days: Optional[Sequence[date]] = None,
        max_lookahead_days: int = 30,
    ) -> date:
        """
        Finds the first available trading day on or after target_date.
        If known_trading_days is provided, finds the minimum date >= target_date.
        Otherwise iterates day by day checking weekends and holidays.
        """
        if known_trading_days:
            # Sorted search if known trading days provided
            future_days = [d for d in known_trading_days if d >= target_date]
            if future_days:
                return min(future_days)

        current = target_date
        for _ in range(max_lookahead_days):
            if self.is_trading_day(current, known_trading_days=known_trading_days):
                return current
            current += timedelta(days=1)

        return target_date
