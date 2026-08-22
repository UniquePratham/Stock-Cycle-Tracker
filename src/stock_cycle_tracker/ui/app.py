"""Root Rio Application and navigation container with dual light/dark theme switching and mobile hamburger drawer."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import rio

from stock_cycle_tracker.domain.user import User
from stock_cycle_tracker.ui.components.auth_modal import AuthModal
from stock_cycle_tracker.ui.state import ServiceContainer
from stock_cycle_tracker.ui.theme import (
    COLOR_BG_DARK,
    COLOR_BORDER,
    COLOR_SURFACE_CARD,
    COLOR_TEXT_DIM,
    COLOR_TEXT_MUTED,
    create_app_theme,
    create_dark_theme,
    create_light_theme,
)
from stock_cycle_tracker.ui.views.alerts_view import AlertsView
from stock_cycle_tracker.ui.views.dashboard_view import DashboardView
from stock_cycle_tracker.ui.views.excel_view import ExcelView
from stock_cycle_tracker.ui.views.home_view import HomeView
from stock_cycle_tracker.ui.views.manage_cycles_view import ManageCyclesView
from stock_cycle_tracker.ui.views.stock_detail_view import StockDetailView

ASSETS_DIR = Path(__file__).parent / "assets"
FAVICON_PATH = ASSETS_DIR / "favicon.png"


class RootComponent(rio.Component):
    """Main application frame with responsive navigation bar, user authentication, avatar profiles, and local storage disclaimers."""

    active_page: str = "home"
    selected_stock: Optional[str] = None
    is_mobile_menu_open: bool = False
    is_dark_mode: bool = True
    current_user: Optional[User] = None
    is_auth_modal_open: bool = False
    auth_modal_initial_tab: str = "signin"

    def navigate(self, page_name: str, stock_symbol: Optional[str] = None) -> None:
        if self.current_user is None and page_name not in ("home",):
            self._open_signin()
            return
        self.active_page = page_name
        self.selected_stock = stock_symbol
        self.is_mobile_menu_open = False

    def _toggle_mobile_menu(self) -> None:
        self.is_mobile_menu_open = not self.is_mobile_menu_open

    def _toggle_theme(self) -> None:
        self.is_dark_mode = not self.is_dark_mode
        self.session.theme = create_dark_theme() if self.is_dark_mode else create_light_theme()

    def _open_auth_modal(self, initial_tab: str = "signin") -> None:
        self.auth_modal_initial_tab = initial_tab
        self.is_auth_modal_open = True
        self.is_mobile_menu_open = False

    def _open_signin(self) -> None:
        self._open_auth_modal("signin")

    def _open_signup(self) -> None:
        self._open_auth_modal("signup")

    def _close_auth_modal(self) -> None:
        self.is_auth_modal_open = False

    def _on_auth_success(self, user: User) -> None:
        self.current_user = user
        self.is_auth_modal_open = False
        self.active_page = "dashboard"

    def _handle_quick_demo(self) -> None:
        container = ServiceContainer.get()
        user, _ = container.auth_service.signin("investor", "investor123")
        if not user:
            user, _ = container.auth_service.signup(
                username="investor",
                email="investor@local.dev",
                password="investor123",
                full_name="Chief Market Analyst",
                avatar_id="cycle_master",
            )
        if user:
            self._on_auth_success(user)

    def _sign_out(self) -> None:
        self.current_user = None
        self.active_page = "home"
        self.selected_stock = None

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

        # Brand Icon component
        brand_icon_component: rio.Component
        if FAVICON_PATH.exists():
            brand_icon_component = rio.Image(
                FAVICON_PATH,
                min_width=1.6 if is_mobile else 2.0,
                min_height=1.6 if is_mobile else 2.0,
                corner_radius=0.35,
            )
        else:
            brand_icon_component = rio.Icon(
                "material/candlestick-chart",
                fill=rio.Color.from_hex("#3B82F6"),
                min_width=1.6 if is_mobile else 2.0,
                min_height=1.6 if is_mobile else 2.0,
            )

        # User Profile / Auth Widget in Navbar
        user_widget: rio.Component
        if self.current_user:
            av = self.current_user.avatar
            user_widget = rio.Card(
                rio.Row(
                    rio.Icon(av.icon, fill=rio.Color.from_hex(av.color_hex), min_width=1.3, min_height=1.3),
                    rio.Column(
                        rio.Text(self.current_user.display_name, font_weight="bold", font_size=0.82),
                        rio.Text(f"{av.name} • Local DB", font_size=0.65, fill=rio.Color.from_hex("#10B981")),
                        spacing=0.01,
                    ),
                    rio.Button(
                        "",
                        icon="material/logout",
                        shape="rounded",
                        style="plain-text",
                        color="danger",
                        min_height=1.6,
                        min_width=1.6,
                        on_press=self._sign_out,
                    ),
                    spacing=0.3,
                    align_y=0.5,
                    margin_x=0.4,
                    margin_y=0.15,
                ),
                corner_radius=0.3,
                color="hud",
                grow_x=False,
            )
        else:
            user_widget = rio.Row(
                rio.Button(
                    "Sign In",
                    icon="material/login",
                    shape="rounded",
                    style="minor",
                    color="neutral",
                    min_height=2.0,
                    on_press=self._open_signin,
                ),
                rio.Button(
                    "Create Account",
                    icon="material/person-add",
                    shape="rounded",
                    style="major",
                    color="primary",
                    min_height=2.0,
                    on_press=self._open_signup,
                ),
                spacing=0.2,
                align_y=0.5,
            )

        # Responsive Navbar Header
        header_content: rio.Component
        if is_mobile:
            mobile_top_bar = rio.Row(
                rio.Row(
                    brand_icon_component,
                    rio.Column(
                        rio.Text(
                            "CYCLE TRACKER",
                            font_weight="bold",
                            font_size=0.98,
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
                    "Dark" if self.is_dark_mode else "Light",
                    icon="material/dark-mode" if self.is_dark_mode else "material/light-mode",
                    shape="rounded",
                    style="minor",
                    color="neutral",
                    min_height=2.0,
                    on_press=self._toggle_theme,
                ),
                rio.Button(
                    "",
                    icon="material/menu" if not self.is_mobile_menu_open else "material/close",
                    shape="rounded",
                    style="minor",
                    color="neutral",
                    min_height=2.0,
                    min_width=2.4,
                    on_press=self._toggle_mobile_menu,
                ) if self.current_user else rio.Spacer(),
                spacing=0.25,
                align_y=0.5,
                margin_x=0.4,
                margin_y=0.3,
                grow_x=True,
            )

            if self.is_mobile_menu_open and self.current_user:
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
            # Desktop Header
            nav_links = (
                rio.Row(
                    self._build_nav_button("Dashboard", "material/dashboard", "dashboard"),
                    self._build_nav_button("Manage Cycles", "material/calendar-month", "manage_cycles"),
                    self._build_nav_button("Excel Ingestion", "material/table-view", "excel"),
                    self._build_nav_button("Alerts", "material/notifications", "alerts"),
                    spacing=0.3,
                    align_y=0.5,
                )
                if self.current_user
                else rio.Spacer()
            )

            header_content = rio.Row(
                rio.Row(
                    brand_icon_component,
                    rio.Column(
                        rio.Text(
                            "STOCK CYCLE TRACKER",
                            font_weight="bold",
                            font_size=1.15,
                        ),
                        rio.Text(
                            "Institutional Cycle Intelligence",
                            font_size=0.75,
                            fill=COLOR_TEXT_MUTED,
                        ),
                        spacing=0.03,
                    ),
                    spacing=0.5,
                    align_y=0.5,
                    align_x=0.0,
                    grow_x=False,
                ),
                rio.Spacer(),
                nav_links,
                rio.Spacer(),
                user_widget,
                rio.Button(
                    "Dark Mode" if self.is_dark_mode else "Light Mode",
                    icon="material/dark-mode" if self.is_dark_mode else "material/light-mode",
                    shape="rounded",
                    style="minor",
                    color="neutral",
                    min_height=2.0,
                    on_press=self._toggle_theme,
                ),
                spacing=0.5,
                align_y=0.5,
                margin_x=0.8,
                margin_y=0.35,
                grow_x=True,
            )

        nav_header = rio.Card(
            header_content,
            corner_radius=0.5,
            color="neutral",
            margin_x=0.4 if is_mobile else 0.8,
            margin_top=0.3 if is_mobile else 0.4,
            margin_bottom=0.2 if is_mobile else 0.3,
            grow_x=True,
            grow_y=False,
            align_y=0.0,
        )

        # Legal & Local Computer Storage Global Disclaimer
        disclaimer_banner = rio.Card(
            rio.Row(
                rio.Icon("material/security", fill=rio.Color.from_hex("#10B981"), min_width=1.0, min_height=1.0),
                rio.Text(
                    "Data Privacy Notice: All account details, stocks, and research cycles are stored on your local computer database (SQLite). Calculations are for research & cycle tracking purposes.",
                    font_size=0.68,
                    fill=COLOR_TEXT_MUTED,
                    grow_x=True,
                ),
                spacing=0.3,
                margin_x=0.6,
                margin_y=0.15,
                align_y=0.5,
                grow_x=True,
            ),
            corner_radius=0.25,
            color="hud",
            margin_x=0.4 if is_mobile else 0.8,
            margin_bottom=0.2,
            grow_x=True,
        )

        # Dynamic View Selection with Auth Gate
        view_content: rio.Component
        if self.is_auth_modal_open:
            view_content = rio.Column(
                AuthModal(
                    active_tab=self.auth_modal_initial_tab,
                    on_auth_success=self._on_auth_success,
                    on_close=self._close_auth_modal,
                ),
                align_x=0.5,
                align_y=0.5,
                margin_y=0.8,
                grow_x=True,
            )
        elif self.current_user is None or self.active_page == "home":
            view_content = HomeView(
                on_open_signin=self._open_signin,
                on_open_signup=self._open_signup,
                on_quick_demo=self._handle_quick_demo,
            )
        elif self.active_page == "stock_detail" and self.selected_stock:
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
            disclaimer_banner,
            view_content,
            spacing=0.15,
            grow_x=True,
            align_y=0.0,
        )


def build_app(db_path: Optional[str] = None) -> rio.App:
    """Factory creating the configured Rio Application with custom dark theme and stock logo favicon."""
    ServiceContainer.get(db_path=db_path)

    return rio.App(
        build=RootComponent,
        name="Stock Cycle Tracker",
        theme=create_dark_theme(),
        assets_dir=ASSETS_DIR,
        icon=FAVICON_PATH if FAVICON_PATH.exists() else None,
    )
