# Changelog: Agents Toolkit

## [0.1.0] — 2026-08-13

### Добавлено
- Первая стабильная версия Agents Toolkit
- 8 агентов: HH Jobs, Stocks Local/USA, World Events, Education, Confidential, Passive Income, Finances
- `run_all.py` — мастер-скрипт для запуска одной или всех задач
- `cost_tracker.py` — мониторинг затрат на OpenRouter API
- `optimizer_config.py` — конфигурация моделей с матрицей переключения
- `prompt_optimizer.py` — инструмент оптимизации промптов
- `optimization_advanced.py` — продвинутое кэширование системных промптов
- `batch_processor.py` — batch-обработка для ночного запуска через cron
- `OPTIMIZED_SYSTEM_PROMPT.md` — справочник по техникам оптимизации
- Оптимизация: компактные промпты (-82%), JSON output (-60%), кэширование (до 90%)
- Все задачи используют Claude Opus 5 Fast через OpenRouter