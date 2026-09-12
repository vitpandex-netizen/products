#!/usr/bin/env python3
"""
UZ IT Jobs — Парсер Habr Карьера (TASK-HH-020).
Собирает актуальные IT вакансии (включая Remote и Узбекистан) и заносит в hh.db.
"""

import os
import sys
import sqlite3
import logging
import urllib.request
import urllib.parse
import json
import re
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DB_PATH", str(_BASE_DIR / "data" / "hh.db"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [habr-parser] %(message)s"
)
logger = logging.getLogger("habr-parser")

HABR_API_URL = "https://career.habr.com/api/v1/vacancies"

def fetch_habr_vacancies():
    logger.info("Запуск парсинга Habr Карьера...")
    keywords = ["CIO", "CTO", "CISO", "IT Director", "Информационная безопасность", "Системный администратор", "DevOps"]
    vacancies = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    for kw in keywords:
        try:
            url = f"https://career.habr.com/vacancies?q={urllib.parse.quote(kw)}&type=all"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8")
                # Извлекаем названия, компании и ссылки
                matches = re.findall(r'<a class="vacancy-card__title-link" href="(/vacancies/\d+)">(.*?)</a>', html)
                companies = re.findall(r'<a class="vacancy-card__company-title"[^>]*>(.*?)</a>', html)
                
                for i, (path, title) in enumerate(matches):
                    comp = companies[i] if i < len(companies) else "Habr Employer"
                    vacancies.append({
                        "id": int(re.search(r'\d+', path).group()),
                        "title": title.strip(),
                        "company": comp.strip(),
                        "url": f"https://career.habr.com{path}",
                        "source": "habr"
                    })
        except Exception as e:
            logger.error(f"Ошибка при запросе к Habr по ключевику '{kw}': {e}")

    logger.info(f"Собрано {len(vacancies)} вакансий с Habr Карьера.")
    save_to_db(vacancies)

def save_to_db(vacancies):
    if not vacancies or not os.path.exists(DB_PATH):
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            added = 0
            for v in vacancies:
                res = conn.execute(
                    "INSERT OR IGNORE INTO vacancies (id, title, company, url, description, created_at, is_archived) "
                    "VALUES (?, ?, ?, ?, ?, datetime('now'), 0)",
                    (v["id"] + 900000000, v["title"], v["company"], v["url"], f"Вакансия с Habr Карьера: {v['title']}")
                )
                if res.rowcount > 0:
                    added += 1
            conn.commit()
            logger.info(f"Добавлено новых вакансий с Habr: {added}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении Habr вакансий в БД: {e}")

if __name__ == "__main__":
    fetch_habr_vacancies()
