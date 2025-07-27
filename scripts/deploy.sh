#!/bin/bash

# Deploy a given service to the given k8s environment

service=$1
env=$2

if [ -z "$service" ]; then
    echo "Usage: $0 <service> <env>"
    exit 1
fi

if [ "$env" != "dev" ] && [ "$env" != "prod" ]; then
    echo "env must be either dev or prod"
    exit 1
fi

cd deployments/${env} || exit 1
eval "$(direnv export bash)"
echo "KUBECONFIG=${KUBECONFIG}"

# If there is a kustomization file, use Kustomize to deploy the service
if [ -f "${service}/kustomization.yaml" ]; then
    echo "Deploying ${service} with kustomize"
    kustomize build ${service} | kubectl delete -f -
    kustomize build ${service} | kubectl apply -f -
else
    # manually apply the deployment manifests
    kubectl delete -f ${service}/${service}.yaml --ignore-not-found=true
    kubectl apply -f ${service}/${service}-d.yaml
fi