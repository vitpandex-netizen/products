#!/usr/bin/env python3
"""Интеграция EventBus в Stocks-US — публикует события портфеля."""
import sys, os, logging
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE.parent / 'datacore'))
os.chdir(str(BASE))

logger = logging.getLogger("stocks-eventbus")

def init_bus():
    try:
        from eventbus import EventBus
        bus = EventBus(service_name="stocks-us")
        bus.listen(daemon=True)
        logger.info("✅ EventBus инициализирован для stocks-us")
        return bus
    except Exception as e:
        logger.warning(f"⚠️ EventBus не загружен: {e}")
        return None

def publish_portfolio_summary(bus, summary: dict):
    if not bus:
        return
    bus.publish("portfolio.summary", {
        "total_value": summary.get("total_value", 0),
        "total_pl": summary.get("total_pl", 0),
        "total_pl_pct": summary.get("total_pl_pct", 0),
        "positions": len(summary.get("positions", [])),
    })

def publish_price_alert(bus, ticker: str, price: float, change_pct: float):
    if not bus:
        return
    bus.publish("portfolio.price_alert", {
        "ticker": ticker,
        "price": price,
        "change_pct": change_pct,
    })