"""Turnkey launcher and runner for Stock Cycle Tracker."""

from __future__ import annotations

import argparse
from datetime import date
import os
from pathlib import Path
import sys

# Ensure package src directory is in sys.path
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from stock_cycle_tracker.domain.models import ExchangePreference
from stock_cycle_tracker.ui.app import build_app
from stock_cycle_tracker.ui.state import ServiceContainer


def seed_demo_data(db_path: str) -> None:
    """Pre-populates the database with demo research cycles if empty."""
    container = ServiceContainer.get(db_path=db_path)
    existing = container.repository.list_all_cycles()
    if existing:
        return

    print("Populating demo stocks and research cycles for first run...")
    demo_records = [
        ("RELIANCE", "Reliance Industries Limited", date(2014, 1, 10)),
        ("RELIANCE", "Reliance Industries Limited", date(2016, 1, 30)),
        ("TCS", "Tata Consultancy Services", date(2016, 1, 30)),
        ("INFY", "Infosys Limited", date(2019, 7, 15)),
        ("HDFCBANK", "HDFC Bank Limited", date(2018, 4, 12)),
    ]

    for sym, name, ref_date in demo_records:
        try:
            container.cycle_service.add_stock_cycle(
                query=sym,
                reference_date=ref_date,
                company_name=name,
            )
            print(f"  + Added {sym} (Research Date: {ref_date.strftime('%d-%b-%Y')})")
        except Exception as e:
            print(f"  - Notice on seeding {sym}: {e}")

    print("Demo dataset initialized successfully.\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Launch and use Stock Cycle Tracker.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--db", default="stock_cycle_tracker.db", help="SQLite database path (default: stock_cycle_tracker.db)")
    parser.add_argument("--no-seed", action="store_true", help="Do not automatically populate sample demo stocks on empty database")

    args = parser.parse_args()

    # Cloud platforms (Render, Railway) inject PORT/HOST via env vars
    args.port = int(os.environ.get("PORT", args.port))
    args.host = os.environ.get("HOST", args.host)

    # Automatically seed sample data on first run if database is empty unless --no-seed is specified
    if not args.no_seed:
        seed_demo_data(args.db)

    print(f"============================================================")
    print(f"  Stock Cycle Tracker — Web UI")
    print(f"  Server URL: http://{args.host}:{args.port}")
    print(f"  Database:   {Path(args.db).resolve()}")
    print(f"============================================================")

    app = build_app(db_path=args.db)
    app.run_in_browser(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
