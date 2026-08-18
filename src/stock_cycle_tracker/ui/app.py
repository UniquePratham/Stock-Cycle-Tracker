"""Root Rio Application and navigation container with dual light/dark theme switching and mobile hamburger drawer."""

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
    create_dark_theme,
    create_light_theme,
)
from stock_cycle_tracker.ui.views.alerts_view import AlertsView
from stock_cycle_tracker.ui.views.dashboard_view import DashboardView
from stock_cycle_tracker.ui.views.excel_view import ExcelView
from stock_cycle_tracker.ui.views.manage_cycles_view import ManageCyclesView
from stock_cycle_tracker.ui.views.stock_detail_view import StockDetailView


class RootComponent(rio.Component):
    """Main application frame with responsive navigation bar, light/dark theme toggle, and mobile drawer."""

    active_page: str = "dashboard"
    selected_stock: Optional[str] = None
    is_mobile_menu_open: bool = False
    is_dark_mode: bool = True

    def navigate(self, page_name: str, stock_symbol: Optional[str] = None) -> None:
        self.active_page = page_name
        self.selected_stock = stock_symbol
        self.is_mobile_menu_open = False

    def _toggle_mobile_menu(self) -> None:
        self.is_mobile_menu_open = not self.is_mobile_menu_open

    def _toggle_theme(self) -> None:
        self.is_dark_mode = not self.is_dark_mode
        self.session.theme = "dark" if self.is_dark_mode else "light"

    def _build_nav_button(self, label: str, icon: str, page_name: str, is_mobile: bool = False) -> rio.Component:
        is_active = self.active_page == page_name
        return rio.Button(
            label,
            icon=icon,
            shape="rounded",
            style="major" if is_active else "plain-text",
            color="primary" if is_active else "neutral",
            min_height=2.4 if is_mobile else 2.2,
            grow_x=is_mobile,
            on_press=lambda: self.navigate(page_name, None),
        )

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 55.0

        # Build Navbar Header
        header_content: rio.Component
        if is_mobile:
            # Mobile Header: Logo + Title + Theme Toggle + High-Contrast Hamburger Button
            mobile_top_bar = rio.Row(
                rio.Row(
                    rio.Icon(
                        "material/candlestick-chart",
                        fill=rio.Color.from_hex("#3B82F6"),
                        min_width=1.6,
                        min_height=1.6,
                    ),
                    rio.Column(
                        rio.Text(
                            "CYCLE TRACKER",
                            font_weight="bold",
                            font_size=0.98,
                            fill=COLOR_TEXT_PRIMARY,
                        ),
                        rio.Text(
                            "Cycle Intelligence",
                            font_size=0.68,
                            fill=COLOR_TEXT_MUTED,
                        ),
                        spacing=0.02,
                    ),
                    spacing=0.35,
                    align_y=0.5,
                    align_x=0.0,
                    grow_x=False,
                ),
                rio.Spacer(),
                rio.Button(
                    "",
                    icon="material/light-mode" if self.is_dark_mode else "material/dark-mode",
                    shape="circle",
                    style="minor",
                    color="neutral",
                    min_height=2.2,
                    min_width=2.2,
                    on_press=self._toggle_theme,
                ),
                rio.Button(
                    "",
                    icon="material/close" if self.is_mobile_menu_open else "material/menu",
                    style="major",
                    color="primary",
                    shape="rounded",
                    min_height=2.2,
                    min_width=2.6,
                    on_press=self._toggle_mobile_menu,
                ),
                spacing=0.3,
                align_y=0.5,
                margin_x=0.5,
                margin_y=0.35,
                grow_x=True,
            )

            if self.is_mobile_menu_open:
                menu_drawer = rio.Column(
                    rio.Separator(),
                    self._build_nav_button("Dashboard", "material/dashboard", "dashboard", is_mobile=True),
                    self._build_nav_button("Manage Cycles", "material/calendar-month", "manage_cycles", is_mobile=True),
                    self._build_nav_button("Excel Ingestion", "material/table-view", "excel", is_mobile=True),
                    self._build_nav_button("Alerts", "material/notifications", "alerts", is_mobile=True),
                    spacing=0.3,
                    margin_x=0.5,
                    margin_bottom=0.5,
                    margin_top=0.2,
                    grow_x=True,
                )
                header_content = rio.Column(
                    mobile_top_bar,
                    menu_drawer,
                    spacing=0.2,
                    grow_x=True,
                )
            else:
                header_content = mobile_top_bar
        else:
            # Desktop Header: Logo + Title on left, Nav pills + Theme Toggle on right
            header_content = rio.Row(
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
                    align_x=0.0,
                    grow_x=False,
                ),
                rio.Spacer(),
                rio.Row(
                    self._build_nav_button("Dashboard", "material/dashboard", "dashboard"),
                    self._build_nav_button("Manage Cycles", "material/calendar-month", "manage_cycles"),
                    self._build_nav_button("Excel Ingestion", "material/table-view", "excel"),
                    self._build_nav_button("Alerts", "material/notifications", "alerts"),
                    rio.Button(
                        "",
                        icon="material/light-mode" if self.is_dark_mode else "material/dark-mode",
                        shape="circle",
                        style="minor",
                        color="neutral",
                        min_height=2.2,
                        min_width=2.2,
                        on_press=self._toggle_theme,
                    ),
                    spacing=0.4,
                    align_y=0.5,
                ),
                spacing=0.8,
                align_y=0.5,
                margin_x=0.8,
                margin_y=0.4,
                grow_x=True,
            )

        nav_header = rio.Card(
            header_content,
            corner_radius=0.5,
            color="neutral",
            margin_x=0.4 if is_mobile else 1.2,
            margin_top=0.3 if is_mobile else 0.6,
            margin_bottom=0.3 if is_mobile else 0.4,
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
    """Factory creating the configured Rio Application with custom dual light/dark theme."""
    ServiceContainer.get(db_path=db_path)

    return rio.App(
        build=RootComponent,
        name="Stock Cycle Tracker",
        theme=create_app_theme(),
    )
