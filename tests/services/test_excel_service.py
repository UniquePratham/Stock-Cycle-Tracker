"""Unit tests for ExcelService."""

from datetime import date
import io
import openpyxl
import pandas as pd
import pytest
from stock_cycle_tracker.domain.engine import CycleEngine
from stock_cycle_tracker.domain.models import NormalizedOHLC
from stock_cycle_tracker.providers.mock import MockMarketDataProvider
from stock_cycle_tracker.services.cycle_service import CycleService
from stock_cycle_tracker.services.excel_service import ExcelService
from stock_cycle_tracker.storage.db import DatabaseManager
from stock_cycle_tracker.storage.repository import StockCycleRepository


@pytest.fixture
def service_setup(tmp_path):
    db_mgr = DatabaseManager(tmp_path / "test_excel.db")
    repo = StockCycleRepository(db_mgr)
    provider = MockMarketDataProvider()
    provider.register_stock("RELIANCE", "Reliance Industries Ltd", current_price=1200.0)
    provider.register_stock("TCS", "Tata Consultancy Services", current_price=3400.0)
    provider.add_ohlc_bars("RELIANCE", [NormalizedOHLC(date=date(2026, 1, 12), open=1280, high=1300, low=1250, close=1290)])
    provider.add_ohlc_bars("TCS", [NormalizedOHLC(date=date(2026, 1, 30), open=3000, high=3000, low=2900, close=2950)])

    cycle_service = CycleService(repo, provider, CycleEngine())
    excel_service = ExcelService()
    return cycle_service, excel_service


def test_excel_upload_and_import(service_setup):
    cycle_service, excel_service = service_setup

    # Create in-memory sample excel
    df = pd.DataFrame([
        {"Stock Name": "RELIANCE", "Reference Date": "10-Jan-2014"},
        {"Stock Name": "TCS", "Reference Date": "2016-01-30"},
        {"Stock Name": "", "Reference Date": "15-Jul-2019"},  # Invalid empty stock
        {"Stock Name": "INFY", "Reference Date": "invalid-date"},  # Invalid date
    ])

    bio = io.BytesIO()
    df.to_excel(bio, index=False)
    bio.seek(0)

    # 1. Validate & parse
    result = excel_service.validate_and_parse_upload(bio)
    assert result.total_rows == 4
    assert len(result.valid_rows) == 2
    assert len(result.invalid_rows) == 2

    # 2. Import
    imported_count, analyses = excel_service.import_validated_rows(cycle_service, result.valid_rows)
    assert imported_count == 2
    assert len(analyses) == 2


def test_excel_export_18_columns(service_setup):
    cycle_service, excel_service = service_setup
    cycle_service.add_stock_cycle("RELIANCE", date(2014, 1, 10))
    analyses = cycle_service.get_dashboard_analyses()

    # Export
    excel_bytes = excel_service.export_analyses_to_excel(analyses)
    assert len(excel_bytes) > 0

    # Verify sheet contents with openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
    ws = wb.active
    assert ws.title == "Cycle Analysis"
    assert ws.max_column == 19
    assert ws.cell(row=1, column=1).value == "S.No."
    assert ws.cell(row=1, column=2).value == "Stock Name"
    assert ws.cell(row=1, column=19).value == "Last Data Refresh"

    # Data row check
    assert ws.cell(row=2, column=2).value == "RELIANCE"
    assert ws.cell(row=2, column=4).value == "Cycle 1"
