#!/usr/bin/env python3
"""HERMES — полный аудит системы и план автоматизации."""
import sys, os, json
sys.path.insert(0, os.path.expanduser("~/projects/stocks-uz"))
sys.path.insert(0, os.path.expanduser("~/projects/stocks-uz/src"))

# 1. Текущее состояние портфеля
print("=== PORTFOLIO STATE ===")
import urllib.request
try:
    r = urllib.request.urlopen("http://localhost:8003/api/portfolio", timeout=5)
    portfolio = json.loads(r.read())
    print(f"Positions: {len(portfolio['positions'])}")
    print(f"Total: {portfolio['total_value']:,.0f} UZS")
    print(f"P&L: {portfolio['total_pl']:+,.0f} UZS")
    bb = portfolio.get('barbell', {})
    print(f"Equity: {bb.get('equity_pct',0)}% | Bonds: {bb.get('bond_pct',0)}%")
except Exception as e:
    print(f"API error: {e}")

# 2. Текущие сигналы
print("\n=== SIGNALS ===")
try:
    r = urllib.request.urlopen("http://localhost:8003/api/signals", timeout=5)
    signals = json.loads(r.read())
    for group in ['sell', 'watch', 'buy', 'hold']:
        items = signals.get(group, [])
        if items:
            print(f"{group.upper()}: {len(items)}")
            for i in items[:3]:
                print(f"  {i['ticker']}: {i['verdict']} - {i['message'][:60]}")
except Exception as e:
    print(f"API error: {e}")

# 3. Каналы
print("\n=== CHANNEL DATA ===")
from src.db import DB
db = DB()
rows = db.conn.execute("SELECT channel, COUNT(*) FROM channel_messages GROUP BY channel ORDER BY COUNT(*) DESC").fetchall()
for r in rows:
    print(f"  @{r[0]}: {r[1]} msgs")

# 4. Цены (последние)
print("\n=== LATEST PRICES ===")
rows = db.conn.execute("SELECT ticker, price, day_change_pct FROM price_history WHERE id IN (SELECT MAX(id) FROM price_history GROUP BY ticker) ORDER BY day_change_pct DESC LIMIT 10").fetchall()
for r in rows:
    arrow = "GREEN" if r[2] and r[2] > 0 else "RED"
    print(f"  {r[0]}: {r[1]:,.2f} ({r[2]:+.2f}%)")