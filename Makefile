# Runs the service locally
dev:
	uv run services/${service}/src/${service}/main.py

build-and-push:
	./scripts/build-and-push-image.sh ${image_name} ${env}

# Deploys the service to the given environment
deploy:
	./scripts/deploy.sh ${service} ${env}

lint:
	ruff check . --fix