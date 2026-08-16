"""Domain models for Stock Cycle Tracker."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional


class ExchangePreference(str, Enum):
    NSE = "NSE"
    BSE = "BSE"
    FALLBACK = "FALLBACK"


class MarketSessionStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class PriceType(str, Enum):
    LIVE = "LIVE"
    CLOSE = "CLOSE"


class CycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UPCOMING = "UPCOMING"
    COMPLETED = "COMPLETED"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class NormalizedOHLC:
    """Standardized OHLC bar."""
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    source: str = "UNKNOWN"


@dataclass
class Stock:
    """Stock instrument record."""
    symbol: str
    company_name: str = ""
    user_display_name: str = ""
    nse_symbol: Optional[str] = None
    bse_code: Optional[str] = None
    preferred_exchange: ExchangePreference = ExchangePreference.NSE
    id: Optional[int] = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def get_display_name(self) -> str:
        return self.user_display_name or self.symbol or self.company_name


@dataclass
class Cycle:
    """Cycle research date configuration."""
    reference_date: date  # Original user research date (LD)
    stock_id: Optional[int] = None
    cycle_number: int = 1
    id: Optional[int] = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    @property
    def month(self) -> int:
        return self.reference_date.month

    @property
    def day(self) -> int:
        return self.reference_date.day

    @property
    def recurring_formatted(self) -> str:
        return self.reference_date.strftime("%d %B")


@dataclass(frozen=True)
class CycleAnalysis:
    """Immutable calculation snapshot for a cycle."""
    stock_symbol: str
    company_name: str
    cycle_number: int
    original_reference_date: date
    recurring_reference_date: date
    actual_reference_trading_date: date
    exchange: str
    reference_high: float
    current_price: float
    price_type: PriceType
    calculation_date: date
    percentage_change: float
    bucket: str
    cycle_start_date: date
    cycle_end_date: date
    data_source: str = "NSE"
    last_data_refresh: datetime = field(default_factory=utc_now)
    is_fallback_or_stale: bool = False
    cycle_status: CycleStatus = CycleStatus.ACTIVE
