"""Сборщик новостей — мониторинг компаний по RSS/Atom."""
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional
from xml.etree import ElementTree

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from collectors.base import BaseCollector

logger = logging.getLogger(__name__)

# Мониторинг: компания → список RSS/сайтов
# Можно расширять без остановки бота
WATCHLIST = {
    # === УЗБЕКСКИЕ КОМПАНИИ ===
    "UzAuto Motors": {
        "keywords": ["UzAuto", "UzAuto Motors", "GM Uzbekistan", "Асака"],
        "feeds": [
            "https://www.spot.uz/ru/rss/",
            "https://www.gazeta.uz/ru/rss/",
        ],
    },
    "Uztelecom": {
        "keywords": ["Uztelecom", "Узтелеком", "Uzbektelecom"],
        "feeds": [
            "https://www.spot.uz/ru/rss/",
            "https://www.gazeta.uz/ru/rss/",
        ],
    },
    "National Bank of Uzbekistan": {
        "keywords": ["NBU", "Национальный банк", "Uzbekistan bank", "Central Bank of Uzbekistan"],
        "feeds": [
            "https://www.spot.uz/ru/rss/",
            "https://www.gazeta.uz/ru/rss/",
        ],
    },
    "Hamroh MMT": {
        "keywords": ["Hamroh", "Hamroh MMT", "HMMT"],
        "feeds": [
            "https://www.spot.uz/ru/rss/",
            "https://www.gazeta.uz/ru/rss/",
        ],
    },
    "Uzbekistan Economy": {
        "keywords": ["Узбекистан", "экономика", "инвестиции", "Uzbekistan", "investment"],
        "feeds": [
            "https://www.spot.uz/ru/rss/",
            "https://www.gazeta.uz/ru/rss/",
            "https://kun.uz/ru/rss",
        ],
    },
    # === АМЕРИКАНСКИЕ КОМПАНИИ ===
    "AAPL": {
        "keywords": ["Apple", "AAPL", "iPhone", "Tim Cook"],
        "feeds": ["https://feeds.content.dowjones.io/public/rss/mw_topstories"],
    },
    "MSFT": {
        "keywords": ["Microsoft", "MSFT", "Azure", "Windows"],
        "feeds": ["https://feeds.content.dowjones.io/public/rss/mw_topstories"],
    },
    "NVDA": {
        "keywords": ["NVIDIA", "NVDA", "Nvidia", "GPU"],
        "feeds": ["https://feeds.content.dowjones.io/public/rss/mw_topstories"],
    },
    "TSLA": {
        "keywords": ["Tesla", "TSLA", "Elon Musk", "Cybertruck"],
        "feeds": ["https://feeds.content.dowjones.io/public/rss/mw_topstories"],
    },
    "S&P 500": {
        "keywords": ["S&P 500", "SPY", "stock market", "Federal Reserve", "Fed", "inflation"],
        "feeds": [
            "https://feeds.content.dowjones.io/public/rss/mw_topstories",
            "https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headlines",
        ],
    },
}


class NewsCollector(BaseCollector):
    """Сборщик новостей по компаниям из RSS/Atom."""

    def __init__(self, db_url: Optional[str] = None):
        super().__init__(
            name="news",
            api_url="",
            db_url=db_url,
        )
        self.seen_urls = set()

    def fetch(self) -> list[dict]:
        """Забрать новости по всем компаниям из watchlist."""
        articles = []
        all_feeds = set()

        # Собираем все уникальные RSS
        for company, config in WATCHLIST.items():
            for feed in config.get("feeds", []):
                all_feeds.add(feed)

        for feed_url in all_feeds:
            try:
                items = self._parse_feed(feed_url)
                articles.extend(items)
            except Exception as e:
                logger.debug("Feed error %s: %s", feed_url, e)

        # Фильтруем по компаниям
        matched = []
        for article in articles:
            url = article.get("url", "")
            if url in self.seen_urls:
                continue
            self.seen_urls.add(url)

            title = (article.get("title", "") or "").lower()
            summary = (article.get("summary", "") or "").lower()
            text = title + " " + summary

            for company, config in WATCHLIST.items():
                for kw in config.get("keywords", []):
                    if kw.lower() in text:
                        article["company"] = company
                        article["keyword"] = kw
                        matched.append(article)
                        break

        # Ограничиваем размер seen_urls
        if len(self.seen_urls) > 10000:
            self.seen_urls = set(list(self.seen_urls)[-5000:])

        logger.info("Fetched %d feeds, %d matched articles", len(articles), len(matched))
        return matched

    def _parse_feed(self, url: str) -> list[dict]:
        """Парсинг RSS/Atom ленты."""
        resp = self.client.get(url, timeout=15)
        resp.raise_for_status()

        articles = []
        root = ElementTree.fromstring(resp.content)

        # RSS
        for item in root.iter("item"):
            articles.append(self._extract_rss_item(item))

        # Atom
        for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
            articles.append(self._extract_atom_entry(entry))

        return articles

    def _extract_rss_item(self, item) -> dict:
        ns = {"dc": "http://purl.org/dc/elements/1.1/"}
        return {
            "title": self._get_text(item, "title"),
            "url": self._get_text(item, "link"),
            "summary": self._get_text(item, "description") or "",
            "published": self._get_text(item, "pubDate") or self._get_text(item, "dc:date", ns),
            "source": "rss",
        }

    def _extract_atom_entry(self, entry) -> dict:
        return {
            "title": self._get_text(entry, "{http://www.w3.org/2005/Atom}title"),
            "url": self._get_link(entry),
            "summary": self._get_text(entry, "{http://www.w3.org/2005/Atom}summary") or "",
            "published": self._get_text(entry, "{http://www.w3.org/2005/Atom}updated"),
            "source": "atom",
        }

    def _get_text(self, parent, tag, ns=None):
        el = parent.find(tag, ns) if ns else parent.find(tag)
        return el.text.strip() if el is not None and el.text else ""

    def _get_link(self, entry):
        for link in entry.findall("{http://www.w3.org/2005/Atom}link"):
            href = link.get("href", "")
            if href:
                return href
        return ""

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
                    # Проверяем, не было ли уже такой новости
                    existing = await conn.fetchval(
                        "SELECT id FROM analytics.signals WHERE source='news' AND meta->>'url'=$1 LIMIT 1",
                        d["url"],
                    )
                    if existing:
                        continue

                    await conn.execute("""
                        INSERT INTO analytics.signals
                            (source, signal_type, symbol, direction, strength, reason, meta, ts)
                        VALUES ('news', 'news_alert', $1, 'neutral', 0.5, $2, $3::jsonb, NOW())
                    """,
                        d.get("company", "?"),
                        "📰 {}: {} — {}".format(
                            d.get("company", "?"),
                            d["title"][:150],
                            d["url"],
                        ),
                        json.dumps({
                            "url": d["url"],
                            "title": d["title"],
                            "keyword": d.get("keyword", ""),
                        }),
                    )
                    count += 1

                await conn.execute(
                    "INSERT INTO core.collector_logs (collector, status, items_count) VALUES ('news', 'success', $1)",
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

    parser = argparse.ArgumentParser(description="News Collector")
    parser.add_argument("--db", help="Database URL")
    parser.add_argument("--stdout", action="store_true")
    parser.add_argument("--interval", type=int, default=300, help="Loop interval (seconds)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    collector = NewsCollector(db_url=args.db)
    try:
        while True:
            data = collector.fetch()
            if args.stdout or not args.db:
                print(json.dumps({
                    "collector": "news",
                    "items": len(data),
                    "articles": data[:5],
                }, indent=2, default=str))
            else:
                count = collector.store(data)
                if count:
                    logger.info("Stored %d news items", count)

            if args.interval <= 0:
                break
            time.sleep(args.interval)
    finally:
        collector.close()


if __name__ == "__main__":
    main()