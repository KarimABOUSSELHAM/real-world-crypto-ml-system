# The training script for the predictor service.

import os
from typing import Optional

import mlflow
import numpy as np
import pandas as pd
from loguru import logger
from risingwave import OutputFormat, RisingWave, RisingWaveConnOptions
from sklearn.metrics import mean_absolute_error
from ydata_profiling import ProfileReport

from predictor.data_validation import validate_data
from predictor.model_registry import get_model_name, push_model
from predictor.models import BaselineModel, get_model_candidates, get_model_obj


def generate_data_exploratory_analysis_report(
    ts_data: pd.DataFrame,
    output_html_path: str,
):
    """
    Generates a data exploratory analysis report for the time series data.
    This report can be used to understand the data better and identify potential issues.

    Args:
        ts_data (pd.DataFrame): input time series data to analyze.
        output_html_path (str): The path to the html file which saves the report.
    """
    logger.info('Generating data exploratory analysis report...')
    profile = ProfileReport(
        ts_data, tsmode=True, sortby='window_start_ms', title='Technical indicators EDA'
    )
    profile.to_file(output_html_path)


def load_ts_data_from_risingwave(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    table: str,
    pair: str,
    lookback_period: int,
    candle_seconds: int,
) -> pd.DataFrame:
    """
    Loads time series data from RisingWave for the specific crypto.
    Args:
        host (str): The RisingWave host.
        port (int): The RisingWave port.
        user (str): The RisingWave user.
        password (str): The RisingWave password.
        database (str): The RisingWave database.
        pair (str): The crypto pair to load data for.
        lookback_period (int): The number of days in the past to load data for.
        candle_seconds (int): The candle duration in seconds.
    Returns:
        pd.DataFrame: The time series data for the specified crypto pair.
    """
    logger.info('Establishing connection to RisingWave...')
    rw = RisingWave(
        RisingWaveConnOptions.from_connection_info(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
        )
    )
    query = f"""
    SELECT * FROM {table}
    WHERE pair='{pair}' and to_timestamp(window_start_ms/1000) > now() - interval '{lookback_period} day'
    and candle_seconds={candle_seconds}
    order by window_start_ms;
    """
    ts_data = rw.fetch(query, format=OutputFormat.DATAFRAME)
    logger.info(
        f'Successfully loaded {len(ts_data)} time series rows data from RisingWave for the pair {pair}.'
    )
    return ts_data


def train(
    mlflow_tracking_uri: str,
    risingwave_host: str,
    risingwave_port: int,
    risingwave_user: str,
    risingwave_password: str,
    risingwave_database: str,
    risingwave_table: str,
    pair: str,
    lookback_period: int,
    candle_seconds: int,
    prediction_horizon_seconds: int,
    train_test_split_ratio: float,
    n_rows_for_data_profiling: int,
    eda_report_html_path: str,
    max_percentage_rows_with_nulls: float,
    features: list[str],
    hyperparam_search_trials: int,
    hyperparam_search_n_splits: int,
    model_name: Optional[str] = None,
    n_model_candidates: Optional[int] = 10,
    max_percentage_diff_vs_baseline: Optional[float] = 0.05,
):
    """
    Trains a predictor for the given pair and data, and if the model is good enough, it pushes it
    to the model registry.
    """
    # Set the MLflow tracking URI
    logger.info('Starting training process...')
    logger.info(f'Setting MLflow tracking URI to {mlflow_tracking_uri}')
    mlflow.set_tracking_uri(uri=mlflow_tracking_uri)
    logger.info('Setting MLflow experiment...')
    experiment_name = get_model_name(
        pair=pair,
        candle_seconds=candle_seconds,
        prediction_horizon_seconds=prediction_horizon_seconds,
    )
    mlflow.set_experiment(experiment_name=experiment_name)
    with mlflow.start_run():
        logger.info('Started MLflow run')
        mlflow.log_param('features', features)
        mlflow.log_param('pair', pair)
        mlflow.log_param('days_in_past', lookback_period)
        mlflow.log_param('candle_seconds', candle_seconds)
        mlflow.log_param('prediction_horizon_seconds', prediction_horizon_seconds)
        mlflow.log_param('train_test_split_ratio', train_test_split_ratio)
        mlflow.log_param('n_rows_data_profiling', n_rows_for_data_profiling)
        if model_name:
            mlflow.log_param('model_name', model_name)
        mlflow.log_param(
            'max_percentage_diff_vs_baseline', max_percentage_diff_vs_baseline
        )
        # Step 1: Load the time series data from RisingWave
        ts_data = load_ts_data_from_risingwave(
            host=risingwave_host,
            port=risingwave_port,
            user=risingwave_user,
            password=risingwave_password,
            database=risingwave_database,
            table=risingwave_table,
            pair=pair,
            lookback_period=lookback_period,
            candle_seconds=candle_seconds,
        )
        # Keep only the features
        ts_data = ts_data[features]
        # Step 2: Add a target column
        ts_data['target'] = ts_data['close'].shift(
            -prediction_horizon_seconds // candle_seconds
        )
        # log the data to mlflow
        dataset = mlflow.data.from_pandas(ts_data)
        mlflow.log_input(dataset, context='training')
        # Log the actual data as artifact
        ts_data.to_csv('ts_data.csv', index=False)
        mlflow.log_artifact('ts_data.csv', artifact_path='datasets')
        os.remove('ts_data.csv')
        # Log dataset size
        mlflow.log_param('ts_data shape', ts_data.shape)
        # Step 3: Validate the data
        ts_data = validate_data(
            ts_data, max_percentage_rows_with_nulls=max_percentage_rows_with_nulls
        )
        # Plot data drift of the current dataset vs the data used by the model
        # in the model registry
        from predictor.data_validation import generate_data_drift_report

        report_path = generate_data_drift_report(
            ts_data, experiment_name=experiment_name
        )
        mlflow.log_artifact(local_path=report_path, artifact_path='reports')
        # Step 4: Profile the data
        ts_data_to_profile = (
            ts_data.head(n_rows_for_data_profiling)
            if n_rows_for_data_profiling
            else ts_data
        )
        generate_data_exploratory_analysis_report(
            ts_data_to_profile, output_html_path=eda_report_html_path
        )
        logger.info(
            'Data exploratory analysis report created and being pushed to mlflow.'
        )
        mlflow.log_artifact(local_path=eda_report_html_path, artifact_path='eda_report')
        # Step 5: Split the data into train and test sets
        train_size = int(len(ts_data) * train_test_split_ratio)
        train_data = ts_data[:train_size]
        test_data = ts_data[train_size:]
        mlflow.log_param('train_data shape', train_data.shape)
        mlflow.log_param('test_data shape', test_data.shape)
        # Step 6: Split data into features and target
        X_train = train_data.drop(columns=['target'])
        y_train = train_data['target']
        X_test = test_data.drop(columns=['target'])
        y_test = test_data['target']
        mlflow.log_param('X_train shape', X_train.shape)
        mlflow.log_param('y_train shape', y_train.shape)
        mlflow.log_param('X_test shape', X_test.shape)
        mlflow.log_param('y_test shape', y_test.shape)
        # Step 7: Train a baseline model

        baseline_model = BaselineModel()
        y_pred_baseline = baseline_model.predict(X_test)
        test_mae_baseline = mean_absolute_error(y_test, y_pred_baseline)
        mlflow.log_metric('test_mae_baseline', test_mae_baseline)
        logger.info(f'Test MAE for baseline model: {test_mae_baseline:.4f}')
        # Step 8:Find the best model candidate,if model_name is not provided
        best_model_name = None
        best_cv_score = float('inf')  # Lower MAE is better
        from sklearn.model_selection import TimeSeriesSplit

        tscv = TimeSeriesSplit(n_splits=hyperparam_search_n_splits)
        if model_name is None:
            # We fit n_model_candidates models with default hyperparameters to
            # find the best model candidate
            model_names = get_model_candidates(
                X_train,
                y_train,
                X_test,
                y_test,
                n_candidates=n_model_candidates,
            )
            # model_name = model_names[0]
            for model_name in model_names:
                logger.info(f'Found model candidate: {model_name}')
                cv_mae_scores = []
                model = get_model_obj(model_name)
                for train_index, val_index in tscv.split(X_train):
                    X_tr, X_val = X_train.iloc[train_index], X_train.iloc[val_index]
                    y_tr, y_val = y_train.iloc[train_index], y_train.iloc[val_index]
                    # in the next step
                    # Step 9: Pick the best model from the table and train it with the best hyperparameters
                    # logger.info(f'Start training model: {model} with hyperparams search')
                    model.fit(
                        X_tr,
                        y_tr,
                        hyperparam_search_trials=hyperparam_search_trials,
                        hyperparam_search_n_splits=hyperparam_search_n_splits,
                    )
                    y_val_pred = model.predict(X_val)
                    val_mae = mean_absolute_error(y_val, y_val_pred)
                    cv_mae_scores.append(val_mae)
                mean_cv_mae = np.mean(cv_mae_scores)
                logger.info(f'Model candidate {model_name} CV MAE: {mean_cv_mae:.4f}')
                # mlflow.log_metric(f'cv_mae_{model_name}', mean_cv_mae)
                if mean_cv_mae < best_cv_score:
                    best_cv_score = mean_cv_mae
                    best_model_name = model_name
            logger.info(
                f'Best model candidate based on CV MAE: {best_model_name} with score {best_cv_score:.4f}'
            )
            mlflow.log_param('best_model_name', best_model_name)
            # Now get the best model and do hyperparameter tuning on the training data
            best_model = get_model_obj(best_model_name)
            best_model.fit(
                X_train,
                y_train,
                hyperparam_search_trials=hyperparam_search_trials,
                hyperparam_search_n_splits=hyperparam_search_n_splits,
            )
            # Step 10: Final evaluation on the test set
            y_test_pred = best_model.predict(X_test)
            test_mae = mean_absolute_error(y_test, y_test_pred)
            logger.info(f'Test MAE for best model {best_model_name}: {test_mae:.4f}')
            mlflow.log_metric('test_mae', test_mae)
        else:
            # If model_name is provided, we use it directly
            logger.info(f'Using provided model name: {model_name}')
            best_model = get_model_obj(model_name)
            best_model.fit(X_train, y_train)
            y_test_pred = best_model.predict(X_test)
            test_mae = mean_absolute_error(y_test, y_test_pred)
            logger.info(f'Test MAE for model {model_name}: {test_mae:.4f}')
            mlflow.log_metric('test_mae', test_mae)
        # Step 11: Log the model to MLflow
        if (
            test_mae - test_mae_baseline
            <= max_percentage_diff_vs_baseline * test_mae_baseline
        ):
            logger.info(
                f'Model {model_name} is good enough, pushing it to MLflow model registry.'
            )
            model_name = get_model_name(
                pair=pair,
                candle_seconds=candle_seconds,
                prediction_horizon_seconds=prediction_horizon_seconds,
            )
            push_model(
                model=best_model,
                X_test=X_test,
                model_name=model_name,
            )
        else:
            logger.info(
                f'Model {model_name} is not good enough, not pushing it to MLflow model registry.'
            )


if __name__ == '__main__':
    from predictor.config import train_config as config

    train(
        mlflow_tracking_uri=config.mlflow_tracking_uri,
        risingwave_host=config.risingwave_host,
        risingwave_port=config.risingwave_port,
        risingwave_user=config.risingwave_user,
        risingwave_password=config.risingwave_password,
        risingwave_database=config.risingwave_database,
        risingwave_table=config.risingwave_table,
        pair=config.pair,
        lookback_period=config.lookback_period,
        candle_seconds=config.candle_seconds,
        prediction_horizon_seconds=config.prediction_horizon_seconds,
        n_rows_for_data_profiling=config.n_rows_for_data_profiling,
        eda_report_html_path=config.eda_report_html_path,
        train_test_split_ratio=config.train_test_split_ratio,
        features=config.features,
        hyperparam_search_trials=config.hyperparam_search_trials,
        hyperparam_search_n_splits=config.hyperparam_search_n_splits,
        model_name=config.model_name,
        n_model_candidates=config.n_model_candidates,
        max_percentage_rows_with_nulls=config.max_percentage_rows_with_nulls,  # Example parameter for data validation
        max_percentage_diff_vs_baseline=config.max_percentage_diff_vs_baseline,  # Example parameter for model performance validation
    )
