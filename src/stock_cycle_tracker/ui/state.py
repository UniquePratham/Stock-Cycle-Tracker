"""UI state and dependency injection container."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from stock_cycle_tracker.domain.engine import CycleEngine
from stock_cycle_tracker.domain.models import MarketSessionStatus
from stock_cycle_tracker.providers.cached_provider import CachedMarketDataProvider
from stock_cycle_tracker.providers.composite import CompositeMarketDataProvider
from stock_cycle_tracker.services.alert_service import AlertService
from stock_cycle_tracker.services.cycle_service import CycleService
from stock_cycle_tracker.services.excel_service import ExcelService
from stock_cycle_tracker.services.stock_search_service import StockSearchService
from stock_cycle_tracker.storage.db import DatabaseManager
from stock_cycle_tracker.storage.repository import StockCycleRepository


class ServiceContainer:
    """Singleton service locator for the application."""

    _instance: Optional[ServiceContainer] = None

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_manager = DatabaseManager(db_path or "stock_cycle_tracker.db")
        self.repository = StockCycleRepository(self.db_manager)
        self.provider = CachedMarketDataProvider(CompositeMarketDataProvider())
        self.engine = CycleEngine()
        self.cycle_service = CycleService(self.repository, self.provider, self.engine)
        self.excel_service = ExcelService()
        self.alert_service = AlertService(self.db_manager)
        self.stock_search_service = StockSearchService()

    @classmethod
    def get(cls, db_path: Optional[str] = None) -> ServiceContainer:
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance

    @classmethod
    def reset(cls, instance: Optional[ServiceContainer] = None) -> None:
        cls._instance = instance
