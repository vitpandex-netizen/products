"""Global events monitor - tracks financial, economic and tech events."""
import sys
import json
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.db import get_conn
from shared.utils import notify, send_hermes_message, get_config, set_config

import requests

# Sources
RSS_FEEDS = get_config("events_rss_feeds", [
    "https://www.investing.com/rss/news.rss",
    "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
])

ECONOMIC_CALENDAR = "https://finance.yahoo.com/calendar/economic"  # Will use scraping

def fetch_economic_calendar():
    """Fetch economic calendar events."""
    events = []
    try:
        resp = requests.get(
            "https://financialmodelingprep.com/api/v3/economic-calendar",
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            # Filter for upcoming events
            today = datetime.now().strftime("%Y-%m-%d")
            for item in data[:20]:
                if item.get("date", "").startswith(today) or True:
                    events.append({
                        "source": "economic-calendar",
                        "title": item.get("event", item.get("indicator", "Economic event")),
                        "summary": f"Country: {item.get('country','')} | Actual: {item.get('actual','')} | Forecast: {item.get('forecast','')} | Previous: {item.get('previous','')}",
                        "url": "",
                        "category": "economics",
                        "impact": item.get("impact", "low")
                    })
    except Exception as e:
        print(f"[EVENTS] Calendar error: {e}")
    
    return events

def scrape_finviz_news():
    """Scrape Finviz for market-moving news."""
    news = []
    try:
        resp = requests.get(
            "https://finviz.com/news.ashx",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        if resp.status_code == 200:
            from html.parser import HTMLParser
            class NewsParser(HTMLParser):
                def handle_data(self, data):
                    if len(data.strip()) > 20:
                        news.append(data.strip())
            parser = NewsParser()
            parser.feed(resp.text)
            # Take first 10 meaningful news items
            news = [n for n in news if len(n) > 30][:10]
            
    except Exception as e:
        print(f"[EVENTS] Finviz error: {e}")
    
    return [{"source": "finviz", "title": n, "summary": "", "url": "", "category": "markets", "impact": "medium"} for n in news]

def run_once():
    """Single events monitoring run."""
    events = []
    
    print("[EVENTS] Fetching economic calendar...")
    events.extend(fetch_economic_calendar())
    
    print("[EVENTS] Fetching market news...")
    events.extend(scrape_finviz_news())
    
    # Store events
    conn = get_conn()
    stored = 0
    for e in events:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO events (source, title, summary, url, category, impact)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (e["source"], e["title"][:500], e["summary"][:1000], 
                  e["url"], e["category"], e["impact"]))
            stored += 1
        except Exception as ex:
            print(f"[EVENTS] Store error: {ex}")
    conn.commit()
    conn.close()
    
    # Alert on high impact events
    high_impact = [e for e in events if e.get("impact") in ("high", "medium")]
    if high_impact:
        msg = "🌍 *События дня*\n\n"
        for e in high_impact[:5]:
            msg += f"• {e['title']}\n"
        send_hermes_message(msg)
    
    print(f"[EVENTS] Done. Stored: {stored}, High impact: {len(high_impact)}")
    return {"stored": stored, "high_impact": len(high_impact)}

if __name__ == "__main__":
    run_once()
