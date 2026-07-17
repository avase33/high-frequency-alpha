"""Shared types (see proto/protocol.md)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Action:
    action: str  # BUY | SELL | HOLD
    price: float
    size: float
    value: float
    reason: str
    risk_ok: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "price": round(self.price, 4),
            "size": self.size,
            "value": round(self.value, 4),
            "reason": self.reason,
            "risk_ok": self.risk_ok,
        }


ACTIONS = ["BUY", "HOLD", "SELL"]


def phi(features: dict[str, float]) -> list[float]:
    """State feature vector the agent's value function is linear in."""
    mid = features.get("mid", 0.0)
    micro = features.get("microprice", mid)
    return [
        features.get("obi", 0.0),
        features.get("obi_ma", 0.0),
        -features.get("spread", 0.0),          # tighter spread → more tradeable
        (micro - mid),                          # micro-price pressure
    ]
