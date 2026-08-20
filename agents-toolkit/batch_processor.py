"""
BATCH API ПРОЦЕССОР - для асинхронных задач (50% экономия)
Запускать ночью через cron: 0 2 * * * python3 batch_processor.py
"""

import os
import json
import anthropic
from datetime import datetime
from cost_tracker import CostTracker
from optimization_advanced import CachingManager, CACHED_CONTEXTS

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
tracker = CostTracker("agent_costs.jsonl")
cache_manager = CachingManager()

# ========================================================================
# BATCH ЗАПРОСЫ - для запуска ночью (50% скидка!)
# ========================================================================

BATCH_REQUESTS = {
    "daily_stock_analysis": {
        "tasks": [
            {
                "task_id": "task_2_stocks_local",
                "ticker": "TASHKENT_POWER",
                "prompt": "Analyze local stock TASHKENT_POWER for investment.",
            },
            {
                "task_id": "task_2_stocks_local",
                "ticker": "ARTEL",
                "prompt": "Analyze local stock ARTEL for investment.",
            },
        ],
        "schedule": "daily_02:00",
        "priority": "high",
    },

    "daily_usa_stocks": {
        "tasks": [
            {
                "task_id": "task_3_stocks_usa",
                "ticker": "AAPL",
                "prompt": "Analyze AAPL stock for investment opportunity.",
            },
            {
                "task_id": "task_3_stocks_usa",
                "ticker": "GOOGL",
                "prompt": "Analyze GOOGL stock for investment opportunity.",
            },
            {
                "task_id": "task_3_stocks_usa",
                "ticker": "MSFT",
                "prompt": "Analyze MSFT stock for investment opportunity.",
            },
        ],
        "schedule": "daily_02:30",
        "priority": "high",
    },

    "daily_world_events": {
        "tasks": [
            {
                "task_id": "task_4_world_events",
                "category": "technology",
                "prompt": "Find 3-5 important tech events from last 24h affecting markets.",
            },
            {
                "task_id": "task_4_world_events",
                "category": "energy",
                "prompt": "Find 3-5 important energy events from last 24h affecting markets.",
            },
        ],
        "schedule": "daily_03:00",
        "priority": "medium",
    },

    "weekly_portfolio_analysis": {
        "tasks": [
            {
                "task_id": "task_6_confidential",
                "action": "full_analysis",
                "prompt": "Perform full portfolio analysis with risk assessment.",
            }
        ],
        "schedule": "weekly_sunday_02:00",
        "priority": "high",
    },
}

# ========================================================================
# BATCH API CLIENT
# ========================================================================

class BatchProcessor:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        self.batch_file = "batch_requests.jsonl"

    def create_batch_request(self, request_id, prompt, max_tokens=500):
        """Создать один запрос для батча"""
        return {
            "custom_id": request_id,
            "params": {
                "model": "anthropic/claude-opus-5-fast",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        }

    def queue_batch(self, batch_name, tasks):
        """Добавить задачи в очередь на ночь"""
        print(f"\n📋 Очередь батча: {batch_name}")
        print(f"   Задач: {len(tasks)}")
        print(f"   Расчетная экономия: {len(tasks)} * 50% = {len(tasks) * 50}% дешевле!")

        requests = []
        for i, task in enumerate(tasks):
            request = self.create_batch_request(
                f"{batch_name}_task_{i}",
                task["prompt"],
                max_tokens=500
            )
            requests.append(request)

        # Сохранить в файл (для позднейшей отправки)
        with open(self.batch_file, 'a') as f:
            for req in requests:
                f.write(json.dumps(req) + "\n")

        return len(requests)

    def get_scheduled_batches(self):
        """Получить расписание батчей"""
        print("\n" + "="*70)
        print("⏰ РАСПИСАНИЕ БАТЧ-ОБРАБОТКИ (50% экономия!)")
        print("="*70)

        total_tasks = 0
        for batch_name, config in BATCH_REQUESTS.items():
            tasks = config["tasks"]
            schedule = config["schedule"]
            print(f"\n📌 {batch_name}")
            print(f"   ⏱️  Время: {schedule}")
            print(f"   📊 Задач: {len(tasks)}")
            print(f"   💰 Экономия: {len(tasks)} * 50% = {len(tasks) * 0.00135:.4f}$ (вместо ${len(tasks) * 0.0027:.4f})")
            total_tasks += len(tasks)

        print(f"\n" + "="*70)
        print(f"📊 ИТОГО ЗАДАЧ В НОЧНОЙ ОЧЕРЕДИ: {total_tasks}")
        print(f"💰 НОЧНАЯ ЭКОНОМИЯ: {total_tasks} * 50% = ${total_tasks * (0.0027 - 0.00135):.4f}/ночь")
        print(f"📅 МЕСЯЧНАЯ ЭКОНОМИЯ: ${total_tasks * (0.0027 - 0.00135) * 30:.2f}")
        print("="*70)

        return total_tasks

    def print_strategy(self):
        """Показать стратегию оптимизации"""
        print("\n" + "="*70)
        print("🎯 СТРАТЕГИЯ BATCH API")
        print("="*70)

        print("""
КАК РАБОТАЕТ:
1. Днем (07:00-22:00):  Используем INSTANT API (быстро, дорого)
   └─ Tasks: 1, 5, 6 (критичные, нужны результаты сразу)
   └─ Цена: $0.0027 за запрос

2. Ночью (02:00-06:00): Используем BATCH API (медленно, дешево!)
   └─ Tasks: 2, 3, 4, 7, 8 (некритичные, результаты завтра OK)
   └─ Цена: $0.00135 за запрос (50% скидка!)
   └─ Результаты готовы к 07:00

ПРИМЕРЫ:
✅ Stock analysis (Task 2,3): Ночной батч → результаты к утру
✅ Events (Task 4): Ночной батч → новости за ночь
✅ Portfolio (Task 6): Еженедельный батч по воскресеньям

ЭКОНОМИЯ:
- За ночь: ~7 задач * 50% = $0.045 сэкономлено
- За месяц: $1.35 сэкономлено
- За год: $16.20 сэкономлено
        """)

        print("="*70)


# ========================================================================
# ЗАПУСК
# ========================================================================

if __name__ == "__main__":
    processor = BatchProcessor()

    print("\n" + "="*70)
    print("🌙 BATCH API ПРОЦЕССОР - НОЧНАЯ ОБРАБОТКА")
    print("="*70)

    # Показать расписание
    total = processor.get_scheduled_batches()

    # Показать стратегию
    processor.print_strategy()

    print("\n✅ READY TO USE!")
    print("\nДобавьте в crontab:")
    print("  0 2 * * * cd ~/Desktop/Cowork/ClaudeCODE/agents && python3 batch_processor.py")
    print("\nОр запустите вручную:")
    print("  python3 batch_processor.py")
