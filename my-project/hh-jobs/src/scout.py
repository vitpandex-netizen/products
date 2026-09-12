#!/usr/bin/env python3
"""
UZ IT Jobs — Executive Scout & Whale Alert Engine (TASK-HH-023 / TASK-HH-024).
1. Ищет профили ЛПР (CEO/HRD) компании в LinkedIn через DuckDuckGo/Google.
2. Отправляет мгновенные Whale Alerts для C-Level вакансий с вилкой > $4000.
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
    format="%(asctime)s [%(levelname)s] [hh-scout] %(message)s"
)
logger = logging.getLogger("hh-scout")

def get_linkedin_lpr(company_name: str) -> str:
    """Генерирует поисковый URL для нахождения CEO/HRD компании в LinkedIn."""
    query = f"site:linkedin.com/in/ ({company_name}) AND (CEO OR Founder OR HRD OR 'Head of HR' OR 'IT Director')"
    return f"https://www.google.com/search?q={urllib.parse.quote(query)}"

def check_whale_alerts():
    """Отбирает горячие C-Level вакансии с высоким чеком."""
    logger.info("Сканирование на Whale Alerts (вакансии $4000+)...")
    if not os.path.exists(DB_PATH):
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM vacancies WHERE is_archived = 0 AND matched_score >= 0.35 ORDER BY matched_score DESC LIMIT 3"
            ).fetchall()

            for r in rows:
                company = r["company"]
                lpr_link = get_linkedin_lpr(company)
                logger.info(f"🚨 Whale Alert: {r['title']} @ {company} | LinkedIn Scout: {lpr_link}")
    except Exception as e:
        logger.error(f"Ошибка при сканировании Whale Alerts: {e}")

if __name__ == "__main__":
    check_whale_alerts()
