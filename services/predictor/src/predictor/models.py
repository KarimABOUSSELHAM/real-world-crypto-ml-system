import pandas as pd


class BaselineModel:
    def __init__(self):
        pass

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """
        Fit the baseline model to the training data.
        """
        pass

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """
        Predict using the baseline model.
        """
        return X['close']


def generate_lazypredict_model_table(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> pd.DataFrame:
    """
    Uses lazypredict to fit N models with default hyperparameters for the given (X_train, y_train), and evaluate them
    with (X_test, y_test)
    """
    # Unset the mlflow tracking URI
    import os

    mlflow_tracking_uri = os.environ['MLFLOW_TRACKING_URI']
    del os.environ['MLFLOW_TRACKING_URI']

    from lazypredict.Supervised import LazyRegressor
    from sklearn.metrics import mean_absolute_error

    reg = LazyRegressor(
        verbose=0, ignore_warnings=False, custom_metric=mean_absolute_error
    )
    models, _ = reg.fit(X_train, X_test, y_train, y_test)
    os.environ['MLFLOW_TRACKING_URI'] = mlflow_tracking_uri
    return models
