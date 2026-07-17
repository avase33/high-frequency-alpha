"""hfa brain — from-scratch value-function trading agent + risk guard."""

from .agent import ValueAgent
from .brain import Brain
from .market import backtest, features_at
from .models import Action, phi
from .risk import RiskConfig, RiskGuard

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "ValueAgent",
    "Brain",
    "backtest",
    "features_at",
    "Action",
    "phi",
    "RiskConfig",
    "RiskGuard",
]
