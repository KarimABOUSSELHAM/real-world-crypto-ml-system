# Create an Application instance with Kafka configs
from typing import List

from kraken_rest_api import KrakenRestAPI
from kraken_websocket_api import KrakenWebsocketAPI
from loguru import logger
from quixstreams import Application
from trade import Trade


def run(
    kafka_broker_address: str,
    kafka_topic_name: str,
    kraken_api: KrakenWebsocketAPI | KrakenRestAPI,
):
    app = Application(
        broker_address=kafka_broker_address,
    )

    # Define a topic "my_topic" with JSON serialization
    topic = app.topic(name=kafka_topic_name, value_serializer='json')

    # Create a Producer instance
    with app.get_producer() as producer:
        while not kraken_api.is_done():
            events: List[Trade] = kraken_api.get_trades()
            # event = {"id": "1", "text": "Lorem ipsum dolor sit amet"}
            for event in events:
                # Serialize an event using the defined Topic
                message = topic.serialize(key=event.product_id, value=event.to_dict())

                # Produce a message into the Kafka topic
                producer.produce(topic=topic.name, value=message.value, key=message.key)
                # Log the produced messages
                # logger.info(f"Produced message to topic: {topic.name}")
                logger.info(f'Trade {event} pushed to kafka')


if __name__ == '__main__':
    from config import config

    # create an instance of KrakenAPI to talk to Kraken websocket API
    if config.live_or_historical == 'live':
        logger.info('Running in live mode')
        api = KrakenWebsocketAPI(product_ids=config.product_ids)
    elif config.live_or_historical == 'historical':
        logger.info('Running in historical mode')
        api = KrakenRestAPI(
            product_id=config.product_ids[0],
            last_n_days=config.last_n_days,
        )
    else:
        raise ValueError(
            "Invalid value for 'live_or_historical'. Must be 'live' or 'historical'."
        )
    run(
        kafka_broker_address=config.kafka_broker_address,
        kafka_topic_name=config.kafka_topic_name,
        kraken_api=api,
    )
