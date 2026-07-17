"""A value-function trading agent, from scratch.

Linear action-value function Q(s, a) = w_a · φ(s), trained with the Bellman /
Q-learning update

    δ = R + γ·max_a' Q(s', a') − Q(s, a);   w_a ← w_a + α·δ·φ(s)

which is exactly the tabular Bellman optimality equation lifted to linear function
approximation. The priors already encode "lean with order-book imbalance"; the
update refines them online. No numpy, no torch.
"""

from __future__ import annotations

from .models import ACTIONS, phi


def _dot(w: list[float], x: list[float]) -> float:
    return sum(wi * xi for wi, xi in zip(w, x))


class ValueAgent:
    def __init__(self, alpha: float = 0.05, gamma: float = 0.9) -> None:
        self.alpha = alpha
        self.gamma = gamma
        # weights over φ = [obi, obi_ma, -spread, micro_pressure]
        self.w: dict[str, list[float]] = {
            "BUY": [1.0, 0.5, 0.0, 2.0],
            "HOLD": [0.0, 0.0, 0.0, 0.0],
            "SELL": [-1.0, -0.5, 0.0, -2.0],
        }

    def q(self, state: list[float], action: str) -> float:
        return _dot(self.w[action], state)

    def best_action(self, state: list[float]) -> str:
        return max(ACTIONS, key=lambda a: self.q(state, a))

    def value(self, state: list[float]) -> float:
        return max(self.q(state, a) for a in ACTIONS)

    def update(self, features: dict, action: str, reward: float, next_features: dict) -> float:
        s = phi(features)
        ns = phi(next_features)
        target = reward + self.gamma * self.value(ns)
        td = target - self.q(s, action)
        self.w[action] = [wi + self.alpha * td * si for wi, si in zip(self.w[action], s)]
        return td
