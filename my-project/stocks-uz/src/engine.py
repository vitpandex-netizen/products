import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import json, math
from datetime import datetime, timezone
from typing import Optional


# ===== M1: Консолидация портфеля =====

def consolidate_positions(positions: list[dict], prices: dict[str, float]) -> dict:
    """
    Свести позиции в единую картину.
    prices: {ticker: current_price}
    """
    # По тикеру
    by_ticker = {}
    # По брокеру
    by_broker = {}
    
    for p in positions:
        t = p["ticker"]
        if t not in by_ticker:
            by_ticker[t] = {"ticker": t, "shares": 0, "cost": 0, "brokers": []}
        by_ticker[t]["shares"] += p["shares"]
        by_ticker[t]["cost"] += p["shares"] * p["avg_buy_price"]
        by_ticker[t]["brokers"].append(p["broker"])
        
        b = p["broker"]
        if b not in by_broker:
            by_broker[b] = {"broker": b, "cost": 0, "positions": []}
        by_broker[b]["cost"] += p["shares"] * p["avg_buy_price"]
        by_broker[b]["positions"].append(p["ticker"])
    
    # Текущая стоимость и P&L
    total_cost = 0
    total_value = 0
    consolidated = []
    for t, data in by_ticker.items():
        price = prices.get(t, 0)
        value = data["shares"] * price
        cost = data["cost"]
        pl = value - cost
        pl_pct = ((price / (cost / data["shares"])) - 1) * 100 if data["shares"] > 0 and cost > 0 else 0
        avg_price = cost / data["shares"] if data["shares"] > 0 else 0
        
        total_cost += cost
        total_value += value
        
        consolidated.append({
            "ticker": t,
            "shares": data["shares"],
            "avg_price": round(avg_price, 2),
            "current_price": price,
            "value": round(value, 2),
            "cost": round(cost, 2),
            "pl": round(pl, 2),
            "pl_pct": round(pl_pct, 2),
            "brokers": list(set(data["brokers"])),
        })
    
    return {
        "positions": sorted(consolidated, key=lambda x: x["value"], reverse=True),
        "by_broker": by_broker,
        "total_cost": round(total_cost, 2),
        "total_value": round(total_value, 2),
        "total_pl": round(total_value - total_cost, 2),
    }


def barbell_balance(positions: list[dict], bonds: list[dict], prices: dict[str, float]) -> dict:
    """Барбелл-баланс: агрессивная (акции) vs консервативная (облигации) нога."""
    equity_value = sum(
        p["shares"] * prices.get(p["ticker"], 0) 
        for p in positions 
        if p.get("leg", "aggressive") == "aggressive"
    )
    bond_value = sum(b["shares"] * b["buy_price"] for b in bonds)
    total = equity_value + bond_value
    
    if total == 0:
        return {"equity_pct": 0, "bond_pct": 0, "total": 0}
    
    return {
        "equity_value": round(equity_value, 2),
        "bond_value": round(bond_value, 2),
        "total": round(total, 2),
        "equity_pct": round(equity_value / total * 100, 1),
        "bond_pct": round(bond_value / total * 100, 1),
    }


def concentration(positions: list[dict], prices: dict[str, float]) -> dict:
    """Доля топ-позиции."""
    if not positions:
        return {"top_ticker": None, "top_pct": 0, "top_value": 0}
    
    values = [(p["ticker"], p["shares"] * prices.get(p["ticker"], 0)) for p in positions]
    total = sum(v for _, v in values)
    if total == 0:
        return {"top_ticker": None, "top_pct": 0, "top_value": 0}
    
    top_ticker, top_value = max(values, key=lambda x: x[1])
    return {
        "top_ticker": top_ticker,
        "top_value": round(top_value, 2),
        "top_pct": round(top_value / total * 100, 1),
    }


# ===== M2: Сигнальный движок =====

def signal_for_position(position: dict, targets: list[dict], rules: dict) -> dict:
    """
    Применить правила пользователя к позиции.
    Возвращает: {verdict, severity, ratio, upside, message, targets_detail}
    """
    ticker = position["ticker"]
    price = position.get("current_price", 0)
    
    if not targets:
        return {
            "ticker": ticker,
            "verdict": "HOLD",
            "severity": "info",
            "message": f"Нет таргета KD для {ticker}",
            "ratio": None, "upside": None,
        }
    
    # Основной таргет (1Y панорама — приоритет)
    main_target = None
    alt_targets = []
    for t in targets:
        if t.get("horizon") == "1Y" and t.get("analyst", "").startswith("KAP DEPO"):
            main_target = t
        else:
            alt_targets.append(t)
    
    if not main_target:
        main_target = targets[0]  # fallback to first
    
    target_value = main_target["value"]
    ratio = price / target_value if target_value > 0 else 999
    
    # Проверка на противоречие
    contra = False
    contra_detail = []
    for t in alt_targets:
        if abs(target_value - t["value"]) / min(target_value, t["value"]) > rules.get("CONTRA_PCT", 0.15):
            contra = True
            contra_detail.append({
                "analyst": t["analyst"],
                "value": t["value"],
                "horizon": t["horizon"],
            })
    
    if contra:
        return {
            "ticker": ticker,
            "verdict": "CONTRADICTION",
            "severity": "watch",
            "ratio": round(ratio, 4),
            "upside": round((target_value / price - 1) * 100, 1) if price > 0 else 0,
            "message": f"Противоречие таргетов для {ticker}: {target_value} vs {[c['value'] for c in contra_detail]}",
            "target_value": target_value,
            "contra": contra_detail,
        }
    
    sell_ratio = rules.get("SELL_RATIO", 1.0)
    near_ratio = rules.get("NEAR_RATIO", 0.9)
    sell_hard = rules.get("SELL_HARD", 1.15)
    
    if ratio >= sell_ratio:
        if ratio >= sell_hard:
            msg = f"Цена {price:,.2f} существенно выше таргета {target_value:,.2f} (+{(ratio-1)*100:.0f}%)"
        else:
            msg = f"Цена {price:,.2f} достигла таргета {target_value:,.2f}"
        return {
            "ticker": ticker, "verdict": "SELL", "severity": "sell",
            "ratio": round(ratio, 4), "upside": round((ratio-1)*100, 1),
            "message": msg, "target_value": target_value,
        }
    elif ratio >= near_ratio:
        return {
            "ticker": ticker, "verdict": "NEAR", "severity": "watch",
            "ratio": round(ratio, 4), "upside": round((target_value/price-1)*100, 1),
            "message": f"У цели: {price:,.2f} до таргета {target_value:,.2f} (+{(target_value/price-1)*100:.0f}%)",
            "target_value": target_value,
        }
    else:
        upside = (target_value / price - 1) * 100
        return {
            "ticker": ticker, "verdict": "UPSIDE", "severity": "buy",
            "ratio": round(ratio, 4), "upside": round(upside, 1),
            "message": f"Потенциал +{upside:.0f}% до таргета {target_value:,.2f}",
            "target_value": target_value,
        }


def run_signal_engine(positions: list[dict], all_targets: list[dict], 
                       prices: dict[str, float], rules: dict) -> dict:
    """Полный прогон сигнального движка по всем позициям."""
    result = {"sell": [], "watch": [], "buy": [], "hold": []}
    
    for pos in positions:
        ticker = pos["ticker"]
        price = prices.get(ticker, 0)
        pos_with_price = {**pos, "current_price": price}
        
        ticker_targets = [t for t in all_targets if t["ticker"] == ticker]
        signal = signal_for_position(pos_with_price, ticker_targets, rules)
        
        # Инструменты без таргета — всегда HOLD
        if not ticker_targets:
            signal["verdict"] = "HOLD"
            signal["message"] = f"Нет таргета · pre-IPO / фонд"
            result["hold"].append(signal)
            continue
        
        if signal["verdict"] == "CONTRADICTION":
            result["watch"].append(signal)
        elif signal["verdict"] == "SELL":
            result["sell"].append(signal)
        elif signal["verdict"] == "NEAR":
            result["watch"].append(signal)
        elif signal["verdict"] == "UPSIDE":
            result["buy"].append(signal)
        else:
            result["hold"].append(signal)
    
    # Сортировка
    for key in ["sell", "buy"]:
        result[key].sort(key=lambda x: abs(x.get("upside", 0) or 0), reverse=True)
    
    return result


# ===== M4: Облигации / YTM =====

def ytm(coupon_rate: float, coupon_freq: int, nominal: float, 
        buy_price: float, maturity: str, shares: float = 1) -> dict:
    """
    Эффективная доходность (YTM) через бисекцию.
    """
    try:
        maturity_date = datetime.fromisoformat(maturity)
    except:
        maturity_date = datetime.now()
    
    today = datetime.now()
    years = max((maturity_date - today).days / 365.25, 0.01)
    n = max(round(years * coupon_freq), 1)
    
    coupon = nominal * coupon_rate / 100 / coupon_freq
    
    def npv(y):
        total = 0.0
        for k in range(1, n + 1):
            total += coupon / (1 + y / coupon_freq) ** k
        total += nominal / (1 + y / coupon_freq) ** n
        return total - buy_price
    
    # Бисекция
    lo, hi = 0.001, 0.99
    for _ in range(100):
        mid = (lo + hi) / 2
        if npv(mid) > 0:
            lo = mid
        else:
            hi = mid
    
    eff_yield = round((lo + hi) / 2 * 100, 2)
    
    # Упрощённая проверка (ментальная модель)
    annual_coupon = nominal * coupon_rate / 100
    premium = buy_price - nominal
    eff_approx = ((annual_coupon - premium / years) / buy_price) * 100
    
    # Месячный купонный поток
    monthly = (annual_coupon * shares) / 12
    
    return {
        "ytm": eff_yield,
        "ytm_approx": round(eff_approx, 2),
        "monthly_coupon": round(monthly, 2),
        "annual_coupon": round(annual_coupon * shares, 2),
        "years_to_maturity": round(years, 2),
        "premium": round(premium, 2),
        "coupon_rate": coupon_rate,
        "n_payments": n,
    }


def bonds_summary(bonds: list[dict]) -> dict:
    """Сводка по всем облигациям ИИС."""
    rows = []
    total_monthly = 0
    total_annual = 0
    
    for b in bonds:
        calc = ytm(
            b["coupon_rate"], b.get("coupon_freq", 4),
            b["nominal"], b["buy_price"], b["maturity"], b["shares"]
        )
        calc["ticker"] = b["ticker"]
        calc["issuer"] = b["issuer"]
        calc["insured"] = b.get("insured", False)
        calc["insurer"] = b.get("insurer")
        rows.append(calc)
        total_monthly += calc["monthly_coupon"]
        total_annual += calc["annual_coupon"]
    
    return {
        "bonds": rows,
        "total_monthly": round(total_monthly, 2),
        "total_annual": round(total_annual, 2),
        "count": len(bonds),
    }