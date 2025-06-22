dev:
	uv run services/trades/src/trades/main.py

build:
	docker build --no-cache -t trades:dev -f docker/trades.Dockerfile .
