import os
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.dirname(
    __file__
)  # /app/services/technical_indicators/src/technical_indicators
ENV_FILE = os.path.join(BASE_DIR, 'settings.env')
YAML_FILE = os.path.join(BASE_DIR, 'configs.yaml')


# class TechnicalIndicators(BaseModel):
#     sma: List[int]
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
    sma_periods: Optional[List[int]] = None

    table_name_in_risingwave: str = 'technical_indicators'

    @classmethod
    def from_yaml(cls):
        import yaml

        with open(YAML_FILE, 'r') as file:
            yaml_data = yaml.safe_load(file)
        env_settings = cls()
        merged = {**yaml_data, **env_settings.model_dump(exclude_unset=True)}
        return cls(**merged)


config = Settings.from_yaml()
# print(settings.model_dump())
