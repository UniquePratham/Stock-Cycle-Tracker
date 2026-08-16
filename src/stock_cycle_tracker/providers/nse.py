"""NSE (National Stock Exchange of India) Provider adapter."""

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


class NSEProvider(MarketDataProvider):
    """
    Dedicated NSE market data provider.
    Prefers NSE official resolution and uses YFinance (.NS) as standard gateway.
    """

    def __init__(self, fallback_adapter: Optional[YFinanceFallbackProvider] = None) -> None:
        self._adapter = fallback_adapter or YFinanceFallbackProvider(default_exchange=ExchangePreference.NSE)

    @property
    def provider_name(self) -> str:
        return "NSE"

    def resolve_stock(self, query: str) -> Optional[Stock]:
        sym = query.strip().upper().replace(".NS", "").replace(".BO", "")
        # Force NSE lookup
        resolved = self._adapter.resolve_stock(f"{sym}.NS")
        if resolved and resolved.preferred_exchange == ExchangePreference.NSE:
            return resolved
        # Also try direct query if resolve_stock matched NSE
        direct = self._adapter.resolve_stock(sym)
        if direct and direct.preferred_exchange == ExchangePreference.NSE:
            return direct
        return None

    def get_historical_ohlc(
        self,
        stock: Stock,
        start_date: date,
        end_date: date,
    ) -> Sequence[NormalizedOHLC]:
        stock_nse = Stock(
            symbol=stock.symbol,
            company_name=stock.company_name,
            nse_symbol=stock.nse_symbol or stock.symbol,
            preferred_exchange=ExchangePreference.NSE,
        )
        return self._adapter.get_historical_ohlc(stock_nse, start_date, end_date)

    def get_reference_day_data(
        self,
        stock: Stock,
        target_date: date,
    ) -> Optional[NormalizedOHLC]:
        stock_nse = Stock(
            symbol=stock.symbol,
            company_name=stock.company_name,
            nse_symbol=stock.nse_symbol or stock.symbol,
            preferred_exchange=ExchangePreference.NSE,
        )
        return self._adapter.get_reference_day_data(stock_nse, target_date)

    def get_current_price(
        self,
        stock: Stock,
    ) -> tuple[float, PriceType, MarketSessionStatus]:
        stock_nse = Stock(
            symbol=stock.symbol,
            company_name=stock.company_name,
            nse_symbol=stock.nse_symbol or stock.symbol,
            preferred_exchange=ExchangePreference.NSE,
        )
        return self._adapter.get_current_price(stock_nse)

    def get_market_status(self) -> MarketSessionStatus:
        return self._adapter.get_market_status()
