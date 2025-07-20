# The training script for the predictor service.

import great_expectations as ge
import mlflow
import pandas as pd
from loguru import logger
from risingwave import OutputFormat, RisingWave, RisingWaveConnOptions
from ydata_profiling import ProfileReport


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


def validate_data(ts_data: pd.DataFrame):
    """
    Runs a battery of validation checks on the time series data.
    If any of the checks fails, an exception is raised, so the training process can be aborted.

    Args:
        ts_data (pd.DataFrame): input time series data to validate.
    """
    ge_df = ge.from_pandas(ts_data)
    validation_result = ge_df.expect_column_values_to_be_between(
        column='close',
        min_value=0,
    )
    if not validation_result.success:
        raise Exception("Column 'close' has values less then 0")

    # TODO: Add more validation checks
    # For example:
    # Check for null values
    # Check for duplicates
    # Check the data is sorted by timestamp


def load_ts_data_from_risingwave(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
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
    SELECT * FROM public.technical_indicators
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
    risingWave_host: str,
    risingWave_port: int,
    risingWave_user: str,
    risingWave_password: str,
    risingWave_database: str,
    pair: str,
    lookback_period: int,
    candle_seconds: int,
    prediction_horizon_seconds: int,
    train_test_split_ratio: float,
    n_rows_for_data_profiling: int,
    eda_report_html_path: str,
    features: list[str],
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
    from predictor.names import get_experiment_name

    mlflow.set_experiment(
        experiment_name=get_experiment_name(
            pair=pair,
            candle_seconds=candle_seconds,
            prediction_horizon_seconds=prediction_horizon_seconds,
        )
    )
    with mlflow.start_run():
        logger.info('Started MLflow run')
        mlflow.log_param('features', features)
        mlflow.log_param('pair', pair)
        mlflow.log_param('days_in_past', lookback_period)
        mlflow.log_param('candle_seconds', candle_seconds)
        mlflow.log_param('prediction_horizon_seconds', prediction_horizon_seconds)
        mlflow.log_param('train_test_split_ratio', train_test_split_ratio)
        mlflow.log_param('n_rows_data_profiling', n_rows_for_data_profiling)
        # Step 1: Load the time series data from RisingWave
        ts_data = load_ts_data_from_risingwave(
            host=risingWave_host,
            port=risingWave_port,
            user=risingWave_user,
            password=risingWave_password,
            database=risingWave_database,
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
        # drop the last rows with NaN target values
        ts_data = ts_data.dropna(subset=['target'])
        # log the data to mlflow
        dataset = mlflow.data.from_pandas(ts_data)
        mlflow.log_input(dataset, context='training')
        # Log dataset size
        mlflow.log_param('ts_data shape', ts_data.shape)
        # Step 3: Validate the data
        validate_data(ts_data)
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
        from predictor.models import BaselineModel

        baseline_model = BaselineModel()
        y_pred = baseline_model.predict(X_test)
        from sklearn.metrics import mean_absolute_error

        test_mae_baseline = mean_absolute_error(y_test, y_pred)
        mlflow.log_metric('test_mae_baseline', test_mae_baseline)
        logger.info(f'Test MAE for baseline model: {test_mae_baseline:.4f}')
    # Step 8: Train a set of n models to get a sense what model is supposed to be the best
    # We use lazypredict which uses default hyperparamters for each model.
    from predictor.models import generate_lazypredict_model_table

    model_scores = generate_lazypredict_model_table(X_train, y_train, X_test, y_test)
    model_scores.reset_index(inplace=True)
    mlflow.log_table(model_scores, 'model_scores_with_default_hyperparameters_2.json')
    logger.info(model_scores.to_string())
    # Step 9: Pick the best model from the table and train it with the best hyperparameters
    # TODO: Implement this step


if __name__ == '__main__':
    train(
        mlflow_tracking_uri='http://localhost:5000',
        risingWave_host='localhost',
        risingWave_port=4567,
        risingWave_user='root',
        risingWave_password='',
        risingWave_database='dev',
        pair='ETH/EUR',
        lookback_period=10,
        candle_seconds=60,
        prediction_horizon_seconds=300,
        n_rows_for_data_profiling=100,
        eda_report_html_path='./eda_report.html',
        train_test_split_ratio=0.8,
        features=[
            'open',
            'high',
            'low',
            'close',
            'window_start_ms',
            'window_end_ms',
            'volume',
            'sma_7',
            'sma_14',
            'sma_21',
            'sma_60',
            'ema_7',
            'ema_14',
            'ema_21',
            'ema_60',
            'rsi_7',
            'rsi_14',
            'rsi_21',
            'rsi_60',
            'macd_7',
            'macdsignal_7',
            'macdhist_7',
            'obv',
        ],
    )
