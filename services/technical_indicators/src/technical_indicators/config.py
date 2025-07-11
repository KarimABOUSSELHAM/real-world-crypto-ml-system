import os

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.dirname(
    __file__
)  # /app/services/technical_indicators/src/technical_indicators
ENV_FILE = os.path.join(BASE_DIR, 'settings.env')


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding='utf-8',
        # case_sensitive=False,
    )

    kafka_broker_address: str
    kafka_input_topic: str
    kafka_output_topic: str
    kafka_consumer_group: str
    candle_seconds: int
    max_candles_in_state: int = 100


config = Settings()
# print(settings.model_dump())
