"""Beautiful, space-optimized Institutional Homepage with live cycle preview, hero metrics, and modal-based auth."""

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
    """Institutional landing page with live cycle preview and balanced viewport utilization."""

    on_open_signin: Callable[[], None]
    on_open_signup: Callable[[], None]
    on_quick_demo: Callable[[], None]

    def _build_preview_row(
        self,
        symbol: str,
        name: str,
        ref_date: str,
        target_date: str,
        cmp_str: str,
        ref_high_str: str,
        diff_str: str,
        bucket_name: str,
        is_positive: bool,
    ) -> rio.Component:
        color_fill = COLOR_UP_STRONG if is_positive else COLOR_DOWN_STRONG

        return rio.Card(
            rio.Row(
                # Stock & Symbol
                rio.Row(
                    rio.Icon("material/trending-up" if is_positive else "material/trending-down", fill=color_fill, min_width=1.1, min_height=1.1),
                    rio.Column(
                        rio.Text(symbol, font_weight="bold", font_size=0.82),
                        rio.Text(name, font_size=0.68, fill=COLOR_TEXT_MUTED),
                        spacing=0.01,
                    ),
                    spacing=0.2,
                    min_width=5.5,
                    align_y=0.5,
                ),
                rio.Spacer(),
                # Reference Date
                rio.Column(
                    rio.Text(ref_date, font_size=0.76, font_weight="bold"),
                    rio.Text("Reference Date", font_size=0.62, fill=COLOR_TEXT_MUTED),
                    spacing=0.01,
                    min_width=4.2,
                    align_y=0.5,
                ),
                rio.Spacer(),
                # Next Cycle Target
                rio.Column(
                    rio.Text(target_date, font_size=0.76, font_weight="bold", fill=rio.Color.from_hex("#3B82F6")),
                    rio.Text("Next Cycle Target", font_size=0.62, fill=COLOR_TEXT_MUTED),
                    spacing=0.01,
                    min_width=4.8,
                    align_y=0.5,
                ),
                rio.Spacer(),
                # CMP & Ref High
                rio.Column(
                    rio.Text(f"CMP: {cmp_str}", font_size=0.76, font_weight="bold"),
                    rio.Text(f"Ref High: {ref_high_str}", font_size=0.62, fill=COLOR_TEXT_MUTED),
                    spacing=0.01,
                    min_width=4.5,
                    align_y=0.5,
                ),
                rio.Spacer(),
                # Upside / Discount Badge
                rio.Card(
                    rio.Text(
                        diff_str,
                        font_size=0.76,
                        font_weight="bold",
                        fill=color_fill,
                        margin_x=0.35,
                        margin_y=0.1,
                    ),
                    corner_radius=0.25,
                    color="hud",
                    align_y=0.5,
                ),
                # Classification Bucket
                rio.Card(
                    rio.Text(
                        bucket_name,
                        font_size=0.72,
                        font_weight="bold",
                        fill=color_fill,
                        margin_x=0.35,
                        margin_y=0.1,
                    ),
                    corner_radius=0.25,
                    color="neutral",
                    align_y=0.5,
                ),
                spacing=0.25,
                margin_x=0.4,
                margin_y=0.2,
                align_y=0.5,
                grow_x=True,
            ),
            corner_radius=0.3,
            color="neutral",
            grow_x=True,
        )

    def _build_feature_card(
        self,
        icon: str,
        icon_color: str,
        title: str,
        subtitle: str,
    ) -> rio.Component:
        return rio.Card(
            rio.Row(
                rio.Icon(icon, fill=rio.Color.from_hex(icon_color), min_width=1.3, min_height=1.3),
                rio.Column(
                    rio.Text(title, font_size=0.82, font_weight="bold"),
                    rio.Text(subtitle, font_size=0.7, fill=COLOR_TEXT_MUTED),
                    spacing=0.02,
                    grow_x=True,
                ),
                spacing=0.25,
                margin=0.35,
                align_y=0.5,
                grow_x=True,
            ),
            corner_radius=0.35,
            color="hud",
            grow_x=True,
        )

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 55.0

        # Hero Badge
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

        # Centered Hero Header
        hero_title = rio.Text(
            "Track Recurring Stock Cycles.\nBenchmark Reference Highs.",
            font_size=1.6 if is_mobile else 2.1,
            font_weight="bold",
            align_x=0.5,
        )

        hero_subhead = rio.Text(
            "Automated annual recurrence mapping, +1 day exchange holiday adjustments, and multi-year technical analytics — stored 100% privately on your computer.",
            font_size=0.78 if is_mobile else 0.86,
            fill=COLOR_TEXT_MUTED,
            align_x=0.5,
        )

        # Action Buttons
        hero_actions = rio.Row(
            rio.Button(
                "Create Free Account",
                icon="material/person-add",
                shape="rounded",
                style="major",
                color="primary",
                min_height=2.1,
                min_width=9.5,
                on_press=self.on_open_signup,
            ),
            rio.Button(
                "Explore Instant Demo",
                icon="material/bolt",
                shape="rounded",
                style="minor",
                color="secondary",
                min_height=2.1,
                min_width=9.5,
                on_press=self.on_quick_demo,
            ),
            rio.Button(
                "Sign In",
                icon="material/login",
                shape="rounded",
                style="plain-text",
                color="neutral",
                min_height=2.1,
                min_width=7.5,
                on_press=self.on_open_signin,
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

        # Live Interactive Preview Table Teaser (Fills viewport with real institutional stock cycle data)
        row1 = self._build_preview_row(
            symbol="RELIANCE",
            name="Reliance Industries Ltd",
            ref_date="18-Sep-2020",
            target_date="21-Sep-2026 (+1 Day)",
            cmp_str="₹3,024.50",
            ref_high_str="₹2,369.35",
            diff_str="+27.65%",
            bucket_name=">20% Upside",
            is_positive=True,
        )
        row2 = self._build_preview_row(
            symbol="HDFCBANK",
            name="HDFC Bank Ltd",
            ref_date="03-Nov-2021",
            target_date="03-Nov-2026",
            cmp_str="₹1,642.10",
            ref_high_str="₹1,725.00",
            diff_str="-4.81%",
            bucket_name="0 to -5% Discount",
            is_positive=False,
        )
        row3 = self._build_preview_row(
            symbol="TCS",
            name="Tata Consultancy Services",
            ref_date="12-Jan-2022",
            target_date="12-Jan-2027",
            cmp_str="₹4,215.80",
            ref_high_str="₹3,990.00",
            diff_str="+5.66%",
            bucket_name="5% to 10% Upside",
            is_positive=True,
        )

        preview_card = rio.Card(
            rio.Column(
                rio.Row(
                    rio.Row(
                        rio.Icon("material/show-chart", fill=rio.Color.from_hex("#3B82F6"), min_width=1.1, min_height=1.1),
                        rio.Text("Live Cycle Engine Preview", font_size=0.84, font_weight="bold"),
                        rio.Card(
                            rio.Text("REAL-TIME RECURRENCE", font_size=0.62, font_weight="bold", fill=rio.Color.from_hex("#10B981"), margin_x=0.25, margin_y=0.06),
                            corner_radius=0.2,
                            color="hud",
                        ),
                        spacing=0.2,
                        align_y=0.5,
                    ),
                    rio.Spacer(),
                    rio.Button(
                        "Launch Full Dashboard",
                        icon="material/arrow-forward",
                        shape="rounded",
                        style="minor",
                        color="primary",
                        min_height=1.7,
                        on_press=self.on_quick_demo,
                    ),
                    spacing=0.25,
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Column(
                    row1,
                    row2,
                    row3,
                    spacing=0.18,
                    grow_x=True,
                ),
                spacing=0.3,
                margin=0.5 if is_mobile else 0.65,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="hud",
            margin_x=0.4 if is_mobile else 0.8,
            margin_top=0.2,
            grow_x=True,
        )

        # 3 Bottom Pillars
        p1 = self._build_feature_card(
            icon="material/history-toggle-off",
            icon_color="#3B82F6",
            title="Annual Cycle Recurrence",
            subtitle="+1 Day holiday adjustment for NSE/BSE",
        )
        p2 = self._build_feature_card(
            icon="material/candlestick-chart",
            icon_color="#8B5CF6",
            title="Multi-Timeframe Charts",
            subtitle="1M to Max timelines with 50 & 200 DMA",
        )
        p3 = self._build_feature_card(
            icon="material/security",
            icon_color="#10B981",
            title="100% Local Privacy",
            subtitle="SQLite database stored on your computer",
        )

        pillars_row: rio.Component
        if is_mobile:
            pillars_row = rio.Column(p1, p2, p3, spacing=0.2, grow_x=True)
        else:
            pillars_row = rio.Row(p1, p2, p3, spacing=0.3, grow_x=True)

        pillars_container = rio.Card(
            pillars_row,
            corner_radius=0.4,
            color="neutral",
            margin_x=0.4 if is_mobile else 0.8,
            margin_top=0.2,
            margin_bottom=0.3,
            grow_x=True,
        )

        return rio.Column(
            hero_card,
            preview_card,
            pillars_container,
            spacing=0.15,
            grow_x=True,
            align_y=0.0,
        )
