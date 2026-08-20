"""Сборщик Polymarket — prediction markets."""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional

import httpx

# Добавляем путь к модулям core для импорта БД
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from collectors.base import BaseCollector

logger = logging.getLogger(__name__)

GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"
DATA_API = "https://data-api.polymarket.com"


class PolymarketCollector(BaseCollector):
    """Сборщик данных с Polymarket."""

    def __init__(self, db_url: Optional[str] = None):
        super().__init__(
            name="polymarket",
            api_url=GAMMA_API,
            db_url=db_url,
        )

    def fetch(self) -> list[dict]:
        """Забрать топовые активные рынки + сделки."""
        result = []
        result.extend(self._fetch_markets())
        result.extend(self._fetch_trades())
        return result

    def _fetch_markets(self) -> list[dict]:
        """Получить активные рынки по объёму."""
        all_markets = []

        # Забираем события (events) — топ по объёму
        try:
            resp = self.client.get(
                f"{GAMMA_API}/events",
                params={
                    "limit": 30,
                    "active": "true",
                    "closed": "false",
                    "order": "volume",
                    "ascending": "false",
                },
            )
            resp.raise_for_status()
            events = resp.json()
        except Exception as e:
            logger.error("Failed to fetch events: %s", e)
            return []

        for evt in events:
            event_title = evt.get("title", "")
            event_slug = evt.get("slug", "")
            category = evt.get("category", "")

            for m in evt.get("markets", []):
                try:
                    prices = json.loads(m.get("outcomePrices", "[]"))
                    if len(prices) < 2:
                        continue

                    end_date_raw = m.get("endDate")
                    end_date = None
                    if end_date_raw:
                        try:
                            end_date = datetime.fromisoformat(end_date_raw.replace("Z", "+00:00"))
                        except (ValueError, AttributeError):
                            pass

                    all_markets.append({
                        "type": "market",
                        "condition_id": m.get("conditionId", ""),
                        "question": m.get("question", ""),
                        "event_title": event_title,
                        "event_slug": event_slug,
                        "category": category,
                        "outcome_yes": float(prices[0]),
                        "outcome_no": float(prices[1]),
                        "volume": float(m.get("volume", 0) or 0),
                        "liquidity": float(m.get("liquidity", 0) or 0),
                        "open_interest": None,
                        "active": m.get("active", True),
                        "closed": m.get("closed", False),
                        "end_date": end_date,
                        "ts": datetime.now(timezone.utc).isoformat(),
                    })
                except (json.JSONDecodeError, ValueError, IndexError) as e:
                    logger.debug("Parse error for market %s: %s", m.get("question", "?"), e)
                    continue

        logger.info("Fetched %d markets from events", len(all_markets))
        return all_markets

    def _fetch_trades(self) -> list[dict]:
        """Получить последние сделки."""
        try:
            resp = self.client.get(
                f"{DATA_API}/trades",
                params={"limit": 50},
            )
            resp.raise_for_status()
            trades = resp.json()
        except Exception as e:
            logger.error("Failed to fetch trades: %s", e)
            return []

        result = []
        for t in trades if isinstance(trades, list) else []:
            if not isinstance(t, dict):
                continue
            try:
                result.append({
                    "type": "trade",
                    "condition_id": t.get("conditionId", ""),
                    "title": t.get("title", ""),
                    "side": t.get("side", ""),
                    "price": float(t.get("price", 0) or 0),
                    "size": float(t.get("size", 0) or 0),
                    "outcome": t.get("outcome", ""),
                    "timestamp": t.get("timestamp", ""),
                    "ts": datetime.now(timezone.utc).isoformat(),
                })
            except (ValueError, TypeError):
                continue

        return result

    def store(self, data: list[dict]) -> int:
        """Сохранить данные в БД через прямой SQL."""
        # Если нет db_url — работаем через stdout для отладки
        if not self.db_url:
            return len(data)

        import asyncpg
        import asyncio

        async def _store():
            conn = await asyncpg.connect(self.db_url)
            try:
                markets = [d for d in data if d.get("type") == "market"]
                trades = [d for d in data if d.get("type") == "trade"]
                count = 0

                for m in markets:
                    # Upsert: INSERT ... ON CONFLICT
                    await conn.execute("""
                        INSERT INTO market_data.prediction_markets
                            (condition_id, question, event_title, event_slug, category,
                             outcome_yes, outcome_no, volume, liquidity, open_interest,
                             active, closed, end_date, last_updated)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW())
                        ON CONFLICT (condition_id) DO UPDATE SET
                            outcome_yes = EXCLUDED.outcome_yes,
                            outcome_no = EXCLUDED.outcome_no,
                            volume = EXCLUDED.volume,
                            liquidity = EXCLUDED.liquidity,
                            active = EXCLUDED.active,
                            closed = EXCLUDED.closed,
                            last_updated = NOW()
                    """,
                        m["condition_id"], m["question"], m["event_title"],
                        m["event_slug"], m["category"],
                        m["outcome_yes"], m["outcome_no"],
                        m["volume"], m["liquidity"], m["open_interest"],
                        m["active"], m["closed"],
                        m["end_date"] if m["end_date"] else None,
                    )
                    count += 1

                    # Пишем историю
                    await conn.execute("""
                        INSERT INTO market_data.prediction_history
                            (market_id, outcome_yes, outcome_no, volume, ts)
                        VALUES (
                            (SELECT id FROM market_data.prediction_markets WHERE condition_id = $1),
                            $2, $3, $4, NOW()
                        )
                    """, m["condition_id"], m["outcome_yes"], m["outcome_no"], m["volume"])

                # Лог сборщика
                await conn.execute("""
                    INSERT INTO core.collector_logs (collector, status, duration_ms, items_count)
                    VALUES ('polymarket', 'success', 0, $1)
                """, len(markets))

                await conn.close()
                return count
            except Exception as e:
                await conn.close()
                raise e

        return asyncio.run(_store())

    def store_stdout(self, data: list[dict]):
        """Вывод в JSON для отладки / перенаправления."""
        markets = [d for d in data if d.get("type") == "market"]
        trades = [d for d in data if d.get("type") == "trade"]

        print(json.dumps({
            "collector": "polymarket",
            "markets_count": len(markets),
            "trades_count": len(trades),
            "markets": markets[:5],  # топ-5 для компактности
            "trades": trades[:5],
            "ts": datetime.now(timezone.utc).isoformat(),
        }, indent=2, default=str))


def main():
    """Точка входа для запуска из cron / systemd."""
    import argparse
    import time

    parser = argparse.ArgumentParser(description="Polymarket Data Collector")
    parser.add_argument("--db", help="Database URL (asyncpg format)")
    parser.add_argument("--stdout", action="store_true", help="Output to stdout instead of DB")
    parser.add_argument("--interval", type=int, default=0, help="Loop interval in seconds (0 = run once)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    collector = PolymarketCollector(db_url=args.db)
    try:
        while True:
            data = collector.fetch()
            if args.stdout:
                collector.store_stdout(data)
            elif args.db:
                count = collector.store(data)
                logger.info("Stored %d items", count)

            if args.interval <= 0:
                break
            time.sleep(args.interval)
    finally:
        collector.close()


if __name__ == "__main__":
    main()