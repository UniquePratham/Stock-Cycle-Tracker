"""Market trading session inspector for Indian stock exchanges (NSE/BSE)."""

from __future__ import annotations

from datetime import datetime, time
import zoneinfo

from stock_cycle_tracker.domain.calendar import TradingCalendar
from stock_cycle_tracker.domain.models import MarketSessionStatus


class MarketSessionInspector:
    """
    Determines live market session status for Indian Stock Exchanges.
    Standard equity trading hours: Monday - Friday, 09:15 to 15:30 IST.
    """

    MARKET_OPEN_TIME = time(9, 15)
    MARKET_CLOSE_TIME = time(15, 30)
    IST_TZ = zoneinfo.ZoneInfo("Asia/Kolkata")

    def __init__(self, calendar: TradingCalendar | None = None) -> None:
        self.calendar = calendar or TradingCalendar()

    def get_current_ist_datetime(self) -> datetime:
        return datetime.now(self.IST_TZ)

    def is_market_open(self, dt: datetime | None = None) -> bool:
        current_dt = dt or self.get_current_ist_datetime()
        if current_dt.tzinfo is None:
            current_dt = current_dt.replace(tzinfo=self.IST_TZ)
        else:
            current_dt = current_dt.astimezone(self.IST_TZ)

        curr_date = current_dt.date()
        curr_time = current_dt.time()

        # Must be a trading day
        if not self.calendar.is_trading_day(curr_date):
            return False

        # Must be within 09:15 and 15:30 IST
        return self.MARKET_OPEN_TIME <= curr_time <= self.MARKET_CLOSE_TIME

    def get_market_status(self, dt: datetime | None = None) -> MarketSessionStatus:
        if self.is_market_open(dt):
            return MarketSessionStatus.OPEN
        return MarketSessionStatus.CLOSED
