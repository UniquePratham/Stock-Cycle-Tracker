"""Market data providers interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, Sequence

from stock_cycle_tracker.domain.models import (
    MarketSessionStatus,
    NormalizedOHLC,
    PriceType,
    Stock,
)


class MarketDataProvider(ABC):
    """Abstract interface for all market data sources."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. NSE, BSE, YahooFinance, Mock)."""
        pass

    @abstractmethod
    def resolve_stock(self, query: str) -> Optional[Stock]:
        """
        Resolves a user-entered stock name or ticker into a canonical Stock entity.
        Returns None if not found on this provider.
        """
        pass

    @abstractmethod
    def get_historical_ohlc(
        self,
        stock: Stock,
        start_date: date,
        end_date: date,
    ) -> Sequence[NormalizedOHLC]:
        """Fetches normalized historical OHLC records for the given date range."""
        pass

    @abstractmethod
    def get_reference_day_data(
        self,
        stock: Stock,
        target_date: date,
    ) -> Optional[NormalizedOHLC]:
        """
        Fetches the OHLC bar for the trading day on or immediately after target_date.
        """
        pass

    @abstractmethod
    def get_current_price(
        self,
        stock: Stock,
    ) -> tuple[float, PriceType, MarketSessionStatus]:
        """
        Returns (current_price, price_type, market_status).
        price_type is LIVE during market hours if available, otherwise CLOSE.
        """
        pass

    @abstractmethod
    def get_market_status(self) -> MarketSessionStatus:
        """Determines if the exchange market is currently OPEN or CLOSED."""
        pass
