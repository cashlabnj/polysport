from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

# Default database path
DEFAULT_DB_PATH = "data/polysport.db"


def connect(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create a database connection with proper settings."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_connection(db_path: str = DEFAULT_DB_PATH) -> Iterator[sqlite3.Connection]:
    """Context manager for database connections."""
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema(conn: sqlite3.Connection) -> None:
    """Initialize database schema with all required tables."""
    conn.executescript("""
        -- Risk state (singleton table for global trading state)
        CREATE TABLE IF NOT EXISTS risk_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            trading_enabled BOOLEAN NOT NULL DEFAULT 0,
            paper_mode BOOLEAN NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL
        );

        -- Insert default risk state if not exists
        INSERT OR IGNORE INTO risk_state (id, trading_enabled, paper_mode, updated_at)
        VALUES (1, 0, 1, datetime('now'));

        -- Orders table
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            market_id TEXT NOT NULL,
            outcome_id TEXT NOT NULL,
            side TEXT NOT NULL,
            price REAL NOT NULL,
            size REAL NOT NULL,
            status TEXT NOT NULL,
            strategy TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        -- Fills table for order executions
        CREATE TABLE IF NOT EXISTS fills (
            fill_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL REFERENCES orders(order_id),
            price REAL NOT NULL,
            size REAL NOT NULL,
            timestamp TEXT NOT NULL
        );

        -- Idempotency keys with TTL
        CREATE TABLE IF NOT EXISTS idempotency_keys (
            key TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );

        -- Audit log for all actions
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            actor_id TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            correlation_id TEXT
        );

        -- Strategy state
        CREATE TABLE IF NOT EXISTS strategy_state (
            strategy_name TEXT PRIMARY KEY,
            enabled BOOLEAN NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL
        );

        -- Watchlist
        CREATE TABLE IF NOT EXISTS watchlist (
            market_id TEXT PRIMARY KEY,
            added_at TEXT NOT NULL
        );

        -- Daily PnL tracking
        CREATE TABLE IF NOT EXISTS daily_pnl (
            date TEXT PRIMARY KEY,
            realized_pnl REAL NOT NULL DEFAULT 0.0,
            unrealized_pnl REAL NOT NULL DEFAULT 0.0,
            updated_at TEXT NOT NULL
        );

        -- Create indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
        CREATE INDEX IF NOT EXISTS idx_orders_market ON orders(market_id);
        CREATE INDEX IF NOT EXISTS idx_fills_order ON fills(order_id);
        CREATE INDEX IF NOT EXISTS idx_idempotency_expires ON idempotency_keys(expires_at);
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
    """)
    conn.commit()


class Database:
    """High-level database operations with thread-safe access."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self.conn = connect(db_path)
        init_schema(self.conn)

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    # Risk State Operations
    def get_trading_enabled(self) -> bool:
        cursor = self.conn.execute(
            "SELECT trading_enabled FROM risk_state WHERE id = 1"
        )
        row = cursor.fetchone()
        return bool(row["trading_enabled"]) if row else False

    def set_trading_enabled(self, enabled: bool) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE risk_state SET trading_enabled = ?, updated_at = ? WHERE id = 1",
            (enabled, now),
        )
        self.conn.commit()

    def get_paper_mode(self) -> bool:
        cursor = self.conn.execute(
            "SELECT paper_mode FROM risk_state WHERE id = 1"
        )
        row = cursor.fetchone()
        return bool(row["paper_mode"]) if row else True

    def set_paper_mode(self, paper: bool) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE risk_state SET paper_mode = ?, updated_at = ? WHERE id = 1",
            (paper, now),
        )
        self.conn.commit()

    # Idempotency Operations
    def check_idempotency_key(self, key: str) -> bool:
        """Check if idempotency key exists and is not expired."""
        now = datetime.now(timezone.utc).isoformat()
        # Clean up expired keys first
        self.conn.execute(
            "DELETE FROM idempotency_keys WHERE expires_at < ?", (now,)
        )
        cursor = self.conn.execute(
            "SELECT 1 FROM idempotency_keys WHERE key = ? AND expires_at >= ?",
            (key, now),
        )
        return cursor.fetchone() is not None

    def add_idempotency_key(self, key: str, ttl_hours: int = 24) -> None:
        """Add idempotency key with TTL."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=ttl_hours)
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO idempotency_keys (key, created_at, expires_at) VALUES (?, ?, ?)",
                (key, now.isoformat(), expires.isoformat()),
            )
            self.conn.commit()

    # Order Operations
    def save_order(
        self,
        order_id: str,
        market_id: str,
        outcome_id: str,
        side: str,
        price: float,
        size: float,
        status: str,
        strategy: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            INSERT OR REPLACE INTO orders
            (order_id, market_id, outcome_id, side, price, size, status, strategy, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (order_id, market_id, outcome_id, side, price, size, status, strategy, now, now),
        )
        self.conn.commit()

    def update_order_status(self, order_id: str, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE orders SET status = ?, updated_at = ? WHERE order_id = ?",
            (status, now, order_id),
        )
        self.conn.commit()

    def get_open_orders(self) -> list[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM orders WHERE status IN ('submitted', 'pending', 'paper')"
        )
        return [dict(row) for row in cursor.fetchall()]

    def count_open_positions(self) -> int:
        cursor = self.conn.execute(
            "SELECT COUNT(DISTINCT market_id) FROM orders WHERE status IN ('filled', 'paper')"
        )
        row = cursor.fetchone()
        return row[0] if row else 0

    # Audit Operations
    def log_action(
        self,
        actor_id: str,
        action: str,
        details: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO audit_log (actor_id, action, details, correlation_id)
            VALUES (?, ?, ?, ?)
            """,
            (actor_id, action, details, correlation_id),
        )
        self.conn.commit()

    # Strategy State Operations
    def get_strategy_enabled(self, strategy_name: str) -> bool:
        cursor = self.conn.execute(
            "SELECT enabled FROM strategy_state WHERE strategy_name = ?",
            (strategy_name,),
        )
        row = cursor.fetchone()
        return bool(row["enabled"]) if row else True  # Default enabled

    def set_strategy_enabled(self, strategy_name: str, enabled: bool) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            INSERT OR REPLACE INTO strategy_state (strategy_name, enabled, updated_at)
            VALUES (?, ?, ?)
            """,
            (strategy_name, enabled, now),
        )
        self.conn.commit()

    # Watchlist Operations
    def get_watchlist(self) -> set[str]:
        cursor = self.conn.execute("SELECT market_id FROM watchlist")
        return {row["market_id"] for row in cursor.fetchall()}

    def add_to_watchlist(self, market_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT OR IGNORE INTO watchlist (market_id, added_at) VALUES (?, ?)",
            (market_id, now),
        )
        self.conn.commit()

    def remove_from_watchlist(self, market_id: str) -> None:
        self.conn.execute(
            "DELETE FROM watchlist WHERE market_id = ?", (market_id,)
        )
        self.conn.commit()

    # Daily PnL Operations
    def get_daily_pnl(self, date: str | None = None) -> float:
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cursor = self.conn.execute(
            "SELECT realized_pnl + unrealized_pnl as total FROM daily_pnl WHERE date = ?",
            (date,),
        )
        row = cursor.fetchone()
        return row["total"] if row else 0.0

    def update_daily_pnl(self, realized: float = 0.0, unrealized: float = 0.0) -> None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            INSERT INTO daily_pnl (date, realized_pnl, unrealized_pnl, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                realized_pnl = realized_pnl + excluded.realized_pnl,
                unrealized_pnl = excluded.unrealized_pnl,
                updated_at = excluded.updated_at
            """,
            (date, realized, unrealized, now),
        )
        self.conn.commit()
