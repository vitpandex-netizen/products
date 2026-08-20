"""
main.py — HH Remote Jobs оркестратор.

Pipeline: HHClient.search_and_enrich() → VacancyMatcher.batch_match() → Responder.notify()

Защита от дублей: fcntl.flock на logs/.hh-remote-jobs.lock.
Рабочее окно: START_HOUR / END_HOUR из .env.
SQLite: таблица vacancies с notified_at / digested_at в CREATE TABLE.
"""

import fcntl
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.net import force_ipv4
from src.hh_client import HHClient
from src.matcher import VacancyMatcher
from src.responder import Responder

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Настройка
# ─────────────────────────────────────────────


def setup_logging(log_file: str, log_level: str = "INFO") -> None:
    """Настроить логгирование: файл + stderr."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Файловый обработчик
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # stderr (цвета нет, просто текст для терминала)
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(level)
    sh.setFormatter(fmt)
    root.addHandler(sh)

    logger.info("Логгирование настроено: %s [%s]", log_file, log_level)


def within_working_hours(start_hour: int, end_hour: int) -> bool:
    """Проверить, попадает ли текущее локальное время в [start_hour, end_hour)."""
    now = datetime.now()
    if start_hour <= end_hour:
        return start_hour <= now.hour < end_hour
    # crosses midnight — rare, but handle it
    return now.hour >= start_hour or now.hour < end_hour


# ─────────────────────────────────────────────
# Lock
# ─────────────────────────────────────────────


def acquire_lock(lock_path: str) -> int:
    """Захватить эксклюзивный fcntl flock. Блокирует, пока не получим."""
    Path(lock_path).parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX)
    logger.info("Lock захвачен: %s", lock_path)
    return fd


def release_lock(fd: int, lock_path: str) -> None:
    """Освободить flock и закрыть fd."""
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        logger.info("Lock освобождён: %s", lock_path)
    except OSError:
        pass


# ─────────────────────────────────────────────
# SQLite
# ─────────────────────────────────────────────


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS vacancies (
    id              TEXT PRIMARY KEY,
    title           TEXT,
    company         TEXT,
    url             TEXT,
    salary_from     REAL,
    salary_to       REAL,
    salary_currency TEXT,
    area            TEXT,
    matched_score   REAL,
    matched_skills  TEXT,
    raw_text        TEXT,
    published_at    TEXT,
    inserted_at     TEXT NOT NULL DEFAULT (datetime('now')),
    notified_at     TEXT,
    digested_at     TEXT
);
"""


def init_db(db_path: str) -> sqlite3.Connection:
    """Подключиться к SQLite, создать таблицу если её нет."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(SCHEMA_SQL)
    conn.commit()
    logger.info("БД готова: %s", db_path)
    return conn


def store_vacancies(conn: sqlite3.Connection, vacancies: list) -> list:
    """Вставить новые вакансии в БД (INSERT OR IGNORE).

    Возвращает список вакансий, которые реально вставились (ранее не виденные).
    """
    if not vacancies:
        return []

    seen_ids = set()
    cursor = conn.execute("SELECT id FROM vacancies")
    for row in cursor.fetchall():
        seen_ids.add(row["id"])

    new_vacancies = []
    for v in vacancies:
        vid = v.get("id")
        if not vid or vid in seen_ids:
            continue
        seen_ids.add(vid)  # не вставим повторно в этой же пачке
        new_vacancies.append(v)

    if not new_vacancies:
        logger.info("Новых вакансий нет (все %d уже в БД)", len(vacancies))
        return []

    rows = []
    for v in new_vacancies:
        rows.append((
            v.get("id"),
            v.get("title", ""),
            v.get("company", ""),
            v.get("url", ""),
            v.get("salary_from"),
            v.get("salary_to"),
            v.get("salary_currency"),
            v.get("area", ""),
            v.get("matched_score"),
            json.dumps(v.get("matched_skills", []), ensure_ascii=False),
            v.get("raw_text", ""),
            v.get("published_at", ""),
        ))

    conn.executemany(
        """INSERT OR IGNORE INTO vacancies
           (id, title, company, url, salary_from, salary_to,
            salary_currency, area, matched_score, matched_skills,
            raw_text, published_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    logger.info("Сохранено %d новых вакансий", len(new_vacancies))
    return new_vacancies


def mark_notified(conn: sqlite3.Connection, vacancy_ids: list) -> None:
    """Обновить notified_at для списка ID."""
    if not vacancy_ids:
        return
    now_iso = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        "UPDATE vacancies SET notified_at = ? WHERE id = ?",
        [(now_iso, vid) for vid in vacancy_ids],
    )
    conn.commit()
    logger.info("notified_at проставлен для %d вакансий", len(vacancy_ids))


def mark_digested(conn: sqlite3.Connection, vacancy_ids: list) -> None:
    """Обновить digested_at для списка ID."""
    if not vacancy_ids:
        return
    now_iso = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        "UPDATE vacancies SET digested_at = ? WHERE id = ?",
        [(now_iso, vid) for vid in vacancy_ids],
    )
    conn.commit()
    logger.info("digested_at проставлен для %d вакансий", len(vacancy_ids))


# ─────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────


def run_pipeline() -> None:
    """Основной pipeline: поиск → матчинг → уведомление."""
    load_dotenv()
    force_ipv4()

    # ── 1. Логгирование (до любых logger.* вызовов, включая ранние guard'ы —
    # иначе сообщения об пропуске работы вне окна/при блокировке уходят в
    # никуда: без настроенного handler'а INFO-логи молча проглатываются) ──
    log_file = os.getenv("LOG_FILE", "logs/hh-remote-jobs.log")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(log_file, log_level)

    # ── 2. Рабочее окно ──
    start_hour = int(os.getenv("START_HOUR", "8"))
    end_hour = int(os.getenv("END_HOUR", "21"))
    if not os.environ.get("FORCE_HH") and not within_working_hours(start_hour, end_hour):
        now_h = datetime.now().hour
        logger.info(
            "Вне рабочего окна (%02d-%02d, сейчас %02d:00) — завершаемся",
            start_hour, end_hour, now_h,
        )
        return

    # ── 3. Lock ──
    lock_path = "logs/.hh-remote-jobs.lock"
    lock_fd = acquire_lock(lock_path)
    try:
        # ── 4. БД ──
        db_path = os.getenv("DB_PATH", "data/hh_remote.db")
        conn = init_db(db_path)

        # ── 5. Поиск ──
        keywords = os.getenv("SEARCH_KEYWORDS", "IT Manager,Head of IT")
        schedule = os.getenv("SEARCH_SCHEDULE", "remote")
        period = int(os.getenv("SEARCH_PERIOD_DAYS", "7"))

        areas = []
        if os.getenv("SOURCE_HH_RU_ENABLED", "true").strip().lower() == "true":
            areas.append(113)
        if os.getenv("SOURCE_HH_KZ_ENABLED", "true").strip().lower() == "true":
            areas.append(40)

        if not areas:
            logger.warning("Ни один источник не включён — завершаемся")
            return

        logger.info(
            "Поиск: keywords=%s schedule=%s period=%d areas=%s",
            keywords, schedule, period, areas,
        )

        client = HHClient()
        enriched = client.search_and_enrich(
            keywords=keywords,
            schedule=schedule,
            period=period,
            areas=areas,
        )

        if not enriched:
            logger.info("Нет вакансий для обработки")
            return

        logger.info("Обогащено %d сырых вакансий", len(enriched))

        # ── 6. Матчинг ──
        matcher = VacancyMatcher.from_env()
        matched = matcher.batch_match(enriched)

        min_score = float(os.getenv("MIN_MATCH_SCORE", "0.70"))
        digest_enabled = os.getenv("DIGEST_ENABLED", "true").strip().lower() == "true"
        digest_min_score = float(os.getenv("DIGEST_MIN_SCORE", "0.40"))
        notify_limit = int(os.getenv("NOTIFY_BATCH_LIMIT", "15"))
        digest_limit = int(os.getenv("DIGEST_BATCH_LIMIT", "15"))

        high = [v for v in matched if v["matched_score"] >= min_score]
        low = (
            [v for v in matched if digest_min_score <= v["matched_score"] < min_score]
            if digest_enabled
            else []
        )

        logger.info(
            "Матчинг: всего %d, >=%.2f=%d, digest=[%.2f,%.2f)=%d",
            len(matched), min_score, len(high),
            digest_min_score, min_score, len(low),
        )

        # ── 7. Сохранение в БД ──
        new_high = store_vacancies(conn, high)
        new_low = store_vacancies(conn, low) if low else []

        if new_low:
            logger.info("Digest-кандидатов сохранено в БД: %d", len(new_low))

        # ── 8. Уведомление ──
        responder = None
        if new_high:
            to_notify = new_high[:notify_limit]
            responder = Responder()
            ok = responder.notify(to_notify)
            if ok:
                ids = [v["id"] for v in to_notify]
                mark_notified(conn, ids)
                logger.info("Успешно уведомлено %d вакансий", len(ids))
            else:
                logger.warning("Ошибка отправки — notified_at НЕ проставлен")
        else:
            logger.info("Новых подходящих вакансий нет — уведомление пропущено")

        # ── 9. Дайджест слабых совпадений ──
        if new_low:
            to_digest = new_low[:digest_limit]
            responder = responder or Responder()
            ok = responder.notify_digest(to_digest)
            if ok:
                ids = [v["id"] for v in to_digest]
                mark_digested(conn, ids)
                logger.info("Дайджест отправлен: %d вакансий", len(ids))
            else:
                logger.warning("Ошибка отправки дайджеста — digested_at НЕ проставлен")

        conn.close()

    finally:
        release_lock(lock_fd, lock_path)


# ─────────────────────────────────────────────
# Entry point (используется и как скрипт, и как cron task)
# ─────────────────────────────────────────────


def main() -> None:
    """Точка входа. Оборачивает pipeline в try/except для логирования."""
    try:
        run_pipeline()
    except Exception:
        logger.exception("Необработанная ошибка в pipeline")
        sys.exit(1)


if __name__ == "__main__":
    main()
