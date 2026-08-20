"""Сборщик Yahoo Finance — цены активов."""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from collectors.base import BaseCollector

logger = logging.getLogger(__name__)

# Маппинг символов
SYMBOLS = {
    # Индексы
    "^GSPC": "%5EGSPC",
    "^IXIC": "%5EIXIC",
    "^DJI": "%5EDJI",
    "^VIX": "%5EVIX",
    # ETF
    "SPY": "SPY",
    "QQQ": "QQQ",
    # Крипто
    "BTC-USD": "BTC-USD",
    "ETH-USD": "ETH-USD",
    "SOL-USD": "SOL-USD",
    # Товары
    "GC=F": "GC=F",
    "CL=F": "CL=F",
    # US Stocks — топ
    "AAPL": "AAPL",
    "MSFT": "MSFT",
    "GOOGL": "GOOGL",
    "AMZN": "AMZN",
    "NVDA": "NVDA",
    "META": "META",
    "TSLA": "TSLA",
    "JPM": "JPM",
    "V": "V",
    "JNJ": "JNJ",
    "WMT": "WMT",
    "PG": "PG",
    "MA": "MA",
    "UNH": "UNH",
    "HD": "HD",
    "BAC": "BAC",
    "DIS": "DIS",
    "NFLX": "NFLX",
    "ADBE": "ADBE",
    "CRM": "CRM",
    "INTC": "INTC",
    "AMD": "AMD",
    "UBER": "UBER",
    "PYPL": "PYPL",
    "SNAP": "SNAP",
    "SQ": "SQ",
    "COIN": "COIN",
    "MSTR": "MSTR",
    "PLTR": "PLTR",
}


class YahooFinanceCollector(BaseCollector):
    """Сборщик данных с Yahoo Finance."""

    def __init__(self, db_url: Optional[str] = None):
        super().__init__(
            name="yahoo",
            api_url="https://query2.finance.yahoo.com",
            db_url=db_url,
        )
        self.client.headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

    def fetch(self) -> list[dict]:
        """Забрать цены по всем символам."""
        results = []
        for label, ticker in SYMBOLS.items():
            try:
                data = self._fetch_one(ticker, label)
                if data:
                    results.append(data)
            except Exception as e:
                logger.warning("Failed to fetch %s: %s", label, e)
                continue
        return results

    def _fetch_one(self, ticker: str, label: str) -> Optional[dict]:
        """Получить цену одного символа."""
        resp = self.client.get(
            f"{self.api_url}/v8/finance/chart/{ticker}",
            params={"region": "US", "lang": "en-US", "interval": "2m", "range": "1d"},
        )
        resp.raise_for_status()
        data = resp.json()

        result = data.get("chart", {}).get("result", [{}])[0]
        meta = result.get("meta", {})

        return {
            "type": "price",
            "symbol": label,
            "price": meta.get("regularMarketPrice"),
            "previous_close": meta.get("previousClose"),
            "day_high": meta.get("regularMarketDayHigh"),
            "day_low": meta.get("regularMarketDayLow"),
            "volume": meta.get("regularMarketVolume"),
            "ts": datetime.now(timezone.utc).isoformat(),
        }

    def store(self, data: list[dict]) -> int:
        if not self.db_url:
            return len(data)

        import asyncpg
        import asyncio

        async def _store():
            conn = await asyncpg.connect(self.db_url)
            try:
                count = 0
                for d in data:
                    # Получаем symbol_id
                    row = await conn.fetchrow("""
                        SELECT id FROM core.symbols WHERE symbol = $1
                    """, d["symbol"])
                    if not row:
                        continue

                    await conn.execute("""
                        INSERT INTO market_data.prices
                            (symbol_id, source, price, bid, ask, volume, ts)
                        VALUES ($1, 'yahoo', $2, NULL, NULL, $3, NOW())
                    """, row["id"], d["price"], d["volume"])
                    count += 1

                await conn.execute("""
                    INSERT INTO core.collector_logs (collector, status, items_count)
                    VALUES ('yahoo', 'success', $1)
                """, count)

                await conn.close()
                return count
            except Exception as e:
                await conn.close()
                raise e

        return asyncio.run(_store())


def main():
    import argparse
    import time

    parser = argparse.ArgumentParser(description="Yahoo Finance Collector")
    parser.add_argument("--db", help="Database URL")
    parser.add_argument("--stdout", action="store_true", help="Output to stdout")
    parser.add_argument("--interval", type=int, default=0, help="Loop interval in seconds (0 = run once)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    collector = YahooFinanceCollector(db_url=args.db)
    try:
        while True:
            data = collector.fetch()
            if args.stdout or not args.db:
                print(json.dumps({
                    "collector": "yahoo",
                    "items": len(data),
                    "prices": data,
                    "ts": datetime.now(timezone.utc).isoformat(),
                }, indent=2, default=str))
            else:
                count = collector.store(data)
                logger.info("Stored %d items", count)

            if args.interval <= 0:
                break
            time.sleep(args.interval)
    finally:
        collector.close()


if __name__ == "__main__":
    main()