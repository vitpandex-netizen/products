#!/usr/bin/env python3
"""Stocks-US — точка входа. Запуск: --bot (поллинг), --scan, --report, --ideas"""
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
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("stocks-us")

def get_bot_token() -> str:
    return vault_get('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN', '')

def get_chat_id() -> str:
    return vault_get('TELEGRAM_CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID', '-1004297012607')

def get_thread_id() -> str | None:
    return vault_get('TELEGRAM_THREAD_ID') or os.getenv('TELEGRAM_THREAD_ID', '116')

def get_bot():
    from src.bot import StocksBot
    return StocksBot(get_bot_token(), get_chat_id(), get_thread_id())

def cmd_scan():
    logger.info("🔍 Scan started...")
    db = DB()
    bot = get_bot()
    results = screen_market(min_score=55)
    if not results:
        bot.send_report("🔍 Скрининг завершён. Ничего не найдено (все ниже порога).")
        logger.info("Scan done: 0 results")
        return
    for r in results:
        db.save_fundamentals(r['ticker'], r)
    ideas_generated = 0
    for r in results[:5]:
        score = r.get('score', 50)
        price = r.get('price', 0)
        if price <= 0: continue
        direction = 'buy' if score >= 60 else 'sell' if score <= 35 else 'hold'
        target = round(price * 1.15, 2) if direction == 'buy' else round(price * 0.85, 2)
        stop = round(price * 0.9, 2) if direction == 'buy' else round(price * 1.1, 2)
        rationale = ', '.join(r.get('signal_detail', [])) if r.get('signal_detail') else f"Счёт {score}/100"
        risk = 'low' if score >= 70 else 'medium' if score >= 45 else 'high'
        idea_id = db.save_idea(r['ticker'], direction, price, target, stop, score, rationale, risk)
        bot.send_idea_notification(r['ticker'], direction, price, target, stop, score, rationale, risk, idea_id)
        ideas_generated += 1
    top = '\n'.join(f"{r.get('signals', '➖')} <b>{r['ticker']}</b> ${r.get('price', 0):.2f} | {r.get('score', 0)}/100" for r in results[:10])
    report = f"🔍 <b>Скрининг рынка — {len(results)} кандидатов</b>\n📅 {datetime.now(TASHKENT).strftime('%d.%m.%Y %H:%M')}\n\n<b>Топ-10:</b>\n{top}\n\n💡 Сгенерировано идей: {ideas_generated} (отправлены на апрув)"
    bot.send_report(report)
    logger.info(f"Scan done: {len(results)} results, {ideas_generated} ideas")

def cmd_report():
    logger.info("📊 Report started...")
    db = DB()
    bot = get_bot()
    prices = db.get_all_latest_prices()
    summary = db.get_portfolio_summary()
    lines = [f"📊 <b>Ежедневный отчёт stocks-us</b>\n📅 {datetime.now(TASHKENT).strftime('%d.%m.%Y %H:%M')}\n"]
    key_tickers = ['SPY', 'QQQ', 'NVDA', 'AAPL', 'TSLA', 'MSTR', 'GLD']
    lines.append("<b>Ключевые цены:</b>")
    for t in key_tickers:
        if t in prices:
            p = prices[t]
            lines.append(f"  {'🟢' if p.get('day_change',0)>=0 else '🔴'} {t}: ${p['price']:.2f} ({p.get('day_change',0):+.2f}%)")
    if summary['positions']:
        lines.append(f"\n<b>Портфель:</b> ${summary['total_value']:,.2f} | P&L: ${summary['total_pl']:+,.2f} ({summary['total_pl_pct']:+.2f}%)")
        for p in summary['positions'][:5]:
            lines.append(f"  {'🟢' if p['pl']>=0 else '🔴'} {p['ticker']}: ${p['value']:.2f} ({p['pl_pct']:+.2f}%)")
    pending = db.get_pending_ideas()
    if pending: lines.append(f"\n💡 <b>Ожидает апрува:</b> {len(pending)} идей")
    bot.send_report('\n'.join(lines))
    logger.info("Report done")

def cmd_bot():
    logger.info("🤖 Stocks-US bot starting polling mode...")
    from src.bot import StocksBot
    bot = StocksBot(get_bot_token(), get_chat_id(), get_thread_id())
    bot.start()

def cmd_add_portfolio(ticker: str, shares: float, price: float):
    db = DB()
    db.add_to_portfolio(ticker, shares, price)
    get_bot().send_report(f"📊 Добавлено: {ticker} {shares} шт × ${price:.2f}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python main.py --bot | --scan | --report | --portfolio | --ideas | --add TICKER SHARES PRICE")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == '--bot': cmd_bot()
    elif cmd == '--scan': cmd_scan()
    elif cmd == '--report': cmd_report()
    elif cmd == '--portfolio':
        from analytics import send_report
        send_report()
    elif cmd == '--add' and len(sys.argv) >= 5: cmd_add_portfolio(sys.argv[2].upper(), float(sys.argv[3]), float(sys.argv[4]))
    else: print(f"Неизвестная команда: {cmd}")
