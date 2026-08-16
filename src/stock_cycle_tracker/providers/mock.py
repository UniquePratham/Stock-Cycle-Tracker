"""Mock market data provider for deterministic testing."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Sequence

from stock_cycle_tracker.domain.models import (
    ExchangePreference,
    MarketSessionStatus,
    NormalizedOHLC,
    PriceType,
    Stock,
)
from stock_cycle_tracker.providers.base import MarketDataProvider


class MockMarketDataProvider(MarketDataProvider):
    """Hermetic mock provider for unit and integration testing."""

    def __init__(
        self,
        name: str = "MockNSE",
        default_exchange: ExchangePreference = ExchangePreference.NSE,
        market_status: MarketSessionStatus = MarketSessionStatus.CLOSED,
    ) -> None:
        self._name = name
        self._default_exchange = default_exchange
        self._market_status = market_status
        self._stocks: Dict[str, Stock] = {}
        self._ohlc_data: Dict[str, List[NormalizedOHLC]] = {}
        self._current_prices: Dict[str, float] = {}

    @property
    def provider_name(self) -> str:
        return self._name

    def set_market_status(self, status: MarketSessionStatus) -> None:
        self._market_status = status

    def register_stock(
        self,
        symbol: str,
        company_name: str = "",
        nse_symbol: Optional[str] = None,
        bse_code: Optional[str] = None,
        preferred_exchange: Optional[ExchangePreference] = None,
        current_price: float = 1000.0,
    ) -> Stock:
        stock = Stock(
            symbol=symbol.upper(),
            company_name=company_name or symbol.upper(),
            nse_symbol=nse_symbol or symbol.upper(),
            bse_code=bse_code,
            preferred_exchange=preferred_exchange or self._default_exchange,
        )
        self._stocks[symbol.upper()] = stock
        self._current_prices[symbol.upper()] = current_price
        return stock

    def add_ohlc_bars(self, symbol: str, bars: Sequence[NormalizedOHLC]) -> None:
        sym = symbol.upper()
        if sym not in self._ohlc_data:
            self._ohlc_data[sym] = []
        self._ohlc_data[sym].extend(bars)
        self._ohlc_data[sym].sort(key=lambda b: b.date)

    def set_current_price(self, symbol: str, price: float) -> None:
        self._current_prices[symbol.upper()] = price

    def resolve_stock(self, query: str) -> Optional[Stock]:
        q = query.strip().upper()
        # Direct symbol match
        if q in self._stocks:
            return self._stocks[q]
        # Partial match on company name or symbol
        for stock in self._stocks.values():
            if q == stock.symbol or q in stock.company_name.upper():
                return stock
        return None

    def get_historical_ohlc(
        self,
        stock: Stock,
        start_date: date,
        end_date: date,
    ) -> Sequence[NormalizedOHLC]:
        sym = stock.symbol.upper()
        bars = self._ohlc_data.get(sym, [])
        return [b for b in bars if start_date <= b.date <= end_date]

    def get_reference_day_data(
        self,
        stock: Stock,
        target_date: date,
    ) -> Optional[NormalizedOHLC]:
        sym = stock.symbol.upper()
        bars = self._ohlc_data.get(sym, [])
        future_bars = [b for b in bars if b.date >= target_date]
        if future_bars:
            return min(future_bars, key=lambda b: b.date)
        return None

    def get_current_price(
        self,
        stock: Stock,
    ) -> tuple[float, PriceType, MarketSessionStatus]:
        sym = stock.symbol.upper()
        price = self._current_prices.get(sym, 1000.0)
        price_type = PriceType.LIVE if self._market_status == MarketSessionStatus.OPEN else PriceType.CLOSE
        return price, price_type, self._market_status

    def get_market_status(self) -> MarketSessionStatus:
        return self._market_status
