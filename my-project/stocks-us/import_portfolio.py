#!/usr/bin/env python3
"""Импорт портфеля пользователя из скриншотов в БД stocks-us."""
import sys, os, logging
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / 'src'))
os.chdir(str(BASE))

from dotenv import load_dotenv
load_dotenv(BASE / '.env')
from src.db import DB

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("import")

# Полный портфель из скриншотов (17.08.2026)
# Формат: (ticker, shares, avg_price, target_pct, stop_loss_pct)
PORTFOLIO = [
    # === Скриншот 1: Основные позиции ===
    ("INTC",  0.805, 76.40,  None, 10.0),   # Intel +$23.18
    ("GOOGL", 0.111, 337.20, None, 10.0),   # Alphabet +$1.29
    ("AAPL",  0.894, 276.30, None, 10.0),   # Apple +$28.02
    ("CVX",   0.00136, 184.20, None, 10.0), # Chevron +$0.02
    ("JPM",   0.0149, 326.60, None, 10.0),  # JPMorgan +$0.56

    # === Скриншот 2: Технологии и металлы ===
    ("ORCL",  0.172, 157.73, None, 10.0),   # Oracle -$1.46
    ("AMD",   0.0272, 252.85, None, 15.0),  # AMD +$7.28
    ("NFLX",  1.186, 94.30,  None, 10.0),   # Netflix -$20.22
    ("MCD",   0.0102, 282.35, None, 10.0),  # McDonald's -$0.09
    ("SLV",   2.860, 66.87,  None, 15.0),   # Silver ETF -$22.77
    ("TSLA",  0.2273, 380.15, None, 15.0),  # Tesla -$8.21
    ("PPLT",  1.177, 17.47,  None, 15.0),   # Platinum ETF -$1.87
    ("COPX",  0.1149, 83.46,  None, 15.0),  # Copper ETF +$0.44
    ("XOM",   0.0131, 162.72, None, 10.0),  # Exxon -$0.01
    ("NVDA",  0.5847, 191.77, None, 10.0),  # NVIDIA +$20.14
    ("PEP",   0.2807, 151.79, None, 10.0),  # PepsiCo -$2.80
    ("SPY",   0.2726, 707.41, None, 10.0),  # S&P 500 ETF +$20.24
    ("PALL",  1.208, 27.70,  None, 15.0),   # Palladium ETF -$4.17
    ("AVGO",  0.0098, 391.65, None, 10.0),  # Broadcom +$0.07

    # === Скриншот 3: Редкие активы ===
    ("SPCXX", 3.93,  142.52, None, 10.0),   # SpaceX -$3.09
    ("MSFT",  0.039, 374.10, None, 10.0),   # Microsoft +$4.60
    ("BAC",   0.069, 56.38,  None, 10.0),   # Bank of America +$0.55
    ("GS",    0.0018, 1027.77, None, 10.0), # Goldman Sachs -$0.04
    ("TQQQ",  0.053, 73.58,  None, 15.0),   # Nasdaq 3x +$0.25
    ("BSP",   1.71,  28.71,  None, 10.0),   # Bending Spoons +$16.80
    ("SKHY",  0.242, 149.58, None, 10.0),   # SK Hynix +$5.73
    ("XLE",   0.034, 57.94,  None, 10.0),   # Energy ETF +$0.15
    ("TSM",   0.0096, 411.08, None, 10.0),  # TSMC +$0.18
    ("XOP",   0.0234, 167.95, None, 10.0),  # Oil & Gas ETF +$0.28
    ("URA",   0.0498, 39.56,  None, 15.0),  # Uranium ETF +$0.29
    ("SNDK",  0.00126, 1563.00, None, 10.0),# SanDisk +$0.21
]

def main():
    db = DB()
    count = 0
    for ticker, shares, price, target, stop in PORTFOLIO:
        try:
            db.add_to_portfolio(ticker, shares, price, target, stop)
            count += 1
            logger.info(f"  ✅ {ticker}: {shares:.4f} шт @ ${price:.2f}")
        except Exception as e:
            logger.error(f"  ❌ {ticker}: {e}")

    # Сводка
    summary = db.get_portfolio_summary()
    print(f"\n{'='*50}")
    print(f"✅ Импортировано: {count} позиций")
    print(f"💰 Стоимость: ${summary['total_value']:,.2f}")
    print(f"📊 P&L: ${summary['total_pl']:+,.2f} ({summary['total_pl_pct']:+.2f}%)")
    print(f"{'='*50}")

    # Показываем топ прибыли/убытка
    positions = sorted(summary['positions'], key=lambda x: x['pl'], reverse=True)
    print(f"\n🏆 Топ-5 прибыли:")
    for p in positions[:5]:
        print(f"  🟢 {p['ticker']}: ${p['pl']:+.2f} ({p['pl_pct']:+.2f}%)")
    print(f"\n🔻 Топ-5 убытка:")
    for p in positions[-5:]:
        print(f"  🔴 {p['ticker']}: ${p['pl']:+.2f} ({p['pl_pct']:+.2f}%)")

if __name__ == "__main__":
    main()