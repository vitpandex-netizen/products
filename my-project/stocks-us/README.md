# Stocks US — Анализ рынка акций США

Агент для отслеживания, анализа и рекомендаций по ценным бумагам на американском рынке (S&P 500, NASDAQ).

## 📋 Функционал

- 📊 Отслеживание котировок S&P 500, NASDAQ
- 🔍 Анализ акций, ETF, криптовалют
- 💡 Рекомендации "Buy/Sell/Hold"
- 📰 Интеграция с новостями (market-events)
- 💰 Расчёт потенциальной прибыли

## 🚀 Быстрый старт

```bash
cd stocks-us
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python src/main.py
```

## 📁 Структура

```
stocks-us/
├── src/
│   ├── main.py
│   ├── yfinance_parser.py   # Yahoo Finance API
│   ├── analyzer.py          # Анализ акций
│   ├── alerts.py            # Оповещения
│   └── recommendations.py   # Рекомендации
├── tests/
├── data/
│   └── stocks-us.db
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 Данные

Источники:
- Yahoo Finance (yfinance)
- Alpha Vantage API (бесплатный tier)
- Finnhub API (опционально)

## 💾 Интеграция

Использует `shared/models.py` для стандартизации.
Координирует с `market-events` для анализа влияния новостей.

---

**Статус:** 🟡 Планируется

**Участники:** TBD

**Последнее обновление:** 2026-07-26
