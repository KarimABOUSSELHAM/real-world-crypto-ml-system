from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='services/technical_indicators/src/technical_indicators/settings.env',
        evn_file_encoding='utf-8',
    )

    kafka_broker_address: str
    kafka_input_topic: str
    kafka_output_topic: str
    kafka_consumer_group: str
    candle_seconds: int
    max_candles_in_state: int = 1000


config = Settings()
# print(settings.model_dump())
