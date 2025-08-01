import os
from typing import Optional, Union

import mlflow
import numpy as np
import optuna
import pandas as pd
import sklearn.compose
import sklearn.dummy
import sklearn.ensemble
import sklearn.gaussian_process
import sklearn.kernel_ridge
import sklearn.linear_model
import sklearn.neighbors
import sklearn.neural_network
import sklearn.svm
import sklearn.tree
import yaml
from lazypredict.Supervised import LazyRegressor
from loguru import logger
from sklearn.linear_model import OrthogonalMatchingPursuit
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


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


class OrthogonalMatchingPursuitWithHyperparameterTuning:
    """
    A wrapper around OrthogonalMatchingPursuit that supports hyperparameter tuning using Optuna.
    """

    def __init__(
        self,
        # hyperparam_search_trials: Optional[int] = 0,
        # hyperparam_search_n_splits: Optional[int] = 5
    ):
        """
        Initializes the model.
        """
        # self.model: OrthogonalMatchingPursuit = OrthogonalMatchingPursuit()
        # self.preprocessor =  StandardScaler()
        self.pipeline = self._get_pipeline()
        self.hyperparam_search_trials = None
        self.hyperparam_search_n_splits = None

    def _get_pipeline(self, model_hyperparams: Optional[dict] = None) -> Pipeline:
        """
        Returns the pipeline with the model and preprocessor.
        """
        if model_hyperparams is None:
            pipeline = Pipeline(
                [('scaler', StandardScaler()), ('model', OrthogonalMatchingPursuit())]
            )
        else:
            pipeline = Pipeline(
                [
                    ('scaler', StandardScaler()),
                    ('model', OrthogonalMatchingPursuit(**model_hyperparams)),
                ]
            )
        return pipeline

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        hyperparam_search_trials: Optional[int] = 0,
        hyperparam_search_n_splits: Optional[int] = 5,
    ) -> None:
        """
        Fit the OrthogonalMatchingPursuit model to the training data.

        Args:
            X (pd.DataFrame): Training features.
            y (pd.Series): Target variable.
        """
        self.hyperparam_search_trials = hyperparam_search_trials
        self.hyperparam_search_n_splits = hyperparam_search_n_splits
        if self.hyperparam_search_trials == 0:
            logger.info(
                'No hyperparameter search trials specified, fitting the model with default parameters.'
            )
            self.pipeline.fit(X, y)
        else:
            logger.info(
                f'Hyperparameter search trials specified: {self.hyperparam_search_trials}, '
                'performing hyperparameter tuning...'
            )
            best_hyperparams = self._find_best_hyperparameters(X, y)
            logger.info(f'Best hyperparameters found: {best_hyperparams}')
            # Set the best hyperparameters to the model
            self.pipeline = self._get_pipeline(model_hyperparams=best_hyperparams)
            # Fit the model with the best hyperparameters
            logger.info('Fitting the model with the best hyperparameters...')
            self.pipeline.fit(X, y)

    def _find_best_hyperparameters(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
    ) -> dict:
        """
        Placeholder for hyperparameter tuning logic.
        Args:
            X_train (pd.DataFrame): Training data.
            y_train (pd.Series): Training target.
        Returns:
            dict: Best hyperparameters found.
        """

        def objective(trial: optuna.Trial) -> float:
            """
            Objective function for hyperparameter tuning to make optuna work.

            Args:
                trial (optuna.Trial): The optuna trial object.

            Returns:
                float: The mean absolute error of the model on the split sets.
            """
            # We need to constrain the number of non-zero coefficients to be smaller
            # than the number of features for the model to work
            n_features = X_train.shape[1]
            max_n_nonzero_coefs = max(n_features, 1)
            params = {
                'n_nonzero_coefs': trial.suggest_int(
                    'n_nonzero_coefs', 1, max_n_nonzero_coefs
                ),
                'fit_intercept': trial.suggest_categorical(
                    'fit_intercept', [True, False]
                ),
            }
            # We split the training data into n_splits and evaluate the model on each split
            # And remember it is a time series data, so we need to use TimeSeriesSplit
            tscv = TimeSeriesSplit(n_splits=self.hyperparam_search_n_splits)
            mae_scores = []
            for train_index, val_index in tscv.split(X_train):
                X_train_split, X_val_split = (
                    X_train.iloc[train_index],
                    X_train.iloc[val_index],
                )
                y_train_split, y_val_split = (
                    y_train.iloc[train_index],
                    y_train.iloc[val_index],
                )
                # Build pipeline with the current hyperparameters
                self.pipeline = self._get_pipeline(model_hyperparams=params)
                self.pipeline.fit(X_train_split, y_train_split)
                y_pred = self.pipeline.predict(X_val_split)
                mae_scores.append(mean_absolute_error(y_val_split, y_pred))
            return np.mean(mae_scores)

        # Create an Optuna study to find the best hyperparameters
        study = optuna.create_study(direction='minimize')
        # Run the trials
        logger.info(
            f'Starting hyperparameter tuning with {self.hyperparam_search_trials} trials...'
        )
        study.optimize(objective, n_trials=self.hyperparam_search_trials)
        return study.best_trial.params

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """
        Predict the target variable using the fitted model.
        """
        return self.pipeline.predict(X)


def get_model_candidates(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    n_candidates: int,
) -> list[str]:
    """
    Uses lazypredict to fit N models with default hyperparameters for the given (X_train, y_train), and evaluate them
    with (X_test, y_test)
    It returns a list of model names in order of preference from best to worst.
    Args:
        X_train (pd.DataFrame): Training features.
        y_train (pd.Series): Training target.
        X_test (pd.DataFrame): Test features.
        y_test (pd.Series): Test target.
        n_candidates (int): Number of model candidates to return.
    Returns:
        list[str]: List of model names in order of preference from best to worst.
    """
    # Unset the mlflow tracking URI
    mlflow_tracking_uri = os.environ['MLFLOW_TRACKING_URI']
    del os.environ['MLFLOW_TRACKING_URI']
    # Fit n models with default hyperparameters
    reg = LazyRegressor(
        verbose=0, ignore_warnings=False, custom_metric=mean_absolute_error
    )
    models, _ = reg.fit(X_train, X_test, y_train, y_test)
    models.reset_index(inplace=True)
    # log table to mlflow experiment
    mlflow.log_table(models, 'model_scores_with_default_hyperparameters.json')
    os.environ['MLFLOW_TRACKING_URI'] = mlflow_tracking_uri
    # No need to sort top n model names because LazyPredict sorts them by default
    models_candidates = models['Model'].tolist()[:n_candidates]
    return models_candidates


Model = Union[str, OrthogonalMatchingPursuitWithHyperparameterTuning]


def get_best_model_candidate(
    model_candidates_from_best_to_worst: list[str],
) -> Model:
    """
    Factory function that returns a model from the given list of model candidates.
    It returns the first model that is found in the list.
    Args:
        model_candidates_from_best_to_worst (list[str]): List of model names in order of preference.
    Returns:
        Model: An instance of the model corresponding to the given name.
    """

    def _get_one_model(model_name: str) -> Model:
        if model_name == 'OrthogonalMatchingPursuit':
            return OrthogonalMatchingPursuitWithHyperparameterTuning()
        else:
            raise ValueError(f'Unknown model name: {model_name}')

    model: Model = None
    for model_name in model_candidates_from_best_to_worst:
        try:
            model = _get_one_model(model_name)
            break
        except Exception as e:
            logger.error(f'Model not found {model_name}: {e}')
            continue
    # TODO: handle the case when no model is found
    return model


def get_model_obj(model_name: str) -> Model:
    """
    Factory function that returns a model object based on the model name.
    Args:
        model_name (str): Name of the model.
    Returns:
        Model: An instance of the model corresponding to the given name.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, 'param_space.yaml')
    with open(yaml_path, 'r', encoding='utf-8') as f:
        param_space = yaml.safe_load(f)
    param_space = param_space.get(model_name)
    # breakpoint()
    if model_name == 'OrthogonalMatchingPursuit':
        return OrthogonalMatchingPursuitWithHyperparameterTuning()
    elif param_space is not None:
        return LazyPredictSuggestedModelWithHyperparameterTuning(model_cls=model_name)
    else:
        raise ValueError(f'Unknown model name: {model_name}')


class LazyPredictSuggestedModelWithHyperparameterTuning:
    """
    A wrapper around LazyPredict that supports hyperparameter tuning using Optuna.
    This class is used to suggest a model based on the given training data.
    """

    def __init__(
        self,
        model_cls: str,
    ):
        """
        Initializes the model.
        model_cls: sklearn-like estimator class (not an instance)
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        yaml_path = os.path.join(current_dir, 'param_space.yaml')
        self.model_cls = self._get_sklearn_class(model_cls)
        with open(yaml_path, 'r', encoding='utf-8') as f:
            param_space = yaml.safe_load(f)
        self._param_space = param_space.get(model_cls)
        self.pipeline = self._get_pipeline()
        self.hyperparam_search_trials = None
        self.hyperparam_search_n_splits = None

    def _get_sklearn_class(self, model_cls: str):
        """
        Returns the sklearn-like class for the given model name.
        Args:
            model_cls (str): Name of the model class.
        Returns:
            sklearn-like class: The sklearn-like class corresponding to the given name.
        """
        # List the sklearn modules that iclude the model classes which are used in the param_space.yaml
        # This is a workaround to avoid importing all sklearn modules at once
        sklearn_modules = [
            sklearn.ensemble,
            sklearn.linear_model,
            sklearn.compose,
            sklearn.neighbors,
            sklearn.svm,
            sklearn.tree,
            sklearn.dummy,
            sklearn.gaussian_process,
            sklearn.neural_network,
            sklearn.kernel_ridge,
        ]
        for module in sklearn_modules:
            if hasattr(module, model_cls):
                return getattr(module, model_cls)
        # If the model class is not found in the sklearn modules, raise an error
        raise ValueError(
            f'Model class {model_cls} not found in sklearn modules supported by LazyPredict'
        )

    def _suggest_params(
        self,
        trial: optuna.Trial,
    ) -> dict:
        params = {}
        for param_name, param_info in self._param_space.items():
            ptype = param_info[0]
            if ptype == 'int':
                params[param_name] = trial.suggest_int(
                    param_name, param_info[1][0], param_info[1][1]
                )
            elif ptype == 'float':
                params[param_name] = trial.suggest_float(
                    param_name, param_info[1][0], param_info[1][1]
                )
            elif ptype == 'categorical':
                params[param_name] = trial.suggest_categorical(
                    param_name, param_info[1]
                )
            elif ptype == 'list':
                params[param_name] = trial.suggest_categorical(
                    param_name, param_info[1]
                )
            else:
                raise ValueError(f'Unknown param type {ptype}')
        return params

    def _get_pipeline(self, model_hyperparams: Optional[dict] = None) -> Pipeline:
        """
        Returns the pipeline with the model and preprocessor.
        """
        if model_hyperparams is None:
            pipeline = Pipeline(
                [('scaler', StandardScaler()), ('model', self.model_cls())]
            )
        else:
            pipeline = Pipeline(
                [
                    ('scaler', StandardScaler()),
                    ('model', self.model_cls(**model_hyperparams)),
                ]
            )
        return pipeline

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        hyperparam_search_trials: Optional[int] = 0,
        hyperparam_search_n_splits: Optional[int] = 5,
    ) -> None:
        """
        Fit the model to the training data.

        Args:
            X (pd.DataFrame): Training features.
            y (pd.Series): Target variable.
        """
        self.hyperparam_search_trials = hyperparam_search_trials
        self.hyperparam_search_n_splits = hyperparam_search_n_splits
        if self.hyperparam_search_trials == 0:
            logger.info(
                'No hyperparameter search trials specified, fitting the model with default parameters.'
            )
            self.pipeline.fit(X, y)
        else:
            logger.info(
                f'Hyperparameter search trials specified: {self.hyperparam_search_trials}, '
                'performing hyperparameter tuning...'
            )
            best_hyperparams = self._find_best_hyperparameters(X, y)
            logger.info(f'Best hyperparameters found: {best_hyperparams}')
            # Set the best hyperparameters to the model
            self.pipeline = self._get_pipeline(model_hyperparams=best_hyperparams)
            # Fit the model with the best hyperparameters
            logger.info('Fitting the model with the best hyperparameters...')
            self.pipeline.fit(X, y)

    def _find_best_hyperparameters(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
    ) -> dict:
        """
        Placeholder for hyperparameter tuning logic.
        Args:
            X_train (pd.DataFrame): Training data.
            y_train (pd.Series): Training target.
        Returns:
            dict: Best hyperparameters found.
        """

        def objective(trial: optuna.Trial) -> float:
            """
            Objective function for hyperparameter tuning to make optuna work.

            Args:
                trial (optuna.Trial): The optuna trial object.

            Returns:
                float: The mean absolute error of the model on the split sets.
            """
            params = self._suggest_params(trial)
            # We split the training data into n_splits and evaluate the model on each split
            # And remember it is a time series data, so we need to use TimeSeriesSplit
            tscv = TimeSeriesSplit(n_splits=self.hyperparam_search_n_splits)
            mae_scores = []
            for train_index, val_index in tscv.split(X_train):
                X_train_split, X_val_split = (
                    X_train.iloc[train_index],
                    X_train.iloc[val_index],
                )
                y_train_split, y_val_split = (
                    y_train.iloc[train_index],
                    y_train.iloc[val_index],
                )
                # Build pipeline with the current hyperparameters
                self.pipeline = self._get_pipeline(model_hyperparams=params)
                self.pipeline.fit(X_train_split, y_train_split)
                y_pred = self.pipeline.predict(X_val_split)
                mae_scores.append(mean_absolute_error(y_val_split, y_pred))
            return np.mean(mae_scores)

        # Create an Optuna study to find the best hyperparameters
        study = optuna.create_study(direction='minimize')
        # Run the trials
        logger.info(
            f'Starting hyperparameter tuning with {self.hyperparam_search_trials} trials...'
        )
        study.optimize(objective, n_trials=self.hyperparam_search_trials)
        return study.best_trial.params

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """
        Predict the target variable using the fitted model.
        """
        return self.pipeline.predict(X)
