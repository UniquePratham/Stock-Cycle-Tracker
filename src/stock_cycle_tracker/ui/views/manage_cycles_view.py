"""Manage Stocks and Cycles component with left-aligned headers, rich PC typography, and zero-overflow mobile layout."""

from __future__ import annotations

from datetime import date
from typing import Callable, Optional

import rio

from stock_cycle_tracker.ui.state import ServiceContainer
from stock_cycle_tracker.ui.theme import (
    COLOR_BORDER,
    COLOR_DOWN_STRONG,
    COLOR_SURFACE_CARD,
    COLOR_TEXT_DIM,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_UP_STRONG,
)


class ManageCyclesView(rio.Component):
    """Allows adding new research cycles, viewing existing ones, and deleting cycles."""

    on_navigate: Callable[[str, Optional[str]], None]
    stock_input: str = ""
    date_input_str: str = ""
    feedback_message: str = ""
    feedback_is_error: bool = False

    def _on_add_cycle(self) -> None:
        sym = self.stock_input.strip().upper()
        if not sym:
            self.feedback_message = "Please enter a valid stock symbol or name."
            self.feedback_is_error = True
            return

        raw_date = self.date_input_str.strip()
        if not raw_date:
            self.feedback_message = "Please enter a reference research date (e.g. 2014-01-10 or 10-Jan-2014)."
            self.feedback_is_error = True
            return

        container = ServiceContainer.get()
        parsed_dt = container.excel_service._parse_date(raw_date)
        if not parsed_dt:
            self.feedback_message = f"Could not parse date '{raw_date}'. Please use YYYY-MM-DD or DD-Mon-YYYY."
            self.feedback_is_error = True
            return

        if parsed_dt > date.today():
            self.feedback_message = "Research date cannot be in the future."
            self.feedback_is_error = True
            return

        try:
            stock, cycle, analysis = container.cycle_service.add_stock_cycle(
                query=sym,
                reference_date=parsed_dt,
            )
            self.feedback_message = f"Successfully added {stock.symbol} Cycle {cycle.cycle_number} (Ref: {cycle.reference_date.strftime('%d-%b-%Y')})!"
            self.feedback_is_error = False
            self.stock_input = ""
            self.date_input_str = ""
        except Exception as e:
            self.feedback_message = f"Error adding cycle: {e}"
            self.feedback_is_error = True

    def _on_delete_cycle(self, cycle_id: int) -> None:
        container = ServiceContainer.get()
        container.cycle_service.delete_cycle(cycle_id)
        self.feedback_message = "Cycle deleted successfully."
        self.feedback_is_error = False

    def _on_delete_stock(self, stock_id: int) -> None:
        container = ServiceContainer.get()
        container.cycle_service.delete_stock(stock_id)
        self.feedback_message = "Stock and all its cycles removed."
        self.feedback_is_error = False

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 55.0
        container = ServiceContainer.get()
        all_cycles = container.repository.list_all_cycles()

        # Group cycles by stock
        stocks_map: dict[int, tuple[any, list]] = {}
        for stock, cycle in all_cycles:
            if stock.id not in stocks_map:
                stocks_map[stock.id] = (stock, [])
            stocks_map[stock.id][1].append(cycle)

        # Header Title
        header = rio.Column(
            rio.Text("Manage Stocks & Research Cycles", font_size=1.3 if is_mobile else 1.8, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
            rio.Text("Add new research anchor dates or manage active tracked cycles", font_size=0.78 if is_mobile else 0.95, fill=COLOR_TEXT_MUTED),
            spacing=0.08,
            margin_x=0.4 if is_mobile else 1.2,
            margin_top=0.2,
            align_x=0.0,
            grow_x=True,
        )

        # Left-aligned Section Title Row
        form_title_row = rio.Row(
            rio.Icon(
                "material/add-circle",
                fill=rio.Color.from_hex("#3B82F6"),
                min_width=1.3 if is_mobile else 1.6,
                min_height=1.3 if is_mobile else 1.6,
            ),
            rio.Column(
                rio.Text("Add New Research Date Cycle", font_size=1.0 if is_mobile else 1.2, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                rio.Text("Enter a stock ticker (e.g. RELIANCE, TCS) and historical research anchor date", font_size=0.75 if is_mobile else 0.85, fill=COLOR_TEXT_MUTED),
                spacing=0.02,
                align_x=0.0,
            ),
            spacing=0.4 if is_mobile else 0.5,
            align_y=0.5,
            align_x=0.0,
            grow_x=False,
        )

        # Input Card with FlowContainer
        form_card = rio.Card(
            rio.Column(
                form_title_row,
                rio.Separator(),
                rio.FlowContainer(
                    rio.TextInput(
                        label="Stock Symbol / Name (e.g. RELIANCE)",
                        text=self.bind().stock_input,
                        min_width=10.0 if is_mobile else 18.0,
                        grow_x=True,
                    ),
                    rio.TextInput(
                        label="Research Date (e.g. 10-Jan-2014)",
                        text=self.bind().date_input_str,
                        min_width=10.0 if is_mobile else 16.0,
                        grow_x=True,
                    ),
                    rio.Button(
                        "Register Cycle",
                        icon="material/add",
                        shape="rounded",
                        style="major",
                        color="primary",
                        min_height=2.2 if is_mobile else 2.6,
                        grow_x=is_mobile,
                        on_press=self._on_add_cycle,
                    ),
                    spacing=0.4 if is_mobile else 0.6,
                    row_spacing=0.3 if is_mobile else 0.4,
                    column_spacing=0.4 if is_mobile else 0.6,
                    justify="left",
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Text(
                    self.feedback_message,
                    font_size=0.82 if is_mobile else 0.92,
                    font_weight="bold",
                    fill=COLOR_DOWN_STRONG if self.feedback_is_error else COLOR_UP_STRONG,
                ) if self.feedback_message else rio.Spacer(),
                spacing=0.5 if is_mobile else 0.7,
                margin=0.6 if is_mobile else 1.0,
                align_x=0.0,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            margin_x=0.4 if is_mobile else 1.2,
            grow_x=True,
        )

        # Tracked Stocks Section Header
        stock_cards: list[rio.Component] = []
        stock_cards.append(
            rio.Text(
                "Currently Tracked Portfolios & Cycles",
                font_size=1.1 if is_mobile else 1.35,
                font_weight="bold",
                fill=COLOR_TEXT_PRIMARY,
                margin_x=0.4 if is_mobile else 1.2,
                margin_top=0.4,
            )
        )

        if not stocks_map:
            stock_cards.append(
                rio.Card(
                    rio.Column(
                        rio.Icon("material/inbox", min_width=2.4, min_height=2.4, fill=COLOR_TEXT_DIM),
                        rio.Text("No stocks currently tracked. Use the form above to add one.", font_size=0.9 if is_mobile else 1.05, fill=COLOR_TEXT_MUTED),
                        spacing=0.4,
                        align_x=0.5,
                        align_y=0.5,
                        margin=1.5,
                    ),
                    corner_radius=0.5,
                    color="neutral",
                    margin_x=0.4 if is_mobile else 1.2,
                    grow_x=True,
                )
            )
        else:
            for stock_id, (stk, cyc_list) in stocks_map.items():
                cycles_rows: list[rio.Component] = []
                for c in cyc_list:
                    c_id = c.id
                    if is_mobile:
                        cycles_rows.append(
                            rio.Card(
                                rio.Column(
                                    rio.Row(
                                        rio.Text(f"Cycle {c.cycle_number}", font_weight="bold", font_size=0.88, fill=COLOR_TEXT_PRIMARY),
                                        rio.Spacer(),
                                        rio.Button(
                                            "Delete",
                                            icon="material/delete",
                                            shape="rounded",
                                            style="plain-text",
                                            color="danger",
                                            on_press=lambda cid=c_id: self._on_delete_cycle(cid),
                                        ),
                                        align_y=0.5,
                                        grow_x=True,
                                    ),
                                    rio.Row(
                                        rio.Text(f"Ref Date: {c.reference_date.strftime('%d-%b-%Y')}", font_size=0.75, fill=COLOR_TEXT_MUTED),
                                        rio.Spacer(),
                                        rio.Text(f"Recur: {c.recurring_formatted}", font_size=0.75, fill=COLOR_TEXT_DIM),
                                        align_y=0.5,
                                        grow_x=True,
                                    ),
                                    spacing=0.2,
                                    margin=0.4,
                                    grow_x=True,
                                ),
                                corner_radius=0.3,
                                color="hud",
                                grow_x=True,
                            )
                        )
                    else:
                        cycles_rows.append(
                            rio.Card(
                                rio.Row(
                                    rio.Text(f"Cycle {c.cycle_number}", font_weight="bold", font_size=0.95, fill=COLOR_TEXT_PRIMARY, min_width=7.0),
                                    rio.Column(
                                        rio.Text("Original Research Date", font_size=0.75, fill=COLOR_TEXT_DIM),
                                        rio.Text(c.reference_date.strftime("%d-%b-%Y"), font_size=0.92, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                                        min_width=14.0,
                                        spacing=0.03,
                                    ),
                                    rio.Column(
                                        rio.Text("Annual Recurrence", font_size=0.75, fill=COLOR_TEXT_DIM),
                                        rio.Text(c.recurring_formatted, font_size=0.92, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                                        min_width=12.0,
                                        spacing=0.03,
                                    ),
                                    rio.Spacer(),
                                    rio.Button(
                                        "Delete Cycle",
                                        icon="material/delete",
                                        shape="rounded",
                                        style="plain-text",
                                        color="danger",
                                        min_height=2.2,
                                        on_press=lambda cid=c_id: self._on_delete_cycle(cid),
                                    ),
                                    spacing=0.6,
                                    align_y=0.5,
                                    margin_x=0.8,
                                    margin_y=0.35,
                                    grow_x=True,
                                ),
                                corner_radius=0.4,
                                color="hud",
                                grow_x=True,
                            )
                        )

                stk_id = stk.id
                stk_sym = stk.symbol

                exchange_badge = rio.Card(
                    rio.Text(
                        stk.preferred_exchange.value,
                        font_size=0.72,
                        font_weight="bold",
                        fill=rio.Color.from_hex("#60A5FA"),
                        margin_x=0.45,
                        margin_y=0.1,
                    ),
                    corner_radius=0.25,
                    color="hud",
                    grow_x=False,
                    grow_y=False,
                    align_x=0.0,
                    align_y=0.5,
                )

                card_header: rio.Component
                if is_mobile:
                    card_header = rio.Column(
                        rio.Row(
                            rio.Row(
                                rio.Text(stk.symbol, font_size=1.1, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                                exchange_badge,
                                spacing=0.3,
                                align_y=0.5,
                                align_x=0.0,
                                grow_x=False,
                            ),
                            rio.Spacer(),
                            rio.Text(stk.company_name[:24], font_size=0.75, fill=COLOR_TEXT_MUTED),
                            align_y=0.5,
                            grow_x=True,
                        ),
                        rio.Row(
                            rio.Button(
                                "View Chart",
                                icon="material/show-chart",
                                shape="rounded",
                                style="minor",
                                color="primary",
                                min_height=2.0,
                                grow_x=True,
                                on_press=lambda s=stk_sym: self.on_navigate("stock_detail", s),
                            ),
                            rio.Button(
                                "Remove Stock",
                                icon="material/delete-forever",
                                shape="rounded",
                                style="plain-text",
                                color="danger",
                                min_height=2.0,
                                grow_x=True,
                                on_press=lambda sid=stk_id: self._on_delete_stock(sid),
                            ),
                            spacing=0.3,
                            grow_x=True,
                        ),
                        spacing=0.25,
                        grow_x=True,
                    )
                else:
                    card_header = rio.Row(
                        rio.Row(
                            rio.Text(stk.symbol, font_size=1.35, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                            exchange_badge,
                            spacing=0.4,
                            align_y=0.5,
                            align_x=0.0,
                            grow_x=False,
                        ),
                        rio.Text(f"— {stk.company_name}", font_size=0.9, fill=COLOR_TEXT_MUTED, align_y=0.5),
                        rio.Spacer(),
                        rio.Button(
                            "View Chart",
                            icon="material/show-chart",
                            shape="rounded",
                            style="minor",
                            color="primary",
                            min_height=2.4,
                            on_press=lambda s=stk_sym: self.on_navigate("stock_detail", s),
                        ),
                        rio.Button(
                            "Remove Stock",
                            icon="material/delete-forever",
                            shape="rounded",
                            style="minor",
                            color="danger",
                            min_height=2.4,
                            on_press=lambda sid=stk_id: self._on_delete_stock(sid),
                        ),
                        spacing=0.4,
                        align_y=0.5,
                        grow_x=True,
                    )

                card = rio.Card(
                    rio.Column(
                        card_header,
                        rio.Separator(),
                        *cycles_rows,
                        spacing=0.35,
                        margin=0.6 if is_mobile else 0.9,
                        grow_x=True,
                    ),
                    corner_radius=0.5,
                    color="neutral",
                    margin_x=0.4 if is_mobile else 1.2,
                    grow_x=True,
                )
                stock_cards.append(card)

        return rio.Column(
            header,
            form_card,
            *stock_cards,
            spacing=0.6 if is_mobile else 0.8,
            grow_x=True,
            margin_bottom=1.5,
        )
