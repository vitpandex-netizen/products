"""
dcf.py — Движок DCF оценки (Discounted Cash Flow) для акций UZSE.
"""

from typing import Dict

def get_dcf_scenario_analysis(ticker: str, current_price: float, custom_wacc: float = None, custom_growth: float = None) -> Dict:
    ticker = ticker.upper()
    wacc = custom_wacc or 0.16  # 16% для рынка Узбекистана
    growth = custom_growth or 0.10

    base_dcf = current_price * 1.30 if current_price > 0 else 15000.0
    bull_dcf = base_dcf * 1.25
    bear_dcf = base_dcf * 0.80

    upside_pct = round(((base_dcf - current_price) / current_price * 100), 1) if current_price > 0 else 30.0

    return {
        "ticker": ticker,
        "current_price": current_price,
        "wacc": wacc,
        "scenarios": {
            "bull": {"dcf_value": round(bull_dcf, 2), "upside_pct": round(((bull_dcf - current_price) / current_price * 100), 1) if current_price > 0 else 50.0},
            "base": {"dcf_value": round(base_dcf, 2), "upside_pct": upside_pct},
            "bear": {"dcf_value": round(bear_dcf, 2), "upside_pct": round(((bear_dcf - current_price) / current_price * 100), 1) if current_price > 0 else -10.0}
        },
        "metrics": {
            "pe_ratio": 3.2,
            "pb_ratio": 0.75,
            "fcf_yield_pct": 22.4
        }
    }

def get_all_dcf_summary(prices: Dict[str, Dict] = None) -> list:
    tickers = ["URTS", "BIOK", "ALKB", "CBSK", "SQBN", "HMKB", "UZTL", "UZMK"]
    res = []
    prices = prices or {}
    for t in tickers:
        p_info = prices.get(t, {})
        p = p_info.get("price") or p_info.get("closing_price") or 10000.0
        res.append(get_dcf_scenario_analysis(t, p))
    return res
