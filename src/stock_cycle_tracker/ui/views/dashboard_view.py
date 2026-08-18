"""Polished, modern Dashboard view component with zero horizontal scrollbar and clean Upside/Downside bucket filter."""

from __future__ import annotations

from datetime import date
from typing import Callable, List, Optional

import rio

from stock_cycle_tracker.domain.models import CycleAnalysis, PriceType
from stock_cycle_tracker.ui.state import ServiceContainer
from stock_cycle_tracker.ui.theme import (
    COLOR_BORDER,
    COLOR_DOWN_STRONG,
    COLOR_SURFACE_CARD,
    COLOR_SURFACE_HOVER,
    COLOR_TEXT_DIM,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_UP_STRONG,
    get_bucket_color,
    get_change_color,
)


class DashboardView(rio.Component):
    """Main Cycle Analysis Dashboard with zero horizontal scrollbar on PC and zero-scroll mobile cards."""

    on_navigate: Callable[[str, Optional[str]], None]
    search_query: str = ""
    bucket_filter: str = "ALL"
    exchange_filter: str = "ALL"
    is_refreshing: bool = False
    status_message: str = ""

    def _get_analyses(self) -> List[CycleAnalysis]:
        container = ServiceContainer.get()
        analyses = container.cycle_service.get_dashboard_analyses(force_refresh=self.is_refreshing)

        # Apply search filter
        if self.search_query.strip():
            q = self.search_query.strip().upper()
            analyses = [a for a in analyses if q in a.stock_symbol.upper() or q in a.company_name.upper()]

        # Apply bucket filter
        if self.bucket_filter != "ALL":
            if self.bucket_filter == "UPSIDE":
                analyses = [a for a in analyses if "upside" in a.bucket.lower()]
            elif self.bucket_filter == "DOWNSIDE":
                analyses = [a for a in analyses if "downside" in a.bucket.lower()]

        # Apply exchange filter
        if self.exchange_filter != "ALL":
            analyses = [a for a in analyses if a.exchange == self.exchange_filter]

        return analyses

    async def _on_refresh(self) -> None:
        self.is_refreshing = True
        self.status_message = "Updating market prices..."
        await self.force_refresh()
        container = ServiceContainer.get()
        container.cycle_service.get_dashboard_analyses(force_refresh=True)
        self.is_refreshing = False
        self.status_message = "Market data successfully refreshed."
        await self.force_refresh()

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 55.0
        container = ServiceContainer.get()
        market_status = container.provider.get_market_status()
        analyses = self._get_analyses()

        total_stocks = len(set(a.stock_symbol for a in analyses))
        total_cycles = len(analyses)
        upside_count = sum(1 for a in analyses if "upside" in a.bucket.lower())
        downside_count = sum(1 for a in analyses if "downside" in a.bucket.lower())

        # Header Title Bar
        header_content: rio.Component
        if is_mobile:
            header_content = rio.Column(
                rio.Row(
                    rio.Text("Cycle Analytics", font_size=1.3, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                    rio.Spacer(),
                    rio.Card(
                        rio.Row(
                            rio.Icon(
                                "material/fiber-manual-record",
                                fill=COLOR_UP_STRONG if market_status.value == "OPEN" else COLOR_TEXT_DIM,
                                min_width=0.8,
                                min_height=0.8,
                            ),
                            rio.Text(
                                market_status.value,
                                font_size=0.7,
                                font_weight="bold",
                                fill=COLOR_UP_STRONG if market_status.value == "OPEN" else COLOR_TEXT_MUTED,
                            ),
                            spacing=0.2,
                            align_y=0.5,
                            margin_x=0.4,
                            margin_y=0.1,
                        ),
                        corner_radius=0.3,
                        color="hud",
                    ),
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Text(
                    "Annual research-date cycle benchmark vs Ref High",
                    font_size=0.75,
                    fill=COLOR_TEXT_MUTED,
                ),
                spacing=0.08,
                margin_x=0.4,
                margin_top=0.2,
                grow_x=True,
            )
        else:
            header_content = rio.Row(
                rio.Column(
                    rio.Text(
                        "Cycle Overview & Analytics",
                        font_size=1.8,
                        font_weight="bold",
                        fill=COLOR_TEXT_PRIMARY,
                    ),
                    rio.Text(
                        "Annual research-date cycle boundaries benchmarked against historical reference High",
                        font_size=0.95,
                        fill=COLOR_TEXT_MUTED,
                    ),
                    spacing=0.08,
                    align_x=0.0,
                ),
                rio.Spacer(),
                rio.Card(
                    rio.Row(
                        rio.Icon(
                            "material/fiber-manual-record",
                            fill=COLOR_UP_STRONG if market_status.value == "OPEN" else COLOR_TEXT_DIM,
                            min_width=1.3,
                            min_height=1.3,
                        ),
                        rio.Text(
                            f"MARKET {market_status.value} (09:15–15:30 IST)" if market_status.value == "OPEN" else "MARKET CLOSED (PREV CLOSE)",
                            font_size=0.85,
                            font_weight="bold",
                            fill=COLOR_UP_STRONG if market_status.value == "OPEN" else COLOR_TEXT_MUTED,
                        ),
                        spacing=0.4,
                        align_y=0.5,
                        margin_x=0.8,
                        margin_y=0.35,
                    ),
                    corner_radius=0.4,
                    color="hud",
                ),
                spacing=1.0,
                align_y=0.5,
                margin_x=1.2,
                margin_top=0.2,
                grow_x=True,
            )

        # KPI Metric Cards
        metric_cards: list[rio.Component] = [
            # Card 1: Tracked Stocks
            rio.Card(
                rio.Column(
                    rio.Row(
                        rio.Text("Tracked Stocks", font_size=0.85 if is_mobile else 0.95, font_weight="bold", fill=COLOR_TEXT_MUTED),
                        rio.Spacer(),
                        rio.Icon("material/domain", fill=rio.Color.from_hex("#3B82F6"), min_width=1.3 if is_mobile else 1.6, min_height=1.3 if is_mobile else 1.6),
                        align_y=0.5,
                    ),
                    rio.Text(str(total_stocks), font_size=1.6 if is_mobile else 2.1, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                    spacing=0.08,
                    margin=0.6 if is_mobile else 0.8,
                ),
                corner_radius=0.5,
                color="neutral",
                grow_x=True,
            ),
            # Card 2: Active Cycles
            rio.Card(
                rio.Column(
                    rio.Row(
                        rio.Text("Active Cycles", font_size=0.85 if is_mobile else 0.95, font_weight="bold", fill=COLOR_TEXT_MUTED),
                        rio.Spacer(),
                        rio.Icon("material/autorenew", fill=rio.Color.from_hex("#8B5CF6"), min_width=1.3 if is_mobile else 1.6, min_height=1.3 if is_mobile else 1.6),
                        align_y=0.5,
                    ),
                    rio.Text(str(total_cycles), font_size=1.6 if is_mobile else 2.1, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                    spacing=0.08,
                    margin=0.6 if is_mobile else 0.8,
                ),
                corner_radius=0.5,
                color="neutral",
                grow_x=True,
            ),
            # Card 3: Upside
            rio.Card(
                rio.Column(
                    rio.Row(
                        rio.Text("In Upside", font_size=0.85 if is_mobile else 0.95, font_weight="bold", fill=COLOR_TEXT_MUTED),
                        rio.Spacer(),
                        rio.Icon("material/trending-up", fill=COLOR_UP_STRONG, min_width=1.3 if is_mobile else 1.6, min_height=1.3 if is_mobile else 1.6),
                        align_y=0.5,
                    ),
                    rio.Text(str(upside_count), font_size=1.6 if is_mobile else 2.1, font_weight="bold", fill=COLOR_UP_STRONG),
                    spacing=0.08,
                    margin=0.6 if is_mobile else 0.8,
                ),
                corner_radius=0.5,
                color="neutral",
                grow_x=True,
            ),
            # Card 4: Downside
            rio.Card(
                rio.Column(
                    rio.Row(
                        rio.Text("In Downside", font_size=0.85 if is_mobile else 0.95, font_weight="bold", fill=COLOR_TEXT_MUTED),
                        rio.Spacer(),
                        rio.Icon("material/trending-down", fill=COLOR_DOWN_STRONG, min_width=1.3 if is_mobile else 1.6, min_height=1.3 if is_mobile else 1.6),
                        align_y=0.5,
                    ),
                    rio.Text(str(downside_count), font_size=1.6 if is_mobile else 2.1, font_weight="bold", fill=COLOR_DOWN_STRONG),
                    spacing=0.08,
                    margin=0.6 if is_mobile else 0.8,
                ),
                corner_radius=0.5,
                color="neutral",
                grow_x=True,
            ),
        ]

        metrics_layout: rio.Component
        if is_mobile:
            metrics_layout = rio.Column(
                rio.Row(metric_cards[0], metric_cards[1], spacing=0.3, grow_x=True),
                rio.Row(metric_cards[2], metric_cards[3], spacing=0.3, grow_x=True),
                spacing=0.3,
                margin_x=0.4,
                grow_x=True,
            )
        else:
            metrics_layout = rio.Row(
                *metric_cards,
                spacing=0.8,
                margin_x=1.2,
                grow_x=True,
            )

        # Toolbar Filter Bar (Removed UNCLASSIFIED from options)
        toolbar_elements: list[rio.Component] = [
            rio.TextInput(
                label="Search Symbol or Company",
                text=self.bind().search_query,
                min_width=10.0 if is_mobile else 18.0,
                grow_x=True,
            ),
            rio.Dropdown(
                options=["ALL", "UPSIDE", "DOWNSIDE"],
                selected_value=self.bind().bucket_filter,
                label="Bucket Filter",
            ),
            rio.Dropdown(
                options=["ALL", "NSE", "BSE"],
                selected_value=self.bind().exchange_filter,
                label="Exchange",
            ),
            rio.Button(
                "Refresh",
                icon="material/refresh",
                shape="rounded",
                style="minor",
                color="neutral",
                min_height=2.2 if is_mobile else 2.6,
                on_press=self._on_refresh,
                is_loading=self.is_refreshing,
            ),
            rio.Button(
                "Add Cycle",
                icon="material/add",
                shape="rounded",
                style="major",
                color="primary",
                min_height=2.2 if is_mobile else 2.6,
                on_press=lambda: self.on_navigate("manage_cycles", None),
            ),
        ]

        toolbar_card = rio.Card(
            rio.FlowContainer(
                *toolbar_elements,
                spacing=0.4 if is_mobile else 0.6,
                row_spacing=0.3 if is_mobile else 0.4,
                column_spacing=0.4 if is_mobile else 0.6,
                justify="left",
                align_y=0.5,
                margin_x=0.6 if is_mobile else 0.9,
                margin_y=0.4 if is_mobile else 0.6,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            margin_x=0.4 if is_mobile else 1.2,
            grow_x=True,
        )

        # Data Display Section (Zero-scroll Mobile Cards vs Compact Desktop Table)
        data_content: rio.Component

        if not analyses:
            data_content = rio.Card(
                rio.Column(
                    rio.Icon("material/search-off", min_width=2.4, min_height=2.4, fill=COLOR_TEXT_DIM),
                    rio.Text("No stock cycles found matching the filters.", font_size=1.0 if is_mobile else 1.15, fill=COLOR_TEXT_MUTED),
                    rio.Button(
                        "Add a Stock Research Cycle",
                        icon="material/add",
                        shape="rounded",
                        style="major",
                        color="primary",
                        min_height=2.4,
                        on_press=lambda: self.on_navigate("manage_cycles", None),
                    ),
                    spacing=0.6,
                    align_x=0.5,
                    align_y=0.5,
                    margin=1.5,
                ),
                corner_radius=0.5,
                color="neutral",
                margin_x=0.4 if is_mobile else 1.2,
                grow_x=True,
            )
        elif is_mobile:
            mobile_cards: list[rio.Component] = []
            for item in analyses:
                chg_col = get_change_color(item.percentage_change)
                bucket_col = get_bucket_color(item.bucket)
                price_badge_col = COLOR_UP_STRONG if item.price_type == PriceType.LIVE else COLOR_TEXT_MUTED
                sym = item.stock_symbol

                mobile_card = rio.Card(
                    rio.Column(
                        # Top Row: Symbol, Exchange badge, Price, Price badge
                        rio.Row(
                            rio.Row(
                                rio.Text(item.stock_symbol, font_weight="bold", font_size=1.1, fill=COLOR_TEXT_PRIMARY),
                                rio.Card(
                                    rio.Text(
                                        item.exchange,
                                        font_size=0.68,
                                        font_weight="bold",
                                        fill=rio.Color.from_hex("#60A5FA"),
                                        margin_x=0.35,
                                        margin_y=0.1,
                                    ),
                                    corner_radius=0.25,
                                    color="hud",
                                    grow_x=False,
                                    grow_y=False,
                                    align_x=0.0,
                                    align_y=0.5,
                                ),
                                spacing=0.3,
                                align_y=0.5,
                                align_x=0.0,
                                grow_x=False,
                            ),
                            rio.Spacer(),
                            rio.Row(
                                rio.Text(f"₹{item.current_price:,.2f}", font_weight="bold", font_size=1.1, fill=COLOR_TEXT_PRIMARY),
                                rio.Card(
                                    rio.Text(
                                        item.price_type.value,
                                        font_size=0.65,
                                        font_weight="bold",
                                        fill=price_badge_col,
                                        margin_x=0.3,
                                        margin_y=0.1,
                                    ),
                                    corner_radius=0.2,
                                    color="hud",
                                    grow_x=False,
                                    grow_y=False,
                                    align_x=0.0,
                                    align_y=0.5,
                                ),
                                spacing=0.25,
                                align_y=0.5,
                            ),
                            align_y=0.5,
                            grow_x=True,
                        ),
                        rio.Text(item.company_name[:32], font_size=0.75, fill=COLOR_TEXT_MUTED),
                        rio.Separator(),
                        # Cycle & Metrics
                        rio.Row(
                            rio.Column(
                                rio.Text(f"Cycle {item.cycle_number}", font_size=0.78, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                                rio.Text(f"Ref: {item.original_reference_date.strftime('%d-%b-%Y')}", font_size=0.7, fill=COLOR_TEXT_DIM),
                                spacing=0.02,
                            ),
                            rio.Spacer(),
                            rio.Column(
                                rio.Text(f"Ref High: ₹{item.reference_high:,.2f}", font_size=0.78, fill=COLOR_TEXT_MUTED),
                                rio.Text(f"Recur: {item.recurring_reference_date.strftime('%d-%b')}", font_size=0.7, fill=COLOR_TEXT_DIM),
                                spacing=0.02,
                                align_x=1.0,
                            ),
                            align_y=0.5,
                            grow_x=True,
                        ),
                        # Bucket & % Change Row
                        rio.Row(
                            rio.Card(
                                rio.Text(
                                    item.bucket,
                                    font_size=0.72,
                                    font_weight="bold",
                                    fill=bucket_col,
                                    margin_x=0.4,
                                    margin_y=0.15,
                                ),
                                corner_radius=0.25,
                                color="hud",
                            ),
                            rio.Spacer(),
                            rio.Text(
                                f"{item.percentage_change:+.2f}%",
                                font_weight="bold",
                                font_size=1.1,
                                fill=chg_col,
                            ),
                            align_y=0.5,
                            grow_x=True,
                        ),
                        # Action Button
                        rio.Button(
                            "View Interactive Chart",
                            icon="material/show-chart",
                            shape="rounded",
                            style="minor",
                            color="primary",
                            min_height=2.2,
                            grow_x=True,
                            on_press=lambda s=sym: self.on_navigate("stock_detail", s),
                        ),
                        spacing=0.3,
                        margin=0.5,
                        grow_x=True,
                    ),
                    corner_radius=0.4,
                    color="neutral",
                    margin_x=0.4,
                    grow_x=True,
                )
                mobile_cards.append(mobile_card)

            data_content = rio.Column(
                *mobile_cards,
                spacing=0.4,
                grow_x=True,
                margin_bottom=1.5,
            )
        else:
            # Desktop Table View
            table_rows: list[rio.Component] = []

            # Table Header
            header_row = rio.Card(
                rio.Row(
                    rio.Text("STOCK & EXCHANGE", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=10.5),
                    rio.Text("CYCLE", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=4.0),
                    rio.Text("RESEARCH DATE (LD)", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=8.5),
                    rio.Text("TRADING DATE", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=7.5),
                    rio.Text("REF HIGH", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=6.5),
                    rio.Text("CURRENT PRICE", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=6.5),
                    rio.Text("MODE", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=4.2),
                    rio.Text("% CHANGE", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=5.5),
                    rio.Text("BUCKET CLASSIFICATION", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=9.0),
                    rio.Spacer(),
                    rio.Text("CHART", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=4.5),
                    spacing=0.4,
                    align_y=0.5,
                    margin_x=0.7,
                    margin_y=0.35,
                ),
                corner_radius=0.4,
                color="hud",
                grow_x=True,
            )
            table_rows.append(header_row)

            for item in analyses:
                chg_col = get_change_color(item.percentage_change)
                bucket_col = get_bucket_color(item.bucket)
                price_badge_col = COLOR_UP_STRONG if item.price_type == PriceType.LIVE else COLOR_TEXT_MUTED
                sym = item.stock_symbol

                row_card = rio.Card(
                    rio.Row(
                        # Stock & Exchange
                        rio.Column(
                            rio.Row(
                                rio.Text(item.stock_symbol, font_weight="bold", font_size=1.0, fill=COLOR_TEXT_PRIMARY),
                                rio.Card(
                                    rio.Text(
                                        item.exchange,
                                        font_size=0.65,
                                        font_weight="bold",
                                        fill=rio.Color.from_hex("#60A5FA"),
                                        margin_x=0.3,
                                        margin_y=0.08,
                                    ),
                                    corner_radius=0.2,
                                    color="hud",
                                    grow_x=False,
                                    grow_y=False,
                                    align_x=0.0,
                                    align_y=0.5,
                                ),
                                spacing=0.25,
                                align_y=0.5,
                                align_x=0.0,
                                grow_x=False,
                            ),
                            rio.Text(item.company_name[:20], font_size=0.75, fill=COLOR_TEXT_DIM),
                            min_width=10.5,
                            spacing=0.02,
                        ),
                        # Cycle Number
                        rio.Text(f"Cycle {item.cycle_number}", font_size=0.88, font_weight="bold", fill=COLOR_TEXT_MUTED, min_width=4.0),
                        # Original LD
                        rio.Column(
                            rio.Text(item.original_reference_date.strftime("%d-%b-%Y"), font_size=0.88, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                            rio.Text(f"Recur: {item.recurring_reference_date.strftime('%d-%b')}", font_size=0.72, fill=COLOR_TEXT_DIM),
                            min_width=8.5,
                            spacing=0.02,
                        ),
                        # Actual Trading Date
                        rio.Text(item.actual_reference_trading_date.strftime("%d-%b-%Y"), font_size=0.88, fill=COLOR_TEXT_PRIMARY, min_width=7.5),
                        # Ref High
                        rio.Text(f"₹{item.reference_high:,.2f}", font_size=0.9, font_weight="bold", fill=COLOR_TEXT_PRIMARY, min_width=6.5),
                        # Current Price
                        rio.Text(f"₹{item.current_price:,.2f}", font_weight="bold", font_size=0.98, fill=COLOR_TEXT_PRIMARY, min_width=6.5),
                        # Price Mode Badge
                        rio.Card(
                            rio.Text(
                                item.price_type.value,
                                font_size=0.68,
                                font_weight="bold",
                                fill=price_badge_col,
                                margin_x=0.35,
                                margin_y=0.1,
                            ),
                            corner_radius=0.25,
                            color="hud",
                            min_width=4.2,
                        ),
                        # % Change
                        rio.Text(
                            f"{item.percentage_change:+.2f}%",
                            font_weight="bold",
                            font_size=0.98,
                            fill=chg_col,
                            min_width=5.5,
                        ),
                        # Bucket Chip
                        rio.Card(
                            rio.Text(
                                item.bucket,
                                font_size=0.78,
                                font_weight="bold",
                                fill=bucket_col,
                                margin_x=0.4,
                                margin_y=0.15,
                            ),
                            corner_radius=0.25,
                            color="hud",
                            min_width=9.0,
                        ),
                        rio.Spacer(),
                        # Action Button
                        rio.Button(
                            "Chart",
                            icon="material/show-chart",
                            shape="rounded",
                            style="minor",
                            color="primary",
                            min_height=2.0,
                            min_width=4.5,
                            on_press=lambda s=sym: self.on_navigate("stock_detail", s),
                        ),
                        spacing=0.4,
                        align_y=0.5,
                        margin_x=0.7,
                        margin_y=0.35,
                    ),
                    corner_radius=0.4,
                    color="neutral",
                    elevate_on_hover=True,
                    grow_x=True,
                )
                table_rows.append(row_card)

            data_content = rio.Column(
                *table_rows,
                spacing=0.3,
                margin_x=1.2,
                margin_bottom=1.5,
                grow_x=True,
            )

        return rio.Column(
            header_content,
            metrics_layout,
            toolbar_card,
            data_content,
            spacing=0.6 if is_mobile else 0.8,
            grow_x=True,
        )
