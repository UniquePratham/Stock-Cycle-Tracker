"""Tests for MockMarketDataProvider."""

from datetime import date
import pytest
from stock_cycle_tracker.domain.models import (
    ExchangePreference,
    MarketSessionStatus,
    NormalizedOHLC,
    PriceType,
)
from stock_cycle_tracker.providers.mock import MockMarketDataProvider


def test_resolve_stock_and_quotes():
    provider = MockMarketDataProvider()
    stock = provider.register_stock(
        symbol="INFY",
        company_name="Infosys Limited",
        nse_symbol="INFY",
        bse_code="500209",
        current_price=1800.0,
    )

    resolved = provider.resolve_stock("infy")
    assert resolved is not None
    assert resolved.symbol == "INFY"
    assert resolved.company_name == "Infosys Limited"

    price, p_type, m_status = provider.get_current_price(resolved)
    assert price == 1800.0
    assert p_type == PriceType.CLOSE
    assert m_status == MarketSessionStatus.CLOSED

    # Test open market mode
    provider.set_market_status(MarketSessionStatus.OPEN)
    price, p_type, m_status = provider.get_current_price(resolved)
    assert p_type == PriceType.LIVE
    assert m_status == MarketSessionStatus.OPEN


def test_historical_ohlc_and_reference_day():
    provider = MockMarketDataProvider()
    stock = provider.register_stock("TCS", "Tata Consultancy Services")

    bars = [
        NormalizedOHLC(date=date(2026, 1, 9), open=3000, high=3050, low=2980, close=3020),
        NormalizedOHLC(date=date(2026, 1, 12), open=3030, high=3100, low=3010, close=3080),
        NormalizedOHLC(date=date(2026, 1, 13), open=3080, high=3120, low=3050, close=3110),
    ]
    provider.add_ohlc_bars("TCS", bars)

    history = provider.get_historical_ohlc(stock, date(2026, 1, 9), date(2026, 1, 12))
    assert len(history) == 2

    # Request Saturday 10-Jan-2026 -> resolves to Monday 12-Jan-2026 bar
    ref_bar = provider.get_reference_day_data(stock, date(2026, 1, 10))
    assert ref_bar is not None
    assert ref_bar.date == date(2026, 1, 12)
    assert ref_bar.high == 3100
