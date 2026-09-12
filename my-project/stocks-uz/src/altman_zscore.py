"""
altman_zscore.py — Оценка банкротства (Altman Z-Score UZ) и коэффициентов ликвидности (TASK-STOCKS-082).
Формула Альтмана для развивающихся рынков (Emerging Markets Z'-Score) и метрики платежеспособности.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Финансовые показатели компаний UZSE (в млн UZS)
FINANCIAL_HEALTH_DATA: Dict[str, Dict] = {
    "URTS": {"working_cap": 120000, "total_assets": 450000, "retained_earnings": 180000, "ebit": 210000, "equity": 320000, "liabilities": 130000, "sales": 480000},
    "BIOK": {"working_cap": 35000, "total_assets": 140000, "retained_earnings": 45000, "ebit": 48000, "equity": 95000, "liabilities": 45000, "sales": 130000},
    "SQBN": {"working_cap": 4500000, "total_assets": 32000000, "retained_earnings": 2100000, "ebit": 1100000, "equity": 4800000, "liabilities": 27200000, "sales": 3500000},
    "HMKB": {"working_cap": 2800000, "total_assets": 18500000, "retained_earnings": 1400000, "ebit": 680000, "equity": 3100000, "liabilities": 15400000, "sales": 2100000},
    "ALKB": {"working_cap": 15000, "total_assets": 85000, "retained_earnings": 22000, "ebit": 24000, "equity": 52000, "liabilities": 33000, "sales": 95000},
    "CBSK": {"working_cap": 1200000, "total_assets": 9800000, "retained_earnings": 450000, "ebit": 290000, "equity": 1400000, "liabilities": 8400000, "sales": 1100000},
    "UZTL": {"working_cap": 350000, "total_assets": 2100000, "retained_earnings": 480000, "ebit": 320000, "equity": 1200000, "liabilities": 900000, "sales": 1900000},
    "UZMK": {"working_cap": 890000, "total_assets": 5400000, "retained_earnings": 1100000, "ebit": 750000, "equity": 3200000, "liabilities": 2200000, "sales": 4200000}
}


def calculate_altman_zscore(ticker: str) -> Dict:
    """Расчёт Altman Z'-Score и ликвидности для конкретного эмитента."""
    ticker = ticker.upper()
    data = FINANCIAL_HEALTH_DATA.get(ticker, {
        "working_cap": 50000, "total_assets": 200000, "retained_earnings": 40000,
        "ebit": 30000, "equity": 120000, "liabilities": 80000, "sales": 180000
    })

    ta = data["total_assets"]
    x1 = data["working_cap"] / ta if ta > 0 else 0
    x2 = data["retained_earnings"] / ta if ta > 0 else 0
    x3 = data["ebit"] / ta if ta > 0 else 0
    x4 = data["equity"] / data["liabilities"] if data["liabilities"] > 0 else 1.0
    x5 = data["sales"] / ta if ta > 0 else 0

    # Z'-Score формула для развивающихся рынков
    z_score = round(0.717 * x1 + 0.847 * x2 + 3.107 * x3 + 0.420 * x4 + 0.998 * x5, 2)

    if z_score > 2.90:
        zone = "Safe Zone"
        zone_ru = "Безопасная зона (Низкий риск)"
    elif z_score >= 1.23:
        zone = "Grey Zone"
        zone_ru = "Серая зона (Умеренный риск)"
    else:
        zone = "Distress Zone"
        zone_ru = "Опасная зона (Высокий риск)"

    current_ratio = round((data["working_cap"] + data["liabilities"]) / data["liabilities"], 2) if data["liabilities"] > 0 else 1.5
    debt_to_assets = round(data["liabilities"] / ta * 100, 1) if ta > 0 else 40.0

    return {
        "ticker": ticker,
        "z_score": z_score,
        "zone": zone,
        "zone_ru": zone_ru,
        "current_ratio": current_ratio,
        "debt_to_assets_pct": debt_to_assets,
        "components": {
            "x1_working_cap_ratio": round(x1, 3),
            "x2_retained_earnings_ratio": round(x2, 3),
            "x3_ebit_ratio": round(x3, 3),
            "x4_solvency_ratio": round(x4, 3),
            "x5_asset_turnover": round(x5, 3)
        }
    }


def get_all_zscores_summary() -> List[Dict]:
    """Сводный рейтинг финансовой устойчивости эмитентов UZSE."""
    results = [calculate_altman_zscore(t) for t in FINANCIAL_HEALTH_DATA.keys()]
    return sorted(results, key=lambda x: -x["z_score"])
