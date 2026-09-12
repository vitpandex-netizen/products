#!/usr/bin/env python3
"""
UZ IT Jobs — Модуль отправки ежедневного Executive Digest (TASK-HH-019).
Формирует подборку Top-5 самых релевантных вакансий (score > 60%) и отправляет пользователям из белого списка.
"""

import os
import sys
import sqlite3
import logging
import urllib.request
import urllib.parse
import json
from pathlib import Path

# Подгружаем окружение и общий Vault
_BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BASE_DIR / "shared"))
try:
    from vault import get as vault_get
except ImportError:
    def vault_get(k):
        return None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [hh-digest] %(message)s"
)
logger = logging.getLogger("hh-digest")

TOKEN = os.getenv("HH_JOBS_BOT_TOKEN") or vault_get("HH_JOBS_BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else ""
DB_PATH = os.getenv("DB_PATH", str(_BASE_DIR / "data" / "hh.db"))
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://us.tailc8105c.ts.net/uzjobs/")


def get_allowed_user_ids():
    allowed = set()
    raw_ids = os.getenv("ALLOWED_TELEGRAM_USER_IDS") or vault_get("ALLOWED_TELEGRAM_USER_IDS") or ""
    if raw_ids:
        for item in str(raw_ids).split(","):
            item = item.strip()
            if item.isdigit():
                allowed.add(int(item))

    owner_id = vault_get("TELEGRAM_USER_ID")
    if owner_id and str(owner_id).strip().isdigit():
        allowed.add(int(str(owner_id).strip()))

    return allowed


def send_message(chat_id: int, text: str, reply_markup: dict = None):
    if not TOKEN:
        logger.error("Token is missing!")
        return
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    req = urllib.request.Request(
        f"{API_URL}/sendMessage",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.error(f"Error sending message to {chat_id}: {e}")
        return None


def run_digest():
    logger.info(f"Запуск генерации Executive Digest из БД: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        logger.error(f"БД не найдена: {DB_PATH}")
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT title, company, salary_from, salary_to, salary_currency, matched_score, url "
                "FROM vacancies WHERE is_archived = 0 AND matched_score >= 0.30 "
                "ORDER BY matched_score DESC, created_at DESC LIMIT 5"
            ).fetchall()

        if not rows:
            logger.info("Нет подходящих вакансий для дайджеста.")
            return

        text = "<b>☀️ Ежедневный Executive Digest вакансий (UZ IT Jobs)</b>\n\n"
        text += "Топовые предложения, подобранные под ваш профиль (CIO / CISO / CTO):\n\n"

        import html
        for i, r in enumerate(rows, 1):
            title = html.escape(r["title"] or "")
            company = html.escape(r["company"] or "")
            score = int(r["matched_score"] * 100)
            url = r["url"]

            salary_str = "По договорённости"
            if r["salary_from"] or r["salary_to"]:
                s_from = f"{r['salary_from']:,}" if r["salary_from"] else ""
                s_to = f"{r['salary_to']:,}" if r["salary_to"] else ""
                curr = r["salary_currency"] or "UZS"
                if s_from and s_to:
                    salary_str = f"{s_from} – {s_to} {curr}"
                elif s_from:
                    salary_str = f"от {s_from} {curr}"
                elif s_to:
                    salary_str = f"до {s_to} {curr}"

            text += f"{i}. <b>{title}</b>\n"
            text += f"🏢 Компания: {company}\n"
            text += f"💰 Зарплата: {salary_str}\n"
            text += f"🎯 Совпадение: <b>{score}%</b>\n"
            text += f"🔗 <a href='{url}'>Открыть вакансию</a>\n\n"

        keyboard = {
            "inline_keyboard": [
                [{"text": "🚀 Открыть в Mini App", "web_app": {"url": MINI_APP_URL}}]
            ]
        }

        allowed_users = get_allowed_user_ids()
        logger.info(f"Отправка дайджеста пользователям: {allowed_users}")

        for user_id in allowed_users:
            send_message(user_id, text, reply_markup=keyboard)

        logger.info("Executive Digest успешно отправлен!")

    except Exception as e:
        logger.error(f"Ошибка при формировании дайджеста: {e}")


if __name__ == "__main__":
    run_digest()
