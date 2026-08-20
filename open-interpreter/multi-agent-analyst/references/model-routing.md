# Model Routing Reference

## Decision matrix for OpenRouter models

| Task type | Recommended model | Price ($/1M in) | When to use |
|-----------|-------------------|-----------------|-------------|
| **Классификация / Фильтрация** | `google/gemini-2.5-flash` | $0.05 | Быстрая проверка: "есть ли новые вакансии?", "стоит ли смотреть?" |
| **Сбор данных / Парсинг** | `deepseek/deepseek-chat` | $0.14 | Разбор HTML, JSON, извлечение структурированных данных |
| **Аналитика / Логика** | `deepseek/deepseek-chat` | $0.14 | Основной "рабочий конь": анализ акций, трендов, рекомендации |
| **Финансовые решения** | `anthropic/claude-sonnet-4-20250514` | $3.00 | Высокая точность, сложный контекст, финальная валидация |
| **Локальный фолбэк** | `ollama/qwen2.5:7b` (локально) | $0.00 | Фоновые задачи, черновики, тестирование |
| **Быстрый прототип** | `deepseek/deepseek-v4-flash` | $0.08 | Когда важна скорость, качество среднее |

## Prompt caching compatibility

| Model via OpenRouter | cache_control | Примечание |
|---------------------|---------------|------------|
| anthropic/claude-* | ✅ Да | Поддерживают `{"type": "ephemeral"}`. TTL ~5-10 мин |
| deepseek/* | ❌ Нет | Использовать client-side dedup |
| google/gemini-* | ❌ Нет | Слишком дёшево — кэш не нужен |
| qwen/* | ❌ Нет | — |

## Cost comparison: 10 agents × 500 in-tokens each

| Strategy | Input cost | Output cost | Total |
|----------|-----------|-------------|-------|
| Все на Claude Sonnet | 10×500×$3/1M = $0.015 | 10×200×$15/1M = $0.030 | **$0.045** |
| Все на DeepSeek | 10×500×$0.14/1M = $0.0007 | 10×200×$0.28/1M = $0.00056 | **$0.00126** |
| **Routing: Gemini→DeepSeek (1:3 ratio)** | ~$0.002 | ~$0.001 | **~$0.003** |
| **With caching (90% on context)** | ~$0.0002 | ~$0.001 | **~$0.0012** |

Худший сценарий (все Claude Sonnet) — $0.045 за 10 агентов.
Лучший сценарий (DeepSeek + caching) — $0.0012 за 10 агентов.
**Разница в 37×.**
