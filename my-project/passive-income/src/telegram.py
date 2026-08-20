"""Telegram — отправка в @famaly_helper_bot. Токен из vault/.env."""
import sys, os, logging, time
from pathlib import Path
import requests
from dotenv import load_dotenv

_BASE = Path(__file__).resolve().parent.parent
load_dotenv(_BASE / '.env')

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_THREAD_ID

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN()
        self.chat_id = TELEGRAM_CHAT_ID()
        self.thread_id = TELEGRAM_THREAD_ID()
        self.enabled = bool(self.bot_token)
        self.max_retries = int(os.getenv("TELEGRAM_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("TELEGRAM_RETRY_DELAY", "30"))

    def send_report(self, text):
        if not self.enabled or not text: return False
        payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        if self.thread_id: payload["message_thread_id"] = int(self.thread_id)
        for attempt in range(1, self.max_retries + 2):
            try:
                r = requests.post(f"https://api.telegram.org/bot{self.bot_token}/sendMessage", json=payload, timeout=15)
                if r.status_code == 200: logger.info("✅ Report sent"); return True
                logger.warning(f"Telegram API error (attempt {attempt}): {r.status_code}")
                if attempt <= self.max_retries: time.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Telegram error (attempt {attempt}): {e}")
                if attempt <= self.max_retries: time.sleep(self.retry_delay)
        logger.error("❌ Telegram send failed after all retries")
        return False

    def send_message(self, text, parse_mode="HTML"):
        return self.send_report(text)
