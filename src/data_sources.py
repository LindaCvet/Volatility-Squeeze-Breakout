import datetime as dt
from dateutil import tz
import pandas as pd
import httpx
from tenacity import retry, wait_exponential, stop_after_attempt

GRANULARITY_MAP = {
    "M15": 900,
    "M30": 1800,
    "H1": 3600,
}

CB_BASE = "https://api.exchange.coinbase.com"

def _to_df(rows, symbol):
    # Coinbase candles: [ time, low, high, open, close, volume ] (latest first)
    cols = ["time", "low", "high", "open", "close", "volume"]
    if not rows:
        return pd.DataFrame(columns=cols + ["symbol"])

    df = pd.DataFrame(rows, columns=cols)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df = df.sort_values("time").reset_index(drop=True)
    df["symbol"] = symbol
    return df

@retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(5))
def fetch_ohlcv(symbol: str, granularity: int, limit: int = 400) -> pd.DataFrame:
    # Coinbase atbalsta param 'granularity' un (līdz) 300 sveces per request;
    # mēs varam izvilkt nedaudz vairāk, ja vajag – bet 300–400 pietiek indikatoriem.
    params = {"granularity": granularity}
    url = f"{CB_BASE}/products/{symbol}/candles"
    # Vienkāršībai: 1 pieprasījums; jaunākās ~300 sveces
    # (ja vajag striktu limitu – slice pēc tam)
    with httpx.Client(timeout=20) as client:
        r = client.get(url, params=params, headers={"User-Agent": "WolfeWave/1.0"})
        r.raise_for_status()
        data = r.json()
    df = _to_df(data, symbol)
    if limit and len(df) > limit:
        df = df.iloc[-limit:].copy()
    return df

def localize_ts(ts: pd.Timestamp, tz_name: str = "Europe/Riga") -> str:
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    tz_target = tz.gettz(tz_name)
    return ts.tz_convert(tz_target).strftime("%Y-%m-%d %H:%M")
