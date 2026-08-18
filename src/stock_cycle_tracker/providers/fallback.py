"""Yahoo Finance adapter provider."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import logging
from typing import Optional, Sequence

import pandas as pd
import yfinance as yf

from stock_cycle_tracker.domain.models import (
    ExchangePreference,
    MarketSessionStatus,
    NormalizedOHLC,
    PriceType,
    Stock,
)
from stock_cycle_tracker.providers.base import MarketDataProvider
from stock_cycle_tracker.providers.session import MarketSessionInspector

logger = logging.getLogger(__name__)


class YFinanceFallbackProvider(MarketDataProvider):
    """
    Adapter for Yahoo Finance market data.
    Encapsulates ticker suffixes (.NS / .BO) so the domain remains clean.
    """

    def __init__(
        self,
        default_exchange: ExchangePreference = ExchangePreference.NSE,
        session_inspector: Optional[MarketSessionInspector] = None,
    ) -> None:
        self._default_exchange = default_exchange
        self.session_inspector = session_inspector or MarketSessionInspector()

    @property
    def provider_name(self) -> str:
        return "YahooFinance"

    def _get_ticker_symbol(self, stock: Stock) -> str:
        sym = stock.symbol.strip().replace(" ", "").upper()
        if sym.endswith(".NS") or sym.endswith(".BO"):
            return sym

        if stock.preferred_exchange == ExchangePreference.BSE or stock.bse_code:
            code = (stock.bse_code or sym).replace(" ", "")
            return f"{code}.BO"
        nse_sym = (stock.nse_symbol or sym).replace(" ", "")
        return f"{nse_sym}.NS"

    def resolve_stock(self, query: str) -> Optional[Stock]:
        q = query.strip().upper().replace(" ", "")
        # Strip potential suffixes if user entered them
        clean_sym = q.replace(".NS", "").replace(".BO", "")

        # Try NSE ticker first
        try:
            ticker_nse = yf.Ticker(f"{clean_sym}.NS")
            hist = ticker_nse.history(period="5d")
            if not hist.empty:
                info = ticker_nse.info if hasattr(ticker_nse, "info") else {}
                long_name = info.get("longName") or info.get("shortName") or clean_sym
                return Stock(
                    symbol=clean_sym,
                    company_name=long_name,
                    nse_symbol=clean_sym,
                    preferred_exchange=ExchangePreference.NSE,
                )
        except Exception as e:
            logger.debug(f"Error resolving NSE ticker {clean_sym}.NS: {e}")

        # Try BSE ticker next
        try:
            ticker_bse = yf.Ticker(f"{clean_sym}.BO")
            hist_bse = ticker_bse.history(period="5d")
            if not hist_bse.empty:
                info = ticker_bse.info if hasattr(ticker_bse, "info") else {}
                long_name = info.get("longName") or info.get("shortName") or clean_sym
                return Stock(
                    symbol=clean_sym,
                    company_name=long_name,
                    bse_code=clean_sym,
                    preferred_exchange=ExchangePreference.BSE,
                )
        except Exception as e:
            logger.debug(f"Error resolving BSE ticker {clean_sym}.BO: {e}")

        return None

    def get_historical_ohlc(
        self,
        stock: Stock,
        start_date: date,
        end_date: date,
    ) -> Sequence[NormalizedOHLC]:
        ticker_sym = self._get_ticker_symbol(stock)
        try:
            # yfinance end date is exclusive, so add 1 day
            end_plus_one = end_date + timedelta(days=1)
            ticker = yf.Ticker(ticker_sym)
            df = ticker.history(start=start_date.isoformat(), end=end_plus_one.isoformat())
            if df.empty:
                return []

            bars: list[NormalizedOHLC] = []
            for ts, row in df.iterrows():
                dt = ts.date() if isinstance(ts, (pd.Timestamp, datetime)) else date.fromisoformat(str(ts)[:10])
                bars.append(
                    NormalizedOHLC(
                        date=dt,
                        open=float(row.get("Open", 0.0)),
                        high=float(row.get("High", 0.0)),
                        low=float(row.get("Low", 0.0)),
                        close=float(row.get("Close", 0.0)),
                        volume=int(row.get("Volume", 0)),
                        source=self.provider_name,
                    )
                )
            bars.sort(key=lambda b: b.date)
            return bars
        except Exception as e:
            logger.error(f"Error fetching historical OHLC for {ticker_sym}: {e}")
            return []

    def get_reference_day_data(
        self,
        stock: Stock,
        target_date: date,
    ) -> Optional[NormalizedOHLC]:
        # Fetch a 15-day window to guarantee finding the trading day on or after target_date
        window_end = target_date + timedelta(days=15)
        bars = self.get_historical_ohlc(stock, target_date, window_end)
        future_bars = [b for b in bars if b.date >= target_date]
        if future_bars:
            return min(future_bars, key=lambda b: b.date)
        return None

    def get_current_price(
        self,
        stock: Stock,
    ) -> tuple[float, PriceType, MarketSessionStatus]:
        ticker_sym = self._get_ticker_symbol(stock)
        market_status = self.get_market_status()
        price_type = PriceType.LIVE if market_status == MarketSessionStatus.OPEN else PriceType.CLOSE

        try:
            ticker = yf.Ticker(ticker_sym)
            # Use 1d history or fast_info
            price = 0.0
            if hasattr(ticker, "fast_info") and ticker.fast_info:
                price = float(getattr(ticker.fast_info, "last_price", 0.0) or 0.0)

            if price <= 0:
                hist = ticker.history(period="5d")
                if not hist.empty:
                    price = float(hist["Close"].iloc[-1])

            return price, price_type, market_status
        except Exception as e:
            logger.error(f"Error fetching current price for {ticker_sym}: {e}")
            return 0.0, price_type, market_status

    def get_market_status(self) -> MarketSessionStatus:
        return self.session_inspector.get_market_status()
