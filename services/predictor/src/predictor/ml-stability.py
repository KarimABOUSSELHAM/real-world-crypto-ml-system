"""
This script is custom Prometheus exporter which takes mae metrics from mlflow
and converts them to Prometheus metrics for consumption
"""

import time

import mlflow
from prometheus_client import Gauge, start_http_server

from predictor.model_registry import get_model_name

mae_test_gauge = Gauge(
    'mlflow_model_mae_test',
    'Mean Absolute Error of the model on the test set',
    ['experiment', 'run_id', 'model_name'],
)


def collect_mae_metrics(
    mlflow_tracking_uri: str,
    pair: str,
    candle_seconds: int,
    prediction_horizon_seconds: int,
):
    """
    Collects MAE metrics from MLflow and updates Prometheus gauges.
    Args:
        uri (str): The MLflow tracking URI.
    """
    mlflow.set_tracking_uri(uri=mlflow_tracking_uri)
    client = mlflow.client.MlflowClient()
    # Step1. Load the experiment name
    experiment_name = get_model_name(
        pair=pair,
        candle_seconds=candle_seconds,
        prediction_horizon_seconds=prediction_horizon_seconds,
    )
    experiment = client.get_experiment_by_name(experiment_name)
    # Step2. Search for the latest runs in the experiment
    runs = client.search_runs(experiment_ids=[experiment.experiment_id], max_results=1)
    if runs:
        latest_run = runs[0]
        test_mae = latest_run.data.metrics.get('test_mae')
        model_name = latest_run.data.tags.get('model_name', 'unknown')
        if test_mae is not None:
            # Step3. Update the Prometheus gauge with the latest MAE metric
            mae_test_gauge.labels(
                experiment=experiment_name,
                run_id=latest_run.info.run_id,
                model_name=model_name,
            ).set(test_mae)


if __name__ == '__main__':
    from predictor.config import stability_config as config

    start_http_server(config.exporter_port)
    while True:
        collect_mae_metrics(
            mlflow_tracking_uri=config.mlflow_tracking_uri,
            pair=config.pair,
            candle_seconds=config.candle_seconds,
            prediction_horizon_seconds=config.prediction_horizon_seconds,
        )
        time.sleep(30)
