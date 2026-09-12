"""
tax_calculator.py — Налоговый калькулятор по операциям UZSE (TASK-STOCKS-088).
Расчёт налога на дивиденды и прирост капитала в соответствии с Налоговым кодексом РУз.
"""

from typing import Dict

# Налоговые ставки РУз (НК РУз 2026)
DIVIDEND_TAX_RESIDENT = 0.05       # 5% для физических лиц-резидентов РУз
DIVIDEND_TAX_NON_RESIDENT = 0.12   # 12% для нерезидентов
CAPITAL_GAINS_TAX_RESIDENT = 0.00  # 0% освобождение для физлиц-резидентов при продаже акций на UZSE


def calculate_tax_breakdown(
    ticker: str,
    shares: float,
    buy_price: float,
    current_price: float,
    dividend_per_share: float = 0.0,
    is_resident: bool = True
) -> Dict:
    """Полный расчёт налоговых обязательств и чистой доходности (Net Yield)."""
    div_tax_rate = DIVIDEND_TAX_RESIDENT if is_resident else DIVIDEND_TAX_NON_RESIDENT
    cap_tax_rate = CAPITAL_GAINS_TAX_RESIDENT if is_resident else 0.12

    gross_dividend = shares * dividend_per_share
    dividend_tax = gross_dividend * div_tax_rate
    net_dividend = gross_dividend - dividend_tax

    gross_capital_gain = max(0.0, (current_price - buy_price) * shares)
    capital_gains_tax = gross_capital_gain * cap_tax_rate
    net_capital_gain = gross_capital_gain - capital_gains_tax

    total_cost = shares * buy_price
    total_net_profit = net_dividend + net_capital_gain
    net_roi_pct = round((total_net_profit / total_cost * 100), 2) if total_cost > 0 else 0.0

    gross_div_yield_pct = (dividend_per_share / buy_price * 100) if buy_price > 0 else 0.0
    net_div_yield_pct = (dividend_per_share * (1 - div_tax_rate) / buy_price * 100) if buy_price > 0 else 0.0

    return {
        "ticker": ticker.upper(),
        "shares": shares,
        "buy_price": buy_price,
        "current_price": current_price,
        "is_resident": is_resident,
        "gross_dividend_uzs": round(gross_dividend, 2),
        "dividend_tax_uzs": round(dividend_tax, 2),
        "net_dividend_uzs": round(net_dividend, 2),
        "dividend_tax_rate_pct": round(div_tax_rate * 100, 1),
        "gross_capital_gain_uzs": round(gross_capital_gain, 2),
        "capital_gains_tax_uzs": round(capital_gains_tax, 2),
        "net_capital_gain_uzs": round(net_capital_gain, 2),
        "total_net_profit_uzs": round(total_net_profit, 2),
        "gross_div_yield_pct": round(gross_div_yield_pct, 2),
        "net_div_yield_pct": round(net_div_yield_pct, 2),
        "net_roi_pct": net_roi_pct
    }
