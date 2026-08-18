"""End-to-End Acceptance Tests verifying all 7 Scenarios from Section 39."""

from datetime import date
import io
import openpyxl
import pandas as pd
import pytest

from stock_cycle_tracker.domain.engine import CycleEngine
from stock_cycle_tracker.domain.models import (
    ExchangePreference,
    MarketSessionStatus,
    NormalizedOHLC,
    PriceType,
    Stock,
)
from stock_cycle_tracker.providers.composite import CompositeMarketDataProvider
from stock_cycle_tracker.providers.mock import MockMarketDataProvider
from stock_cycle_tracker.services.alert_service import AlertConditionType, AlertService
from stock_cycle_tracker.services.cycle_service import CycleService
from stock_cycle_tracker.services.excel_service import ExcelService
from stock_cycle_tracker.storage.db import DatabaseManager
from stock_cycle_tracker.storage.repository import StockCycleRepository


@pytest.fixture
def e2e_harness(tmp_path):
    """Hermetic test harness for end-to-end acceptance testing."""
    db_file = tmp_path / "e2e_test.db"
    db_mgr = DatabaseManager(db_file)
    repo = StockCycleRepository(db_mgr)

    nse_mock = MockMarketDataProvider(name="MockNSE", default_exchange=ExchangePreference.NSE)
    bse_mock = MockMarketDataProvider(name="MockBSE", default_exchange=ExchangePreference.BSE)
    fallback_mock = MockMarketDataProvider(name="MockFallback", default_exchange=ExchangePreference.NSE)

    composite = CompositeMarketDataProvider(
        nse_provider=nse_mock,
        bse_provider=bse_mock,
        fallback_provider=fallback_mock,
    )

    engine = CycleEngine()
    cycle_service = CycleService(repo, composite, engine)
    excel_service = ExcelService()
    alert_service = AlertService(db_mgr)

    return {
        "repo": repo,
        "nse": nse_mock,
        "bse": bse_mock,
        "fallback": fallback_mock,
        "composite": composite,
        "engine": engine,
        "cycle_service": cycle_service,
        "excel_service": excel_service,
        "alert_service": alert_service,
    }


def test_scenario_1_and_2_basic_cycle_and_holiday_resolution(e2e_harness):
    """
    Scenario 1 & 2:
    Input: RELIANCE with Research Date 10-Jan-2014.
    In 2026, 10-Jan is Saturday (non-trading).
    Actual trading date resolves to Monday 12-Jan-2026.
    Reference High is taken from 12-Jan-2026.
    Percentage change and bucket are calculated accurately.
    """
    cs: CycleService = e2e_harness["cycle_service"]
    nse: MockMarketDataProvider = e2e_harness["nse"]

    # Register RELIANCE with current price 1170.0 and 12-Jan High 1300.0
    nse.register_stock("RELIANCE", "Reliance Industries Ltd", current_price=1170.0)
    bars = [
        NormalizedOHLC(date=date(2026, 1, 9), open=1270, high=1290, low=1250, close=1280),
        NormalizedOHLC(date=date(2026, 1, 12), open=1280, high=1300, low=1260, close=1295),
    ]
    nse.add_ohlc_bars("RELIANCE", bars)

    stock, cycle, analysis = cs.add_stock_cycle("RELIANCE", date(2014, 1, 10))

    # Assertions
    assert analysis.stock_symbol == "RELIANCE"
    assert analysis.original_reference_date == date(2014, 1, 10)
    assert analysis.recurring_reference_date == date(2026, 1, 10)
    assert analysis.actual_reference_trading_date == date(2026, 1, 12)
    assert analysis.reference_high == 1300.0
    assert analysis.current_price == 1170.0
    assert analysis.percentage_change == -10.0
    assert analysis.bucket == "Downside 5–10%"
    assert analysis.cycle_start_date == date(2026, 1, 10)
    assert analysis.cycle_end_date == date(2027, 1, 9)


def test_scenario_3_new_year_cycle_transition(e2e_harness):
    """
    Scenario 3:
    Cycle boundary: On 10-Jan-2026, cycle runs 10-Jan-2026 -> 09-Jan-2027.
    When 10-Jan-2027 arrives, a new annual cycle starts: 10-Jan-2027 -> 09-Jan-2028.
    """
    cs: CycleService = e2e_harness["cycle_service"]
    nse: MockMarketDataProvider = e2e_harness["nse"]

    nse.register_stock("TCS", "Tata Consultancy Services", current_price=3500.0)
    nse.add_ohlc_bars(
        "TCS",
        [
            NormalizedOHLC(date=date(2026, 1, 12), open=3000, high=3100, low=2950, close=3050),
            NormalizedOHLC(date=date(2027, 1, 11), open=3300, high=3400, low=3250, close=3350),
        ],
    )

    stock, cycle, analysis_2026 = cs.add_stock_cycle("TCS", date(2016, 1, 10))

    # Test as of 2026
    assert analysis_2026.cycle_start_date == date(2026, 1, 10)
    assert analysis_2026.cycle_end_date == date(2027, 1, 9)

    # Test when evaluated in 2027
    engine: CycleEngine = e2e_harness["engine"]
    analysis_2027 = engine.compute_analysis(
        stock=stock,
        cycle=cycle,
        historical_ohlc=nse.get_historical_ohlc(stock, date(2027, 1, 1), date(2027, 1, 20)),
        current_price=3500.0,
        as_of_date=date(2027, 2, 1),
    )
    assert analysis_2027.cycle_start_date == date(2027, 1, 10)
    assert analysis_2027.cycle_end_date == date(2028, 1, 9)
    assert analysis_2027.reference_high == 3400.0


def test_scenario_4_multiple_independent_cycles_per_stock(e2e_harness):
    """
    Scenario 4:
    RELIANCE has Cycle 1 (10-Jan-2014), Cycle 2 (30-Jan-2016), Cycle 3 (15-Jul-2019).
    All 3 are independently calculated.
    """
    cs: CycleService = e2e_harness["cycle_service"]
    nse: MockMarketDataProvider = e2e_harness["nse"]

    nse.register_stock("RELIANCE", "Reliance Industries Ltd", current_price=1320.0)
    bars = [
        NormalizedOHLC(date=date(2026, 1, 12), open=1100, high=1200, low=1050, close=1150),
        NormalizedOHLC(date=date(2026, 1, 30), open=1300, high=1400, low=1250, close=1350),
        NormalizedOHLC(date=date(2026, 7, 15), open=1500, high=1600, low=1450, close=1550),
    ]
    nse.add_ohlc_bars("RELIANCE", bars)

    _, c1, a1 = cs.add_stock_cycle("RELIANCE", date(2014, 1, 10))
    _, c2, a2 = cs.add_stock_cycle("RELIANCE", date(2016, 1, 30))
    _, c3, a3 = cs.add_stock_cycle("RELIANCE", date(2019, 7, 15))

    assert c1.cycle_number == 1
    assert c2.cycle_number == 2
    assert c3.cycle_number == 3

    assert a1.reference_high == 1200.0
    assert a1.percentage_change == 10.0
    assert a1.bucket == "Upside 5–10%"

    assert a2.reference_high == 1400.0
    assert a2.percentage_change == -5.71
    assert a2.bucket == "Downside 5–10%"

    assert a3.reference_high == 1600.0
    assert a3.percentage_change == -17.5
    assert a3.bucket == "Downside 15–20%"


def test_scenario_5_nse_bse_resolution_hierarchy(e2e_harness):
    """
    Scenario 5:
    If stock is on NSE -> NSE wins.
    If stock is only on BSE -> BSE is used.
    """
    cs: CycleService = e2e_harness["cycle_service"]
    nse: MockMarketDataProvider = e2e_harness["nse"]
    bse: MockMarketDataProvider = e2e_harness["bse"]

    # Stock 1 exists on both NSE and BSE -> NSE should be preferred
    nse.register_stock("INFY", "Infosys (NSE)", current_price=1800.0)
    bse.register_stock("INFY", "Infosys (BSE)", current_price=1799.0)
    nse.add_ohlc_bars("INFY", [NormalizedOHLC(date=date(2026, 1, 12), open=1700, high=1750, low=1680, close=1720)])

    s1, _, a1 = cs.add_stock_cycle("INFY", date(2015, 1, 10))
    assert s1.preferred_exchange == ExchangePreference.NSE
    assert a1.exchange == "NSE"

    # Stock 2 exists ONLY on BSE
    bse.register_stock("BSEONLY", "BSE Small Cap Security", current_price=250.0, preferred_exchange=ExchangePreference.BSE)
    bse.add_ohlc_bars("BSEONLY", [NormalizedOHLC(date=date(2026, 1, 12), open=200, high=220, low=190, close=210)])

    s2, _, a2 = cs.add_stock_cycle("BSEONLY", date(2018, 1, 10))
    assert s2.preferred_exchange == ExchangePreference.BSE
    assert a2.exchange == "BSE"


def test_scenario_6_excel_import_and_export(e2e_harness):
    """
    Scenario 6:
    Upload Excel with (Stock Name, Reference Date).
    Verify validation and automated cycle creation.
    Download full 18-column Excel analysis and verify schema.
    """
    cs: CycleService = e2e_harness["cycle_service"]
    excel_svc: ExcelService = e2e_harness["excel_service"]
    nse: MockMarketDataProvider = e2e_harness["nse"]

    nse.register_stock("RELIANCE", "Reliance Industries Ltd", current_price=1200.0)
    nse.register_stock("TCS", "Tata Consultancy Services", current_price=3300.0)
    nse.add_ohlc_bars("RELIANCE", [NormalizedOHLC(date=date(2026, 1, 12), open=1280, high=1300, low=1250, close=1290)])
    nse.add_ohlc_bars("TCS", [NormalizedOHLC(date=date(2026, 1, 30), open=2950, high=3000, low=2900, close=2980)])

    # Create test excel sheet in memory
    df = pd.DataFrame([
        {"Stock Name": "RELIANCE", "Reference Date": "10-Jan-2014"},
        {"Stock Name": "TCS", "Reference Date": "30-Jan-2016"},
    ])
    bio = io.BytesIO()
    df.to_excel(bio, index=False)
    bio.seek(0)

    # 1. Parse and import
    parsed = excel_svc.validate_and_parse_upload(bio)
    assert parsed.total_rows == 2
    assert len(parsed.valid_rows) == 2

    imported, analyses = excel_svc.import_validated_rows(cs, parsed.valid_rows)
    assert imported == 2
    assert len(analyses) == 2

    # 2. Export full calculated Excel
    exported_bytes = excel_svc.export_analyses_to_excel(analyses)
    wb = openpyxl.load_workbook(io.BytesIO(exported_bytes))
    ws = wb.active

    assert ws.max_column == 19
    assert ws.cell(row=1, column=1).value == "S.No."
    assert ws.cell(row=1, column=2).value == "Stock Name"
    assert ws.cell(row=1, column=9).value == "Reference High"
    assert ws.cell(row=1, column=10).value == "Reference Low"
    assert ws.cell(row=1, column=11).value == "Current Price"
    assert ws.cell(row=1, column=12).value == "Price Type"
    assert ws.cell(row=1, column=14).value == "% Change"
    assert ws.cell(row=1, column=15).value == "Bucket"


def test_scenario_7_market_status_price_modes(e2e_harness):
    """
    Scenario 7:
    During market hours: LIVE price mode.
    After market close: CLOSE price mode.
    """
    cs: CycleService = e2e_harness["cycle_service"]
    nse: MockMarketDataProvider = e2e_harness["nse"]

    nse.register_stock("INFY", "Infosys Limited", current_price=1750.0)
    nse.add_ohlc_bars("INFY", [NormalizedOHLC(date=date(2026, 1, 12), open=1600, high=1700, low=1580, close=1650)])

    # 1. Market Closed Mode
    nse.set_market_status(MarketSessionStatus.CLOSED)
    _, _, analysis_closed = cs.add_stock_cycle("INFY", date(2014, 1, 10))
    assert analysis_closed.price_type == PriceType.CLOSE

    # 2. Market Open Mode
    nse.set_market_status(MarketSessionStatus.OPEN)
    analyses_live = cs.get_dashboard_analyses(force_refresh=True)
    assert len(analyses_live) == 1
    assert analyses_live[0].price_type == PriceType.LIVE
