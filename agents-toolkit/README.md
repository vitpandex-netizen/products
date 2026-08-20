# 🚀 Agents Toolkit

Исследовательский проект по AI-агентам и мульти-агентным системам. Набор оптимизированных агентов для финансового анализа, поиска вакансий, мониторинга событий и других задач.

**Статус:** 🟢 Активен  
**Модель по умолчанию:** Claude Opus 5 Fast (OpenRouter)

---

## Архитектура

```
agents-toolkit/
├── task_1_hh_jobs.py           # Поиск вакансий (HH.ru)
├── task_2_stocks_local.py      # Анализ локальных акций
├── task_3_stocks_usa.py        # Анализ US акций
├── task_4_world_events.py      # Мониторинг мировых событий
├── task_5_education.py         # Создание учебных материалов
├── task_6_confidential.py      # Конфиденциальный анализ портфеля
├── task_7_passive_income.py    # Идеи пассивного дохода
├── task_8_finances.py          # Финансовый анализ
├── run_all.py                  # Мастер-скрипт запуска
├── batch_processor.py          # Batch-обработка (cron)
├── cost_tracker.py             # Мониторинг затрат на API
├── optimizer_config.py         # Конфигурация моделей и стоимости
├── prompt_optimizer.py         # Оптимизация промптов
├── optimization_advanced.py    # Продвинутые техники (кэширование)
├── OPTIMIZED_SYSTEM_PROMPT.md  # Справочник по оптимизации
└── graphify-out/               # Экспорт графов задач
```

## Стек

| Компонент | Технология |
|-----------|-----------|
| Язык | Python 3.11+ |
| Модели | Claude Opus 5 Fast (OpenRouter) |
| API | OpenRouter API |
| Мониторинг | CostTracker (JSONL) |
| Планировщик | cron (batch_processor) |

## 8 Агентов

| № | Агент | Приоритет | Кэш | Описание |
|---|-------|-----------|-----|----------|
| 1 | HH Jobs | high | ✅ | Поиск вакансий, генерация сопроводительных |
| 2 | Stocks Local | medium | ❌ | Анализ узбекских акций |
| 3 | Stocks USA | medium | ❌ | Анализ американских акций (AAPL, GOOGL...) |
| 4 | World Events | low | ❌ | Мониторинг мировых новостей |
| 5 | Education | low | ❌ | Генерация учебных курсов |
| 6 | Confidential | critical | ✅ | Конфиденциальный анализ портфеля |
| 7 | Passive Income | low | ❌ | Идеи пассивного дохода |
| 8 | Finances | medium | ❌ | Финансовый анализ |

## Быстрый старт

### 1. Установить ключ

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

### 2. Запустить задачу

```bash
cd agents-toolkit
python3 task_5_education.py
```

### 3. Запустить всё сразу

```bash
python3 run_all.py all
```

### 4. Посмотреть затраты

```bash
python3 -c "from cost_tracker import CostTracker; CostTracker().daily_report()"
```

## Управление

```bash
# Запуск одной задачи
python3 run_all.py task_5

# Отчёт по всем задачам
python3 run_all.py report

# Batch-обработка (ночью)
python3 batch_processor.py

# Справка
python3 run_all.py help
```

## Мониторинг затрат

```bash
# Дневной отчёт
python3 -c "from cost_tracker import CostTracker; CostTracker().daily_report()"

# Месячный отчёт
python3 -c "from cost_tracker import CostTracker; CostTracker().monthly_summary()"

# Логи затрат
tail -20 agent_costs.jsonl
```

## Оптимизация

Проект включает систему оптимизации затрат на LLM:

| Техника | Экономия |
|---------|----------|
| Кэширование системных промптов | до 90% на повторных вызовах |
| Структурированный JSON output | -60% на парсинге |
| Компактные промпты | -82% токенов |
| Batch API (ночной запуск) | -50% |

**Модели сравнения:**
- **Claude Opus 5 Fast** — $0.01/$0.05 за млн токен (текущая, самая дешёвая)
- Claude Sonnet 3.5 — $3/$15 за млн токен
- Claude Haiku 3.5 — $0.80/$4 за млн токен

## Конфигурация

Все настройки в `optimizer_config.py`:

```python
TASK_CONFIG = {
    "task_5_education": {
        "model": "anthropic/claude-opus-5-fast",
        "max_tokens": 1000,
        "use_caching": False,
        "output_format": "json",
    }
}
```