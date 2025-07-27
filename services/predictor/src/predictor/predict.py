from datetime import datetime, timezone
from typing import Optional

import mlflow
import pandas as pd
from loguru import logger
from risingwave import OutputFormat, RisingWave, RisingWaveConnOptions

from predictor.model_registry import get_model_name, load_model


def predict(
    mlflow_tracking_uri: str,
    risingwave_host: str,
    risingwave_port: int,
    risingwave_user: str,
    risingwave_password: str,
    risingwave_database: str,
    risingwave_schema: str,
    risingwave_input_table: str,
    risingwave_output_table: str,
    pair: str,
    prediction_horizon_seconds: int,
    candle_seconds: int,
    model_version: Optional[str] = 'latest',
):
    """
    Generates a new prediction as soon as new data is available in the `risingwave_input_table`.

    Steps:
    1. Load the model from the model registry.
    2. Start listening to data changes in the `risingwave_input_table`.
    3. For each new or updated row, generate a prediction.
    4. Write the prediction to the `risingwave_output_table`.
    Args:
        mlflow_tracking_uri: The URI of the Mlflow tracking server,
        risingwave_host: The host of the RisingWave server,
        risingwave_port: The port of the RisingWave server,
        risingwave_user: The user of the RisingWave server,
        risingwave_password: The password of the RisingWave server,
        risingwave_database: The database of the RisingWave server,
        risingwave_schema: The schema of the risingwave tables,
        risingwave_input_table,
        risingwave_output_table,
        pair,
        prediction_horizon_seconds,
        candle_seconds,
        model_version,
    """
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    # Step 1. Load the model from the model registry
    model_name = get_model_name(pair, candle_seconds, prediction_horizon_seconds)
    logger.info(f'Loading model {model_name} with version {model_version}')
    # breakpoint()
    model, features = load_model(model_name=model_name, model_version=model_version)
    # Step 2. Start listening to data changes in the `risingwave_input_table`
    rw = RisingWave(
        RisingWaveConnOptions.from_connection_info(
            host=risingwave_host,
            port=risingwave_port,
            user=risingwave_user,
            password=risingwave_password,
            database=risingwave_database,
        )
    )

    def prediction_handler(data: pd.DataFrame):
        """
        Maps the given input data changes to fresh predictions using the loaded model.
        Writes these predictions into the `risignwave_output_table`.
        """
        logger.info(f'Received {data.shape[0]} updates from {risingwave_input_table}')
        # print(data)
        # Filter only Insert and Updates
        data = data[data['op'].isin(['Insert', 'UpdateInsert'])]
        # For the given pair
        data = data[data['pair'] == pair]
        # for the given candle_seconds
        data = data[data['candle_seconds'] == candle_seconds]
        # Keep only inserts and updates of recent data
        current_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        data = data[data['window_start_ms'] > current_ms - 1000 * candle_seconds * 2]
        # keep only the `features` columns
        data = data[features]
        if data.empty:
            return
        # Generate predictions
        predictions: pd.Series = model.predict(data)
        ts_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        # Write predictions to `risingwave_output_table`

        # Prepare the output dataframe
        output = pd.DataFrame()
        output['predicted_price'] = predictions
        output['pair'] = pair
        output['ts_ms'] = ts_ms
        output['model_name'] = model_name
        output['model_version'] = model_version
        output['predicted_ts_ms'] = (
            data['window_start_ms']
            + (prediction_horizon_seconds + candle_seconds) * 1000
        ).to_list()
        logger.info(
            f'Writing {len(output)} predictions to table {risingwave_output_table}'
        )
        rw.insert(table_name=risingwave_output_table, data=output)
        # breakpoint()

    rw.on_change(
        subscribe_from=risingwave_input_table,
        schema_name=risingwave_schema,
        handler=prediction_handler,
        output_format=OutputFormat.DATAFRAME,
    )


if __name__ == '__main__':
    from predictor.config import predictor_config as config

    predict(
        mlflow_tracking_uri=config.mlflow_tracking_uri,
        risingwave_host=config.risingwave_host,
        risingwave_port=config.risingwave_port,
        risingwave_user=config.risingwave_user,
        risingwave_password=config.risingwave_password,
        risingwave_database=config.risingwave_database,
        risingwave_schema=config.risingwave_schema,
        risingwave_input_table=config.risingwave_input_table,
        risingwave_output_table=config.risingwave_output_table,
        pair=config.pair,
        prediction_horizon_seconds=config.prediction_horizon_seconds,
        candle_seconds=config.candle_seconds,
        model_version=config.model_version,
    )
