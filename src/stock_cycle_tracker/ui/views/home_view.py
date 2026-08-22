"""Homepage with stock-themed background image, centered hero text, and zero overflow."""

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
    """Full-viewport hero landing page with stock background and centered content."""

    on_open_signin: Callable[[], None]
    on_open_signup: Callable[[], None]
    on_quick_demo: Callable[[], None]

    def build(self) -> rio.Component:
        # ── Hero Badge ──
        hero_badge = rio.Card(
            rio.Text(
                "⚡  INSTITUTIONAL CYCLE INTELLIGENCE  •  LOCAL FIRST",
                font_size=0.7,
                font_weight="bold",
                fill=rio.Color.from_hex("#3B82F6"),
                margin_x=0.5,
                margin_y=0.12,
            ),
            corner_radius=1.0,
            color="hud",
            align_x=0.5,
        )

        # ── Hero Title (centered via Column with align_x) ──
        hero_title = rio.Column(
            rio.Text(
                "Master Recurring",
                font_size=2.4,
                font_weight="bold",
            ),
            rio.Text(
                "Annual Stock Cycles",
                font_size=2.4,
                font_weight="bold",
            ),
            spacing=0.1,
            align_x=0.5,
        )

        # ── Hero Subtitle (centered via Column with align_x) ──
        hero_sub = rio.Column(
            rio.Text(
                "Benchmark reference highs with precision.",
                font_size=0.88,
                fill=COLOR_TEXT_MUTED,
            ),
            rio.Text(
                "Automated recurrence mapping, holiday settlement,",
                font_size=0.88,
                fill=COLOR_TEXT_MUTED,
            ),
            rio.Text(
                "and multi-year analytics — 100% private.",
                font_size=0.88,
                fill=COLOR_TEXT_MUTED,
            ),
            spacing=0.05,
            align_x=0.5,
        )

        # ── CTA Buttons ──
        cta_row = rio.Row(
            rio.Button(
                "Get Started Free",
                icon="material/person-add",
                shape="rounded",
                style="major",
                color="primary",
                min_height=2.4,
                on_press=self.on_open_signup,
            ),
            rio.Button(
                "Launch Demo",
                icon="material/bolt",
                shape="rounded",
                style="minor",
                color="secondary",
                min_height=2.4,
                on_press=self.on_quick_demo,
            ),
            spacing=0.4,
            align_x=0.5,
        )

        # ── Feature Pills ──
        features_strip = rio.Row(
            rio.Icon("material/history-toggle-off", fill=rio.Color.from_hex("#3B82F6"), min_width=1.0, min_height=1.0),
            rio.Text("Annual Recurrence", font_size=0.78, font_weight="bold"),
            rio.Text("•", font_size=0.8, fill=COLOR_TEXT_MUTED),
            rio.Icon("material/candlestick-chart", fill=rio.Color.from_hex("#8B5CF6"), min_width=1.0, min_height=1.0),
            rio.Text("Multi-Timeframe Charts", font_size=0.78, font_weight="bold"),
            rio.Text("•", font_size=0.8, fill=COLOR_TEXT_MUTED),
            rio.Icon("material/security", fill=rio.Color.from_hex("#10B981"), min_width=1.0, min_height=1.0),
            rio.Text("100% Offline & Private", font_size=0.78, font_weight="bold"),
            spacing=0.3,
            align_x=0.5,
            align_y=0.5,
        )

        # ── Privacy Footer ──
        privacy_line = rio.Text(
            "🔒  All data stored locally in SQLite  •  Zero cloud telemetry  •  Your data never leaves your machine",
            font_size=0.68,
            fill=COLOR_TEXT_MUTED,
            align_x=0.5,
        )

        # ── Hero content group ──
        hero_content = rio.Column(
            hero_badge,
            hero_title,
            hero_sub,
            cta_row,
            spacing=0.5,
            align_x=0.5,
        )

        # ── Bottom strip ──
        bottom_strip = rio.Column(
            features_strip,
            privacy_line,
            spacing=0.4,
            align_x=0.5,
            grow_x=True,
        )

        # ── Foreground content: hero centered with small top bias, bottom pinned ──
        foreground = rio.Column(
            rio.Spacer(),
            hero_content,
            rio.Spacer(),
            rio.Spacer(),
            bottom_strip,
            spacing=0.3,
            margin_x=1.5,
            margin_bottom=0.6,
            margin_top=3.5,
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
