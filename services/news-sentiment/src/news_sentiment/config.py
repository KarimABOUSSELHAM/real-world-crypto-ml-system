from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    kafka_broker_address: str
    kafka_input_topic: str
    kafka_output_topic: str
    kafka_consumer_group: str
    base_url: Optional[str] = None
    model: str


config = Settings()
