# Changelog — Open Interpreter

## [1.0.0] — 2026-08-13

### Добавлено
- **Оркестратор 24/7** (scripts/orchestrator.py): запуск всех сервисов по расписанию, launchd-агент для macOS
- **LLM Client** (shared/llm_client.py): tiered-роутинг, cost tracker, structured output, exponential backoff
- **HH Monitor**: парсинг HH.ru, авто-матчинг вакансий, генерация сопроводительных писем через Ollama
- **US Stocks Monitor**: мониторинг 9 тикеров через Yahoo Finance (free API)
- **UZ Stocks Monitor**: мониторинг Узбекской фондовой биржи (UZSE API + demo mode)
- **Events Monitor**: экономический календарь + Finviz новости
- **Finance Analytics**: еженедельный дайджест, анализ пассивного дохода, CSV-импорт
- **SQLite**: 8 таблиц (config, jobs, stock_signals, events, transactions, notifications, ai_skills)
- **Hermes интеграция**: уведомления через Telegram, send_hermes_message()
- **Multi-agent analyst**: Hermes-скилл для multi-agent аналитики
- **Docker**: Postgres контейнер (опционально)
- **Cost tracking**: лог каждого вызова LLM в costs.jsonl
- **Ollama**: локальная генерация через qwen3.5:4b
- **Pricing**: детальная таблица цен для 8 моделей OpenRouter

### Технический долг
- Нет unit-тестов
- Нет graceful shutdown (KeyboardInterrupt в цикле)
- Нет ротации логов
- Yahoo Finance — без API ключа, rate limit 0.5s между запросами
- UZSE API нестабилен (есть demo fallback с хардкоженными данными)
- Нет CI/CD