# STATUS — Open Interpreter

> **Дата**: 13 августа 2026
> **Версия**: v1.0.0
> **Git**: не инициализирован

---

## Общий статус

| Область | Статус | Детали |
|---------|--------|--------|
| **Orchestrator** | ✅ | Работает 24/7 через launchd, циклический запуск с интервальным контролем |
| **LLM Client** | ✅ | Tiered routing, Structured Output, Cost Tracker, Retry |
| **HH Monitor** | ✅ | Парсинг HH.ru, матчинг, Ollama cover letters |
| **US Stocks** | ✅ | Yahoo Finance, 9 тикеров, сигналы oversold/dip |
| **UZ Stocks** | ✅ | UZSE API + demo fallback |
| **Events Monitor** | ✅ | Finviz + economic calendar, high-impact alerts |
| **Finance Analytics** | ✅ | Monthly reports, passive income analysis, CSV import |
| **SQLite** | ✅ | 8 таблиц, WAL mode, инициализация через init_db() |
| **Hermes Gateway** | ✅ | Уведомления в Telegram |
| **Tests** | ❌ | Отсутствуют |
| **CI/CD** | ❌ | Отсутствуют |
| **Git** | ❌ | Репозиторий не инициализирован |

---

## Анализ кода

| Параметр | Значение |
|----------|----------|
| Файлов Python | 10 |
| Общий код | ~1,420 строк |
| Сервисов | 5 активных + 3 запланированных |
| Таблиц БД | 8 |
| Моделей OpenRouter | 8 (с ценами) |
| Tiers | 4 (fast, cheap, medium, heavy) |

### Структура кода

```
shared/          (3 файла, 586 строк)
  ├── db.py           — SQLite, 8 таблиц
  ├── utils.py        — notify, config, send_hermes_message
  └── llm_client.py   — OpenRouterClient (420 строк)

services/        (5 сервисов, ~620 строк)
  ├── hh-monitor/monitor.py          — 140 строк
  ├── us-stocks/monitor.py           — 129 строк
  ├── uz-stocks/monitor.py           — 92 строки
  ├── events-monitor/monitor.py      — 114 строк
  └── finance-analytics/agent.py     — 190 строк

scripts/         (2 файла, 216 строк)
  ├── orchestrator.py                — 183 строки
  └── com.interp.orchestrator.plist  — launchd config
```

---

## Сервисы: детальный статус

### HH Monitor
- **Источник**: HH.ru API (бесплатный)
- **Частота**: каждые 30 минут
- **Статус**: ✅ Работает
- **Матчинг**: 2+ ключевых слова из списка → вакансия помечается matched
- **Ollama**: генерация cover letters через qwen3.5:4b
- **Риски**: HH.ru может изменить API

### US Stocks
- **Источник**: Yahoo Finance (free, без API ключа)
- **Тикеры**: AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META, SPY, QQQ
- **Статус**: ✅ Работает
- **Сигналы**: oversold (< -3%), dip (< -1%), overbought (> +5%)
- **Риски**: Yahoo может заблокировать без User-Agent

### UZ Stocks
- **Источник**: UZSE API (нестабилен)
- **Статус**: ⚠️ Работает с demo fallback
- **Demo данные**: UZMK, KVAZ, IPAK (хардкоженные)
- **Риски**: UZSE API часто недоступен

### Events Monitor
- **Источники**: Finviz, Investing.com, Financial Modeling Prep
- **Статус**: ✅ Работает
- **Категории**: economics, markets

### Finance Analytics
- **Статус**: ✅ Работает
- **Команды**: weekly, report, passive
- **Функции**: CSV-импорт, ежемесячные отчёты, анализ пассивного дохода

---

## Cost Tracking

Файл: `data/costs.jsonl`

Формат записи:
```json
{
  "ts": "2026-08-13T10:00:00",
  "agent": "hh_parser",
  "model": "deepseek/deepseek-chat",
  "tier": "cheap",
  "tokens": {"input": 450, "output": 120, "cached": 200},
  "cost": 0.000042,
  "latency": 1.23,
  "success": true
}
```

Отчёт за N дней: `python3 -c "from shared.llm_client import print_cost_report; print_cost_report(7)"`

---

## Инфраструктура

| Компонент | Статус | Детали |
|-----------|--------|--------|
| launchd-агент | ✅ | Загружен, автозапуск, KeepAlive |
| Ollama | ✅ | qwen3.5:4b (pull при первом запуске) |
| Hermes Gateway | ✅ | localhost:20128 |
| Postgres Docker | 🟡 | Опционально (docker-compose.yml) |
| SQLite backup | ❌ | Нет |
| Мониторинг | ❌ | Нет |

---

## Ближайшие шаги

1. Инициализировать git-репозиторий
2. Добавить graceful shutdown для оркестратора
3. Настроить ротацию логов
4. Написать тесты для shared модулей
5. Добавить веб-дашборд состояния сервисов