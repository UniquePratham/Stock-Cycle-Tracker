"""Unit tests for CycleService."""

from datetime import date
import pytest
from stock_cycle_tracker.domain.engine import CycleEngine
from stock_cycle_tracker.domain.models import NormalizedOHLC
from stock_cycle_tracker.providers.mock import MockMarketDataProvider
from stock_cycle_tracker.services.cycle_service import CycleService
from stock_cycle_tracker.storage.db import DatabaseManager
from stock_cycle_tracker.storage.repository import StockCycleRepository


@pytest.fixture
def cycle_service(tmp_path):
    db_mgr = DatabaseManager(tmp_path / "test_cycle_service.db")
    repo = StockCycleRepository(db_mgr)
    provider = MockMarketDataProvider()

    # Pre-register stocks and OHLC
    provider.register_stock("RELIANCE", "Reliance Industries Ltd", current_price=1200.0)
    bars = [
        NormalizedOHLC(date=date(2026, 1, 9), open=1280, high=1300, low=1250, close=1290),
        NormalizedOHLC(date=date(2026, 1, 12), open=1290, high=1300, low=1260, close=1280),
    ]
    provider.add_ohlc_bars("RELIANCE", bars)

    engine = CycleEngine()
    return CycleService(repo, provider, engine)


def test_add_stock_cycle_and_dashboard(cycle_service):
    stock, cycle, analysis = cycle_service.add_stock_cycle("RELIANCE", date(2014, 1, 10))

    assert stock.symbol == "RELIANCE"
    assert cycle.cycle_number == 1
    assert analysis.reference_high == 1300.0
    assert analysis.current_price == 1200.0
    assert analysis.percentage_change == -7.69
    assert analysis.bucket == "Downside 5–10%"

    analyses = cycle_service.get_dashboard_analyses()
    assert len(analyses) == 1
    assert analyses[0].stock_symbol == "RELIANCE"


def test_get_stock_detail(cycle_service):
    cycle_service.add_stock_cycle("RELIANCE", date(2014, 1, 10))
    detail = cycle_service.get_stock_detail("RELIANCE")

    assert "stock" in detail
    assert detail["stock"].symbol == "RELIANCE"
    assert len(detail["cycles"]) == 1
    assert len(detail["analyses"]) == 1
    assert detail["current_price"] == 1200.0
