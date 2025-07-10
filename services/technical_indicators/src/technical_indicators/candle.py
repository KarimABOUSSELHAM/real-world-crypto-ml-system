from quixstreams import State

from technical_indicators.config import config


def are_same_window(candle: dict, previous_candle: dict) -> bool:
    """
    Check if two candles are in the same time window and crypt currency.
    Args:
        candle (dict): The latest candle.
        previous_candle (dict): The previous candle to compare against.
    Returns:
        bool: True if both candles are in the same time window, False otherwise.
    """
    return (
        candle['pair'] == previous_candle['pair']
        and candle['window_start_ms'] == previous_candle['window_start_ms']
        and candle['window_end_ms'] == previous_candle['window_end_ms']
    )


def update_candles_in_state(candle: dict, state: State):
    """
    Takes the current state (with the list of N previous candles) and the latest
    candle, and update this list.
    It can either happen that the latest candle is already in the state or that it is a new candle.

    Args:
        candle (dict): The latest candle
        state (State): The current state containing the list of previous candles.
    Returns:
        None
    """
    candles = state.get('candles', default=[])
    # chack if the candle is already in the state
    if not candles:
        # if the state is empty, add the candle to the state
        candles.append(candle)
    if are_same_window(candle, candles[-1]):
        # replace the latest candle in state
        candles[-1] = candle
    else:
        # add the candle to the state
        candles.append(candle)
    if len(candles) > config.max_candles_in_state:
        # remove the oldest candle if the state is full
        candles.pop(0)
    state.set('candles', candles)
    return candle
