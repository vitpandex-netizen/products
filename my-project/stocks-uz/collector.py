#!/usr/bin/env python3
"""
UZSE Collector — запускается по cron на US Server.
Режимы:
  collect     — сбор цен + проверка алертов (каждый час)
  channels   — сбор сообщений из TG-каналов в БД (каждые 3ч)
  report     — генерация отчёта из БД + отправка (18:00)
  full       — collect + report
  alert      — проверить и отправить неотправленные алерты
"""
import sys, os, json, logging, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / 'src'))
sys.path.insert(0, str(BASE.parent))

from dotenv import load_dotenv
load_dotenv(BASE / '.env')

from src.uzse_enhanced import UZSEEnhancedClient, UZSEChannelCollector, UZSEAnalytics
from src.db import DB
from shared.net import force_ipv4
from shared.vault import get as vault_get

TASHKENT = timezone(timedelta(hours=5))
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("uzse-collector")

force_ipv4()


def get_bot_token():
    return vault_get('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN', '')


def get_chat_id():
    return vault_get('TELEGRAM_CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID', '-1004297012607')


def get_thread_id():
    return vault_get('TELEGRAM_THREAD_ID') or os.getenv('TELEGRAM_THREAD_ID', '576')


def get_alert_thread_id():
    return vault_get('TELEGRAM_ALERT_THREAD_ID') or os.getenv('TELEGRAM_ALERT_THREAD_ID', '576')


def send_telegram(text, parse_mode='Markdown', thread_id=None):
    """Отправить сообщение в Telegram."""
    token = get_bot_token()
    chat_id = get_chat_id()
    thread_id = thread_id or get_thread_id()
    if not token:
        logger.error("No Telegram token")
        return False

    import requests
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode,
        'disable_web_page_preview': True,
    }
    if thread_id:
        payload['message_thread_id'] = int(thread_id)

    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            logger.info("Telegram sent OK")
            return True
        else:
            logger.error("Telegram error: %s %s", r.status_code, r.text[:200])
            return False
    except Exception as e:
        logger.error("Telegram send failed: %s", e)
        return False


def collect_and_save():
    """Собрать цены и сохранить в БД. Вернуть цены для проверки алертов."""
    client = UZSEEnhancedClient()
    db = DB()

    prices = client.fetch_all_prices()
    logger.info("Fetched %d prices", len(prices))

    now = datetime.now(TASHKENT).isoformat()
    for p in prices:
        db.conn.execute(
            "INSERT INTO price_history (ticker, price, closing_price, day_change_pct, fetched_at) VALUES (?,?,?,?,?)",
            (p['ticker'], p.get('last_trade_price'), p.get('closing_price'), p.get('change_pct'), now)
        )
    db.conn.commit()

    for p in prices:
        db.conn.execute(
            "INSERT OR REPLACE INTO fundamentals (ticker, price, closing_price, updated_at) VALUES (?,?,?,?)",
            (p['ticker'], p.get('last_trade_price') or p.get('closing_price'), p.get('closing_price'), now)
        )
    db.conn.commit()

    logger.info("Saved %d prices to DB", len(prices))
    return prices


def check_and_send_alerts(prices):
    """Проверить цены на сильные движения, сохранить и отправить алерты."""
    db = DB()
    alerts_sent = 0

    for p in prices:
        change_pct = p.get('change_pct')
        if change_pct is None or abs(change_pct) < 10:
            continue

        ticker = p['ticker']
        price = p.get('last_trade_price') or p.get('closing_price') or 0
        em = "🟢" if change_pct > 0 else "🔴"
        direction = "рост" if change_pct > 0 else "падение"
        msg = f"{em} **{ticker}**: {direction} {change_pct:+.2f}% (цена: {price:,.2f} сум)"

        # Сохраняем в БД
        db.save_alert(ticker, 'big_move', price, change_pct, msg)

        # Отправляем сразу (для сильных движений)
        alert_text = (
            f"⚡ **UZSE Alert**\n"
            f"{em} **{ticker}** {direction} на **{abs(change_pct):.1f}%**\n"
            f"💰 Цена: {price:,.2f} сум\n"
            f"📅 {datetime.now(TASHKENT).strftime('%d.%m.%Y %H:%M')}"
        )
        if send_telegram(alert_text, thread_id=get_alert_thread_id()):
            alerts_sent += 1
            logger.info("Alert sent for %s: %.2f%%", ticker, change_pct)

    # Отправить накопившиеся алерты (если не отправились по одному)
    unsent = db.get_unsent_alerts()
    if unsent and alerts_sent == 0:
        lines = ["⚡ **UZSE Market Alert**", f"Сильные движения за последний час:\n"]
        for a in unsent[:10]:
            lines.append(f"  {a['message']}")
        if send_telegram('\n'.join(lines), thread_id=get_alert_thread_id()):
            for a in unsent:
                db.mark_alert_sent(a['id'])

    logger.info("Alerts checked: %d big movers, %d sent", 
                sum(1 for p in prices if abs(p.get('change_pct', 0) or 0) >= 10), alerts_sent)


def collect_channels():
    """Собрать сообщения из TG-каналов и сохранить в БД."""
    cc = UZSEChannelCollector()
    db = DB()
    total = 0

    for ch in cc.CHANNELS:
        try:
            msgs = cc.fetch_channel(ch, limit=5)
            for m in msgs:
                parsed = cc.parse_signal_message(m['text']) if ch == 'fond_birja_signal' else None
                db.save_channel_message(ch, m['text'], m['date'][:19], parsed)
                total += 1
            time.sleep(1.5)  # Rate limit
        except Exception as e:
            logger.warning("Channel %s error: %s", ch, e)

    logger.info("Collected %d messages from %d channels", total, len(cc.CHANNELS))
    return total


def generate_and_send_report(prices=None):
    """Сгенерировать отчёт из данных в БД + каналы и отправить."""
    client = UZSEEnhancedClient()
    db = DB()
    analytics = UZSEAnalytics()

    if prices is None:
        prices = client.fetch_all_prices()

    # OHLCV для топ-15
    history = {}
    for p in prices[:15]:
        try:
            h = client.fetch_ohlcv_history(p['ticker'], days=7)
            if h:
                history[p['ticker']] = h
            time.sleep(0.3)
        except Exception:
            pass

    # Берём последние сообщения из каналов из БД
    channel_msgs = db.get_latest_channel_msgs_for_report(
        channels=UZSEChannelCollector.CHANNELS, per_channel=3
    )
    logger.info("Loaded %d channel messages from DB for report", len(channel_msgs))

    trends = analytics.compute_trends(prices, history)
    report = analytics.generate_daily_report(prices, trends, channel_msgs)

    success = send_telegram(report)
    logger.info("Report sent: %s", success)
    return report


def cmd_collect():
    """Сбор цен + проверка алертов."""
    prices = collect_and_save()
    check_and_send_alerts(prices)
    logger.info("Collect + alerts done")


def cmd_report():
    """Отчёт из БД."""
    generate_and_send_report()
    logger.info("Report done")


def cmd_full():
    """Полный цикл."""
    prices = collect_and_save()
    check_and_send_alerts(prices)
    generate_and_send_report(prices)
    logger.info("Full cycle done")


def cmd_channels():
    """Сбор каналов в БД."""
    total = collect_channels()
    print(f"Collected {total} messages")
    return total


def cmd_alert():
    """Проверить и отправить неотправленные алерты."""
    db = DB()
    unsent = db.get_unsent_alerts()
    if not unsent:
        print("No unsent alerts")
        return
    lines = ["⚡ **UZSE Market Alert**\n"]
    for a in unsent[:10]:
        lines.append(f"  {a['message']}")
    text = '\n'.join(lines)
    if send_telegram(text, thread_id=get_alert_thread_id()):
        for a in unsent:
            db.mark_alert_sent(a['id'])
        print(f"Sent {len(unsent)} alerts")
    else:
        print("Failed to send alerts")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python collector.py <collect|report|full|channels|alert>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'collect':
        cmd_collect()
    elif cmd == 'report':
        cmd_report()
    elif cmd == 'full':
        cmd_full()
    elif cmd == 'channels':
        cmd_channels()
    elif cmd == 'alert':
        cmd_alert()
    else:
        print(f"Unknown: {cmd}")
        sys.exit(1)