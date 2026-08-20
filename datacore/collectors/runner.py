"""Раннер сборщиков — запускает все collectors в цикле.

Использование:
    python3 runner.py                    # Все сборщики, вывод в stdout
    python3 runner.py --db postgresql://...  # Все сборщики, запись в БД
    python3 runner.py --once             # Один цикл, выход
"""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from collectors.collector_polymarket import PolymarketCollector
from collectors.collector_yahoo import YahooFinanceCollector

logger = logging.getLogger(__name__)

COLLECTORS = {
    "polymarket": PolymarketCollector,
    "yahoo": YahooFinanceCollector,
}

INTERVALS = {
    "polymarket": 300,   # 5 мин
    "yahoo": 120,        # 2 мин
}


def run_all(db_url: str = None, once: bool = False):
    """Запустить все сборщики."""
    collectors = {}
    for name, cls in COLLECTORS.items():
        try:
            collectors[name] = cls(db_url=db_url)
            logger.info("Initialized collector: %s", name)
        except Exception as e:
            logger.error("Failed to init %s: %s", name, e)

    if not collectors:
        logger.error("No collectors initialized!")
        return

    try:
        while True:
            for name, collector in collectors.items():
                logger.info("Running collector: %s", name)
                result = collector.run_once()
                logger.info("Collector %s: %s", name, result)

            if once:
                break

            # Спим до следующего цикла (мин. интервал)
            time.sleep(min(INTERVALS.values()))
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        for c in collectors.values():
            c.close()


def main():
    parser = argparse.ArgumentParser(description="DataCore Collector Runner")
    parser.add_argument("--db", help="Database URL (asyncpg)")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    run_all(db_url=args.db, once=args.once)


if __name__ == "__main__":
    main()