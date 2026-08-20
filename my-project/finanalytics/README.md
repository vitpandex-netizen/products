# FinAnalytics — Финансовый Агент

Персональный финансовый агент для ведения финансов, анализа расходов, доходов и финансового планирования.

## 📋 Функционал

- 💳 Отслеживание транзакций и расходов
- 📊 Анализ финансового состояния
- 🎯 Финансовые цели и планирование
- 📈 Прогнозирование доходов/расходов
- 💡 Рекомендации по оптимизации расходов
- 🔗 Интеграция с данными из stocks-ru и stocks-us

## 🚀 Быстрый старт

```bash
cd finanalytics
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python src/main.py
```

## 📁 Структура

```
finanalytics/
├── src/
│   ├── main.py
│   ├── wallet.py           # Управление кошельками/счётами
│   ├── transactions.py     # Работа с транзакциями
│   ├── analytics.py        # Аналитика и отчёты
│   ├── goals.py            # Финансовые цели
│   └── portfolio.py        # Портфель инвестиций
├── tests/
├── data/
│   └── finances.db
├── requirements.txt
├── .env.example
└── README.md
```

## 📊 Основные метрики

- Общие активы
- Месячные расходы по категориям
- Коэффициент сбережений
- Баланс инвестиций
- Прогноз финансового состояния

## 🔗 Интеграция

- `stocks-ru` и `stocks-us` — портфель инвестиций
- `shared/models.py` — стандартные модели данных
- `market-events` — влияние новостей на портфель

## 📚 Примеры

### Добавить транзакцию

```python
from src.wallet import Wallet

wallet = Wallet(user_id=1)
wallet.add_transaction(
    amount=1000,
    category="Groceries",
    description="Супермаркет",
    date=datetime.now()
)
```

### Получить отчёт

```python
from src.analytics import Analytics

analytics = Analytics(user_id=1)
report = analytics.get_monthly_report()
print(report)
```

---

**Статус:** 🟡 Планируется

**Участники:** TBD

**Последнее обновление:** 2026-07-26
