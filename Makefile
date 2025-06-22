# Runs the trade service locally
dev:
	uv run services/trades/src/trades/main.py

# Loads the trades docker image into KinD cluster
push:
	kind load docker-image trades:dev --name rwml-34fa

#Build a docker image for the trades service
build:
	docker build --no-cache -t trades:dev -f docker/trades.Dockerfile .

# Deploys the trades service to the KinD cluster
deploy: build push
	kubectl delete -f deployments/dev/trades/trades.yaml || true 
	kubectl apply -f deployments/dev/trades/trades.yaml

lint:
	ruff check . --fix