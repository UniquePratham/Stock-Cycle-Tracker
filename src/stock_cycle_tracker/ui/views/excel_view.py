"""Excel Import and Export view component with native file upload, Google Docs URL support, and zero-overflow mobile styling."""

from __future__ import annotations

from datetime import date
import io
from pathlib import Path
from typing import Callable, Optional

import rio

from stock_cycle_tracker.services.excel_service import ExcelImportResult
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


class ExcelView(rio.Component):
    """Handles bulk Excel file upload via browser picker, Google Sheets link ingestion, and analytical export."""

    on_navigate: Callable[[str, Optional[str]], None]
    url_input: str = ""
    file_path_input: str = "sample_stocks.xlsx"
    uploaded_file_name: str = ""
    validation_result: Optional[ExcelImportResult] = None
    status_message: str = ""
    export_message: str = ""

    async def _on_pick_file(self) -> None:
        try:
            file_info = await self.session.pick_file(file_types=[".xlsx", ".xls"])
            if not file_info:
                return

            raw_bytes = file_info.read_bytes()
            self.uploaded_file_name = file_info.name
            container = ServiceContainer.get()
            self.validation_result = container.excel_service.validate_and_parse_upload(raw_bytes)
            self.status_message = f"Uploaded '{self.uploaded_file_name}': Parsed {self.validation_result.total_rows} rows ({len(self.validation_result.valid_rows)} valid, {len(self.validation_result.invalid_rows)} errors)."
        except Exception as e:
            self.status_message = f"Upload cancelled or failed: {e}"

    def _on_import_from_url(self) -> None:
        url_str = self.url_input.strip()
        if not url_str:
            self.status_message = "Please paste a Google Sheets share link or XLSX URL."
            return

        container = ServiceContainer.get()
        self.validation_result = container.excel_service.validate_and_parse_url(url_str)
        if self.validation_result.warnings and not self.validation_result.valid_rows:
            self.status_message = f"Error: {self.validation_result.warnings[0]}"
        else:
            self.status_message = f"Fetched from URL: Parsed {self.validation_result.total_rows} rows ({len(self.validation_result.valid_rows)} valid, {len(self.validation_result.invalid_rows)} errors)."

    def _on_use_sample_path(self) -> None:
        p = Path("sample_stocks.xlsx")
        if not p.exists():
            self.status_message = "sample_stocks.xlsx not found."
            return

        container = ServiceContainer.get()
        self.validation_result = container.excel_service.validate_and_parse_upload(p)
        self.status_message = f"Parsed demo sample: {self.validation_result.total_rows} rows ({len(self.validation_result.valid_rows)} valid, {len(self.validation_result.invalid_rows)} errors)."

    def _on_confirm_import(self) -> None:
        if not self.validation_result or not self.validation_result.valid_rows:
            self.status_message = "No valid rows to import."
            return

        container = ServiceContainer.get()
        imported, analyses = container.excel_service.import_validated_rows(
            container.cycle_service,
            self.validation_result.valid_rows,
        )
        self.status_message = f"Successfully imported {imported} stock research cycles into the database!"
        self.validation_result = None
        self.uploaded_file_name = ""
        self.url_input = ""

    def _on_export_excel(self) -> None:
        container = ServiceContainer.get()
        analyses = container.cycle_service.get_dashboard_analyses()
        if not analyses:
            self.export_message = "No active cycles to export. Database is currently empty."
            return

        out_path = Path("Stock_Cycle_Analysis_Export.xlsx")
        container.excel_service.export_analyses_to_excel(analyses, out_path)
        self.export_message = f"Export generated: {out_path.resolve()}"

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 55.0
        container = ServiceContainer.get()
        all_cycles = container.repository.list_all_cycles()
        total_cycles_count = len(all_cycles)

        # Header Title
        header = rio.FlowContainer(
            rio.Column(
                rio.Text(
                    "Excel Ingestion & Export",
                    font_size=1.3 if is_mobile else 1.6,
                    font_weight="bold",
                    fill=COLOR_TEXT_PRIMARY,
                ),
                rio.Text(
                    "Upload spreadsheet, import Google Sheets link, or export full report",
                    font_size=0.78 if is_mobile else 0.88,
                    fill=COLOR_TEXT_MUTED,
                ),
                spacing=0.1,
            ),
            spacing=1.0,
            align_y=0.5,
            margin_x=0.6 if is_mobile else 1.2,
            margin_top=0.2,
            grow_x=True,
        )

        # Ingestion Card
        upload_card = rio.Card(
            rio.Column(
                rio.Row(
                    rio.Icon("material/upload-file", fill=rio.Color.from_hex("#3B82F6"), min_width=1.2 if is_mobile else 1.4, min_height=1.2 if is_mobile else 1.4),
                    rio.Column(
                        rio.Text("Bulk Ingest Research Dates", font_size=0.95 if is_mobile else 1.1, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                        rio.Text("Required: 'Stock Name' and 'Reference Date'", font_size=0.72 if is_mobile else 0.8, fill=COLOR_TEXT_MUTED),
                        spacing=0.03,
                    ),
                    spacing=0.4 if is_mobile else 0.6,
                    align_y=0.5,
                ),
                rio.Separator(),
                # Method A: Direct File Upload
                rio.FlowContainer(
                    rio.Button(
                        "Upload .xlsx File from Device",
                        icon="material/upload-file",
                        shape="rounded",
                        style="major",
                        color="primary",
                        min_height=2.2,
                        grow_x=is_mobile,
                        on_press=self._on_pick_file,
                    ),
                    rio.Button(
                        "Load Built-in Sample File",
                        icon="material/table-view",
                        shape="rounded",
                        style="minor",
                        color="neutral",
                        min_height=2.2,
                        grow_x=is_mobile,
                        on_press=self._on_use_sample_path,
                    ),
                    spacing=0.4 if is_mobile else 0.6,
                    row_spacing=0.3 if is_mobile else 0.4,
                    column_spacing=0.4 if is_mobile else 0.6,
                    justify="left",
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Text(
                    f"Selected: {self.uploaded_file_name}" if self.uploaded_file_name else "No file uploaded yet",
                    font_size=0.78 if is_mobile else 0.85,
                    fill=COLOR_UP_STRONG if self.uploaded_file_name else COLOR_TEXT_DIM,
                ),
                # Method B: Google Docs / Sheets URL Ingestion
                rio.FlowContainer(
                    rio.TextInput(
                        label="Google Sheets Share Link / XLSX URL",
                        text=self.bind().url_input,
                        min_width=12.0 if is_mobile else 16.0,
                        grow_x=True,
                    ),
                    rio.Button(
                        "Import from Link",
                        icon="material/check-circle",
                        shape="rounded",
                        style="major",
                        color="primary",
                        min_height=2.2,
                        grow_x=is_mobile,
                        on_press=self._on_import_from_url,
                    ),
                    spacing=0.4 if is_mobile else 0.6,
                    row_spacing=0.3 if is_mobile else 0.4,
                    column_spacing=0.4 if is_mobile else 0.6,
                    justify="left",
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Text(
                    self.status_message,
                    font_size=0.8,
                    font_weight="bold",
                    fill=COLOR_UP_STRONG if "successfully" in self.status_message.lower() or "parsed" in self.status_message.lower() else rio.Color.from_hex("#3B82F6"),
                ) if self.status_message else rio.Spacer(),
                spacing=0.4 if is_mobile else 0.6,
                margin=0.6 if is_mobile else 1.0,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            margin_x=0.6 if is_mobile else 1.2,
            grow_x=True,
        )

        # Validation Diagnostics
        validation_components: list[rio.Component] = []
        if self.validation_result:
            if self.validation_result.invalid_rows:
                err_rows = []
                for err in self.validation_result.invalid_rows:
                    err_rows.append(
                        rio.FlowContainer(
                            rio.Text(f"Row {err.row_index}", font_weight="bold", font_size=0.8, fill=COLOR_TEXT_PRIMARY),
                            rio.Text(f"Stock: {err.raw_stock}", font_size=0.8, fill=COLOR_TEXT_MUTED),
                            rio.Text(f"Date: {err.raw_date}", font_size=0.8, fill=COLOR_TEXT_MUTED),
                            rio.Text(err.error_message, font_size=0.8, fill=COLOR_DOWN_STRONG),
                            spacing=0.4,
                            row_spacing=0.2,
                            column_spacing=0.4,
                            grow_x=True,
                        )
                    )
                validation_components.append(
                    rio.Card(
                        rio.Column(
                            rio.Text("Validation Diagnostics & Errors", font_weight="bold", font_size=0.85, fill=COLOR_DOWN_STRONG),
                            *err_rows,
                            spacing=0.3,
                            margin=0.6,
                            grow_x=True,
                        ),
                        corner_radius=0.4,
                        color="hud",
                        margin_x=0.6 if is_mobile else 1.2,
                        grow_x=True,
                    )
                )

            if self.validation_result.valid_rows:
                validation_components.append(
                    rio.Card(
                        rio.FlowContainer(
                            rio.Column(
                                rio.Text(f"Found {len(self.validation_result.valid_rows)} valid cycle records ready for import.", font_weight="bold", font_size=0.85, fill=COLOR_UP_STRONG),
                                rio.Text("All tickers and historical dates verified.", font_size=0.72, fill=COLOR_TEXT_DIM),
                                spacing=0.03,
                            ),
                            rio.Button(
                                "Confirm Import to Database",
                                icon="material/file-download-done",
                                shape="rounded",
                                style="major",
                                color="success",
                                min_height=2.2,
                                grow_x=is_mobile,
                                on_press=self._on_confirm_import,
                            ),
                            spacing=0.6,
                            row_spacing=0.3,
                            column_spacing=0.6,
                            justify="justify",
                            align_y=0.5,
                            margin=0.6,
                            grow_x=True,
                        ),
                        corner_radius=0.4,
                        color="neutral",
                        margin_x=0.6 if is_mobile else 1.2,
                        grow_x=True,
                    )
                )

        # Section 2: Export Analytical Report Card
        export_card = rio.Card(
            rio.Column(
                rio.Row(
                    rio.Icon("material/download", fill=COLOR_UP_STRONG, min_width=1.2 if is_mobile else 1.4, min_height=1.2 if is_mobile else 1.4),
                    rio.Column(
                        rio.Text("Institutional Analytical Export", font_size=0.95 if is_mobile else 1.1, font_weight="bold", fill=COLOR_TEXT_PRIMARY),
                        rio.Text("Generates complete 18-column Excel workbook report", font_size=0.72 if is_mobile else 0.8, fill=COLOR_TEXT_MUTED),
                        spacing=0.03,
                    ),
                    spacing=0.4 if is_mobile else 0.6,
                    align_y=0.5,
                ),
                rio.FlowContainer(
                    rio.Card(
                        rio.Text(f"Cycles Available: {total_cycles_count}", font_size=0.75, font_weight="bold", fill=COLOR_TEXT_PRIMARY, margin_x=0.4, margin_y=0.15),
                        corner_radius=0.25,
                        color="hud",
                    ),
                    rio.Card(
                        rio.Text("Format: .xlsx (18 Cols)", font_size=0.75, font_weight="bold", fill=COLOR_TEXT_MUTED, margin_x=0.4, margin_y=0.15),
                        corner_radius=0.25,
                        color="hud",
                    ),
                    rio.Button(
                        "Generate Export",
                        icon="material/download",
                        shape="rounded",
                        style="major",
                        color="success",
                        min_height=2.2,
                        grow_x=is_mobile,
                        on_press=self._on_export_excel,
                    ),
                    spacing=0.4 if is_mobile else 0.6,
                    row_spacing=0.3 if is_mobile else 0.4,
                    column_spacing=0.4 if is_mobile else 0.6,
                    justify="justify",
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Text(
                    self.export_message,
                    font_size=0.8,
                    font_weight="bold",
                    fill=COLOR_UP_STRONG,
                ) if self.export_message else rio.Spacer(),
                spacing=0.4 if is_mobile else 0.6,
                margin=0.6 if is_mobile else 1.0,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            margin_x=0.6 if is_mobile else 1.2,
            grow_x=True,
        )

        return rio.Column(
            header,
            upload_card,
            *validation_components,
            export_card,
            spacing=0.6 if is_mobile else 0.8,
            grow_x=True,
            margin_bottom=1.5,
        )
