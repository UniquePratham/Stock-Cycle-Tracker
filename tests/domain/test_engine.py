"""Unit tests for CycleEngine."""

from datetime import date
import pytest
from stock_cycle_tracker.domain.engine import CycleEngine
from stock_cycle_tracker.domain.models import (
    Cycle,
    ExchangePreference,
    NormalizedOHLC,
    PriceType,
    Stock,
)


def create_mock_ohlc(start_date: date, end_date: date, base_high: float = 1300.0) -> list[NormalizedOHLC]:
    """Generates continuous weekday OHLC bars."""
    bars = []
    curr = start_date
    while curr <= end_date:
        # Only weekdays
        if curr.weekday() < 5:
            bars.append(
                NormalizedOHLC(
                    date=curr,
                    open=base_high - 20,
                    high=base_high,
                    low=base_high - 50,
                    close=base_high - 10,
                    volume=100000,
                    source="NSE",
                )
            )
        curr = date.fromordinal(curr.toordinal() + 1)
    return bars


def test_basic_cycle_reliance_scenario():
    engine = CycleEngine()
    stock = Stock(
        symbol="RELIANCE",
        company_name="Reliance Industries Ltd",
        preferred_exchange=ExchangePreference.NSE,
    )
    cycle = Cycle(
        reference_date=date(2014, 1, 10),
        cycle_number=1,
    )

    # 10 Jan 2026 is Saturday -> next trading day is 12 Jan 2026
    ohlc = create_mock_ohlc(date(2026, 1, 1), date(2026, 8, 16), base_high=1300.0)

    # As of 16-Aug-2026, current price is 1170.0 -> -10% -> Downside 5-10% (-10% <= x < -5%)
    analysis = engine.compute_analysis(
        stock=stock,
        cycle=cycle,
        historical_ohlc=ohlc,
        current_price=1170.0,
        price_type=PriceType.CLOSE,
        as_of_date=date(2026, 8, 16),
    )

    assert analysis.stock_symbol == "RELIANCE"
    assert analysis.cycle_number == 1
    assert analysis.original_reference_date == date(2014, 1, 10)
    assert analysis.recurring_reference_date == date(2026, 1, 10)
    assert analysis.actual_reference_trading_date == date(2026, 1, 12)
    assert analysis.cycle_start_date == date(2026, 1, 10)
    assert analysis.cycle_end_date == date(2027, 1, 9)
    assert analysis.reference_high == 1300.0
    assert analysis.current_price == 1170.0
    assert analysis.percentage_change == -10.0
    assert analysis.bucket == "Downside 5–10%"


def test_cycle_upside_calculation():
    engine = CycleEngine()
    stock = Stock(symbol="TCS", company_name="Tata Consultancy Services")
    cycle = Cycle(reference_date=date(2016, 1, 30), cycle_number=1)

    ohlc = create_mock_ohlc(date(2026, 1, 1), date(2026, 8, 16), base_high=3000.0)

    # Current price 3450.0 -> +15% -> Upside 10-15% (10 < x <= 15)
    analysis = engine.compute_analysis(
        stock=stock,
        cycle=cycle,
        historical_ohlc=ohlc,
        current_price=3450.0,
        price_type=PriceType.LIVE,
        as_of_date=date(2026, 8, 16),
    )

    assert analysis.reference_high == 3000.0
    assert analysis.percentage_change == 15.0
    assert analysis.bucket == "Upside 10–15%"
    assert analysis.price_type == PriceType.LIVE


def test_cycle_year_transition_before_reference_date():
    engine = CycleEngine()
    # If today is 05-Jan-2026 and research date is 10-Jan-2014,
    # the active cycle is 10-Jan-2025 -> 09-Jan-2026.
    cycle_year = engine.determine_active_cycle_year(
        original_ref_date=date(2014, 1, 10),
        as_of_date=date(2026, 1, 5),
    )
    assert cycle_year == 2025

    start_date, end_date = engine.calculate_cycle_boundaries(date(2014, 1, 10), 2025)
    assert start_date == date(2025, 1, 10)
    assert end_date == date(2026, 1, 9)


def test_multiple_independent_cycles_for_same_stock():
    engine = CycleEngine()
    stock = Stock(symbol="RELIANCE", company_name="Reliance Industries Ltd")

    cycle1 = Cycle(reference_date=date(2014, 1, 10), cycle_number=1)
    cycle2 = Cycle(reference_date=date(2016, 1, 30), cycle_number=2)
    cycle3 = Cycle(reference_date=date(2019, 7, 15), cycle_number=3)

    # Setup OHLC with different highs on different dates
    ohlc = create_mock_ohlc(date(2026, 1, 1), date(2026, 8, 16), base_high=1000.0)

    # Put distinct highs on specific trading dates
    ohlc_dict = {b.date: b for b in ohlc}
    ohlc_dict[date(2026, 1, 12)] = NormalizedOHLC(date=date(2026, 1, 12), open=900, high=1200, low=850, close=1000)
    ohlc_dict[date(2026, 1, 30)] = NormalizedOHLC(date=date(2026, 1, 30), open=1000, high=1400, low=950, close=1100)
    ohlc_dict[date(2026, 7, 15)] = NormalizedOHLC(date=date(2026, 7, 15), open=1100, high=1600, low=1050, close=1200)

    custom_ohlc = list(ohlc_dict.values())

    a1 = engine.compute_analysis(stock, cycle1, custom_ohlc, current_price=1320.0, as_of_date=date(2026, 8, 16))
    a2 = engine.compute_analysis(stock, cycle2, custom_ohlc, current_price=1320.0, as_of_date=date(2026, 8, 16))
    a3 = engine.compute_analysis(stock, cycle3, custom_ohlc, current_price=1320.0, as_of_date=date(2026, 8, 16))

    assert a1.reference_high == 1200.0
    assert a1.percentage_change == 10.0
    assert a1.bucket == "Upside 5–10%"

    assert a2.reference_high == 1400.0
    assert a2.percentage_change == -5.71
    assert a2.bucket == "Downside 5–10%"

    assert a3.reference_high == 1600.0
    assert a3.percentage_change == -17.5
    assert a3.bucket == "Downside 15–20%"
