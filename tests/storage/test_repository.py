"""Unit tests for SQLite repository."""

from datetime import date
import pytest
from stock_cycle_tracker.domain.models import (
    ExchangePreference,
    NormalizedOHLC,
    Stock,
)
from stock_cycle_tracker.storage.db import DatabaseManager
from stock_cycle_tracker.storage.repository import StockCycleRepository


@pytest.fixture
def repo(tmp_path):
    db_file = tmp_path / "test_stocks.db"
    db_mgr = DatabaseManager(db_file)
    return StockCycleRepository(db_mgr)


def test_stock_crud(repo):
    stock = Stock(
        symbol="RELIANCE",
        company_name="Reliance Industries Ltd",
        preferred_exchange=ExchangePreference.NSE,
    )
    saved = repo.create_or_get_stock(stock)
    assert saved.id is not None
    assert saved.symbol == "RELIANCE"

    fetched = repo.get_stock("reliance")
    assert fetched is not None
    assert fetched.id == saved.id
    assert fetched.company_name == "Reliance Industries Ltd"

    stocks = repo.list_stocks()
    assert len(stocks) == 1


def test_cycle_crud_and_auto_numbering(repo):
    stock = repo.create_or_get_stock(Stock(symbol="INFY", company_name="Infosys"))

    # Add cycle 1
    c1 = repo.add_cycle(stock.id, date(2014, 1, 10))
    assert c1.cycle_number == 1
    assert c1.reference_date == date(2014, 1, 10)

    # Add cycle 2
    c2 = repo.add_cycle(stock.id, date(2016, 3, 15))
    assert c2.cycle_number == 2
    assert c2.reference_date == date(2016, 3, 15)

    # Adding duplicate date returns existing cycle without incrementing number
    c1_dup = repo.add_cycle(stock.id, date(2014, 1, 10))
    assert c1_dup.id == c1.id
    assert c1_dup.cycle_number == 1

    cycles = repo.list_cycles_for_stock(stock.id)
    assert len(cycles) == 2

    # Test list_all_cycles
    all_cycles = repo.list_all_cycles()
    assert len(all_cycles) == 2
    assert all_cycles[0][0].symbol == "INFY"
    assert all_cycles[0][1].cycle_number == 1


def test_ohlc_cache(repo):
    bars = [
        NormalizedOHLC(date=date(2026, 1, 12), open=100, high=110, low=95, close=105, volume=5000),
        NormalizedOHLC(date=date(2026, 1, 13), open=105, high=115, low=100, close=110, volume=6000),
    ]
    repo.save_cached_ohlc("TCS", bars)

    cached = repo.get_cached_ohlc("TCS", date(2026, 1, 1), date(2026, 1, 15))
    assert len(cached) == 2
    assert cached[0].high == 110.0
