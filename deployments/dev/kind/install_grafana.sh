#!/bin/bash
# Check if the `grafana-values.yaml` file contains the `.alertEmails` field
if yq eval '.alertEmails' manifests/grafana-values.yaml &>/dev/null; then
    echo "alertEmails field found in grafana-values.yaml"
    helm repo add grafana https://grafana.github.io/helm-charts
    echo "Setting Grafana Alerting..."
    helm upgrade --install --create-namespace --wait grafana grafana/grafana \
    --namespace=monitoring --values manifests/grafana-values.yaml \
    --set-file dashboards.default.candles-dashboard.json=../../../dashboards/candles.json
else
    helm repo add grafana https://grafana.github.io/helm-charts
    helm upgrade --install --create-namespace --wait grafana grafana/grafana \
    --namespace=monitoring --values manifests/grafana-values.yaml \
    --set-file dashboards.default.candles-dashboard.json=../../../dashboards/candles.json
fi