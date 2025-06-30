from datetime import timedelta

from loguru import logger
from quixstreams import Application


def init_candle(trade: dict) -> dict:
    """ "Initialize a candle with the first trade

    Args:
        trade (dict): the trade ingested from streaming data

    Returns:
        dict: the initial candle state
    """
    return {
        'open': trade['price'],
        'high': trade['price'],
        'low': trade['price'],
        'close': trade['price'],
        'volume': trade['quantity'],
        # 'timestamp_ms': trade['timestamp_ms'],
        'pair': trade['product_id'],
    }


def update_candle(candle: dict, trade: dict) -> dict:
    """Takes the current candle also known as the state and the new trade and update the candle state

    Args:
        candle (dict): the current candle state
        trade (dict): the new trade

    Returns:
        dict: the updated candle state
    """
    # Open price does not change so there is no need to update it
    candle['high'] = max(candle['high'], trade['price'])
    candle['low'] = min(candle['low'], trade['price'])
    candle['close'] = trade['price']
    candle['volume'] += trade['quantity']

    return candle


def run(
    kafka_broker_address: str,
    kafka_input_topic: str,
    kafka_output_topic: str,
    kafka_consumer_group: str,
    candle_seconds: int,
):
    """
    Transforms a stream of input trades into a stream of output candles.

    In three steps:
    - Ingests trades from `kafka_input_topic`
    - Aggregates trades into candles of `candle_sec` seconds
    - Produces candles to `kafka_output_topic`
    Args:
        kafka_broker_address (str): Address of the Kafka broker.
        kafka_input_topic (str): Name of the Kafka topic to read trades from.
        kafka_output_topic (str): Name of the Kafka topic to write candles to.
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
    trades_topic = app.topic(
        name=kafka_input_topic,
        value_serializer='json',
    )
    # Define the output topic
    candles_topic = app.topic(
        name=kafka_output_topic,
        value_serializer='json',
    )
    # Step 1. Ingest trades from the input topic
    # Create a streaming dataframe connected to the input topic
    sdf = app.dataframe(topic=trades_topic)

    # Step 2. Aggregate trades into candles
    sdf = (
        # Define tumbling window of candle_seconds
        sdf.tumbling_window(timedelta(seconds=candle_seconds))
        # Create a `reduce` aggregation with `reducer` and `initializer` functions
        .reduce(reducer=update_candle, initializer=init_candle)
    )
    # emit all the intermediate candles to make the system more reactive
    sdf = sdf.current()
    # Extract open, high, low, close, volume, timestamp_ms, pair from the dataframe
    sdf['open'] = sdf['value']['open']
    sdf['high'] = sdf['value']['high']
    sdf['low'] = sdf['value']['low']
    sdf['close'] = sdf['value']['close']
    sdf['volume'] = sdf['value']['volume']
    # sdf['timestamp_ms'] = sdf['value']['timestamp_ms']
    sdf['pair'] = sdf['value']['pair']

    # Extract window start and end timestamps
    sdf['window_start_ms'] = sdf['start']
    sdf['window_end_ms'] = sdf['end']

    # keep only the relevant columns
    sdf = sdf[
        [
            'pair',
            # 'timestamp_ms',
            'open',
            'high',
            'low',
            'close',
            'volume',
            'window_start_ms',
            'window_end_ms',
        ]
    ]

    sdf['candle_seconds'] = candle_seconds

    # Print the data
    sdf = sdf.update(lambda message: logger.debug(f'Received trade: {message}'))

    # Step 3. Produce candles to the output topic
    sdf = sdf.to_topic(topic=candles_topic)

    # Start the streaming application
    app.run()


if __name__ == '__main__':
    from candles.config import config

    run(
        kafka_broker_address=config.kafka_broker_address,
        kafka_input_topic=config.kafka_input_topic,
        kafka_output_topic=config.kafka_output_topic,
        kafka_consumer_group=config.kafka_consumer_group,
        candle_seconds=config.candle_seconds,
    )
