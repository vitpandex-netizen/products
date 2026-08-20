# Graph Report - agents/  (2026-07-30)

## Corpus Check
- Corpus is ~7,223 words - fits in a single context window. You may not need a graph.

## Summary
- 145 nodes · 222 edges · 16 communities
- Extraction: 90% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.72)
- Token cost: 61,684 input · 0 output

## Community Hubs (Navigation)
- Cost Tracking
- Batch Processing & Caching
- README & Task Specs
- Prompt Optimization Techniques
- Batch Request Scheduling
- Prompt Optimizer Class
- Task Runner: USA Stocks
- Task 5: Education Courses
- Optimizer Config
- Run-All Orchestration
- Task 1: HH Jobs
- Task 6: Confidential Analysis
- Task 4: World Events
- Task 7: Passive Income
- Task 8: Finances
- Task 2: Local Stocks

## God Nodes (most connected - your core abstractions)
1. `CostTracker` - 16 edges
2. `Optimized System Prompt v2.0` - 15 edges
3. `Optimized Agents System README` - 14 edges
4. `CachingManager` - 12 edges
5. `run_all_tasks()` - 11 edges
6. `Per-Task Prompt Specs (Tasks 1-8)` - 9 edges
7. `run_all.py (Master Script)` - 9 edges
8. `BatchProcessor` - 8 edges
9. `Efficiency Metrics Table (token savings by technique)` - 7 edges
10. `generate_course_optimized()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Model Optimization Table (Task -> Model Before/After)` --semantically_similar_to--> `Efficiency Metrics Table (token savings by technique)`  [INFERRED] [semantically similar]
  README.md → OPTIMIZED_SYSTEM_PROMPT.md
- `optimizer_config.py (TASK_CONFIG)` --semantically_similar_to--> `Implementation Plan (SYSTEM_PROMPTS / OUTPUT_FORMATS dicts)`  [INFERRED] [semantically similar]
  README.md → OPTIMIZED_SYSTEM_PROMPT.md
- `cost_tracker.py (CostTracker)` --semantically_similar_to--> `Results After Implementation (tokens/cost/accuracy)`  [INFERRED] [semantically similar]
  README.md → OPTIMIZED_SYSTEM_PROMPT.md
- `BatchProcessor` --uses--> `CostTracker`  [INFERRED]
  batch_processor.py → cost_tracker.py
- `BatchProcessor` --uses--> `CachingManager`  [INFERRED]
  batch_processor.py → optimization_advanced.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Prompt Optimization Technique Set** — optimized_system_prompt_structuredoutput, optimized_system_prompt_rolespecificprompt, optimized_system_prompt_constraintspecification, optimized_system_prompt_fewshotexamples, optimized_system_prompt_chainofthought, optimized_system_prompt_templatebased [INFERRED 0.85]
- **Agent Cost Optimization Pipeline** — readme_cost_tracker, readme_optimizer_config, readme_model_optimization_table, optimized_system_prompt_results [INFERRED 0.80]
- **Multi-Task Agent Orchestration** — readme_run_all, readme_optimizer_config, readme_cost_tracker, readme_task_5_education [INFERRED 0.85]

## Communities (16 total, 0 thin omitted)

### Community 0 - "Cost Tracking"
Cohesion: 0.12
Nodes (11): CostTracker, Мониторинг расходов - отслеживание затрат по задачам, Логировать каждый вызов API, Вывести дневной отчёт по затратам, Вывести месячный суммарный отчёт, ЗАДАЧА 1: Поиск вакансий на HH (HH Jobs) 🎯 ОПТИМИЗАЦИЯ: ✅ Модель: Claude Sonnet…, ЗАДАЧА 2: Анализ локальных акций (Stocks Local) 🎯 ОПТИМИЗАЦИЯ: Claude Haiku,…, ЗАДАЧА 4: Мировые события и новости (World Events) 🎯 ОПТИМИЗАЦИЯ: ✅ Модель:… (+3 more)

### Community 1 - "Batch Processing & Caching"
Cohesion: 0.12
Nodes (9): BATCH API ПРОЦЕССОР - для асинхронных задач (50% экономия) Запускать ночью…, CachingManager, ПРОДВИНУТАЯ ОПТИМИЗАЦИЯ - Фаза 1 Экономия: -60% через кэширование + smart…, Загрузить кэш из файла, Получить кэшированный контекст для задачи, Проверить нужно ли обновить кэш, Выбрать оптимальную модель (smart routing), Залогировать что использован кэш (+1 more)

### Community 2 - "README & Task Specs"
Cohesion: 0.25
Nodes (18): Implementation Plan (SYSTEM_PROMPTS / OUTPUT_FORMATS dicts), Results After Implementation (tokens/cost/accuracy), Per-Task Prompt Specs (Tasks 1-8), Optimized Agents System README, cost_tracker.py (CostTracker), Model Optimization Table (Task -> Model Before/After), OPENROUTER_API_KEY Environment Variable, optimizer_config.py (TASK_CONFIG) (+10 more)

### Community 3 - "Prompt Optimization Techniques"
Cohesion: 0.18
Nodes (15): Optimized System Prompt v2.0, Anthropic's Prompt Best Practices, Chain-of-Thought Technique, Compact Core System Prompt (35 tokens), Constraint Specification Technique, DeepLearning.AI Short Courses (Prompt Engineering), Efficiency Metrics Table (token savings by technique), Few-Shot Examples Technique (+7 more)

### Community 4 - "Batch Request Scheduling"
Cohesion: 0.22
Nodes (5): BatchProcessor, Создать один запрос для батча, Добавить задачи в очередь на ночь, Получить расписание батчей, Показать стратегию оптимизации

### Community 5 - "Prompt Optimizer Class"
Cohesion: 0.20
Nodes (6): PromptOptimizer, ОПТИМИЗИРОВАННЫЕ СИСТЕМНЫЕ ПРОМПТЫ для всех 8 задач Версия 2.0 - минимум…, Получить ожидаемый формат вывода, Построить пользовательский промпт, Интеграция оптимизированных промптов, Получить оптимизированный системный промпт

### Community 6 - "Task Runner: USA Stocks"
Cohesion: 0.32
Nodes (5): Запустить Task 3 (US акции), run_task_3(), analyze_usa_stock(), ЗАДАЧА 3: Анализ американских акций (Stocks USA) 🎯 ОПТИМИЗАЦИЯ: Claude Haiku,…, Анализировать американскую акцию (Tech/Growth)

### Community 7 - "Task 5: Education Courses"
Cohesion: 0.32
Nodes (7): batch_generate_courses(), generate_course_optimized(), get_education_client(), ЗАДАЧА 5: Создание учебных материалов (Education) 🎯 ОПТИМИЗАЦИЯ: ✅ Модель:…, Генерировать несколько курсов и вывести отчёт, Клиент с правильной конфигурацией для OpenRouter, ✅ ОПТИМИЗИРОВАННАЯ версия задачи 5 (Обучение) Экономия: 10x (используем Haiku…

### Community 8 - "Optimizer Config"
Cohesion: 0.33
Nodes (5): get_model_for_task(), print_summary(), Конфигурация оптимизации - какая модель для какой задачи, Получить конфиг модели для задачи, Вывести сводку по оптимизации

### Community 9 - "Run-All Orchestration"
Cohesion: 0.40
Nodes (5): Запустить все 8 задач, Запустить Task 5 (обучение), run_all_tasks(), run_task_5(), show_welcome()

### Community 10 - "Task 1: HH Jobs"
Cohesion: 0.50
Nodes (4): Запустить Task 1 (HH Jobs), run_task_1(), match_job_and_create_application(), Анализировать вакансию и создать приложение (с опциональным кэшированием для…

### Community 11 - "Task 6: Confidential Analysis"
Cohesion: 0.50
Nodes (4): Запустить Task 6 (конфиденциальный анализ), run_task_6(), analyze_confidential_data(), Анализировать конфиденциальные финансовые данные (с высокой степенью защиты)

### Community 12 - "Task 4: World Events"
Cohesion: 0.50
Nodes (4): Запустить Task 4 (события), run_task_4(), get_world_events(), Получить мировые события которые влияют на инвестиции

### Community 13 - "Task 7: Passive Income"
Cohesion: 0.50
Nodes (4): Запустить Task 7 (пассивный доход), run_task_7(), generate_passive_income_ideas(), Генерировать идеи пассивного дохода

### Community 14 - "Task 8: Finances"
Cohesion: 0.50
Nodes (4): Запустить Task 8 (финансы), run_task_8(), analyze_finances(), Анализировать личные финансы и давать рекомендации

### Community 15 - "Task 2: Local Stocks"
Cohesion: 0.50
Nodes (4): Запустить Task 2 (локальные акции), run_task_2(), analyze_local_stock(), Анализировать локальную акцию (узбекские компании)

## Ambiguous Edges - Review These
- `cost_tracker.py (CostTracker)` → `OPENROUTER_API_KEY Environment Variable`  [AMBIGUOUS]
  README.md · relation: references

## Knowledge Gaps
- **7 isolated node(s):** `Real Before/After Example (200 to 35 tokens)`, `OpenAI Prompt Engineering Guide`, `Anthropic's Prompt Best Practices`, `DeepLearning.AI Short Courses (Prompt Engineering)`, `Lil'Log Blog (Prompt Techniques)` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `cost_tracker.py (CostTracker)` and `OPENROUTER_API_KEY Environment Variable`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `CostTracker` connect `Cost Tracking` to `Batch Processing & Caching`, `Batch Request Scheduling`, `Task Runner: USA Stocks`, `Task 5: Education Courses`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Why does `CachingManager` connect `Batch Processing & Caching` to `Batch Request Scheduling`, `Task 5: Education Courses`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Why does `BatchProcessor` connect `Batch Request Scheduling` to `Cost Tracking`, `Batch Processing & Caching`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `run_all_tasks()` (e.g. with `run_task_1()` and `run_task_2()`) actually correct?**
  _`run_all_tasks()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Real Before/After Example (200 to 35 tokens)`, `OpenAI Prompt Engineering Guide`, `Anthropic's Prompt Best Practices` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Cost Tracking` be split into smaller, more focused modules?**
  _Cohesion score 0.11688311688311688 - nodes in this community are weakly interconnected._