from pydantic_settings import BaseSettings


class CryptopanicConfig(BaseSettings):
    """
    Configuration of the cryptopanic API and the news service.
    """

    cryptopanic_api_key: str
    kafka_broker_address: str
    kafka_topic: str


config = CryptopanicConfig()
