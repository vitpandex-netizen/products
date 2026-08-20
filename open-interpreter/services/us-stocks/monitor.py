"""US stock market monitor - tracks signals and opportunities."""
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.db import get_conn
from shared.utils import notify, send_hermes_message, get_config, set_config

import requests

# Free APIs for US stocks
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
FINNHUB_URL = "https://finnhub.io/api/v1"

# Default watchlist
DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "SPY", "QQQ"]

def get_free_api_key():
    """Try to get a free API key, or return None (will use alternative sources)."""
    return get_config("alpha_vantage_key")

def fetch_yahoo_quote(ticker):
    """Fetch quote from Yahoo Finance (no API key needed)."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {"range": "1d", "interval": "1d"}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("chart", {}).get("result", [{}])[0]
        meta = result.get("meta", {})
        return {
            "ticker": ticker,
            "price": meta.get("regularMarketPrice"),
            "previous_close": meta.get("previousClose"),
            "change_pct": meta.get("chartPreviousClose"),
            "currency": meta.get("currency", "USD"),
            "exchange": meta.get("exchangeName", "UNKNOWN"),
            "timestamp": meta.get("regularMarketTime")
        }
    except Exception as e:
        print(f"[US] Error fetching {ticker}: {e}")
        return None

def fetch_finnhub_news(ticker):
    """Fetch news for a ticker from Finnhub (free tier)."""
    api_key = get_config("finnhub_key")
    if not api_key:
        return []
    try:
        resp = requests.get(
            f"{FINNHUB_URL}/company-news",
            params={"symbol": ticker, "from": time.strftime("%Y-%m-%d"), "to": time.strftime("%Y-%m-%d"), "token": api_key},
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json()[:5]
    except Exception as e:
        print(f"[US] News error: {e}")
    return []

def analyze_ticker(ticker, quote):
    """Simple analysis: trend detection."""
    if not quote or not quote.get("price"):
        return None
    
    price = quote["price"]
    prev_close = quote.get("previous_close", price)
    change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0
    
    signal = "neutral"
    reason = f"Цена: ${price:.2f}, изменение: {change_pct:+.2f}%"
    
    if change_pct < -3:
        signal = "oversold"
        reason += " ⚠️ Перепродана — возможен отскок"
    elif change_pct > 5:
        signal = "overbought"
        reason += " 🔥 Перекуплена — осторожно"
    elif change_pct < -1:
        signal = "dip"
        reason += " 📉 Краткосрочное снижение — стоит присмотреться"
    
    return {"ticker": ticker, "price": price, "signal": signal, "reason": reason, "metadata": json.dumps(quote)}

def run_once():
    """Single monitoring run."""
    tickers = get_config("us_tickers", DEFAULT_TICKERS)
    signals = []
    
    print(f"[US] Checking {len(tickers)} tickers...")
    
    for ticker in tickers:
        quote = fetch_yahoo_quote(ticker)
        if quote:
            analysis = analyze_ticker(ticker, quote)
            if analysis:
                signals.append(analysis)
        time.sleep(0.5)  # Rate limit for Yahoo
        print(f"  {ticker}: ${quote.get('price', 'N/A') if quote else 'N/A'}")
    
    # Store signals
    conn = get_conn()
    for s in signals:
        conn.execute("""
            INSERT INTO stock_signals (ticker, exchange, price, signal, reason, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (s["ticker"], "US", s["price"], s["signal"], s["reason"], s.get("metadata", "{}")))
    conn.commit()
    conn.close()
    
    # Alert on meaningful signals
    alerts = [s for s in signals if s["signal"] in ("oversold", "dip")]
    if alerts:
        msg = "📊 *Анализ US рынка*\n\n"
        for a in alerts:
            msg += f"• ${a['ticker']}: ${a['price']:.2f} — *{a['reason']}*\n"
        msg += "\n_Нужен апрув для действий?_"
        send_hermes_message(msg)
    
    print(f"[US] Done. Signals: {len(signals)}, Alerts: {len(alerts)}")
    return {"total": len(signals), "alerts": len(alerts)}

if __name__ == "__main__":
    run_once()
