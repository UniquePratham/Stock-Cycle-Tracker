"""Beautiful, centered Institutional Homepage with rich hero, capability showcase, and modal-based Auth triggers."""

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
    """Clean, high-impact institutional homepage without embedded inputs."""

    on_open_signin: Callable[[], None]
    on_open_signup: Callable[[], None]
    on_quick_demo: Callable[[], None]

    def _build_showcase_card(
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
                    "INSTITUTIONAL CYCLE INTELLIGENCE • LOCAL FIRST",
                    font_size=0.68,
                    font_weight="bold",
                    fill=rio.Color.from_hex("#3B82F6"),
                ),
                spacing=0.2,
                margin_x=0.4,
                margin_y=0.12,
                align_y=0.5,
            ),
            corner_radius=0.5,
            color="hud",
            grow_x=False,
            align_x=0.5,
        )

        # Centered Hero Title & Subhead
        hero_title = rio.Text(
            "Track Recurring Stock Cycles.\nBenchmark Reference Highs.",
            font_size=1.8 if is_mobile else 2.5,
            font_weight="bold",
            align_x=0.5,
        )

        hero_subhead = rio.Text(
            "Systematic calendar recurrence mapping, automated +1 trading day holiday resolution, and multi-year timeframe analytics — stored 100% privately on your local computer.",
            font_size=0.82 if is_mobile else 0.95,
            fill=COLOR_TEXT_MUTED,
            align_x=0.5,
        )

        # Centered Hero Action Buttons
        hero_actions: rio.Component
        if is_mobile:
            hero_actions = rio.Column(
                rio.Button(
                    "Create Free Account",
                    icon="material/person-add",
                    shape="rounded",
                    style="major",
                    color="primary",
                    min_height=2.3,
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
                    "Explore with Instant Demo",
                    icon="material/bolt",
                    shape="rounded",
                    style="plain-text",
                    color="secondary",
                    min_height=2.0,
                    grow_x=True,
                    on_press=self.on_quick_demo,
                ),
                spacing=0.25,
                margin_x=0.4,
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
                    min_height=2.3,
                    min_width=11.5,
                    on_press=self.on_open_signup,
                ),
                rio.Button(
                    "Sign In to Portfolio",
                    icon="material/login",
                    shape="rounded",
                    style="minor",
                    color="neutral",
                    min_height=2.3,
                    min_width=10.5,
                    on_press=self.on_open_signin,
                ),
                rio.Button(
                    "Explore Instant Demo",
                    icon="material/bolt",
                    shape="rounded",
                    style="minor",
                    color="secondary",
                    min_height=2.3,
                    min_width=10.5,
                    on_press=self.on_quick_demo,
                ),
                spacing=0.35,
                align_x=0.5,
                align_y=0.5,
            )

        # 4 Core Capability Cards
        c1 = self._build_showcase_card(
            icon="material/history-toggle-off",
            icon_color="#3B82F6",
            title="Annual Cycle Recurrence",
            subtitle="Automated +1 trading day settlement adjustment for weekends & NSE/BSE holidays",
        )
        c2 = self._build_showcase_card(
            icon="material/candlestick-chart",
            icon_color="#8B5CF6",
            title="Screener-Grade Charts",
            subtitle="1M to Max historical candlestick timelines with 50 DMA, 200 DMA & Volume",
        )
        c3 = self._build_showcase_card(
            icon="material/calculate",
            icon_color="#EC4899",
            title="10 Classification Buckets",
            subtitle="Granular upside and downside percentage performance tiers benchmarked to reference highs",
        )
        c4 = self._build_showcase_card(
            icon="material/security",
            icon_color="#10B981",
            title="100% Local Privacy",
            subtitle="Credentials, stock portfolios, and cycles reside exclusively in your local SQLite database",
        )

        showcase_grid: rio.Component
        if is_mobile:
            showcase_grid = rio.Column(c1, c2, c3, c4, spacing=0.3, grow_x=True)
        else:
            showcase_grid = rio.Row(c1, c2, c3, c4, spacing=0.35, grow_x=True)

        return rio.Column(
            rio.Card(
                rio.Column(
                    hero_badge,
                    hero_title,
                    hero_subhead,
                    hero_actions,
                    spacing=0.5,
                    margin=0.8 if is_mobile else 1.2,
                    align_x=0.5,
                    grow_x=True,
                ),
                corner_radius=0.5,
                color="neutral",
                margin_x=0.4 if is_mobile else 0.8,
                margin_top=0.3,
                grow_x=True,
            ),
            rio.Card(
                rio.Column(
                    rio.Row(
                        rio.Icon("material/diamond", fill=rio.Color.from_hex("#3B82F6"), min_width=1.1, min_height=1.1),
                        rio.Text("Core Architecture & Institutional Capabilities", font_size=0.88, font_weight="bold"),
                        spacing=0.2,
                        align_y=0.5,
                        align_x=0.5,
                    ),
                    showcase_grid,
                    spacing=0.4,
                    margin=0.6 if is_mobile else 0.8,
                    grow_x=True,
                ),
                corner_radius=0.5,
                color="hud",
                margin_x=0.4 if is_mobile else 0.8,
                margin_top=0.3,
                margin_bottom=0.4,
                grow_x=True,
            ),
            spacing=0.2,
            grow_x=True,
            align_y=0.0,
        )
