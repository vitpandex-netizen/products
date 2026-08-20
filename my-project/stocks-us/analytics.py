#!/usr/bin/env python3
"""Аналитика портфеля US Stocks — еженедельные рекомендации."""
import sys, os, logging
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / 'src'))
os.chdir(str(BASE))

from dotenv import load_dotenv
load_dotenv(BASE / '.env')
from src.db import DB
from src.market import fetch_quotes, screen_market

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("analytics")
TASHKENT = timezone(timedelta(hours=5))

def analyze_portfolio():
    """Полный анализ портфеля: текущие цены, P&L, рекомендации."""
    db = DB()

    # 1. Получаем портфель
    portfolio = db.get_portfolio()
    logger.info(f"📊 Позиций в портфеле: {len(portfolio)}")

    # 2. Фетчим текущие цены для всех тикеров портфеля
    tickers = [p['ticker'] for p in portfolio]
    # Фильтруем только стандартные тикеры (не SpaceX)
    valid_tickers = [t for t in tickers if t not in ('SPCXX', 'BSP', 'SKHY', 'SNDK')]
    logger.info(f"🔍 Фетчим цены для {len(valid_tickers)} тикеров...")
    quotes = fetch_quotes(valid_tickers)
    db.save_prices(quotes)
    logger.info(f"✅ Получено цен: {len(quotes)}")

    # 3. Получаем сводку портфеля
    summary = db.get_portfolio_summary()
    positions = sorted(summary['positions'], key=lambda x: x['value'], reverse=True)

    # 4. Формируем аналитику
    now = datetime.now(TASHKENT)
    lines = []
    lines.append(f"📈 <b>Аналитика портфеля US Stocks</b>")
    lines.append(f"📅 {now.strftime('%d.%m.%Y %H:%M')} Tashkent")
    lines.append(f"")
    lines.append(f"💰 <b>Общая стоимость:</b> ${summary['total_value']:,.2f}")
    lines.append(f"📊 <b>P&L:</b> ${summary['total_pl']:+,.2f} ({summary['total_pl_pct']:+.2f}%)")
    lines.append(f"")

    # Топ-10 позиций
    lines.append(f"<b>Крупнейшие позиции:</b>")
    for p in positions[:10]:
        emoji = '🟢' if p['pl'] >= 0 else '🔴'
        pct = p['pl_pct']
        lines.append(f"  {emoji} <b>{p['ticker']}</b> ${p['value']:.2f} ({p['pl_pct']:+.2f}%) — {p['shares']:.4f} шт")
    lines.append(f"")

    # Рекомендации
    lines.append(f"<b>💡 Рекомендации:</b>")

    for p in positions:
        ticker = p['ticker']
        pl_pct = p['pl_pct']
        stop = p['stop_loss_pct']

        # Сигналы
        if pl_pct <= -15 and stop and stop >= 10:
            lines.append(f"  ⚠️ <b>{ticker}</b>: просадка {pl_pct:.1f}% — рассмотри стоп-лосс")
        elif pl_pct >= 15:
            lines.append(f"  🎯 <b>{ticker}</b>: рост {pl_pct:.1f}% — возможно зафиксировать часть")
        elif pl_pct <= -5 and pl_pct > -15:
            lines.append(f"  👀 <b>{ticker}</b>: просадка {pl_pct:.1f}% — усреднение?")
        elif pl_pct >= 5 and pl_pct < 15:
            lines.append(f"  📈 <b>{ticker}</b>: рост {pl_pct:.1f}% — держим")

    # Распределение по секторам
    lines.append(f"")
    lines.append(f"<b>🏭 Распределение:</b>")
    sectors = {}
    for p in positions:
        v = p['value']
        if v > 10:
            t = p['ticker']
            if t in ('NVDA','AMD','AVGO','TSM','INTC','QCOM','MRVL'):
                sec = 'Полупроводники'
            elif t in ('AAPL','MSFT','ORCL','GOOGL'):
                sec = 'Технологии'
            elif t in ('TSLA','NFLX','BSP','SPCXX'):
                sec = 'Рост/Инновации'
            elif t in ('JPM','BAC','GS'):
                sec = 'Финансы'
            elif t in ('XOM','CVX','XLE','XOP'):
                sec = 'Энергетика'
            elif t in ('MCD','PEP','KO','PG'):
                sec = 'Потребление'
            elif t in ('SLV','PALL','PPLT','COPX','URA'):
                sec = 'Металлы/Сырьё'
            elif t in ('SPY','TQQQ'):
                sec = 'Индексы'
            else:
                sec = 'Другое'
            sectors[sec] = sectors.get(sec, 0) + v

    for sec, val in sorted(sectors.items(), key=lambda x: -x[1]):
        pct = (val / summary['total_value']) * 100 if summary['total_value'] else 0
        lines.append(f"  • {sec}: ${val:.0f} ({pct:.0f}%)")

    lines.append(f"")
    lines.append(f"🔄 Данные: Yahoo Finance | Следующий отчёт: завтра")

    report = '\n'.join(lines)
    logger.info(f"\n{report}")
    return report, summary

def send_report():
    """Отправить отчёт в Telegram."""
    report, summary = analyze_portfolio()

    # Если есть бот — отправляем
    try:
        from src.main import get_bot
        bot = get_bot()
        # Отправляем в топик stocks-us (116)
        import requests
        token = bot.token
        chat_id = bot.chat_id
        thread_id = bot.thread_id
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'message_thread_id': thread_id,
            'text': report,
            'parse_mode': 'HTML'
        }
        r = requests.post(url, json=payload, timeout=10)
        logger.info(f"Telegram: {r.status_code}")
    except Exception as e:
        logger.error(f"Telegram error: {e}")

    return summary

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--send':
        send_report()
    else:
        analyze_portfolio()