from typing import Optional

from pydantic_settings import BaseSettings


class TrainingConfig(BaseSettings):
    mlflow_tracking_uri: str = 'http://localhost:5000'
    risingwave_host: str = 'localhost'
    risingwave_port: int = 4567
    risingwave_user: str = 'root'
    risingwave_password: str = ''
    risingwave_database: str = 'dev'
    risingwave_table: str = 'public.technical_indicators'
    pair: str = 'ETH/EUR'
    lookback_period: int = 10
    candle_seconds: int = 60
    prediction_horizon_seconds: int = 300
    n_rows_for_data_profiling: int = 30
    eda_report_html_path: str = './eda_report.html'
    train_test_split_ratio: float = 0.8
    features: list[str] = [
        'open',
        'high',
        'low',
        'close',
        'window_start_ms',
        'window_end_ms',
        'volume',
        'sma_7',
        'sma_14',
        'sma_21',
        'sma_60',
        'ema_7',
        'ema_14',
        'ema_21',
        'ema_60',
        'rsi_7',
        'rsi_14',
        'rsi_21',
        'rsi_60',
        'macd_7',
        'macdsignal_7',
        'macdhist_7',
        'obv',
    ]
    hyperparam_search_trials: int = 5
    hyperparam_search_n_splits: int = 5
    model_name: Optional[str] = 'OrthogonalMatchingPursuit'
    n_model_candidates: int = 2
    max_percentage_rows_with_nulls: float = (
        0.01  # Example parameter for data validation
    )
    max_percentage_diff_vs_baseline: float = 0.5


train_config = TrainingConfig()
# print(settings.model_dump())


class PredictorConfig(BaseSettings):
    mlflow_tracking_uri: str = 'http://localhost:5000'
    risingwave_host: str = 'localhost'
    risingwave_port: int = 4567
    risingwave_user: str = 'root'
    risingwave_password: str = ''
    risingwave_database: str = 'dev'
    risingwave_schema: str = 'public'
    risingwave_input_table: str = 'technical_indicators'
    risingwave_output_table: str = 'predictions'
    pair: str = 'ETH/EUR'
    prediction_horizon_seconds: int = 300
    candle_seconds: int = 60
    model_version: Optional[str] = 'latest'


predictor_config = PredictorConfig()


class StabilityConfig(BaseSettings):
    mlflow_tracking_uri: str = 'http://localhost:5000'
    candle_seconds: int = 60
    prediction_horizon_seconds: int = 300
    pair: str = 'ETH/EUR'
    exporter_port: int = 11000


stability_config = StabilityConfig()
