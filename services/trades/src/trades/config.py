from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="services/trades/settings.env",
        evn_file_encoding="utf-8",
        )
    product_ids: List[str] = ["BTC/USD", "BTC/EUR", "ETH/EUR", "ETH/USD", "SOL/USD", "SOL/EUR", "XRP/USD", "XRP/EUR"]
    kafka_broker_address: str 
    kafka_topic_name: str
    
config = Settings()
# print(settings.model_dump())