# high-frequency-alpha architecture

A distributed HFT alpha engine. Each language owns its computing domain; one JSON
contract (`proto/protocol.md`) connects them.

```
   market feeds (exchange WebSockets / synthetic)
        │  normalized MarketEvents
        ▼
┌──────────────────────────┐   HTTP /submit   ┌──────────────────────────┐
│ Concentrator · Go        │ ───────────────▶ │ Matcher · Rust           │
│ ingest · route · fills   │ ◀─── book +      │ limit order book + OBI   │
│ desk broadcast (WS)      │      features    │ microstructure features  │
└───────┬──────────────────┘                  └──────────────────────────┘
        │ HTTP /decide                                  ▲
        ▼                                               │ features
┌──────────────────────────┐                            │
│ Brain · Python           │ ───────────────────────────┘
│ value-function agent +   │
│ pre-trade risk guard     │
└──────────────────────────┘
        │ WebSocket /ws/desk
        ▼
┌──────────────────────────┐
│ Desk · TypeScript        │ canvas depth · OBI · latency · equity
└──────────────────────────┘
```

## Why each language

| Layer | Language | Reason |
| --- | --- | --- |
| Ingestion | **Go** | Thousands of concurrent exchange WebSockets, non-blocking routing, tiny per-connection cost. |
| Matcher | **Rust** | The order book + feature math is the hottest path; zero-GC, cache-friendly `BTreeMap`s. |
| Brain | **Python** | RL / numerical ecosystem; here a from-scratch value-function agent. |
| Desk | **TypeScript** | 60fps canvas depth charts and streaming metrics. |

## Loop

1. The Go concentrator normalizes market messages into uniform `MarketEvent`s and
   batches them to the Rust matcher.
2. Rust applies each event to the order book (price-time matching), then computes
   **Order Book Imbalance**, its moving average, micro-price and spread.
3. Go passes those features (plus account state) to the Python brain.
4. The brain evaluates `Q(s,a)=w_a·φ(s)` for BUY/HOLD/SELL, picks the best action,
   and the **risk guard** vetoes anything that breaches position, notional or
   drawdown limits.
5. Go applies the (simulated) fill and broadcasts the desk state — book, features,
   action, position, equity, round-trip latency — to every terminal.

## The math

The agent is grounded in the Bellman optimality equation

    V*(s) = max_a [ R(s,a) + γ · Σ_s' P(s'|s,a) V*(s') ]

realised as Q-learning with linear function approximation:

    δ = R + γ·max_a' Q(s',a') − Q(s,a);   w_a ← w_a + α·δ·φ(s)

where `R(s,a)` is risk-adjusted realised PnL and the state features φ (OBI, OBI
moving-average, spread, micro-price pressure) come from Rust. See
`brain-python/hfa_brain/agent.py`.

## Offline-first

- **Brain**: pure-Python agent + synthetic OBI-predictive market → no torch, no
  data feed; `HFA_BRAIN=torch` swaps in a neural policy.
- **Go**: a built-in synthetic event generator drives the whole pipeline with no
  live exchange connection.
- **Rust**: the matcher is self-contained.

`docker compose up` gives a live, trading desk you can watch; `make backtest`
runs the agent through the synthetic market with no services at all.
