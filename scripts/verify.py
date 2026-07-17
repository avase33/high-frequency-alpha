#!/usr/bin/env python3
"""Offline end-to-end check of the HFA RL brain.

Runs the value-function agent through the synthetic OBI-predictive market, and
checks the policy leans with imbalance, the risk guard blocks limit breaches, and
the agent turns a profit — no matcher, no torch, no live feed.

    python scripts/verify.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "brain-python"))

from hfa_brain.brain import Brain  # noqa: E402
from hfa_brain.market import backtest, features_at  # noqa: E402
from hfa_brain.risk import RiskConfig, RiskGuard  # noqa: E402

_passed = 0
_failed = 0


def check(label: str, cond: bool) -> None:
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  [PASS] {label}")
    else:
        _failed += 1
        print(f"  [FAIL] {label}")


def main() -> int:
    print("=" * 70)
    print("high-frequency-alpha - offline end-to-end verification")
    print("=" * 70)

    b = Brain()
    check("policy buys on strong positive OBI", b.decide(features_at(100.0, 0.8)).action == "BUY")
    check("policy sells on strong negative OBI", b.decide(features_at(100.0, -0.8)).action == "SELL")

    guarded = Brain(risk=RiskGuard(RiskConfig(max_position=10)))
    blocked = guarded.decide(features_at(100.0, 0.9), position=10.0)
    check("risk guard blocks the position-limit breach", blocked.risk_ok is False and blocked.action == "HOLD")

    res = backtest(steps=600, seed=0)
    print(f"  backtest: {res['trades']} trades, position {res['position']}, "
          f"equity ${res['final_equity']:,.2f}, pnl {res['pnl']:+.2f}")
    check("agent trades", res["trades"] > 0 and res["finite"])
    check("agent is profitable in an OBI-predictive market", res["pnl"] > 0)

    print("-" * 70)
    print(f"RESULT: {_passed} passed, {_failed} failed")
    return 0 if _failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
