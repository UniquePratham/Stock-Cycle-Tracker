"""Alert evaluation and notification service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from stock_cycle_tracker.domain.models import CycleAnalysis, utc_now
from stock_cycle_tracker.storage.db import DatabaseManager


class AlertConditionType(str, Enum):
    PERCENTAGE_BELOW = "PERCENTAGE_BELOW"
    PERCENTAGE_ABOVE = "PERCENTAGE_ABOVE"
    BUCKET_MATCH = "BUCKET_MATCH"
    REF_HIGH_CROSSED = "REF_HIGH_CROSSED"


@dataclass
class AlertRule:
    id: Optional[int]
    stock_symbol: str
    cycle_number: int
    condition_type: AlertConditionType
    threshold_value: float = 0.0
    target_bucket: Optional[str] = None
    is_enabled: bool = True
    created_at: datetime = field(default_factory=utc_now)
    last_triggered_at: Optional[datetime] = None


@dataclass
class AlertTriggerEvent:
    alert_id: int
    stock_symbol: str
    cycle_number: int
    condition_summary: str
    current_value: str
    triggered_at: datetime = field(default_factory=utc_now)


class AlertService:
    """Evaluates configured alert rules against cycle calculation analyses."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def add_alert(
        self,
        stock_symbol: str,
        cycle_number: int,
        condition_type: AlertConditionType,
        threshold_value: float = 0.0,
        target_bucket: Optional[str] = None,
    ) -> AlertRule:
        sym = stock_symbol.strip().upper()
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO alerts (stock_symbol, cycle_number, condition_type, threshold_value, target_bucket, is_enabled)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (sym, cycle_number, condition_type.value, threshold_value, target_bucket),
            )
            conn.commit()
            new_id = cur.lastrowid
            return AlertRule(
                id=new_id,
                stock_symbol=sym,
                cycle_number=cycle_number,
                condition_type=condition_type,
                threshold_value=threshold_value,
                target_bucket=target_bucket,
                is_enabled=True,
            )

    def list_alerts(self) -> List[AlertRule]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM alerts ORDER BY id DESC")
            return [
                AlertRule(
                    id=row["id"],
                    stock_symbol=row["stock_symbol"],
                    cycle_number=row["cycle_number"],
                    condition_type=AlertConditionType(row["condition_type"]),
                    threshold_value=row["threshold_value"],
                    target_bucket=row["target_bucket"],
                    is_enabled=bool(row["is_enabled"]),
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else utc_now(),
                    last_triggered_at=datetime.fromisoformat(row["last_triggered_at"]) if row["last_triggered_at"] else None,
                )
                for row in cur.fetchall()
            ]

    def toggle_alert(self, alert_id: int, is_enabled: bool) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE alerts SET is_enabled = ? WHERE id = ?", (int(is_enabled), alert_id))
            conn.commit()
            return cur.rowcount > 0

    def delete_alert(self, alert_id: int) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
            conn.commit()
            return cur.rowcount > 0

    def evaluate_analyses(self, analyses: List[CycleAnalysis]) -> List[AlertTriggerEvent]:
        alerts = self.list_alerts()
        enabled_alerts = [a for a in alerts if a.is_enabled]
        if not enabled_alerts or not analyses:
            return []

        analysis_map = {(a.stock_symbol.upper(), a.cycle_number): a for a in analyses}
        triggered_events: List[AlertTriggerEvent] = []

        now = utc_now()
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            for alert in enabled_alerts:
                key = (alert.stock_symbol.upper(), alert.cycle_number)
                analysis = analysis_map.get(key)
                if not analysis:
                    continue

                triggered = False
                summary = ""
                curr_val = ""

                if alert.condition_type == AlertConditionType.PERCENTAGE_BELOW:
                    if analysis.percentage_change <= alert.threshold_value:
                        triggered = True
                        summary = f"% Change <= {alert.threshold_value:.1f}%"
                        curr_val = f"{analysis.percentage_change:+.2f}%"
                elif alert.condition_type == AlertConditionType.PERCENTAGE_ABOVE:
                    if analysis.percentage_change >= alert.threshold_value:
                        triggered = True
                        summary = f"% Change >= {alert.threshold_value:.1f}%"
                        curr_val = f"{analysis.percentage_change:+.2f}%"
                elif alert.condition_type == AlertConditionType.BUCKET_MATCH:
                    if alert.target_bucket and alert.target_bucket.lower() in analysis.bucket.lower():
                        triggered = True
                        summary = f"Bucket matches '{alert.target_bucket}'"
                        curr_val = analysis.bucket
                elif alert.condition_type == AlertConditionType.REF_HIGH_CROSSED:
                    if analysis.current_price >= analysis.reference_high:
                        triggered = True
                        summary = f"Price crossed Ref High (₹{analysis.reference_high:.2f})"
                        curr_val = f"₹{analysis.current_price:.2f}"

                if triggered and alert.id is not None:
                    event = AlertTriggerEvent(
                        alert_id=alert.id,
                        stock_symbol=alert.stock_symbol,
                        cycle_number=alert.cycle_number,
                        condition_summary=summary,
                        current_value=curr_val,
                        triggered_at=now,
                    )
                    triggered_events.append(event)
                    cur.execute(
                        "UPDATE alerts SET last_triggered_at = ? WHERE id = ?",
                        (now.isoformat(), alert.id),
                    )

            conn.commit()

        return triggered_events
