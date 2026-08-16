"""SQLite Repository implementation for stocks, cycles, cache, and alerts."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional, Sequence, Tuple

from stock_cycle_tracker.domain.models import (
    Cycle,
    CycleAnalysis,
    ExchangePreference,
    NormalizedOHLC,
    Stock,
)
from stock_cycle_tracker.storage.db import DatabaseManager


class StockCycleRepository:
    """Provides relational CRUD operations for Stock Cycle Tracker."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    # ------------------ Stock CRUD ------------------

    def create_or_get_stock(self, stock: Stock) -> Stock:
        sym = stock.symbol.strip().upper()
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, symbol, company_name, user_display_name, nse_symbol, bse_code, preferred_exchange FROM stocks WHERE symbol = ?", (sym,))
            row = cur.fetchone()
            if row:
                return Stock(
                    id=row["id"],
                    symbol=row["symbol"],
                    company_name=row["company_name"] or stock.company_name,
                    user_display_name=row["user_display_name"],
                    nse_symbol=row["nse_symbol"],
                    bse_code=row["bse_code"],
                    preferred_exchange=ExchangePreference(row["preferred_exchange"] or "NSE"),
                )

            cur.execute(
                """
                INSERT INTO stocks (symbol, company_name, user_display_name, nse_symbol, bse_code, preferred_exchange)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    sym,
                    stock.company_name or sym,
                    stock.user_display_name,
                    stock.nse_symbol or sym,
                    stock.bse_code,
                    stock.preferred_exchange.value,
                ),
            )
            conn.commit()
            new_id = cur.lastrowid
            stock.id = new_id
            stock.symbol = sym
            return stock

    def get_stock(self, symbol: str) -> Optional[Stock]:
        sym = symbol.strip().upper()
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM stocks WHERE symbol = ?", (sym,))
            row = cur.fetchone()
            if not row:
                return None
            return Stock(
                id=row["id"],
                symbol=row["symbol"],
                company_name=row["company_name"],
                user_display_name=row["user_display_name"],
                nse_symbol=row["nse_symbol"],
                bse_code=row["bse_code"],
                preferred_exchange=ExchangePreference(row["preferred_exchange"] or "NSE"),
            )

    def list_stocks(self) -> List[Stock]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM stocks ORDER BY symbol ASC")
            return [
                Stock(
                    id=row["id"],
                    symbol=row["symbol"],
                    company_name=row["company_name"],
                    user_display_name=row["user_display_name"],
                    nse_symbol=row["nse_symbol"],
                    bse_code=row["bse_code"],
                    preferred_exchange=ExchangePreference(row["preferred_exchange"] or "NSE"),
                )
                for row in cur.fetchall()
            ]

    def delete_stock(self, stock_id: int) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM stocks WHERE id = ?", (stock_id,))
            conn.commit()
            return cur.rowcount > 0

    # ------------------ Cycle CRUD ------------------

    def add_cycle(self, stock_id: int, reference_date: date) -> Cycle:
        """
        Adds a new cycle for the stock.
        Auto-computes cycle_number (Cycle 1, Cycle 2, ...).
        Prevents duplicate cycles for the exact same stock and reference date.
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            # Check if cycle with same date already exists
            cur.execute(
                "SELECT * FROM cycles WHERE stock_id = ? AND reference_date = ?",
                (stock_id, reference_date.isoformat()),
            )
            existing = cur.fetchone()
            if existing:
                return Cycle(
                    id=existing["id"],
                    stock_id=existing["stock_id"],
                    cycle_number=existing["cycle_number"],
                    reference_date=date.fromisoformat(existing["reference_date"]),
                )

            # Determine next cycle number
            cur.execute("SELECT COALESCE(MAX(cycle_number), 0) + 1 AS next_num FROM cycles WHERE stock_id = ?", (stock_id,))
            next_num = cur.fetchone()["next_num"]

            cur.execute(
                "INSERT INTO cycles (stock_id, cycle_number, reference_date) VALUES (?, ?, ?)",
                (stock_id, next_num, reference_date.isoformat()),
            )
            conn.commit()
            new_id = cur.lastrowid
            return Cycle(
                id=new_id,
                stock_id=stock_id,
                cycle_number=next_num,
                reference_date=reference_date,
            )

    def list_cycles_for_stock(self, stock_id: int) -> List[Cycle]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM cycles WHERE stock_id = ? ORDER BY cycle_number ASC",
                (stock_id,),
            )
            return [
                Cycle(
                    id=row["id"],
                    stock_id=row["stock_id"],
                    cycle_number=row["cycle_number"],
                    reference_date=date.fromisoformat(row["reference_date"]),
                )
                for row in cur.fetchall()
            ]

    def list_all_cycles(self) -> List[Tuple[Stock, Cycle]]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT s.id as s_id, s.symbol, s.company_name, s.user_display_name, s.nse_symbol, s.bse_code, s.preferred_exchange,
                       c.id as c_id, c.stock_id, c.cycle_number, c.reference_date
                FROM cycles c
                JOIN stocks s ON c.stock_id = s.id
                ORDER BY s.symbol ASC, c.cycle_number ASC
                """
            )
            results = []
            for row in cur.fetchall():
                stock = Stock(
                    id=row["s_id"],
                    symbol=row["symbol"],
                    company_name=row["company_name"],
                    user_display_name=row["user_display_name"],
                    nse_symbol=row["nse_symbol"],
                    bse_code=row["bse_code"],
                    preferred_exchange=ExchangePreference(row["preferred_exchange"] or "NSE"),
                )
                cycle = Cycle(
                    id=row["c_id"],
                    stock_id=row["stock_id"],
                    cycle_number=row["cycle_number"],
                    reference_date=date.fromisoformat(row["reference_date"]),
                )
                results.append((stock, cycle))
            return results

    def delete_cycle(self, cycle_id: int) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM cycles WHERE id = ?", (cycle_id,))
            conn.commit()
            return cur.rowcount > 0

    # ------------------ OHLC Cache ------------------

    def save_cached_ohlc(self, symbol: str, bars: Sequence[NormalizedOHLC]) -> None:
        sym = symbol.strip().upper()
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.executemany(
                """
                INSERT INTO market_data_cache (stock_symbol, trading_date, open, high, low, close, volume, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(stock_symbol, trading_date) DO UPDATE SET
                  open=excluded.open,
                  high=excluded.high,
                  low=excluded.low,
                  close=excluded.close,
                  volume=excluded.volume,
                  source=excluded.source,
                  created_at=CURRENT_TIMESTAMP
                """,
                [
                    (sym, b.date.isoformat(), b.open, b.high, b.low, b.close, b.volume, b.source)
                    for b in bars
                ],
            )
            conn.commit()

    def get_cached_ohlc(self, symbol: str, start_date: date, end_date: date) -> List[NormalizedOHLC]:
        sym = symbol.strip().upper()
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM market_data_cache
                WHERE stock_symbol = ? AND trading_date >= ? AND trading_date <= ?
                ORDER BY trading_date ASC
                """,
                (sym, start_date.isoformat(), end_date.isoformat()),
            )
            return [
                NormalizedOHLC(
                    date=date.fromisoformat(row["trading_date"]),
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                    source=row["source"],
                )
                for row in cur.fetchall()
            ]

    # ------------------ Snapshot Storage ------------------

    def save_snapshot(self, snapshot: CycleAnalysis, cycle_id: Optional[int] = None) -> None:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO calculation_snapshots (
                    cycle_id, stock_symbol, cycle_number, calculation_date,
                    actual_reference_date, reference_high, current_price,
                    price_type, percentage_change, bucket, data_source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cycle_id,
                    snapshot.stock_symbol,
                    snapshot.cycle_number,
                    snapshot.calculation_date.isoformat(),
                    snapshot.actual_reference_trading_date.isoformat(),
                    snapshot.reference_high,
                    snapshot.current_price,
                    snapshot.price_type.value,
                    snapshot.percentage_change,
                    snapshot.bucket,
                    snapshot.data_source,
                ),
            )
            conn.commit()
