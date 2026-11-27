"""Cycle analysis dashboard at /dashboard."""

from __future__ import annotations

import rio

from stock_cycle_tracker.ui.guard import require_login


@rio.page(url_segment="dashboard", guard=require_login)
class DashboardPage(rio.Component):
    def build(self) -> rio.Component:
        from stock_cycle_tracker.ui.app import RootComponent

        return RootComponent(initial_page="dashboard")
