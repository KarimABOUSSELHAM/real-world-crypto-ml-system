from typing import List

from loguru import logger
from quixstreams import Application

# from news_sentiment.candle import get_sentiment_scores


def get_sentiment_scores(news_item: dict) -> List[dict]:
    # TODO: Call the actual LLM API to get the sentiment scores
    # But before let's mock the sentiment scores
    timestamp_ms = news_item['timestamp_ms']
    return [
        {'coin': 'BTC', 'score': 1, 'timestamp_ms': timestamp_ms},
        {'coin': 'ETH', 'score': -1, 'timestamp_ms': timestamp_ms},
    ]


def run(
    kafka_broker_address: str,
    kafka_input_topic: str,
    kafka_output_topic: str,
    kafka_consumer_group: str,
):
    """
    Ingests news articles from Kafka and outputs structured outputs with
    sentiment scores.
    Args:
        kafka_broker_address (str): Address of the Kafka broker.
        kafka_input_topic (str): Name of the Kafka topic to read article from.
        kafka_output_topic (str): Name of the Kafka topic to write outputs to.
        kafka_consumer_group (str): Kafka consumer group name.

    Returns:
        None
    """
    app = Application(
        broker_address=kafka_broker_address,
        consumer_group=kafka_consumer_group,
        auto_offset_reset='earliest',  # Set to earliest for debugging purpose
    )
    # Define the input topic
    news_topic = app.topic(
        name=kafka_input_topic,
        value_serializer='json',
    )
    # Define the output topic
    news_sentiment_topic = app.topic(
        name=kafka_output_topic,
        value_serializer='json',
    )
    # Create a streaming dataframe connected to the input topic
    sdf = app.dataframe(topic=news_topic)
    sdf = sdf.apply(get_sentiment_scores, expand=True)
    sdf = sdf.update(lambda message: logger.debug(f'Final message: {message}'))
    sdf = sdf.to_topic(topic=news_sentiment_topic)

    # Start the streaming application
    app.run()


if __name__ == '__main__':
    from news_sentiment.config import config

    run(
        kafka_broker_address=config.kafka_broker_address,
        kafka_input_topic=config.kafka_input_topic,
        kafka_output_topic=config.kafka_output_topic,
        kafka_consumer_group=config.kafka_consumer_group,
    )
