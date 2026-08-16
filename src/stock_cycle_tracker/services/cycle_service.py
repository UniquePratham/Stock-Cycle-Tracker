"""Cycle application service."""

from __future__ import annotations

from datetime import date, timedelta
import logging
from typing import Any, Dict, List, Optional, Tuple

from stock_cycle_tracker.domain.engine import CycleEngine
from stock_cycle_tracker.domain.models import (
    Cycle,
    CycleAnalysis,
    NormalizedOHLC,
    PriceType,
    Stock,
)
from stock_cycle_tracker.providers.base import MarketDataProvider
from stock_cycle_tracker.providers.cached_provider import CachedMarketDataProvider
from stock_cycle_tracker.storage.repository import StockCycleRepository

logger = logging.getLogger(__name__)


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

    def add_stock_cycle(
        self,
        query: str,
        reference_date: date,
        company_name: str = "",
    ) -> Tuple[Stock, Cycle, CycleAnalysis]:
        """
        Resolves stock, persists stock and cycle in database, and computes initial cycle analysis.
        """
        # 1. Resolve stock via provider
        resolved_stock = self.provider.resolve_stock(query)
        if not resolved_stock:
            # Create standard fallback stock record
            resolved_stock = Stock(
                symbol=query.strip().upper(),
                company_name=company_name or query.strip().upper(),
            )

        # 2. Persist stock
        stock = self.repo.create_or_get_stock(resolved_stock)

        # 3. Add cycle record
        cycle = self.repo.add_cycle(stock.id, reference_date)

        # 4. Compute analysis
        analysis = self._compute_cycle_analysis(stock, cycle)

        # 5. Persist snapshot
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
        if not ohlc or len(ohlc) < 20:
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
        ohlc = self.repo.get_cached_ohlc(stock.symbol, fetch_start, fetch_end)
        if not ohlc:
            ohlc = list(self.provider.get_historical_ohlc(stock, fetch_start, fetch_end))
            if ohlc:
                self.repo.save_cached_ohlc(stock.symbol, ohlc)

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
