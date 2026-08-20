---
name: multi-agent-analyst
description: >
  Orchestrate multiple sub-agents with a shared system context for parallel analysis,
  data extraction, monitoring, and decision-making tasks. Use when the user needs to:
  (1) Run the same analysis template across many tickers/sources/entities,
  (2) Decompose a complex question into parallel research tasks with structured JSON output,
  (3) Monitor multiple streams (jobs, stocks, news) with confidence-threshold filtering,
  (4) Apply cost-aware model routing (cheap models for classification, expensive ones for
  final decisions), (5) Track token usage and estimate costs across agent turns, or
  (6) Build a reusable multi-agent analysis pipeline with prompt caching for shared context.
  Designed for OpenRouter-based model access with cost optimisation.
metadata:
  short-description: Run parallel sub-agents with shared context, JSON output, and cost tracking
---

# Multi-Agent Analyst

Система для параллельного запуска нескольких агентов-аналитиков с единым контекстом,
структурированным JSON-выходом, confidence-фильтрацией и трекингом затрат.

## Когда использовать

- **Параллельный анализ**: Один и тот же анализ по N сущностям (акции, вакансии, новости)
- **Мониторинг**: Проверка нескольких источников с порогом уверенности
- **Экономия токенов**: Один системный контекст → много агентов (prompt caching / fork_context)
- **Routing**: Дешёвая модель для фильтрации, дорогая для финального решения

## Принципы

| Принцип | Как применять |
|---------|--------------|
| **Shared context** | Общий промпт (правила, схемы, ограничения) задаётся 1 раз → наследуется всеми sub-agent'ами |
| **JSON output** | Все агенты отвечают строго JSON. Без рассуждений, без лишнего текста |
| **Confidence filter** | Если `confidence < 0.7` → агент помечается как `SKIP` / `low_confidence` |
| **Model routing** | Tier 1 (классификация/сбор): Gemini Flash / Qwen. Tier 2 (логика/решения): DeepSeek / Claude |
| **Cost tracking** | Каждый вызов логирует токены, кэш, затраты |
| **max_tokens discipline** | Жёсткое ограничение output. JSON должен влезать в лимит |

## Встроенные скрипты и файлы

### `scripts/optimized_agent_router.py`

Готовый Python-модуль для вызова моделей через OpenRouter SDK с:
- Prompt caching (`cache_control` для Anthropic-моделей)
- Structured Output (strict JSON + fallback от ```json блоков)
- Cascading model routing (Tier 1 → Tier 2)
- Cost & latency tracker (таблица с токенами, кэшем, затратами)
- Confidence-фильтрация и SKIP-логика

```python
from scripts.optimized_agent_router import OptimizedAgentRouter

router = OptimizedAgentRouter()

# Общий системный контекст — загружается 1 раз
CONTEXT = """
Ты финансовый аналитик. Анализируй данные и выдавай JSON:
{"action": "buy|sell|skip", "ticker": str, "confidence": float, "reason": str}
Правила: confidence >= 0.7 → action, иначе skip.
"""

# Запуск N агентов с одним контекстом
results = []
for ticker in ["AAPL", "TSLA", "GOOGL"]:
    r = router.execute(
        agent_id=f"analyst_{ticker}",
        system_prompt=CONTEXT,
        user_input=f"Проанализируй {ticker} на основе последних новостей",
        model="deepseek/deepseek-chat",
        max_tokens=300,
        enable_cache=True,
        temperature=0.1
    )
    if r and r.get("confidence", 0) >= 0.7:
        results.append(r)

router.print_report()
```

### `requirements.txt`

```txt
openai>=1.0.0
```

### `scripts/setup.sh`

Скрипт быстрой установки: создаёт venv, ставит зависимости.

### `references/model-routing.md`

Справочник по моделям, ценам и поддержке кэширования.

### `agents/openai.yaml`

UI-метаданные для отображения в списке скиллов.

## Рабочий процесс

### Шаг 1: Определить общий контекст

Выдели то, что одинаково для всех агентов:
- Роль / persona
- Правила анализа
- JSON-схема ответа
- Константы (лимиты, таймзона, пороги)

### Шаг 2: Составить специфичные запросы

Каждый агент получает только то, что меняется:
- Разный тикер / источник / период
- Свой `agent_id` для трекинга

### Шаг 3: Выбрать модель для каждого агента

| Задача | Модель | Почему |
|--------|--------|--------|
| Сбор/классификация | `google/gemini-2.5-flash` | Дёшево, быстро |
| Аналитика/логика | `deepseek/deepseek-chat` | Качество DeepSeek V3 по цене 1/10 Claude |
| Финальное решение | `anthropic/claude-sonnet-4` | Максимальная точность для сложного контекста |

### Шаг 4: Запустить и собрать результаты

Все агенты запускаются с `fork_context=true` (наследуют контекст).
Каждый возвращает JSON. Отфильтровать по confidence.

### Шаг 5: Проверить cost report

После всех вызовов вызвать `router.print_report()` чтобы увидеть:
- Сколько токенов сэкономлено через кэш
- Средняя задержка на агента
- Какие агенты самые дорогие

## Model caching notes

- **Anthropic-модели через OpenRouter**: поддерживают `cache_control: {"type": "ephemeral"}` в system-блоке. Кэш живёт 5-10 минут. Если агенты запускаются реже — кэш «холодный».
- **DeepSeek через OpenRouter**: `cache_control` не поддерживается. Экономия только через client-side кэш (см. `OptimizedAgentRouter`).
- **Gemini Flash**: крайне дёшев (≈$0.05/1M input) — кэширование не нужно.
- **fork_context** в Interpreter: полный аналог prompt caching — контекст родителя наследуется без повторной загрузки.

## JSON schema convention

Все агенты следуют единому формату ответа:

```json
{
  "status": "success|error|skip",
  "action": "buy|sell|hold|notify|skip",
  "confidence": 0.0-1.0,
  "data": {},
  "reason": "string"
}
```

Если `confidence < 0.7` → status = "skip". Если ошибка → status = "error".

## Ошибки и обработка

| Ситуация | Что делать |
|----------|-----------|
| JSONDecodeError | Проверить `max_tokens`. Если модель обрезала JSON — увеличить лимит |
| Cache miss | Проверить интервал между вызовами. Нужно <5 мин для cache hit |
| timeout | Уменьшить модель до Tier 1 или снизить `max_tokens` |
| Все SKIP | Поднять confidence threshold или сменить модель на более качественную |
| Ошибка API | Проверить `OPENROUTER_API_KEY`, баланс, лимиты модели |

## Быстрый старт

```bash
# 1. Установить зависимости
cd multi-agent-analyst
bash scripts/setup.sh

# 2. Установить API-ключ
export OPENROUTER_API_KEY="sk-or-v1-..."

# 3. Запустить демо
.venv/bin/python scripts/optimized_agent_router.py
```
