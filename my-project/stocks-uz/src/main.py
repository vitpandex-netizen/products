"""Stocks-UZ — точка входа. Запуск: --bot (поллинг), --scan, --report"""
import sys, os, logging
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE = Path(__file__).resolve().parent.parent
os.chdir(str(BASE))
sys.path.insert(0, str(BASE / 'src'))
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE.parent))

from dotenv import load_dotenv
load_dotenv(BASE / '.env')
from shared.net import force_ipv4
from shared.vault import get as vault_get
from src.db import DB
from src.market import screen_market, fetch_quotes, ALL_TICKERS
force_ipv4()

TASHKENT = timezone(timedelta(hours=5))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.StreamHandler()])
logger = logging.getLogger("stocks-uz")

def get_bot_token():
    return vault_get('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN', '')

def get_chat_id():
    return vault_get('TELEGRAM_CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID', '-1004297012607')

def get_thread_id():
    return vault_get('TELEGRAM_THREAD_ID') or os.getenv('TELEGRAM_THREAD_ID', '116')

def get_bot():
    from src.bot import StocksUZBot
    return StocksUZBot(get_bot_token(), get_chat_id(), get_thread_id())

def cmd_scan():
    logger.info("Scan started...")
    db = DB()
    bot = get_bot()
    quotes = fetch_quotes()
    db.save_prices(quotes)
    results = screen_market(min_score=40)
    if not results:
        bot.send_report("Skrinning yakunlandi. Hech narsa topilmadi.")
        return
    for r in results:
        price = r.get('price', 0) or 0
        score = r.get('score', 50)
        direction = 'buy' if score >= 55 else 'hold'
        target = round(price * 1.1, 2) if direction == 'buy' else None
        stop = round(price * 0.85, 2) if direction == 'buy' else None
        rationale = ', '.join(r.get('signal_detail', [])) or f"Score {score}/100"
        risk = 'low' if score >= 70 else 'medium'
        db.save_idea(r['ticker'], direction, price, target, stop, score, rationale, risk)
    top = '\n'.join(f"{r.get('signals','')} {r['ticker']}: {r.get('price',0):.2f} sum | {r.get('score',0)}/100" for r in results[:9])
    report = f"UZSE skrinning — {len(results)} kandidat\n\n{top}\n\nG'oyalar yaratildi: {len(results)}"
    bot.send_report(report)
    logger.info(f"Scan done: {len(results)} results")

def cmd_report():
    logger.info("Report...")
    db = DB()
    bot = get_bot()
    prices = db.get_all_latest_prices()
    lines = [f"Kundalik hisobot UZSE\n{datetime.now(TASHKENT).strftime('%d.%m.%Y %H:%M')}\n"]
    for t, p in sorted(prices.items()):
        lines.append(f"{'🟢' if p.get('day_change_pct',0)>=0 else '🔴'} {t}: {p['price']:.2f} sum ({p.get('day_change_pct',0):+.2f}%)")
    pending = db.get_pending_ideas()
    if pending: lines.append(f"\nKutayotgan g'oyalar: {len(pending)}")
    bot.send_report('\n'.join(lines))

def cmd_bot():
    logger.info("Bot starting...")
    bot = get_bot()
    bot.start()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py --bot | --scan | --report")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == '--bot': cmd_bot()
    elif cmd == '--scan': cmd_scan()
    elif cmd == '--report': cmd_report()
    else: print(f"Unknown: {cmd}")
