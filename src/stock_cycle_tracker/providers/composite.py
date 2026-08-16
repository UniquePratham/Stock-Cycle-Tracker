"""Composite market data provider enforcing NSE -> BSE -> Fallback hierarchy."""

from __future__ import annotations

from datetime import date
import logging
from typing import Optional, Sequence

from stock_cycle_tracker.domain.models import (
    ExchangePreference,
    MarketSessionStatus,
    NormalizedOHLC,
    PriceType,
    Stock,
)
from stock_cycle_tracker.providers.base import MarketDataProvider
from stock_cycle_tracker.providers.bse import BSEProvider
from stock_cycle_tracker.providers.fallback import YFinanceFallbackProvider
from stock_cycle_tracker.providers.nse import NSEProvider

logger = logging.getLogger(__name__)


class CompositeMarketDataProvider(MarketDataProvider):
    """
    Orchestrates market data providers according to the strict preference order:
    1. NSE
    2. BSE
    3. Fallback
    """

    def __init__(
        self,
        nse_provider: Optional[MarketDataProvider] = None,
        bse_provider: Optional[MarketDataProvider] = None,
        fallback_provider: Optional[MarketDataProvider] = None,
    ) -> None:
        self.fallback_provider = fallback_provider or YFinanceFallbackProvider()
        self.nse_provider = nse_provider or NSEProvider(fallback_adapter=self.fallback_provider if isinstance(self.fallback_provider, YFinanceFallbackProvider) else None)
        self.bse_provider = bse_provider or BSEProvider(fallback_adapter=self.fallback_provider if isinstance(self.fallback_provider, YFinanceFallbackProvider) else None)

    @property
    def provider_name(self) -> str:
        return "Composite(NSE->BSE->Fallback)"

    def resolve_stock(self, query: str) -> Optional[Stock]:
        # 1. Try NSE first
        try:
            stock = self.nse_provider.resolve_stock(query)
            if stock:
                return stock
        except Exception as e:
            logger.warning(f"NSE resolve failed for {query}: {e}")

        # 2. Try BSE second
        try:
            stock = self.bse_provider.resolve_stock(query)
            if stock:
                return stock
        except Exception as e:
            logger.warning(f"BSE resolve failed for {query}: {e}")

        # 3. Try generic fallback third
        try:
            return self.fallback_provider.resolve_stock(query)
        except Exception as e:
            logger.warning(f"Fallback resolve failed for {query}: {e}")
            return None

    def _select_provider(self, stock: Stock) -> MarketDataProvider:
        if stock.preferred_exchange == ExchangePreference.BSE:
            return self.bse_provider
        return self.nse_provider

    def get_historical_ohlc(
        self,
        stock: Stock,
        start_date: date,
        end_date: date,
    ) -> Sequence[NormalizedOHLC]:
        primary = self._select_provider(stock)
        try:
            bars = primary.get_historical_ohlc(stock, start_date, end_date)
            if bars:
                return bars
        except Exception as e:
            logger.warning(f"Primary provider {primary.provider_name} failed for OHLC: {e}")

        # Fallback to secondary provider if primary failed
        secondary = self.bse_provider if primary is self.nse_provider else self.nse_provider
        try:
            bars = secondary.get_historical_ohlc(stock, start_date, end_date)
            if bars:
                return bars
        except Exception as e:
            logger.warning(f"Secondary provider {secondary.provider_name} failed for OHLC: {e}")

        return self.fallback_provider.get_historical_ohlc(stock, start_date, end_date)

    def get_reference_day_data(
        self,
        stock: Stock,
        target_date: date,
    ) -> Optional[NormalizedOHLC]:
        primary = self._select_provider(stock)
        try:
            bar = primary.get_reference_day_data(stock, target_date)
            if bar:
                return bar
        except Exception as e:
            logger.warning(f"Primary provider {primary.provider_name} failed for ref day: {e}")

        secondary = self.bse_provider if primary is self.nse_provider else self.nse_provider
        try:
            bar = secondary.get_reference_day_data(stock, target_date)
            if bar:
                return bar
        except Exception as e:
            logger.warning(f"Secondary provider {secondary.provider_name} failed for ref day: {e}")

        return self.fallback_provider.get_reference_day_data(stock, target_date)

    def get_current_price(
        self,
        stock: Stock,
    ) -> tuple[float, PriceType, MarketSessionStatus]:
        primary = self._select_provider(stock)
        try:
            price, p_type, m_status = primary.get_current_price(stock)
            if price > 0:
                return price, p_type, m_status
        except Exception as e:
            logger.warning(f"Primary provider {primary.provider_name} failed for current price: {e}")

        secondary = self.bse_provider if primary is self.nse_provider else self.nse_provider
        try:
            price, p_type, m_status = secondary.get_current_price(stock)
            if price > 0:
                return price, p_type, m_status
        except Exception as e:
            logger.warning(f"Secondary provider {secondary.provider_name} failed for current price: {e}")

        return self.fallback_provider.get_current_price(stock)

    def get_market_status(self) -> MarketSessionStatus:
        return self.nse_provider.get_market_status()
