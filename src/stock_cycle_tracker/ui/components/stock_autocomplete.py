"""Debounced stock autocomplete input component with intelligent suggestions dropdown and clickable suggestion items."""

from __future__ import annotations

import asyncio
import time
from typing import Callable, List, Optional

import rio

from stock_cycle_tracker.services.stock_search_service import StockSearchResult
from stock_cycle_tracker.ui.state import ServiceContainer
from stock_cycle_tracker.ui.theme import (
    COLOR_BORDER,
    COLOR_SURFACE_CARD,
    COLOR_SURFACE_HOVER,
    COLOR_TEXT_DIM,
    COLOR_TEXT_MUTED,
    COLOR_UP_STRONG,
)


class StockAutocompleteInput(rio.Component):
    """
    Interactive text input with debounced auto-complete dropdown for Indian stocks.
    Protects market APIs from rapid keystroke spam while delivering instant clickable suggestions.
    """

    label: str = "Stock Symbol or Company Name (e.g. RELIANCE, TCS, Tata Motors)"
    text: str = ""
    on_text_change: Optional[Callable[[str], None]] = None
    on_select: Optional[Callable[[str, str], None]] = None
    min_width: float = 14.0
    grow_x: bool = True

    # Internal state
    suggestions: List[StockSearchResult] = []
    is_searching: bool = False
    _debounce_task_id: int = 0

    async def _on_input_change(self, event: rio.TextInputChangeEvent) -> None:
        query_text = event.text
        self.text = query_text

        # Notify parent immediately so typed input is never lost
        if self.on_text_change:
            self.on_text_change(query_text)

        query = query_text.strip()
        if len(query) < 1:
            self.suggestions = []
            self.is_searching = False
            return

        self._debounce_task_id += 1
        current_task_id = self._debounce_task_id

        # 300ms Debounce Delay to prevent API over-hitting
        await asyncio.sleep(0.3)

        if current_task_id != self._debounce_task_id:
            return

        self.is_searching = True
        self.force_refresh()

        container = ServiceContainer.get()
        matches = container.stock_search_service.search(query, limit=5)

        self.suggestions = matches
        self.is_searching = False
        self.force_refresh()

    def _select_stock(self, symbol: str, name: str) -> None:
        self.text = symbol
        self.suggestions = []
        if self.on_text_change:
            self.on_text_change(symbol)
        if self.on_select:
            self.on_select(symbol, name)

    def _dismiss_suggestions(self) -> None:
        self.suggestions = []

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 55.0

        # Input field
        input_widget = rio.TextInput(
            label=self.label,
            text=self.text,
            on_change=self._on_input_change,
            min_width=self.min_width,
            grow_x=self.grow_x,
        )

        # Dropdown suggestion items
        dropdown_items: list[rio.Component] = []
        if self.suggestions and self.text.strip():
            for item in self.suggestions:
                sym = item.symbol
                name = item.company_name
                exch = item.exchange

                dropdown_items.append(
                    rio.Button(
                        rio.Row(
                            rio.Text(sym, font_weight="bold", font_size=0.9 if is_mobile else 0.95, min_width=6.5),
                            rio.Card(
                                rio.Text(exch, font_size=0.65, font_weight="bold", fill=rio.Color.from_hex("#60A5FA"), margin_x=0.3, margin_y=0.08),
                                corner_radius=0.2,
                                color="hud",
                            ),
                            rio.Text(name[:32], font_size=0.78 if is_mobile else 0.85, fill=COLOR_TEXT_MUTED),
                            rio.Spacer(),
                            rio.Icon("material/arrow-forward", fill=COLOR_TEXT_DIM, min_width=1.0, min_height=1.0),
                            spacing=0.35,
                            align_y=0.5,
                            grow_x=True,
                            margin_x=0.4,
                            margin_y=0.2,
                        ),
                        shape="rounded",
                        style="minor",
                        color="neutral",
                        grow_x=True,
                        min_height=2.2,
                        on_press=lambda s=sym, n=name: self._select_stock(s, n),
                    )
                )

            # Close suggestion banner
            dropdown_items.append(
                rio.Row(
                    rio.Text(f"Showing top {len(self.suggestions)} suggestions", font_size=0.72, fill=COLOR_TEXT_DIM),
                    rio.Spacer(),
                    rio.Button(
                        "Close",
                        shape="rounded",
                        style="plain-text",
                        color="neutral",
                        min_height=1.8,
                        on_press=self._dismiss_suggestions,
                    ),
                    align_y=0.5,
                    margin_x=0.4,
                    margin_top=0.1,
                )
            )

        if dropdown_items:
            return rio.Column(
                input_widget,
                rio.Card(
                    rio.Column(
                        *dropdown_items,
                        spacing=0.2,
                        margin=0.3,
                        grow_x=True,
                    ),
                    corner_radius=0.4,
                    color="hud",
                    grow_x=True,
                ),
                spacing=0.2,
                grow_x=True,
            )

        return input_widget
