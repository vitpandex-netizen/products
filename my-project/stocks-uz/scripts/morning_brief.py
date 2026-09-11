#!/usr/bin/env python3
"""
Morning Brief — утренний бриф перед открытием UZSE (09:50 AM).
Формирует и отправляет сводку в Telegram с лидерами рынка, дивидендными новостями
и состоянием портфеля с указанием доходности в % и UZS.
"""
import sys
import os
import sqlite3
import requests
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / 'src'))

from dotenv import load_dotenv
load_dotenv(BASE / '.env')

try:
    from shared.vault import get as vault_get
except ImportError:
    try:
        from vault import get as vault_get
    except ImportError:
        def vault_get(k): return os.getenv(k, '')

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("morning-brief")

DB_PATH = BASE / "data" / "stocks-uz.db"
TASHKENT = timezone(timedelta(hours=5))

def get_bot_token():
    return vault_get('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN', '')

def get_chat_id():
    return vault_get('TELEGRAM_CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID', '-1004297012607')

def get_thread_id():
    return vault_get('TELEGRAM_THREAD_ID') or os.getenv('TELEGRAM_THREAD_ID', '576')

def send_telegram_digest(message):
    token = get_bot_token()
    chat_id = get_chat_id()
    thread_id = get_thread_id()

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден.")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if thread_id:
        payload["message_thread_id"] = int(thread_id)

    try:
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        logger.info("Утренний бриф успешно отправлен.")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки утреннего брифа в TG: {e}")
        return False

def generate_brief():
    if not DB_PATH.exists():
        logger.error("БД не найдена")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    now_tashkent = datetime.now(TASHKENT).strftime("%d.%m.%Y %H:%M")
    
    # 1. Позиции портфеля
    c.execute("""
        SELECT ticker, shares, avg_price
        FROM portfolio
    """)
    portfolio_rows = c.fetchall()
    
    portfolio_summary = []
    total_val = 0
    total_profit_uzs = 0
    
    for row in portfolio_rows:
        ticker = row['ticker']
        shares = row['shares']
        avg = row['avg_price']
        
        # Получаем последнюю цену
        c.execute("""
            SELECT price FROM price_history 
            WHERE ticker = ? ORDER BY id DESC LIMIT 1
        """, (ticker,))
        p_row = c.fetchone()
        last_price = p_row['price'] if p_row else avg
        
        cost = shares * avg
        curr_val = shares * last_price
        profit_uzs = curr_val - cost
        profit_pct = ((last_price - avg) / avg * 100) if avg > 0 else 0
        
        total_val += curr_val
        total_profit_uzs += profit_uzs
        
        sign = "+" if profit_uzs >= 0 else ""
        portfolio_summary.append(
            f"• <b>{ticker}</b>: {shares:.0f} шт @ {last_price:,.0f} UZS <i>({sign}{profit_pct:.1f}%, {sign}{profit_uzs:,.0f} UZS)</i>"
        )

    # 2. Дивидендные события
    c.execute("""
        SELECT ticker, amount_per_share, ex_date
        FROM corporate_actions
        WHERE action_type = 'dividend'
        ORDER BY id DESC LIMIT 3
    """)
    div_rows = c.fetchall()
    div_summary = []
    for d in div_rows:
        div_summary.append(f"• <b>{d['ticker']}</b>: {d['amount_per_share']} UZS / акция (отсечка: {d['ex_date']})")

    conn.close()

    msg = f"🌅 <b>Утренний Бриф UZSE | {now_tashkent}</b>\n"
    msg += f"<i>Подготовка к открытию торговой сессии (09:50 AM)</i>\n\n"
    
    msg += "💼 <b>Статус Портфеля Инвестора:</b>\n"
    if portfolio_summary:
        msg += "\n".join(portfolio_summary) + "\n"
        sign_tot = "+" if total_profit_uzs >= 0 else ""
        msg += f"<b>Итого оценка:</b> {total_val:,.0f} UZS <i>({sign_tot}{total_profit_uzs:,.0f} UZS)</i>\n\n"
    else:
        msg += "<i>Портфель пуст или не инициализирован</i>\n\n"

    msg += "💰 <b>Ближайшие дивидендные выплаты:</b>\n"
    if div_summary:
        msg += "\n".join(div_summary) + "\n\n"
    else:
        msg += "<i>Нет предстоящих реестров</i>\n\n"

    msg += "🎯 <b>План на день:</b>\n"
    msg += "• Мониторинг просадок по BIOK (целевая покупка: 14 000 – 14 200 UZS)\n"
    msg += "• Усреднение URTS при откате к 10 500 UZS\n"
    msg += "• Сканер аномальных объемов (Smart Money) активен\n"

    send_telegram_digest(msg)

if __name__ == "__main__":
    generate_brief()
