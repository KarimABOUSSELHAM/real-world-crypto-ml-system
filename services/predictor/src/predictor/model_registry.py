from typing import Any, Optional, Tuple

import mlflow
import pandas as pd
from loguru import logger
from mlflow.models import infer_signature


def get_model_name(
    pair: str,
    candle_seconds: int,
    prediction_horizon_seconds: int,
):
    """
    Generates a unique model name based on the trading pair, candle seconds, and prediction horizon.
    """
    return (
        f'{pair.replace("/", "-")}_{candle_seconds}_{prediction_horizon_seconds}_model'
    )


def load_model(
    model_name: str,
    model_version: Optional[str] = 'latest',
) -> Tuple[Any, list[str]]:
    """
    Loads model name with version tag from the Mlflow model registry together with the model's
    input schema.

    Args:
        model_name (str): The name of the model to load from the Mlflow model registry.
        model_version (Optional[str], optional): The version of the registered model. Defaults to "latest".
    Returns:
        model: The model object and the model's features list.
    """
    model = mlflow.sklearn.load_model(model_uri=f'models:/{model_name}/{model_version}')
    # Get the model info which contains the signature
    model_info = mlflow.models.get_model_info(
        model_uri=f'models:/{model_name}/{model_version}'
    )
    # Access the signature and extract the list of model features
    features = model_info.signature.inputs.input_names()
    return model, features


def push_model(
    model,
    X_test: pd.DataFrame,
    model_name: str,
) -> None:
    """
    Pushes the trained model to the MLflow model registry.

    Args:
        model : The model to be pushed.
        X_test (pd.DataFrame): Test data used for inference to generate the model signature.
        model_name (str): The name under which the model will be registered in MLflow.
    """
    y_pred = model.predict(X_test)
    signature = infer_signature(X_test, y_pred)
    logger.info(f'Pushing model {model_name} to MLflow model registry')
    mlflow.sklearn.log_model(
        model,
        artifact_path='model',
        signature=signature,
        registered_model_name=model_name,
    )
    logger.info(f'Model {model_name} pushed successfully to MLflow model registry')
