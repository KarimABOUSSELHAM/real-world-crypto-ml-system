def get_experiment_name(
    pair: str,
    candle_seconds: int,
    prediction_horizon_seconds: int,
) -> str:
    """
    Generates a unique experiment name based on the trading pair, candle seconds, and prediction horizon.
    """
    return f'{pair}_{candle_seconds}_{prediction_horizon_seconds}'
