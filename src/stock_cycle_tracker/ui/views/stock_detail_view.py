"""Stock Detail and Interactive Chart view component with dark terminal aesthetics, multi-cycle switcher, and mobile layout."""

from __future__ import annotations

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
    COLOR_TEXT_PRIMARY,
    COLOR_UP_STRONG,
    get_bucket_color,
    get_change_color,
)


class StockDetailView(rio.Component):
    """Detailed cycle breakdown and Plotly chart view for a selected stock with multi-cycle switching."""

    stock_symbol: str
    on_navigate: Callable[[str, Optional[str]], None]
    selected_cycle_index: int = 0
    overlay_all_cycles: bool = False

    def _select_cycle(self, index: int) -> None:
        self.selected_cycle_index = index
        self.overlay_all_cycles = False

    def _toggle_overlay_all(self) -> None:
        self.overlay_all_cycles = True

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 55.0
        container = ServiceContainer.get()
        detail = container.cycle_service.get_stock_detail(self.stock_symbol)

        if not detail or not detail.get("stock"):
            return rio.Column(
                rio.Button(
                    "Back to Dashboard",
                    icon="material/arrow-back",
                    shape="rounded",
                    style="major",
                    color="primary",
                    on_press=lambda: self.on_navigate("dashboard", None),
                ),
                rio.Text(f"Stock '{self.stock_symbol}' not found.", font_size=1.2, fill=COLOR_TEXT_MUTED),
                spacing=1.0,
                margin=1.5,
                grow_x=True,
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

        # Build Plotly chart with multi-cycle support & mobile vertical height
        fig = create_cycle_plotly_figure(
            symbol=stock.symbol,
            ohlc_bars=ohlc,
            analysis=active_analysis,
            all_analyses=analyses,
            overlay_all=self.overlay_all_cycles,
            is_mobile=is_mobile,
        )

        # Tight, non-stretching Exchange Badge
        exchange_badge = rio.Card(
            rio.Text(
                stock.preferred_exchange.value,
                font_size=0.72,
                font_weight="bold",
                fill=rio.Color.from_hex("#60A5FA"),
                margin_x=0.45,
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

        # Header Section
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
                        on_press=lambda: self.on_navigate("dashboard", None),
                    ),
                    rio.Spacer(),
                    rio.Row(
                        rio.Text(f"₹{current_price:,.2f}", font_size=1.3, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                        price_badge,
                        spacing=0.3,
                        align_y=0.5,
                        align_x=1.0,
                    ),
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Row(
                    rio.Text(stock.symbol, font_size=1.4, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                    exchange_badge,
                    spacing=0.3,
                    align_y=0.5,
                    align_x=0.0,
                    grow_x=False,
                ),
                rio.Text(f"{stock.company_name} — {len(cycles)} Cycle(s)", font_size=0.75, fill=COLOR_TEXT_MUTED),
                spacing=0.3,
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
                        rio.Text(stock.symbol, font_size=1.6, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
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
                            rio.Text(f"₹{current_price:,.2f}", font_size=1.5, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                            price_badge,
                            spacing=0.4,
                            align_y=0.5,
                        ),
                        spacing=0.05,
                        margin_x=0.8,
                        margin_y=0.3,
                    ),
                    corner_radius=0.4,
                    color="neutral",
                ),
                spacing=1.0,
                align_y=0.5,
                grow_x=True,
            )

        header_card = rio.Card(
            header_content,
            corner_radius=0.5,
            color="neutral",
            margin_x=0.6 if is_mobile else 1.2,
            margin_top=0.2,
            grow_x=True,
        )

        # Multi-Cycle Selection Switcher (when multiple cycles exist)
        cycle_switcher_card: Optional[rio.Component] = None
        if len(analyses) > 1:
            tab_buttons: list[rio.Component] = []
            for i, a in enumerate(analyses):
                is_selected = (not self.overlay_all_cycles) and (self.selected_cycle_index == i)
                tab_buttons.append(
                    rio.Button(
                        f"Cycle {a.cycle_number} ({a.original_reference_date.strftime('%d-%b-%Y')})",
                        shape="rounded",
                        style="major" if is_selected else "minor",
                        color="primary",
                        on_press=lambda idx=i: self._select_cycle(idx),
                    )
                )

            # Option to overlay all cycles simultaneously
            tab_buttons.append(
                rio.Button(
                    "✨ Overlay All Cycles",
                    shape="rounded",
                    style="major" if self.overlay_all_cycles else "minor",
                    color="secondary" if self.overlay_all_cycles else "primary",
                    on_press=self._toggle_overlay_all,
                )
            )

            cycle_switcher_card = rio.Card(
                rio.Column(
                    rio.Row(
                        rio.Icon("material/tune", fill=rio.Color.from_hex("#3B82F6"), min_width=1.2, min_height=1.2),
                        rio.Text("Select Active Cycle to View on Chart:", font_size=0.9, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                        spacing=0.4,
                        align_y=0.5,
                    ),
                    rio.FlowContainer(
                        *tab_buttons,
                        spacing=0.5,
                        row_spacing=0.4,
                        column_spacing=0.5,
                        justify="left",
                        grow_x=True,
                    ),
                    spacing=0.5,
                    margin=0.7,
                    grow_x=True,
                ),
                corner_radius=0.5,
                color="neutral",
                margin_x=0.6 if is_mobile else 1.2,
                grow_x=True,
            )

        # Highlight KPI Banner for active cycle
        kpi_banner: Optional[rio.Component] = None
        if active_analysis:
            chg_col = get_change_color(active_analysis.percentage_change)
            bkt_col = get_bucket_color(active_analysis.bucket)
            c_label = f"Cycle {active_analysis.cycle_number}" if not self.overlay_all_cycles else "Active Cycle Overview"

            card1 = rio.Card(
                rio.Column(
                    rio.Text(f"{c_label} Ref High", font_size=0.8, fill=COLOR_TEXT_MUTED),
                    rio.Text(f"₹{active_analysis.reference_high:,.2f}", font_size=1.3, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                    rio.Text(f"Anchor: {active_analysis.actual_reference_trading_date.strftime('%d-%b-%Y')}", font_size=0.75, fill=COLOR_TEXT_DIM),
                    spacing=0.08,
                    margin=0.6,
                ),
                corner_radius=0.4,
                color="neutral",
                grow_x=True,
            )
            card2 = rio.Card(
                rio.Column(
                    rio.Text("Percentage Change", font_size=0.8, fill=COLOR_TEXT_MUTED),
                    rio.Text(f"{active_analysis.percentage_change:+.2f}%", font_size=1.3, font_weight="bold", fill=chg_col),
                    rio.Text("vs Reference High", font_size=0.75, fill=COLOR_TEXT_DIM),
                    spacing=0.08,
                    margin=0.6,
                ),
                corner_radius=0.4,
                color="neutral",
                grow_x=True,
            )
            card3 = rio.Card(
                rio.Column(
                    rio.Text("Classification Bucket", font_size=0.8, fill=COLOR_TEXT_MUTED),
                    rio.Text(active_analysis.bucket, font_size=1.3, font_weight="bold", fill=bkt_col),
                    rio.Text(f"Window: {active_analysis.cycle_start_date.strftime('%d-%b')} → {active_analysis.cycle_end_date.strftime('%d-%b-%y')}", font_size=0.75, fill=COLOR_TEXT_DIM),
                    spacing=0.08,
                    margin=0.6,
                ),
                corner_radius=0.4,
                color="neutral",
                grow_x=True,
            )

            if is_mobile:
                kpi_banner = rio.Column(
                    card1,
                    card2,
                    card3,
                    spacing=0.4,
                    margin_x=0.6,
                    grow_x=True,
                )
            else:
                kpi_banner = rio.Row(
                    card1,
                    card2,
                    card3,
                    spacing=0.8,
                    margin_x=1.2,
                    grow_x=True,
                )

        # Plotly Chart Card
        chart_elements: list[rio.Component] = []
        if is_mobile:
            chart_elements.append(
                rio.Card(
                    rio.Row(
                        rio.Icon("material/screen-rotation", fill=rio.Color.from_hex("#3B82F6"), min_width=1.2, min_height=1.2),
                        rio.Text("Tip: Tilt phone to landscape for widescreen chart view", font_size=0.72, fill=COLOR_TEXT_MUTED),
                        spacing=0.3,
                        align_y=0.5,
                        margin_x=0.6,
                        margin_y=0.25,
                    ),
                    corner_radius=0.3,
                    color="hud",
                    margin_bottom=0.3,
                    grow_x=True,
                )
            )

        chart_elements.append(
            rio.Plot(
                fig,
                min_height=38.0 if is_mobile else 28.0,
                grow_x=True,
                grow_y=True,
                corner_radius=0.4,
            )
        )

        chart_card = rio.Card(
            rio.Column(
                *chart_elements,
                spacing=0.2,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            margin_x=0.6 if is_mobile else 1.2,
            grow_x=True,
        )

        # Configured Research Cycles Breakdown Section
        cycle_cards: list[rio.Component] = []
        cycle_cards.append(
            rio.Text(
                "Configured Research Cycles Breakdown",
                font_size=1.1 if is_mobile else 1.2,
                font_weight="bold",
                fill=COLOR_TEXT_PRIMARY,
                margin_x=0.6 if is_mobile else 1.2,
                margin_top=0.4,
            )
        )

        for i, a in enumerate(analyses):
            chg_col = get_change_color(a.percentage_change)
            bkt_col = get_bucket_color(a.bucket)
            is_active = (not self.overlay_all_cycles) and (self.selected_cycle_index == i)

            if is_mobile:
                card_content = rio.Column(
                    rio.Row(
                        rio.Text(f"Cycle {a.cycle_number}", font_size=1.0, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                        rio.Spacer(),
                        rio.Text(f"{a.percentage_change:+.2f}%", font_size=1.0, font_weight="bold", fill=chg_col),
                        align_y=0.5,
                        grow_x=True,
                    ),
                    rio.Row(
                        rio.Text(f"Ref Date: {a.original_reference_date.strftime('%d-%b-%Y')}", font_size=0.75, fill=COLOR_TEXT_MUTED),
                        rio.Spacer(),
                        rio.Text(f"Ref High: ₹{a.reference_high:,.2f}", font_size=0.8, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                        align_y=0.5,
                        grow_x=True,
                    ),
                    rio.Row(
                        rio.Card(
                            rio.Text(a.bucket, font_size=0.72, font_weight="bold", fill=bkt_col, margin_x=0.35, margin_y=0.1),
                            corner_radius=0.25,
                            color="hud",
                        ),
                        rio.Spacer(),
                        rio.Button(
                            "Viewing on Chart" if is_active else "View on Chart",
                            icon="material/show-chart",
                            shape="rounded",
                            style="major" if is_active else "minor",
                            color="primary",
                            on_press=lambda idx=i: self._select_cycle(idx),
                        ),
                        align_y=0.5,
                        grow_x=True,
                    ),
                    spacing=0.3,
                    margin=0.6,
                    grow_x=True,
                )
            else:
                card_content = rio.Row(
                    rio.Column(
                        rio.Row(
                            rio.Text(f"Cycle {a.cycle_number}", font_size=1.05, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                            rio.Card(
                                rio.Text("ACTIVE ON CHART", font_size=0.65, font_weight="bold", fill=COLOR_UP_STRONG, margin_x=0.35, margin_y=0.1),
                                corner_radius=0.2,
                                color="hud",
                            ) if is_active else rio.Spacer(),
                            spacing=0.4,
                            align_y=0.5,
                        ),
                        rio.Text(f"Original Date: {a.original_reference_date.strftime('%d-%b-%Y')}", font_size=0.75, fill=COLOR_TEXT_DIM),
                        spacing=0.05,
                    ),
                    rio.Column(
                        rio.Text(f"Recurrence: {a.recurring_reference_date.strftime('%d-%b')}", font_size=0.85, fill=COLOR_TEXT_MUTED),
                        rio.Text(f"Trading Day: {a.actual_reference_trading_date.strftime('%d-%b-%Y')}", font_size=0.75, fill=COLOR_TEXT_DIM),
                        spacing=0.05,
                    ),
                    rio.Column(
                        rio.Text(f"Ref High: ₹{a.reference_high:,.2f}", font_size=0.9, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                        rio.Text(f"Window: {a.cycle_start_date.strftime('%d-%b-%Y')} → {a.cycle_end_date.strftime('%d-%b-%Y')}", font_size=0.75, fill=COLOR_TEXT_DIM),
                        spacing=0.05,
                    ),
                    rio.Spacer(),
                    rio.Column(
                        rio.Text(f"{a.percentage_change:+.2f}%", font_size=1.15, font_weight="bold", fill=chg_col),
                        rio.Card(
                            rio.Text(a.bucket, font_size=0.75, font_weight="bold", fill=bkt_col, margin_x=0.4, margin_y=0.15),
                            corner_radius=0.25,
                            color="hud",
                        ),
                        spacing=0.1,
                        align_x=1.0,
                    ),
                    rio.Button(
                        "Active on Chart" if is_active else "Switch to This Cycle",
                        icon="material/show-chart",
                        shape="rounded",
                        style="major" if is_active else "minor",
                        color="primary",
                        on_press=lambda idx=i: self._select_cycle(idx),
                    ),
                    spacing=0.8,
                    align_y=0.5,
                    margin_x=0.8,
                    margin_y=0.4,
                    grow_x=True,
                )

            cycle_cards.append(
                rio.Card(
                    card_content,
                    corner_radius=0.4,
                    color="hud" if is_active else "neutral",
                    margin_x=0.6 if is_mobile else 1.2,
                    grow_x=True,
                )
            )

        components = [header_card]
        if cycle_switcher_card:
            components.append(cycle_switcher_card)
        if kpi_banner:
            components.append(kpi_banner)
        components.append(chart_card)
        components.extend(cycle_cards)

        return rio.Column(
            *components,
            spacing=0.6,
            grow_x=True,
            margin_bottom=1.5,
        )
