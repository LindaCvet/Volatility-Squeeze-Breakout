# src/selftest.py
from src.config import get_settings
from src.notifier import send_telegram

def main():
    cfg = get_settings()
    msg = (
        "🧪 TEST | Volatility Squeeze Breakout\n"
        "Savienojums ar Telegram strādā. Ja redzi šo ziņu, viss ok.\n"
        f"Timeframe: {cfg.TIMEFRAME} | Pāri: {', '.join(cfg.SYMBOLS[:5])}…\n"
        "⚙️ Šī ir tikai testa ziņa (bez tirgus datiem)."
    )
    send_telegram(cfg.TELEGRAM_BOT_TOKEN, cfg.TELEGRAM_CHAT_ID, msg)

if __name__ == '__main__':
    main()
