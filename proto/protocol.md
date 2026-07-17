# high-frequency-alpha wire protocol

A distributed HFT alpha engine. Each language owns its domain; one JSON contract
connects them.

```
market feeds ──WS──▶ Go concentrator ──HTTP──▶ Rust matcher ──features──▶ Python RL brain
                        │  (normalize + route)   (order book + OBI)         (Bellman action)
                        └──WebSocket──▶ TypeScript trading desk ◀── book + action ──┘
```

## 1. Feed ⇄ Concentrator (Go)

The Go concentrator connects to exchange feeds (or a synthetic generator) and
normalizes every message into a uniform market event:

```jsonc
{ "id": 128, "side": "bid", "price": 100.25, "size": 3.0, "kind": "limit" }
// kind: "limit" | "market" | "cancel"   side: "bid" | "ask"
```

## 2. Concentrator ⇄ Matcher (Rust)

```jsonc
POST /submit { "events": [ { ...MarketEvent... } ] }
->
{ "book": { "bids": [[100.25, 3.0], ...], "asks": [[100.30, 2.0], ...] },
  "trades": [ { "price": 100.30, "size": 1.0 } ],
  "features": { "mid": 100.275, "spread": 0.05, "obi": 0.20, "obi_ma": 0.15,
                "microprice": 100.29, "best_bid": 100.25, "best_ask": 100.30 } }
GET /features   -> { ...features... }
GET /book       -> { "bids": [...], "asks": [...] }
GET /health
```

## 3. Concentrator ⇄ Brain (Python)

```jsonc
POST /decide { "features": { ...matcher features... }, "position": 0.0, "cash": 100000.0 }
->
{ "action": "BUY", "price": 100.26, "size": 1.0, "value": 0.42, "reason": "obi>0 …",
  "risk_ok": true }
GET /health
```

## Alert / desk stream (Concentrator → Desk, WebSocket)

```jsonc
{ "ts": 1730000000.0, "book": {...}, "features": {...}, "action": {...}, "latency_ms": 0.8 }
```

## The math

The RL brain scores actions with the Bellman optimality update

    V*(s) = max_a [ R(s,a) + γ Σ_s' P(s'|s,a) V*(s') ]

where the reward `R(s,a)` is risk-adjusted realized PnL, `γ` the discount factor,
and the state features (OBI, microprice, spread) are computed by Rust. Offline the
brain runs a deterministic from-scratch value-function agent; set `HFA_BRAIN=torch`
to plug in a PyTorch policy.
