"""Beautiful, ultra-clean, zero-overflow Homepage with centered hero and compact feature pillars."""

from __future__ import annotations

from typing import Callable

import rio

from stock_cycle_tracker.ui.theme import (
    COLOR_BORDER,
    COLOR_DOWN_STRONG,
    COLOR_SURFACE_CARD,
    COLOR_TEXT_DIM,
    COLOR_TEXT_MUTED,
    COLOR_UP_STRONG,
)


class HomeView(rio.Component):
    """Clean, centered institutional homepage with modal-based authentication."""

    on_open_signin: Callable[[], None]
    on_open_signup: Callable[[], None]
    on_quick_demo: Callable[[], None]

    def _build_feature_card(
        self,
        icon: str,
        icon_color: str,
        title: str,
        subtitle: str,
    ) -> rio.Component:
        return rio.Card(
            rio.Column(
                rio.Icon(icon, fill=rio.Color.from_hex(icon_color), min_width=1.5, min_height=1.5, align_x=0.5),
                rio.Text(title, font_size=0.88, font_weight="bold", align_x=0.5),
                rio.Text(subtitle, font_size=0.72, fill=COLOR_TEXT_MUTED, align_x=0.5),
                spacing=0.15,
                margin=0.4,
                align_x=0.5,
                grow_x=True,
            ),
            corner_radius=0.35,
            color="neutral",
            grow_x=True,
        )

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 55.0

        # Hero Badge
        hero_badge = rio.Card(
            rio.Row(
                rio.Icon("material/bolt", fill=rio.Color.from_hex("#3B82F6"), min_width=0.9, min_height=0.9),
                rio.Text(
                    "INSTITUTIONAL CYCLE INTELLIGENCE",
                    font_size=0.68,
                    font_weight="bold",
                    fill=rio.Color.from_hex("#3B82F6"),
                ),
                spacing=0.15,
                margin_x=0.35,
                margin_y=0.1,
                align_y=0.5,
            ),
            corner_radius=0.4,
            color="hud",
            grow_x=False,
            align_x=0.5,
        )

        # Centered Hero Title & Subhead
        hero_title = rio.Text(
            "Track Recurring Stock Cycles.\nBenchmark Reference Highs.",
            font_size=1.6 if is_mobile else 2.3,
            font_weight="bold",
            align_x=0.5,
        )

        hero_subhead = rio.Text(
            "Automated annual recurrence mapping, +1 day exchange holiday resolution, and multi-year screener charts.",
            font_size=0.82 if is_mobile else 0.92,
            fill=COLOR_TEXT_MUTED,
            align_x=0.5,
        )

        # Hero Action Buttons
        hero_actions: rio.Component
        if is_mobile:
            hero_actions = rio.Column(
                rio.Button(
                    "Create Free Account",
                    icon="material/person-add",
                    shape="rounded",
                    style="major",
                    color="primary",
                    min_height=2.2,
                    grow_x=True,
                    on_press=self.on_open_signup,
                ),
                rio.Button(
                    "Sign In to Portfolio",
                    icon="material/login",
                    shape="rounded",
                    style="minor",
                    color="neutral",
                    min_height=2.2,
                    grow_x=True,
                    on_press=self.on_open_signin,
                ),
                rio.Button(
                    "Explore Instant Demo",
                    icon="material/bolt",
                    shape="rounded",
                    style="plain-text",
                    color="secondary",
                    min_height=2.0,
                    grow_x=True,
                    on_press=self.on_quick_demo,
                ),
                spacing=0.2,
                grow_x=True,
            )
        else:
            hero_actions = rio.Row(
                rio.Button(
                    "Create Free Account",
                    icon="material/person-add",
                    shape="rounded",
                    style="major",
                    color="primary",
                    min_height=2.2,
                    min_width=10.0,
                    on_press=self.on_open_signup,
                ),
                rio.Button(
                    "Sign In to Portfolio",
                    icon="material/login",
                    shape="rounded",
                    style="minor",
                    color="neutral",
                    min_height=2.2,
                    min_width=9.5,
                    on_press=self.on_open_signin,
                ),
                rio.Button(
                    "Explore Instant Demo",
                    icon="material/bolt",
                    shape="rounded",
                    style="minor",
                    color="secondary",
                    min_height=2.2,
                    min_width=9.5,
                    on_press=self.on_quick_demo,
                ),
                spacing=0.3,
                align_x=0.5,
                align_y=0.5,
            )

        hero_card = rio.Card(
            rio.Column(
                hero_badge,
                hero_title,
                hero_subhead,
                hero_actions,
                spacing=0.4,
                margin=0.6 if is_mobile else 0.9,
                align_x=0.5,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            margin_x=0.4 if is_mobile else 0.8,
            margin_top=0.3,
            grow_x=True,
        )

        # 3 Core Pillars (fits perfectly across any screen width)
        p1 = self._build_feature_card(
            icon="material/history-toggle-off",
            icon_color="#3B82F6",
            title="Annual Cycle Recurrence",
            subtitle="Automated +1 trading day settlement adjustment for NSE/BSE holidays",
        )
        p2 = self._build_feature_card(
            icon="material/candlestick-chart",
            icon_color="#8B5CF6",
            title="Screener-Grade Candlesticks",
            subtitle="1M to Max timelines with 50 DMA, 200 DMA, and Volume overlays",
        )
        p3 = self._build_feature_card(
            icon="material/security",
            icon_color="#10B981",
            title="100% Local Machine Privacy",
            subtitle="Credentials and stock portfolios stored on your computer in SQLite",
        )

        pillars_layout: rio.Component
        if is_mobile:
            pillars_layout = rio.Column(p1, p2, p3, spacing=0.25, grow_x=True)
        else:
            pillars_layout = rio.Row(p1, p2, p3, spacing=0.3, grow_x=True)

        pillars_card = rio.Card(
            rio.Column(
                rio.Row(
                    rio.Icon("material/diamond", fill=rio.Color.from_hex("#3B82F6"), min_width=1.0, min_height=1.0),
                    rio.Text("Institutional Platform Capabilities", font_size=0.82, font_weight="bold"),
                    spacing=0.2,
                    align_y=0.5,
                    align_x=0.5,
                ),
                pillars_layout,
                spacing=0.35,
                margin=0.5 if is_mobile else 0.7,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="hud",
            margin_x=0.4 if is_mobile else 0.8,
            margin_top=0.25,
            margin_bottom=0.3,
            grow_x=True,
        )

        return rio.Column(
            hero_card,
            pillars_card,
            spacing=0.15,
            grow_x=True,
            align_y=0.0,
        )
