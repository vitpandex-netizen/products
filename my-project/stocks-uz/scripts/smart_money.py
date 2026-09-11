#!/usr/bin/env python3
"""
Smart Money Scanner — сканер аномальных объёмов на UZSE.
Анализирует таблицу trade_flow в БД stocks-uz.db и отправляет алерты
при обнаружении сделок > 20,000,000 UZS и > 5x от среднего чека тикера.
"""
import sys
import os
import sqlite3
import requests
import logging
from pathlib import Path
from datetime import datetime

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
logger = logging.getLogger("smart-money")

DB_PATH = BASE / "data" / "stocks-uz.db"

def get_bot_token():
    return vault_get('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN', '')

def get_chat_id():
    return vault_get('TELEGRAM_CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID', '-1004297012607')

def get_alert_thread_id():
    return vault_get('TELEGRAM_ALERT_THREAD_ID') or os.getenv('TELEGRAM_ALERT_THREAD_ID', '576')

def send_telegram_alert(message):
    token = get_bot_token()
    chat_id = get_chat_id()
    thread_id = get_alert_thread_id()

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
        logger.info("Telegram-алерт успешно отправлен.")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке в Telegram: {e}")
        return False

def analyze_trade_flow():
    if not DB_PATH.exists():
        logger.error(f"База данных не найдена по адресу: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    c.execute("""
        SELECT ticker, MAX(amount) as max_amount, COUNT(*) as trades_today
        FROM trade_flow 
        WHERE trade_date LIKE ? 
        GROUP BY ticker
    """, (f"{today}%",))
    
    todays_anomalies = []
    
    for row in c.fetchall():
        ticker = row['ticker']
        max_amt = row['max_amount']
        
        c.execute("""
            SELECT AVG(amount) as avg_amt
            FROM trade_flow
            WHERE ticker = ? AND trade_date < ?
        """, (ticker, today))
        
        hist_row = c.fetchone()
        hist_avg = hist_row['avg_amt'] if hist_row and hist_row['avg_amt'] else 0
        
        if hist_avg > 0 and max_amt > (hist_avg * 5) and max_amt > 20_000_000:
            todays_anomalies.append({
                "ticker": ticker,
                "amount": max_amt,
                "avg": hist_avg,
                "ratio": max_amt / hist_avg
            })
            
    conn.close()
    
    if todays_anomalies:
        msg = "🚨 <b>Smart Money Alert (Аномальные объемы UZSE)</b>\n\n"
        for a in todays_anomalies:
            amt_mln = a['amount'] / 1_000_000
            avg_mln = a['avg'] / 1_000_000
            msg += f"• <b>{a['ticker']}</b>: Крупная сделка на <b>{amt_mln:.1f} млн UZS</b> <i>(в {a['ratio']:.1f}x больше среднего чека {avg_mln:.1f} млн)</i>\n"
        
        logger.info(f"Обнаружено {len(todays_anomalies)} аномальных сделок.")
        send_telegram_alert(msg)
    else:
        logger.info("За сегодня аномальных объёмов не зафиксировано.")

if __name__ == "__main__":
    analyze_trade_flow()
