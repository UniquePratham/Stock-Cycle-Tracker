"""Root Rio Application and navigation container with responsive dark navigation bar."""

from __future__ import annotations

from typing import Optional

import rio

from stock_cycle_tracker.ui.state import ServiceContainer
from stock_cycle_tracker.ui.theme import (
    COLOR_BG_DARK,
    COLOR_BORDER,
    COLOR_SURFACE_CARD,
    COLOR_TEXT_DIM,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    create_app_theme,
)
from stock_cycle_tracker.ui.views.alerts_view import AlertsView
from stock_cycle_tracker.ui.views.dashboard_view import DashboardView
from stock_cycle_tracker.ui.views.excel_view import ExcelView
from stock_cycle_tracker.ui.views.manage_cycles_view import ManageCyclesView
from stock_cycle_tracker.ui.views.stock_detail_view import StockDetailView


class RootComponent(rio.Component):
    """Main application frame with responsive dark navigation bar."""

    active_page: str = "dashboard"
    selected_stock: Optional[str] = None

    def navigate(self, page_name: str, stock_symbol: Optional[str] = None) -> None:
        self.active_page = page_name
        self.selected_stock = stock_symbol

    def _build_nav_button(self, label: str, icon: str, page_name: str) -> rio.Component:
        is_active = self.active_page == page_name
        return rio.Button(
            label,
            icon=icon,
            shape="rounded",
            style="major" if is_active else "plain-text",
            color="primary" if is_active else "neutral",
            min_height=2.2,
            on_press=lambda: self.navigate(page_name, None),
        )

    def build(self) -> rio.Component:
        # Fully responsive Navigation Header
        nav_header = rio.Card(
            rio.FlowContainer(
                # Brand Logo & Title
                rio.Row(
                    rio.Icon(
                        "material/candlestick-chart",
                        fill=rio.Color.from_hex("#3B82F6"),
                        min_width=2.0,
                        min_height=2.0,
                    ),
                    rio.Column(
                        rio.Text(
                            "STOCK CYCLE TRACKER",
                            font_weight="bold",
                            font_size=1.15,
                            fill=COLOR_TEXT_PRIMARY,
                        ),
                        rio.Text(
                            "Institutional Cycle Intelligence",
                            font_size=0.75,
                            fill=COLOR_TEXT_MUTED,
                        ),
                        spacing=0.05,
                    ),
                    spacing=0.5,
                    align_y=0.5,
                ),
                # Flat navigation buttons for seamless mobile wrap
                self._build_nav_button("Dashboard", "material/dashboard", "dashboard"),
                self._build_nav_button("Manage Cycles", "material/calendar-month", "manage_cycles"),
                self._build_nav_button("Excel Ingestion", "material/table-view", "excel"),
                self._build_nav_button("Alerts", "material/notifications", "alerts"),
                spacing=0.4,
                row_spacing=0.4,
                column_spacing=0.4,
                justify="justify",
                align_y=0.5,
                margin_x=0.8,
                margin_y=0.4,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            margin_x=1.2,
            margin_top=0.6,
            margin_bottom=0.4,
            grow_x=True,
            grow_y=False,
            align_y=0.0,
        )

        # Dynamic View Selection
        view_content: rio.Component
        if self.active_page == "stock_detail" and self.selected_stock:
            view_content = StockDetailView(
                stock_symbol=self.selected_stock,
                on_navigate=self.navigate,
            )
        elif self.active_page == "manage_cycles":
            view_content = ManageCyclesView(on_navigate=self.navigate)
        elif self.active_page == "excel":
            view_content = ExcelView(on_navigate=self.navigate)
        elif self.active_page == "alerts":
            view_content = AlertsView(on_navigate=self.navigate)
        else:
            view_content = DashboardView(on_navigate=self.navigate)

        return rio.Column(
            nav_header,
            view_content,
            spacing=0.2,
            grow_x=True,
            align_y=0.0,
        )


def build_app(db_path: Optional[str] = None) -> rio.App:
    """Factory creating the configured Rio Application with custom dark theme."""
    ServiceContainer.get(db_path=db_path)

    return rio.App(
        build=RootComponent,
        name="Stock Cycle Tracker",
        theme=create_app_theme(),
    )
