"""Homepage / Landing View for unauthenticated users with Institutional Hero, Feature Grid, and Auth CTAs."""

from __future__ import annotations

from typing import Callable

import rio

from stock_cycle_tracker.domain.user import AVAILABLE_AVATARS
from stock_cycle_tracker.ui.theme import (
    COLOR_BORDER,
    COLOR_DOWN_STRONG,
    COLOR_SURFACE_CARD,
    COLOR_TEXT_DIM,
    COLOR_TEXT_MUTED,
    COLOR_UP_STRONG,
)


class HomeView(rio.Component):
    """Institutional landing page introducing Stock Cycle Tracker with direct authentication triggers."""

    on_open_signin: Callable[[], None]
    on_open_signup: Callable[[], None]
    on_quick_demo: Callable[[], None]

    def _build_feature_card(
        self,
        icon: str,
        icon_color: str,
        tag: str,
        title: str,
        description: str,
    ) -> rio.Component:
        return rio.Card(
            rio.Column(
                rio.Row(
                    rio.Icon(icon, fill=rio.Color.from_hex(icon_color), min_width=1.4, min_height=1.4),
                    rio.Spacer(),
                    rio.Card(
                        rio.Text(tag, font_size=0.62, font_weight="bold", fill=rio.Color.from_hex(icon_color), margin_x=0.25, margin_y=0.08),
                        corner_radius=0.2,
                        color="hud",
                    ),
                    spacing=0.2,
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Text(title, font_weight="bold", font_size=0.92),
                rio.Text(description, font_size=0.74, fill=COLOR_TEXT_MUTED),
                spacing=0.18,
                margin=0.5,
                grow_x=True,
                align_y=0.0,
            ),
            corner_radius=0.4,
            color="neutral",
            grow_x=True,
        )

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 55.0

        # Hero Badge
        hero_badge = rio.Card(
            rio.Row(
                rio.Icon("material/bolt", fill=rio.Color.from_hex("#3B82F6"), min_width=1.0, min_height=1.0),
                rio.Text(
                    "INSTITUTIONAL CYCLE INTELLIGENCE • LOCAL FIRST",
                    font_size=0.7,
                    font_weight="bold",
                    fill=rio.Color.from_hex("#3B82F6"),
                ),
                spacing=0.2,
                margin_x=0.4,
                margin_y=0.15,
                align_y=0.5,
            ),
            corner_radius=0.5,
            color="hud",
            grow_x=False,
            align_x=0.5,
        )

        # Hero Headline & Subhead
        hero_text = rio.Column(
            hero_badge,
            rio.Text(
                "Track Recurring Stock Cycles.\nGain Institutional Edge.",
                font_size=1.8 if is_mobile else 2.6,
                font_weight="bold",
                align_x=0.5,
            ),
            rio.Text(
                "Automated calendar recurrence mapping, dynamic +1 trading day holiday resolution, and multi-year timeframe analytics — stored 100% privately on your local computer.",
                font_size=0.85 if is_mobile else 1.0,
                fill=COLOR_TEXT_MUTED,
                align_x=0.5,
            ),
            spacing=0.4,
            align_x=0.5,
            grow_x=True,
        )

        # Hero Action CTAs
        hero_actions: rio.Component
        if is_mobile:
            hero_actions = rio.Column(
                rio.Button(
                    "Create Free Account",
                    icon="material/person-add",
                    shape="rounded",
                    style="major",
                    color="primary",
                    min_height=2.4,
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
                margin_x=0.5,
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
                    min_height=2.4,
                    min_width=11.0,
                    on_press=self.on_open_signup,
                ),
                rio.Button(
                    "Sign In to Portfolio",
                    icon="material/login",
                    shape="rounded",
                    style="minor",
                    color="neutral",
                    min_height=2.4,
                    min_width=9.0,
                    on_press=self.on_open_signin,
                ),
                rio.Button(
                    "Explore Instant Demo",
                    icon="material/bolt",
                    shape="rounded",
                    style="minor",
                    color="secondary",
                    min_height=2.4,
                    min_width=10.0,
                    on_press=self.on_quick_demo,
                ),
                spacing=0.4,
                align_x=0.5,
                align_y=0.5,
            )

        hero_section = rio.Card(
            rio.Column(
                hero_text,
                hero_actions,
                spacing=0.8,
                margin=0.8 if is_mobile else 1.4,
                align_x=0.5,
                grow_x=True,
            ),
            corner_radius=0.6,
            color="neutral",
            margin_x=0.4 if is_mobile else 0.8,
            margin_top=0.4,
            grow_x=True,
        )

        # Platform Highlights Grid
        f1 = self._build_feature_card(
            icon="material/history-toggle-off",
            icon_color="#3B82F6",
            tag="RECURRENCE ALGORITHM",
            title="Annual Cycle Benchmarking",
            description="Projects reference dates forward across multi-year cycles. Automatically handles leap years, weekends, and exchange holidays with next-day settlement logic.",
        )
        f2 = self._build_feature_card(
            icon="material/security",
            icon_color="#10B981",
            tag="ZERO CLOUD LOCK-IN",
            title="100% Local Machine Privacy",
            description="All credentials, research cycles, and portfolio calculations are stored directly in your local computer SQLite database with seamless exportability.",
        )
        f3 = self._build_feature_card(
            icon="material/candlestick-chart",
            icon_color="#8B5CF6",
            tag="SCREENER-GRADE CHARTS",
            title="Multi-Timeframe Analytics",
            description="Inspect real historical candlestick patterns from 1M to Max timelines with interactive 50 DMA, 200 DMA, and trading volume overlays.",
        )
        f4 = self._build_feature_card(
            icon="material/calculate",
            icon_color="#EC4899",
            tag="PERFORMANCE TIERS",
            title="Granular Classification Buckets",
            description="Categorizes stocks into 10 distinct upside (>20% to 0-5%) and downside discount buckets against historical cycle reference highs.",
        )
        f5 = self._build_feature_card(
            icon="material/table-view",
            icon_color="#F59E0B",
            tag="BATCH WORKFLOWS",
            title="Excel Ingestion & 18-Col Export",
            description="Seamlessly upload trade journals with auto-column detection and export comprehensive institutional calculation reports in seconds.",
        )
        f6 = self._build_feature_card(
            icon="material/account-circle",
            icon_color="#06B6D4",
            tag="PERSONALIZED STRATEGIES",
            title="8 Curated Trader Personas",
            description="Customize your investor profile with avatars tailored for momentum riders, cycle masters, quantitative analysts, and value compounders.",
        )

        grid_content: rio.Component
        if is_mobile:
            grid_content = rio.Column(f1, f2, f3, f4, f5, f6, spacing=0.35, grow_x=True)
        else:
            row1 = rio.Row(f1, f2, f3, spacing=0.4, grow_x=True)
            row2 = rio.Row(f4, f5, f6, spacing=0.4, grow_x=True)
            grid_content = rio.Column(row1, row2, spacing=0.4, grow_x=True)

        features_grid = rio.Column(
            rio.Row(
                rio.Icon("material/diamond", fill=rio.Color.from_hex("#3B82F6"), min_width=1.2, min_height=1.2),
                rio.Text("Engineered for Serious Market Analysts & Investors", font_weight="bold", font_size=1.05),
                spacing=0.3,
                align_y=0.5,
                margin_x=0.5,
                margin_top=0.6,
            ),
            grid_content,
            spacing=0.4,
            margin_x=0.4 if is_mobile else 0.8,
            grow_x=True,
        )

        # Bottom Call to Action Card
        bottom_cta = rio.Card(
            rio.Column(
                rio.Text("Ready to Track Your Stock Cycles?", font_size=1.2, font_weight="bold", align_x=0.5),
                rio.Text(
                    "Create your account in 10 seconds. All data stays private on your computer.",
                    font_size=0.8,
                    fill=COLOR_TEXT_MUTED,
                    align_x=0.5,
                ),
                rio.Button(
                    "Get Started Free",
                    icon="material/arrow-forward",
                    shape="rounded",
                    style="major",
                    color="primary",
                    min_height=2.2,
                    min_width=10.0,
                    align_x=0.5,
                    on_press=self.on_open_signup,
                ),
                spacing=0.35,
                margin=0.8,
                align_x=0.5,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            margin_x=0.4 if is_mobile else 0.8,
            margin_y=0.6,
            grow_x=True,
        )

        return rio.Column(
            hero_section,
            features_grid,
            bottom_cta,
            spacing=0.4,
            grow_x=True,
            align_y=0.0,
        )
