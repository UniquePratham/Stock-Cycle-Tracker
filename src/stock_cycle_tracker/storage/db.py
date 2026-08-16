"""Database schema and connection management using SQLite."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Optional


class DatabaseManager:
    """Manages SQLite database connections and schema migrations."""

    SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT UNIQUE NOT NULL,
        company_name TEXT DEFAULT '',
        user_display_name TEXT DEFAULT '',
        nse_symbol TEXT,
        bse_code TEXT,
        preferred_exchange TEXT DEFAULT 'NSE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS cycles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
        cycle_number INTEGER NOT NULL,
        reference_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(stock_id, reference_date)
    );

    CREATE TABLE IF NOT EXISTS market_data_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_symbol TEXT NOT NULL,
        trading_date DATE NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER DEFAULT 0,
        source TEXT DEFAULT 'NSE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(stock_symbol, trading_date)
    );

    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_symbol TEXT NOT NULL,
        cycle_number INTEGER DEFAULT 1,
        condition_type TEXT NOT NULL,
        threshold_value REAL DEFAULT 0.0,
        target_bucket TEXT,
        is_enabled BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_triggered_at TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS calculation_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cycle_id INTEGER REFERENCES cycles(id) ON DELETE CASCADE,
        stock_symbol TEXT NOT NULL,
        cycle_number INTEGER NOT NULL,
        calculation_date DATE NOT NULL,
        actual_reference_date DATE,
        reference_high REAL,
        current_price REAL,
        price_type TEXT,
        percentage_change REAL,
        bucket TEXT,
        data_source TEXT,
        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_cycles_stock_id ON cycles(stock_id);
    CREATE INDEX IF NOT EXISTS idx_market_data ON market_data_cache(stock_symbol, trading_date);
    """

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        if db_path is None:
            self.db_path = Path("stock_cycle_tracker.db")
        elif isinstance(db_path, str):
            self.db_path = Path(db_path)
        else:
            self.db_path = db_path

        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self.get_connection() as conn:
            conn.executescript(self.SCHEMA_SQL)
            conn.commit()
