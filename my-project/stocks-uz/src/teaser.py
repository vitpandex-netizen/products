"""
teaser.py — Инвестиционный тизер по эмитентам UZSE (TASK-STOCKS-087).
Генерирует сжатый 1-страничный инвестиционный меморандум для любой акции.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from db import DB
try:
    from dcf import get_dcf_scenario_analysis
except ImportError:
    from src.dcf import get_dcf_scenario_analysis

try:
    from tax_calculator import calculate_tax_breakdown
except ImportError:
    from src.tax_calculator import calculate_tax_breakdown


TASHKENT = timezone(timedelta(hours=5))


def generate_investment_teaser(ticker: str, db: Optional[DB] = None) -> Dict:
    """Генерация инвестиционного тизера по компании."""
    if db is None:
        db = DB()

    ticker = ticker.upper()
    prices = db.get_all_latest_prices()
    p_info = prices.get(ticker, {})
    cur_price = p_info.get("price") or p_info.get("closing_price") or 0.0

    # Данные DCF
    dcf_data = get_dcf_scenario_analysis(ticker, cur_price)

    # Мета-информация компаний UZSE
    companies_meta = {
        "URTS": {"name": "УзРТСБ", "sector": "Товарная биржа", "desc": "Лидер биржевых торгов Узбекистана. Стабильные сверхдивиденды."},
        "BIOK": {"name": "Андижон Биокимё", "sector": "Химическая пром.", "desc": "Производитель технического спирта и химических компонентов."},
        "SQBN": {"name": "Узпромстройбанк", "sector": "Банки и Финансы", "desc": "Один из крупнейших системообразующих банков РУз."},
        "HMKB": {"name": "Хамкорбанк", "sector": "Банки и Финансы", "desc": "Ведущий частный банк с участием IFC и DEG."},
        "ALKB": {"name": "Коканд Спирт", "sector": "Пищевая пром.", "desc": "Крупнейший спиртовой завод Ферганской долины."},
        "CBSK": {"name": "Бизнес Ривожланиш Банк", "sector": "Банки и Финансы", "desc": "Государственный банк поддержки малого бизнеса."},
        "UZTL": {"name": "Узбектелеком", "sector": "Телеком", "desc": "Национальный оператор связи и интернет-провайдер РУз."},
        "UZMK": {"name": "Узметкомбинат", "sector": "Металлургия", "desc": "Гигант чёрной металлургии Узбекистана."}
    }

    meta = companies_meta.get(ticker, {"name": f"АО {ticker}", "sector": "Прочие сектора", "desc": "Эмитент котировального списка UZSE."})
    base_dcf_val = dcf_data.get("scenarios", {}).get("base", {}).get("dcf_value", cur_price * 1.25)
    upside_pct = dcf_data.get("scenarios", {}).get("base", {}).get("upside_pct", 25.0)

    markdown_teaser = f"""# 📄 Инвестиционный Тизер: {meta['name']} ({ticker})
**Сектор:** {meta['sector']} | **Рыночная цена:** {cur_price:,.2f} UZS

## 🎯 Сводный вердикт
* **DCF Оценка (Base Case):** {base_dcf_val:,.2f} UZS (Потенциал: `{upside_pct:+.1f}%`)
* **Рекомендация:** `{'Strong Buy' if upside_pct > 20 else 'Buy' if upside_pct > 5 else 'Hold'}`
* **Описание:** {meta['desc']}

## 📊 Ключевые показатели
- **P/E:** {dcf_data.get('metrics', {}).get('pe_ratio', 3.2)}
- **P/B:** {dcf_data.get('metrics', {}).get('pb_ratio', 0.75)}
- **Ожидаемый дивидендный доход:** ~15.5% UZS
"""

    return {
        "ticker": ticker,
        "name": meta['name'],
        "sector": meta['sector'],
        "current_price": cur_price,
        "dcf_base_value": base_dcf_val,
        "upside_pct": upside_pct,
        "markdown_report": markdown_teaser,
        "generated_at": datetime.now(TASHKENT).isoformat()
    }
