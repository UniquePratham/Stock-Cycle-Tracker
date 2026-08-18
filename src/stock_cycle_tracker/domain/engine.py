"""Core Cycle Calculation Engine."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional, Sequence

from stock_cycle_tracker.domain.buckets import BucketClassifier
from stock_cycle_tracker.domain.calendar import TradingCalendar
from stock_cycle_tracker.domain.models import (
    Cycle,
    CycleAnalysis,
    CycleStatus,
    NormalizedOHLC,
    PriceType,
    Stock,
    utc_now,
)


class CycleEngine:
    """
    Computes deterministic cycle analysis for a given stock and research date.
    Pure domain logic with zero network/UI dependencies.
    """

    def __init__(
        self,
        calendar: Optional[TradingCalendar] = None,
        bucket_classifier: Optional[BucketClassifier] = None,
    ) -> None:
        self.calendar = calendar or TradingCalendar()
        self.bucket_classifier = bucket_classifier or BucketClassifier()

    def determine_active_cycle_year(
        self,
        original_ref_date: date,
        as_of_date: date,
    ) -> int:
        """
        Determines which annual cycle year is active for as_of_date.
        If as_of_date is before (month, day) in the current calendar year,
        the active cycle belongs to (current_year - 1).
        Otherwise it belongs to current_year.
        """
        curr_year = as_of_date.year
        curr_annual_ref = self.calendar.resolve_annual_occurrence(original_ref_date, curr_year)

        if as_of_date < curr_annual_ref:
            return curr_year - 1
        return curr_year

    def calculate_cycle_boundaries(
        self,
        original_ref_date: date,
        cycle_year: int,
    ) -> tuple[date, date]:
        """
        Calculates (cycle_start_date, cycle_end_date).
        Cycle starts on the recurring reference date of cycle_year,
        and ends on the day before the next recurring reference date (cycle_year + 1).
        """
        start_date = self.calendar.resolve_annual_occurrence(original_ref_date, cycle_year)
        next_cycle_start = self.calendar.resolve_annual_occurrence(original_ref_date, cycle_year + 1)
        end_date = next_cycle_start - timedelta(days=1)
        return start_date, end_date

    def compute_analysis(
        self,
        stock: Stock,
        cycle: Cycle,
        historical_ohlc: Sequence[NormalizedOHLC],
        current_price: float,
        price_type: PriceType = PriceType.CLOSE,
        as_of_date: Optional[date] = None,
        data_source: str = "NSE",
        is_fallback_or_stale: bool = False,
    ) -> CycleAnalysis:
        """
        Executes full cycle analysis for a single stock cycle.
        """
        calc_date = as_of_date or date.today()
        cycle_year = self.determine_active_cycle_year(cycle.reference_date, calc_date)
        recurring_ref_date, cycle_end_date = self.calculate_cycle_boundaries(
            cycle.reference_date, cycle_year
        )

        # Build trading days index from provided OHLC
        ohlc_by_date = {bar.date: bar for bar in historical_ohlc}
        known_dates = sorted(ohlc_by_date.keys())

        # Resolve next available trading day on or after recurring_ref_date
        actual_trading_date = self.calendar.resolve_next_trading_day(
            recurring_ref_date, known_trading_days=known_dates
        )

        # Extract Reference High and Reference Low
        ref_bar = ohlc_by_date.get(actual_trading_date)
        if ref_bar is not None:
            ref_high = float(ref_bar.high)
            ref_low = float(ref_bar.low)
        else:
            # Fallback if no matching bar in slice
            ref_high = current_price
            ref_low = current_price

        # Percentage change relative to Reference High
        if ref_high > 0:
            percentage_change = ((current_price - ref_high) / ref_high) * 100.0
        else:
            percentage_change = 0.0

        # Classify into bucket
        bucket = self.bucket_classifier.classify(percentage_change)

        # Determine cycle status
        if calc_date < recurring_ref_date:
            cycle_status = CycleStatus.UPCOMING
        elif calc_date > cycle_end_date:
            cycle_status = CycleStatus.COMPLETED
        else:
            cycle_status = CycleStatus.ACTIVE

        return CycleAnalysis(
            stock_symbol=stock.symbol,
            company_name=stock.company_name or stock.symbol,
            cycle_number=cycle.cycle_number,
            original_reference_date=cycle.reference_date,
            recurring_reference_date=recurring_ref_date,
            actual_reference_trading_date=actual_trading_date,
            exchange=stock.preferred_exchange.value,
            reference_high=round(ref_high, 2),
            reference_low=round(ref_low, 2),
            current_price=round(current_price, 2),
            price_type=price_type,
            calculation_date=calc_date,
            percentage_change=round(percentage_change, 2),
            bucket=bucket,
            cycle_start_date=recurring_ref_date,
            cycle_end_date=cycle_end_date,
            data_source=data_source,
            last_data_refresh=utc_now(),
            is_fallback_or_stale=is_fallback_or_stale,
            cycle_status=cycle_status,
        )
