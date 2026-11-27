"""Manage tracked stocks and cycles at /cycles."""

from __future__ import annotations

import rio

from stock_cycle_tracker.ui.guard import require_login


@rio.page(url_segment="cycles", guard=require_login)
class CyclesPage(rio.Component):
    def build(self) -> rio.Component:
        from stock_cycle_tracker.ui.app import RootComponent

        return RootComponent(initial_page="manage_cycles")
