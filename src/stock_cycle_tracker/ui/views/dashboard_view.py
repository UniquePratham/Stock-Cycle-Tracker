"""Polished, modern Dashboard view component with Reference High/Low, compact '+' icon button, 10s auto-dismissing toast notifications, and strict 0>=Up / <0 Down counting."""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone
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
    COLOR_UP_STRONG,
    get_bucket_color,
    get_change_color,
)


class DashboardView(rio.Component):
    """Main Cycle Analysis Dashboard with Reference High/Low, compact '+' button, and 10s auto-dismissing toast notifications."""

    on_navigate: Callable[[str, Optional[str]], None]
    search_query: str = ""
    bucket_filter: str = "ALL"
    exchange_filter: str = "ALL"
    is_refreshing: bool = False
    status_message: str = ""
    show_market_status: bool = True

    # 10s Toast Notification State
    toast_message: str = ""
    toast_is_error: bool = False
    _toast_id: int = 0

    # Quick Add Cycle Modal State (via '+' button on dashboard)
    quick_add_stock_symbol: Optional[str] = None
    quick_add_company_name: str = ""
    quick_add_date_str: str = ""
    is_submitting_cycle: bool = False
    quick_add_error: str = ""

    async def _show_toast(self, message: str, is_error: bool = False) -> None:
        self.toast_message = message
        self.toast_is_error = is_error
        self._toast_id += 1
        current_id = self._toast_id

        # Automatically dismiss toast after 10 seconds
        await asyncio.sleep(10.0)
        if current_id == self._toast_id:
            self.toast_message = ""

    def _toggle_market_status(self) -> None:
        self.show_market_status = not self.show_market_status

    def _get_analyses(self) -> List[CycleAnalysis]:
        container = ServiceContainer.get()
        analyses = container.cycle_service.get_dashboard_analyses(force_refresh=self.is_refreshing)

        # Apply search filter
        if self.search_query.strip():
            q = self.search_query.strip().upper()
            analyses = [a for a in analyses if q in a.stock_symbol.upper() or q in a.company_name.upper()]

        # Apply bucket filter
        if self.bucket_filter != "ALL":
            if self.bucket_filter in ("All Upside (≥0%)", "UPSIDE"):
                analyses = [a for a in analyses if a.percentage_change >= 0.0]
            elif self.bucket_filter in ("All Downside (<0%)", "DOWNSIDE"):
                analyses = [a for a in analyses if a.percentage_change < 0.0]
            else:
                def norm_b(s: str) -> str:
                    return s.replace("–", "-").replace("—", "-").replace(" ", "").upper()
                target_b = norm_b(self.bucket_filter)
                analyses = [a for a in analyses if norm_b(a.bucket) == target_b]

        # Apply exchange filter
        if self.exchange_filter != "ALL":
            analyses = [a for a in analyses if a.exchange == self.exchange_filter]

        return analyses

    async def _on_refresh(self) -> None:
        self.is_refreshing = True
        self.status_message = "Updating market prices..."
        container = ServiceContainer.get()
        container.cycle_service.get_dashboard_analyses(force_refresh=True)
        self.is_refreshing = False
        self.status_message = ""
        await self._show_toast("Market data prices successfully refreshed.", is_error=False)

    def _open_quick_add(self, symbol: str, company: str) -> None:
        self.quick_add_stock_symbol = symbol
        self.quick_add_company_name = company
        self.quick_add_date_str = ""
        self.quick_add_error = ""

    def _close_quick_add(self) -> None:
        self.quick_add_stock_symbol = None
        self.quick_add_company_name = ""
        self.quick_add_date_str = ""
        self.quick_add_error = ""

    async def _on_confirm_quick_add(self) -> None:
        raw_date = self.quick_add_date_str.strip()
        if not raw_date:
            self.quick_add_error = "Please enter a research date (e.g. 10-Jan-2018)."
            return

        container = ServiceContainer.get()
        parsed_dt = container.excel_service._parse_date(raw_date)
        if not parsed_dt:
            self.quick_add_error = f"Could not parse date '{raw_date}'. Please use DD-Mon-YYYY or YYYY-MM-DD."
            return

        if parsed_dt > date.today():
            self.quick_add_error = f"Research date ({parsed_dt.strftime('%d-%b-%Y')}) cannot be in the future."
            return

        self.is_submitting_cycle = True
        self.quick_add_error = ""

        sym = self.quick_add_stock_symbol
        try:
            stock, cycle, analysis = container.cycle_service.add_stock_cycle(
                query=sym,
                reference_date=parsed_dt,
            )
            self._close_quick_add()
            await self._show_toast(
                f"Cycle Added: Successfully registered Cycle {cycle.cycle_number} for {stock.symbol} (Ref: {cycle.reference_date.strftime('%d-%b-%Y')})!",
                is_error=False,
            )
        except Exception as e:
            self.quick_add_error = f"Error adding cycle: {e}"
        finally:
            self.is_submitting_cycle = False

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 45.0
        container = ServiceContainer.get()
        market_status = container.provider.get_market_status()
        analyses = self._get_analyses()

        total_stocks = len(set(a.stock_symbol for a in analyses))
        total_cycles = len(analyses)

        # 0 and above = In Upside; Below 0 = In Downside
        upside_count = sum(1 for a in analyses if a.percentage_change >= 0.0)
        downside_count = sum(1 for a in analyses if a.percentage_change < 0.0)

        # Accurate Indian Market Open / Close Timings (Mon-Fri 09:15-15:30 IST)
        now_utc = datetime.now(timezone.utc)
        ist_time = now_utc + timedelta(hours=5, minutes=30)
        is_weekday = ist_time.weekday() in (0, 1, 2, 3, 4)
        current_minute = ist_time.hour * 60 + ist_time.minute
        is_market_live = is_weekday and ((9 * 60 + 15) <= current_minute < (15 * 60 + 30))

        market_status_text = (
            "MARKET OPEN (09:15–15:30 IST)"
            if is_market_live
            else f"MARKET CLOSED ({'WEEKEND' if not is_weekday else 'PREV CLOSE'})"
        )
        market_status_color = COLOR_UP_STRONG if is_market_live else COLOR_TEXT_MUTED
        market_status_dot = COLOR_UP_STRONG if is_market_live else COLOR_TEXT_DIM

        # Market Status Component with Eye Toggle
        market_status_widget: rio.Component
        if self.show_market_status:
            market_status_widget = rio.Card(
                rio.Row(
                    rio.Icon(
                        "material/fiber-manual-record",
                        fill=market_status_dot,
                        min_width=1.0 if is_mobile else 1.3,
                        min_height=1.0 if is_mobile else 1.3,
                    ),
                    rio.Text(
                        market_status_text if not is_mobile else ("OPEN" if is_market_live else "CLOSED"),
                        font_size=0.7 if is_mobile else 0.85,
                        font_weight="bold",
                        fill=market_status_color,
                    ),
                    rio.IconButton(
                        icon="material/visibility",
                        style="plain-text",
                        color="neutral",
                        min_size=1.6 if is_mobile else 1.8,
                        on_press=self._toggle_market_status,
                    ),
                    spacing=0.25,
                    align_y=0.5,
                    margin_x=0.4 if is_mobile else 0.6,
                    margin_y=0.15,
                ),
                corner_radius=0.4,
                color="hud",
            )
        else:
            market_status_widget = rio.IconButton(
                icon="material/visibility-off",
                style="minor",
                color="neutral",
                min_size=1.8 if is_mobile else 2.2,
                on_press=self._toggle_market_status,
            )

        # Header Title Bar
        header_content: rio.Component
        if is_mobile:
            header_content = rio.Column(
                rio.Row(
                    rio.Text("Cycle Analytics", font_size=1.3, font_weight="bold"),
                    rio.Spacer(),
                    market_status_widget,
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Text(
                    "Annual research-date cycle benchmark vs Ref High / Low",
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
                    ),
                    rio.Text(
                        "Annual research-date cycle boundaries benchmarked against historical Reference High & Low",
                        font_size=0.95,
                        fill=COLOR_TEXT_MUTED,
                    ),
                    spacing=0.08,
                    align_x=0.0,
                ),
                rio.Spacer(),
                market_status_widget,
                spacing=1.0,
                align_y=0.5,
                margin_x=1.2,
                margin_top=0.2,
                grow_x=True,
            )

        # Sticky Floating 10-Second Auto-Dismissing Toast Notification Overlay
        toast_overlay: Optional[rio.Component] = None
        if self.toast_message:
            toast_overlay = rio.Overlay(
                rio.Card(
                    rio.Row(
                        rio.Icon(
                            "material/error" if self.toast_is_error else "material/check-circle",
                            fill=COLOR_DOWN_STRONG if self.toast_is_error else COLOR_UP_STRONG,
                            min_width=1.4,
                            min_height=1.4,
                        ),
                        rio.Text(
                            self.toast_message,
                            font_size=0.95,
                            font_weight="bold",
                            fill=COLOR_DOWN_STRONG if self.toast_is_error else COLOR_UP_STRONG,
                        ),
                        rio.Spacer(),
                        rio.IconButton(
                            icon="material/close",
                            style="plain-text",
                            color="neutral",
                            min_size=1.6,
                            on_press=lambda: setattr(self, "toast_message", ""),
                        ),
                        spacing=0.4,
                        align_y=0.5,
                        margin_x=0.8,
                        margin_y=0.35,
                        grow_x=True,
                    ),
                    corner_radius=0.5,
                    color="hud",
                    elevate_on_hover=True,
                    align_x=0.5,
                    align_y=0.0,
                    margin_top=1.0,
                    margin_x=0.5 if is_mobile else 1.5,
                    grow_x=False,
                    grow_y=False,
                )
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
                    rio.Text(str(total_stocks), font_size=1.6 if is_mobile else 2.1, font_weight="bold"),
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
                    rio.Text(str(total_cycles), font_size=1.6 if is_mobile else 2.1, font_weight="bold"),
                    spacing=0.08,
                    margin=0.6 if is_mobile else 0.8,
                ),
                corner_radius=0.5,
                color="neutral",
                grow_x=True,
            ),
            # Card 3: Upside (>= 0%)
            rio.Card(
                rio.Column(
                    rio.Row(
                        rio.Text("In Upside (≥0%)", font_size=0.85 if is_mobile else 0.95, font_weight="bold", fill=COLOR_TEXT_MUTED),
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
            # Card 4: Downside (< 0%)
            rio.Card(
                rio.Column(
                    rio.Row(
                        rio.Text("In Downside (<0%)", font_size=0.85 if is_mobile else 0.95, font_weight="bold", fill=COLOR_TEXT_MUTED),
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

        # Toolbar Filter Bar
        toolbar_elements: list[rio.Component] = [
            rio.TextInput(
                label="Search Symbol or Company",
                text=self.bind().search_query,
                min_width=10.0 if is_mobile else 18.0,
                grow_x=True,
            ),
            rio.Dropdown(
                options=[
                    "ALL",
                    "All Upside (≥0%)",
                    "All Downside (<0%)",
                    "Upside >20%",
                    "Upside 15–20%",
                    "Upside 10–15%",
                    "Upside 5–10%",
                    "Upside 0–5%",
                    "Downside 0–5%",
                    "Downside 5–10%",
                    "Downside 10–15%",
                    "Downside 15–20%",
                    "Downside >20%",
                ],
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
                style="major",
                color="secondary",
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
                comp = item.company_name

                mobile_card = rio.Card(
                    rio.Column(
                        # Top Row: Symbol, Exchange badge, Price, Price badge
                        rio.Row(
                            rio.Row(
                                rio.Text(item.stock_symbol, font_weight="bold", font_size=1.1),
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
                                rio.Text(f"₹{item.current_price:,.2f}", font_weight="bold", font_size=1.1),
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
                                rio.Text(f"Cycle {item.cycle_number}", font_size=0.78, font_weight="bold"),
                                rio.Text(f"Ref: {item.original_reference_date.strftime('%d-%b-%Y')}", font_size=0.7, fill=COLOR_TEXT_DIM),
                                spacing=0.02,
                            ),
                            rio.Spacer(),
                            rio.Column(
                                rio.Text(f"High: ₹{item.reference_high:,.2f} | Low: ₹{item.reference_low:,.2f}", font_size=0.75, fill=COLOR_TEXT_MUTED),
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
                        # Action Buttons Row
                        rio.Row(
                            rio.Button(
                                "+ Add Cycle",
                                icon="material/add",
                                shape="rounded",
                                style="minor",
                                color="success",
                                min_height=2.0,
                                grow_x=True,
                                on_press=lambda s=sym, c=comp: self._open_quick_add(s, c),
                            ),
                            rio.Button(
                                "View Chart",
                                icon="material/show-chart",
                                shape="rounded",
                                style="minor",
                                color="primary",
                                min_height=2.0,
                                grow_x=True,
                                on_press=lambda s=sym: self.on_navigate("stock_detail", s),
                            ),
                            spacing=0.3,
                            grow_x=True,
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
                    rio.Text("STOCK & EXCHANGE", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=9.5),
                    rio.Text("CYCLE", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=3.8),
                    rio.Text("RESEARCH DATE (LD)", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=8.0),
                    rio.Text("TRADING DATE", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=7.0),
                    rio.Text("REF HIGH", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=5.8),
                    rio.Text("REF LOW", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=5.8),
                    rio.Text("CURRENT PRICE", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=6.0),
                    rio.Text("MODE", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=3.8),
                    rio.Text("% CHANGE", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=5.2),
                    rio.Text("BUCKET CLASSIFICATION", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=8.5),
                    rio.Spacer(),
                    rio.Text("ACTIONS", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=7.5),
                    spacing=0.35,
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
                comp = item.company_name

                row_card = rio.Card(
                    rio.Row(
                        # Stock & Exchange
                        rio.Column(
                            rio.Row(
                                rio.Text(item.stock_symbol, font_weight="bold", font_size=0.98),
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
                            rio.Text(item.company_name[:18], font_size=0.72, fill=COLOR_TEXT_DIM),
                            min_width=9.5,
                            spacing=0.02,
                        ),
                        # Cycle Number
                        rio.Text(f"Cycle {item.cycle_number}", font_size=0.85, font_weight="bold", fill=COLOR_TEXT_MUTED, min_width=3.8),
                        # Original LD
                        rio.Column(
                            rio.Text(item.original_reference_date.strftime("%d-%b-%Y"), font_size=0.85, font_weight="bold"),
                            rio.Text(f"Recur: {item.recurring_reference_date.strftime('%d-%b')}", font_size=0.7, fill=COLOR_TEXT_DIM),
                            min_width=8.0,
                            spacing=0.02,
                        ),
                        # Actual Trading Date
                        rio.Text(item.actual_reference_trading_date.strftime("%d-%b-%Y"), font_size=0.85, min_width=7.0),
                        # Ref High
                        rio.Text(f"₹{item.reference_high:,.2f}", font_size=0.88, font_weight="bold", min_width=5.8),
                        # Ref Low
                        rio.Text(f"₹{item.reference_low:,.2f}", font_size=0.88, fill=COLOR_TEXT_MUTED, min_width=5.8),
                        # Current Price
                        rio.Text(f"₹{item.current_price:,.2f}", font_weight="bold", font_size=0.92, min_width=6.0),
                        # Price Mode Badge
                        rio.Card(
                            rio.Text(
                                item.price_type.value,
                                font_size=0.65,
                                font_weight="bold",
                                fill=price_badge_col,
                                margin_x=0.3,
                                margin_y=0.08,
                            ),
                            corner_radius=0.2,
                            color="hud",
                            min_width=3.8,
                        ),
                        # % Change
                        rio.Text(
                            f"{item.percentage_change:+.2f}%",
                            font_weight="bold",
                            font_size=0.92,
                            fill=chg_col,
                            min_width=5.2,
                        ),
                        # Bucket Chip
                        rio.Card(
                            rio.Text(
                                item.bucket,
                                font_size=0.75,
                                font_weight="bold",
                                fill=bucket_col,
                                margin_x=0.35,
                                margin_y=0.12,
                            ),
                            corner_radius=0.25,
                            color="hud",
                            min_width=8.5,
                        ),
                        rio.Spacer(),
                        # Action Buttons (Circular '+' Add Cycle IconButton + Chart button)
                        rio.Row(
                            rio.IconButton(
                                icon="material/add",
                                style="minor",
                                color="success",
                                min_size=2.0,
                                on_press=lambda s=sym, c=comp: self._open_quick_add(s, c),
                            ),
                            rio.Button(
                                "Chart",
                                icon="material/show-chart",
                                shape="rounded",
                                style="minor",
                                color="primary",
                                min_height=2.0,
                                min_width=4.6,
                                grow_x=False,
                                on_press=lambda s=sym: self.on_navigate("stock_detail", s),
                            ),
                            spacing=0.3,
                            align_y=0.5,
                            grow_x=False,
                            min_width=7.5,
                        ),
                        spacing=0.35,
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

        page_layout = rio.Column(
            header_content,
            metrics_layout,
            toolbar_card,
            data_content,
            spacing=0.6 if is_mobile else 0.8,
            grow_x=True,
        )

        components: list[rio.Component] = [page_layout]

        # Sticky Floating Toast Overlay (floats on top regardless of scroll position)
        if toast_overlay is not None:
            components.append(toast_overlay)

        # Centered Quick Add Cycle Modal Dialog Box (Overlay)
        if self.quick_add_stock_symbol is not None:
            quick_add_dialog = rio.Overlay(
                rio.Card(
                    rio.Card(
                        rio.Column(
                            rio.Row(
                                rio.Icon("material/add-circle", fill=COLOR_UP_STRONG, min_width=1.8, min_height=1.8),
                                rio.Column(
                                    rio.Text(
                                        "Add New Research Cycle",
                                        font_size=1.2 if is_mobile else 1.4,
                                        font_weight="bold",
                                    ),
                                    rio.Text(f"{self.quick_add_stock_symbol} ({self.quick_add_company_name})", font_size=0.95, fill=COLOR_TEXT_MUTED),
                                    spacing=0.04,
                                ),
                                spacing=0.4,
                                align_y=0.5,
                            ),
                            rio.Separator(),
                            rio.TextInput(
                                label="Research Anchor Date (e.g. 10-Jan-2018, 2018-01-10)",
                                text=self.bind().quick_add_date_str,
                                min_width=16.0 if is_mobile else 22.0,
                                grow_x=True,
                            ),
                            rio.Text(self.quick_add_error, font_size=0.85, font_weight="bold", fill=COLOR_DOWN_STRONG) if self.quick_add_error else rio.Spacer(),
                            rio.Row(
                                rio.Button(
                                    "Cancel",
                                    icon="material/close",
                                    shape="rounded",
                                    style="minor",
                                    color="danger",
                                    min_height=2.4,
                                    min_width=6.5,
                                    grow_x=is_mobile,
                                    on_press=self._close_quick_add,
                                ),
                                rio.Spacer(),
                                rio.Button(
                                    "Register Cycle",
                                    icon="material/check",
                                    shape="rounded",
                                    style="major",
                                    color="success",
                                    min_height=2.4,
                                    grow_x=is_mobile,
                                    is_loading=self.is_submitting_cycle,
                                    on_press=self._on_confirm_quick_add,
                                ),
                                spacing=0.4,
                                align_y=0.5,
                                grow_x=True,
                            ),
                            spacing=0.6,
                            margin=1.0,
                            grow_x=True,
                        ),
                        corner_radius=0.6,
                        color="neutral",
                        min_width=22.0 if not is_mobile else 18.0,
                        align_x=0.5,
                        align_y=0.5,
                    ),
                    color="hud",
                    align_x=0.5,
                    align_y=0.5,
                    grow_x=True,
                    grow_y=True,
                )
            )
            components.append(quick_add_dialog)

        return rio.Column(*components, grow_x=True)
