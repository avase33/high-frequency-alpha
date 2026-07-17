# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/); versioning: [SemVer](https://semver.org/).

## [0.1.0] - 2026-07-17

Initial release — a four-language distributed HFT alpha engine.

### Added
- **Rust matcher**: aggregated limit order book on tick-quantised `BTreeMap`s,
  price-time matching, and microstructure features (Order Book Imbalance, sliding
  OBI moving average, micro-price, spread). axum `/submit` `/features` `/book`.
- **Python RL brain**: linear value-function agent trained with the Bellman /
  Q-learning update, a pre-trade risk guard (position / notional / max-drawdown),
  a synthetic OBI-predictive market + backtest, FastAPI `/decide`, CLI, tests +
  offline verifier.
- **Go concentrator**: synthetic (or live) market-event generator, batches to the
  matcher, asks the brain for an action, applies fills, and streams the desk state
  to terminals over WebSocket. Tests.
- **Next.js desk**: canvas order-book depth, live OBI / spread / micro-price /
  position / equity, and equity + round-trip-latency sparklines.
- Shared JSON protocol, docker-compose, per-language Dockerfiles, multi-language
  CI, Makefile, MIT license.
