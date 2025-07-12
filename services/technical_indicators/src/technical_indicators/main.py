from loguru import logger
from quixstreams import Application

from technical_indicators.candle import update_candles_in_state
from technical_indicators.indicators import compute_technical_indicators


def run(
    kafka_broker_address: str,
    kafka_input_topic: str,
    kafka_output_topic: str,
    kafka_consumer_group: str,
    candle_seconds: int,
):
    """
    Transforms a stream of input candles into a stream of output technical indicators.

    In three steps:
    - Ingests candles from `kafka_input_topic`
    - Computes technical indicators
    - Produces technical indicators to `kafka_output_topic`
    Args:
        kafka_broker_address (str): Address of the Kafka broker.
        kafka_input_topic (str): Name of the Kafka topic to read candles from.
        kafka_output_topic (str): Name of the Kafka topic to write technical indicators to.
        kafka_consumer_group (str): Kafka consumer group name.
        candle_seconds (int): Duration of each candle in seconds.

    Returns:
        None
    """
    app = Application(
        broker_address=kafka_broker_address,
        consumer_group=kafka_consumer_group,
    )
    # Define the input topic
    candles_topic = app.topic(
        name=kafka_input_topic,
        value_serializer='json',
    )
    # Define the output topic
    technical_indicators_topic = app.topic(
        name=kafka_output_topic,
        value_serializer='json',
    )
    # Step 1. Ingest candles from the input topic for the given `candle_seconds`
    # Create a streaming dataframe connected to the input topic
    sdf = app.dataframe(topic=candles_topic)

    # Filter the candles for the given `candle_seconds`
    sdf = sdf[sdf['candle_seconds'] == candle_seconds]

    # Step 2. Add candles to the state
    sdf = sdf.apply(update_candles_in_state, stateful=True)
    # Log the updated candle
    # sdf=sdf.update(lambda message: logger.debug(f'Updated candle: {message}'))

    # Step3. Compute technical indicators and
    sdf = sdf.apply(compute_technical_indicators, stateful=True)
    # Print the data
    sdf = sdf.update(lambda message: logger.debug(f'Final message: {message}'))

    # Step 4. Produce candles to the output topic
    sdf = sdf.to_topic(topic=technical_indicators_topic)

    # Start the streaming application
    app.run()


if __name__ == '__main__':
    from technical_indicators.config import config
    # from technical_indicators.table import create_table_in_risingwave

    # create_table_in_risingwave(
    #     table_name=config.table_name_in_risingwave,
    #     kafka_broker_address=config.kafka_broker_address,
    #     kafka_topic=config.kafka_output_topic,
    # )
    run(
        kafka_broker_address=config.kafka_broker_address,
        kafka_input_topic=config.kafka_input_topic,
        kafka_output_topic=config.kafka_output_topic,
        kafka_consumer_group=config.kafka_consumer_group,
        candle_seconds=config.candle_seconds,
    )
