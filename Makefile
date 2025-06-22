# Runs the trade service locally
dev:
	uv run services/trades/src/trades/main.py

push:
	kind load docker-image trades:dev --name rwml-34fa

build:
	docker build --no-cache -t trades:dev -f docker/trades.Dockerfile .

deploy: build push
	kubectl delete -f deployments/dev/trades/trades.yaml || true 
	kubectl apply -f deployments/dev/trades/trades.yaml