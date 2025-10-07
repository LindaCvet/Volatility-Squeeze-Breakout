import numpy as np
import pandas as pd

def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()

def ema(series: pd.Series, window: int) -> pd.Series:
    return series.ewm(span=window, adjust=False).mean()

def bollinger_bands(close: pd.Series, period: int, std_mult: float):
    mid = sma(close, period)
    std = close.rolling(window=period, min_periods=period).std(ddof=0)
    upper = mid + std_mult * std
    lower = mid - std_mult * std
    return mid, upper, lower

def true_range(high, low, close):
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr

def atr(high, low, close, period: int):
    tr = true_range(high, low, close)
    # Wilder smoothing
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr

def keltner_channels(high, low, close, period: int, atr_mult: float):
    mid = ema(close, period)
    _atr = atr(high, low, close, period)
    upper = mid + atr_mult * _atr
    lower = mid - atr_mult * _atr
    return mid, upper, lower, _atr

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / (avg_loss.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
    # directional movement
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = ((up_move > down_move) & (up_move > 0)).astype(float) * up_move
    minus_dm = ((down_move > up_move) & (down_move > 0)).astype(float) * down_move

    tr = true_range(high, low, close)

    # Wilder smoothing
    atr_w = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr_w)
    minus_di = 100 * (minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr_w)

    dx = 100 * ( (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan) )
    adx_val = dx.ewm(alpha=1/period, adjust=False).mean()
    return plus_di, minus_di, adx_val
