"""Excel Ingestion and Export view component with 2-column widescreen desktop layout, Top-5 live preview, and adaptive light/dark typography."""

from __future__ import annotations

from datetime import date
import io
from pathlib import Path
from typing import Callable, Optional

import pandas as pd
import rio

from stock_cycle_tracker.services.excel_service import ExcelImportResult
from stock_cycle_tracker.ui.state import ServiceContainer
from stock_cycle_tracker.ui.theme import (
    COLOR_BORDER,
    COLOR_DOWN_STRONG,
    COLOR_SURFACE_CARD,
    COLOR_TEXT_DIM,
    COLOR_TEXT_MUTED,
    COLOR_UP_STRONG,
)


class ExcelView(rio.Component):
    """Handles bulk Excel file upload via browser picker, Google Sheets link ingestion, Top-5 data preview, and analytical export."""

    on_navigate: Callable[[str, Optional[str]], None]
    url_input: str = ""
    file_path_input: str = "sample_stocks.xlsx"
    uploaded_file_name: str = ""
    validation_result: Optional[ExcelImportResult] = None
    status_message: str = ""
    export_message: str = ""
    is_exporting: bool = False

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
            self.uploaded_file_name = "Google_Sheets_Import.xlsx"
            self.status_message = f"Fetched from URL: Parsed {self.validation_result.total_rows} rows ({len(self.validation_result.valid_rows)} valid, {len(self.validation_result.invalid_rows)} errors)."

    def _on_use_sample_path(self) -> None:
        p = Path("sample_stocks.xlsx")
        if not p.exists():
            self.status_message = "sample_stocks.xlsx not found."
            return

        container = ServiceContainer.get()
        self.uploaded_file_name = "sample_stocks.xlsx"
        self.validation_result = container.excel_service.validate_and_parse_upload(p)
        self.status_message = f"Parsed demo sample: {self.validation_result.total_rows} rows ({len(self.validation_result.valid_rows)} valid, {len(self.validation_result.invalid_rows)} errors)."

    async def _on_download_template(self) -> None:
        """Generates a clean pre-formatted Excel template and triggers download."""
        df = pd.DataFrame([
            {"Stock Name": "RELIANCE", "Reference Date": "10-Jan-2014"},
            {"Stock Name": "TCS", "Reference Date": "30-Jan-2016"},
            {"Stock Name": "INFY", "Reference Date": "15-Jul-2019"},
            {"Stock Name": "HDFCBANK", "Reference Date": "12-Apr-2018"},
            {"Stock Name": "ICICIBANK", "Reference Date": "05-May-2017"},
            {"Stock Name": "SBIN", "Reference Date": "20-Nov-2015"},
        ])
        bio = io.BytesIO()
        with pd.ExcelWriter(bio, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Stock_Cycles")
        content_bytes = bio.getvalue()

        await self.session.save_file(
            file_contents=content_bytes,
            file_name="Stock_Cycle_Template.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.status_message = "Sample Excel template downloaded to your device!"

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

    async def _on_export_excel(self) -> None:
        self.is_exporting = True
        self.export_message = "Generating Excel report..."

        container = ServiceContainer.get()
        analyses = container.cycle_service.get_dashboard_analyses()
        if not analyses:
            self.export_message = "No active cycles to export. Database is currently empty."
            self.is_exporting = False
            return

        try:
            content_bytes = container.excel_service.export_analyses_to_excel(analyses)
            await self.session.save_file(
                file_contents=content_bytes,
                file_name="Stock_Cycle_Analysis_Export.xlsx",
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            self.export_message = "Excel report generated and downloaded to your device!"
        except Exception as e:
            self.export_message = f"Export failed: {e}"
        finally:
            self.is_exporting = False

    def build(self) -> rio.Component:
        is_mobile = self.session.window_width < 50.0
        container = ServiceContainer.get()
        all_cycles = container.repository.list_all_cycles()
        total_cycles_count = len(all_cycles)
        unique_stocks_count = len(set(s.symbol for s, _ in all_cycles))

        # Page Header
        header = rio.Column(
            rio.Text(
                "Excel Ingestion & Analytical Reporting",
                font_size=1.3 if is_mobile else 1.7,
                font_weight="bold",
            ),
            rio.Text(
                "Upload bulk research portfolios, ingest from Google Sheets, preview top rows, or download reports",
                font_size=0.78 if is_mobile else 0.9,
                fill=COLOR_TEXT_MUTED,
            ),
            spacing=0.06,
            margin_x=0.4 if is_mobile else 1.2,
            margin_top=0.2,
            align_x=0.0,
            grow_x=True,
        )

        # ---------------- LEFT COLUMN: Ingestion & Live Top-5 Preview ----------------
        ingest_title_row = rio.Row(
            rio.Icon(
                "material/upload-file",
                fill=rio.Color.from_hex("#3B82F6"),
                min_width=1.3 if is_mobile else 1.5,
                min_height=1.3 if is_mobile else 1.5,
            ),
            rio.Column(
                rio.Text(
                    "Bulk Ingest Research Dates (.xlsx / Google Sheets)",
                    font_size=1.0 if is_mobile else 1.15,
                    font_weight="bold",
                ),
                rio.Text(
                    "Required columns: 'Stock Name' and 'Reference Date' (e.g. 10-Jan-2014)",
                    font_size=0.75 if is_mobile else 0.82,
                    fill=COLOR_TEXT_MUTED,
                ),
                spacing=0.02,
                align_x=0.0,
            ),
            spacing=0.4,
            align_y=0.5,
            align_x=0.0,
            grow_x=False,
        )

        upload_card = rio.Card(
            rio.Column(
                ingest_title_row,
                rio.Separator(),
                # Action Buttons Row
                rio.FlowContainer(
                    rio.Button(
                        "Upload .xlsx File",
                        icon="material/upload-file",
                        shape="rounded",
                        style="major",
                        color="primary",
                        min_height=2.2 if is_mobile else 2.5,
                        grow_x=is_mobile,
                        on_press=self._on_pick_file,
                    ),
                    rio.Button(
                        "Download Blank Template",
                        icon="material/description",
                        shape="rounded",
                        style="minor",
                        color="primary",
                        min_height=2.2 if is_mobile else 2.5,
                        grow_x=is_mobile,
                        on_press=self._on_download_template,
                    ),
                    rio.Button(
                        "Load Built-in Sample",
                        icon="material/table-view",
                        shape="rounded",
                        style="minor",
                        color="neutral",
                        min_height=2.2 if is_mobile else 2.5,
                        grow_x=is_mobile,
                        on_press=self._on_use_sample_path,
                    ),
                    spacing=0.4,
                    row_spacing=0.3,
                    column_spacing=0.4,
                    justify="left",
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Text(
                    f"Selected File: {self.uploaded_file_name}" if self.uploaded_file_name else "No file selected yet",
                    font_size=0.8 if is_mobile else 0.85,
                    fill=COLOR_UP_STRONG if self.uploaded_file_name else COLOR_TEXT_DIM,
                ),
                # Google Docs / Sheets URL Ingestion
                rio.FlowContainer(
                    rio.TextInput(
                        label="Google Sheets Public Share Link / XLSX URL",
                        text=self.bind().url_input,
                        min_width=12.0 if is_mobile else 18.0,
                        grow_x=True,
                    ),
                    rio.Button(
                        "Import from Link",
                        icon="material/check-circle",
                        shape="rounded",
                        style="major",
                        color="primary",
                        min_height=2.2 if is_mobile else 2.5,
                        grow_x=is_mobile,
                        on_press=self._on_import_from_url,
                    ),
                    spacing=0.4,
                    row_spacing=0.3,
                    column_spacing=0.4,
                    justify="left",
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Text(
                    self.status_message,
                    font_size=0.82 if is_mobile else 0.88,
                    font_weight="bold",
                    fill=COLOR_UP_STRONG if "successfully" in self.status_message.lower() or "parsed" in self.status_message.lower() or "downloaded" in self.status_message.lower() else rio.Color.from_hex("#3B82F6"),
                ) if self.status_message else rio.Spacer(),
                spacing=0.4 if is_mobile else 0.55,
                margin=0.6 if is_mobile else 0.8,
                align_x=0.0,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            grow_x=True,
        )

        # Top 5 Data Preview Card
        preview_rows: list[rio.Component] = []

        if self.validation_result and self.validation_result.valid_rows:
            # Header Row
            preview_rows.append(
                rio.Row(
                    rio.Text("#", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=2.5),
                    rio.Text("STOCK SYMBOL", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=9.0),
                    rio.Text("RESEARCH DATE", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=9.0),
                    rio.Text("STATUS", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=7.0),
                    spacing=0.4,
                    align_y=0.5,
                    margin_x=0.5,
                    margin_y=0.2,
                )
            )
            top_5 = self.validation_result.valid_rows[:5]
            for idx, r in enumerate(top_5, start=1):
                preview_rows.append(
                    rio.Card(
                        rio.Row(
                            rio.Text(str(idx), font_weight="bold", font_size=0.82, fill=COLOR_TEXT_MUTED, min_width=2.5),
                            rio.Text(r.stock_name, font_weight="bold", font_size=0.88, min_width=9.0),
                            rio.Text(r.reference_date.strftime("%d-%b-%Y"), font_size=0.85, min_width=9.0),
                            rio.Card(
                                rio.Text("Ready to Import", font_size=0.68, font_weight="bold", fill=COLOR_UP_STRONG, margin_x=0.35, margin_y=0.1),
                                corner_radius=0.25,
                                color="neutral",
                                min_width=7.0,
                            ),
                            spacing=0.4,
                            align_y=0.5,
                            margin_x=0.5,
                            margin_y=0.25,
                        ),
                        corner_radius=0.3,
                        color="hud",
                        grow_x=True,
                    )
                )

            # Confirm Action Button
            confirm_btn_row = rio.Row(
                rio.Text(
                    f"Showing top {len(top_5)} of {len(self.validation_result.valid_rows)} valid records",
                    font_size=0.78,
                    fill=COLOR_TEXT_MUTED,
                    align_y=0.5,
                ),
                rio.Spacer(),
                rio.Button(
                    f"Confirm Import ({len(self.validation_result.valid_rows)} Records)",
                    icon="material/file-download-done",
                    shape="rounded",
                    style="major",
                    color="success",
                    min_height=2.3,
                    on_press=self._on_confirm_import,
                ),
                align_y=0.5,
                grow_x=True,
            )
            preview_rows.append(confirm_btn_row)

        elif self.validation_result and self.validation_result.invalid_rows and not self.validation_result.valid_rows:
            preview_rows.append(
                rio.Text("All uploaded rows contained formatting or ticker errors. See diagnostics below.", font_size=0.85, fill=COLOR_DOWN_STRONG)
            )
        else:
            # Placeholder Sample Preview
            preview_rows.append(
                rio.Row(
                    rio.Text("#", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=2.5),
                    rio.Text("STOCK SYMBOL", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=9.0),
                    rio.Text("SAMPLE DATE", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=9.0),
                    rio.Text("FORMAT STATUS", font_weight="bold", font_size=0.78, fill=COLOR_TEXT_MUTED, min_width=7.0),
                    spacing=0.4,
                    align_y=0.5,
                    margin_x=0.5,
                    margin_y=0.2,
                )
            )
            mock_samples = [
                ("1", "RELIANCE", "10-Jan-2014"),
                ("2", "TCS", "30-Jan-2016"),
                ("3", "INFY", "15-Jul-2019"),
                ("4", "HDFCBANK", "12-Apr-2018"),
                ("5", "ICICIBANK", "05-May-2017"),
            ]
            for num, sym, sdate in mock_samples:
                preview_rows.append(
                    rio.Card(
                        rio.Row(
                            rio.Text(num, font_weight="bold", font_size=0.82, fill=COLOR_TEXT_MUTED, min_width=2.5),
                            rio.Text(sym, font_weight="bold", font_size=0.88, min_width=9.0),
                            rio.Text(sdate, font_size=0.85, min_width=9.0),
                            rio.Card(
                                rio.Text("Sample Schema", font_size=0.68, font_weight="bold", fill=COLOR_TEXT_DIM, margin_x=0.35, margin_y=0.1),
                                corner_radius=0.25,
                                color="neutral",
                                min_width=7.0,
                            ),
                            spacing=0.4,
                            align_y=0.5,
                            margin_x=0.5,
                            margin_y=0.2,
                        ),
                        corner_radius=0.3,
                        color="hud",
                        grow_x=True,
                    )
                )

        preview_card = rio.Card(
            rio.Column(
                rio.Row(
                    rio.Icon("material/preview", fill=rio.Color.from_hex("#3B82F6"), min_width=1.3, min_height=1.3),
                    rio.Text(
                        "Top 5 Uploaded Data Preview" if self.validation_result else "Spreadsheet Structure Preview (Top 5 Sample)",
                        font_size=0.98 if is_mobile else 1.1,
                        font_weight="bold",
                    ),
                    spacing=0.35,
                    align_y=0.5,
                ),
                rio.Separator(),
                *preview_rows,
                spacing=0.35,
                margin=0.6 if is_mobile else 0.8,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            grow_x=True,
        )

        left_column = rio.Column(
            upload_card,
            preview_card,
            spacing=0.5,
            grow_x=True,
        )

        # ---------------- RIGHT COLUMN: Export & Column Specifications ----------------
        export_title_row = rio.Row(
            rio.Icon(
                "material/download",
                fill=COLOR_UP_STRONG,
                min_width=1.3 if is_mobile else 1.5,
                min_height=1.3 if is_mobile else 1.5,
            ),
            rio.Column(
                rio.Text(
                    "Institutional Analytical Export",
                    font_size=1.0 if is_mobile else 1.15,
                    font_weight="bold",
                ),
                rio.Text(
                    "Generates complete 18-column Excel workbook with prices, modes, cycles, and buckets",
                    font_size=0.75 if is_mobile else 0.82,
                    fill=COLOR_TEXT_MUTED,
                ),
                spacing=0.02,
                align_x=0.0,
            ),
            spacing=0.4,
            align_y=0.5,
            align_x=0.0,
            grow_x=False,
        )

        export_card = rio.Card(
            rio.Column(
                export_title_row,
                rio.Separator(),
                rio.FlowContainer(
                    rio.Card(
                        rio.Text(
                            f"Portfolios: {unique_stocks_count}",
                            font_size=0.78 if is_mobile else 0.88,
                            font_weight="bold",
                            margin_x=0.45,
                            margin_y=0.18,
                        ),
                        corner_radius=0.3,
                        color="hud",
                    ),
                    rio.Card(
                        rio.Text(
                            f"Total Cycles: {total_cycles_count}",
                            font_size=0.78 if is_mobile else 0.88,
                            font_weight="bold",
                            margin_x=0.45,
                            margin_y=0.18,
                        ),
                        corner_radius=0.3,
                        color="hud",
                    ),
                    rio.Card(
                        rio.Text(
                            "Format: .xlsx (18 Cols)",
                            font_size=0.78 if is_mobile else 0.88,
                            font_weight="bold",
                            fill=COLOR_TEXT_MUTED,
                            margin_x=0.45,
                            margin_y=0.18,
                        ),
                        corner_radius=0.3,
                        color="hud",
                    ),
                    rio.Button(
                        "Download Excel Report",
                        icon="material/download",
                        shape="rounded",
                        style="major",
                        color="success",
                        min_height=2.2 if is_mobile else 2.5,
                        grow_x=is_mobile,
                        is_loading=self.is_exporting,
                        on_press=self._on_export_excel,
                    ),
                    spacing=0.4,
                    row_spacing=0.3,
                    column_spacing=0.4,
                    justify="left",
                    align_y=0.5,
                    grow_x=True,
                ),
                rio.Text(
                    self.export_message,
                    font_size=0.82 if is_mobile else 0.88,
                    font_weight="bold",
                    fill=COLOR_UP_STRONG if "downloaded" in self.export_message.lower() or "generated" in self.export_message.lower() else COLOR_DOWN_STRONG,
                ) if self.export_message else rio.Spacer(),
                spacing=0.4 if is_mobile else 0.55,
                margin=0.6 if is_mobile else 0.8,
                align_x=0.0,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            grow_x=True,
        )

        spec_card = rio.Card(
            rio.Column(
                rio.Row(
                    rio.Icon("material/info", fill=rio.Color.from_hex("#8B5CF6"), min_width=1.3 if is_mobile else 1.5, min_height=1.3 if is_mobile else 1.5),
                    rio.Column(
                        rio.Text("Spreadsheet Specifications & Recognized Columns", font_size=1.0 if is_mobile else 1.15, font_weight="bold"),
                        rio.Text("Intelligent column mapping automatically detects all common naming variations", font_size=0.75 if is_mobile else 0.82, fill=COLOR_TEXT_MUTED),
                        spacing=0.02,
                        align_x=0.0,
                    ),
                    spacing=0.4,
                    align_y=0.5,
                    align_x=0.0,
                    grow_x=False,
                ),
                rio.Separator(),
                rio.Column(
                    rio.Row(
                        rio.Text("Stock Columns:", font_weight="bold", font_size=0.82, fill=rio.Color.from_hex("#60A5FA"), min_width=9.0),
                        rio.Text("Stock Name, Symbol, Ticker, Company, Script", font_size=0.8, fill=COLOR_TEXT_MUTED),
                        spacing=0.3,
                        align_y=0.5,
                    ),
                    rio.Row(
                        rio.Text("Date Columns:", font_weight="bold", font_size=0.82, fill=rio.Color.from_hex("#34D399"), min_width=9.0),
                        rio.Text("Reference Date, Anchor Date, Research Date, LD, Date", font_size=0.8, fill=COLOR_TEXT_MUTED),
                        spacing=0.3,
                        align_y=0.5,
                    ),
                    rio.Row(
                        rio.Text("Date Formats:", font_weight="bold", font_size=0.82, fill=rio.Color.from_hex("#FBBF24"), min_width=9.0),
                        rio.Text("10-Jan-2014, 2014-01-10, 10/01/2014, 10.01.2014", font_size=0.8, fill=COLOR_TEXT_MUTED),
                        spacing=0.3,
                        align_y=0.5,
                    ),
                    spacing=0.3,
                    grow_x=True,
                ),
                spacing=0.4 if is_mobile else 0.55,
                margin=0.6 if is_mobile else 0.8,
                grow_x=True,
            ),
            corner_radius=0.5,
            color="neutral",
            grow_x=True,
        )

        right_column = rio.Column(
            export_card,
            spec_card,
            spacing=0.5,
            grow_x=True,
        )

        # Widescreen Responsive Layout (2-Column Grid on Desktop, Vertical Stack on Mobile)
        main_content: rio.Component
        if is_mobile:
            main_content = rio.Column(
                upload_card,
                preview_card,
                export_card,
                spec_card,
                spacing=0.5,
                margin_x=0.4,
                grow_x=True,
            )
        else:
            main_content = rio.Row(
                left_column,
                right_column,
                spacing=0.8,
                margin_x=1.2,
                grow_x=True,
            )

        return rio.Column(
            header,
            main_content,
            spacing=0.5 if is_mobile else 0.6,
            grow_x=True,
            margin_bottom=1.0,
        )
