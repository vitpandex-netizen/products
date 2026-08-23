#!/usr/bin/env python3
"""
HERMES Alert Engine — запускается по cron.
Проверяет сигналы, портфель, цены и отправляет уведомления в Telegram.
"""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

TASHKENT = timezone(timedelta(hours=5))
API = "http://localhost:8003/api"
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-1004297012607")
THREAD_ID = os.environ.get("TELEGRAM_THREAD_ID", "576")

def api_get(path):
    r = urllib.request.urlopen(f"{API}{path}", timeout=10)
    return json.loads(r.read())

def send_tg(text, thread_id=None):
    if not TOKEN:
        print("No TELEGRAM_BOT_TOKEN")
        return False
    import urllib.parse
    tid = thread_id or THREAD_ID
    data = json.dumps({
        "chat_id": CHAT_ID, "text": text,
        "parse_mode": "Markdown", "disable_web_page_preview": True,
        "message_thread_id": int(tid),
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data=data, headers={"Content-Type": "application/json"},
    )
    try:
        r = urllib.request.urlopen(req, timeout=15)
        return r.status == 200
    except Exception as e:
        print(f"TG send error: {e}")
        return False

def daily_brief():
    """Ежедневный брифинг портфеля."""
    portfolio = api_get("/portfolio")
    signals = api_get("/signals")
    bonds = api_get("/bonds")
    catalysts = api_get("/catalysts")

    now = datetime.now(TASHKENT)
    lines = [
        f"📊 *BGT Bot Daily Brief*",
        f"📅 {now.strftime('%d.%m.%Y %H:%M')} Tashkent",
        "",
    ]

    # Stats
    bb = portfolio.get("barbell", {})
    conc = portfolio.get("concentration", {})
    lines.append(f"💰 *Портфель:* {portfolio['total_value']:,.0f} сум")
    pl = portfolio.get("total_pl", 0)
    emoji = "🟢" if pl >= 0 else "🔴"
    lines.append(f"{emoji} P&L: {pl:+,.0f} сум")
    lines.append(f"📊 Барбелл: {bb.get('equity_pct',0)}% акции / {bb.get('bond_pct',0)}% облигации")
    if conc.get("top_pct", 0) > 25:
        lines.append(f"⚠️ Концентрация: {conc['top_ticker']} {conc['top_pct']}%")
    lines.append("")

    # Signals
    sell = signals.get("sell", [])
    watch = signals.get("watch", [])
    buy = signals.get("buy", [])
    lines.append(f"⚡ *Сигналы:* SELL {len(sell)} | WATCH {len(watch)} | BUY {len(buy)}")

    if sell:
        lines.append(f"\n🔴 *Продать:*")
        for s in sell[:3]:
            lines.append(f"  • {s['ticker']}: {s['message'][:60]}")
    if watch:
        lines.append(f"\n🟡 *Внимание:*")
        for s in watch[:3]:
            lines.append(f"  • {s['ticker']}: {s['message'][:60]}")
    if buy:
        lines.append(f"\n🟢 *Потенциал:*")
        for s in buy[:3]:
            lines.append(f"  • {s['ticker']}: {s['message'][:60]}")

    # Bonds
    s = bonds.get("summary", {})
    lines.append(f"\n💵 *Купон:* {s.get('total_monthly',0):,.0f} сум/мес")
    for b in s.get("bonds", []):
        if not b.get("insured"):
            lines.append(f"⚠️ *{b['ticker']}* НЕТ СТРАХОВКИ!")

    # Next catalysts
    events = catalysts.get("catalysts", [])
    upcoming = [c for c in events if c.get("status") == "confirmed"][:3]
    if upcoming:
        lines.append(f"\n📅 *Ближайшие:*")
        for c in upcoming:
            lines.append(f"  • {c.get('fuzzy_label','?')} — {c['label']}")

    return "\n".join(lines)

def check_alerts():
    """Проверить сигналы и отправить алерты."""
    signals = api_get("/signals")
    alerts = []

    # SELL alerts
    for s in signals.get("sell", []):
        alerts.append({
            "severity": "sell",
            "text": f"🔴 *SIGNAL: {s['ticker']}*\n{s['message']}\nУровень: {s.get('ratio',0)*100:.0f}% от таргета",
        })

    # CONTRADICTION alerts
    for s in signals.get("watch", []):
        if s.get("verdict") == "CONTRADICTION":
            alerts.append({
                "severity": "watch",
                "text": f"🟡 *CONTRADICTION: {s['ticker']}*\n{s['message']}",
            })

    # Check for uninsured bonds
    bonds = api_get("/bonds")
    for b in bonds.get("summary", {}).get("bonds", []):
        if not b.get("insured"):
            alerts.append({
                "severity": "watch",
                "text": f"⚠️ *{b['ticker']}* — нет страховки! Не добирать позицию.",
            })

    return alerts

def cmd_daily():
    """Ежедневный брифинг."""
    brief = daily_brief()
    send_tg(brief)
    print(f"Daily brief sent ({len(brief)} chars)")

def cmd_alerts():
    """Проверка и отправка алертов."""
    alerts = check_alerts()
    if not alerts:
        print("No alerts to send")
        return

    for a in alerts:
        send_tg(a["text"])
        print(f"Sent alert: {a['severity']}")

    # Also save to API
    data = json.dumps(alerts).encode()
    for a in alerts:
        req = urllib.request.Request(
            f"{API}/alerts",
            data=data, headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            urllib.request.urlopen(req, timeout=5)
        except:
            pass

def cmd_full():
    """Полный цикл: цены → алерты → брифинг."""
    # 1. Get UZSE prices from DataCore
    try:
        r = urllib.request.urlopen("http://core-api:8000/api/v1/prices/?source=uzse&limit=80", timeout=10)
        prices = json.loads(r.read())
        # Update HERMES prices
        for p in prices.get("prices", []):
            data = json.dumps({"ticker": p["symbol"], "price": p["price"], "source": "uzse"}).encode()
            req = urllib.request.Request(
                f"{API}/prices",
                data=data, headers={"Content-Type": "application/json"},
            )
            try:
                urllib.request.urlopen(req, timeout=5)
            except:
                pass
        print(f"Updated {len(prices.get('prices',[]))} prices from UZSE")
    except Exception as e:
        print(f"Price sync: {e}")

    # 2. Check alerts
    alerts = check_alerts()
    for a in alerts:
        send_tg(a["text"])
        print(f"Alert: {a['severity']}")

    # 3. Send daily brief
    if not alerts:
        brief = daily_brief()
        send_tg(brief)
        print(f"Brief sent")

    print("Full cycle done")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python alert_engine.py <daily|alerts|full>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "daily":
        cmd_daily()
    elif cmd == "alerts":
        cmd_alerts()
    elif cmd == "full":
        cmd_full()
    else:
        print(f"Unknown: {cmd}")
        sys.exit(1)