# Create an Application instance with Kafka configs
from quixstreams import Application
from kraken_api import KrakenAPI, Trade
from typing import List
from loguru import logger

def run(
    kafka_broker_address: str,
    kafka_topic_name: str,
    kraken_api:KrakenAPI
):
    app = Application(
        broker_address=kafka_broker_address, 
    )

    # Define a topic "my_topic" with JSON serialization
    topic = app.topic(name=kafka_topic_name, value_serializer='json')



    # Create a Producer instance
    with app.get_producer() as producer:
        while True:
            
            events: List[Trade]=kraken_api.get_trades()
            #event = {"id": "1", "text": "Lorem ipsum dolor sit amet"}
            for event in events:
                # Serialize an event using the defined Topic 
                message = topic.serialize(
                    # key=event["id"],
                    value=event.to_dict()
                    )

                # Produce a message into the Kafka topic
                producer.produce(
                    topic=topic.name, 
                    value=message.value, 
                    #key=message.key
                )
                # Log the produced messages
                logger.info(f"Produced message to topic: {topic.name}")

if __name__ == '__main__':
    # create an instance of KrakenAPI to talk to Kraken websocket API
    api= KrakenAPI(product_ids=["BTC/USD"])
    run(
        kafka_broker_address="localhost:9092",
        kafka_topic_name="trades",
        kraken_api=api
    )