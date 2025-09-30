import pandas as pd
import numpy as np

def ensure_1d(series_or_df):
    """Convert any Series, single-column DataFrame, or ndarray to 1D Series."""
    if isinstance(series_or_df, pd.DataFrame):
        series_or_df = series_or_df.iloc[:, 0]
    if isinstance(series_or_df, np.ndarray):
        series_or_df = pd.Series(series_or_df.ravel())
    elif isinstance(series_or_df, pd.Series):
        series_or_df = pd.Series(series_or_df.values.ravel(), index=series_or_df.index)
    return series_or_df

def compute_rsi(series, window=14):
    series = ensure_1d(series)
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_macd(df, fast=12, slow=26, signal=9):
    df = df.copy()
    close = ensure_1d(df['Close'])
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    macd_diff = macd_line - signal_line

    df.loc[:, 'macd'] = macd_line
    df.loc[:, 'macd_signal'] = signal_line
    df.loc[:, 'macd_diff'] = macd_diff

    return df[['macd', 'macd_signal', 'macd_diff']]

def detect_macd_cross(df):
    if 'macd' not in df or 'macd_signal' not in df:
        return None
    macd = df['macd']
    signal = df['macd_signal']
    if len(macd) < 2:
        return None
    prev_diff = macd.iloc[-2] - signal.iloc[-2]
    curr_diff = macd.iloc[-1] - signal.iloc[-1]
    if prev_diff < 0 < curr_diff:
        return 'bullish'
    if prev_diff > 0 > curr_diff:
        return 'bearish'
    return None
