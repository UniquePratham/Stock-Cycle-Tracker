"""Homepage with full responsiveness across mobile, tablet, and desktop viewports, stock-themed background, centered hero text, and zero overflow."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import rio

from stock_cycle_tracker.ui.theme import (
    COLOR_TEXT_MUTED,
)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
HERO_BG_PATH = ASSETS_DIR / "hero_bg.jpg"


class HomeView(rio.Component):
    """Full-viewport responsive hero landing page with stock background and adaptive layout."""

    on_open_signin: Callable[[], None]
    on_open_signup: Callable[[], None]
    on_quick_demo: Callable[[], None]

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 50.0
        is_small_mobile = self.session.window_width < 32.0

        # ── Hero Badge ──
        hero_badge = rio.Card(
            rio.Text(
                "⚡  CYCLE INTELLIGENCE  •  LOCAL FIRST" if is_mobile else "⚡  INSTITUTIONAL CYCLE INTELLIGENCE  •  LOCAL FIRST",
                font_size=0.6 if is_mobile else 0.7,
                font_weight="bold",
                fill=rio.Color.from_hex("#3B82F6"),
                margin_x=0.4 if is_mobile else 0.5,
                margin_y=0.1,
            ),
            corner_radius=1.0,
            color="hud",
            align_x=0.5,
        )

        # ── Hero Title ──
        title_size = 1.4 if is_small_mobile else (1.75 if is_mobile else 2.3)
        hero_title = rio.Column(
            rio.Text(
                "Master Recurring",
                font_size=title_size,
                font_weight="bold",
                align_x=0.5,
            ),
            rio.Text(
                "Annual Stock Cycles",
                font_size=title_size,
                font_weight="bold",
                align_x=0.5,
            ),
            spacing=0.05 if is_mobile else 0.1,
            align_x=0.5,
        )

        # ── Hero Subtitle ──
        sub_size = 0.72 if is_mobile else 0.88
        hero_sub = rio.Column(
            rio.Text(
                "Benchmark reference highs with precision.",
                font_size=sub_size,
                fill=COLOR_TEXT_MUTED,
                align_x=0.5,
            ),
            rio.Text(
                "Automated recurrence mapping, holiday settlement,",
                font_size=sub_size,
                fill=COLOR_TEXT_MUTED,
                align_x=0.5,
            ),
            rio.Text(
                "and multi-year analytics — 100% private.",
                font_size=sub_size,
                fill=COLOR_TEXT_MUTED,
                align_x=0.5,
            ),
            spacing=0.04,
            align_x=0.5,
        )

        # ── CTA Buttons (Row on desktop, full-width Column on mobile) ──
        cta_actions: rio.Component
        btn_height = 2.2 if is_mobile else 2.4
        if is_mobile:
            cta_actions = rio.Column(
                rio.Button(
                    "Get Started Free",
                    icon="material/person-add",
                    shape="rounded",
                    style="major",
                    color="primary",
                    min_height=btn_height,
                    grow_x=True,
                    on_press=self.on_open_signup,
                ),
                rio.Button(
                    "Launch Demo",
                    icon="material/bolt",
                    shape="rounded",
                    style="minor",
                    color="secondary",
                    min_height=btn_height,
                    grow_x=True,
                    on_press=self.on_quick_demo,
                ),
                spacing=0.25,
                margin_x=1.0,
                align_x=0.5,
                grow_x=True,
            )
        else:
            cta_actions = rio.Row(
                rio.Button(
                    "Get Started Free",
                    icon="material/person-add",
                    shape="rounded",
                    style="major",
                    color="primary",
                    min_height=btn_height,
                    on_press=self.on_open_signup,
                ),
                rio.Button(
                    "Launch Demo",
                    icon="material/bolt",
                    shape="rounded",
                    style="minor",
                    color="secondary",
                    min_height=btn_height,
                    on_press=self.on_quick_demo,
                ),
                spacing=0.4,
                align_x=0.5,
            )

        # ── Feature Pills ──
        pill_1 = rio.Row(
            rio.Icon("material/history-toggle-off", fill=rio.Color.from_hex("#3B82F6"), min_width=0.9 if is_mobile else 1.0, min_height=0.9 if is_mobile else 1.0),
            rio.Text("Annual Recurrence", font_size=0.72 if is_mobile else 0.78, font_weight="bold"),
            spacing=0.15,
            align_y=0.5,
        )
        pill_2 = rio.Row(
            rio.Icon("material/candlestick-chart", fill=rio.Color.from_hex("#8B5CF6"), min_width=0.9 if is_mobile else 1.0, min_height=0.9 if is_mobile else 1.0),
            rio.Text("Multi-Timeframe Charts", font_size=0.72 if is_mobile else 0.78, font_weight="bold"),
            spacing=0.15,
            align_y=0.5,
        )
        pill_3 = rio.Row(
            rio.Icon("material/security", fill=rio.Color.from_hex("#10B981"), min_width=0.9 if is_mobile else 1.0, min_height=0.9 if is_mobile else 1.0),
            rio.Text("100% Offline & Private", font_size=0.72 if is_mobile else 0.78, font_weight="bold"),
            spacing=0.15,
            align_y=0.5,
        )

        features_strip: rio.Component
        if is_mobile:
            features_strip = rio.Column(
                pill_1,
                pill_2,
                pill_3,
                spacing=0.18,
                align_x=0.5,
            )
        else:
            features_strip = rio.Row(
                pill_1,
                rio.Text("•", font_size=0.8, fill=COLOR_TEXT_MUTED),
                pill_2,
                rio.Text("•", font_size=0.8, fill=COLOR_TEXT_MUTED),
                pill_3,
                spacing=0.4,
                align_x=0.5,
                align_y=0.5,
            )

        # ── Privacy Footer ──
        privacy_line = rio.Text(
            "🔒  100% Offline SQLite Privacy • Zero Telemetry" if is_mobile else "🔒  All data stored locally in SQLite  •  Zero cloud telemetry  •  Your data never leaves your machine",
            font_size=0.62 if is_mobile else 0.68,
            fill=COLOR_TEXT_MUTED,
            align_x=0.5,
        )

        # ── Hero content group ──
        hero_content = rio.Column(
            hero_badge,
            hero_title,
            hero_sub,
            cta_actions,
            spacing=0.35 if is_mobile else 0.45,
            align_x=0.5,
            grow_x=True,
        )

        # ── Bottom strip ──
        bottom_strip = rio.Column(
            features_strip,
            privacy_line,
            spacing=0.3 if is_mobile else 0.4,
            align_x=0.5,
            grow_x=True,
        )

        # ── Foreground content ──
        foreground = rio.Column(
            rio.Spacer(),
            hero_content,
            rio.Spacer(),
            rio.Spacer() if not is_mobile else rio.Row(),
            bottom_strip,
            spacing=0.2 if is_mobile else 0.3,
            margin_x=0.5 if is_mobile else 1.5,
            margin_bottom=0.4 if is_mobile else 0.6,
            margin_top=3.0 if is_mobile else 3.5,
            grow_x=True,
            grow_y=True,
        )

        # ── Background image layer ──
        bg_image: rio.Component
        if HERO_BG_PATH.exists():
            bg_image = rio.Image(
                HERO_BG_PATH,
                fill_mode="stretch",
                grow_x=True,
                grow_y=True,
                corner_radius=0,
            )
        else:
            bg_image = rio.Rectangle(
                fill=rio.Color.from_hex("#090D16"),
                grow_x=True,
                grow_y=True,
            )

        # ── Stack: background + foreground ──
        return rio.Stack(
            bg_image,
            foreground,
            grow_x=True,
            grow_y=True,
        )
