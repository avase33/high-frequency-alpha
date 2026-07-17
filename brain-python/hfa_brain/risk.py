"""Pre-trade risk guard — the safety layer between the agent and the market.

Rejects any order that would breach position, notional, or max-drawdown limits.
In a real system this is the difference between a bug and a blown-up account.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskConfig:
    max_position: float = 10.0
    max_notional: float = 1_000_000.0
    max_drawdown: float = 0.10  # fraction of peak equity


class RiskGuard:
    def __init__(self, config: RiskConfig | None = None) -> None:
        self.cfg = config or RiskConfig()

    def check(
        self,
        action: str,
        position: float,
        size: float,
        price: float,
        equity: float,
        peak_equity: float,
    ) -> tuple[bool, str]:
        if action == "HOLD" or size == 0.0:
            return True, "hold"

        if peak_equity > 0 and (peak_equity - equity) / peak_equity > self.cfg.max_drawdown:
            return False, f"max drawdown {self.cfg.max_drawdown:.0%} breached"

        new_pos = position + (size if action == "BUY" else -size)
        if abs(new_pos) > self.cfg.max_position:
            return False, f"position limit {self.cfg.max_position} exceeded"
        if abs(new_pos * price) > self.cfg.max_notional:
            return False, "notional limit exceeded"
        return True, "ok"
