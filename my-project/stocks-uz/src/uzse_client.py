"""
uzse_client — парсер текущих цен с сайта UZSE.

Источник: https://uzse.uz/trade_results/ (публичная страница итогов торгов).
Парсинг через BeautifulSoup по классам внутри .main-ticker-item.
"""

import logging
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Браузерный User-Agent — без него сайт отдаёт 403
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
TRADE_RESULTS_URL = "https://uzse.uz/trade_results/"


class UZSEClient:
    """Клиент для получения текущих котировок с uzse.uz."""

    def __init__(self, timeout: int = 30):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": BROWSER_UA})
        self.timeout = timeout

    def fetch_all(self) -> list:
        """Получить текущие цены всех тикеров со страницы trade_results.

        Страница может содержать дубли (два блока с одинаковыми тикерами) —
        возвращаем только уникальные (по первому вхождению).
        """
        html = self._fetch_page()
        if html is None:
            return []

        soup = BeautifulSoup(html, "html.parser")
        items = soup.find_all("div", class_="main-ticker-item")

        seen: set = set()
        results = []
        for item in items:
            title_div = item.find("div", class_="title")
            if not title_div:
                continue
            link = title_div.find("a")
            if not link:
                continue
            link_text = link.get_text(strip=True)
            ticker = link_text.split()[0].upper()
            if ticker in seen:
                continue
            seen.add(ticker)
            results.append(self._parse_item(item, ticker))

        return results

    def fetch_ticker(self, ticker: str) -> Optional[dict]:
        """Получить текущую цену для одного тикера."""
        for row in self.fetch_all():
            if row["ticker"] == ticker.upper():
                return row
        logger.warning("Тикер %s не найден на странице trade_results", ticker)
        return None

    def _fetch_page(self) -> Optional[str]:
        """GET trade_results/ и вернуть HTML или None."""
        try:
            resp = self.session.get(TRADE_RESULTS_URL, timeout=self.timeout)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            logger.error("Ошибка загрузки %s: %s", TRADE_RESULTS_URL, e)
            return None

    def _parse_item(self, item, ticker: str) -> dict:
        """Извлечь цены из .main-ticker-item блока."""
        price_values = item.find_all("span", class_="price-value")
        datetime_value = item.find("span", class_="datetime-value")

        closing_price = None
        last_trade_price = None

        if len(price_values) >= 1:
            closing_price = self._parse_price(self._own_text(price_values[0]))

        if len(price_values) >= 2:
            last_trade_price = self._parse_price(self._own_text(price_values[1]))

        last_trade_date = (
            datetime_value.get_text(strip=True) if datetime_value else None
        )

        return {
            "ticker": ticker,
            "closing_price": closing_price,
            "last_trade_price": last_trade_price,
            "last_trade_date": last_trade_date,
        }

    @staticmethod
    def _own_text(tag) -> str:
        """Текст только самого тега, БЕЗ вложенных тегов.

        Критично: внутри span.price-value сайт кладёт вложенный
        span.price-down/.price-up с дельтой изменения — например
        "87 <span>(▼ 4.67)</span>". get_text() склеил бы всё вместе и
        дельта попала бы в цену.
        """
        return "".join(tag.find_all(string=True, recursive=False)).strip()

    @staticmethod
    def _parse_price(text: str) -> Optional[float]:
        """Извлечь число из текста цены.

        UZSE форматирует цены в американском стиле: запятая — разделитель
        тысяч, точка — десятичный. Примеры:
            "79"       → 79.0
            "88.29"    → 88.29
            "6,099"    → 6099.0   (НЕ 6.099 — запятая разделитель тысяч)
            "3,748.99" → 3748.99
        """
        cleaned = text.replace("\xa0", "").replace(" ", "").replace(",", "")
        match = re.search(r"(\d+(?:\.\d+)?)", cleaned)
        if match:
            return float(match.group(1))
        return None


# ===== CLI =====
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    client = UZSEClient()
    result = client.fetch_ticker("HMKB")
    if result:
        print(result)
    else:
        print("No data")
