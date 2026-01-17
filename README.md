# Polysport — Polymarket Sports Betting Trader

## Executive Summary
Polysport is a paper-trading-first Polymarket sports betting system. It ingests Polymarket market data, compares it against sportsbook odds, tracks high-performing wallets, and generates multi-strategy signals with risk controls and safe execution. The system is designed to be production-ready with Docker Compose, structured logging, and a Telegram control plane.

## Polymarket Integration Notes (Phase 1)
**Sources to review** (documentation and repos should be verified before live trading):
- Polymarket API / data endpoints for market discovery and orderbooks.
- CLOB (Central Limit Order Book) gateway for order placement and fills.
- Authentication: wallet-based signing (EIP-712) and API key/nonce patterns.
- Sports market structure: event → market → outcomes (YES/NO or multi-outcome).

**Integration assumptions used for scaffolding**
- Market discovery returns a list of markets with outcomes and pricing fields.
- Order placement requires a signed payload, and returns an order id with status.
- Fills are returned by a separate trades endpoint or websocket stream.
- Positions can be computed by aggregating fills per outcome.

**Hello-trade pseudocode**
```text
client = PolymarketClient.from_env()
market = client.get_market(market_id)
order = Order(market_id=market.id, outcome_id=market.outcomes[0].id, side="buy", price=0.52, size=10)
result = client.place_order(order)
```

> Note: the client is intentionally stubbed to support paper trading and offline development. Replace stub responses with live API calls once credentials and official API details are confirmed.

## Runbook
### One-command startup
```bash
docker compose up
```

### Configure paper trading
- Update `.env` based on `.env.example`.
- Keep `PAPER_TRADING=true` for paper-only mode.
- Add Telegram admin IDs to `TELEGRAM_ADMINS` as a comma-separated list.
- Set `DB_PATH` to control where the SQLite database is stored.

### Operational checks
- `/status` should report paper mode.
- `/signals` should show the count of active signals.
- `/trade off` should disable live trading globally.
- `/health` should return the current Polymarket client status.

### Clean shutdown
```bash
docker compose down
```

### Export a repo zip (without .git)
If you need a clean zip archive of the current HEAD without the `.git` directory:
```bash
./scripts/export_repo_zip.sh
```
To customize the output file name or path:
```bash
./scripts/export_repo_zip.sh /path/to/polysport.zip
```
The script prints a SHA256 checksum for easy verification when `shasum` or
`sha256sum` is available on your system.

## Roadmap
See `docs/diagrams.md` for architecture diagrams and state machines.
