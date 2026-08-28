#!/usr/bin/env python3
"""Полный анализ трёх кандидатов для Claude + BGT Bot"""
import sys, json
sys.path.insert(0, '/home/us/projects/stocks-uz')
sys.path.insert(0, '/home/us/projects/stocks-uz/src')
from src.uzse_enhanced import UZSEEnhancedClient
from src.db import DB

client = UZSEEnhancedClient()
db = DB()

# 1. LIQUIDITY ANALYSIS
print("=== LIQUIDITY: CBSK ===")
h = client.fetch_ohlcv_history("CBSK", days=30)
v = [x["volume"] for x in h]
print(f"Volume avg: {sum(v)/len(v):,.0f}/d | range: {min(v):,} - {max(v):,}")
print(f"Last 5d avg: {sum(v[-5:])/5:,.0f}")
target = 315457
pct = target / (sum(v)/len(v)) * 100
print(f"315k shares = {pct:.1f}% of daily avg {'SAFE' if pct < 10 else 'CAUTION'}")
print(f"Latest close: {h[-1]['close']} | Range 30d: {min(x['low'] for x in h)}-{max(x['high'] for x in h)}")
print()

print("=== LIQUIDITY: ALKB ===")
h = client.fetch_ohlcv_history("ALKB", days=30)
v = [x["volume"] for x in h]
print(f"Volume avg: {sum(v)/len(v):,.0f}/d")
print(f"Aug 24 spike: {v[-3] if len(v)>=3 else 'N/A'} (vs avg {sum(v[:-3])/(len(v)-3):,.0f})")
p = v[-3] / (sum(v[:-3])/max(len(v)-3,1)) if len(v)>3 else 0
print(f"Spike ratio: x{p:.1f} {'PUMP' if p>3 else 'NORMAL'}")
print(f"Post-spike avg (last 2d): {sum(v[-2:])/2:,.0f}")
print()

print("=== LIQUIDITY: IPTB ===")
h = client.fetch_ohlcv_history("IPTB", days=30)
v = [x["volume"] for x in h]
prices = [x["close"] for x in h]
print(f"Volume avg: {sum(v)/len(v):,.0f}/d")
print(f"Price range 30d: {min(prices):.2f} - {max(prices):.2f}")
print(f"Price last 3 weeks: {prices[-1]:.2f} vs {prices[-21]:.2f} (flat)")
print(f"Volume spike Aug 6-7: {sorted(v)[-2]:,} + {sorted(v)[-1]:,} vs avg {sum(v)/len(v):,.0f}")
print()

# 2. TG MENTIONS
print("=== TG: CBSK / Chilonzor ===")
rows = db.conn.execute("SELECT channel, message_text, fetched_at FROM channel_messages WHERE (message_text LIKE '%CBSK%' OR message_text LIKE '%Chilonzor%') ORDER BY fetched_at DESC LIMIT 5").fetchall()
for r in rows:
    print(f"@{r[0]}: {r[1][:200]}")

print("\n=== TG: ALKB / Алока ===")
rows = db.conn.execute("SELECT channel, message_text, fetched_at FROM channel_messages WHERE (message_text LIKE '%ALKB%' OR message_text LIKE '%Алока%') ORDER BY fetched_at DESC LIMIT 5").fetchall()
for r in rows:
    print(f"@{r[0]}: {r[1][:200]}")

print("\n=== TG: IPTB / Ipoteka / Ипотека ===")
rows = db.conn.execute("SELECT channel, message_text, fetched_at FROM channel_messages WHERE (message_text LIKE '%IPTB%' OR message_text LIKE '%Ipoteka%' OR message_text LIKE '%Ипотека%') ORDER BY fetched_at DESC LIMIT 5").fetchall()
for r in rows:
    print(f"@{r[0]}: {r[1][:200]}")

print("\n=== LATEST @fond_birja_signal ===")
rows = db.conn.execute("SELECT message_text, fetched_at FROM channel_messages WHERE channel='fond_birja_signal' ORDER BY fetched_at DESC LIMIT 15").fetchall()
for r in rows:
    print(f"[{r[1][:19]}] {r[0][:150]}")