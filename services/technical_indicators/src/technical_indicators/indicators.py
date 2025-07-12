import numpy as np
from loguru import logger
from talib import stream

from technical_indicators.config import config


def compute_technical_indicators(candle: dict, state: dict):
    """
    Computes technical indicators from the candles in the state.

    Args:
        candles (list): List of candles from the state.
    Returns:
        dict: A dictionary containing the computed technical indicators.
    """
    candles = state.get('candles', [])
    logger.debug(f'Number of candles in state : {len(candles)}')
    # Extract the open, high, low volume form candles into numpy arrays since this is the forma which talib expects
    close = np.array([c['close'] for c in candles], dtype=np.float64)
    _open = np.array([c['open'] for c in candles], dtype=np.float64)
    _high = np.array([c['high'] for c in candles], dtype=np.float64)
    _low = np.array([c['low'] for c in candles], dtype=np.float64)
    volume = np.array([c['volume'] for c in candles], dtype=np.float64)
    indicators = {}

    for period in config.sma_periods:
        # Simple moving average
        # - window: period
        indicators[f'sma_{period}'] = stream.SMA(close, timeperiod=period)
    # Exponential moving average for different periods
    indicators['ema_7'] = stream.EMA(close, timeperiod=7)
    indicators['ema_14'] = stream.EMA(close, timeperiod=14)
    indicators['ema_21'] = stream.EMA(close, timeperiod=21)
    indicators['ema_60'] = stream.EMA(close, timeperiod=60)

    # Relative strength index for different periods
    indicators['rsi_7'] = stream.RSI(close, timeperiod=7)
    indicators['rsi_14'] = stream.RSI(close, timeperiod=14)
    indicators['rsi_21'] = stream.RSI(close, timeperiod=21)
    indicators['rsi_60'] = stream.RSI(close, timeperiod=60)

    # Moving average convergence divergence for different periods
    indicators['macd_7'], indicators['macdsignal_7'], indicators['macdhist_7'] = (
        stream.MACD(close, fastperiod=7, slowperiod=14, signalperiod=9)
    )
    # On balance volume
    indicators['obv'] = stream.OBV(close, volume)
    # breakpoint()
    return {
        **candle,
        **indicators,
    }
