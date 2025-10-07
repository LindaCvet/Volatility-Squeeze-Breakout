import pandas as pd
from .indicators import (
    bollinger_bands, keltner_channels, sma, ema, rsi, adx, atr
)

def compute_all_indicators(df: pd.DataFrame, cfg) -> pd.DataFrame:
    c = df["close"]
    h, l = df["high"], df["low"]
    v = df["volume"]

    # BB
    bb_mid, bb_up, bb_dn = bollinger_bands(c, cfg.BB_PERIOD, cfg.BB_STD)
    df["bb_mid"], df["bb_up"], df["bb_dn"] = bb_mid, bb_up, bb_dn
    df["bb_width"] = (bb_up - bb_dn) / bb_mid

    # Keltner + ATR
    kel_mid, kel_up, kel_dn, atr_val = keltner_channels(h, l, c, cfg.ATR_PERIOD, cfg.KELTNER_ATR_MULT)
    df["kel_mid"], df["kel_up"], df["kel_dn"] = kel_mid, kel_up, kel_dn
    df["atr"] = atr_val

    # MA
    df["ma_fast"] = ema(c, cfg.MA_FAST)
    df["ma_slow"] = ema(c, cfg.MA_SLOW)

    # Vol SMA
    df["vol_sma"] = sma(v, cfg.VOL_SMA_WIN)
    df["vol_strong"] = v > (df["vol_sma"] * cfg.VOL_MIN_MULT)

    # RSI / ADX
    df["rsi"] = rsi(c, cfg.RSI_PERIOD)
    plus_di, minus_di, adx_val = adx(h, l, c, cfg.ADX_PERIOD)
    df["plus_di"], df["minus_di"], df["adx"] = plus_di, minus_di, adx_val

    # Squeeze: BB iekš Keltner
    df["squeeze_on"] = (df["bb_up"] <= df["kel_up"]) & (df["bb_dn"] >= df["kel_dn"])

    # Breakout nosacījums (svece aizveras ārpus BB + apjoms)
    df["breakout_up"] = (c > df["bb_up"]) & df["vol_strong"]
    df["breakout_dn"] = (c < df["bb_dn"]) & df["vol_strong"]

    # Papildfiltri (MA/RSI/ADX)
    if cfg.USE_MA_FILTER:
        df["ma_ok_up"] = (c > df["ma_fast"]) & (c > df["ma_slow"])
        df["ma_ok_dn"] = (c < df["ma_fast"]) & (c < df["ma_slow"])
    else:
        df["ma_ok_up"] = True
        df["ma_ok_dn"] = True

    if cfg.USE_RSI_FILTER:
        df["rsi_ok_up"] = df["rsi"] >= cfg.RSI_LONG_MIN
        df["rsi_ok_dn"] = df["rsi"] <= cfg.RSI_SHORT_MAX
    else:
        df["rsi_ok_up"] = True
        df["rsi_ok_dn"] = True

    if cfg.USE_ADX_FILTER:
        df["adx_ok"] = df["adx"] >= cfg.ADX_MIN
    else:
        df["adx_ok"] = True

    df["filters_ok_up"] = df["ma_ok_up"] & df["rsi_ok_up"] & df["adx_ok"]
    df["filters_ok_dn"] = df["ma_ok_dn"] & df["rsi_ok_dn"] & df["adx_ok"]

    return df

def detect_first_breakout_after_squeeze(df: pd.DataFrame, cfg):
    """
    Atrodi signālu pēdējā *pabeigtajā* svecē:
    - pēdējā rinda = jaunākā svece (pabeigta Coinbase datos)
    - breakout_up/down True
    - iepriekšējais bārs bija squeeze_on == True
    - un squeeze posmā līdz tam nebija breakout
    """
    if len(df) < 50:
        return None

    last = df.iloc[-1].copy()
    prev = df.iloc[-2].copy()

    direction = None
    if last["breakout_up"] and last["filters_ok_up"]:
        direction = "up"
    elif last["breakout_dn"] and last["filters_ok_dn"]:
        direction = "down"

    if direction is None:
        return None

    # Pārliecināmies, ka tas ir pirmais breakout pēc squeeze_on
    # atrodam pēdējo indeksu, kur squeeze_on pārgāja no False->True (“sākās squeeze posms”)
    squeeze_series = df["squeeze_on"].iloc[:-1]  # līdz pirms pēdējās rindas
    if not squeeze_series.any():
        return None
    # no beigām atpakaļ – cik ilgi squeeze bija True pirms pēdējās sveces
    run_len = 0
    for val in reversed(squeeze_series.values):
        if val:
            run_len += 1
        else:
            break

    if run_len == 0:
        # iepr. svece nebija squeeze_on
        return None

    # pārbaudām, vai šajā squeeze “skrējienā” nebija jau breakout
    start_idx = len(df) - 1 - run_len - 1  # posma sākums (iesk. pirmssveces)
    start_idx = max(0, start_idx)
    in_run = df.iloc[start_idx:-1]  # līdz pirms pēdējās sveces
    if (in_run["breakout_up"] | in_run["breakout_dn"]).any():
        return None

    return {
        "direction": direction,
        "row": last,
        "prev": prev,
    }
