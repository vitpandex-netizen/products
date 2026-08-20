"""Remote Jobs — коллектор международной удалёнки (RemoteOK + WeWorkRemotely).

Третий канал поиска. Собирает руководящие IT-позиции (CTO/CIO/Director/
Head of IT/VP Engineering) с зарплатой в $ с международных remote-платформ.

Источники:
- RemoteOK (https://remoteok.com/api) — JSON, salary в $
- WeWorkRemotely (https://weworkremotely.com/remote-jobs.rss) — RSS
"""

import os
import re
import sys
import time
import logging
import html
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from dotenv import load_dotenv

_PROJECT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT / ".env")

sys.path.insert(0, str(_PROJECT / "shared"))
from vault import get as vault_get  # noqa: E402

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("remote-jobs")

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

# Руководящие IT-титулы (англ) для фильтрации
EXEC_TITLES = [
    "cto", "cio", "chief technology", "chief information",
    "vp of engineering", "vp engineering", "vice president of engineering",
    "director of engineering", "engineering director", "head of engineering",
    "head of it", "head of infrastructure", "it director",
    "director of it", "director of technology", "technology director",
    "head of technology", "it operations manager", "engineering manager",
    "head of platform", "head of data", "director of data",
]

# Зарплата $ для highlight (не фильтруем жёстко — многие без зарплаты)
SALARY_HIGHLIGHT = 80000  # $80k/год


def is_executive(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in EXEC_TITLES)


def fetch_remoteok() -> list:
    """RemoteOK JSON API — возвращает список dict-вакансий."""
    out = []
    try:
        r = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=25)
        r.raise_for_status()
        data = r.json()
        for item in data[1:]:  # первый элемент — legal notice
            pos = item.get("position", "")
            if not pos:
                continue
            if is_executive(pos):
                out.append({
                    "title": pos,
                    "company": item.get("company", ""),
                    "url": item.get("url", ""),
                    "salary_min": item.get("salary_min"),
                    "salary_max": item.get("salary_max"),
                    "location": item.get("location", "Remote"),
                    "source": "RemoteOK",
                    "tags": item.get("tags", []),
                })
    except Exception as e:
        logger.warning(f"RemoteOK failed: {e}")
    return out


def fetch_weworkremotely() -> list:
    """WeWorkRemotely RSS — возвращает список dict-вакансий."""
    out = []
    try:
        r = requests.get("https://weworkremotely.com/remote-jobs.rss",
                         headers=HEADERS, timeout=25)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        for item in root.findall(".//item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            # WWR title format: "Company: Position"
            if not is_executive(title):
                continue
            company = title.split(":")[0].strip() if ":" in title else ""
            position = title.split(":", 1)[1].strip() if ":" in title else title
            out.append({
                "title": position,
                "company": company,
                "url": link,
                "salary_min": None,
                "salary_max": None,
                "location": "Remote",
                "source": "WeWorkRemotely",
                "tags": [],
            })
    except Exception as e:
        logger.warning(f"WeWorkRemotely failed: {e}")
    return out


def fmt_salary(v: dict) -> str:
    lo, hi = v.get("salary_min"), v.get("salary_max")
    if not lo and not hi:
        return "не указана"
    if lo and hi:
        return f"${lo//1000}k – ${hi//1000}k/год"
    if lo:
        return f"от ${lo//1000}k/год"
    return f"до ${hi//1000}k/год"


def send_telegram(text: str):
    bot_token = vault_get("TELEGRAM_BOT_TOKEN") or ""
    chat_id = vault_get("TELEGRAM_CHAT_ID") or "-1004297012607"
    thread_id = vault_get("HH_JOBS_THREAD_ID") or "15"
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, printing instead:")
        print(text)
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML",
               "disable_web_page_preview": True}
    if thread_id:
        payload["message_thread_id"] = int(thread_id)
    try:
        r = requests.post(url, json=payload, timeout=15)
        logger.info(f"Telegram: {'OK' if r.status_code == 200 else r.status_code}")
    except Exception as e:
        logger.warning(f"Telegram send error: {e}")


def main():
    all_jobs = fetch_remoteok() + fetch_weworkremotely()
    logger.info(f"Remote: найдено {len(all_jobs)} руководящих вакансий")

    if not all_jobs:
        logger.info("Нет новых руководящих вакансий.")
        return

    # Сортируем: с зарплатой выше
    all_jobs.sort(key=lambda v: (v.get("salary_min") or 0), reverse=True)

    lines = [f"🌍 <b>Remote — руководящие IT-позиции ({len(all_jobs)})</b>\n"]
    for v in all_jobs[:20]:
        title = v["title"]
        comp = v["company"]
        src = v["source"]
        sal = fmt_salary(v)
        url = v["url"]
        tags = ", ".join(v.get("tags", [])[:5])

        lines.append(f"⭐ <b>{title}</b>")
        if comp:
            lines.append(f"🏢 {comp} [{src}]")
        lines.append(f"💰 {sal}")
        if tags:
            lines.append(f"🏷 {tags}")
        lines.append(f'🔗 <a href="{url}">{url}</a>')
        lines.append("")

    send_telegram("\n".join(lines))


if __name__ == "__main__":
    main()
