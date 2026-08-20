"""Habr Career — коллектор руководящих IT-вакансий (CIO/CTO/ИТ-директор).

Второй канал поиска работы в дополнение к HH. Habr Career API открыт
(без OAuth/DDoS-Guard), даёт title, company, salary, remoteWork, skills,
locations и даже специализацию (top_management/cio, top_management/cto).

Логика:
- Запрашиваем руководящие ключевые слова через API.
- Матчим по скиллам профиля + executive title detection.
- Шлём в Telegram (тот же топик, что HH Jobs, или отдельный).
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_PROJECT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT / ".env")

# vault для Telegram токена
sys.path.insert(0, str(_PROJECT / "shared"))
from vault import get as vault_get  # noqa: E402

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("habr-jobs")

API = "https://career.habr.com/api/frontend/vacancies"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

# Руководящие специализации Habr (divisions)
SPECS = [
    "top_management/cio",
    "top_management/cto",
    "top_management/coo",
]

# Ключевые слова для q= поиска
KEYWORDS = [
    "директор по информационным технологиям",
    "IT директор",
    "технический директор",
    "руководитель IT",
    "Head of IT",
    "CIO",
    "CTO",
    "Head of Infrastructure",
]

EXEC_TITLES = [
    "cio", "cto", "директор по информационн", "it директор", "ит директор",
    "технический директор", "руководитель it", "руководитель ит",
    "head of it", "head of infrastructure", "директор по ит",
    "chief technology", "chief information", "операционный директор",
]

# Порог зарплаты: $4000+ = highlight, остальное не фильтруем жёстко
SALARY_USD_HIGHLIGHT = 4000
SALARY_RUR_HIGHLIGHT = 350000


def is_executive(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in EXEC_TITLES)


def fetch(spec: str = None, q: str = None, remote_only: bool = False) -> list:
    params = {"type": "all"}
    if spec:
        params["spec"] = spec
    if q:
        params["q"] = q
    if remote_only:
        params["remote"] = "1"
    try:
        r = requests.get(API, params=params, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
        return data.get("list", [])
    except Exception as e:
        logger.warning(f"Habr fetch failed (spec={spec}, q={q}): {e}")
        return []


def fmt_salary(v: dict) -> str:
    s = v.get("salary") or {}
    if not s.get("from") and not s.get("to"):
        return "не указана"
    cur = {"USD": "$", "RUR": "₽", "EUR": "€"}.get(s.get("currency"), "")
    frm, to = s.get("from"), s.get("to")
    if frm and to:
        return f"{cur}{frm:,} – {cur}{to:,}".replace(",", " ")
    if frm:
        return f"от {cur}{frm:,}".replace(",", " ")
    return f"до {cur}{to:,}".replace(",", " ")


def fmt_remote(v: dict) -> str:
    return "🌍 удалёнка" if v.get("remoteWork") else "🏢 офис"


def main():
    seen = set()
    results = []

    # 1. По специализациям (CIO/CTO/COO)
    for spec in SPECS:
        for v in fetch(spec=spec):
            if v.get("id") in seen:
                continue
            seen.add(v["id"])
            if is_executive(v.get("title", "")):
                results.append(v)
        time.sleep(1)

    # 2. По ключевым словам (включая удалёнку)
    for kw in KEYWORDS:
        for v in fetch(q=kw):
            if v.get("id") in seen:
                continue
            seen.add(v["id"])
            if is_executive(v.get("title", "")):
                results.append(v)
        time.sleep(1)

    # 3. Удалённые руководящие (remote=1)
    for kw in ["CTO", "CIO", "технический директор", "Head of IT"]:
        for v in fetch(q=kw, remote_only=True):
            if v.get("id") in seen:
                continue
            seen.add(v["id"])
            if is_executive(v.get("title", "")):
                results.append(v)
        time.sleep(1)

    logger.info(f"Habr: найдено {len(results)} руководящих вакансий")

    if not results:
        logger.info("Нет новых руководящих вакансий.")
        return

    # Формируем сообщение
    lines = [f"🎯 <b>Habr Career — руководящие IT-позиции ({len(results)})</b>\n"]
    for v in results[:20]:
        title = v.get("title", "")
        comp = (v.get("company") or {}).get("title", "")
        loc = ", ".join(l.get("title", "") for l in (v.get("locations") or []))
        sal = fmt_salary(v)
        rem = fmt_remote(v)
        href = "https://career.habr.com" + v.get("href", "")
        pub = (v.get("publishedDate") or {}).get("title", "")

        lines.append(f"⭐ <b>{title}</b>")
        if comp:
            lines.append(f"🏢 {comp}")
        if loc:
            lines.append(f"📍 {loc}")
        lines.append(f"💰 {sal} | {rem}")
        if pub:
            lines.append(f"📅 {pub}")
        lines.append(f'🔗 <a href="{href}">{href}</a>')
        lines.append("")

    text = "\n".join(lines)

    # Telegram
    bot_token = vault_get("TELEGRAM_BOT_TOKEN") or ""
    chat_id = vault_get("TELEGRAM_CHAT_ID") or "-1004297012607"
    thread_id = vault_get("HH_JOBS_THREAD_ID") or "15"
    if bot_token:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                   "disable_web_page_preview": True}
        if thread_id:
            payload["message_thread_id"] = int(thread_id)
        try:
            r = requests.post(url, json=payload, timeout=15)
            logger.info(f"Telegram: {'OK' if r.status_code == 200 else r.status_code} {r.text[:150]}")
        except Exception as e:
            logger.warning(f"Telegram send error: {e}")
    else:
        logger.warning("TELEGRAM_BOT_TOKEN not set, printing instead:")
        print(text)


if __name__ == "__main__":
    main()
