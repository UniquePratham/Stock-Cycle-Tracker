"""Alerts configuration and monitoring view component with debounced autocomplete, quick presets, left-aligned event cards, and zero-overflow layout."""

from __future__ import annotations

from typing import Callable, Optional

import rio

from stock_cycle_tracker.services.alert_service import AlertConditionType
from stock_cycle_tracker.ui.components.stock_autocomplete import StockAutocompleteInput
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


class AlertsView(rio.Component):
    """Configures cycle-specific alert rules and inspects triggered events."""

    on_navigate: Callable[[str, Optional[str]], None]
    stock_input: str = ""
    cycle_num_input: str = "1"
    condition_type_input: str = "PERCENTAGE_BELOW"
    threshold_input: str = "-10.0"
    target_bucket_input: str = ""
    status_message: str = ""

    def _on_stock_selected(self, symbol: str, name: str) -> None:
        self.stock_input = symbol

    def _apply_preset(self, condition: str, threshold: str) -> None:
        self.condition_type_input = condition
        self.threshold_input = threshold
        self.status_message = f"Applied Preset: {condition} at {threshold}%"

    def _on_add_alert(self) -> None:
        sym = self.stock_input.strip().upper().replace(" ", "")
        if not sym:
            self.status_message = "Please enter a stock symbol."
            return

        try:
            c_num = int(self.cycle_num_input)
            thresh = float(self.threshold_input) if self.threshold_input else 0.0
            cond = AlertConditionType(self.condition_type_input)

            container = ServiceContainer.get()
            container.alert_service.add_alert(
                stock_symbol=sym,
                cycle_number=c_num,
                condition_type=cond,
                threshold_value=thresh,
                target_bucket=self.target_bucket_input.strip() or None,
            )
            self.status_message = f"Alert rule for {sym} Cycle {c_num} saved successfully!"
            self.stock_input = ""
        except Exception as e:
            self.status_message = f"Error creating alert: {e}"

    def _on_toggle_alert(self, alert_id: int, current_status: bool) -> None:
        container = ServiceContainer.get()
        container.alert_service.toggle_alert(alert_id, not current_status)
        self.status_message = "Alert status updated."

    def _on_delete_alert(self, alert_id: int) -> None:
        container = ServiceContainer.get()
        container.alert_service.delete_alert(alert_id)
        self.status_message = "Alert removed."

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 55.0
        container = ServiceContainer.get()
        alerts = container.alert_service.list_alerts()

        # Evaluate against active analyses for live check
        analyses = container.cycle_service.get_dashboard_analyses()
        triggered_events = container.alert_service.evaluate_analyses(analyses)

        # Header Title
        header = rio.Column(
            rio.Text(
                "Cycle Alerts & Threshold Triggers",
                font_size=1.3 if is_mobile else 1.8,
                font_weight="bold",
                fill=COLOR_TEXT_PRIMARY,
            ),
            rio.Text(
                "Configure automated rules triggered by percentage moves relative to reference High or bucket shifts",
                font_size=0.78 if is_mobile else 0.95,
                fill=COLOR_TEXT_MUTED,
            ),
            spacing=0.08,
            margin_x=0.4 if is_mobile else 1.2,
            margin_top=0.2,
            align_x=0.0,
            grow_x=True,
        )

        # Quick Preset Buttons Row
        presets_row = rio.FlowContainer(
            rio.Text("Quick Trigger Presets:", font_weight="bold", font_size=0.82 if is_mobile else 0.9, fill=COLOR_TEXT_MUTED, align_y=0.5),
            rio.Button(
                "Downside -5% Alert",
                shape="rounded",
                style="minor",
                color="neutral",
                min_height=2.0,
                on_press=lambda: self._apply_preset("PERCENTAGE_BELOW", "-5.0"),
            ),
            rio.Button(
                "Downside -10% Alert",
                shape="rounded",
                style="minor",
                color="neutral",
                min_height=2.0,
                on_press=lambda: self._apply_preset("PERCENTAGE_BELOW", "-10.0"),
            ),
            rio.Button(
                "Upside +10% Breakout",
                shape="rounded",
                style="minor",
                color="neutral",
                min_height=2.0,
                on_press=lambda: self._apply_preset("PERCENTAGE_ABOVE", "10.0"),
            ),
            rio.Button(
                "Upside +15% Surge",
                shape="rounded",
                style="minor",
                color="neutral",
                min_height=2.0,
                on_press=lambda: self._apply_preset("PERCENTAGE_ABOVE", "15.0"),
            ),
            spacing=0.4,
            row_spacing=0.25,
            column_spacing=0.4,
            align_y=0.5,
            grow_x=True,
        )

        # Left-aligned Section Title Row
        form_title_row = rio.Row(
            rio.Icon(
                "material/add-alert",
                fill=rio.Color.from_hex("#3B82F6"),
                min_width=1.3 if is_mobile else 1.6,
                min_height=1.3 if is_mobile else 1.6,
            ),
            rio.Column(
                rio.Text(
                    "Create Real-Time Alert Rule",
                    font_size=1.0 if is_mobile else 1.2,
                    font_weight="bold",
                    fill=COLOR_TEXT_PRIMARY,
                ),
                rio.Text(
                    "Set triggers for percentage moves with debounced stock selection",
                    font_size=0.75 if is_mobile else 0.85,
                    fill=COLOR_TEXT_MUTED,
                ),
                spacing=0.02,
                align_x=0.0,
            ),
            spacing=0.4 if is_mobile else 0.5,
            align_y=0.5,
            align_x=0.0,
            grow_x=False,
        )

        # Create Alert Card Form Inputs
        form_inputs: rio.Component
        if is_mobile:
            form_inputs = rio.Column(
                StockAutocompleteInput(
                    label="Stock Symbol / Name (e.g. RELIANCE)",
                    text=self.stock_input,
                    on_select=self._on_stock_selected,
                    grow_x=True,
                ),
                rio.Row(
                    rio.TextInput(
                        label="Cycle #",
                        text=self.bind().cycle_num_input,
                        min_width=4.0,
                        grow_x=True,
                    ),
                    rio.TextInput(
                        label="Threshold (%)",
                        text=self.bind().threshold_input,
                        min_width=6.0,
                        grow_x=True,
                    ),
                    spacing=0.3,
                    grow_x=True,
                ),
                rio.Dropdown(
                    options=[
                        "PERCENTAGE_BELOW",
                        "PERCENTAGE_ABOVE",
                        "BUCKET_MATCH",
                        "REF_HIGH_CROSSED",
                    ],
                    selected_value=self.bind().condition_type_input,
                    label="Condition Type",
                ),
                rio.Button(
                    "Save Alert Rule",
                    icon="material/notifications-active",
                    shape="rounded",
                    style="major",
                    color="primary",
                    min_height=2.2,
                    grow_x=True,
                    on_press=self._on_add_alert,
                ),
                spacing=0.35,
                grow_x=True,
            )
        else:
            form_inputs = rio.Row(
                StockAutocompleteInput(
                    label="Stock Symbol (e.g. RELIANCE)",
                    text=self.stock_input,
                    on_select=self._on_stock_selected,
                    grow_x=True,
                ),
                rio.TextInput(
                    label="Cycle #",
                    text=self.bind().cycle_num_input,
                    min_width=5.0,
                ),
                rio.Dropdown(
                    options=[
                        "PERCENTAGE_BELOW",
                        "PERCENTAGE_ABOVE",
                        "BUCKET_MATCH",
                        "REF_HIGH_CROSSED",
                    ],
                    selected_value=self.bind().condition_type_input,
                    label="Condition Type",
                ),
                rio.TextInput(
                    label="Threshold (%)",
                    text=self.bind().threshold_input,
                    min_width=8.0,
                ),
                rio.Button(
                    "Save Alert Rule",
                    icon="material/notifications-active",
                    shape="rounded",
                    style="major",
                    color="primary",
                    min_height=2.6,
                    min_width=11.0,
                    on_press=self._on_add_alert,
                ),
                spacing=0.6,
                align_y=0.5,
                grow_x=True,
            )

        form_card = rio.Card(
            rio.Column(
                form_title_row,
                rio.Separator(),
                presets_row,
                form_inputs,
                rio.Text(
                    self.status_message,
                    font_size=0.82 if is_mobile else 0.92,
                    font_weight="bold",
                    fill=COLOR_UP_STRONG if "successfully" in self.status_message.lower() or "applied" in self.status_message.lower() else rio.Color.from_hex("#3B82F6"),
                ) if self.status_message else rio.Spacer(),
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

        # Triggered Events Banner (Strict left-alignment)
        triggered_cards: list[rio.Component] = []
        if triggered_events:
            triggered_cards.append(
                rio.Text(
                    "Currently Triggered Alert Events",
                    font_size=1.1 if is_mobile else 1.3,
                    font_weight="bold",
                    fill=COLOR_DOWN_STRONG,
                    margin_x=0.4 if is_mobile else 1.2,
                    margin_top=0.4,
                )
            )
            for evt in triggered_events:
                triggered_cards.append(
                    rio.Card(
                        rio.Row(
                            rio.Icon(
                                "material/warning",
                                fill=COLOR_DOWN_STRONG,
                                min_width=1.3 if is_mobile else 1.6,
                                min_height=1.3 if is_mobile else 1.6,
                            ),
                            rio.Column(
                                rio.Text(
                                    f"{evt.stock_symbol} (Cycle {evt.cycle_number}) — {evt.condition_summary}",
                                    font_weight="bold",
                                    font_size=0.9 if is_mobile else 1.05,
                                    fill=COLOR_TEXT_PRIMARY,
                                ),
                                rio.Text(
                                    f"Current Value: {evt.current_value} | Triggered: {evt.triggered_at.strftime('%Y-%m-%d %H:%M')}",
                                    font_size=0.75 if is_mobile else 0.85,
                                    fill=COLOR_TEXT_MUTED,
                                ),
                                spacing=0.03,
                                align_x=0.0,
                            ),
                            spacing=0.4 if is_mobile else 0.6,
                            align_y=0.5,
                            align_x=0.0,
                            margin=0.6 if is_mobile else 0.9,
                            grow_x=False,
                        ),
                        corner_radius=0.4,
                        color="hud",
                        margin_x=0.4 if is_mobile else 1.2,
                        grow_x=True,
                    )
                )

        # Configured Alerts List
        alert_rows: list[rio.Component] = []
        alert_rows.append(
            rio.Text(
                "Configured Alert Rules",
                font_size=1.1 if is_mobile else 1.35,
                font_weight="bold",
                fill=COLOR_TEXT_PRIMARY,
                margin_x=0.4 if is_mobile else 1.2,
                margin_top=0.4,
            )
        )

        if not alerts:
            alert_rows.append(
                rio.Card(
                    rio.Column(
                        rio.Icon("material/notifications-off", min_width=2.4, min_height=2.4, fill=COLOR_TEXT_DIM),
                        rio.Text("No active alert rules configured yet.", font_size=0.9 if is_mobile else 1.05, fill=COLOR_TEXT_MUTED),
                        spacing=0.2,
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
            for alt in alerts:
                alt_id = alt.id
                is_en = alt.is_enabled

                cycle_badge = rio.Card(
                    rio.Text(f"Cycle {alt.cycle_number}", font_size=0.72, font_weight="bold", fill=rio.Color.from_hex("#60A5FA"), margin_x=0.4, margin_y=0.1),
                    corner_radius=0.25,
                    color="hud",
                    grow_x=False,
                    grow_y=False,
                    align_x=0.0,
                    align_y=0.5,
                )
                status_badge = rio.Card(
                    rio.Text(
                        "ACTIVE" if alt.is_enabled else "PAUSED",
                        font_size=0.7,
                        font_weight="bold",
                        fill=COLOR_UP_STRONG if alt.is_enabled else COLOR_TEXT_DIM,
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

                if is_mobile:
                    row_content = rio.Column(
                        rio.Row(
                            rio.Row(
                                rio.Text(alt.stock_symbol, font_weight="bold", font_size=1.05, fill=COLOR_TEXT_PRIMARY),
                                cycle_badge,
                                status_badge,
                                spacing=0.25,
                                align_y=0.5,
                                align_x=0.0,
                                grow_x=False,
                            ),
                            align_y=0.5,
                            grow_x=True,
                        ),
                        rio.Text(f"Condition: {alt.condition_type.value} ({alt.threshold_value}%)", font_size=0.75, fill=COLOR_TEXT_MUTED),
                        rio.Row(
                            rio.Button(
                                "Pause" if is_en else "Resume",
                                shape="rounded",
                                style="minor",
                                color="warning" if is_en else "primary",
                                min_height=2.0,
                                grow_x=True,
                                on_press=lambda aid=alt_id, st=is_en: self._on_toggle_alert(aid, st),
                            ),
                            rio.Button(
                                "Delete",
                                icon="material/delete",
                                shape="rounded",
                                style="plain-text",
                                color="danger",
                                min_height=2.0,
                                grow_x=True,
                                on_press=lambda aid=alt_id: self._on_delete_alert(aid),
                            ),
                            spacing=0.3,
                            grow_x=True,
                        ),
                        spacing=0.25,
                        margin=0.5,
                        grow_x=True,
                    )
                else:
                    row_content = rio.Row(
                        rio.Column(
                            rio.Row(
                                rio.Text(alt.stock_symbol, font_weight="bold", font_size=1.2, fill=COLOR_TEXT_PRIMARY),
                                cycle_badge,
                                status_badge,
                                spacing=0.4,
                                align_y=0.5,
                                align_x=0.0,
                                grow_x=False,
                            ),
                            rio.Text(f"Condition: {alt.condition_type.value} ({alt.threshold_value}%)", font_size=0.88, fill=COLOR_TEXT_MUTED),
                            spacing=0.04,
                            align_x=0.0,
                        ),
                        rio.Spacer(),
                        rio.Row(
                            rio.Button(
                                "Pause Rule" if is_en else "Resume Rule",
                                shape="rounded",
                                style="minor",
                                color="warning" if is_en else "primary",
                                min_height=2.4,
                                on_press=lambda aid=alt_id, st=is_en: self._on_toggle_alert(aid, st),
                            ),
                            rio.Button(
                                "Delete",
                                icon="material/delete",
                                shape="rounded",
                                style="plain-text",
                                color="danger",
                                min_height=2.4,
                                on_press=lambda aid=alt_id: self._on_delete_alert(aid),
                            ),
                            spacing=0.4,
                            align_y=0.5,
                        ),
                        spacing=0.6,
                        align_y=0.5,
                        margin_x=0.8,
                        margin_y=0.4,
                        grow_x=True,
                    )

                alert_rows.append(
                    rio.Card(
                        row_content,
                        corner_radius=0.4,
                        color="neutral",
                        margin_x=0.4 if is_mobile else 1.2,
                        grow_x=True,
                    )
                )

        return rio.Column(
            header,
            form_card,
            *triggered_cards,
            *alert_rows,
            spacing=0.6 if is_mobile else 0.8,
            grow_x=True,
            margin_bottom=1.5,
        )
