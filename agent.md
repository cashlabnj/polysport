# agent.md — Polymarket Sports Betting Trader (Python)

## Role
You are a coordinated team of agents building a production-grade Polymarket sports betting trading bot.
You must produce structured deliverables and then implement the system end-to-end in Python.

## Mission
Build a Polymarket sports betting trading system that:
1) Learns Polymarket GitHub repos/docs and becomes expert at integration + bot development patterns.
2) Tracks high-performing wallets in sports markets (“top wallets”) and converts behavior into signal features.
3) Compares Vegas sportsbook odds/lines vs Polymarket implied probabilities to find mispricing/value.
4) Implements multiple profitable strategies with risk controls, execution guards, and auditability.
5) Exposes a Telegram interface for monitoring/configuration and optional auto-trading.
6) Ships with paper trading, tests, observability, and safe deployment via Docker Compose.

---

## Operating Rules (Non-Negotiables)
- Default mode is PAPER trading. Live trading requires explicit `/trade on` + admin allowlist.
- All trading actions must be logged (who/what/why).
- Every order must be idempotent and deduped.
- If odds data or market data is stale, HALT trading automatically.
- Secrets never stored in repo; use env vars + .env.example.
- Provide state machine diagrams in Mermaid and keep them synced with code.

---

## Architecture Overview (Target)
Services / modules:
- `market_ingestor`: polls Polymarket markets, orderbooks, prices
- `odds_ingestor`: pulls sportsbook odds/lines, normalizes to fair probability (de-vig)
- `wallet_tracker`: tracks watchlist wallets, computes performance + features
- `signal_engine`: computes strategy signals with confidence + explanations
- `risk_engine`: enforces caps + halts + portfolio rules
- `execution_engine`: places/cancels/orders with safety + retries
- `tg_bot`: Telegram command interface, admin-only actions
- `api` (optional): REST for dashboard
- `db`: Postgres (MVP can start with SQLite but must have Postgres-ready schema)

---

## Repo Structure (Create Exactly)
.
├── README.md
├── agent.md
├── docker-compose.yml
├── .env.example
├── pyproject.toml
├── src/
│   ├── app/
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── main.py
│   │   └── health.py
│   ├── polymarket/
│   │   ├── client.py
│   │   ├── models.py
│   │   ├── market_data.py
│   │   └── execution.py
│   ├── odds/
│   │   ├── providers/
│   │   │   ├── provider_base.py
│   │   │   └── provider_example.py
│   │   ├── normalize.py
│   │   └── fair_prob.py
│   ├── wallets/
│   │   ├── tracker.py
│   │   ├── scoring.py
│   │   └── features.py
│   ├── signals/
│   │   ├── engine.py
│   │   ├── strategies/
│   │   │   ├── vegas_value.py
│   │   │   ├── smart_money_confirm.py
│   │   │   ├── orderbook_imbalance.py
│   │   │   ├── drift_late_info.py
│   │   │   ├── mean_reversion.py
│   │   │   └── hedged_portfolio.py
│   │   └── types.py
│   ├── risk/
│   │   ├── engine.py
│   │   └── limits.py
│   ├── execution/
│   │   ├── engine.py
│   │   ├── orders.py
│   │   └── slippage.py
│   ├── telegram/
│   │   ├── bot.py
│   │   ├── commands.py
│   │   └── auth.py
│   ├── storage/
│   │   ├── db.py
│   │   ├── schema.sql
│   │   └── migrations/
│   └── utils/
│       ├── time.py
│       ├── retry.py
│       └── idempotency.py
└── tests/
   ├── unit/
   ├── integration/
   └── simulation/

---

## Multi-Agent Workflow (Execute in Order)
### Agent A — Polymarket Repo/SDK + Integration Expert
Deliver:
- Repo map + integration guide
- API endpoints + auth + order lifecycle + pitfalls
- Minimal “hello trade” pseudocode
- Canonical data models: Market/Outcome/Order/Fill/Position

### Agent B — Wallet Intelligence / Top Wallet Tracker
Deliver:
- Define wallet metrics: ROI, win rate, drawdown proxy, timing edge, market selectivity
- Data sourcing plan (how to attribute trades to sports markets)
- Watchlist scoring algorithm
- Derived features for smart-money confirmation
- Storage schema for wallet events + aggregates

### Agent C — Vegas / Odds Comparator
Deliver:
- Odds normalization (American/decimal) to implied probability
- De-vig method(s) and book aggregation
- Mismatch detection + confidence scoring
- Arb/value feasibility rules accounting for fees/slippage/limits

### Agent D — Quant Strategy Playbook (6+ Strategies)
You MUST specify at least these:
1) Vegas-vs-Poly Value
2) Smart Money Confirmation
3) Orderbook Imbalance / Liquidity Shock
4) Late Information Drift
5) Mean Reversion after Overreaction
6) Hedged Portfolio / Correlated Outcomes
Each strategy must include entry/exit, sizing, risk limits, and execution method.

### Agent E — Architect (State Machines + High-Level Plan)
Deliver:
- Component & dataflow diagrams
- State machines (Mermaid): market monitor, signal loop, order lifecycle, risk states, tg commands
- Milestones + acceptance criteria
- Threat model + mitigations

### Agent F — Full-Stack Dev (Implement)
Deliver:
- Working codebase per structure
- Docker compose + DB schema
- Telegram bot commands + permissioning
- Paper trading + simulation harness
- Tests + CI
- Runbook (deploy/monitor/recover)

---

## Required Outputs (In This Exact Order)
1) Executive Summary
2) Polymarket Integration Notes (Agent A)
3) Wallet Intelligence Spec (Agent B)
4) Vegas/Odds Comparator Spec (Agent C)
5) Strategy Playbook (Agent D)
6) Architecture + Data Models
7) State Machine Diagrams (Mermaid)
8) Implementation Plan (milestones + acceptance criteria)
9) Build Output (code scaffolding + key modules)
10) Test Plan (unit/integration/sim/paper)
11) Operational Runbook

---

## Telegram Bot Requirements (Minimum Commands)
- /status (health, balances, open positions, PnL)
- /markets <query>
- /watchlist add|remove <market_id>
- /wallets top
- /signals
- /trade on|off (global kill switch)
- /strategy enable|disable <name>
- /risk set <param> <value>
- /orders
- /paper on|off

Security:
- Admin allowlist of Telegram user IDs
- All commands logged with timestamp and actor
- Live trading requires confirm-required mode

---

## Mermaid Diagrams (Must Produce)
### Order Lifecycle (example skeleton)
```mermaid
stateDiagram-v2
  [*] --> Idle
  Idle --> CreateOrder: signal approved
  CreateOrder --> SubmitOrder
  SubmitOrder --> Open: accepted
  Open --> PartialFill
  PartialFill --> Filled
  Open --> Canceled
  SubmitOrder --> Failed
  Failed --> Idle
  Filled --> Idle
  Canceled --> Idle
