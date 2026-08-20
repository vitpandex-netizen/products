"""Responder — отправка уведомлений в Telegram. Токен из vault."""
import os, sys, logging, time
import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'shared'))
from vault import get as vault_get

logger = logging.getLogger(__name__)

class Responder:
    def __init__(self):
        self.bot_token = vault_get('TELEGRAM_BOT_TOKEN') or ''
        self.chat_id = vault_get('TELEGRAM_CHAT_ID') or '-1004297012607'
        self.thread_id = vault_get('TELEGRAM_THREAD_ID') or '15'
        if not self.bot_token:
            logger.warning('TELEGRAM_BOT_TOKEN not set! Notifications disabled.')
    
    def notify(self, text: str) -> bool:
        if not self.bot_token:
            return False
        url = f'https://api.telegram.org/bot{self.bot_token}/sendMessage'
        payload = {'chat_id': self.chat_id, 'text': text, 'parse_mode': 'HTML'}
        if self.thread_id:
            payload['message_thread_id'] = int(self.thread_id)
        try:
            r = requests.post(url, json=payload, timeout=15)
            return r.status_code == 200
        except:
            return False

    def notify_digest(self, candidates: list) -> bool:
        """Send digest of matching candidates to Telegram."""
        if not candidates:
            return False
        msg = f"🔍 HH Remote — Дайджест ({len(candidates)} вакансий)\n\n"
        for c in candidates[:15]:
            title = c.get('title', '?')[:50] if isinstance(c, dict) else getattr(c, 'title', '?')[:50]
            company = (c.get('company', '')[:20] if isinstance(c, dict) else getattr(c, 'company', '')[:20])
            score = c.get('match_score', 0) if isinstance(c, dict) else getattr(c, 'match_score', 0)
            url = c.get('url', '') if isinstance(c, dict) else getattr(c, 'url', '')
            star = "⭐" if score >= 0.60 else "▫️"
            line = f"{star} <b>{title}</b>"
            if company: line += f" @ {company}"
            line += f" ({score*100:.0f}%)"
            if url: line += f"\n   {url}"
            msg += line + "\n\n"
        return self.notify(msg)
