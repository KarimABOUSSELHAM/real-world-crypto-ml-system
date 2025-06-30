# Runs the service locally
dev:
	uv run services/${service}/src/${service}/main.py

# Loads the docker image into KinD cluster
push:
	kind load docker-image ${service}:dev --name rwml-34fa

#Build a docker image for the service
build:
	docker build -t ${service}:dev -f docker/${service}.Dockerfile .

# Deploys the service to the KinD cluster
deploy: build push
	kubectl delete -f deployments/dev/${service}/${service}.yaml || true 
	kubectl apply -f deployments/dev/${service}/${service}.yaml

lint:
	ruff check . --fix