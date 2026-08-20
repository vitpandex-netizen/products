"""Сборщик Bitget — баланс, позиции, сделки."""
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from collectors.base import BaseCollector

logger = logging.getLogger(__name__)

# API keys — из переменных окружения
BITGET_API_KEY = os.environ.get("BITGET_API_KEY", "")
BITGET_SECRET_KEY = os.environ.get("BITGET_SECRET_KEY", "")
BITGET_PASSPHRASE = os.environ.get("BITGET_PASSPHRASE", "")


class BitgetCollector(BaseCollector):
    """Сборщик данных с Bitget."""

    def __init__(self, db_url: Optional[str] = None):
        super().__init__(
            name="bitget",
            api_url="https://api.bitget.com",
            db_url=db_url,
        )

    def fetch(self) -> list[dict]:
        """Забрать баланс, позиции, сделки."""
        if not all([BITGET_API_KEY, BITGET_SECRET_KEY, BITGET_PASSPHRASE]):
            logger.warning("Bitget API keys not set, skipping")
            return []

        import ccxt

        exchange = ccxt.bitget({
            "apiKey": BITGET_API_KEY,
            "secret": BITGET_SECRET_KEY,
            "password": BITGET_PASSPHRASE,
            "enableRateLimit": True,
            "options": {"defaultType": "swap", "uta": True},
        })

        result = []
        try:
            # Баланс
            balance = exchange.fetch_balance()
            total_usd = 0
            for currency, data in balance.get("total", {}).items():
                if data and data > 0:
                    total_usd += data
            result.append({
                "type": "balance",
                "total_usd": total_usd,
                "details": {k: v for k, v in balance.get("total", {}).items() if v and v > 0},
                "ts": datetime.now(timezone.utc).isoformat(),
            })

            # Позиции
            try:
                positions = exchange.fetch_positions()
                for pos in positions:
                    if float(pos.get("contracts", 0) or 0) > 0:
                        result.append({
                            "type": "position",
                            "symbol": pos.get("symbol", ""),
                            "side": pos.get("side", ""),
                            "size": float(pos.get("contracts", 0) or 0),
                            "entry_price": float(pos.get("entryPrice", 0) or 0),
                            "mark_price": float(pos.get("markPrice", 0) or 0),
                            "pnl": float(pos.get("unrealizedPnl", 0) or 0),
                            "pnl_pct": float(pos.get("percentage", 0) or 0),
                            "ts": datetime.now(timezone.utc).isoformat(),
                        })
            except Exception as e:
                logger.debug("Positions fetch error: %s", e)

            logger.info(
                "Fetched balance: $%.2f, positions: %d",
                total_usd,
                len([r for r in result if r["type"] == "position"]),
            )

        except Exception as e:
            logger.error("Bitget fetch error: %s", e)

        return result

    def store(self, data: list[dict]) -> int:
        if not self.db_url or not data:
            return 0

        import asyncpg
        import asyncio

        async def _store():
            conn = await asyncpg.connect(self.db_url)
            try:
                count = 0
                for d in data:
                    if d["type"] == "balance":
                        # Пишем баланс в prices
                        symbol_id = await conn.fetchval(
                            "SELECT id FROM core.symbols WHERE symbol = 'USDT' AND source_id = 3"
                        )
                        if symbol_id:
                            await conn.execute(
                                "INSERT INTO market_data.prices (symbol_id, source, price, volume, ts) "
                                "VALUES ($1, 'bitget', $2, $3, NOW())",
                                symbol_id, d["total_usd"], 0,
                            )
                            count += 1

                    elif d["type"] == "position":
                        # Пишем позицию
                        await conn.execute("""
                            INSERT INTO analytics.trades
                                (bot_name, symbol, side, quantity, price, value_usd, pnl, meta, ts)
                            VALUES ('bitget-bot', $1, $2, $3, $4, $5, $6, $7::jsonb, NOW())
                        """,
                            d["symbol"], d["side"],
                            d["size"], d["entry_price"],
                            d["size"] * d["mark_price"],
                            d["pnl"],
                            json.dumps({"mark_price": d["mark_price"], "pnl_pct": d["pnl_pct"]}),
                        )
                        count += 1

                # Лог
                await conn.execute(
                    "INSERT INTO core.collector_logs (collector, status, items_count) "
                    "VALUES ('bitget', 'success', $1)",
                    count,
                )
                await conn.close()
                return count
            except Exception as e:
                await conn.close()
                raise e

        return asyncio.run(_store())


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Bitget Collector")
    parser.add_argument("--db", help="Database URL")
    parser.add_argument("--stdout", action="store_true", help="Output to stdout")
    parser.add_argument("--interval", type=int, default=60, help="Loop interval")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    collector = BitgetCollector(db_url=args.db)
    try:
        while True:
            data = collector.fetch()
            if args.stdout or not args.db:
                print(json.dumps({
                    "collector": "bitget",
                    "items": len(data),
                    "data": data,
                }, indent=2, default=str))
            else:
                count = collector.store(data)
                if count:
                    logger.info("Stored %d items", count)

            if args.interval <= 0:
                break
            time.sleep(args.interval)
    finally:
        collector.close()


if __name__ == "__main__":
    main()