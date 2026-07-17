"""FastAPI service for the RL brain. POST /decide with matcher features + account
state, get a risk-checked action back."""

from __future__ import annotations

from typing import Any

from .brain import Brain

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except ImportError as e:  # pragma: no cover
    raise RuntimeError("Install server extras: pip install 'hfa-brain[server]'") from e

app = FastAPI(title="hfa-brain", version="0.1.0")
_brain = Brain()


class DecideReq(BaseModel):
    features: dict[str, float]
    position: float = 0.0
    cash: float = 100_000.0
    equity: float | None = None
    peak_equity: float | None = None


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "brain", "gamma": _brain.agent.gamma})


@app.post("/decide")
def decide(req: DecideReq) -> dict[str, Any]:
    action = _brain.decide(req.features, req.position, req.cash, req.equity, req.peak_equity)
    return action.to_dict()
