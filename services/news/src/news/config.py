from pydantic_settings import BaseSettings


class CryptopanicConfig(BaseSettings):
    """
    Configuration of the cryptopanic API and the news service.
    """

    cryptopanic_api_key: str
    polling_interval_sec: int = 10
    kafka_broker_address: str
    kafka_output_topic: str


config = CryptopanicConfig()
