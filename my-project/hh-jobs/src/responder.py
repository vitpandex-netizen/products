"""Responder — отправка уведомлений в Telegram. Токен из vault.

Форматы сообщений:
- notify()           — произвольный текст
- notify_matches()   — список подходящих вакансий (score >= threshold)
- notify_digest()    — дайджест слабых совпадений (min_score..max_score)
"""

import os
import sys
import logging
import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shared'))
from vault import get as vault_get

logger = logging.getLogger(__name__)


def _fmt_salary(v: dict) -> str:
    """Форматировать зарплату из полей vacancy-строки БД."""
    cur = (v.get("salary_currency") or "UZS").upper()
    sign = {"USD": "$", "RUB": "₽", "UZS": "сум"}.get(cur, "")
    frm = v.get("salary_from")
    to = v.get("salary_to")
    if not frm and not to:
        return "💰 не указана"
    def human(n):
        if cur == "UZS" and n and n >= 1000:
            return f"{n/1000000:.1f} млн"
        return str(n)
    if frm and to:
        return f"💰 {sign}{human(frm)} – {sign}{human(to)}"
    if frm:
        return f"💰 от {sign}{human(frm)}"
    return f"💰 до {sign}{human(to)}"


def _escape(text: str) -> str:
    """Экранировать HTML-сущности для parse_mode=HTML."""
    if not text:
        return ""
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;"))


class Responder:
    def __init__(self, db=None):
        self.db = db
        self.bot_token = vault_get('TELEGRAM_BOT_TOKEN') or ''
        self.chat_id = vault_get('TELEGRAM_CHAT_ID') or '-1004297012607'
        self.thread_id = vault_get('HH_JOBS_THREAD_ID') or vault_get('TELEGRAM_THREAD_ID') or '15'
        if not self.bot_token:
            logger.warning('TELEGRAM_BOT_TOKEN not set! Notifications disabled.')

    def _send(self, text: str) -> bool:
        if not self.bot_token:
            return False
        url = f'https://api.telegram.org/bot{self.bot_token}/sendMessage'
        payload = {'chat_id': self.chat_id, 'text': text, 'parse_mode': 'HTML',
                   'disable_web_page_preview': True}
        if self.thread_id:
            payload['message_thread_id'] = int(self.thread_id)
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code != 200:
                logger.warning(f'Telegram send failed ({r.status_code}): {r.text[:200]}')
            return r.status_code == 200
        except Exception as e:
            logger.warning(f'Telegram send error: {e}')
            return False

    def notify(self, text: str) -> bool:
        return self._send(text)

    def _mark_notified(self, vacancy_id: int):
        """Пометить вакансию отправленной (notified_at)."""
        if not self.db:
            return
        self.db.execute_update(
            "UPDATE vacancies SET notified_at = datetime('now') WHERE id = ?",
            (vacancy_id,),
        )

    def _mark_digested(self, vacancy_id: int):
        if not self.db:
            return
        self.db.execute_update(
            "UPDATE vacancies SET digested_at = datetime('now') WHERE id = ?",
            (vacancy_id,),
        )

    def _render_block(self, v: dict, top: bool = False) -> str:
        """Один блок вакансии для сообщения."""
        flag = "🔥" if top else "⭐"
        title = _escape(v.get("title") or "Без названия")
        company = _escape(v.get("company") or "")
        loc = _escape(v.get("location") or "")
        url = v.get("url") or ""
        score = v.get("matched_score") or 0
        lines = [f"{flag} <b>{title}</b>"]
        if company:
            lines.append(f"🏢 {company}")
        if loc:
            lines.append(f"📍 {loc}")
        lines.append(_fmt_salary(v))
        lines.append(f"🎯 совпадение {score:.0%}")
        if url:
            lines.append(f'🔗 <a href="{url}">{url}</a>')
        return "\n".join(lines)

    def notify_matches(self, threshold: float = 0.30, limit: int = 10) -> int:
        """Отправить вакансии со score >= threshold, ещё не отправленные."""
        if not self.db or not self.bot_token:
            return 0
        rows = self.db.execute(
            "SELECT * FROM vacancies WHERE matched_score >= ? AND notified_at IS NULL "
            "ORDER BY matched_score DESC LIMIT ?",
            (threshold, limit),
        )
        if not rows:
            return 0

        blocks = [self._render_block(r, top=(i == 0)) for i, r in enumerate(rows)]
        body = "\n\n".join(blocks)
        header = f"🎯 <b>HH Jobs — {len(rows)} подходящих вакансий</b>\n\n"
        self._send(header + body)

        for r in rows:
            self._mark_notified(r["id"])
        return len(rows)

    def notify_digest(self, min_score: float = 0.40, max_score: float = 0.70,
                      limit: int = 20) -> int:
        """Дайджест слабых совпадений (min_score..max_score), ещё не в дайджесте."""
        if not self.db or not self.bot_token:
            return 0
        rows = self.db.execute(
            "SELECT * FROM vacancies WHERE matched_score >= ? AND matched_score < ? "
            "AND digested_at IS NULL ORDER BY matched_score DESC LIMIT ?",
            (min_score, max_score, limit),
        )
        if not rows:
            return 0

        blocks = [self._render_block(r) for r in rows]
        body = "\n\n".join(blocks)
        header = f"📋 <b>HH Jobs — дайджест ({len(rows)} вакансий)</b>\n\n"
        self._send(header + body)

        for r in rows:
            self._mark_digested(r["id"])
        return len(rows)
