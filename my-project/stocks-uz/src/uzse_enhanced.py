"""
uzse_enhanced — расширенный клиент UZSE с поддержкой JSON API, OHLCV истории
и сбора данных с TG-каналов аналитики.

Источники:
  - trade_results/ (HTML) — текущие цены всех тикеров (72 шт)
  - trade_results.json (JSON API) — сырые сделки (22k+ записей, 444 страницы)
  - isu_infos/STK?isu_cd=X (HTML) — OHLCV история + фундаментальные данные
"""

import logging
import re
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
TRADE_RESULTS_URL = "https://uzse.uz/trade_results/"
TRADE_RESULTS_JSON = "https://uzse.uz/trade_results.json"
ISU_INFO_URL = "https://uzse.uz/isu_infos/STK?isu_cd={}"

TASHKENT_TZ = timezone(timedelta(hours=5))

# Маппинг тикер -> issue_code (актуально на 12.08.2026)
TICKER_TO_ISU = {
    "AGMKP": "UZ700055K015", "KFSK": "UZ7001100005", "KFSKP": "UZ700110K018",
    "AGBA": "UZ7001560000", "AGBAP": "UZ700156K011", "UZMT": "UZ7003040001",
    "UPOS": "UZ7005280001", "UPOSP": "UZ700528K011", "MIQE": "UZ7007440009",
    "UZGFP": "UZ700788K011", "HMKB": "UZ7011340005", "HMKBP": "UZ701134K017",
    "UZAL": "UZ7011500004", "PLST": "UZ7011550009", "JASM": "UZ7012450001",
    "MCBA": "UZ7015230004", "MCBAP": "UZ701523K011", "UZHM": "UZ7016400002",
    "BRBN": "UZ7018790004", "BRBNP": "UZ701879K017", "UZMK": "UZ7021720006",
    "UZMKP": "UZ702172K016", "KSCM": "UZ7022100000", "OHDN": "UZ7023190000",
    "KVTS": "UZ7025770007", "BIOK": "UZ7025870005", "TKDM": "UZ7026980001",
    "TKDMP": "UZ702698K010", "BECM": "UZ7028450003", "KASU": "UZ7028660007",
    "KASUP": "UZ702866K013", "QZSM": "UZ7029000005", "TRSB": "UZ7033480003",
    "QATT": "UZ7034730000", "METQ": "UZ7035230000", "TNBN": "UZ7035530003",
    "TNBNP": "UZ703553K016", "UZNGP": "UZ7036271003", "TGPG": "UZ7036730008",
    "SQBN": "UZ7037560008", "SQBNP": "UZ703756K015", "GRBK": "UZ7037610001",
    "CBSK": "UZ7038380000", "IPKY": "UZ7039920002", "UQEQ": "UZ7042540003",
    "NGQS": "UZ7042650000", "URTS": "UZ7043200003", "UTGA": "UZ7043380003",
    "UTGAP": "UZ704338K011", "ALKB": "UZ7044760005", "ALKBP": "UZ704476K019",
    "ALSM": "UZ7045320007", "ALSMP": "UZ704532K019", "BNGP": "UZ7045550009",
    "BNGPP": "UZ704555K010", "UZAS": "UZ7045570007", "UNVB": "UZ7046910004",
    "UZTL": "UZ7047110000", "UZTLP": "UZ704711K019", "UTYK": "UZ7051720009",
    "YRFS": "UZ7051820007", "UVGT": "UZ7051840005", "UZIR": "UZ7052260005",
    "UZIRP": "UZ705226K017", "BTRL": "UZ7052610001", "IPTB": "UZ7054570005",
    "IPTBP": "UZ705457K018", "DORI": "UZ7054590003", "UZML": "UZ7055630006",
    "UZINP": "UZ7056921008", "TMYS": "UZ7057480012", "UZNF": "UZ7058980010",
}


class UZSEEnhancedClient:
    """Расширенный клиент для получения данных UZSE."""

    def __init__(self, timeout: int = 30):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": BROWSER_UA})
        self.timeout = timeout

    # ===== ТЕКУЩИЕ ЦЕНЫ (HTML парсинг) =====

    def fetch_all_prices(self) -> list[dict]:
        """Получить текущие цены всех тикеров (72 шт) с trade_results/ HTML."""
        html = self._fetch_page(TRADE_RESULTS_URL)
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

            # Парсим цены
            price_values = item.find_all("span", class_="price-value")
            datetime_value = item.find("span", class_="datetime-value")

            closing_price = None
            last_trade_price = None
            change = None
            direction = None

            if len(price_values) >= 1:
                closing_price = self._parse_price(self._own_text(price_values[0]))

            if len(price_values) >= 2:
                last_trade_price = self._parse_price(self._own_text(price_values[1]))
                # Change is in a nested span
                change_span = price_values[1].find("span", class_="price-up") or price_values[1].find("span", class_="price-down")
                if change_span:
                    change_text = change_span.get_text(strip=True)
                    change_match = re.search(r"([\d,.]+)", change_text)
                    if change_match:
                        change = self._parse_price(change_match.group(1))
                    direction = "up" if change_span.get("class") == ["price-up"] else "down"

            last_trade_date = (
                datetime_value.get_text(strip=True) if datetime_value else None
            )

            # Change percent
            change_pct = None
            if closing_price and closing_price > 0 and change is not None:
                change_pct = round((change / closing_price) * 100, 2)
                if direction == "down":
                    change_pct = -abs(change_pct)

            result = {
                "ticker": ticker,
                "issue_code": TICKER_TO_ISU.get(ticker),
                "closing_price": closing_price,
                "last_trade_price": last_trade_price,
                "change": change,
                "change_pct": change_pct,
                "last_trade_date": last_trade_date,
                "fetched_at": datetime.now(TASHKENT_TZ).isoformat(),
            }
            results.append(result)

        return results

    def fetch_ticker_price(self, ticker: str) -> Optional[dict]:
        """Получить текущую цену одного тикера."""
        for row in self.fetch_all_prices():
            if row["ticker"] == ticker.upper():
                return row
        logger.warning("Ticker %s not found", ticker)
        return None

    # ===== OHLCV ИСТОРИЯ (isu_infos/STK) =====

    def fetch_ohlcv_history(self, ticker: str, days: int = 30) -> list[dict]:
        """Получить OHLCV историю тикера со страницы isu_infos/STK.

        Данные встроены в JavaScript: data.push([timestamp, open, high, low, close, volume])
        """
        issue_code = TICKER_TO_ISU.get(ticker.upper())
        if not issue_code:
            logger.warning("No issue_code for ticker %s", ticker)
            return []

        html = self._fetch_page(ISU_INFO_URL.format(issue_code))
        if html is None:
            return []

        # Ищем OHLCV данные в JS
        pattern = r'data\.push\(\s*\[\s*moment\("(\d{8})",\s*"YYYYMMDD"\)\._d\.valueOf\(\),\s*([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*(\d+)'
        matches = re.findall(pattern, html)

        results = []
        cutoff = datetime.now(TASHKENT_TZ) - timedelta(days=days)

        for m in matches:
            date_str = m[0]
            try:
                date = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=TASHKENT_TZ)
            except ValueError:
                continue

            if date < cutoff:
                continue

            results.append({
                "ticker": ticker.upper(),
                "date": date.isoformat(),
                "open": float(m[1]),
                "high": float(m[2]),
                "low": float(m[3]),
                "close": float(m[4]),
                "volume": int(m[5]),
            })

        return sorted(results, key=lambda x: x["date"])

    # ===== СЫРЫЕ СДЕЛКИ (JSON API) =====

    def fetch_trades(self, page: int = 1, per_page: int = 50) -> dict:
        """Получить сырые сделки с trade_results.json.

        Возвращает {'results': [...], 'meta': {...}, 'total_pages': N}
        """
        try:
            resp = self.session.get(
                TRADE_RESULTS_JSON,
                params={"page": page, "per_page": per_page},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "results": data.get("results", []),
                "meta": data.get("meta", {}),
                "total_pages": data.get("meta", {}).get("total_pages", 0),
            }
        except requests.RequestException as e:
            logger.error("JSON API error (page %d): %s", page, e)
            return {"results": [], "meta": {}, "total_pages": 0}

    def fetch_recent_trades(self, minutes: int = 60) -> list[dict]:
        """Получить свежие сделки за последние N минут."""
        all_trades = []
        page = 1
        cutoff = datetime.now(TASHKENT_TZ) - timedelta(minutes=minutes)

        while True:
            data = self.fetch_trades(page=page)
            trades = data.get("results", [])
            if not trades:
                break

            for t in trades:
                trade_time = t.get("created_at", "")
                if trade_time:
                    try:
                        tt = datetime.fromisoformat(trade_time)
                        if tt < cutoff:
                            # Достигли границы времени
                            return all_trades
                    except ValueError:
                        pass
                all_trades.append(t)

            if page >= data.get("total_pages", 1):
                break
            page += 1
            time.sleep(0.3)

        return all_trades

    # ===== ВСЁ В ОДНОМ: полный снимок =====

    def full_snapshot(self, ohlcv_days: int = 7) -> dict:
        """Полный снимок рынка: текущие цены + последние сделки + OHLCV топ-10."""
        prices = self.fetch_all_prices()
        logger.info("Fetched %d current prices", len(prices))

        # Сортируем по объёму изменений
        movers = sorted(
            [p for p in prices if p.get("change_pct") is not None],
            key=lambda x: abs(x["change_pct"]),
            reverse=True,
        )

        # OHLCV для топ-10 по капитализации/объёму
        ohlcv_data = {}
        top_tickers = [p["ticker"] for p in prices[:10]]
        for ticker in top_tickers:
            try:
                history = self.fetch_ohlcv_history(ticker, days=ohlcv_days)
                if history:
                    ohlcv_data[ticker] = history
                time.sleep(0.5)
            except Exception as e:
                logger.warning("OHLCV failed for %s: %s", ticker, e)

        return {
            "prices": prices,
            "count": len(prices),
            "movers": movers[:20],
            "top_gainers": [m for m in movers if m.get("change_pct", 0) > 0][:10],
            "top_losers": [m for m in movers if m.get("change_pct", 0) < 0][:10],
            "ohlcv": ohlcv_data,
            "fetched_at": datetime.now(TASHKENT_TZ).isoformat(),
        }

    # ===== ВНУТРЕННИЕ МЕТОДЫ =====

    def _fetch_page(self, url: str) -> Optional[str]:
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            logger.error("Failed to fetch %s: %s", url, e)
            return None

    @staticmethod
    def _own_text(tag) -> str:
        return "".join(tag.find_all(string=True, recursive=False)).strip()

    @staticmethod
    def _parse_price(text: str) -> Optional[float]:
        cleaned = text.replace("\xa0", "").replace(" ", "").replace(",", "")
        match = re.search(r"(\d+(?:\.\d+)?)", cleaned)
        if match:
            return float(match.group(1))
        return None


# ===== TG КАНАЛЫ АНАЛИТИКИ =====

class UZSEChannelCollector:
    """Сбор аналитики из Telegram-каналов."""

    CHANNELS = [
        # Official UZSE
        "fond_birja_signal",     # Официальные сигналы UZSE по тикерам
        "uzseofficial",          # Официальный UZSE: индекс UCI, объёмы
        
        # Аналитика и обзоры
        "kapdepo",               # Kap Depo: KD Index, обзоры банков, ЦБ
        "investds_uz",           # Invest DS: UzNIF, IPO, аналитика
        "hbcapital_uzb",         # HB Capital: брокерский рейтинг топ-10
        
        # Макроэкономика
        "FinansistUZ",           # Макро: ВВП, ставка ЦБ, реформы
        "kursiv_uz_ru",          # Бизнес-новости Узбекистана
        
        # Брокеры и рынки
        "FREEDOM_finance",       # Freedom Broker: US рынок, обзоры
        "jett_uz_club",          # Jett broker
        
        # Смежные
        "Sarmoya",               # Forex/Crypto/Investment
        "fondbozori",            # Мировые финансовые рынки
        "ipo_uzbekistan",        # IPO в Узбекистане
        "uzbekinvest",           # Uzbekinvest Insurance
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": BROWSER_UA})

    def fetch_channel(self, channel: str, limit: int = 10) -> list[dict]:
        """Получить последние сообщения из публичного TG-канала."""
        url = f"https://t.me/s/{channel}"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                logger.warning("Channel %s returned %d", channel, resp.status_code)
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            messages = soup.find_all("div", class_="tgme_widget_message_wrap")

            results = []
            for msg in messages[:limit]:
                text_div = msg.find("div", class_="tgme_widget_message_text")
                date_tag = msg.find("time", class_="time")

                text = text_div.get_text(strip=True) if text_div else ""
                date = date_tag.get("datetime", "") if date_tag else ""

                results.append({
                    "channel": channel,
                    "text": text[:2000],
                    "date": date,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                })

            return results
        except Exception as e:
            logger.error("Failed to fetch channel %s: %s", channel, e)
            return []

    def fetch_all_channels(self, limit: int = 5) -> list[dict]:
        """Получить сообщения из всех каналов."""
        all_messages = []
        for ch in self.CHANNELS:
            try:
                msgs = self.fetch_channel(ch, limit=limit)
                all_messages.extend(msgs)
                time.sleep(1)  # Rate limit
            except Exception as e:
                logger.warning("Channel %s error: %s", ch, e)
        return all_messages

    def parse_signal_message(self, text: str) -> Optional[dict]:
        """Парсинг структурированного сообщения от @fond_birja_signal.

        Формат:
        📊TICKER·Ko'tarildi/Tushdi
        🏢Компания ...
        💰Joriy narx X so'm (🟢+X% / 🔴−X%)
        📉Oldingi narx X so'm
        📈Narx farqi+X so'm
        📦Savdo miqdori:X ta
        📅Savdo kuni:DD.MM.YYYY
        """
        patterns = {
            "ticker": r"📊([A-Z]+)",
            "price": r"💰Joriy narx\s*([\d\s]+)\s*so'm",
            "change_pct": r"[🟢🔴]\s*([+-]?[\d.]+)%",
            "prev_price": r"📉Oldingi narx\s*([\d\s]+)\s*so'm",
            "price_diff": r"📈Narx farqi\s*([+-]?[\d\s]+)\s*so'm",
            "volume": r"📦Savdo miqdori:\s*([\d\s]+)\s*ta",
            "date": r"📅Savdo kuni:\s*([\d.]+)",
        }

        result = {}
        for key, pattern in patterns.items():
            m = re.search(pattern, text)
            if m:
                val = m.group(1).strip()
                if key in ("price", "prev_price", "price_diff"):
                    val = float(val.replace(" ", "").replace(",", ""))
                elif key == "change_pct":
                    val = float(val.replace(",", "."))
                elif key == "volume":
                    val = int(val.replace(" ", "").replace(",", ""))
                result[key] = val

        # Direction
        if "Ko'tarildi" in text:
            result["direction"] = "up"
        elif "Tushdi" in text:
            result["direction"] = "down"

        return result if result else None


# ===== АНАЛИТИКА =====

class UZSEAnalytics:
    """Аналитика UZSE: тренды, моментум, алерты."""

    @staticmethod
    def compute_trends(prices: list[dict], history: dict[str, list[dict]]) -> dict:
        """Вычислить тренды для всех тикеров.

        Returns: {ticker: {trend, momentum_score, volume_surge, alert}}
        """
        trends = {}
        for p in prices:
            ticker = p["ticker"]
            ticker_history = history.get(ticker, [])

            trend = {
                "ticker": ticker,
                "current_price": p.get("last_trade_price") or p.get("closing_price"),
                "change_pct": p.get("change_pct", 0),
                "trend": "neutral",
                "momentum_score": 50,
                "alert": None,
            }

            if ticker_history and len(ticker_history) > 1:
                # Compute momentum over available history
                closes = [h["close"] for h in ticker_history]
                n = min(5, len(closes))
                if n >= 2:
                    # Simple momentum: close[-1] / close[-n] - 1
                    momentum = (closes[-1] / closes[-n] - 1) * 100
                    trend["momentum_5d"] = round(momentum, 2)

                    if momentum > 10:
                        trend["trend"] = "strong_up"
                        trend["momentum_score"] = min(100, 50 + int(momentum * 2))
                        trend["alert"] = f"🚀 {ticker} +{momentum:.1f}% за 5 дней!"
                    elif momentum > 5:
                        trend["trend"] = "up"
                        trend["momentum_score"] = min(80, 50 + int(momentum * 2))
                    elif momentum < -10:
                        trend["trend"] = "strong_down"
                        trend["momentum_score"] = max(0, 50 + int(momentum * 2))
                        trend["alert"] = f"🔻 {ticker} {momentum:.1f}% за 5 дней!"
                    elif momentum < -5:
                        trend["trend"] = "down"
                        trend["momentum_score"] = max(20, 50 + int(momentum * 2))
                    else:
                        trend["trend"] = "neutral"

                # Volume surge detection
                volumes = [h["volume"] for h in ticker_history]
                nv = min(5, len(volumes))
                if nv >= 3:
                    avg_vol = sum(volumes[:-1]) / (len(volumes) - 1)
                    if avg_vol > 0 and volumes[-1] > avg_vol * 2:
                        trend["volume_surge"] = round(volumes[-1] / avg_vol, 1)
                        trend["alert"] = (trend.get("alert") or "") + f" 📊 Объём x{trend['volume_surge']}"

            trends[ticker] = trend

        return trends

    @staticmethod
    def generate_daily_report(prices: list[dict], trends: dict,
                               channel_msgs: list[dict] | None = None) -> str:
        """Сгенерировать ежедневный отчёт по рынку UZSE."""
        now = datetime.now(TASHKENT_TZ)
        lines = [
            f"📊 **UZSE Daily Report**",
            f"📅 {now.strftime('%d.%m.%Y %H:%M')} (Tashkent)",
            f"Тикеров: {len(prices)} | Торговалось: {sum(1 for p in prices if p.get('last_trade_price'))}",
            "",
        ]

        # Top gainers
        gainers = sorted(
            [p for p in prices if p.get("change_pct") and p["change_pct"] > 0],
            key=lambda x: x["change_pct"], reverse=True,
        )[:7]
        if gainers:
            lines.append("**🚀 Топ Growers:**")
            for g in gainers:
                emoji = "🟢"
                lines.append(f"  {emoji} **{g['ticker']}**: "
                           f"{g.get('last_trade_price', 0):,.2f} сум "
                           f"(+{g['change_pct']:.2f}%)")
            lines.append("")

        # Top losers
        losers = sorted(
            [p for p in prices if p.get("change_pct") and p["change_pct"] < 0],
            key=lambda x: x["change_pct"],
        )[:7]
        if losers:
            lines.append("**🔻 Топ Losers:**")
            for l in losers:
                lines.append(f"  🔴 **{l['ticker']}**: "
                           f"{l.get('last_trade_price', 0):,.2f} сум "
                           f"({l['change_pct']:.2f}%)")
            lines.append("")

        # Alerts from trends
        alerts = [t["alert"] for t in trends.values() if t.get("alert")]
        if alerts:
            lines.append("**⚡ Алерты:**")
            for a in alerts[:5]:
                lines.append(f"  {a}")
            lines.append("")

        # Channel signals
        if channel_msgs:
            # Parse @fond_birja_signal signals
            signals = []
            for msg in channel_msgs:
                parsed = UZSEChannelCollector().parse_signal_message(msg["text"])
                if parsed:
                    signals.append(parsed)
            if signals:
                lines.append("**📡 Сигналы @fond_birja_signal:**")
                for s in signals[:5]:
                    em = "🟢" if s.get("direction") == "up" else "🔴"
                    lines.append(f"  {em} {s.get('ticker', '?')}: "
                               f"{s.get('price', 0):,.2f} сум "
                               f"({s.get('change_pct', 0):+.2f}%)")
                lines.append("")

            # Extract key news from channels
            news_items = []
            for msg in channel_msgs:
                ch = msg.get("channel", "")
                text = msg.get("text", "")
                if not text:
                    continue
                # UZSE official: index/volume data
                if ch == "uzseofficial":
                    # Extract UCI index
                    uci = re.search(r"UCI indeksi\s*([\d\s,.]+)", text)
                    if uci:
                        news_items.append(("📊", "UCI Index", uci.group(1).strip()))
                    # Extract volume
                    vol = re.search(r"savdolarning umumiy hajmi\s*([\d\s,.]+trln)", text, re.IGNORECASE)
                    if vol:
                        news_items.append(("💹", "Объём торгов", vol.group(1).strip()))
                # Kap Depo: KD Index
                elif ch == "kapdepo":
                    kd = re.search(r"KD Index.*?o'zgarishlar", text, re.IGNORECASE)
                    if kd:
                        news_items.append(("📈", "KD Index", "обновление"))
                    # ЦБ резервы
                    cb = re.search(r"ЦБ.*?резерв", text, re.IGNORECASE)
                    if cb:
                        snippet = text[:120]
                        news_items.append(("🏦", "ЦБ", snippet))
                # Macro news
                elif ch == "FinansistUZ":
                    # Extract key economic news
                    for kw in ["ВВП", "ставк", "инфляци", "реформ", "налог", "бюджет"]:
                        if kw.lower() in text.lower():
                            snippet = text[:150]
                            news_items.append(("📰", "Макро", snippet))
                            break
                # IPO news
                elif ch == "investds_uz" or ch == "ipo_uzbekistan":
                    if "IPO" in text or "UzNIF" in text or "размещ" in text:
                        snippet = text[:150]
                        news_items.append(("🏢", "IPO", snippet))
                # Business news
                elif ch == "kursiv_uz_ru":
                    for kw in ["экономик", "компани", "рынок", "инвестиц", "банк"]:
                        if kw.lower() in text.lower():
                            snippet = text[:150]
                            news_items.append(("📰", "Бизнес", snippet))
                            break

            if news_items:
                lines.append("**📰 Новости и аналитика:**")
                seen = set()
                for emoji, topic, snippet in news_items[:5]:
                    key = f"{topic}:{snippet[:50]}"
                    if key not in seen:
                        seen.add(key)
                        lines.append(f"  {emoji} **{topic}:** {snippet[:120]}...")
                lines.append("")

        # Market summary
        avg_change = sum(p.get("change_pct", 0) or 0 for p in prices if p.get("change_pct"))
        count_with_change = sum(1 for p in prices if p.get("change_pct"))
        avg = avg_change / count_with_change if count_with_change else 0
        lines.append(f"**📈 Рынок:** среднее изменение {avg:+.2f}% | "
                    f"{len(gainers)} grow / {len(losers)} los")

        return "\n".join(lines)


# ===== CLI =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    import sys

    client = UZSEEnhancedClient()

    if len(sys.argv) > 1 and sys.argv[1] == "prices":
        prices = client.fetch_all_prices()
        print(json.dumps(prices, indent=2, default=str, ensure_ascii=False))

    elif len(sys.argv) > 1 and sys.argv[1] == "ohlcv":
        ticker = sys.argv[2] if len(sys.argv) > 2 else "HMKB"
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        history = client.fetch_ohlcv_history(ticker, days=days)
        print(f"OHLCV for {ticker} ({len(history)} days):")
        for h in history[-10:]:
            print(f"  {h['date'][:10]}: O={h['open']} H={h['high']} L={h['low']} C={h['close']} V={h['volume']}")

    elif len(sys.argv) > 1 and sys.argv[1] == "snapshot":
        snap = client.full_snapshot(ohlcv_days=7)
        print(json.dumps({
            "count": snap["count"],
            "top_gainers": [{"ticker": g["ticker"], "change_pct": g["change_pct"]} for g in snap["top_gainers"][:5]],
            "top_losers": [{"ticker": l["ticker"], "change_pct": l["change_pct"]} for l in snap["top_losers"][:5]],
            "ohlcv_tickers": list(snap["ohlcv"].keys()),
            "fetched_at": snap["fetched_at"],
        }, indent=2, ensure_ascii=False))

    elif len(sys.argv) > 1 and sys.argv[1] == "report":
        prices = client.fetch_all_prices()
        analytics = UZSEAnalytics()
        cc = UZSEChannelCollector()

        # Get OHLCV for top movers
        history = {}
        for p in prices[:15]:
            try:
                h = client.fetch_ohlcv_history(p["ticker"], days=7)
                if h:
                    history[p["ticker"]] = h
                time.sleep(0.3)
            except Exception:
                pass

        # Fetch channel data
        channel_msgs = cc.fetch_all_channels(limit=3)
        logger.info("Fetched %d messages from %d channels", len(channel_msgs), len(cc.CHANNELS))

        trends = analytics.compute_trends(prices, history)
        report = analytics.generate_daily_report(prices, trends, channel_msgs)
        print(report)

    elif len(sys.argv) > 1 and sys.argv[1] == "channels":
        collector = UZSEChannelCollector()
        msgs = collector.fetch_all_channels(limit=3)
        print(json.dumps([{
            "channel": m["channel"],
            "date": m["date"][:19],
            "text": m["text"][:200],
        } for m in msgs], indent=2, ensure_ascii=False))

    else:
        print("Usage: python uzse_enhanced.py <prices|ohlcv|snapshot|report|channels>")