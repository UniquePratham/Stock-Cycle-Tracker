"""Root Rio Application and navigation container with dual light/dark theme switching and mobile hamburger drawer."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import rio

from stock_cycle_tracker.domain.user import User
from stock_cycle_tracker.ui.components.auth_modal import AuthModal
from stock_cycle_tracker.ui.session_auth import (
    cookie_url_for,
    create_session,
    current_user,
    destroy_session,
    session_token,
)
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


def demo_login_enabled() -> bool:
    """True only when ENABLE_DEMO_LOGIN=1 is set.

    Demo login is off by default so a production deployment never ships a
    working back door.
    """
    return os.environ.get("ENABLE_DEMO_LOGIN", "").strip() == "1"


class RootComponent(rio.Component):
    """Main application frame with responsive navigation bar, user authentication, avatar profiles, and local storage disclaimers."""

    active_page: str = "home"
    selected_stock: Optional[str] = None
    is_mobile_menu_open: bool = False
    is_dark_mode: bool = True
    current_user: Optional[User] = None
    is_auth_modal_open: bool = False
    auth_modal_initial_tab: str = "signin"

    # Set by the URL page wrappers so a direct visit to /dashboard or
    # /chart/RELIANCE lands on the right view.
    initial_page: str = "home"
    initial_stock: Optional[str] = None

    # One-shot URL that sets the httponly session cookie. Rendered as a hidden
    # image so the browser fetches it (applying Set-Cookie) without navigating.
    _pending_cookie_url: str = ""

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
        # Persist the login in an httponly cookie so it survives a reload and a
        # new tab. The cookie holds an opaque token; the server keeps only its
        # hash.
        #
        # The cookie is set by loading a one-shot URL. It must not be navigated
        # to from inside build(), or the page reloads in a loop — so it is
        # opened in a hidden way: the URL is fetched by the browser as a
        # subresource, which still applies the Set-Cookie header.
        token = create_session(user)
        url = cookie_url_for(self.session, token)
        if url:
            self._pending_cookie_url = url

    def _handle_quick_demo(self) -> None:
        """Signs in the shared demo account, only when demo mode is enabled.

        Demo login is off unless ENABLE_DEMO_LOGIN=1 is set, so a production
        deployment does not ship a working back door. There is no hardcoded
        password: the demo account is created with a random one and signed in
        directly, so nobody can log into it from the sign-in form.
        """
        if not demo_login_enabled():
            return

        container = ServiceContainer.get()
        user = container.auth_service.get_or_create_demo_user()
        if user:
            self._on_auth_success(user)

    def _sign_out(self) -> None:
        # Delete the server-side session so the cookie stops working, then clear
        # the in-memory user.
        destroy_session(session_token(self.session))
        self.current_user = None
        self.active_page = "home"
        self.selected_stock = None

    def __init__(self, **kwargs) -> None:
        """Resolves the session and the URL's requested page, once.

        This runs before the first build, so the state it sets is stable by the
        time `build()` reads it. Doing this work inside `build()` would mutate
        state during a build, which marks the component dirty and schedules
        another build — an infinite reload loop.
        """
        super().__init__(**kwargs)

        # Rio's observable properties raise AttributeError until they have been
        # assigned, so every read here goes through a safe getter.
        def current(field: str, default=None):
            try:
                return getattr(self, field)
            except AttributeError:
                return default

        # Restore the login from the httponly session cookie, so a reload or a
        # new tab lands the user back where they were.
        restored = current("current_user")
        if restored is None:
            restored = current_user(self.session)

        # Assign every field explicitly. A property that is never assigned keeps
        # raising AttributeError, which would crash the first build.
        self.current_user = restored
        self.active_page = current("active_page", "home") or "home"
        self.selected_stock = current("selected_stock")
        self.is_mobile_menu_open = bool(current("is_mobile_menu_open", False))
        self.is_dark_mode = bool(current("is_dark_mode", True))
        self.is_auth_modal_open = bool(current("is_auth_modal_open", False))
        self.auth_modal_initial_tab = current("auth_modal_initial_tab", "signin") or "signin"
        self.initial_page = current("initial_page", "home") or "home"
        self.initial_stock = current("initial_stock")
        self._pending_cookie_url = current("_pending_cookie_url", "") or ""

        # A signed-in visitor landing on "/" goes straight to the dashboard.
        if restored is not None and self.active_page == "home":
            self.active_page = "dashboard"

        # Honour the page the URL asked for (set by the page wrappers).
        if self.initial_page != "home" and restored is not None:
            self.active_page = self.initial_page
            if self.initial_stock:
                self.selected_stock = self.initial_stock

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
        is_mobile = self.session.window_width < 60.0

        # NOTE: build() must not mutate component state. Assigning to
        # `self.active_page` here marks the component dirty, which schedules
        # another build, which assigns again — an infinite reload loop. The
        # session restore and the URL's requested page are therefore resolved
        # once, in `on_session_start`, and only read here.
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
                        rio.Text(f"{av.name}", font_size=0.65, fill=rio.Color.from_hex("#10B981")),
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
            if self.current_user:
                av = self.current_user.avatar
                mobile_top_bar = rio.Row(
                    rio.Row(
                        brand_icon_component,
                        rio.Column(
                            rio.Text(
                                "CYCLE TRACKER",
                                font_weight="bold",
                                font_size=0.92,
                            ),
                            rio.Text(
                                "Stock Cycle Tracker",
                                font_size=0.64,
                                fill=COLOR_TEXT_MUTED,
                            ),
                            spacing=0.01,
                        ),
                        spacing=0.25,
                        align_y=0.5,
                        align_x=0.0,
                        grow_x=False,
                    ),
                    rio.Spacer(),
                    rio.IconButton(
                        icon="material/dark-mode" if self.is_dark_mode else "material/light-mode",
                        style="minor",
                        color="neutral",
                        min_size=2.0,
                        on_press=self._toggle_theme,
                    ),
                    rio.IconButton(
                        icon="material/menu" if not self.is_mobile_menu_open else "material/close",
                        style="major" if self.is_mobile_menu_open else "minor",
                        color="primary" if self.is_mobile_menu_open else "neutral",
                        min_size=2.0,
                        on_press=self._toggle_mobile_menu,
                    ),
                    spacing=0.2,
                    align_y=0.5,
                    margin_x=0.4,
                    margin_y=0.25,
                    grow_x=True,
                )

                if self.is_mobile_menu_open:
                    user_drawer_card = rio.Card(
                        rio.Row(
                            rio.Icon(av.icon, fill=rio.Color.from_hex(av.color_hex), min_width=1.3, min_height=1.3),
                            rio.Column(
                                rio.Text(self.current_user.display_name, font_weight="bold", font_size=0.82),
                                rio.Text(f"{av.name}", font_size=0.65, fill=rio.Color.from_hex("#10B981")),
                                spacing=0.01,
                            ),
                            rio.Spacer(),
                            rio.Button(
                                "Logout",
                                icon="material/logout",
                                shape="rounded",
                                style="plain-text",
                                color="danger",
                                min_height=1.6,
                                on_press=self._sign_out,
                            ),
                            spacing=0.25,
                            align_y=0.5,
                            margin=0.3,
                            grow_x=True,
                        ),
                        corner_radius=0.4,
                        color="hud",
                        grow_x=True,
                    )

                    menu_drawer = rio.Column(
                        rio.Separator(),
                        user_drawer_card,
                        self._build_nav_button("Dashboard", "material/dashboard", "dashboard", is_mobile=True),
                        self._build_nav_button("Manage Cycles", "material/calendar-month", "manage_cycles", is_mobile=True),
                        self._build_nav_button("Excel Ingestion", "material/table-view", "excel", is_mobile=True),
                        self._build_nav_button("Alerts", "material/notifications", "alerts", is_mobile=True),
                        spacing=0.25,
                        margin_x=0.4,
                        margin_bottom=0.4,
                        margin_top=0.15,
                        grow_x=True,
                    )
                    header_content = rio.Column(
                        mobile_top_bar,
                        menu_drawer,
                        spacing=0.15,
                        grow_x=True,
                    )
                else:
                    header_content = mobile_top_bar
            else:
                # Guest Mobile Header
                mobile_top_bar = rio.Row(
                    rio.Row(
                        brand_icon_component,
                        rio.Text(
                            "CYCLE TRACKER",
                            font_weight="bold",
                            font_size=0.88,
                        ),
                        spacing=0.2,
                        align_y=0.5,
                        grow_x=False,
                    ),
                    rio.Spacer(),
                    rio.Button(
                        "Sign In",
                        shape="rounded",
                        style="plain-text",
                        color="neutral",
                        min_height=1.8,
                        on_press=self._open_signin,
                    ),
                    rio.Button(
                        "Join",
                        icon="material/person-add",
                        shape="rounded",
                        style="major",
                        color="primary",
                        min_height=1.8,
                        on_press=self._open_signup,
                    ),
                    rio.IconButton(
                        icon="material/dark-mode" if self.is_dark_mode else "material/light-mode",
                        style="minor",
                        color="neutral",
                        min_size=2.0,
                        on_press=self._toggle_theme,
                    ),
                    spacing=0.15,
                    align_y=0.5,
                    margin_x=0.35,
                    margin_y=0.2,
                    grow_x=True,
                )
                header_content = mobile_top_bar
        else:
            # Desktop Header
            if self.current_user:
                header_content = rio.Row(
                    rio.Row(
                        brand_icon_component,
                        rio.Column(
                            rio.Text(
                                "STOCK CYCLE TRACKER",
                                font_weight="bold",
                                font_size=1.1,
                            ),
                            rio.Text(
                                "Stock Cycle Tracker",
                                font_size=0.72,
                                fill=COLOR_TEXT_MUTED,
                            ),
                            spacing=0.02,
                        ),
                        spacing=0.4,
                        align_y=0.5,
                        grow_x=False,
                    ),
                    rio.Spacer(),
                    rio.Row(
                        self._build_nav_button("Dashboard", "material/dashboard", "dashboard"),
                        self._build_nav_button("Manage Cycles", "material/calendar-month", "manage_cycles"),
                        self._build_nav_button("Excel Ingestion", "material/table-view", "excel"),
                        self._build_nav_button("Alerts", "material/notifications", "alerts"),
                        spacing=0.25,
                        align_y=0.5,
                    ),
                    rio.Spacer(),
                    user_widget,
                    rio.IconButton(
                        icon="material/dark-mode" if self.is_dark_mode else "material/light-mode",
                        style="minor",
                        color="neutral",
                        min_size=2.2,
                        on_press=self._toggle_theme,
                    ),
                    spacing=0.35,
                    align_y=0.5,
                    margin_x=0.6,
                    margin_y=0.3,
                    grow_x=True,
                )
            else:
                header_content = rio.Row(
                    rio.Row(
                        brand_icon_component,
                        rio.Column(
                            rio.Text(
                                "STOCK CYCLE TRACKER",
                                font_weight="bold",
                                font_size=1.1,
                            ),
                            rio.Text(
                                "Stock Cycle Tracker",
                                font_size=0.72,
                                fill=COLOR_TEXT_MUTED,
                            ),
                            spacing=0.02,
                        ),
                        spacing=0.4,
                        align_y=0.5,
                        grow_x=False,
                    ),
                    rio.Spacer(),
                    rio.Button(
                        "Sign In",
                        icon="material/login",
                        shape="rounded",
                        style="plain-text",
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
                    rio.IconButton(
                        icon="material/dark-mode" if self.is_dark_mode else "material/light-mode",
                        style="minor",
                        color="neutral",
                        min_size=2.2,
                        on_press=self._toggle_theme,
                    ),
                    spacing=0.25,
                    align_y=0.5,
                    margin_x=0.6,
                    margin_y=0.3,
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

        if self.is_auth_modal_open:
            return rio.Stack(
                HomeView(
                    on_open_signin=self._open_signin,
                    on_open_signup=self._open_signup,
                    on_quick_demo=self._handle_quick_demo,
                ),
                rio.Rectangle(
                    fill=rio.Color.from_hex("#000000B3"),
                    grow_x=True,
                    grow_y=True,
                ),
                rio.Column(
                    AuthModal(
                        active_tab=self.auth_modal_initial_tab,
                        on_auth_success=self._on_auth_success,
                        on_close=self._close_auth_modal,
                    ),
                    align_x=0.5,
                    align_y=0.5,
                    margin_x=0.5 if is_mobile else 2.0,
                    margin_y=0.5,
                    grow_x=True,
                    grow_y=True,
                ),
                grow_x=True,
                grow_y=True,
            )

        # Dynamic View Selection with Auth Gate
        view_content: rio.Component
        if self.current_user is None or self.active_page == "home":
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

        # For the homepage, overlay navbar on top of the full-bleed background
        is_homepage = self.current_user is None or self.active_page == "home"

        # A hidden 1px image whose src is the one-shot cookie URL. The browser
        # fetches it as a subresource, which applies the Set-Cookie header
        # without navigating away from the page.
        #
        # `rio.Image` treats its argument as an asset path and rejects a
        # `/rio/cookies/...` URL, so the cookie is set with a plain HTML image
        # via `rio.Html`.
        cookie_setter: rio.Component = rio.Spacer()
        if self._pending_cookie_url:
            cookie_setter = rio.Html(
                f'<img src="{self._pending_cookie_url}" alt="" '
                'width="1" height="1" style="position:absolute;opacity:0;pointer-events:none" />'
            )

        if is_homepage:
            return rio.Stack(
                view_content,
                rio.Column(
                    nav_header,
                    rio.Spacer(),
                    grow_x=True,
                    grow_y=True,
                ),
                cookie_setter,
                grow_x=True,
                grow_y=True,
            )

        return rio.Column(
            nav_header,
            view_content,
            cookie_setter,
            spacing=0.15,
            grow_x=True,
            grow_y=True,
        )

def build_app(db_path: Optional[str] = None) -> rio.App:
    """Factory creating the configured Rio Application with custom dark theme and stock logo favicon."""
    ServiceContainer.get(db_path=db_path)

    # The `pages` package holds one module per URL. Passing the folder
    # explicitly means the routes are found regardless of which module
    # constructs the app.
    pages_dir = Path(__file__).parent.parent / "pages"

    return rio.App(
        build=RootComponent,
        name="Stock Cycle Tracker",
        theme=create_dark_theme(),
        assets_dir=ASSETS_DIR,
        icon=FAVICON_PATH if FAVICON_PATH.exists() else None,
        pages=pages_dir,
    )
