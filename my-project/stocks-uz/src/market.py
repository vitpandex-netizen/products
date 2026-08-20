"""Рыночные данные — UZSE парсинг + анализ."""
import logging, time
from datetime import datetime, timezone, timedelta
from typing import Optional
from src.uzse_client import UZSEClient

logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))

ALL_TICKERS = ['HMKB', 'UZMK', 'UZMKP', 'KVTS', 'QZSM', 'SQBN', 'SQBNP', 'URTS', 'IPTB']

def fetch_quotes() -> dict:
    """Текущие цены с UZSE."""
    client = UZSEClient()
    data = client.fetch_all()
    result = {}
    for d in data:
        ticker = d['ticker']
        price = d.get('last_trade_price') or d.get('closing_price') or 0
        prev_close = d.get('closing_price') or 0
        day_change = ((price - prev_close) / prev_close * 100) if prev_close and price else 0
        result[ticker] = {
            'price': price, 'prev_close': prev_close, 'day_change_pct': day_change,
            'closing_price': d.get('closing_price'), 'last_trade_date': d.get('last_trade_date'),
        }
    return result

def analyze_ticker(ticker: str) -> dict:
    """Анализ одного тикера UZSE."""
    result = {'ticker': ticker, 'error': None}
    try:
        client = UZSEClient()
        data = client.fetch_ticker(ticker)
        if not data:
            result['error'] = 'Ticker not found'
            return result
        price = data.get('last_trade_price') or data.get('closing_price') or 0
        close = data.get('closing_price') or 0
        result['price'] = price
        result['closing_price'] = close
        result['day_change'] = ((price - close) / close * 100) if close and price else 0
        result['last_trade_date'] = data.get('last_trade_date')
        # Генерация сигнала (упрощённая для UZSE)
        signals = []
        score = 50
        if price > 0 and close > 0:
            if price < close * 0.95:
                signals.append(('🟢', 'below_close', 10))
                score += 10
            elif price > close * 1.05:
                signals.append(('🔴', 'above_close', -5))
                score -= 5
            else:
                signals.append(('⚪', 'near_close', 0))
        result['score'] = max(0, min(100, score))
        result['signals'] = ''.join(s[0] for s in signals)
        result['signal_detail'] = [s[1] for s in signals]
    except Exception as e:
        result['error'] = str(e)
    return result

def screen_market(min_score: int = 50) -> list:
    """Скрининг всех тикеров UZSE."""
    results = []
    for ticker in ALL_TICKERS:
        a = analyze_ticker(ticker)
        if a.get('error'): continue
        if a.get('score', 0) >= min_score:
            results.append(a)
        time.sleep(0.5)
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    return results
