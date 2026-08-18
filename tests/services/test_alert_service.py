"""Unit tests for AlertService."""

from datetime import date
import pytest
from stock_cycle_tracker.domain.models import (
    CycleAnalysis,
    CycleStatus,
    PriceType,
)
from stock_cycle_tracker.services.alert_service import (
    AlertConditionType,
    AlertService,
)
from stock_cycle_tracker.storage.db import DatabaseManager


@pytest.fixture
def alert_service(tmp_path):
    db_mgr = DatabaseManager(tmp_path / "test_alerts.db")
    return AlertService(db_mgr)


def test_alert_lifecycle_and_evaluation(alert_service):
    # Create an alert for RELIANCE % change <= -10%
    alert = alert_service.add_alert(
        stock_symbol="RELIANCE",
        cycle_number=1,
        condition_type=AlertConditionType.PERCENTAGE_BELOW,
        threshold_value=-10.0,
    )
    assert alert.id is not None
    assert alert.is_enabled is True

    # Dummy analyses
    a1 = CycleAnalysis(
        stock_symbol="RELIANCE",
        company_name="Reliance Industries Ltd",
        cycle_number=1,
        original_reference_date=date(2014, 1, 10),
        recurring_reference_date=date(2026, 1, 10),
        actual_reference_trading_date=date(2026, 1, 12),
        exchange="NSE",
        reference_high=1300.0,
        reference_low=1250.0,
        current_price=1150.0,
        price_type=PriceType.CLOSE,
        calculation_date=date(2026, 8, 16),
        percentage_change=-11.54,
        bucket="Downside 10–15%",
        cycle_start_date=date(2026, 1, 10),
        cycle_end_date=date(2027, 1, 9),
    )

    events = alert_service.evaluate_analyses([a1])
    assert len(events) == 1
    assert events[0].stock_symbol == "RELIANCE"
    assert "% Change <= -10.0%" in events[0].condition_summary

    # Toggle alert off
    alert_service.toggle_alert(alert.id, False)
    events2 = alert_service.evaluate_analyses([a1])
    assert len(events2) == 0
