"""BSE (Bombay Stock Exchange) Provider adapter."""

from __future__ import annotations

from datetime import date
from typing import Optional, Sequence

from stock_cycle_tracker.domain.models import (
    ExchangePreference,
    MarketSessionStatus,
    NormalizedOHLC,
    PriceType,
    Stock,
)
from stock_cycle_tracker.providers.base import MarketDataProvider
from stock_cycle_tracker.providers.fallback import YFinanceFallbackProvider


class BSEProvider(MarketDataProvider):
    """
    Dedicated BSE market data provider.
    Handles securities available on BSE (.BO).
    """

    def __init__(self, fallback_adapter: Optional[YFinanceFallbackProvider] = None) -> None:
        self._adapter = fallback_adapter or YFinanceFallbackProvider(default_exchange=ExchangePreference.BSE)

    @property
    def provider_name(self) -> str:
        return "BSE"

    def resolve_stock(self, query: str) -> Optional[Stock]:
        sym = query.strip().upper().replace(".NS", "").replace(".BO", "")
        # Force BSE lookup
        resolved = self._adapter.resolve_stock(f"{sym}.BO")
        if resolved:
            resolved.preferred_exchange = ExchangePreference.BSE
            resolved.bse_code = sym
            return resolved
        return None

    def get_historical_ohlc(
        self,
        stock: Stock,
        start_date: date,
        end_date: date,
    ) -> Sequence[NormalizedOHLC]:
        stock_bse = Stock(
            symbol=stock.symbol,
            company_name=stock.company_name,
            bse_code=stock.bse_code or stock.symbol,
            preferred_exchange=ExchangePreference.BSE,
        )
        return self._adapter.get_historical_ohlc(stock_bse, start_date, end_date)

    def get_reference_day_data(
        self,
        stock: Stock,
        target_date: date,
    ) -> Optional[NormalizedOHLC]:
        stock_bse = Stock(
            symbol=stock.symbol,
            company_name=stock.company_name,
            bse_code=stock.bse_code or stock.symbol,
            preferred_exchange=ExchangePreference.BSE,
        )
        return self._adapter.get_reference_day_data(stock_bse, target_date)

    def get_current_price(
        self,
        stock: Stock,
    ) -> tuple[float, PriceType, MarketSessionStatus]:
        stock_bse = Stock(
            symbol=stock.symbol,
            company_name=stock.company_name,
            bse_code=stock.bse_code or stock.symbol,
            preferred_exchange=ExchangePreference.BSE,
        )
        return self._adapter.get_current_price(stock_bse)

    def get_market_status(self) -> MarketSessionStatus:
        return self._adapter.get_market_status()
