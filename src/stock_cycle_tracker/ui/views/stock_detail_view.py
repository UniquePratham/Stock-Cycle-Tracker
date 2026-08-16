"""Stock Detail and Interactive Chart view component with dark terminal aesthetics and responsive layout."""

from __future__ import annotations

from typing import Callable, Optional

import rio

from stock_cycle_tracker.domain.models import PriceType
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
    """Detailed cycle breakdown and Plotly chart view for a selected stock."""

    stock_symbol: str
    on_navigate: Callable[[str, Optional[str]], None]

    def build(self) -> rio.Component:
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
        analyses = detail.get("analyses", [])
        ohlc = detail.get("ohlc", [])
        current_price = detail.get("current_price", 0.0)
        price_type = detail.get("price_type", PriceType.CLOSE)

        # Primary analysis for chart reference
        primary_analysis = analyses[0] if analyses else None

        # Build Plotly chart
        fig = create_cycle_plotly_figure(
            symbol=stock.symbol,
            ohlc_bars=ohlc,
            analysis=primary_analysis,
        )

        # Top Navigation & Stock Header — responsive FlowContainer
        header = rio.FlowContainer(
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
                    rio.Card(
                        rio.Text(
                            stock.preferred_exchange.value,
                            font_size=0.75,
                            font_weight="bold",
                            fill=rio.Color.from_hex("#3B82F6"),
                            margin_x=0.4,
                            margin_y=0.15,
                        ),
                        corner_radius=0.25,
                        color="hud",
                        align_y=0.5,
                    ),
                    spacing=0.4,
                    align_y=0.5,
                ),
                rio.Text(f"{stock.company_name} — {len(cycles)} Research Cycle(s) Tracked", font_size=0.85, fill=COLOR_TEXT_MUTED),
                spacing=0.05,
            ),
            rio.Card(
                rio.Column(
                    rio.Text("Current Market Price", font_size=0.75, fill=COLOR_TEXT_MUTED),
                    rio.Row(
                        rio.Text(f"₹{current_price:,.2f}", font_size=1.5, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                        rio.Card(
                            rio.Text(
                                price_type.value,
                                font_size=0.7,
                                font_weight="bold",
                                fill=COLOR_UP_STRONG if price_type == PriceType.LIVE else COLOR_TEXT_MUTED,
                                margin_x=0.4,
                                margin_y=0.15,
                            ),
                            corner_radius=0.25,
                            color="hud",
                            align_y=0.5,
                        ),
                        spacing=0.4,
                        align_y=0.5,
                    ),
                    spacing=0.05,
                    margin_x=0.9,
                    margin_y=0.4,
                ),
                corner_radius=0.4,
                color="neutral",
            ),
            spacing=1.0,
            row_spacing=0.5,
            column_spacing=1.0,
            justify="justify",
            align_y=0.5,
            margin_x=1.2,
            margin_top=0.2,
            grow_x=True,
        )

        # Highlight KPI Banner — responsive FlowContainer
        kpi_banner: Optional[rio.Component] = None
        if primary_analysis:
            chg_col = get_change_color(primary_analysis.percentage_change)
            bkt_col = get_bucket_color(primary_analysis.bucket)
            kpi_banner = rio.FlowContainer(
                rio.Card(
                    rio.Column(
                        rio.Text("Cycle 1 Reference High", font_size=0.8, fill=COLOR_TEXT_MUTED),
                        rio.Text(f"₹{primary_analysis.reference_high:,.2f}", font_size=1.3, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                        rio.Text(f"Anchored to {primary_analysis.actual_reference_trading_date.strftime('%d-%b-%Y')}", font_size=0.72, fill=COLOR_TEXT_DIM),
                        spacing=0.1,
                        margin=0.6,
                    ),
                    corner_radius=0.4,
                    color="neutral",
                    min_width=16.0,
                    grow_x=True,
                ),
                rio.Card(
                    rio.Column(
                        rio.Text("Percentage Change", font_size=0.8, fill=COLOR_TEXT_MUTED),
                        rio.Text(f"{primary_analysis.percentage_change:+.2f}%", font_size=1.3, font_weight="bold", fill=chg_col),
                        rio.Text("Relative to Reference High", font_size=0.72, fill=COLOR_TEXT_DIM),
                        spacing=0.1,
                        margin=0.6,
                    ),
                    corner_radius=0.4,
                    color="neutral",
                    min_width=16.0,
                    grow_x=True,
                ),
                rio.Card(
                    rio.Column(
                        rio.Text("Current Classification", font_size=0.8, fill=COLOR_TEXT_MUTED),
                        rio.Text(primary_analysis.bucket, font_size=1.3, font_weight="bold", fill=bkt_col),
                        rio.Text(f"Cycle: {primary_analysis.cycle_start_date.strftime('%d-%b-%Y')} → {primary_analysis.cycle_end_date.strftime('%d-%b-%Y')}", font_size=0.72, fill=COLOR_TEXT_DIM),
                        spacing=0.1,
                        margin=0.6,
                    ),
                    corner_radius=0.4,
                    color="neutral",
                    min_width=16.0,
                    grow_x=True,
                ),
                spacing=0.8,
                row_spacing=0.6,
                column_spacing=0.8,
                justify="justify",
                margin_x=1.2,
                grow_x=True,
            )

        # Plotly Chart — NO align_x, with grow_x on everything
        chart_card = rio.Card(
            rio.Plot(
                fig,
                min_height=28.0,
                grow_x=True,
                grow_y=True,
                corner_radius=0.4,
            ),
            corner_radius=0.5,
            color="neutral",
            margin_x=1.2,
            grow_x=True,
        )

        # Cycle breakdown list — responsive FlowContainer per cycle
        cycle_cards: list[rio.Component] = []
        cycle_cards.append(
            rio.Text(
                "Configured Research Cycles Breakdown",
                font_size=1.2,
                font_weight="bold",
                fill=COLOR_TEXT_PRIMARY,
                margin_x=1.2,
                margin_top=0.4,
            )
        )

        for a in analyses:
            chg_col = get_change_color(a.percentage_change)
            bkt_col = get_bucket_color(a.bucket)
            cycle_cards.append(
                rio.Card(
                    rio.FlowContainer(
                        rio.Column(
                            rio.Text(f"Cycle {a.cycle_number}", font_size=1.0, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
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
                        rio.Column(
                            rio.Text(f"{a.percentage_change:+.2f}%", font_size=1.2, font_weight="bold", fill=chg_col),
                            rio.Card(
                                rio.Text(a.bucket, font_size=0.75, font_weight="bold", fill=bkt_col, margin_x=0.4, margin_y=0.15),
                                corner_radius=0.25,
                                color="hud",
                            ),
                            spacing=0.1,
                        ),
                        spacing=1.0,
                        row_spacing=0.4,
                        column_spacing=1.0,
                        justify="justify",
                        align_y=0.5,
                        margin_x=0.8,
                        margin_y=0.4,
                        grow_x=True,
                    ),
                    corner_radius=0.4,
                    color="neutral",
                    margin_x=1.2,
                    grow_x=True,
                )
            )

        components = [header]
        if kpi_banner:
            components.append(kpi_banner)
        components.append(chart_card)
        components.extend(cycle_cards)

        return rio.Column(
            *components,
            spacing=0.8,
            grow_x=True,
            margin_bottom=1.5,
        )
