#!/usr/bin/env python3
"""
UZ IT Jobs — Telegram Bot (@hhjob_ai_bot)
Автономный бот проекта с железным контролем доступа (Zero Trust / Whitelist only).
Поддерживает команды /start, /stats, /top и запуск закрытого Telegram Mini App.
"""

import os
import sys
import time
import json
import sqlite3
import logging
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

# Подключение к shared Vault
_BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BASE_DIR / "shared"))
try:
    from vault import get as vault_get
except ImportError:
    def vault_get(k):
        return None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [hhjob-bot] %(message)s"
)
logger = logging.getLogger("hhjob-bot")

TOKEN = os.getenv("HH_JOBS_BOT_TOKEN") or vault_get("HH_JOBS_BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else ""
DB_PATH = os.getenv("DB_PATH", str(_BASE_DIR / "data" / "hh.db"))
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://us.tailc8105c.ts.net/uzjobs/")


def get_allowed_user_ids():
    """Загрузить белый список Telegram User ID из .env и Vault."""
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

    qa_id = vault_get("TELEGRAM_QA_USER_ID")
    if qa_id and str(qa_id).strip().isdigit():
        allowed.add(int(str(qa_id).strip()))

    return allowed


def api_call(method: str, payload: dict = None, timeout: int = 20):
    if not TOKEN:
        return {"ok": False, "description": "Token not set"}
    url = f"{API_URL}/{method}"
    try:
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        else:
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"ok": False, "description": str(e)}
    except Exception as e:
        return {"ok": False, "description": str(e)}


def send_message(chat_id: int, text: str, reply_markup: dict = None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return api_call("sendMessage", payload)


def get_app_keyboard():
    return {
        "inline_keyboard": [
            [
                {
                    "text": "🚀 Открыть UZ IT Jobs (Mini App)",
                    "web_app": {"url": MINI_APP_URL}
                }
            ],
            [
                {"text": "📊 Статистика рынка", "callback_data": "cmd_stats"},
                {"text": "🔥 Топ Match", "callback_data": "cmd_top"}
            ]
        ]
    }


def get_stats_text():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            total = conn.execute("SELECT count(*) FROM vacancies").fetchone()[0]
            companies = conn.execute("SELECT count(DISTINCT company) FROM vacancies").fetchone()[0]
            good = conn.execute("SELECT count(*) FROM vacancies WHERE matched_score >= 0.30").fetchone()[0]
            recent = conn.execute("SELECT count(*) FROM vacancies WHERE datetime(created_at) >= datetime('now', '-7 days')").fetchone()[0]
        return (
            f"📊 <b>Статистика IT-рынка Узбекистана:</b>\n\n"
            f"• Всего вакансий в базе: <b>{total}</b>\n"
            f"• Активных компаний: <b>{companies}</b>\n"
            f"• С высоким Match (>30%): <b>{good}</b>\n"
            f"• Свежих за 7 дней: <b>{recent}</b>\n"
            f"• Мониторинг: <b>US Server 24/7</b>"
        )
    except Exception as e:
        return f"⚠️ Ошибка чтения базы: {e}"


def get_top_vacancies_text(limit=5):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT title, company, matched_score, salary_from, salary_to, salary_currency, url "
                "FROM vacancies WHERE matched_score >= 0.25 ORDER BY matched_score DESC, created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        if not rows:
            return "Нет вакансий с высоким соответствием."
        
        lines = ["🔥 <b>Топ вакансий по соответствию профилю:</b>\n"]
        for idx, r in enumerate(rows, 1):
            score_pct = int(round((r['matched_score'] or 0) * 100))
            sal = ""
            if r['salary_from'] or r['salary_to']:
                cur = (r['salary_currency'] or "UZS").upper()
                sign = "$" if cur == "USD" else ("₽" if cur == "RUB" else "сум")
                if r['salary_from'] and r['salary_to']:
                    sal = f" | {r['salary_from']}-{r['salary_to']} {sign}"
                elif r['salary_from']:
                    sal = f" | от {r['salary_from']} {sign}"
                else:
                    sal = f" | до {r['salary_to']} {sign}"

            lines.append(
                f"{idx}. <a href=\"{r['url']}\"><b>{r['title']}</b></a>\n"
                f"   🏢 {r['company']}{sal}\n"
                f"   🎯 Match: <b>{score_pct}%</b>\n"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ Ошибка выборки: {e}"


def handle_message(msg: dict, allowed_ids: set):
    user = msg.get("from", {})
    user_id = user.get("id")
    username = user.get("username", "unknown")
    chat_id = msg.get("chat", {}).get("id")
    text = (msg.get("text") or "").strip()

    # СТРОГАЯ ПРОВЕРКА WHITELIST
    if not user_id or user_id not in allowed_ids:
        logger.warning(
            f"[SECURITY ALERT] Unauthorized access attempt blocked: user_id={user_id}, "
            f"username=@{username}, chat_id={chat_id}, text='{text}'"
        )
        # Блокировка без выдачи информации (или вежливый отказ приватного бета-теста)
        send_message(
            chat_id,
            "⛔ <b>Доступ ограничен.</b>\n\nЭтот сервис находится в режиме закрытого Enterprise-тестирования. "
            "Доступ предоставляется строго по авторизованному списку."
        )
        return

    logger.info(f"Authorized command from @{username} (ID: {user_id}): '{text}'")

    if text.startswith("/start"):
        welcome_text = (
            f"👋 Здравствуйте, <b>{user.get('first_name', 'Владелец')}</b>!\n\n"
            f"Добро пожаловать в <b>UZ IT Jobs</b> — закрытую систему мониторинга "
            f"и анализа IT-рынка Узбекистана.\n\n"
            f"Все сервисы функционируют автономно 24/7 на <b>US Server</b>.\n"
            f"Нажмите кнопку ниже для запуска полноэкранного <b>Telegram Mini App</b>:"
        )
        send_message(chat_id, welcome_text, reply_markup=get_app_keyboard())

    elif text.startswith("/set_profile"):
        skills = text.replace("/set_profile", "").strip()
        if not skills:
            send_message(chat_id, "⚠️ Укажите навыки через запятую.\nПример: /set_profile Python, SQL, Docker")
        else:
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    cur = conn.execute("SELECT user_id FROM user_profiles WHERE user_id = ?", (user_id,))
                    if cur.fetchone():
                        conn.execute("UPDATE user_profiles SET skills = ? WHERE user_id = ?", (skills, user_id))
                    else:
                        conn.execute("INSERT INTO user_profiles (user_id, skills) VALUES (?, ?)", (user_id, skills))
                send_message(chat_id, f"✅ Профиль сохранён!\nНавыки: {skills}\n\nСмотреть подборку: /my_digest")
            except Exception as e:
                send_message(chat_id, f"⚠️ Ошибка: {e}")

    elif text == "/my_digest":
        send_message(chat_id, "⏳ Анализирую вакансии под ваш профиль...")
        from digest_generator import get_personal_digest
        digest_text = get_personal_digest(user_id)
        send_message(chat_id, digest_text, reply_markup=get_app_keyboard())

    elif text == "/stats":
        send_message(chat_id, get_stats_text(), reply_markup=get_app_keyboard())

    elif text == "/top":
        send_message(chat_id, get_top_vacancies_text(), reply_markup=get_app_keyboard())

    elif text == "/app":
        send_message(chat_id, "📱 Запуск Telegram Mini App:", reply_markup=get_app_keyboard())

    else:
        send_message(
            chat_id,
            "Доступные команды:\n"
            "/app — Открыть приложение UZ IT Jobs\n"
            "/set_profile <навыки> — Настроить профиль\n"
            "/my_digest — Моя персональная подборка\n"
            "/stats — Статистика IT-рынка РУз\n"
            "/top — Топ подходящих вакансий\n"
            "/start — Главное меню"
        )


def handle_callback_query(cq: dict, allowed_ids: set):
    user = cq.get("from", {})
    user_id = user.get("id")
    cq_id = cq.get("id")
    data = cq.get("data", "")
    chat_id = cq.get("message", {}).get("chat", {}).get("id")

    if not user_id or user_id not in allowed_ids:
        logger.warning(f"[SECURITY ALERT] Unauthorized callback blocked: user_id={user_id}")
        api_call("answerCallbackQuery", {"callback_query_id": cq_id, "text": "⛔ Доступ запрещен", "show_alert": True})
        return

    api_call("answerCallbackQuery", {"callback_query_id": cq_id})
    if data == "cmd_stats":
        send_message(chat_id, get_stats_text(), reply_markup=get_app_keyboard())
    elif data == "cmd_top":
        send_message(chat_id, get_top_vacancies_text(), reply_markup=get_app_keyboard())


def main():
    global TOKEN, API_URL
    logger.info("Starting UZ IT Jobs Bot (@hhjob_ai_bot)...")
    if not TOKEN:
        logger.error(
            "CRITICAL: HH_JOBS_BOT_TOKEN is not set in environment or Vault! "
            "Bot will sleep and wait for token configuration."
        )
        while not (os.getenv("HH_JOBS_BOT_TOKEN") or vault_get("HH_JOBS_BOT_TOKEN")):
            time.sleep(10)
        TOKEN = os.getenv("HH_JOBS_BOT_TOKEN") or vault_get("HH_JOBS_BOT_TOKEN")
        API_URL = f"https://api.telegram.org/bot{TOKEN}"
        logger.info("HH_JOBS_BOT_TOKEN successfully acquired.")

    allowed_ids = get_allowed_user_ids()
    logger.info(f"Security initialized. Allowed User IDs: {sorted(list(allowed_ids))}")

    # Настройка Menu Button для бота
    menu_resp = api_call("setChatMenuButton", {
        "menu_button": {
            "type": "web_app",
            "text": "🇺🇿 UZ IT Jobs",
            "web_app": {"url": MINI_APP_URL}
        }
    })
    logger.info(f"ChatMenuButton configured: {menu_resp.get('ok')}")

    offset = None
    while True:
        try:
            allowed_ids = get_allowed_user_ids()
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
            url = f"{API_URL}/getUpdates?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if not data.get("ok"):
                logger.warning(f"getUpdates error: {data.get('description')}")
                time.sleep(5)
                continue

            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                if "message" in upd:
                    handle_message(upd["message"], allowed_ids)
                elif "callback_query" in upd:
                    handle_callback_query(upd["callback_query"], allowed_ids)

        except Exception as e:
            logger.error(f"Polling loop exception: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
