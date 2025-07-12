def create_table_in_risingwave(
    kafka_broker_address: str,
    kafka_topic: str,
    table_name: str = 'technical_indicators',
):
    """
    Create a table with the given name inside risingwave and connect it to the Kafka topic.

    This way, Risingwave automatically ingests messages from Kafka and updates the table in real-time.
    """
    pass
