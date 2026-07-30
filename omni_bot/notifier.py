import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ENABLE_TELEGRAM
import logging

logger = logging.getLogger("OmniBot")

def send_telegram_message(message: str):
    """Sends a message to the configured Telegram chat."""
    if not ENABLE_TELEGRAM:
        return
        
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE" or not TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram is enabled, but TELEGRAM_BOT_TOKEN is not set in config.py")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            logger.error(f"Failed to send Telegram message: {response.text}")
    except Exception as e:
        logger.error(f"Telegram API exception: {e}")
