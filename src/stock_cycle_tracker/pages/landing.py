"""Landing page — the only public URL."""

from __future__ import annotations

import rio


@rio.page(url_segment="")
class LandingPage(rio.Component):
    def build(self) -> rio.Component:
        from stock_cycle_tracker.ui.app import RootComponent

        return RootComponent(initial_page="home")
