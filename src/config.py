from pydantic import BaseModel
import os

class Settings(BaseModel):
    # --- Instruments & timeframe ---
    SYMBOLS: list[str] = [
        "BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "XRP-USD",
        "ADA-USD", "LTC-USD", "DOGE-USD", "LINK-USD", "MATIC-USD",
    ]
    TIMEFRAME: str = "M15"  # M15 | M30 | H1
    MAX_CANDLES: int = 400  # vēsture indikatoriem

    # --- Squeeze / breakout parametri ---
    BB_PERIOD: int = 20
    BB_STD: float = 2.0

    ATR_PERIOD: int = 20
    KELTNER_ATR_MULT: float = 1.5

    VOL_SMA_WIN: int = 20
    VOL_MIN_MULT: float = 1.3  # Vol > SMA20 * 1.3

    USE_MA_FILTER: bool = True
    MA_FAST: int = 20
    MA_SLOW: int = 50

    # --- RSI / ADX filtrēšana ---
    USE_RSI_FILTER: bool = True
    RSI_PERIOD: int = 14
    RSI_LONG_MIN: float = 55.0     # longiem min RSI
    RSI_SHORT_MAX: float = 45.0    # ja reiz nākotnē izmantosi shortus

    USE_ADX_FILTER: bool = True
    ADX_PERIOD: int = 14
    ADX_MIN: float = 20.0

    # --- Entry/SL/TP (tikai pie bullish “Vērts pirkt”) ---
    ENTRY_USE_BUFFER: bool = True
    ENTRY_BUFFER_ATR: float = 0.10
    SL_ATR_MULT: float = 1.5
    TP_MULTS: list[float] = [1.0, 2.0, 3.0]
    ROUNDING_MODE: str = "auto"     # "auto" | "fixed"
    FIXED_DECIMALS: int = 2

    # --- Notifikācijas ---
    TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "")  # var būt "id1,id2"
    LOCALE: str = "LV"
    TZ: str = "Europe/Riga"

    # --- Loģika ---
    SEND_FREQUENCY: str = "first"  # "first" | "each"
    SKIP_IF_NO_FRESH: bool = True

def get_settings() -> Settings:
    return Settings()
