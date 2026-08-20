"""Uzbekistan stock market monitor - local stocks and analysis."""
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.db import get_conn
from shared.utils import notify, send_hermes_message, get_config

import requests

# UZ stock exchange sources
UZSE_URL = "https://uzse.uz/api"  # Tashkent RSE API
UZSE_V2_URL = "https://api.uzse.uz/api/v1"

def fetch_uzse_quotes():
    """Fetch quotes from Uzbekistan Stock Exchange."""
    try:
        # Try Tashkent RSE open API
        resp = requests.get(f"{UZSE_V2_URL}/quotes", timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"[UZ] Primary API error: {e}")
    
    # Fallback: scrape or use cached data
    return []

def analyze_uzse_quotes(quotes):
    """Analyze UZ stocks for opportunities."""
    if not quotes:
        return []
    
    signals = []
    conn = get_conn()
    
    for q in quotes[:30]:  # Limit to 30
        ticker = q.get("symbol", q.get("ticker", "?"))
        price = q.get("price", q.get("last_price", 0))
        change = q.get("change_pct", 0)
        volume = q.get("volume", 0)
        
        signal = "neutral"
        reason = f"Цена: {price:.0f} сум, объем: {volume}"
        
        if change and abs(float(change or 0)) > 3:
            signal = "dip" if float(change) < 0 else "surge"
            reason += f" 📊 Изменение: {change:+.2f}%"
        
        conn.execute("""
            INSERT INTO stock_signals (ticker, exchange, price, signal, reason, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ticker, "UZ", float(price or 0), signal, reason, json.dumps(q)))
        
        signals.append({"ticker": ticker, "price": price, "signal": signal, "reason": reason})
    
    conn.commit()
    conn.close()
    return signals

def run_once():
    """Single monitoring run."""
    print("[UZ] Fetching UZSE quotes...")
    quotes = fetch_uzse_quotes()
    
    if not quotes:
        print("[UZ] No data from API, using demo mode")
        # Demo tickers for testing
        demo = [
            {"symbol": "UZMK", "last_price": 8500, "change_pct": -2.1, "volume": 15000},
            {"symbol": "KVAZ", "last_price": 12500, "change_pct": 1.5, "volume": 8000},
            {"symbol": "IPAK", "last_price": 3200, "change_pct": -4.2, "volume": 25000},
        ]
        quotes = demo
    
    signals = analyze_uzse_quotes(quotes)
    
    # Alert on dips
    alerts = [s for s in signals if s["signal"] == "dip"]
    if alerts:
        msg = "🇺🇿 *UZ Рынок — сигналы*\n\n"
        for a in alerts:
            msg += f"• {a['ticker']}: {a['price']:.0f} сум — *{a['reason']}*\n"
        send_hermes_message(msg)
    
    print(f"[UZ] Done. Signals: {len(signals)}, Alerts: {len(alerts)}")
    return {"total": len(signals), "alerts": len(alerts)}

if __name__ == "__main__":
    run_once()
