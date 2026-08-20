"""GH Scout — Collector Runner.

Запускает сбор данных по расписанию.
В production используется APScheduler, но для контейнера — простой polling loop.
"""

import time
import logging
from datetime import datetime, timedelta
import os

from core.config import settings
from collectors.github_collector import collect_all_projects, collect_trends, GitHubCollector
from analyzers.feature_extractor import process_unprocessed_releases

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Ждём БД при старте
WAIT_DB_RETRIES = 30
WAIT_DB_DELAY = 2


def wait_for_db():
    """Ждём, пока БД будет доступна."""
    import psycopg2
    for i in range(WAIT_DB_RETRIES):
        try:
            conn = psycopg2.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                dbname=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password,
            )
            conn.close()
            logger.info("Database is ready")
            return True
        except Exception:
            if i < WAIT_DB_RETRIES - 1:
                logger.info(f"Waiting for database ({i+1}/{WAIT_DB_RETRIES})...")
                time.sleep(WAIT_DB_DELAY)
    logger.error("Database not ready after retries")
    return False


def run_p0_collection():
    """P0: сбор релизов trading ботов (каждые 24h)."""
    logger.info("=== P0 Collection ===")
    try:
        collect_all_projects(token=settings.github_token)
        process_unprocessed_releases()
        logger.info("P0 collection complete")
    except Exception as e:
        logger.error(f"P0 collection failed: {e}")


def run_trending():
    """Trending: сбор трендов (каждые 24h)."""
    logger.info("=== Trending Collection ===")
    try:
        collect_trends(token=settings.github_token)
        logger.info("Trending collection complete")
    except Exception as e:
        logger.error(f"Trending collection failed: {e}")


def seed_initial_projects():
    """Заполнить начальные проекты для отслеживания."""
    from core.database import get_sync_session
    from core.models import TrackedProject, Priority

    session = get_sync_session()
    collector = GitHubCollector(token=settings.github_token)

    # P0 — Trading боты
    p0_projects = [
        ("Freqtrade", "freqtrade/freqtrade", "https://github.com/freqtrade/freqtrade",
         "Популярный крипто-трейдинг бот с открытым кодом", "trading", "bot", ["bitget-bot"]),
        ("3Commas", "3commas-io/3commas", "https://github.com/3commas-io/3commas",
         "Торговая платформа для крипто-ботов", "trading", "platform", ["bitget-bot"]),
        ("Hummingbot", "hummingbot/hummingbot", "https://github.com/hummingbot/hummingbot",
         "Фреймворк для создания market-making ботов", "trading", "framework", ["bitget-bot"]),
        ("Jesse", "jesse-ai/jesse", "https://github.com/jesse-ai/jesse",
         "Крипто-трейдинг бот на Python", "trading", "bot", ["bitget-bot"]),
        ("OctoBot", "Drakkar-Software/OctoBot", "https://github.com/Drakkar-Software/OctoBot",
         "Модульный крипто-трейдинг бот", "trading", "bot", ["bitget-bot"]),
        ("Gekko", "askmike/gekko", "https://github.com/askmike/gekko",
         "Крипто-трейдинг бот с веб-интерфейсом", "trading", "bot", ["bitget-bot"]),
    ]

    # P1 — DeFi, AI/ML
    p1_projects = [
        ("Uniswap", "Uniswap/v3-core", "https://github.com/Uniswap/v3-core",
         "Ядро Uniswap DEX v3", "defi", "dex", []),
        ("LangChain", "langchain-ai/langchain", "https://github.com/langchain-ai/langchain",
         "Фреймворк для LLM-приложений", "ai_ml", "framework", ["anyidea"]),
        ("CrewAI", "joaomdmoura/crewAI", "https://github.com/joaomdmoura/crewai",
         "Фреймворк для AI-агентов", "ai_ml", "framework", ["anyidea"]),
        ("AutoGPT", "Significant-Gravitas/AutoGPT", "https://github.com/Significant-Gravitas/AutoGPT",
         "Автономный AI-агент", "ai_ml", "agent", ["anyidea"]),
    ]

    # P2 — FinTech
    p2_projects = [
        ("Metabase", "metabase/metabase", "https://github.com/metabase/metabase",
         "BI-инструмент с открытым кодом", "fintech", "bi", ["finanalytics"]),
        ("Superset", "apache/superset", "https://github.com/apache/superset",
         "Apache Superset BI", "fintech", "bi", ["finanalytics"]),
    ]

    all_projects = [
        (p + (Priority.P0,)) for p in p0_projects
    ] + [
        (p + (Priority.P1,)) for p in p1_projects
    ] + [
        (p + (Priority.P2,)) for p in p2_projects
    ]

    try:
        for name, repo, url, desc, cat, subcat, our_projects, priority in all_projects:
            existing = session.query(TrackedProject).filter(
                TrackedProject.repo_full_name == repo
            ).first()
            if existing:
                continue

            info = collector.fetch_repo_info(repo)
            proj = TrackedProject(
                name=name,
                repo_full_name=repo,
                repo_url=url,
                description=desc,
                category=cat,
                subcategory=subcat,
                priority=priority,
                our_projects=our_projects,
                stars=info["stars"] if info else 0,
                forks=info["forks"] if info else 0,
                language=info["language"] if info else "",
                status="active",
            )
            session.add(proj)

        session.commit()
        logger.info("Initial projects seeded")
    except Exception as e:
        session.rollback()
        logger.error(f"Seed failed: {e}")
    finally:
        session.close()


def main():
    logger.info("Starting GH Scout Collector...")

    if not wait_for_db():
        logger.error("Cannot start: database not available")
        return

    # Seed initial data (first run only)
    seed_initial_projects()

    # Основной цикл
    last_p0 = datetime.min
    last_trend = datetime.min

    while True:
        now = datetime.utcnow()

        # P0 — каждые 24 часа
        if now - last_p0 >= timedelta(hours=settings.p0_interval_hours):
            run_p0_collection()
            last_p0 = now

        # Trends — каждые 24 часа
        if now - last_trend >= timedelta(hours=settings.trending_interval_hours):
            run_trending()
            last_trend = now

        # Спим 30 минут
        logger.info(f"Sleeping 30min... Next P0: {last_p0 + timedelta(hours=settings.p0_interval_hours)}")
        time.sleep(1800)


if __name__ == "__main__":
    main()