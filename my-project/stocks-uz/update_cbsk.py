"""Обновить трекер CBSK после размещения ордера 3.12"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.tracker import init_trades, add_limit_order, add_watch
from src.db import DB

init_trades()
db = DB()

db.conn.execute("DELETE FROM trades WHERE ticker='CBSK'")
db.conn.execute("DELETE FROM portfolio_watch WHERE ticker='CBSK'")
db.conn.commit()

tid = add_limit_order("CBSK", 150000, 3.12, 2.70, 4.20,
    "Фактический ордер. Лимитка 3.12. Стоп 2.70. Таргет 4.20.")
wid = add_watch("CBSK", 150000, 3.12, 4.20, 2.70,
    "Таргет KD 4.20. Стоп 2.70. Вход 3.12.")

price = 3.12
total = price * 150000
commission = total * 0.03
upside = (4.20 / price - 1) * 100

print(f"=== CBSK ORDER UPDATED ===")
print(f"Price: {price:.2f}")
print(f"Shares: 150,000")
print(f"Total: {total:,.0f} UZS")
print(f"Commission: {commission:,.0f} UZS")
print(f"Target: 4.20 (+{upside:.1f}%)")
print(f"Stop: 2.70")
print(f"Remaining: {1000000 - total - commission:,.0f} UZS")
print(f"Trade ID: {tid}, Watch ID: {wid}")