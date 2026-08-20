"""
DataCore Telegram Bot — только дайджесты по расписанию.

Запуск:
    python3 bot.py                     # Режим ожидания (ничего не делает)
    python3 bot.py --digest            # Отправить дайджест сейчас
    python3 bot.py --digest --topic 397 # Отправить в конкретный топик

Все проекты получают аналитику в реальном времени через DataCore API :8001.
Telegram — только 3 дайджеста в день (9:30, 14:00, 17:00 TST).
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("datacore-bot")

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-1004297012607")
API_URL = "http://core-api:8000"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Topics
TOPIC_MONITORING = 203
TOPIC_FINANALYTICS = 239
TOPIC_STOCKS_US = 577
TOPIC_DATACORE = 397
TOPIC_UZ_STOCKS = 576
TOPIC_US_STOCKS = 577


async def send_telegram(
    text: str,
    topic_id: Optional[int] = None,
    parse_mode: str = "HTML",
) -> bool:
    if not BOT_TOKEN:
        logger.warning("TELEGRAM_TOKEN not set, skipping")
        return False
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    if topic_id:
        payload["message_thread_id"] = topic_id
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{TELEGRAM_API}/sendMessage", json=payload)
            if resp.status_code != 200:
                logger.error("Telegram error: %s %s", resp.status_code, resp.text)
                return False
            return True
    except Exception as e:
        logger.error("Telegram error: %s", e)
        return False


async def send_digest(topic_id: int = TOPIC_FINANALYTICS):
    """Собрать и отправить дайджест."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            summary = await client.get(f"{API_URL}/api/v1/analytics/summary")
            if summary.status_code != 200:
                return
            data = summary.json()

            prices = await client.get(f"{API_URL}/api/v1/prices/?limit=8")
            prices_data = prices.json() if prices.status_code == 200 else []

            signals = await client.get(f"{API_URL}/api/v1/signals/?limit=5")
            signals_data = signals.json() if signals.status_code == 200 else []
    except Exception as e:
        logger.error("Digest API error: %s", e)
        return

    signals_24h = data.get("signals_24h", 0)
    trades_24h = data.get("trades_24h", 0)
    active_pm = data.get("active_prediction_markets", 0)
    collectors = data.get("collector_status", [])
    pnl = data.get("pnl_by_bot", [])

    # Prices
    price_lines = []
    seen = set()
    for p in prices_data:
        sym = p.get("symbol", "")
        if sym not in seen and sym:
            seen.add(sym)
            pr = p.get("price", 0)
            price_lines.append(f"  {sym}: ${pr:,.2f}" if pr else f"  {sym}: N/A")

    # Collector status
    coll_lines = []
    for c in collectors:
        s = "✅" if c.get("status") == "success" else "❌"
        coll_lines.append(f"{s} {c['name']}")

    # PnL
    pnl_lines = []
    for b in pnl:
        pnl_val = float(b.get("pnl", 0) or 0)
        arrow = "🟢" if pnl_val >= 0 else "🔴"
        pnl_lines.append(f"{arrow} {b['bot']}: ${pnl_val:+.2f} ({b['trades']} trades)")

    # Signals
    sig_lines = []
    for s in signals_data[:5]:
        dir_ = s.get("direction", "?")
        emoji = "🟢" if dir_ == "buy" else "🔴" if dir_ == "sell" else "⚪"
        st = float(s.get("strength", 0) or 0) * 100
        sig_lines.append(f"{emoji} {s.get('symbol','?')[:40]} | {st:.0f}% | {s.get('signal_type','?')}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    text = (
        f"📊 <b>DataCore Digest</b>  |  {now}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"<b>📈 Цены:</b>\n" + ("\n".join(price_lines) if price_lines else "  Нет данных") + "\n"
        f"\n"
        f"<b>🎯 Рынки:</b> {active_pm} активных\n"
        f"<b>🔔 Сигналов:</b> {signals_24h} за 24ч\n"
        f"<b>📈 Сделок:</b> {trades_24h} за 24ч\n"
        f"\n"
        f"<b>📡 Сборщики:</b>\n" + ("\n".join(coll_lines) if coll_lines else "  Нет данных") + "\n"
        f"\n"
        f"<b>💰 PnL:</b>\n" + ("\n".join(pnl_lines) if pnl_lines else "  Нет данных") + "\n"
        f"\n"
        f"<b>🔔 Последние сигналы:</b>\n" + ("\n".join(sig_lines) if sig_lines else "  Нет сигналов") + "\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Данные: DataCore API → :8001"
    )

    await send_telegram(text, topic_id=topic_id)
    logger.info("Digest sent to topic %s", topic_id)


async def poll_news():
    """Опрос новых новостных сигналов и отправка в топики."""
    try:
        import asyncpg

        conn = await asyncpg.connect(
            os.environ.get("DATABASE_URL", "postgresql://datacore:***@postgres:5432/datacore")
        )
        last_id = 0

        while True:
            rows = await conn.fetch("""
                SELECT id, symbol, reason, meta, ts
                FROM analytics.signals
                WHERE source = 'news' AND id > $1
                ORDER BY id ASC
                LIMIT 5
            """, last_id)

            for r in rows:
                company = r["symbol"]
                meta = json.loads(r["meta"]) if isinstance(r["meta"], str) else (r["meta"] or {})
                url = meta.get("url", "")
                title = meta.get("title", "")[:100]

                # Определяем топик по компании
                uz_companies = [
                    "UzAuto", "Uztelecom", "Hamroh", "NBU",
                    "National Bank", "Uzbekistan", "Uzstandard"
                ]
                is_uz = any(k.lower() in company.lower() for k in uz_companies)
                topic = TOPIC_UZ_STOCKS if is_uz else TOPIC_US_STOCKS

                text = (
                    f"📰 <b>{company}</b>\n"
                    f"{title}\n"
                    f"🔗 {url}"
                )
                await send_telegram(text, topic_id=topic)
                last_id = r["id"]

            await asyncio.sleep(30)
    except Exception as e:
        logger.error("News poll error: %s", e)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DataCore Bot")
    parser.add_argument("--digest", action="store_true", help="Send digest now")
    parser.add_argument("--topic", type=int, default=TOPIC_FINANALYTICS, help="Topic ID")
    parser.add_argument("--schedule", action="store_true", help="Run scheduler mode (3 digests/day)")
    args = parser.parse_args()

    if args.digest:
        asyncio.run(send_digest(topic_id=args.topic))
    elif args.schedule:
        async def scheduler():
            """Отправка дайджестов по расписанию + мониторинг новостей."""
            logger.info("Digest scheduler started (9:30, 14:00, 17:00 TST)")
            last_sent = {"9:30": None, "14:00": None, "17:00": None}
            while True:
                now = datetime.now(timezone.utc)
                # TST = UTC+5 → 4:30 UTC, 9:00 UTC, 12:00 UTC
                targets = [
                    (4, 30, "9:30", TOPIC_DATACORE),
                    (9, 0,  "14:00", TOPIC_DATACORE),
                    (12, 0, "17:00", TOPIC_DATACORE),
                ]
                for h, m, name, topic in targets:
                    if now.hour == h and now.minute == m and last_sent[name] != now.date():
                        logger.info("Sending %s digest to topic %s", name, topic)
                        await send_digest(topic_id=topic)
                        last_sent[name] = now.date()
                await asyncio.sleep(60)

        async def runner():
            await asyncio.gather(
                scheduler(),
                poll_news(),
                return_exceptions=True,
            )
        asyncio.run(runner())
    else:
        logger.info("DataCore Bot started (idle mode)")
        asyncio.get_event_loop().run_forever()