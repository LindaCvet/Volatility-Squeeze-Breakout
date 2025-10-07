import time
import httpx

def _clean_chats(chat_id_env: str) -> list[str]:
    if not chat_id_env:
        return []
    return [x.strip() for x in chat_id_env.split(",") if x.strip()]

def send_telegram(token: str, chat_ids_env: str, text: str) -> None:
    chat_ids = _clean_chats(chat_ids_env)
    if not token or not chat_ids:
        print("WARN: Telegram not configured (token / chat id missing).")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with httpx.Client(timeout=20) as client:
        for i, chat_id in enumerate(chat_ids):
            payload = {"chat_id": chat_id, "text": text}
            r = client.post(url, json=payload)
            if r.status_code >= 400:
                print(f"Telegram error for chat {chat_id}: {r.text}")
            # vienkāršs throttling
            if i < len(chat_ids) - 1:
                time.sleep(1.1)
