#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/vitaliyr/dev/my-project/stocks-us')

from src.db import DB
from src.market import fetch_quotes

db = DB()
tickers = [p['ticker'] for p in db.get_portfolio() if p['ticker'] not in ('SPCXX','BSP','SKHY','SNDK')]
quotes = fetch_quotes(tickers)
db.save_prices(quotes)

key = ['SPY','QQQ','NVDA','AAPL','MSFT','TSLA','AMD','INTC']
for t in key:
    if t in quotes:
        q = quotes[t]
        pct = q.get('day_change_pct', 0)
        e = '🟢' if pct >= 0 else '🔴'
        print(f"{e} {t}: ${q['price']:.2f} ({pct:+.2f}%)")

print('✅ Утренние цены обновлены')