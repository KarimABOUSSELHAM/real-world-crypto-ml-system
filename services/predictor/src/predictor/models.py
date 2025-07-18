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
