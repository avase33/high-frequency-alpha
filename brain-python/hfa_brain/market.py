"""A synthetic market for offline backtests.

Order-book imbalance is made mildly predictive of the next price move (as it is in
real microstructure), so an agent that leans with OBI and respects its risk limits
should make money. Deterministic given the seed.
"""

from __future__ import annotations

import math
import random
from typing import Optional

from .brain import Brain


def features_at(mid: float, obi: float) -> dict[str, float]:
    return {
        "mid": mid,
        "best_bid": round(mid - 0.01, 4),
        "best_ask": round(mid + 0.01, 4),
        "spread": 0.02,
        "obi": obi,
        "obi_ma": obi,
        "microprice": mid + 0.01 * obi,
    }


def backtest(brain: Optional[Brain] = None, steps: int = 600, seed: int = 0, train: bool = True) -> dict:
    brain = brain or Brain()
    rng = random.Random(seed)
    mid = 100.0
    position = 0.0
    cash = 100_000.0
    equity = cash
    peak = cash
    obi = 0.0
    trades = 0

    for _ in range(steps):
        obi = max(-1.0, min(1.0, 0.85 * obi + rng.gauss(0.0, 0.35)))
        f = features_at(mid, obi)
        act = brain.decide(f, position, cash, equity, peak)

        if act.action == "BUY":
            position += act.size
            cash -= act.size * act.price
            trades += 1
        elif act.action == "SELL":
            position -= act.size
            cash += act.size * act.price
            trades += 1

        move = 0.06 * obi + rng.gauss(0.0, 0.03)  # price leans with OBI
        mid = max(1.0, mid + move)
        equity = cash + position * mid
        peak = max(peak, equity)

        reward = position * move - 0.005 * abs(position)  # risk-adjusted PnL
        if train:
            brain.agent.update(f, act.action, reward, features_at(mid, obi))

    return {
        "final_equity": round(equity, 2),
        "pnl": round(equity - 100_000.0, 2),
        "position": round(position, 3),
        "trades": trades,
        "steps": steps,
        "finite": math.isfinite(equity),
    }
