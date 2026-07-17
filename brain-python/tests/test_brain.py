from hfa_brain.agent import ValueAgent
from hfa_brain.brain import Brain
from hfa_brain.market import backtest, features_at
from hfa_brain.risk import RiskConfig, RiskGuard


def test_policy_leans_with_obi():
    b = Brain()
    assert b.decide(features_at(100.0, 0.8)).action == "BUY"
    assert b.decide(features_at(100.0, -0.8)).action == "SELL"


def test_risk_blocks_position_limit():
    b = Brain(risk=RiskGuard(RiskConfig(max_position=10)))
    act = b.decide(features_at(100.0, 0.9), position=10.0)
    assert act.action == "HOLD"
    assert act.risk_ok is False


def test_risk_blocks_on_drawdown():
    b = Brain()
    act = b.decide(features_at(100.0, 0.9), position=0.0, cash=100_000, equity=80_000, peak_equity=100_000)
    assert act.risk_ok is False  # 20% drawdown exceeds the 10% limit


def test_bellman_update_changes_weights():
    a = ValueAgent()
    before = list(a.w["BUY"])
    td = a.update(features_at(100.0, 0.8), "BUY", reward=1.0, next_features=features_at(100.1, 0.8))
    assert a.w["BUY"] != before
    assert isinstance(td, float)


def test_backtest_trades_and_finite():
    res = backtest(steps=200, seed=1)
    assert res["trades"] > 0
    assert res["finite"]


def test_backtest_profitable_in_predictive_market():
    res = backtest(steps=600, seed=0)
    assert res["pnl"] > 0
