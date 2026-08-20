"""Рыночные данные — Yahoo Finance + фундаментал + технический анализ."""
import logging, math, time
from datetime import datetime, timezone, timedelta
from typing import Optional
import yfinance as yf

logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))

STOCKS = [
    "NVDA", "AAPL", "MSFT", "GOOGL", "META", "AMZN",
    "TSLA", "AVGO", "ORCL", "AMD", "MRVL",
    "IBM", "QCOM", "CSCO", "CRWD", "PLTR",
    "JPM", "GS", "BAC", "V", "COIN", "HOOD",
    "MSTR", "MCD", "KO", "PEP", "PG", "NVO",
    "XOM", "CVX", "LLY", "JNJ", "PFE", "UNH", "MRK", "ABBV",
    "NFLX", "GME",
]
ETFS = ["SPY", "QQQ", "TQQQ", "VOO", "VTI", "IEMG", "SCHF", "TBLL", "COPX", "XLE", "XOP", "URA"]
METALS = ["GLD", "SLV", "PALL", "PPLT"]
ALL_TICKERS = STOCKS + ETFS + METALS

def _get_single_ticker_price(data, ticker):
    """Извлечь цену из DataFrame с MultiIndex колонками (один тикер)."""
    try:
        # data columns are MultiIndex e.g. [('NVDA','Close'), ('NVDA','Volume')]
        close = data.xs('Close', level='Price', axis=1).iloc[:, 0].dropna()
        if len(close) < 1:
            return None
        price = float(close.iloc[-1])
        prev_close = float(close.iloc[-2]) if len(close) >= 2 else price
        vol = data.xs('Volume', level='Price', axis=1).iloc[:, 0].dropna()
        volume = int(vol.iloc[-1]) if len(vol) > 0 else 0
        return {'price': price, 'prev_close': prev_close, 'volume': volume}
    except Exception:
        return None

def _get_multi_ticker_price(data, ticker):
    """Извлечь цену из group_by='ticker' DataFrame (много тикеров)."""
    try:
        df = data[ticker]
        close = df['Close'].dropna()
        if len(close) < 1:
            return None
        price = float(close.iloc[-1])
        prev_close = float(close.iloc[-2]) if len(close) >= 2 else price
        volume = int(df['Volume'].dropna().iloc[-1]) if 'Volume' in df.columns else 0
        return {'price': price, 'prev_close': prev_close, 'volume': volume}
    except Exception:
        return None

def fetch_quotes(tickers: list = None) -> dict:
    """Текущие цены для списка тикеров одним батч-запросом."""
    if tickers is None:
        tickers = ALL_TICKERS
    tickers = list(tickers)
    if not tickers:
        return {}
    result = {}
    try:
        data = yf.download(tickers, period='2d', progress=False, auto_adjust=True, group_by='ticker')
        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    info = _get_single_ticker_price(data, ticker)
                else:
                    info = _get_multi_ticker_price(data, ticker)
                if info is None:
                    continue
                price = info['price']
                if math.isnan(price):
                    continue
                day_change_pct = ((price - info['prev_close']) / info['prev_close']) * 100 if info['prev_close'] else None
                result[ticker] = {'price': price, 'prev_close': info['prev_close'], 'day_change_pct': day_change_pct, 'volume': info['volume']}
            except Exception:
                continue
    except Exception as e:
        logger.error(f"Yahoo batch fetch failed: {e}")
    return result

def fetch_fundamentals(ticker: str) -> Optional[dict]:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        if not info:
            return None
        pe = info.get('trailingPE') or info.get('forwardPE') or 0
        return {
            'pe_ratio': float(pe) if pe and pe > 0 else 0,
            'forward_pe': float(info.get('forwardPE') or 0),
            'pb_ratio': float(info.get('priceToBook') or 0),
            'eps_ttm': float(info.get('trailingEps') or 0),
            'div_yield': float(info.get('dividendYield') or 0) * 100,
            'market_cap': float(info.get('marketCap') or 0),
            'beta': float(info.get('beta') or 0),
            'fifty_two_week_high': float(info.get('fiftyTwoWeekHigh') or 0),
            'fifty_two_week_low': float(info.get('fiftyTwoWeekLow') or 0),
            'avg_volume': float(info.get('averageVolume') or 0),
            'sector': str(info.get('sector', '') or ''),
            'industry': str(info.get('industry', '') or ''),
        }
    except Exception as e:
        logger.debug(f"Fundamentals failed {ticker}: {e}")
        return None

def fetch_history(ticker: str, period: str = '3mo') -> Optional[list]:
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period)
        if df.empty:
            return None
        return [{
            'date': idx.strftime('%Y-%m-%d'),
            'open': float(row['Open']), 'high': float(row['High']),
            'low': float(row['Low']), 'close': float(row['Close']),
            'volume': int(row['Volume']),
        } for idx, row in df.iterrows()]
    except Exception:
        return None

def compute_rsi(prices: list, period: int = 14) -> Optional[float]:
    if len(prices) < period + 1:
        return None
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    return 100 - (100 / (1 + avg_gain / avg_loss))

def compute_sma(prices: list, period: int = 20) -> Optional[float]:
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def compute_macd(prices: list) -> Optional[dict]:
    if len(prices) < 26:
        return None
    ema12 = _ema(prices, 12)
    ema26 = _ema(prices, 26)
    macd = ema12 - ema26
    signal = _ema([macd] * len(prices), 9) if len(prices) >= 9 else macd
    return {'macd': macd, 'signal': signal, 'histogram': macd - signal}

def _ema(prices: list, period: int) -> float:
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema

def analyze_ticker(ticker: str) -> dict:
    """Полный анализ: цена, фундаментал, технические индикаторы, сигнал."""
    result = {'ticker': ticker, 'error': None}
    try:
        quotes = fetch_quotes([ticker])
        if ticker in quotes:
            result['price'] = quotes[ticker]['price']
            result['prev_close'] = quotes[ticker]['prev_close']
            result['day_change'] = quotes[ticker]['day_change_pct']
            result['volume'] = quotes[ticker]['volume']
        else:
            result['price'] = 0

        fund = fetch_fundamentals(ticker)
        if fund:
            for k in ['pe_ratio', 'forward_pe', 'pb_ratio', 'eps_ttm', 'div_yield',
                       'market_cap', 'beta', 'sector', 'industry']:
                v = fund.get(k)
                if v: result[k] = v
            high = fund.get('fifty_two_week_high')
            low = fund.get('fifty_two_week_low')
            if high and high > 0: result['high_52w'] = high
            if low and low > 0: result['low_52w'] = low

        hist = fetch_history(ticker, '3mo')
        if hist and len(hist) > 30:
            closes = [h['close'] for h in hist]
            result['rsi_14'] = compute_rsi(closes, 14)
            result['sma_20'] = compute_sma(closes, 20)
            result['sma_50'] = compute_sma(closes, 50)
            macd = compute_macd(closes)
            if macd:
                result['macd'] = macd['macd']
                result['macd_signal'] = macd['signal']

        price = result.get('price', 0) or 0
        high = result.get('high_52w')
        low = result.get('low_52w')
        if high and high > 0: result['high_52w_pct'] = ((price / high) - 1) * 100
        if low and low > 0: result['low_52w_pct'] = ((price / low) - 1) * 100

        # Сигнал
        signals = []
        score = 50
        rsi = result.get('rsi_14')
        if rsi is not None:
            if rsi < 30: signals.append(('🟢', 'oversold', 15))
            elif rsi < 40: signals.append(('🟢', 'near_oversold', 10))
            elif rsi > 70: signals.append(('🔴', 'overbought', -15))
            elif rsi > 60: signals.append(('🟡', 'near_overbought', -10))
        sma20 = result.get('sma_20')
        if sma20 and price:
            if price < sma20 * 0.95: signals.append(('🟢', 'below_sma20_discount', 10))
            elif price > sma20 * 1.05: signals.append(('🔴', 'above_sma20_premium', -5))
        pe = result.get('pe_ratio')
        if pe and pe > 0:
            if pe < 15: signals.append(('🟢', 'low_pe', 10))
            elif pe > 40: signals.append(('🟡', 'high_pe', -5))
        if result.get('high_52w_pct') is not None:
            if result['high_52w_pct'] < -30: signals.append(('🟢', 'deep_discount_52w', 15))
            elif result['high_52w_pct'] < -15: signals.append(('🟢', 'discount_52w', 10))
        if result.get('low_52w_pct') is not None and result['low_52w_pct'] < 5:
            signals.append(('🔴', 'near_52w_low', -5))

        for _, _, s in signals:
            score += s
        result['score'] = max(0, min(100, score))
        result['signals'] = ''.join(s[0] for s in signals)
        result['signal_detail'] = [s[1] for s in signals]
    except Exception as e:
        result['error'] = str(e)
    return result

def screen_market(tickers: list = None, min_score: int = 50) -> list:
    if tickers is None:
        tickers = ALL_TICKERS
    results = []
    for i, ticker in enumerate(tickers):
        analysis = analyze_ticker(ticker)
        if analysis.get('error'):
            continue
        score = analysis.get('score', 0)
        if score >= min_score:
            results.append(analysis)
        if i > 0 and i % 3 == 0:
            time.sleep(1)
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    return results
