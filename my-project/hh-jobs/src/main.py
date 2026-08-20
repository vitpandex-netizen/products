"""
HH Jobs Automation — Main Entry Point.
Полный цикл: парсинг → матчинг → уведомление в Telegram.
"""

import fcntl
import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Fix cwd для launchd (TCC compat — chdir после инициализации Python)
import os
os.chdir(Path(__file__).resolve().parent.parent)

from dotenv import load_dotenv
from pathlib import Path

_PROJECT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT / '.env')
from shared.net import force_ipv4
force_ipv4()

# Ensure logs directory
Path("logs").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.getenv("LOG_FILE", "logs/hh-jobs.log")),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

LOCK_FILE = "logs/.hh-jobs.lock"
_lock_fd = None  # kept open for the process lifetime, or flock() releases on close


def _acquire_lock() -> bool:
    """Non-blocking exclusive lock to prevent two runs overlapping.

    2026-07-29: a manually-triggered run and a launchd-triggered run ended
    up executing at the same time (session background task vs launchctl
    kickstart), and both independently queried "unnotified" vacancies
    before either had committed its notified_at update — real duplicate
    Telegram messages went out. This closes that race: a second run that
    starts while one is still in progress just logs and exits immediately
    instead of racing the first for the same batch.
    """
    global _lock_fd
    _lock_fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


LAST_RUN_FILE = "logs/.last_run_completed"


def _minutes_since_last_run() -> float:
    """Minutes since the last successful full run, or infinity if never run.

    2026-07-30: both launchd trigger mechanisms tried so far
    (StartCalendarInterval, then StartInterval=14400) silently stopped
    firing on this machine — StartInterval left a 15-hour gap despite the
    laptop never sleeping or rebooting. Root cause unclear and apparently
    not worth chasing further; instead the trigger is now decoupled from
    the actual work: something (launchd AND cron, redundantly) invokes
    this script every ~30 minutes, cheaply, and THIS check decides whether
    enough time has actually passed to do the real 4-hour cycle. A missed
    trigger now costs at most ~30 minutes of delay instead of hours.
    """
    try:
        mtime = Path(LAST_RUN_FILE).stat().st_mtime
    except FileNotFoundError:
        return float("inf")
    return (datetime.now().timestamp() - mtime) / 60


def _mark_run_completed():
    Path(LAST_RUN_FILE).touch()


def load_config() -> dict:
    """Load all configuration from .env."""
    return {
        "keywords": os.getenv("SEARCH_KEYWORDS", "IT Infrastructure Engineer"),
        "min_salary": int(os.getenv("MIN_SALARY", "45000000")),
        "area": int(os.getenv("SEARCH_AREA_ID", "97")),
        "search_period_days": int(os.getenv("SEARCH_PERIOD_DAYS", "7")),
        "exclude_keywords": [
            kw.strip() for kw in os.getenv("EXCLUDE_KEYWORDS", "").split(",") if kw.strip()
        ],
        "min_match_score": float(os.getenv("MIN_MATCH_SCORE", "0.30")),
        "digest_enabled": os.getenv("DIGEST_ENABLED", "true").lower() == "true",
        "digest_min_score": float(os.getenv("DIGEST_MIN_SCORE", "0.40")),
        "notify_batch_limit": int(os.getenv("NOTIFY_BATCH_LIMIT", "10")),
        "digest_batch_limit": int(os.getenv("DIGEST_BATCH_LIMIT", "20")),
        "notify_enabled": os.getenv("TELEGRAM_NOTIFY_ENABLED", "true").lower() == "true",
        "max_pages": int(os.getenv("MAX_PAGES", "3")),
        "start_hour": int(os.getenv("START_HOUR", "8")),
        "end_hour": int(os.getenv("END_HOUR", "21")),
        "min_run_interval_minutes": int(os.getenv("MIN_RUN_INTERVAL_MINUTES", "235")),
    }


def main():
    """Main entry point: parse → match → notify."""
    if not _acquire_lock():
        logger.warning("Another run is already in progress (lock held) — skipping to avoid duplicate sends.")
        return 0

    logger.info("=" * 50)
    logger.info("HH Jobs Automation Started")
    logger.info(f"Time: {datetime.now()}")
    logger.info("=" * 50)

    cfg = load_config()

    # 2026-07-29: StartCalendarInterval in launchd silently failed to fire
    # twice in a row despite the laptop being continuously awake — switched
    # the plist to StartInterval (fires every N seconds, no wall-clock
    # matching, much harder to silently break) and moved the actual
    # 08:00-21:00 window check here, in code, where it's guaranteed to run.
    current_hour = datetime.now().hour
    if not os.environ.get("FORCE_HH") and not (cfg["start_hour"] <= current_hour < cfg["end_hour"]):
        logger.info(f"Outside operating hours ({cfg['start_hour']}:00-{cfg['end_hour']}:00), current hour={current_hour}. Skipping run.")
        return 0

    # 2026-07-30: decouple "how often are we invoked" from "how often do we
    # actually do work". launchd + cron now both invoke this script every
    # ~30 min (cheap, no-ops most of the time); this check is what actually
    # enforces the ~4h cadence. See _minutes_since_last_run() docstring.
    since_last = _minutes_since_last_run()
    if since_last < cfg["min_run_interval_minutes"]:
        logger.info(f"Last full run was {since_last:.0f} min ago (< {cfg['min_run_interval_minutes']}), too soon. Skipping.")
        return 0
    logger.info(f"Last full run was {since_last:.0f} min ago (or never) — proceeding.")

    logger.info(f"Keywords: {cfg['keywords']}")
    logger.info(f"Min Salary: {cfg['min_salary']}")
    logger.info(f"Area: {cfg['area']}")
    logger.info(f"Min Match Score: {cfg['min_match_score']}")
    logger.info(f"Telegram Notify: {cfg['notify_enabled']}")

    try:
        # === Phase 1: Parse vacancies ===
        logger.info("")
        logger.info("📡 Phase 1: Fetching vacancies...")
        from src.hh_parser import HHParser
        from shared.db import Database

        db = Database("data/hh.db")
        parser = HHParser(db)

        vacancies = parser.search(
            keywords=cfg["keywords"],
            area=cfg["area"],
            min_salary=cfg["min_salary"],
            exclude_keywords=cfg["exclude_keywords"],
            period=cfg["search_period_days"],
        )
        logger.info(f"Found {len(vacancies)} vacancies")

        new_vacancies = parser.save_vacancies(vacancies, exclude_keywords=cfg["exclude_keywords"])
        logger.info(f"New vacancies saved: {len(new_vacancies)}")

        # === Phase 2: Match vacancies ===
        logger.info("")
        logger.info("🎯 Phase 2: Matching vacancies...")
        from src.matcher import VacancyMatcher

        skills_str = os.getenv("MY_SKILLS", "")
        signal_str = os.getenv("SIGNAL_KEYWORDS", "")
        profile = {
            "skills": [s.strip() for s in skills_str.split(",") if s.strip()],
            "min_salary": cfg["min_salary"],
            "experience_years": 19,
            "signal_keywords": [s.strip() for s in signal_str.split(",") if s.strip()],
            "locations": [os.getenv("PREFERRED_LOCATION", "Tashkent")],
        }
        matcher = VacancyMatcher(profile)

        # Get all vacancies that haven't been matched yet
        unprocessed = db.execute(
            "SELECT * FROM vacancies WHERE matched_score = 0 ORDER BY created_at DESC"
        )

        if not unprocessed:
            logger.info("No unprocessed vacancies to match.")
        else:
            results = []
            for v in unprocessed:
                from shared.models import Vacancy as VacancyModel

                vac = VacancyModel(
                    id=v["id"],
                    title=v["title"],
                    company=v["company"],
                    url=v["url"],
                    salary_from=v.get("salary_from"),
                    salary_to=v.get("salary_to"),
                    salary_currency=v.get("salary_currency"),
                    description=v.get("description", ""),
                    experience=v.get("experience", ""),
                    employment_type=v.get("employment_type", ""),
                    skills=v.get("skills", "").split(", ") if v.get("skills") else [],
                )
                result = matcher.calculate_match(vac)
                results.append(result)
                matcher._save_match_score(vac.id, result.score)

                if result.is_good_match(cfg["min_match_score"]):
                    logger.info(f"✅ [{result.score:.1%}] {vac.title} — {vac.company}")
                else:
                    logger.info(f"⏳ [{result.score:.1%}] {vac.title} — {vac.company}")

            good = [r for r in results if r.is_good_match(cfg["min_match_score"])]
            logger.info(f"Good matches: {len(good)}/{len(results)}")

        # === Phase 3: Notify via Telegram ===
        if cfg["notify_enabled"]:
            logger.info("")
            logger.info("📤 Phase 3: Sending Telegram notifications...")
            from src.responder import Responder

            responder = Responder(db)
            # Try notify_matches, fallback to basic notify
            try:
                notified = responder.notify_matches(threshold=cfg["min_match_score"], limit=cfg["notify_batch_limit"])
                logger.info(f"Telegram notifications sent: {notified}")
            except AttributeError:
                # Simplified responder - just send a summary
                summary = f"🔍 HH Jobs: проверка завершена\nНовых вакансий: {len(new_vacancies)}"
                responder.notify(summary)
                logger.info("Basic notification sent")
            
            if cfg["digest_enabled"]:
                try:
                    digested = responder.notify_digest(
                        min_score=cfg["digest_min_score"],
                        max_score=cfg["min_match_score"],
                        limit=cfg["digest_batch_limit"],
                    )
                    logger.info(f"Digest vacancies sent: {digested}")
                except AttributeError:
                    pass
        else:
            logger.info("Telegram notify disabled. Skipping Phase 3.")

        # Summary
        logger.info("")
        logger.info("=" * 50)
        logger.info("✅ HH Jobs Automation Completed")
        logger.info(f"   Vacancies fetched: {len(vacancies)}")
        logger.info(f"   New: {len(new_vacancies)}")
        logger.info(f"   Telegram notify: {'ON' if cfg['notify_enabled'] else 'OFF'}")
        logger.info("=" * 50)
        # Only mark complete on success — a failed run should retry at the
        # next ~30min poll instead of waiting a full 4h cadence.
        _mark_run_completed()

    except KeyboardInterrupt:
        logger.info("Stopped by user")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())