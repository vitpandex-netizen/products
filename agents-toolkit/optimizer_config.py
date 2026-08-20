"""
Конфигурация оптимизации - какая модель для какой задачи
"""

TASK_CONFIG = {
    "task_1_hh_jobs": {
        "model": "anthropic/claude-opus-5-fast",  # ✅ Работает
        "description": "Поиск вакансий HH",
        "max_tokens": 800,
        "use_caching": True,
        "output_format": "json",
        "priority": "high"
    },

    "task_2_stocks_local": {
        "model": "anthropic/claude-opus-5-fast",  # ✅ Работает
        "description": "Анализ локальных акций",
        "max_tokens": 500,
        "use_caching": False,
        "output_format": "json",
        "priority": "medium"
    },

    "task_3_stocks_usa": {
        "model": "anthropic/claude-opus-5-fast",  # ✅ Работает
        "description": "Анализ американских акций",
        "max_tokens": 500,
        "use_caching": False,
        "output_format": "json",
        "priority": "medium"
    },

    "task_4_world_events": {
        "model": "anthropic/claude-opus-5-fast",  # ✅ Работает
        "description": "Мировые события и новости",
        "max_tokens": 600,
        "use_caching": False,
        "output_format": "json",
        "priority": "low"
    },

    "task_5_education": {
        "model": "anthropic/claude-opus-5-fast",  # ✅ Работает
        "description": "Создание учебных материалов",
        "max_tokens": 1000,
        "use_caching": False,
        "output_format": "json",
        "priority": "low"
    },

    "task_6_confidential": {
        "model": "anthropic/claude-opus-5-fast",  # ✅ Работает
        "description": "Конфиденциальный анализ",
        "max_tokens": 2000,
        "use_caching": True,
        "output_format": "text",
        "priority": "critical"
    },

    "task_7_passive_income": {
        "model": "anthropic/claude-opus-5-fast",  # ✅ Работает
        "description": "Идеи пассивного дохода",
        "max_tokens": 800,
        "use_caching": False,
        "output_format": "json",
        "priority": "low"
    },

    "task_8_finances": {
        "model": "anthropic/claude-opus-5-fast",  # ✅ Работает
        "description": "Финансовый анализ",
        "max_tokens": 600,
        "use_caching": False,
        "output_format": "json",
        "priority": "medium"
    }
}

# МАТРИЦА ПЕРЕКЛЮЧЕНИЙ
SWITCHING_GUIDE = """
┌─────────────────────────────────────────────────────────────┐
│  МАТРИЦА ОПТИМИЗАЦИИ: Какую модель использовать            │
├─────────────────────────────────────────────────────────────┤
│  💎 Claude Opus 5 Fast                                      │
│     → Task 6 (Конфиденциальные данные)                      │
│     → Когда: максимум качества, надёжности                  │
│     → Цена: $0.01/$0.05 за млн токен (самый дешевый!)      │
│                                                               │
│  ⚡ Claude Sonnet 3.5                                       │
│     → Task 1 (HH - нужна скорость)                           │
│     → Когда: баланс между скоростью и качеством             │
│     → Цена: $3/$15 за млн токен                             │
│                                                               │
│  🚀 Claude Haiku 3.5                                        │
│     → Tasks 2,3,4,5,7,8 (остальное)                          │
│     → Когда: простые задачи, структурированный вывод        │
│     → Цена: $0.80/$4 за млн токен                           │
└─────────────────────────────────────────────────────────────┘
"""

# РЕКОМЕНДАЦИИ ПО КЭШИРОВАНИЮ
CACHING_GUIDE = """
┌─────────────────────────────────────────────────────────────┐
│  КЭШИРОВАНИЕ: экономия 90% на системных промптах            │
├─────────────────────────────────────────────────────────────┤
│  ✅ ИСПОЛЬЗУЙТЕ кэш когда:                                  │
│     • Большой системный промпт (>500 токен)                 │
│     • Вызовы повторяются (одна задача много раз)            │
│     • Контекст не меняется между вызовами                   │
│                                                               │
│  ❌ НЕ используйте кэш когда:                               │
│     • Первый и единственный вызов                           │
│     • Быстро меняющийся контекст                            │
│     • Контекст < 500 токенов                                │
└─────────────────────────────────────────────────────────────┘
"""

# ФИНАНСОВЫЙ РАСЧЁТ
COST_ANALYSIS = {
    "per_million_tokens": {
        "claude-opus-5-fast": {"input": 0.01, "output": 0.05},
        "claude-3.5-sonnet": {"input": 3, "output": 15},
        "claude-3.5-haiku": {"input": 0.80, "output": 4},
        "deepseek-chat": {"input": 0.14, "output": 0.56},
    },
    "estimated_monthly_volume": {
        "task_1_hh_jobs": 100,           # 100 вызовов в день × 30
        "task_2_stocks_local": 30,
        "task_3_stocks_usa": 30,
        "task_4_world_events": 50,
        "task_5_education": 20,
        "task_6_confidential": 10,
        "task_7_passive_income": 40,
        "task_8_finances": 60,
    }
}


def get_model_for_task(task_id: str) -> dict:
    """Получить конфиг модели для задачи"""
    return TASK_CONFIG.get(task_id, TASK_CONFIG["task_5_education"])


def print_summary():
    """Вывести сводку по оптимизации"""
    print(SWITCHING_GUIDE)
    print(CACHING_GUIDE)
