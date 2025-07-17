# The training script for the predictor service.
import great_expectations as ge
import pandas as pd
from loguru import logger
from risingwave import OutputFormat, RisingWave, RisingWaveConnOptions


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


def train(
    risingWave_host: str,
    risingWave_port: int,
    risingWave_user: str,
    risingWave_password: str,
    risingWave_database: str,
    pair: str,
    lookback_period: int,
    candle_seconds: int,
    prediction_horizon_seconds: int,
):
    """
    Trains a predictor for the given pair and data, and if the model is good enough, it pushes it
    to the model registry.
    """
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
    # Step 2: Add a target column
    ts_data['target'] = ts_data['close'].shift(
        -prediction_horizon_seconds // candle_seconds
    )
    # Step 3: Validate the data
    validate_data(ts_data)
    # Step 4: Profile the data


if __name__ == '__main__':
    train(
        risingWave_host='localhost',
        risingWave_port=4567,
        risingWave_user='root',
        risingWave_password='',
        risingWave_database='dev',
        pair='ETH/EUR',
        lookback_period=30,
        candle_seconds=60,
        prediction_horizon_seconds=300,
    )
