"""CLI: ``hfa-brain backtest|serve``."""

from __future__ import annotations

import argparse
import sys

from .market import backtest


def _backtest(steps: int, seed: int) -> int:
    res = backtest(steps=steps, seed=seed)
    print("=" * 64)
    print("hfa brain — synthetic backtest (OBI-predictive market)")
    print("=" * 64)
    for k, v in res.items():
        print(f"  {k:14} {v}")
    print("-" * 64)
    print(f"  {'PROFIT' if res['pnl'] > 0 else 'LOSS'}: {res['pnl']:+.2f} over {res['trades']} trades")
    return 0


def _serve(host: str, port: int) -> int:
    try:
        import uvicorn  # type: ignore
    except ImportError:
        print("Install server extras: pip install 'hfa-brain[server]'", file=sys.stderr)
        return 1
    uvicorn.run("hfa_brain.server:app", host=host, port=port, log_level="info")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="hfa-brain")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backtest", help="run the offline backtest")
    b.add_argument("--steps", type=int, default=600)
    b.add_argument("--seed", type=int, default=0)
    s = sub.add_parser("serve", help="run the FastAPI service")
    s.add_argument("--host", default="0.0.0.0")
    s.add_argument("--port", type=int, default=8000)
    args = p.parse_args(argv)
    if args.cmd == "backtest":
        return _backtest(args.steps, args.seed)
    return _serve(args.host, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
