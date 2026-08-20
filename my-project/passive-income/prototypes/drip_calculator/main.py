#!/usr/bin/env python3
"""UZSE Dividend Reinvestment Plan (DRIP) Calculator."""
import os, sys, json, logging, time
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from telegram import Telegram

logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))

UZSE_STOCKS = {
    "QZZ": {"name": "Qishloq Qurilish Bank", "sector": "banking", "div_yield": 0.12, "price": 1250, "frequency": "annual"},
    "UZMK": {"name": "Uzmetkombinat", "sector": "metallurgy", "div_yield": 0.08, "price": 8500, "frequency": "annual"},
    "HMKB": {"name": "Hamkorbank", "sector": "banking", "div_yield": 0.10, "price": 110, "frequency": "annual"},
    "IPKY": {"name": "Ipak Yoli Bank", "sector": "banking", "div_yield": 0.09, "price": 45, "frequency": "annual"},
    "TRNB": {"name": "Trastbank", "sector": "banking", "div_yield": 0.11, "price": 65, "frequency": "annual"},
}

def calculate_drip(investment_usd=1000, years=5, reinvest=True):
    usd_to_uzs = 12700
    investment = investment_usd * usd_to_uzs
    results = []
    for ticker, info in UZSE_STOCKS.items():
        shares = int(investment / info["price"])
        if reinvest:
            total = investment
            for y in range(years):
                total += total * info["div_yield"]
            final_value = total
            total_div = final_value - investment
        else:
            annual_div = shares * info["price"] * info["div_yield"]
            total_div = annual_div * years
            final_value = investment + total_div
        roi = ((final_value - investment) / investment) * 100
        results.append({"ticker": ticker, "name": info["name"], "shares": shares,
                        "annual_div_usd": round((shares * info["price"] * info["div_yield"]) / usd_to_uzs, 2),
                        "total_div_usd": round(total_div / usd_to_uzs, 2),
                        "final_value_usd": round(final_value / usd_to_uzs, 2), "roi": round(roi, 1)})
    return sorted(results, key=lambda x: x["total_div_usd"], reverse=True)

def format_report(results, investment_usd, years):
    lines = [f"<b>UZSE Dividend Reinvestment Plan</b>",
             f"{datetime.now(TASHKENT).strftime('%d.%m.%Y %H:%M')}",
             f"Investment: ${investment_usd} | Term: {years} years",
             f"1 USD = 12,700 UZS", chr(10)]
    for r in results:
        lines.append(f"<b>{r['ticker']}</b> - {r['name']}")
        lines.append(f"  Shares: {r['shares']} | Div/yr: ${r['annual_div_usd']}")
        lines.append(f"  Total div: ${r['total_div_usd']} | Final: ${r['final_value_usd']} | ROI: {r['roi']}%")
    total_div = sum(r["total_div_usd"] for r in results)
    total_final = sum(r["final_value_usd"] for r in results)
    avg_roi = round(sum(r["roi"] for r in results) / len(results), 1)
    lines.append(chr(10) + f"<b>Portfolio total:</b> Div: ${round(total_div,2)} | Value: ${round(total_final,2)} | Avg ROI: {avg_roi}%")
    return chr(10).join(lines)

if __name__ == "__main__":
    for inv in [500, 1000, 5000]:
        results = calculate_drip(inv, years=5, reinvest=True)
        print(format_report(results, inv, 5))
        print(chr(10) + "="*50 + chr(10))
