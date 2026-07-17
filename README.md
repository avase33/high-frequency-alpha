# high-frequency-alpha 📈

**A distributed, high-frequency algorithmic-trading engine.** Go ingests market
data, Rust maintains a live limit order book and computes microstructure signals,
a Python reinforcement-learning brain turns those signals into risk-checked
orders, and a TypeScript desk renders it all in real time.

Four languages, each on the layer it's built for, over one JSON protocol:

```
market feeds ──▶ Go concentrator ──▶ Rust matcher ──▶ Python RL brain
                    │  (ingest+route)   (order book+OBI)   (Bellman action+risk)
                    └──WebSocket──▶ TypeScript desk ◀── book + action ──┘
```

| Layer | Language | Owns |
| --- | --- | --- |
| **Ingestion** | Go | Concurrent exchange feeds, event normalization, fills, desk broadcast |
| **Matcher** | Rust | Limit order book, price-time matching, OBI & micro-price features |
| **Brain** | Python | Value-function RL agent + pre-trade risk guard |
| **Desk** | TypeScript / Next.js | Canvas order-book depth, latency & equity charts |

Runs **offline** — the Go feed is synthetic, the agent is from-scratch (no torch),
and the market is simulated with OBI made mildly predictive so a sane agent profits.

## Quickstart — the brain, offline

```bash
cd brain-python && pip install -e .
python -m hfa_brain.cli backtest
```

```
hfa brain — synthetic backtest (OBI-predictive market)
  final_equity   1032xx.xx
  pnl            +32xx.xx
  trades         41x
  ...
  PROFIT: +32xx.xx over 41x trades
```

Offline end-to-end check:

```bash
python scripts/verify.py     # RESULT: N passed, 0 failed
```

## Quickstart — the whole desk

```bash
docker compose up --build
# Desk:      http://localhost:3000   (watch the book, agent, latency, equity)
# Ingestion: http://localhost:8080/health
# Matcher:   http://localhost:8091/health
# Brain:     http://localhost:8000/health
```

Or run layers standalone:

```bash
cd matcher-rust   && cargo run                                            # :8091
cd brain-python   && pip install -e ".[server]" && hfa-brain serve        # :8000
cd ingestion-go   && HFA_MATCHER_URL=http://localhost:8091 HFA_BRAIN_URL=http://localhost:8000 go run .   # :8080
cd dashboard-ts   && npm install && npm run dev                           # :3000
```

## The interesting engineering

- **Order book + OBI (Rust)** — tick-quantised `BTreeMap` book, price-time
  matching, and Order Book Imbalance / micro-price over a sliding window.
  `matcher-rust/src/book.rs`
- **Bellman RL agent (Python)** — `Q(s,a)=w_a·φ(s)` trained with the Q-learning
  update `δ = R + γ·maxQ(s') − Q(s,a)`, from scratch. `brain-python/hfa_brain/agent.py`
- **Pre-trade risk guard** — rejects orders that breach position, notional, or
  max-drawdown limits (the difference between a bug and a blown account).
  `brain-python/hfa_brain/risk.py`
- **Go concentrator** — normalizes market events, drives matcher → brain → fill,
  and streams the desk state with round-trip latency. `ingestion-go/`
- **Canvas desk (TS)** — order-book depth, OBI/spread/equity, latency sparkline.
  `dashboard-ts/app/page.tsx`

## Testing

```bash
make test                     # rust + python + go
cd matcher-rust && cargo test
cd brain-python && pytest -q
cd ingestion-go && go test ./...
cd dashboard-ts && npm run build
```

## Layout

```
proto/            shared JSON wire protocol
dashboard-ts/     Next.js trading desk (canvas depth + charts)
ingestion-go/     Go market-data concentrator (feed → matcher → brain → desk)
matcher-rust/     Rust limit order book + microstructure features
brain-python/     value-function RL agent + risk guard + FastAPI
scripts/verify.py offline end-to-end check
docs/ARCHITECTURE.md
```

> ⚠️ Research/education only. Not investment advice; do not point this at a live
> brokerage without extensive review.

## License

MIT © 2026 Akhil Vase
