"""Rule-based alerts at /alerts."""

from __future__ import annotations

import rio

from stock_cycle_tracker.ui.guard import require_login


@rio.page(url_segment="alerts", guard=require_login)
class AlertsPage(rio.Component):
    def build(self) -> rio.Component:
        from stock_cycle_tracker.ui.app import RootComponent

        return RootComponent(initial_page="alerts")
