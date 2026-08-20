"""Analytics Engine — анализирует данные, генерирует сигналы.

Подписывается на Redis Pub/Sub, анализирует данные в БД.
"""
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Движок аналитики."""

    def __init__(self, db_url: Optional[str] = None, redis_url: Optional[str] = None):
        self.db_url = db_url
        self.redis_url = redis_url
        self.redis = None
        if redis_url:
            import redis.asyncio as aioredis
            self.redis = aioredis.from_url(redis_url, decode_responses=True)

    async def analyze_polymarket_curve(self):
        """Анализ кривой вероятности Bitcoin price range.

        Проверяет, что P(>$X) >= P(>$X+1). Нарушение = сигнал.
        """
        if not self.db_url:
            logger.warning("No DB URL, skipping curve analysis")
            return []

        import asyncpg

        conn = await asyncpg.connect(self.db_url)
        try:
            # Берём Bitcoin price range markets
            rows = await conn.fetch("""
                SELECT question, outcome_yes, outcome_no, volume, condition_id
                FROM market_data.prediction_markets
                WHERE event_title ILIKE '%bitcoin%' AND event_title ILIKE '%price%'
                  AND active = true AND closed = false
                  AND outcome_yes > 0.01 AND outcome_yes < 0.99
                ORDER BY outcome_yes DESC
            """)

            signals = []
            for i in range(len(rows) - 1):
                curr = rows[i]
                next_ = rows[i + 1]

                # Если цена выше (больше шансов) для более высокой цели — аномалия
                if curr["outcome_yes"] > next_["outcome_yes"]:
                    continue  # Нормальная кривая

                # Разница должна быть значимой (>1pp)
                diff = next_["outcome_yes"] - curr["outcome_yes"]
                if diff < 0.01:
                    continue

                # Аномалия: P(>$X) < P(>$X+1) — нарушение монотонности
                logger.info(
                    "Curve anomaly: %.1f%% -> %.1f%%",
                    curr["outcome_yes"] * 100,
                    next_["outcome_yes"] * 100,
                )
                signals.append({
                    "source": "polymarket",
                    "signal_type": "curve_mispricing",
                    "symbol": "BTC-USD",
                    "direction": "sell" if curr["outcome_yes"] > next_["outcome_yes"] else "buy",
                    "strength": diff,
                    "reason": f"Curve anomaly: {curr['question'][:50]} ({curr['outcome_yes']*100:.1f}%) "
                              f"vs {next_['question'][:50]} ({next_['outcome_yes']*100:.1f}%)",
                })

            return signals

        finally:
            await conn.close()

    async def analyze_momentum(self):
        """Анализ моментума — резкие изменения цен."""
        if not self.db_url:
            return []

        import asyncpg

        conn = await asyncpg.connect(self.db_url)
        try:
            # Смотрим prediction markets с изменением > 10% за последние 10 записей
            rows = await conn.fetch("""
                WITH latest AS (
                    SELECT market_id, outcome_yes,
                           LAG(outcome_yes, 5) OVER (PARTITION BY market_id ORDER BY ts) as old_yes
                    FROM market_data.prediction_history
                    WHERE ts > NOW() - INTERVAL '1 hour'
                )
                SELECT lm.market_id, pm.question, pm.outcome_yes,
                       lm.old_yes
                FROM latest lm
                JOIN market_data.prediction_markets pm ON pm.id = lm.market_id
                WHERE lm.old_yes IS NOT NULL
                  AND abs(lm.outcome_yes - lm.old_yes) > 0.10
                  AND NOT EXISTS (
                    SELECT 1 FROM analytics.signals s
                    WHERE s.signal_type = 'momentum_break'
                      AND LEFT(pm.question, 50) = s.symbol
                      AND s.ts > NOW() - INTERVAL '2 hours'
                  )
                ORDER BY abs(lm.outcome_yes - lm.old_yes) DESC
                LIMIT 5
            """)

            signals = []
            for r in rows:
                change_val = r["outcome_yes"] - r["old_yes"]
                direction = "buy" if change_val > 0 else "sell"
                signals.append({
                    "source": "polymarket",
                    "signal_type": "momentum_break",
                    "symbol": str(r["question"])[:50],
                    "direction": direction,
                    "strength": abs(change_val),
                    "reason": "Momentum: {} changed {}{:.1f}% in 5 ticks".format(
                        str(r["question"])[:50],
                        "+" if change_val > 0 else "",
                        change_val * 100,
                    ),
                })

            return signals

        finally:
            await conn.close()

    async def run_cycle(self):
        """Один цикл анализа."""
        signals = []
        signals.extend(await self.analyze_polymarket_curve())
        signals.extend(await self.analyze_momentum())

        if signals and self.db_url:
            await self._store_signals(signals)
            logger.info("Generated %d signals", len(signals))

        if signals and self.redis:
            for s in signals:
                await self.redis.publish("signals", json.dumps(s, default=str))

        return signals

    async def _store_signals(self, signals: list[dict]):
        """Сохранить сигналы в БД."""
        import asyncpg

        conn = await asyncpg.connect(self.db_url)
        try:
            for s in signals:
                await conn.execute("""
                    INSERT INTO analytics.signals
                        (source, signal_type, symbol, direction, strength, reason, ts)
                    VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """, s["source"], s["signal_type"], s["symbol"],
                    s["direction"], s["strength"], s["reason"])
        finally:
            await conn.close()

    async def close(self):
        if self.redis:
            await self.redis.close()


async def main_loop(db_url: str, redis_url: str = None, interval: int = 60):
    """Бесконечный цикл анализа."""
    engine = AnalyticsEngine(db_url=db_url, redis_url=redis_url)
    try:
        while True:
            await engine.run_cycle()
            await asyncio.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Shutting down analytics engine...")
    finally:
        await engine.close()


if __name__ == "__main__":
    import asyncio
    import argparse

    parser = argparse.ArgumentParser(description="Analytics Engine")
    parser.add_argument("--db", required=True, help="Database URL")
    parser.add_argument("--redis", help="Redis URL")
    parser.add_argument("--interval", type=int, default=60, help="Analysis interval (seconds)")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    if args.once:
        async def run_once():
            engine = AnalyticsEngine(db_url=args.db, redis_url=args.redis)
            try:
                signals = await engine.run_cycle()
                print(json.dumps({"signals": signals}, indent=2, default=str))
            finally:
                await engine.close()
        asyncio.run(run_once())
    else:
        asyncio.run(main_loop(args.db, args.redis, args.interval))