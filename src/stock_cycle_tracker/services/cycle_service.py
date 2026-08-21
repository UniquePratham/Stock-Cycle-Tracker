"""Cycle application service orchestrating repository, market provider, and cycle engine."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
import urllib.parse
import urllib.request

from stock_cycle_tracker.domain.engine import CycleEngine
from stock_cycle_tracker.domain.models import (
    Cycle,
    CycleAnalysis,
    ExchangePreference,
    NormalizedOHLC,
    PriceType,
    Stock,
)
from stock_cycle_tracker.providers.base import MarketDataProvider
from stock_cycle_tracker.providers.cached_provider import CachedMarketDataProvider
from stock_cycle_tracker.storage.repository import StockCycleRepository

logger = logging.getLogger(__name__)


def sanitize_stock_query(query: str) -> str:
    """Sanitizes raw user input into a clean stock query string."""
    if not query:
        return ""
    q = query.strip()
    q = re.sub(r'[\'\"`,;:]', '', q)
    q = re.sub(r'^(NSE|BSE|BOM|INDEX|EQUITY)\s*[:\-\s]\s*', '', q, flags=re.IGNORECASE)
    q = re.sub(r'\.(NS|BO|BSE|NSE)$', '', q, flags=re.IGNORECASE)
    q = re.sub(r'\-EQ$', '', q, flags=re.IGNORECASE)
    return q.strip()


def search_indian_stock_online(query: str) -> Optional[Tuple[str, str, ExchangePreference]]:
    """
    Searches Yahoo Finance API to resolve company names/tickers into valid NSE/BSE stocks.
    Returns (clean_symbol, company_name, exchange_preference) or None.
    """
    clean_q = sanitize_stock_query(query)
    if not clean_q:
        return None

    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(clean_q)}&quotesCount=6&newsCount=0"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            quotes = data.get("quotes", [])
            for item in quotes:
                sym = item.get("symbol", "")
                if sym.endswith(".NS"):
                    clean_sym = sym[:-3]
                    name = item.get("shortname") or item.get("longname") or clean_sym
                    return clean_sym, name, ExchangePreference.NSE
                elif sym.endswith(".BO"):
                    clean_sym = sym[:-3]
                    name = item.get("shortname") or item.get("longname") or clean_sym
                    return clean_sym, name, ExchangePreference.BSE
    except Exception as e:
        logger.debug(f"Online stock search failed for '{query}': {e}")

    return None


class CycleService:
    """
    Orchestrates repository, market data provider, and cycle calculation engine.
    """

    def __init__(
        self,
        repository: StockCycleRepository,
        provider: MarketDataProvider,
        engine: Optional[CycleEngine] = None,
    ) -> None:
        self.repo = repository
        self.provider = provider if isinstance(provider, CachedMarketDataProvider) else CachedMarketDataProvider(provider)
        self.engine = engine or CycleEngine()

    def sanitize_and_resolve_stock(self, query: str, company_name: str = "") -> Stock:
        """
        Sanitizes input, checks provider and online search API to ensure valid stock entity.
        Raises ValueError if stock cannot be identified.
        """
        clean_q = sanitize_stock_query(query)
        if not clean_q:
            raise ValueError("Please provide a non-empty stock ticker or company name.")

        # 1. Try resolving via market provider (NSE / BSE / YFinance)
        resolved_stock = self.provider.resolve_stock(clean_q)
        if resolved_stock:
            return resolved_stock

        # 2. Try online search API if direct resolution failed (e.g. user typed "Tata Motors" or "Reliance")
        search_res = search_indian_stock_online(clean_q)
        if search_res:
            sym, name, exch = search_res
            return Stock(
                symbol=sym,
                company_name=name,
                preferred_exchange=exch,
                nse_symbol=sym if exch == ExchangePreference.NSE else None,
                bse_code=sym if exch == ExchangePreference.BSE else None,
            )

        # 3. If looks like a valid alphanumeric ticker, construct standard stock record
        if re.match(r'^[A-Z0-9&\-]+$', clean_q.upper()):
            return Stock(
                symbol=clean_q.upper(),
                company_name=company_name.strip() or clean_q.upper(),
                preferred_exchange=ExchangePreference.NSE,
            )

        raise ValueError(f"Could not find a valid Indian stock for '{query}'. Please check the symbol (e.g. RELIANCE, TCS, INFY).")

    def add_stock_cycle(
        self,
        query: str,
        reference_date: date,
        company_name: str = "",
    ) -> Tuple[Stock, Cycle, CycleAnalysis]:
        """
        Resolves stock, persists stock and cycle in database, and computes initial cycle analysis.
        """
        if reference_date > date.today():
            raise ValueError(f"Research date ({reference_date.strftime('%d-%b-%Y')}) cannot be in the future.")
        if reference_date.year < 1990:
            raise ValueError(f"Research date ({reference_date.strftime('%d-%b-%Y')}) must be after 1990.")

        # 1. Resolve stock via sanitized resolver
        resolved_stock = self.sanitize_and_resolve_stock(query, company_name)

        # 2. Persist stock
        stock = self.repo.create_or_get_stock(resolved_stock)

        # 3. Add cycle record
        cycle = self.repo.add_cycle(
            stock_id=stock.id,
            reference_date=reference_date,
        )

        # 4. Perform initial calculation
        analysis = self._compute_cycle_analysis(stock, cycle)
        self.repo.save_snapshot(analysis, cycle_id=cycle.id)

        return stock, cycle, analysis

    def delete_cycle(self, cycle_id: int) -> bool:
        return self.repo.delete_cycle(cycle_id)

    def delete_stock(self, stock_id: int) -> bool:
        return self.repo.delete_stock(stock_id)

    def list_all_stocks(self) -> List[Stock]:
        return self.repo.list_stocks()

    def get_dashboard_analyses(
        self,
        as_of_date: Optional[date] = None,
        force_refresh: bool = False,
    ) -> List[CycleAnalysis]:
        """
        Fetches all registered stock cycles, batches OHLC retrieval, and calculates analyses.
        """
        if force_refresh and isinstance(self.provider, CachedMarketDataProvider):
            self.provider.clear_cache()

        stock_cycles = self.repo.list_all_cycles()
        if not stock_cycles:
            return []

        analyses: List[CycleAnalysis] = []
        for stock, cycle in stock_cycles:
            try:
                analysis = self._compute_cycle_analysis(stock, cycle, as_of_date=as_of_date)
                analyses.append(analysis)
                self.repo.save_snapshot(analysis, cycle_id=cycle.id)
            except Exception as e:
                logger.error(f"Error computing analysis for {stock.symbol} cycle {cycle.cycle_number}: {e}")

        return analyses

    def get_stock_detail(
        self,
        symbol: str,
        lookback_days: int = 365,
    ) -> Dict[str, Any]:
        """
        Returns full detailed payload for a single stock: metadata, cycles, analyses, and OHLC bars for charting.
        Reads cached history from repository for instantaneous rendering.
        """
        sym = symbol.strip().upper()
        stock = self.repo.get_stock(sym)
        if not stock:
            # Attempt to resolve via provider
            stock = self.provider.resolve_stock(sym)
            if not stock:
                return {}

        cycles = self.repo.list_cycles_for_stock(stock.id) if stock.id else []
        analyses: List[CycleAnalysis] = []
        for c in cycles:
            try:
                analyses.append(self._compute_cycle_analysis(stock, c))
            except Exception as e:
                logger.error(f"Error computing cycle {c.cycle_number} for detail view: {e}")

        # Fetch chart history: Check SQLite cache first for instant load
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)
        ohlc = self.repo.get_cached_ohlc(stock.symbol, start_date, end_date)
        if not ohlc or len(ohlc) < min(20, lookback_days // 3):
            ohlc = list(self.provider.get_historical_ohlc(stock, start_date, end_date))
            if ohlc:
                self.repo.save_cached_ohlc(stock.symbol, ohlc)

        current_price, price_type, market_status = self.provider.get_current_price(stock)

        return {
            "stock": stock,
            "cycles": cycles,
            "analyses": analyses,
            "ohlc": ohlc,
            "current_price": current_price,
            "price_type": price_type,
            "market_status": market_status,
        }

    def _compute_cycle_analysis(
        self,
        stock: Stock,
        cycle: Cycle,
        as_of_date: Optional[date] = None,
    ) -> CycleAnalysis:
        calc_date = as_of_date or date.today()
        active_year = self.engine.determine_active_cycle_year(cycle.reference_date, calc_date)
        recurring_ref_date, _ = self.engine.calculate_cycle_boundaries(cycle.reference_date, active_year)

        # Request OHLC around reference date
        fetch_start = recurring_ref_date - timedelta(days=5)
        fetch_end = calc_date + timedelta(days=1)

        # Check SQLite cache first
        ohlc = list(self.repo.get_cached_ohlc(stock.symbol, fetch_start, fetch_end))
        
        # Verify that we have bars covering the reference window around recurring_ref_date
        has_ref_bars = any(recurring_ref_date <= b.date <= recurring_ref_date + timedelta(days=15) for b in ohlc)
        if not has_ref_bars or not ohlc:
            ref_window_start = recurring_ref_date - timedelta(days=5)
            ref_window_end = recurring_ref_date + timedelta(days=15)
            new_bars = list(self.provider.get_historical_ohlc(stock, ref_window_start, ref_window_end))
            if new_bars:
                self.repo.save_cached_ohlc(stock.symbol, new_bars)
                # Re-query cached ohlc
                ohlc = list(self.repo.get_cached_ohlc(stock.symbol, fetch_start, fetch_end))
            elif not ohlc:
                full_bars = list(self.provider.get_historical_ohlc(stock, fetch_start, fetch_end))
                if full_bars:
                    self.repo.save_cached_ohlc(stock.symbol, full_bars)
                    ohlc = full_bars

        # Get current price
        current_price, price_type, _ = self.provider.get_current_price(stock)

        # Compute analysis
        return self.engine.compute_analysis(
            stock=stock,
            cycle=cycle,
            historical_ohlc=ohlc,
            current_price=current_price,
            price_type=price_type,
            as_of_date=calc_date,
            data_source=self.provider.provider_name,
        )
