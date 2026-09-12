#!/usr/bin/env python3
"""
UZ IT Jobs — Скрипт очистки базы (Data Retention Policy).
Выполняет гибридную очистку базы hh.db:
1. Софт-удаление (Архивация): вакансии старше 30 дней помечаются как is_archived = 1
2. Хард-удаление: вакансии старше 90 дней физически удаляются из БД для экономии места.
"""

import os
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [hh-pruner] %(message)s"
)
logger = logging.getLogger("hh-pruner")

_BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DB_PATH", str(_BASE_DIR / "data" / "hh.db"))


def run_pruning():
    logger.info(f"Запуск Data Retention Policy для БД: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        logger.error(f"БД не найдена: {DB_PATH}")
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            # 1. Хард-удаление старше 90 дней
            res_delete = conn.execute(
                "DELETE FROM vacancies WHERE datetime(created_at) < datetime('now', '-90 days')"
            )
            deleted_count = res_delete.rowcount
            logger.info(f"Удалено старых вакансий (>90 дней): {deleted_count}")
            
            # 2. Софт-удаление (архивация) старше 30 дней
            res_archive = conn.execute(
                "UPDATE vacancies SET is_archived = 1 WHERE is_archived = 0 AND datetime(created_at) < datetime('now', '-30 days')"
            )
            archived_count = res_archive.rowcount
            logger.info(f"Перемещено в архив (>30 дней): {archived_count}")
            
            conn.commit()
            
            if deleted_count > 0:
                logger.info("Выполняется VACUUM для оптимизации БД...")
                conn.execute("VACUUM")
                
    except Exception as e:
        logger.error(f"Ошибка при очистке БД: {e}")

if __name__ == "__main__":
    run_pruning()
