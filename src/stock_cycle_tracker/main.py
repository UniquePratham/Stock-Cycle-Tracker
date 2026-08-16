"""Main entry point for Stock Cycle Tracker."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

from stock_cycle_tracker.services.cycle_service import CycleService
from stock_cycle_tracker.services.excel_service import ExcelService
from stock_cycle_tracker.ui.app import build_app
from stock_cycle_tracker.ui.state import ServiceContainer

# Configure UTF-8 on standard streams if available
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="stock-cycle-tracker",
        description="Research-driven Stock Cycle Tracker application in Python with Rio UI.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: run (Default / Launch UI)
    run_parser = subparsers.add_parser("run", help="Launch the Rio UI application server.")
    run_parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    run_parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    run_parser.add_argument("--db", default="stock_cycle_tracker.db", help="SQLite database path")

    # Command: calculate
    calc_parser = subparsers.add_parser("calculate", help="Calculate cycle analysis for a single stock.")
    calc_parser.add_argument("--stock", required=True, help="Stock symbol or query (e.g. RELIANCE)")
    calc_parser.add_argument("--date", required=True, help="Original research date (e.g. 2014-01-10)")
    calc_parser.add_argument("--db", default="stock_cycle_tracker.db", help="SQLite database path")

    # Command: import-excel
    import_parser = subparsers.add_parser("import-excel", help="Import research dates from an Excel file.")
    import_parser.add_argument("--file", required=True, help="Path to .xlsx file")
    import_parser.add_argument("--db", default="stock_cycle_tracker.db", help="SQLite database path")

    # Command: export-excel
    export_parser = subparsers.add_parser("export-excel", help="Export full 18-column calculation analysis to Excel.")
    export_parser.add_argument("--output", default="Stock_Cycle_Analysis_Export.xlsx", help="Output .xlsx file path")
    export_parser.add_argument("--db", default="stock_cycle_tracker.db", help="SQLite database path")

    args = parser.parse_args()

    cmd = args.command or "run"

    if cmd == "run":
        app = build_app(db_path=getattr(args, "db", "stock_cycle_tracker.db"))
        host = getattr(args, "host", "127.0.0.1")
        port = getattr(args, "port", 8000)
        print(f"Starting Stock Cycle Tracker on http://{host}:{port}")
        app.run_in_browser(host=host, port=port)
        return 0

    elif cmd == "calculate":
        container = ServiceContainer.get(db_path=args.db)
        parsed_dt = container.excel_service._parse_date(args.date)
        if not parsed_dt:
            print(f"Error: Invalid date format '{args.date}'", file=sys.stderr)
            return 1

        stock, cycle, analysis = container.cycle_service.add_stock_cycle(args.stock, parsed_dt)
        print("=" * 60)
        print(f"Stock:                  {analysis.stock_symbol} ({analysis.company_name})")
        print(f"Cycle:                  Cycle {analysis.cycle_number}")
        print(f"Original Research Date: {analysis.original_reference_date.strftime('%d-%b-%Y')}")
        print(f"Recurring Date:         {analysis.recurring_reference_date.strftime('%d-%b')}")
        print(f"Actual Trading Date:    {analysis.actual_reference_trading_date.strftime('%d-%b-%Y')}")
        print(f"Exchange:               {analysis.exchange}")
        print(f"Reference High:         INR {analysis.reference_high:,.2f}")
        print(f"Current Price:          INR {analysis.current_price:,.2f} ({analysis.price_type.value})")
        print(f"Percentage Change:      {analysis.percentage_change:+.2f}%")
        print(f"Bucket:                 {analysis.bucket}")
        print(f"Cycle Boundaries:       {analysis.cycle_start_date.strftime('%d-%b-%Y')} -> {analysis.cycle_end_date.strftime('%d-%b-%Y')}")
        print("=" * 60)
        return 0

    elif cmd == "import-excel":
        container = ServiceContainer.get(db_path=args.db)
        p = Path(args.file)
        if not p.exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            return 1

        res = container.excel_service.validate_and_parse_upload(p)
        print(f"Parsed {res.total_rows} rows: {len(res.valid_rows)} valid, {len(res.invalid_rows)} invalid.")
        for err in res.invalid_rows:
            print(f"  [Row {err.row_index}] {err.raw_stock} ({err.raw_date}): {err.error_message}", file=sys.stderr)

        if res.valid_rows:
            imported, analyses = container.excel_service.import_validated_rows(container.cycle_service, res.valid_rows)
            print(f"Successfully imported {imported} stock cycles!")
        return 0

    elif cmd == "export-excel":
        container = ServiceContainer.get(db_path=args.db)
        analyses = container.cycle_service.get_dashboard_analyses()
        if not analyses:
            print("No active cycles to export. Database is empty.")
            return 0

        out_path = Path(args.output)
        container.excel_service.export_analyses_to_excel(analyses, out_path)
        print(f"Exported {len(analyses)} cycles to {out_path.resolve()}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
