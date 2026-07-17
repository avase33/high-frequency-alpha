"""The brain ties the value agent to the risk guard and turns a market snapshot
into a concrete, risk-checked order."""

from __future__ import annotations

from typing import Optional

from .agent import ValueAgent
from .models import Action, phi
from .risk import RiskGuard


class Brain:
    def __init__(
        self,
        agent: Optional[ValueAgent] = None,
        risk: Optional[RiskGuard] = None,
        tick: float = 0.01,
        base_size: float = 1.0,
    ) -> None:
        self.agent = agent or ValueAgent()
        self.risk = risk or RiskGuard()
        self.tick = tick
        self.base_size = base_size

    def decide(
        self,
        features: dict,
        position: float = 0.0,
        cash: float = 100_000.0,
        equity: Optional[float] = None,
        peak_equity: Optional[float] = None,
    ) -> Action:
        state = phi(features)
        action = self.agent.best_action(state)
        value = self.agent.q(state, action)

        ref = features.get("best_bid", features.get("mid", 0.0))
        ask = features.get("best_ask", ref)
        if action == "BUY":
            price = ref + self.tick
        elif action == "SELL":
            price = ask - self.tick
        else:
            price = features.get("mid", ref)
        size = 0.0 if action == "HOLD" else self.base_size

        eq = equity if equity is not None else cash
        peak = peak_equity if peak_equity is not None else eq
        ok, reason = self.risk.check(action, position, size, price, eq, peak)
        if not ok:
            return Action("HOLD", features.get("mid", ref), 0.0, value, reason, risk_ok=False)

        obi = features.get("obi", 0.0)
        return Action(action, price, size, value,
                      f"Q={value:.3f} obi={obi:.2f}", risk_ok=True)
