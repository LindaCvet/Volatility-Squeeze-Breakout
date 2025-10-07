import sys
import traceback
from src.config import get_settings
from src.data_sources import fetch_ohlcv, GRANULARITY_MAP
from src.strategy_squeeze import compute_all_indicators, detect_first_breakout_after_squeeze
from src.formatter import format_message
from src.notifier import send_telegram

def main():
    cfg = get_settings()
    gran = GRANULARITY_MAP.get(cfg.TIMEFRAME.upper())
    if not gran:
        raise ValueError(f"Unsupported TIMEFRAME: {cfg.TIMEFRAME}")

    any_sent = False
    for sym in cfg.SYMBOLS:
        try:
            df = fetch_ohlcv(sym, granularity=gran, limit=cfg.MAX_CANDLES)
            if df.empty or len(df) < 100:
                print(f"{sym}: Skipped: no fresh OHLCV (len={len(df)})")
                continue

            df = compute_all_indicators(df, cfg)
            res = detect_first_breakout_after_squeeze(df, cfg)
            if not res:
                print(f"{sym}: no signal")
                continue

            # ja "each", varētu sūtīt katru breakout; mēs implementējam “first”
            msg = format_message(sym, cfg.TIMEFRAME, res, cfg)
            print(f"\n---\n{msg}\n---\n")
            send_telegram(cfg.TELEGRAM_BOT_TOKEN, cfg.TELEGRAM_CHAT_ID, msg)
            any_sent = True

        except Exception as e:
            print(f"ERROR for {sym}: {e}")
            traceback.print_exc()

    if not any_sent:
        print("Done: no signals this run.")

if __name__ == "__main__":
    main()
