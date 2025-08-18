#!/bin/bash

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install --create-namespace --wait prometheus prometheus-community/prometheus \
    --namespace=monitoring --values manifests/prometheus-values.yaml \
    --set server.service.port=9090 \
    --set server.service.targetPort=9090