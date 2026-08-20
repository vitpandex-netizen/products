#!/usr/bin/env python3
"""
📈 UZ Market Monitor — мониторинг акций UZSE
Собирает данные с uzse.uz/trade_results/ и отправляет в Telegram
"""
import sys, os, json, logging, subprocess, re
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'my-project'))

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('UZMonitor')

# === Configuration ===
UZSE_URL = "https://uzse.uz/trade_results/"
TELEGRAM_BOT_TOKEN = "8938976950:AAF2hv0Tj7pd0vQqcc0S5VqKqGYNhQ5vLTM"
TELEGRAM_CHAT_ID = "-1004297012607"
TELEGRAM_THREAD_ID = "80"  # stocks-uz topic

# Top 10 UZSE tickers to monitor
TICKERS = {
    "HMKB": "Хамкорбанк",
    "UZMK": "Узметкомбинат",
    "KVTS": "Кварц",
    "UZMB": "Узбекская республиканская биржа",
    "UZMD": "Алмалыкский ГМК",
    "UZOB": "Узнацбанк",
    "UZPS": "Узпромстройбанк",
    "UZSB": "Узсаноаткурилишбанк",
    "UZTS": "Тошкент метрополитени",
    "UZYK": "Ер-Энерго",
}

def fetch_uzse_prices():
    """Fetch current prices from UZSE"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        resp = requests.get(UZSE_URL, headers=headers, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"UZSE returned {resp.status_code}")
            return []
        
        soup = BeautifulSoup(resp.text, 'lxml')
        items = soup.select('.main-ticker-item')
        prices = []
        
        for item in items[:20]:  # Top 20
            try:
                name_el = item.select_one('.ticker-name')
                price_el = item.select_one('.price-value')
                change_el = item.select_one('.change-value')
                
                name = name_el.text.strip() if name_el else ''
                price = price_el.text.strip() if price_el else ''
                change = change_el.text.strip() if change_el else ''
                
                if name and price:
                    prices.append({
                        'name': name,
                        'price': price,
                        'change': change,
                        'time': datetime.now().isoformat(),
                    })
            except:
                continue
        
        return prices
    except Exception as e:
        logger.error(f"UZSE fetch failed: {e}")
        return []

def send_telegram(msg):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown",
            "message_thread_id": TELEGRAM_THREAD_ID,
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.warning(f"Telegram send failed: {e}")

def main():
    logger.info("UZ Market Monitor started")
    prices = fetch_uzse_prices()
    
    if not prices:
        logger.warning("No prices fetched")
        send_telegram("⚠️ UZSE: не удалось получить данные")
        return
    
    # Format message
    lines = ["📈 *UZSE Market — Top 10*", ""]
    for i, p in enumerate(prices[:10], 1):
        name = p['name'][:30]
        price = p['price']
        change = p.get('change', '')
        arrow = "🟢" if '+' in change else "🔴" if '-' in change else "⚪"
        lines.append(f"{i}. {arrow} *{name}*")
        lines.append(f"   {price} | {change}")
    
    lines.append(f"\n🕐 {datetime.now().strftime('%H:%M')}")
    msg = "\n".join(lines)
    
    send_telegram(msg)
    logger.info(f"Sent {len(prices)} prices to Telegram")

if __name__ == '__main__':
    main()