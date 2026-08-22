"""Beautiful, world-class Institutional SaaS Homepage with rich hero, feature grid, and zero overflow."""

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
    """Institutional landing page with rich feature grid and modal-based auth triggers."""

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
        badge_text: str,
    ) -> rio.Component:
        return rio.Card(
            rio.Column(
                rio.Row(
                    rio.Icon(icon, fill=rio.Color.from_hex(icon_color), min_width=1.3, min_height=1.3),
                    rio.Spacer(),
                    rio.Card(
                        rio.Text(tag, font_size=0.6, font_weight="bold", fill=rio.Color.from_hex(icon_color), margin_x=0.25, margin_y=0.08),
                        corner_radius=0.2,
                        color="hud",
                    ),
                    spacing=0.2,
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Text(title, font_size=0.88, font_weight="bold"),
                rio.Text(description, font_size=0.72, fill=COLOR_TEXT_MUTED),
                rio.Spacer(),
                rio.Card(
                    rio.Row(
                        rio.Icon("material/check-circle", fill=rio.Color.from_hex(icon_color), min_width=0.8, min_height=0.8),
                        rio.Text(badge_text, font_size=0.64, font_weight="bold", fill=COLOR_TEXT_DIM),
                        spacing=0.15,
                        margin_x=0.3,
                        margin_y=0.1,
                        align_y=0.5,
                    ),
                    corner_radius=0.25,
                    color="hud",
                    align_x=0.0,
                ),
                spacing=0.18,
                margin=0.5,
                grow_x=True,
            ),
            corner_radius=0.4,
            color="neutral",
            grow_x=True,
        )

    def _build_bottom_card(
        self,
        icon: str,
        icon_color: str,
        title: str,
        description: str,
    ) -> rio.Component:
        return rio.Card(
            rio.Row(
                rio.Icon(icon, fill=rio.Color.from_hex(icon_color), min_width=1.4, min_height=1.4),
                rio.Column(
                    rio.Text(title, font_size=0.82, font_weight="bold"),
                    rio.Text(description, font_size=0.7, fill=COLOR_TEXT_MUTED),
                    spacing=0.02,
                    grow_x=True,
                ),
                spacing=0.3,
                margin=0.4,
                align_y=0.5,
                grow_x=True,
            ),
            corner_radius=0.35,
            color="hud",
            grow_x=True,
        )

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 45.0

        # Hero Section
        hero_badge = rio.Card(
            rio.Row(
                rio.Icon("material/bolt", fill=rio.Color.from_hex("#3B82F6"), min_width=0.85, min_height=0.85),
                rio.Text(
                    "INSTITUTIONAL CYCLE INTELLIGENCE • LOCAL FIRST",
                    font_size=0.68,
                    font_weight="bold",
                    fill=rio.Color.from_hex("#3B82F6"),
                ),
                spacing=0.15,
                margin_x=0.35,
                margin_y=0.08,
                align_y=0.5,
            ),
            corner_radius=0.4,
            color="hud",
            grow_x=False,
            align_x=0.5,
        )

        hero_title = rio.Text(
            "Master Recurring Annual Stock Cycles\nBenchmark Reference Highs with Precision",
            font_size=1.5 if is_mobile else 2.1,
            font_weight="bold",
            align_x=0.5,
        )

        hero_subhead = rio.Text(
            "Systematic calendar recurrence mapping, automated +1 trading day settlement adjustments, and multi-year technical analytics — 100% private in local SQLite.",
            font_size=0.76 if is_mobile else 0.86,
            fill=COLOR_TEXT_MUTED,
            align_x=0.5,
        )

        hero_actions = rio.Row(
            rio.Button(
                "Get Started Free",
                icon="material/person-add",
                shape="rounded",
                style="major",
                color="primary",
                min_height=2.2,
                min_width=10.0,
                on_press=self.on_open_signup,
            ),
            rio.Button(
                "Launch Instant Demo",
                icon="material/bolt",
                shape="rounded",
                style="minor",
                color="secondary",
                min_height=2.2,
                min_width=10.0,
                on_press=self.on_quick_demo,
            ),
            spacing=0.35,
            align_x=0.5,
            align_y=0.5,
        )

        hero_card = rio.Card(
            rio.Column(
                hero_badge,
                hero_title,
                hero_subhead,
                hero_actions,
                spacing=0.3,
                margin=0.5 if is_mobile else 0.7,
                align_x=0.5,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            margin_x=0.4 if is_mobile else 0.8,
            margin_top=0.2,
            grow_x=True,
        )

        # 3 Main Feature Cards (Middle Row)
        f1 = self._build_feature_card(
            icon="material/history-toggle-off",
            icon_color="#3B82F6",
            tag="RECURRENCE ENGINE",
            title="Annual Cycle Projection",
            description="Projects reference dates forward across multi-year cycles. Automatically handles leap years, weekends, and exchange holidays with settlement logic.",
            badge_text="+1 Trading Day Holiday Resolution",
        )
        f2 = self._build_feature_card(
            icon="material/candlestick-chart",
            icon_color="#8B5CF6",
            tag="TECHNICAL ANALYTICS",
            title="Multi-Timeframe Charts",
            description="Inspect historical candlestick price action from 1M to Max timelines with interactive 50 DMA, 200 DMA, and trading volume overlays.",
            badge_text="1M • 6M • 1Y • 3Y • 5Y • 10Y • Max",
        )
        f3 = self._build_feature_card(
            icon="material/calculate",
            icon_color="#EC4899",
            tag="PERFORMANCE TIERS",
            title="Classification Buckets",
            description="Categorizes tracked assets into 10 granular upside (>20% to 0-5%) and downside discount tiers benchmarked against historical cycle reference highs.",
            badge_text="10 Granular Performance Tiers",
        )

        middle_row: rio.Component
        if is_mobile:
            middle_row = rio.Column(f1, f2, f3, spacing=0.25, grow_x=True)
        else:
            middle_row = rio.Row(f1, f2, f3, spacing=0.35, grow_x=True)

        middle_section = rio.Column(
            middle_row,
            margin_x=0.4 if is_mobile else 0.8,
            margin_top=0.25,
            grow_x=True,
        )

        # Bottom 2 Capability Highlights
        b1 = self._build_bottom_card(
            icon="material/table-view",
            icon_color="#F59E0B",
            title="Excel Batch Ingestion & 18-Column Export",
            description="Seamlessly upload trade journals with auto-column mapping and export comprehensive institutional calculation reports.",
        )
        b2 = self._build_bottom_card(
            icon="material/security",
            icon_color="#10B981",
            title="100% Offline SQLite Privacy & Security",
            description="All credentials, stock cycles, and portfolio calculations reside directly on your local computer with zero cloud telemetry.",
        )

        bottom_row: rio.Component
        if is_mobile:
            bottom_row = rio.Column(b1, b2, spacing=0.2, grow_x=True)
        else:
            bottom_row = rio.Row(b1, b2, spacing=0.35, grow_x=True)

        bottom_section = rio.Column(
            bottom_row,
            margin_x=0.4 if is_mobile else 0.8,
            margin_top=0.2,
            margin_bottom=0.3,
            grow_x=True,
        )

        return rio.Column(
            hero_card,
            middle_section,
            bottom_section,
            spacing=0.15,
            grow_x=True,
            align_y=0.0,
        )
