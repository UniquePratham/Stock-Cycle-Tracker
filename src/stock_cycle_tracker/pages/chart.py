"""A single stock's chart at /chart/{symbol}.

This is the URL "Open in new tab" points at, so the chart can live in its own
browser tab.
"""

from __future__ import annotations

import rio

from stock_cycle_tracker.ui.guard import require_login


@rio.page(url_segment="chart/{symbol}", guard=require_login)
class ChartPage(rio.Component):
    symbol: str = ""

    def build(self) -> rio.Component:
        from stock_cycle_tracker.ui.app import RootComponent

        return RootComponent(
            initial_page="stock_detail",
            initial_stock=self.symbol.upper() if self.symbol else None,
        )
