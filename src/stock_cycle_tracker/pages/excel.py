"""Bulk import and export at /excel."""

from __future__ import annotations

import rio

from stock_cycle_tracker.ui.guard import require_login


@rio.page(url_segment="excel", guard=require_login)
class ExcelPage(rio.Component):
    def build(self) -> rio.Component:
        from stock_cycle_tracker.ui.app import RootComponent

        return RootComponent(initial_page="excel")
