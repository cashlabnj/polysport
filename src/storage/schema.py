SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS wallet_snapshots (
  wallet TEXT NOT NULL,
  roi REAL NOT NULL,
  win_rate REAL NOT NULL,
  drawdown_proxy REAL NOT NULL,
  timing_edge REAL NOT NULL,
  market_selectivity REAL NOT NULL,
  captured_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
  order_id TEXT PRIMARY KEY,
  market_id TEXT NOT NULL,
  outcome_id TEXT NOT NULL,
  side TEXT NOT NULL,
  price REAL NOT NULL,
  size REAL NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""
