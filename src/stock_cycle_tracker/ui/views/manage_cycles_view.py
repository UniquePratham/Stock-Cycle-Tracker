"""Manage Stocks and Cycles component with centered modal dialogs, dimmed backdrop, '+' quick cycle addition, and red cancel buttons."""

from __future__ import annotations

from datetime import date
from typing import Callable, Optional

import rio

from stock_cycle_tracker.ui.components.stock_autocomplete import StockAutocompleteInput
from stock_cycle_tracker.ui.state import ServiceContainer
from stock_cycle_tracker.ui.theme import (
    COLOR_BORDER,
    COLOR_DOWN_STRONG,
    COLOR_SURFACE_CARD,
    COLOR_TEXT_DIM,
    COLOR_TEXT_MUTED,
    COLOR_UP_STRONG,
)


class ManageCyclesView(rio.Component):
    """Allows registering new stocks/cycles, quick cycle addition via '+', centered deletion modals, and tracking management."""

    on_navigate: Callable[[str, Optional[str]], None]
    stock_input: str = ""
    date_input_str: str = ""
    feedback_message: str = ""
    feedback_is_error: bool = False
    is_submitting: bool = False

    # Deletion Modal State
    pending_delete_type: Optional[str] = None  # "cycle" or "stock"
    pending_delete_id: Optional[int] = None
    pending_delete_name: str = ""
    pending_delete_details: str = ""

    # Quick Add Cycle Modal State (via '+' button on each stock)
    quick_add_stock_id: Optional[int] = None
    quick_add_stock_symbol: str = ""
    quick_add_stock_name: str = ""
    quick_add_date_str: str = ""

    def _on_stock_input_change(self, text: str) -> None:
        self.stock_input = text

    def _on_stock_selected(self, symbol: str, name: str) -> None:
        self.stock_input = symbol

    async def _on_add_cycle(self) -> None:
        raw_sym = self.stock_input.strip()
        if not raw_sym:
            self.feedback_message = "Please enter a valid stock ticker or company name (e.g. RELIANCE, TCS, Tata Motors)."
            self.feedback_is_error = True
            return

        raw_date = self.date_input_str.strip()
        if not raw_date:
            self.feedback_message = "Please enter a reference research date (e.g. 10-Jan-2014 or 2014-01-10)."
            self.feedback_is_error = True
            return

        container = ServiceContainer.get()
        parsed_dt = container.excel_service._parse_date(raw_date)
        if not parsed_dt:
            self.feedback_message = f"Could not parse date '{raw_date}'. Please use DD-Mon-YYYY (e.g. 10-Jan-2014) or YYYY-MM-DD."
            self.feedback_is_error = True
            return

        if parsed_dt > date.today():
            self.feedback_message = f"Research date ({parsed_dt.strftime('%d-%b-%Y')}) cannot be in the future."
            self.feedback_is_error = True
            return

        if parsed_dt.year < 1990:
            self.feedback_message = f"Research date ({parsed_dt.strftime('%d-%b-%Y')}) must be after 1990."
            self.feedback_is_error = True
            return

        self.is_submitting = True
        self.feedback_message = "Resolving ticker and registering research cycle..."
        self.feedback_is_error = False
        self.force_refresh()

        try:
            stock, cycle, analysis = container.cycle_service.add_stock_cycle(
                query=raw_sym,
                reference_date=parsed_dt,
            )
            self.feedback_message = f"Stock Added: {stock.symbol} ({stock.company_name}) Cycle {cycle.cycle_number} registered (Ref: {cycle.reference_date.strftime('%d-%b-%Y')})!"
            self.feedback_is_error = False
            self.stock_input = ""
            self.date_input_str = ""
        except Exception as e:
            self.feedback_message = f"Error adding cycle: {e}"
            self.feedback_is_error = True
        finally:
            self.is_submitting = False
            self.force_refresh()

    # --- Quick Add Cycle Handlers ---
    def _open_quick_add(self, stock_id: int, symbol: str, name: str) -> None:
        self.quick_add_stock_id = stock_id
        self.quick_add_stock_symbol = symbol
        self.quick_add_stock_name = name
        self.quick_add_date_str = ""
        self.feedback_message = ""

    def _close_quick_add(self) -> None:
        self.quick_add_stock_id = None
        self.quick_add_stock_symbol = ""
        self.quick_add_stock_name = ""
        self.quick_add_date_str = ""

    async def _on_confirm_quick_add(self) -> None:
        raw_date = self.quick_add_date_str.strip()
        if not raw_date:
            self.feedback_message = "Please enter a research date for the new cycle."
            self.feedback_is_error = True
            return

        container = ServiceContainer.get()
        parsed_dt = container.excel_service._parse_date(raw_date)
        if not parsed_dt:
            self.feedback_message = f"Could not parse date '{raw_date}'. Please use DD-Mon-YYYY (e.g. 15-Jul-2019) or YYYY-MM-DD."
            self.feedback_is_error = True
            return

        if parsed_dt > date.today():
            self.feedback_message = f"Research date ({parsed_dt.strftime('%d-%b-%Y')}) cannot be in the future."
            self.feedback_is_error = True
            return

        self.is_submitting = True
        self.feedback_message = f"Adding new cycle to {self.quick_add_stock_symbol}..."
        self.feedback_is_error = False
        self.force_refresh()

        try:
            stock, cycle, analysis = container.cycle_service.add_stock_cycle(
                query=self.quick_add_stock_symbol,
                reference_date=parsed_dt,
            )
            self.feedback_message = f"Cycle Added: Successfully added Cycle {cycle.cycle_number} to {stock.symbol} (Ref: {cycle.reference_date.strftime('%d-%b-%Y')})!"
            self.feedback_is_error = False
            self._close_quick_add()
        except Exception as e:
            self.feedback_message = f"Error adding cycle: {e}"
            self.feedback_is_error = True
        finally:
            self.is_submitting = False
            self.force_refresh()

    # --- Deletion Confirmation Handlers ---
    def _prompt_delete_cycle(self, cycle_id: int, cycle_num: int, stock_symbol: str, ref_date_str: str) -> None:
        self.pending_delete_type = "cycle"
        self.pending_delete_id = cycle_id
        self.pending_delete_name = f"Cycle {cycle_num} of {stock_symbol}"
        self.pending_delete_details = f"Research Anchor Date: {ref_date_str}"

    def _prompt_delete_stock(self, stock_id: int, stock_symbol: str, company_name: str, cycle_count: int) -> None:
        self.pending_delete_type = "stock"
        self.pending_delete_id = stock_id
        self.pending_delete_name = f"{stock_symbol} ({company_name})"
        self.pending_delete_details = f"This will permanently delete this stock and all {cycle_count} of its registered research cycles."

    def _cancel_delete(self) -> None:
        self.pending_delete_type = None
        self.pending_delete_id = None
        self.pending_delete_name = ""
        self.pending_delete_details = ""

    def _confirm_delete(self) -> None:
        container = ServiceContainer.get()
        if self.pending_delete_type == "cycle" and self.pending_delete_id is not None:
            container.cycle_service.delete_cycle(self.pending_delete_id)
            self.feedback_message = f"Deleted Successfully: {self.pending_delete_name} removed."
            self.feedback_is_error = False
        elif self.pending_delete_type == "stock" and self.pending_delete_id is not None:
            container.cycle_service.delete_stock(self.pending_delete_id)
            self.feedback_message = f"Deleted Successfully: {self.pending_delete_name} and all associated cycles removed."
            self.feedback_is_error = False

        self._cancel_delete()

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

        # Page Header
        header = rio.Column(
            rio.Text("Manage Stocks & Research Cycles", font_size=1.3 if is_mobile else 1.8, font_weight="bold"),
            rio.Text("Add new research anchor dates, quick '+' cycle additions, or manage active tracked cycles", font_size=0.78 if is_mobile else 0.95, fill=COLOR_TEXT_MUTED),
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
                rio.Text("Add New Stock or Research Cycle", font_size=1.0 if is_mobile else 1.2, font_weight="bold"),
                rio.Text("Type a stock symbol or company name with live suggestions dropdown", font_size=0.75 if is_mobile else 0.85, fill=COLOR_TEXT_MUTED),
                spacing=0.02,
                align_x=0.0,
            ),
            spacing=0.4 if is_mobile else 0.5,
            align_y=0.5,
            align_x=0.0,
            grow_x=False,
        )

        # Main Input Form with Debounced Stock Autocomplete
        form_inputs: rio.Component
        if is_mobile:
            form_inputs = rio.Column(
                StockAutocompleteInput(
                    label="Stock Symbol / Name (e.g. RELIANCE, TCS)",
                    text=self.stock_input,
                    on_text_change=self._on_stock_input_change,
                    on_select=self._on_stock_selected,
                    grow_x=True,
                ),
                rio.TextInput(
                    label="Research Date (e.g. 10-Jan-2014)",
                    text=self.bind().date_input_str,
                    grow_x=True,
                ),
                rio.Button(
                    "Register Cycle",
                    icon="material/add",
                    shape="rounded",
                    style="major",
                    color="primary",
                    min_height=2.2,
                    is_loading=self.is_submitting,
                    grow_x=True,
                    on_press=self._on_add_cycle,
                ),
                spacing=0.35,
                grow_x=True,
            )
        else:
            form_inputs = rio.Row(
                StockAutocompleteInput(
                    label="Stock Symbol / Name (e.g. RELIANCE, TCS, Tata Motors)",
                    text=self.stock_input,
                    on_text_change=self._on_stock_input_change,
                    on_select=self._on_stock_selected,
                    grow_x=True,
                ),
                rio.TextInput(
                    label="Research Anchor Date (e.g. 10-Jan-2014, 2014-01-10)",
                    text=self.bind().date_input_str,
                    min_width=18.0,
                    grow_x=True,
                ),
                rio.Button(
                    "Register Cycle",
                    icon="material/add",
                    shape="rounded",
                    style="major",
                    color="primary",
                    min_height=2.6,
                    min_width=11.0,
                    is_loading=self.is_submitting,
                    on_press=self._on_add_cycle,
                ),
                spacing=0.8,
                align_y=0.5,
                grow_x=True,
            )

        form_card = rio.Card(
            rio.Column(
                form_title_row,
                rio.Separator(),
                form_inputs,
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
                    c_num = c.cycle_number
                    c_sym = stk.symbol
                    c_ref = c.reference_date.strftime("%d-%b-%Y")

                    if is_mobile:
                        cycles_rows.append(
                            rio.Card(
                                rio.Column(
                                    rio.Row(
                                        rio.Text(f"Cycle {c.cycle_number}", font_weight="bold", font_size=0.88),
                                        rio.Spacer(),
                                        rio.Button(
                                            "Delete",
                                            icon="material/delete",
                                            shape="rounded",
                                            style="plain-text",
                                            color="danger",
                                            on_press=lambda cid=c_id, cnum=c_num, csym=c_sym, cref=c_ref: self._prompt_delete_cycle(cid, cnum, csym, cref),
                                        ),
                                        align_y=0.5,
                                        grow_x=True,
                                    ),
                                    rio.Row(
                                        rio.Text(f"Ref Date: {c_ref}", font_size=0.75, fill=COLOR_TEXT_MUTED),
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
                                    rio.Text(f"Cycle {c.cycle_number}", font_weight="bold", font_size=0.95, min_width=6.0),
                                    rio.Column(
                                        rio.Text("Original Research Date", font_size=0.72, fill=COLOR_TEXT_DIM),
                                        rio.Text(c_ref, font_size=0.92, font_weight="bold"),
                                        min_width=12.0,
                                        spacing=0.03,
                                    ),
                                    rio.Column(
                                        rio.Text("Annual Recurrence", font_size=0.72, fill=COLOR_TEXT_DIM),
                                        rio.Text(c.recurring_formatted, font_size=0.92, font_weight="bold"),
                                        min_width=10.0,
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
                                        on_press=lambda cid=c_id, cnum=c_num, csym=c_sym, cref=c_ref: self._prompt_delete_cycle(cid, cnum, csym, cref),
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
                stk_name = stk.company_name
                stk_count = len(cyc_list)

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
                                rio.Text(stk.symbol, font_size=1.1, font_weight="bold"),
                                exchange_badge,
                                spacing=0.3,
                                align_y=0.5,
                                align_x=0.0,
                                grow_x=False,
                            ),
                            rio.Spacer(),
                            rio.Button(
                                "+ Add Cycle",
                                icon="material/add",
                                shape="rounded",
                                style="major",
                                color="success",
                                min_height=1.9,
                                on_press=lambda sid=stk_id, sym=stk_sym, name=stk_name: self._open_quick_add(sid, sym, name),
                            ),
                            align_y=0.5,
                            grow_x=True,
                        ),
                        rio.Text(stk.company_name[:24], font_size=0.75, fill=COLOR_TEXT_MUTED),
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
                                on_press=lambda sid=stk_id, sym=stk_sym, name=stk_name, cnt=stk_count: self._prompt_delete_stock(sid, sym, name, cnt),
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
                            rio.Text(stk.symbol, font_size=1.35, font_weight="bold"),
                            exchange_badge,
                            spacing=0.4,
                            align_y=0.5,
                            align_x=0.0,
                            grow_x=False,
                        ),
                        rio.Text(f"— {stk.company_name}", font_size=0.9, fill=COLOR_TEXT_MUTED, align_y=0.5),
                        rio.Spacer(),
                        rio.Button(
                            "+ Add Cycle",
                            icon="material/add",
                            shape="rounded",
                            style="major",
                            color="success",
                            min_height=2.4,
                            on_press=lambda sid=stk_id, sym=stk_sym, name=stk_name: self._open_quick_add(sid, sym, name),
                        ),
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
                            style="plain-text",
                            color="danger",
                            min_height=2.4,
                            on_press=lambda sid=stk_id, sym=stk_sym, name=stk_name, cnt=stk_count: self._prompt_delete_stock(sid, sym, name, cnt),
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

        # Base Page Content
        page_layout = rio.Column(
            header,
            form_card,
            *stock_cards,
            spacing=0.6 if is_mobile else 0.8,
            grow_x=True,
            margin_bottom=1.5,
        )

        # Centered Full-Screen Dimmed Backdrop Modals
        if self.pending_delete_type and self.pending_delete_id is not None:
            # Centered Deletion Modal Dialog Box
            deletion_modal = rio.Overlay(
                rio.Card(
                    rio.Card(
                        rio.Column(
                            rio.Row(
                                rio.Icon("material/warning", fill=COLOR_DOWN_STRONG, min_width=1.8, min_height=1.8),
                                rio.Column(
                                    rio.Text(
                                        f"Confirm Deletion",
                                        font_size=1.2 if is_mobile else 1.4,
                                        font_weight="bold",
                                        fill=COLOR_DOWN_STRONG,
                                    ),
                                    rio.Text(self.pending_delete_name, font_size=1.0, font_weight="bold"),
                                    spacing=0.04,
                                ),
                                spacing=0.4,
                                align_y=0.5,
                            ),
                            rio.Separator(),
                            rio.Text(self.pending_delete_details, font_size=0.88, fill=COLOR_TEXT_MUTED),
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
                                    on_press=self._cancel_delete,
                                ),
                                rio.Spacer(),
                                rio.Button(
                                    "Confirm & Permanently Delete",
                                    icon="material/delete-forever",
                                    shape="rounded",
                                    style="major",
                                    color="danger",
                                    min_height=2.4,
                                    grow_x=is_mobile,
                                    on_press=self._confirm_delete,
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
            return rio.Column(
                page_layout,
                deletion_modal,
                grow_x=True,
            )

        if self.quick_add_stock_id is not None:
            # Centered Quick Add Cycle Modal Dialog Box
            quick_add_modal = rio.Overlay(
                rio.Card(
                    rio.Card(
                        rio.Column(
                            rio.Row(
                                rio.Icon("material/add-circle", fill=COLOR_UP_STRONG, min_width=1.8, min_height=1.8),
                                rio.Column(
                                    rio.Text(
                                        f"Add New Research Cycle",
                                        font_size=1.2 if is_mobile else 1.4,
                                        font_weight="bold",
                                    ),
                                    rio.Text(f"{self.quick_add_stock_symbol} ({self.quick_add_stock_name})", font_size=0.95, fill=COLOR_TEXT_MUTED),
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
                                    is_loading=self.is_submitting,
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
            return rio.Column(
                page_layout,
                quick_add_modal,
                grow_x=True,
            )

        return page_layout
