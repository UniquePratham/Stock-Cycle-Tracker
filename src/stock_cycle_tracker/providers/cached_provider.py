"""Caching decorator for market data providers."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, Optional, Sequence, Tuple

from stock_cycle_tracker.domain.models import (
    MarketSessionStatus,
    NormalizedOHLC,
    PriceType,
    Stock,
    utc_now,
)
from stock_cycle_tracker.providers.base import MarketDataProvider


class CachedMarketDataProvider(MarketDataProvider):
    """
    Caches historical OHLC bars and reference day High values in memory / local cache.
    Prevents redundant external API calls for multi-cycle calculations.
    """

    def __init__(
        self,
        inner_provider: MarketDataProvider,
        live_price_ttl_seconds: int = 300,  # 5 minutes TTL for smooth, instant tab switching
    ) -> None:
        self.inner = inner_provider
        self.live_price_ttl_seconds = live_price_ttl_seconds

        # In-memory caches
        self._stock_cache: Dict[str, Stock] = {}
        self._ohlc_cache: Dict[Tuple[str, date, date], Sequence[NormalizedOHLC]] = {}
        self._ref_day_cache: Dict[Tuple[str, date], NormalizedOHLC] = {}
        self._price_cache: Dict[str, Tuple[float, PriceType, MarketSessionStatus, datetime]] = {}

    @property
    def provider_name(self) -> str:
        return f"Cached({self.inner.provider_name})"

    def clear_cache(self) -> None:
        """Clears all cached market data."""
        self._stock_cache.clear()
        self._ohlc_cache.clear()
        self._ref_day_cache.clear()
        self._price_cache.clear()

    def resolve_stock(self, query: str) -> Optional[Stock]:
        q = query.strip().upper()
        if q in self._stock_cache:
            return self._stock_cache[q]

        stock = self.inner.resolve_stock(query)
        if stock:
            self._stock_cache[q] = stock
            self._stock_cache[stock.symbol.upper()] = stock
        return stock

    def get_historical_ohlc(
        self,
        stock: Stock,
        start_date: date,
        end_date: date,
    ) -> Sequence[NormalizedOHLC]:
        cache_key = (stock.symbol.upper(), start_date, end_date)
        if cache_key in self._ohlc_cache:
            return self._ohlc_cache[cache_key]

        bars = self.inner.get_historical_ohlc(stock, start_date, end_date)
        if bars:
            self._ohlc_cache[cache_key] = bars
        return bars

    def get_reference_day_data(
        self,
        stock: Stock,
        target_date: date,
    ) -> Optional[NormalizedOHLC]:
        cache_key = (stock.symbol.upper(), target_date)
        if cache_key in self._ref_day_cache:
            return self._ref_day_cache[cache_key]

        bar = self.inner.get_reference_day_data(stock, target_date)
        if bar:
            self._ref_day_cache[cache_key] = bar
        return bar

    def get_current_price(
        self,
        stock: Stock,
    ) -> tuple[float, PriceType, MarketSessionStatus]:
        sym = stock.symbol.upper()
        now = utc_now()

        if sym in self._price_cache:
            price, p_type, m_status, cached_at = self._price_cache[sym]
            if (now - cached_at).total_seconds() < self.live_price_ttl_seconds:
                return price, p_type, m_status

        price, p_type, m_status = self.inner.get_current_price(stock)
        self._price_cache[sym] = (price, p_type, m_status, now)
        return price, p_type, m_status

    def get_market_status(self) -> MarketSessionStatus:
        return self.inner.get_market_status()
