.PHONY: up down test test-rust test-python test-go build-web backtest verify

up:
	docker compose up --build

down:
	docker compose down

test: test-rust test-python test-go

test-rust:
	cd matcher-rust && cargo test

test-python:
	cd brain-python && pip install -e ".[dev]" && pytest -q

test-go:
	cd ingestion-go && go test ./...

build-web:
	cd dashboard-ts && npm install && npm run build

# Offline: run the RL brain through the synthetic market (no services needed).
backtest:
	cd brain-python && python -m hfa_brain.cli backtest

verify:
	python scripts/verify.py
