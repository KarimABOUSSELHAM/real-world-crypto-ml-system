#########################################################################
## Development
#########################################################################

# Runs the service locally
dev:
	uv run services/${service}/src/${service}/main.py

# Loads the docker image into KinD cluster
push-for-dev:
	kind load docker-image ${service}:dev --name rwml-34fa

#Build a docker image for the service
build-for-dev:
	docker build -t ${service}:dev -f docker/${service}.Dockerfile .

# Deploys the service to the KinD cluster
deploy-for-dev: build-for-dev push-for-dev
	kubectl delete -f deployments/dev/${service}/${service}.yaml || true 
	kubectl apply -f deployments/dev/${service}/${service}.yaml

#########################################################################
## Production
#########################################################################

build-and-push-for-prod:
	docker buildx build --push --platform linux/arm64 -t ghcr.io/karimabousselham/${service}:0.1.4-beta.$(date +%s) -f docker/${service}.Dockerfile .

deploy-for-prod:
	kubectl delete -f deployments/prod/${service}/${service}.yaml || true
	kubectl apply -f deployments/prod/${service}/${service}.yaml
lint:
	ruff check . --fix