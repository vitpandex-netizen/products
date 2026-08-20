# Open Interpreter — Локальный AI-ассистент с выполнением кода

> **Локальная AI-система с оркестрацией сервисов, мониторингом рынков и multi-agent аналитикой**

Open Interpreter — это Python-based AI-ассистент, работающий через OpenRouter и локальную Ollama. Система включает оркестратор 24/7, 5 микросервисов для мониторинга финансов, вакансий и событий, а также multi-agent аналитический модуль на Hermes-скиллах.

## Возможности

### 🕐 Оркестратор 24/7
- Запускает все сервисы по расписанию (launchd-агент macOS)
- Мониторит состояние Ollama и Hermes Gateway
- Автоматически перезапускает сервисы при сбоях
- Логирует каждый цикл в SQLite

### 📊 Сервисы мониторинга

| Сервис | Частота | Описание |
|--------|---------|----------|
| **HH Monitor** | 30 мин | Поиск вакансий Python-разработчика с автоматической генерацией сопроводительных писем через Ollama |
| **US Stocks** | 1 час | Мониторинг 9 тикеров (AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META, SPY, QQQ) через Yahoo Finance |
| **UZ Stocks** | 2 часа | Мониторинг Узбекской фондовой биржи (UZSE) |
| **Events Monitor** | 12 часов | Экономический календарь + новости рынков (Finviz, Investing.com) |
| **Finance Analytics** | 1 день | Еженедельный финансовый дайджест, анализ пассивного дохода |

### 🤖 Multi-Agent Analyst
- Аналитические агенты с tiered-роутингом моделей (fast → cheap → medium → heavy)
- Structured Output через Pydantic (гарантированный JSON)
- Cost tracker с пошаговым учётом каждого вызова
- Hermes-скиллы для расширения возможностей

## Стек

| Компонент | Технология |
|-----------|-----------|
| **Язык** | Python 3.11+ |
| **LLM Client** | OpenRouter API (OpenAI SDK) |
| **Локальная модель** | Ollama (qwen3.5:4b) |
| **База данных** | SQLite (WAL mode) |
| **Оркестрация** | launchd (macOS) / Python loop |
| **Модели OpenRouter** | Gemini 2.0 Flash, DeepSeek v4, Claude Sonnet 4 |
| **Уведомления** | Hermes Gateway → Telegram |
| **Контейнеризация** | Docker (Postgres — опционально) |

## Быстрый старт

```bash
# 1. Установка зависимостей
pip install -r requirements.txt

# 2. Настройка API ключа
export OPENROUTER_API_KEY="sk-or-v1-..."

# 3. Инициализация БД
python3 -c "from shared.db import init_db; init_db()"

# 4. Запуск оркестратора (однократный цикл)
python3 scripts/orchestrator.py

# 5. Или запуск в режиме 24/7
python3 scripts/orchestrator.py --loop
```

### Установка launchd-агента (автозапуск macOS)

```bash
cp scripts/com.interp.orchestrator.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.interp.orchestrator.plist
```

## Архитектура

```
open-interpreter/
├── shared/                      # Общий модуль
│   ├── db.py                   # SQLite: 8 таблиц (config, jobs, stock_signals, events, transactions, ...)
│   ├── utils.py                # notify(), get/set_config(), send_hermes_message(), format_salary()
│   └── llm_client.py           # OpenRouterClient: tiered routing, cost tracker, structured output
│
├── services/                    # Микросервисы (каждый запускается отдельно)
│   ├── hh-monitor/monitor.py   # Вакансии HH.ru + Ollama cover letters
│   ├── us-stocks/monitor.py    # US рынок (Yahoo Finance free API)
│   ├── uz-stocks/monitor.py    # UZ рынок (UZSE)
│   ├── events-monitor/monitor.py  # Экономические события
│   └── finance-analytics/agent.py  # Финансовая аналитика
│
├── scripts/                     # Инфраструктура
│   ├── orchestrator.py         # Главный оркестратор (цикл + расписание)
│   └── com.interp.orchestrator.plist  # launchd-агент для macOS
│
├── skills/                      # Hermes-скиллы
│   └── multi-agent-analyst/
│
├── multi-agent-analyst/         # Multi-agent аналитический модуль
│
├── docker/                      # Docker инфраструктура
│   └── docker-compose.yml      # Postgres (опционально)
│
├── data/                        # Данные runtime
│   ├── interp.db              # SQLite БД
│   ├── costs.jsonl            # Лог затрат на LLM
│   └── reports/               # Финансовые отчёты
│
├── logs/                        # Логи оркестратора
│
├── .interpreter-rules           # Правила для Hermes-контекста
└── README.md                    # ← текущий файл
```

## LLM Client (llm_client.py)

Единый production-клиент для OpenRouter с максимальной экономией:

| Tier | Модель | $/1M input | $/1M output | Max tokens |
|------|--------|------------|-------------|------------|
| **fast** | Gemini 2.0 Flash | $0.10 | $0.40 | 150 |
| **cheap** | DeepSeek v4 Flash | $0.07 | $0.30 | 300 |
| **medium** | DeepSeek Chat | $0.14 | $0.56 | 600 |
| **heavy** | Claude Sonnet 4 | $3.00 | $15.00 | 2000 |

Клиент поддерживает:
- **Structured Output** — принудительный JSON через Pydantic
- **Cascading Model Routing** — дешёвая модель для простых задач
- **Exponential Backoff Retry** — не долбит API при ошибках
- **Prompt Caching** — кэш системных промптов (OpenRouter)
- **Cost Tracker** — каждый вызов пишется в `data/costs.jsonl`
- **Temperature = 0.05** — стабильный JSON (почти детерминированный)

## База данных (SQLite)

| Таблица | Назначение |
|---------|-----------|
| `config` | Ключ-значение конфигурация |
| `jobs` | Вакансии HH.ru (с матчингом) |
| `stock_signals` | Сигналы по акциям (US + UZ) |
| `events` | Экономические события |
| `transactions` | Финансовые транзакции |
| `notifications` | Очередь уведомлений |
| `ai_skills` | Анализ навыков AI |
| `refresh_tokens` | (зарезервировано) |

## Система уведомлений

- Все сервисы отправляют уведомления через Hermes Gateway → Telegram
- High-impact события доставляются немедленно
- Финансовый дайджест — раз в неделю
- Найденные вакансии с автогенерацией сопроводительных писем