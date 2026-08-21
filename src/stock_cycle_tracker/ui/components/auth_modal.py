"""Authentication Modal with Sign In, Sign Up, Avatar Selection, and Local Storage Disclaimer."""

from __future__ import annotations

from typing import Callable, Optional

import rio

from stock_cycle_tracker.domain.user import AVAILABLE_AVATARS, AvatarInfo, User
from stock_cycle_tracker.ui.state import ServiceContainer
from stock_cycle_tracker.ui.theme import (
    COLOR_BORDER,
    COLOR_DOWN_STRONG,
    COLOR_SURFACE_CARD,
    COLOR_TEXT_DIM,
    COLOR_TEXT_MUTED,
    COLOR_UP_STRONG,
)


class AuthModal(rio.Component):
    """Interactive glassmorphic dialog for user registration, authentication, and avatar configuration."""

    on_auth_success: Callable[[User], None]
    on_close: Callable[[], None]

    # Form State
    active_tab: str = "signin"  # 'signin' or 'signup'
    signin_identifier: str = ""
    signin_password: str = ""

    signup_full_name: str = ""
    signup_username: str = ""
    signup_email: str = ""
    signup_password: str = ""
    signup_avatar_id: str = "bull_trader"

    error_message: Optional[str] = None
    success_message: Optional[str] = None
    is_loading: bool = False

    def _set_tab(self, tab: str) -> None:
        self.active_tab = tab
        self.error_message = None
        self.success_message = None

    def _select_avatar(self, avatar_id: str) -> None:
        self.signup_avatar_id = avatar_id

    def _handle_signin(self) -> None:
        self.error_message = None
        self.success_message = None
        self.is_loading = True

        container = ServiceContainer.get()
        user, error = container.auth_service.signin(
            identifier=self.signin_identifier,
            password=self.signin_password,
        )
        self.is_loading = False

        if error:
            self.error_message = error
            return

        if user:
            self.success_message = f"Welcome back, {user.display_name}!"
            self.on_auth_success(user)

    def _handle_signup(self) -> None:
        self.error_message = None
        self.success_message = None
        self.is_loading = True

        container = ServiceContainer.get()
        user, error = container.auth_service.signup(
            username=self.signup_username,
            email=self.signup_email,
            password=self.signup_password,
            full_name=self.signup_full_name,
            avatar_id=self.signup_avatar_id,
        )
        self.is_loading = False

        if error:
            self.error_message = error
            return

        if user:
            self.success_message = f"Account created successfully! Welcome, {user.display_name}."
            self.on_auth_success(user)

    def _handle_demo_login(self) -> None:
        """Instant demo login creating or signing into local analyst account."""
        self.error_message = None
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
            self.on_auth_success(user)

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 55.0

        # Modal Header
        header = rio.Row(
            rio.Row(
                rio.Icon("material/lock", fill=rio.Color.from_hex("#3B82F6"), min_width=1.3, min_height=1.3),
                rio.Column(
                    rio.Text("Investor Account & Access", font_weight="bold", font_size=1.05),
                    rio.Text("Manage your tracked portfolios with institutional privacy", font_size=0.72, fill=COLOR_TEXT_MUTED),
                    spacing=0.02,
                ),
                spacing=0.35,
                align_y=0.5,
            ),
            rio.Spacer(),
            rio.Button(
                "",
                icon="material/close",
                shape="rounded",
                style="plain-text",
                color="neutral",
                min_height=1.8,
                on_press=self.on_close,
            ),
            align_y=0.5,
            grow_x=True,
        )

        # Tab Switcher
        tab_switcher = rio.Card(
            rio.Row(
                rio.Button(
                    "Sign In",
                    icon="material/login",
                    shape="rounded",
                    style="major" if self.active_tab == "signin" else "plain-text",
                    color="primary" if self.active_tab == "signin" else "neutral",
                    min_height=1.8,
                    grow_x=True,
                    on_press=lambda: self._set_tab("signin"),
                ),
                rio.Button(
                    "Create Account",
                    icon="material/person-add",
                    shape="rounded",
                    style="major" if self.active_tab == "signup" else "plain-text",
                    color="primary" if self.active_tab == "signup" else "neutral",
                    min_height=1.8,
                    grow_x=True,
                    on_press=lambda: self._set_tab("signup"),
                ),
                spacing=0.2,
                margin=0.15,
                align_y=0.5,
                grow_x=True,
            ),
            corner_radius=0.35,
            color="hud",
            grow_x=True,
        )

        # Alerts / Messages
        feedback_banner: Optional[rio.Component] = None
        if self.error_message:
            feedback_banner = rio.Card(
                rio.Row(
                    rio.Icon("material/error", fill=COLOR_DOWN_STRONG, min_width=1.1, min_height=1.1),
                    rio.Text(self.error_message, font_size=0.78, fill=COLOR_DOWN_STRONG, grow_x=True),
                    spacing=0.3,
                    margin=0.3,
                    align_y=0.5,
                    grow_x=True,
                ),
                corner_radius=0.3,
                color="hud",
                grow_x=True,
            )
        elif self.success_message:
            feedback_banner = rio.Card(
                rio.Row(
                    rio.Icon("material/check-circle", fill=COLOR_UP_STRONG, min_width=1.1, min_height=1.1),
                    rio.Text(self.success_message, font_size=0.78, fill=COLOR_UP_STRONG, grow_x=True),
                    spacing=0.3,
                    margin=0.3,
                    align_y=0.5,
                    grow_x=True,
                ),
                corner_radius=0.3,
                color="hud",
                grow_x=True,
            )

        # Tab Content
        form_content: rio.Component

        if self.active_tab == "signin":
            form_content = rio.Column(
                rio.TextInput(
                    label="Username or Email Address",
                    text=self.bind().signin_identifier,
                    grow_x=True,
                ),
                rio.TextInput(
                    label="Password",
                    is_secret=True,
                    text=self.bind().signin_password,
                    grow_x=True,
                ),
                rio.Button(
                    "Sign In to Portfolio",
                    icon="material/arrow-forward",
                    shape="rounded",
                    style="major",
                    color="primary",
                    min_height=2.2,
                    is_loading=self.is_loading,
                    grow_x=True,
                    on_press=self._handle_signin,
                ),
                rio.Row(
                    rio.Separator(grow_x=True),
                    rio.Text("OR", font_size=0.7, fill=COLOR_TEXT_DIM, margin_x=0.3),
                    rio.Separator(grow_x=True),
                    align_y=0.5,
                    margin_y=0.1,
                    grow_x=True,
                ),
                rio.Button(
                    "Explore with Quick Demo Account",
                    icon="material/bolt",
                    shape="rounded",
                    style="minor",
                    color="secondary",
                    min_height=2.0,
                    grow_x=True,
                    on_press=self._handle_demo_login,
                ),
                spacing=0.35,
                grow_x=True,
            )
        else:
            # Sign Up Form with Avatar Picker
            avatar_cards: list[rio.Component] = []
            for av in AVAILABLE_AVATARS:
                is_sel = self.signup_avatar_id == av.id
                av_id = av.id
                avatar_cards.append(
                    rio.Card(
                        rio.Column(
                            rio.Icon(av.icon, fill=rio.Color.from_hex(av.color_hex), min_width=1.4, min_height=1.4),
                            rio.Text(av.name, font_size=0.75, font_weight="bold", align_x=0.5),
                            rio.Text(av.role, font_size=0.65, fill=COLOR_TEXT_MUTED, align_x=0.5),
                            spacing=0.03,
                            margin=0.25,
                            align_x=0.5,
                            align_y=0.5,
                            grow_x=True,
                        ),
                        corner_radius=0.3,
                        color="primary" if is_sel else "hud",
                        on_press=lambda a=av_id: self._select_avatar(a),
                    )
                )

            avatar_picker = rio.Column(
                rio.Text("Choose Your Trader Avatar", font_size=0.78, font_weight="bold", fill=COLOR_TEXT_MUTED),
                rio.FlowContainer(
                    *avatar_cards,
                    spacing=0.25,
                    row_spacing=0.25,
                    column_spacing=0.25,
                    justify="justify",
                    grow_x=True,
                ),
                spacing=0.2,
                grow_x=True,
            )

            form_content = rio.Column(
                rio.TextInput(
                    label="Full Name / Display Name",
                    text=self.bind().signup_full_name,
                    grow_x=True,
                ),
                rio.Row(
                    rio.TextInput(
                        label="Username (letters & numbers)",
                        text=self.bind().signup_username,
                        grow_x=True,
                    ),
                    rio.TextInput(
                        label="Email Address",
                        text=self.bind().signup_email,
                        grow_x=True,
                    ),
                    spacing=0.3,
                    grow_x=True,
                ) if not is_mobile else rio.Column(
                    rio.TextInput(
                        label="Username (letters & numbers)",
                        text=self.bind().signup_username,
                        grow_x=True,
                    ),
                    rio.TextInput(
                        label="Email Address",
                        text=self.bind().signup_email,
                        grow_x=True,
                    ),
                    spacing=0.3,
                    grow_x=True,
                ),
                rio.TextInput(
                    label="Password (min 6 characters)",
                    is_secret=True,
                    text=self.bind().signup_password,
                    grow_x=True,
                ),
                avatar_picker,
                rio.Button(
                    "Complete Registration & Start Tracking",
                    icon="material/check",
                    shape="rounded",
                    style="major",
                    color="primary",
                    min_height=2.2,
                    is_loading=self.is_loading,
                    grow_x=True,
                    on_press=self._handle_signup,
                ),
                spacing=0.35,
                grow_x=True,
            )

        # Local Storage & Legal Disclaimer Notice
        disclaimer_card = rio.Card(
            rio.Row(
                rio.Icon("material/shield", fill=rio.Color.from_hex("#10B981"), min_width=1.1, min_height=1.1),
                rio.Column(
                    rio.Text(
                        "Local Computer Storage & Privacy Guarantee",
                        font_size=0.72,
                        font_weight="bold",
                        fill=rio.Color.from_hex("#10B981"),
                    ),
                    rio.Text(
                        "Your credentials, stocks, and research cycles are stored securely on your local computer database. Easily switch to cloud DB anytime.",
                        font_size=0.65,
                        fill=COLOR_TEXT_DIM,
                    ),
                    spacing=0.02,
                    grow_x=True,
                ),
                spacing=0.3,
                margin=0.3,
                align_y=0.5,
                grow_x=True,
            ),
            corner_radius=0.3,
            color="hud",
            grow_x=True,
        )

        return rio.Card(
            rio.Column(
                header,
                rio.Separator(),
                tab_switcher,
                feedback_banner if feedback_banner else rio.Spacer(),
                form_content,
                disclaimer_card,
                spacing=0.4,
                margin=0.6 if is_mobile else 0.8,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            min_width=24.0 if not is_mobile else 18.0,
            grow_x=True,
        )
