from typing import List, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='services/trades/settings.env',
        evn_file_encoding='utf-8',
    )
    product_ids: List[str] = [
        'BTC/USD',
        'BTC/EUR',
        'ETH/EUR',
        'ETH/USD',
        'SOL/USD',
        'SOL/EUR',
        'XRP/USD',
        'XRP/EUR',
    ]
    kafka_broker_address: str
    kafka_topic_name: str
    live_or_historical: Literal['live', 'historical'] = 'live'  # 'live' or 'historical'
    last_n_days: int = 30  # Only used in historical mode


config = Settings()
# print(settings.model_dump())
