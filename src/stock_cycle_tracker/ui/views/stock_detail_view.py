"""Enhanced Stock Detail view component supporting multi-cycle tab switching, full cycle overlays, and adaptive light/dark theme."""

from __future__ import annotations

from datetime import date
from typing import Callable, List, Optional

import rio

from stock_cycle_tracker.domain.models import CycleAnalysis, PriceType
from stock_cycle_tracker.ui.components.chart import create_cycle_plotly_figure
from stock_cycle_tracker.ui.state import ServiceContainer
from stock_cycle_tracker.ui.theme import (
    COLOR_BORDER,
    COLOR_DOWN_STRONG,
    COLOR_SURFACE_CARD,
    COLOR_TEXT_DIM,
    COLOR_TEXT_MUTED,
    COLOR_UP_STRONG,
    get_bucket_color,
    get_change_color,
)


class StockDetailView(rio.Component):
    """Detailed cycle inspection for a single stock with interactive chart and multi-cycle tabs."""

    stock_symbol: str
    on_navigate: Callable[[str, Optional[str]], None]
    selected_cycle_index: int = 0
    overlay_all_cycles: bool = False
    selected_timeframe: str = "1Yr"
    show_price: bool = True
    show_50_dma: bool = True
    show_200_dma: bool = True
    show_volume: bool = True
    show_cycle_anchors: bool = True

    def _select_cycle(self, index: int) -> None:
        self.selected_cycle_index = index
        self.overlay_all_cycles = False

    def _toggle_overlay_all(self) -> None:
        self.overlay_all_cycles = not self.overlay_all_cycles

    def _set_timeframe(self, tf: str) -> None:
        self.selected_timeframe = tf

    def _toggle_price(self) -> None:
        self.show_price = not self.show_price

    def _toggle_50_dma(self) -> None:
        self.show_50_dma = not self.show_50_dma

    def _toggle_200_dma(self) -> None:
        self.show_200_dma = not self.show_200_dma

    def _toggle_volume(self) -> None:
        self.show_volume = not self.show_volume

    def _toggle_cycle_anchors(self) -> None:
        self.show_cycle_anchors = not self.show_cycle_anchors

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 55.0
        is_portrait = self.session.window_height > self.session.window_width
        is_dark_mode = not getattr(self.session.theme, "is_light_theme", False)

        # Map selected timeframe to lookback days
        timeframe_days_map = {
            "1M": 30,
            "6M": 180,
            "1Yr": 365,
            "3Yr": 1095,
            "5Yr": 1825,
            "10Yr": 3650,
            "Max": 7300,
        }
        lookback_days = timeframe_days_map.get(self.selected_timeframe, 365)

        container = ServiceContainer.get()
        detail = container.cycle_service.get_stock_detail(self.stock_symbol, lookback_days=lookback_days)

        if not detail:
            return rio.Column(
                rio.Button(
                    "Back to Dashboard",
                    icon="material/arrow-back",
                    shape="rounded",
                    style="minor",
                    color="primary",
                    on_press=lambda: self.on_navigate("dashboard", None),
                ),
                rio.Text(f"Stock '{self.stock_symbol}' not found.", font_size=1.2, fill=COLOR_DOWN_STRONG),
                spacing=1.0,
                margin=1.0,
            )

        stock = detail["stock"]
        cycles = detail.get("cycles", [])
        analyses: List[CycleAnalysis] = detail.get("analyses", [])
        ohlc = detail.get("ohlc", [])
        current_price = detail.get("current_price", 0.0)
        price_type = detail.get("price_type", PriceType.CLOSE)

        # Validate selected cycle index
        if analyses:
            if self.selected_cycle_index >= len(analyses):
                self.selected_cycle_index = 0
            active_analysis = analyses[self.selected_cycle_index]
        else:
            active_analysis = None

        # Build Plotly chart with multi-cycle support & adaptive vertical height & theme gridlines
        fig = create_cycle_plotly_figure(
            symbol=stock.symbol,
            ohlc_bars=ohlc,
            analysis=active_analysis,
            all_analyses=analyses,
            overlay_all=self.overlay_all_cycles,
            show_price=self.show_price,
            show_50_dma=self.show_50_dma,
            show_200_dma=self.show_200_dma,
            show_volume=self.show_volume,
            show_cycle_anchors=self.show_cycle_anchors,
            timeframe_label=self.selected_timeframe,
            is_mobile=is_mobile,
            is_portrait=is_portrait,
            is_dark_mode=is_dark_mode,
        )

        # Tight, non-stretching Exchange Badge
        exchange_badge = rio.Card(
            rio.Text(
                stock.preferred_exchange.value,
                font_size=0.72,
                font_weight="bold",
                fill=rio.Color.from_hex("#60A5FA"),
                margin_x=0.4,
                margin_y=0.1,
            ),
            corner_radius=0.3,
            color="hud",
            grow_x=False,
            grow_y=False,
            align_x=0.0,
            align_y=0.5,
        )

        # Price Badge
        price_badge = rio.Card(
            rio.Text(
                price_type.value,
                font_size=0.7,
                font_weight="bold",
                fill=COLOR_UP_STRONG if price_type == PriceType.LIVE else COLOR_TEXT_MUTED,
                margin_x=0.4,
                margin_y=0.1,
            ),
            corner_radius=0.25,
            color="hud",
            grow_x=False,
            grow_y=False,
            align_x=0.0,
            align_y=0.5,
        )

        # Header Section (Adaptive light/dark text colors)
        header_content: rio.Component
        if is_mobile:
            header_content = rio.Column(
                rio.Row(
                    rio.Button(
                        "Back",
                        icon="material/arrow-back",
                        shape="rounded",
                        style="minor",
                        color="primary",
                        min_height=2.0,
                        on_press=lambda: self.on_navigate("dashboard", None),
                    ),
                    rio.Spacer(),
                    rio.Row(
                        rio.Text(f"₹{current_price:,.2f}", font_size=1.2, font_weight="bold"),
                        price_badge,
                        spacing=0.25,
                        align_y=0.5,
                        align_x=1.0,
                        grow_x=False,
                    ),
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Row(
                    rio.Text(stock.symbol, font_size=1.3, font_weight="bold"),
                    exchange_badge,
                    spacing=0.3,
                    align_y=0.5,
                    align_x=0.0,
                    grow_x=False,
                ),
                rio.Text(f"{stock.company_name} — {len(cycles)} Cycle(s)", font_size=0.75, fill=COLOR_TEXT_MUTED),
                spacing=0.25,
                grow_x=True,
            )
        else:
            header_content = rio.Row(
                rio.Button(
                    "Back to Dashboard",
                    icon="material/arrow-back",
                    shape="rounded",
                    style="major",
                    color="primary",
                    on_press=lambda: self.on_navigate("dashboard", None),
                ),
                rio.Column(
                    rio.Row(
                        rio.Text(stock.symbol, font_size=1.6, font_weight="bold"),
                        exchange_badge,
                        spacing=0.4,
                        align_y=0.5,
                        align_x=0.0,
                        grow_x=False,
                    ),
                    rio.Text(f"{stock.company_name} — {len(cycles)} Research Cycle(s) Tracked", font_size=0.85, fill=COLOR_TEXT_MUTED),
                    spacing=0.05,
                    align_x=0.0,
                ),
                rio.Spacer(),
                rio.Card(
                    rio.Column(
                        rio.Text("Current Market Price", font_size=0.75, fill=COLOR_TEXT_MUTED),
                        rio.Row(
                            rio.Text(f"₹{current_price:,.2f}", font_size=1.5, font_weight="bold"),
                            price_badge,
                            spacing=0.4,
                            align_y=0.5,
                        ),
                        spacing=0.05,
                        margin_x=0.8,
                        margin_y=0.3,
                    ),
                    corner_radius=0.4,
                    color="hud",
                ),
                spacing=1.0,
                align_y=0.5,
                grow_x=True,
            )

        header_card = rio.Card(
            header_content,
            corner_radius=0.5,
            color="neutral",
            margin_x=0.4 if is_mobile else 1.2,
            margin_top=0.2,
            grow_x=True,
        )

        # Multi-Cycle Selection Switcher (when multiple cycles exist)
        cycle_switcher_card: Optional[rio.Component] = None
        if len(analyses) > 1:
            tab_buttons: list[rio.Component] = []
            for i, a in enumerate(analyses):
                is_sel = (i == self.selected_cycle_index) and not self.overlay_all_cycles
                tab_buttons.append(
                    rio.Button(
                        f"Cycle {a.cycle_number} ({a.original_reference_date.strftime('%d-%b-%Y')})",
                        icon="material/history-toggle-off" if is_sel else "material/timeline",
                        shape="rounded",
                        style="major" if is_sel else "minor",
                        color="primary" if is_sel else "neutral",
                        min_height=2.2 if is_mobile else 2.5,
                        grow_x=is_mobile,
                        on_press=lambda idx=i: self._select_cycle(idx),
                    )
                )

            tab_buttons.append(
                rio.Button(
                    "Compare All Cycles",
                    icon="material/stacked-line-chart",
                    shape="rounded",
                    style="major" if self.overlay_all_cycles else "minor",
                    color="success" if self.overlay_all_cycles else "neutral",
                    min_height=2.2 if is_mobile else 2.5,
                    grow_x=is_mobile,
                    on_press=self._toggle_overlay_all,
                )
            )

            cycle_switcher_card = rio.Card(
                rio.Column(
                    rio.Row(
                        rio.Icon("material/layers", fill=rio.Color.from_hex("#3B82F6"), min_width=1.2, min_height=1.2),
                        rio.Text(
                            f"Multiple Research Cycles Detected ({len(analyses)} cycles registered)",
                            font_weight="bold",
                            font_size=0.88 if is_mobile else 0.95,
                        ),
                        spacing=0.3,
                        align_y=0.5,
                    ),
                    rio.FlowContainer(
                        *tab_buttons,
                        spacing=0.4,
                        row_spacing=0.3,
                        column_spacing=0.4,
                        justify="left",
                        align_y=0.5,
                        grow_x=True,
                    ),
                    spacing=0.4,
                    margin_x=0.6 if is_mobile else 0.8,
                    margin_y=0.4 if is_mobile else 0.6,
                    grow_x=True,
                ),
                corner_radius=0.4,
                color="hud",
                margin_x=0.4 if is_mobile else 1.2,
                grow_x=True,
            )

        # Selected Cycle KPI Cards
        stats_cards: list[rio.Component] = []
        if active_analysis:
            chg_col = get_change_color(active_analysis.percentage_change)
            bucket_col = get_bucket_color(active_analysis.bucket)

            stats_cards = [
                rio.Card(
                    rio.Column(
                        rio.Text(f"Cycle {active_analysis.cycle_number} Ref High / Low", font_size=0.75, fill=COLOR_TEXT_MUTED),
                        rio.Row(
                            rio.Text(f"H: ₹{active_analysis.reference_high:,.2f}", font_size=1.1 if is_mobile else 1.3, font_weight="bold"),
                            rio.Text(f"L: ₹{active_analysis.reference_low:,.2f}", font_size=1.1 if is_mobile else 1.3, fill=COLOR_TEXT_MUTED),
                            spacing=0.4,
                            align_y=0.5,
                        ),
                        rio.Text(f"Anchor: {active_analysis.actual_reference_trading_date.strftime('%d-%b-%Y')}", font_size=0.7, fill=COLOR_TEXT_DIM),
                        spacing=0.04,
                        margin=0.5 if is_mobile else 0.7,
                    ),
                    corner_radius=0.4,
                    color="neutral",
                    grow_x=True,
                ),
                rio.Card(
                    rio.Column(
                        rio.Text("Percentage Change", font_size=0.75, fill=COLOR_TEXT_MUTED),
                        rio.Text(f"{active_analysis.percentage_change:+.2f}%", font_size=1.3 if is_mobile else 1.6, font_weight="bold", fill=chg_col),
                        rio.Text("vs Reference High", font_size=0.7, fill=COLOR_TEXT_DIM),
                        spacing=0.04,
                        margin=0.5 if is_mobile else 0.7,
                    ),
                    corner_radius=0.4,
                    color="neutral",
                    grow_x=True,
                ),
                rio.Card(
                    rio.Column(
                        rio.Text("Classification Bucket", font_size=0.75, fill=COLOR_TEXT_MUTED),
                        rio.Text(active_analysis.bucket, font_size=1.1 if is_mobile else 1.3, font_weight="bold", fill=bucket_col),
                        rio.Text(
                            f"Window: {active_analysis.cycle_start_date.strftime('%d-%b')} → {active_analysis.cycle_end_date.strftime('%d-%b-%y')}",
                            font_size=0.7,
                            fill=COLOR_TEXT_DIM,
                        ),
                        spacing=0.04,
                        margin=0.5 if is_mobile else 0.7,
                    ),
                    corner_radius=0.4,
                    color="neutral",
                    grow_x=True,
                ),
            ]

        stats_layout: rio.Component
        if is_mobile:
            stats_layout = rio.Column(
                *stats_cards,
                spacing=0.3,
                margin_x=0.4,
                grow_x=True,
            )
        else:
            stats_layout = rio.Row(
                *stats_cards,
                spacing=0.8,
                margin_x=1.2,
                grow_x=True,
            )

        # Screener-style Timeframe & Indicator Controls Toolbar
        timeframe_buttons = []
        for tf in ["1M", "6M", "1Yr", "3Yr", "5Yr", "10Yr", "Max"]:
            is_active_tf = self.selected_timeframe == tf
            timeframe_buttons.append(
                rio.Button(
                    tf,
                    shape="rounded",
                    style="major" if is_active_tf else "plain-text",
                    color="primary" if is_active_tf else "neutral",
                    min_height=1.8,
                    min_width=2.2 if is_mobile else 2.8,
                    on_press=lambda t=tf: self._set_timeframe(t),
                )
            )

        timeframe_bar = rio.Card(
            rio.Row(
                *timeframe_buttons,
                spacing=0.15,
                align_y=0.5,
                margin_x=0.2,
                margin_y=0.1,
            ),
            corner_radius=0.35,
            color="hud",
            grow_x=False,
        )

        indicator_toggles = [
            rio.Button(
                "Price",
                icon="material/show-chart",
                shape="rounded",
                style="minor" if self.show_price else "plain-text",
                color="primary" if self.show_price else "neutral",
                min_height=1.8,
                on_press=self._toggle_price,
            ),
            rio.Button(
                "50 DMA",
                icon="material/timeline",
                shape="rounded",
                style="minor" if self.show_50_dma else "plain-text",
                color="warning" if self.show_50_dma else "neutral",
                min_height=1.8,
                on_press=self._toggle_50_dma,
            ),
            rio.Button(
                "200 DMA",
                icon="material/trending-up",
                shape="rounded",
                style="minor" if self.show_200_dma else "plain-text",
                color="secondary" if self.show_200_dma else "neutral",
                min_height=1.8,
                on_press=self._toggle_200_dma,
            ),
            rio.Button(
                "Volume",
                icon="material/bar-chart",
                shape="rounded",
                style="minor" if self.show_volume else "plain-text",
                color="primary" if self.show_volume else "neutral",
                min_height=1.8,
                on_press=self._toggle_volume,
            ),
            rio.Button(
                "Cycle Anchors",
                icon="material/anchor",
                shape="rounded",
                style="minor" if self.show_cycle_anchors else "plain-text",
                color="success" if self.show_cycle_anchors else "neutral",
                min_height=1.8,
                on_press=self._toggle_cycle_anchors,
            ),
        ]

        if is_mobile:
            chart_toolbar = rio.Column(
                timeframe_bar,
                rio.Row(
                    *indicator_toggles,
                    spacing=0.2,
                    align_y=0.5,
                    grow_x=True,
                ),
                spacing=0.3,
                margin_x=0.4,
                margin_y=0.25,
                grow_x=True,
            )
        else:
            chart_toolbar = rio.Row(
                timeframe_bar,
                rio.Spacer(),
                rio.Row(
                    *indicator_toggles,
                    spacing=0.25,
                    align_y=0.5,
                ),
                spacing=0.6,
                align_y=0.5,
                margin_x=0.8,
                margin_top=0.35,
                margin_bottom=0.15,
                grow_x=True,
            )

        # Plotly Chart Card
        chart_card = rio.Card(
            rio.Column(
                chart_toolbar,
                rio.Plot(
                    fig,
                    min_height=28.0 if not is_mobile else (36.0 if is_portrait else 22.0),
                    grow_x=True,
                ),
                spacing=0.2,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            margin_x=0.4 if is_mobile else 1.2,
            grow_x=True,
        )

        # Cycles Breakdown Table
        breakdown_rows: list[rio.Component] = []
        breakdown_rows.append(
            rio.Text(
                "Configured Research Cycles Breakdown",
                font_size=1.1 if is_mobile else 1.3,
                font_weight="bold",
                margin_x=0.4 if is_mobile else 1.2,
                margin_top=0.4,
            )
        )

        for a in analyses:
            is_active_row = a.cycle_number == (active_analysis.cycle_number if active_analysis else 1)
            chg_c = get_change_color(a.percentage_change)
            bk_c = get_bucket_color(a.bucket)

            cycle_chip = rio.Card(
                rio.Text(f"Cycle {a.cycle_number}", font_size=0.78, font_weight="bold", fill=rio.Color.from_hex("#60A5FA"), margin_x=0.4, margin_y=0.15),
                corner_radius=0.25,
                color="hud",
                grow_x=False,
                grow_y=False,
                align_x=0.0,
                align_y=0.5,
            )

            if is_mobile:
                row_content = rio.Column(
                    rio.Row(
                        cycle_chip,
                        rio.Spacer(),
                        rio.Text(f"{a.percentage_change:+.2f}%", font_weight="bold", font_size=1.05, fill=chg_c),
                        align_y=0.5,
                        grow_x=True,
                    ),
                    rio.Row(
                        rio.Text(f"Research Date: {a.original_reference_date.strftime('%d-%b-%Y')}", font_size=0.75, fill=COLOR_TEXT_MUTED),
                        rio.Spacer(),
                        rio.Text(f"Trading Date: {a.actual_reference_trading_date.strftime('%d-%b-%Y')}", font_size=0.75, fill=COLOR_TEXT_DIM),
                        align_y=0.5,
                        grow_x=True,
                    ),
                    rio.Row(
                        rio.Text(f"Ref High: ₹{a.reference_high:,.2f} | Low: ₹{a.reference_low:,.2f}", font_size=0.75, font_weight="bold"),
                        rio.Spacer(),
                        rio.Card(
                            rio.Text(a.bucket, font_size=0.7, font_weight="bold", fill=bk_c, margin_x=0.35, margin_y=0.1),
                            corner_radius=0.2,
                            color="hud",
                        ),
                        align_y=0.5,
                        grow_x=True,
                    ),
                    spacing=0.2,
                    margin=0.5,
                    grow_x=True,
                )
            else:
                row_content = rio.Row(
                    cycle_chip,
                    rio.Column(
                        rio.Text("Research Date", font_size=0.7, fill=COLOR_TEXT_DIM),
                        rio.Text(a.original_reference_date.strftime("%d-%b-%Y"), font_size=0.88, font_weight="bold"),
                        spacing=0.02,
                        grow_x=True,
                    ),
                    rio.Column(
                        rio.Text("Trading Date", font_size=0.7, fill=COLOR_TEXT_DIM),
                        rio.Text(a.actual_reference_trading_date.strftime("%d-%b-%Y"), font_size=0.88),
                        spacing=0.02,
                        grow_x=True,
                    ),
                    rio.Column(
                        rio.Text("Ref High", font_size=0.7, fill=COLOR_TEXT_DIM),
                        rio.Text(f"₹{a.reference_high:,.2f}", font_size=0.88, font_weight="bold"),
                        spacing=0.02,
                        grow_x=True,
                    ),
                    rio.Column(
                        rio.Text("Ref Low", font_size=0.7, fill=COLOR_TEXT_DIM),
                        rio.Text(f"₹{a.reference_low:,.2f}", font_size=0.88, fill=COLOR_TEXT_MUTED),
                        spacing=0.02,
                        grow_x=True,
                    ),
                    rio.Column(
                        rio.Text("% Change", font_size=0.7, fill=COLOR_TEXT_DIM),
                        rio.Text(f"{a.percentage_change:+.2f}%", font_size=0.92, font_weight="bold", fill=chg_c),
                        spacing=0.02,
                        grow_x=True,
                    ),
                    rio.Card(
                        rio.Text(a.bucket, font_size=0.75, font_weight="bold", fill=bk_c, margin_x=0.35, margin_y=0.12),
                        corner_radius=0.25,
                        color="hud",
                    ),
                    rio.Spacer(),
                    rio.Button(
                        "Inspect",
                        icon="material/show-chart",
                        shape="rounded",
                        style="major" if is_active_row else "minor",
                        color="primary" if is_active_row else "neutral",
                        min_height=2.0,
                        on_press=lambda idx=analyses.index(a): self._select_cycle(idx),
                    ),
                    spacing=0.4,
                    align_y=0.5,
                    margin_x=0.6,
                    margin_y=0.25,
                    grow_x=True,
                )

            breakdown_rows.append(
                rio.Card(
                    row_content,
                    corner_radius=0.4,
                    color="hud" if is_active_row else "neutral",
                    margin_x=0.4 if is_mobile else 1.2,
                    grow_x=True,
                )
            )

        return rio.Column(
            header_card,
            cycle_switcher_card if cycle_switcher_card else rio.Spacer(),
            stats_layout,
            chart_card,
            *breakdown_rows,
            spacing=0.6 if is_mobile else 0.8,
            grow_x=True,
            margin_bottom=1.5,
        )
