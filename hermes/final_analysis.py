#!/usr/bin/env python3
"""Финальная аналитическая модель: CBSK vs ALKB vs IPTB"""
import sys
sys.path.insert(0, '/home/us/projects/stocks-uz')
sys.path.insert(0, '/home/us/projects/stocks-uz/src')
from src.uzse_enhanced import UZSEEnhancedClient
from src.db import DB

client = UZSEEnhancedClient()
db = DB()

# CBSK full OHLCV for support/resistance
h = client.fetch_ohlcv_history("CBSK", days=30)
print("=== CBSK: SUPPORT & RESISTANCE ===")
highs = [x["high"] for x in h]
lows = [x["low"] for x in h]
closes = [x["close"] for x in h]
print(f"Support (lowest 5d): {sum(sorted(lows[-5:])[:3])/3:.2f}")
print(f"Resistance (highest 5d): {sum(sorted(highs[-5:],reverse=True)[:3])/3:.2f}")
print(f"Current: {closes[-1]:.2f}")
print(f"30d low: {min(lows):.2f}")
print(f"30d high: {max(highs):.2f}")
print(f"May analyst entry zone: 2.50 - 2.70")
print(f"Current vs analyst zone: +{(closes[-1]/2.60-1)*100:.0f}% above")
print()

# Check if price ever touched 2.50-2.70 range recently
near_2_7 = [x for x in h if x["low"] <= 2.70]
print(f"Days where price touched <= 2.70 in last 30d: {len(near_2_7)}")
for x in near_2_7[-5:]:
    print(f"  {x['date'][:10]}: L={x['low']} H={x['high']} C={x['close']}")
print()

# What if we wait? CBSK range analysis
print("=== CBSK: WAIT vs BUY NOW ===")
print(f"Buy now at {closes[-1]:.2f}:")
print(f"  315k shares = ~1M UZS")
print(f"  Target 4.20 = +{(4.20/closes[-1]-1)*100:.0f}%")
print(f"Wait for 2.70:")
print(f"  370k shares = 999k UZS")
print(f"  Target 4.20 = +{(4.20/2.70-1)*100:.0f}%")
print(f"  Risk: price never drops back (bull market)")
print()

# How often does CBSK touch 2.70 area?
below_2_8 = len([x for x in h if x["low"] <= 2.80])
print(f"Days at/below 2.80 in 30d: {below_2_8}/{len(h)}")

# ALKB support zone
h = client.fetch_ohlcv_history("ALKB", days=30)
closes = [x["close"] for x in h]
print(f"\n=== ALKB: SUPPORT ZONE ===")
print(f"Current: {closes[-1]:.2f}")
print(f"Post-pump avg (last 2d): {(closes[-2]+closes[-1])/2:.2f}")
print(f"Pre-pump avg (before Aug 24): {sum(closes[:-3])/len(closes[:-3]):.2f}")
print(f"Entry at 0.88 vs current {closes[-1]:.2f}: {((0.88/closes[-1])-1)*100:.0f}% below")

# UZNF check - the hidden gem?
print(f"\n=== BONUS: UZNF CHECK ===")
h = client.fetch_ohlcv_history("UZNF", days=30)
if h:
    closes = [x["close"] for x in h]
    print(f"Current: {closes[-1]:.2f}")
    print(f"Range 30d: {min(closes):.2f} - {max(closes):.2f}")
    # UZNF is a fund - check its holdings
    print(f"Volume avg: {sum(x['volume'] for x in h)/len(h):,.0f}/d")
PYEOF