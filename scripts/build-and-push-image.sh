#!/bin/bash

# Builds a docker image for the given dockerfile and pushes it to the specified registry.
# given by the env variable

image_name=$1
env=$2

# Check if the required arguments are provided
if [ -z "$image_name" ] || [ -z "$env" ]; then
  echo "Usage: $0 <image_name> <env>"
  exit 1
fi

# Check that env is either dev or prod
if [ "$env" != "dev" ] && [ "$env" != "prod" ]; then
  echo "Error: env must be either 'dev' or 'prod'."
  exit 1
fi

if [ "$env" == "dev" ]; then
  echo "Building image for dev..."
  docker build -t ${image_name}:dev -f docker/${image_name}.Dockerfile .
  kind load docker-image ${image_name}:dev --name rwml-34fa
else
  echo "Building image for prod..."
  docker buildx build --push \
  --platform linux/arm64 \
  -t ghcr.io/karimabousselham/${image_name}:0.1.4-beta.$(date +%s) \
  -f docker/${image_name}.Dockerfile .
fi


