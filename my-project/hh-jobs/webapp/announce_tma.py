#!/usr/bin/env python3
"""
Анонс и регистрация Telegram Mini App «UZ IT Jobs».
1. Регистрирует Menu Button бота на Mini App (для личных чатов).
2. Отправляет карточку с кнопкой запуска WebApp в топик 15 группы AI Assistant.
"""

import os
import sys
import json
import urllib.request
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _BASE_DIR.parent
sys.path.insert(0, str(_PROJECT_DIR / "shared"))

from vault import get as vault_get

TOKEN = vault_get("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("ОШИБКА: TELEGRAM_BOT_TOKEN не найден в Vault!")
    sys.exit(1)

GROUP_ID = vault_get("TELEGRAM_CHAT_ID") or "-1004297012607"
TOPIC_ID = int(os.getenv("HH_JOBS_THREAD_ID", "15"))
TMA_URL = "https://us.tailc8105c.ts.net/uzjobs/"


def tg_api(method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print(f"🔗 TMA URL: {TMA_URL}")

    # 1. Установка кнопки Меню в боте
    try:
        r1 = tg_api("setChatMenuButton", {
            "menu_button": {
                "type": "web_app",
                "text": "🇺🇿 Вакансии РУз",
                "web_app": {"url": TMA_URL}
            }
        })
        print(f"✓ Menu Button установлен: {r1.get('ok')}")
    except Exception as e:
        print(f"⚠️ Ошибка установки Menu Button: {e}")

    # 2. Отправка анонса в топик 15 (HH Jobs)
    text = (
        "🇺🇿 <b>Telegram Mini App «UZ IT Jobs» запущен!</b>\n\n"
        "Полноценный каталог и аналитика IT-рынка труда Узбекистана прямо в Telegram:\n"
        "• 📊 <b>918+ актуальных вакансий</b> Ташкента и регионов\n"
        "• 👔 <b>Руководящие позиции (C-Level):</b> CIO, CTO, Head of IT, IT Director\n"
        "• 🛠 <b>Инфраструктура & DevOps:</b> SRE, Linux, Virtualization, Архитектура\n"
        "• 🔒 <b>Информационная безопасность (SOC, ИБ)</b>\n"
        "• 🏢 <b>Топ работодателей:</b> TBC, Anor Bank, UZCARD/НМПЦ, Paynet, Huawei\n"
        "• 📝 <b>Генератор сопроводительных писем</b> на русском и узбекском\n\n"
        "<i>Нажмите кнопку ниже для запуска веб-приложения:</i>"
    )

    markup = {
        "inline_keyboard": [
            [
                {
                    "text": "🚀 Открыть UZ IT Jobs (Mini App)",
                    "url": TMA_URL
                }
            ],
            [
                {
                    "text": "📊 Аналитика рынка Ташкента",
                    "url": TMA_URL
                }
            ]
        ]
    }

    try:
        r2 = tg_api("sendMessage", {
            "chat_id": GROUP_ID,
            "message_thread_id": TOPIC_ID,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": markup
        })
        print(f"✓ Анонс отправлен в топик {TOPIC_ID}: {r2.get('ok')}")
    except Exception as e:
        print(f"⚠️ Ошибка отправки анонса: {e}")


if __name__ == "__main__":
    main()
