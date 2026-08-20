"""
Мониторинг расходов - отслеживание затрат по задачам
"""
from datetime import datetime
import json
import os

class CostTracker:
    def __init__(self, log_file="agent_costs.jsonl"):
        self.log_file = log_file

    def log_call(self, task_id: str, model: str, input_tokens: int, output_tokens: int):
        """Логировать каждый вызов API"""

        # ЦЕНЫ (за миллион токенов)
        prices = {
            "anthropic/claude-opus-5-fast": {"input": 0.01, "output": 0.05},
            "anthropic/claude-opus-5": {"input": 0.005, "output": 0.025},
            "anthropic/claude-3.5-sonnet": {"input": 3, "output": 15},
            "anthropic/claude-3.5-haiku": {"input": 0.80, "output": 4},
            "deepseek-chat": {"input": 0.14, "output": 0.56},
        }

        price = prices.get(model, {"input": 0.14, "output": 0.56})
        input_cost = (input_tokens * price["input"]) / 1_000_000
        output_cost = (output_tokens * price["output"]) / 1_000_000
        total_cost = input_cost + output_cost

        # ЛОГИРОВАТЬ В ФАЙЛ
        entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return total_cost

    def daily_report(self):
        """Вывести дневной отчёт по затратам"""

        if not os.path.exists(self.log_file):
            print("❌ Нет логов затрат")
            return

        # Прочитать все строки за сегодня
        today = datetime.now().strftime("%Y-%m-%d")
        tasks_cost = {}
        total_cost = 0
        total_calls = 0

        with open(self.log_file, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry["timestamp"].startswith(today):
                        task_id = entry["task_id"]
                        cost = entry["total_cost"]

                        if task_id not in tasks_cost:
                            tasks_cost[task_id] = {"cost": 0, "calls": 0, "tokens": 0}

                        tasks_cost[task_id]["cost"] += cost
                        tasks_cost[task_id]["calls"] += 1
                        tasks_cost[task_id]["tokens"] += entry["input_tokens"] + entry["output_tokens"]
                        total_cost += cost
                        total_calls += 1
                except json.JSONDecodeError:
                    pass

        # ВЫВЕСТИ ОТЧЁТ
        print(f"\n{'='*80}")
        print(f"💰 ДНЕВНОЙ ОТЧЁТ ЗАТРАТ — {today}")
        print(f"{'='*80}")
        print(f"{'Task ID':<30} {'Calls':<8} {'Tokens':<12} {'Cost':<15}")
        print(f"{'-'*80}")

        for task_id in sorted(tasks_cost.keys()):
            data = tasks_cost[task_id]
            print(f"{task_id:<30} {data['calls']:<8} {data['tokens']:<12} ${data['cost']:<14.6f}")

        print(f"{'-'*80}")
        print(f"{'ИТОГО':<30} {total_calls:<8} {'':<12} ${total_cost:<14.6f}")
        print(f"{'='*80}\n")

        return total_cost

    def monthly_summary(self):
        """Вывести месячный суммарный отчёт"""

        if not os.path.exists(self.log_file):
            return None

        models_cost = {}
        total_cost = 0

        with open(self.log_file, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    model = entry["model"]
                    cost = entry["total_cost"]

                    if model not in models_cost:
                        models_cost[model] = {"cost": 0, "calls": 0}

                    models_cost[model]["cost"] += cost
                    models_cost[model]["calls"] += 1
                    total_cost += cost
                except:
                    pass

        print(f"\n{'='*80}")
        print(f"📊 МЕСЯЧНЫЙ ОТЧЁТ")
        print(f"{'='*80}")
        print(f"{'Model':<40} {'Calls':<10} {'Cost':<15}")
        print(f"{'-'*80}")

        for model in sorted(models_cost.keys()):
            data = models_cost[model]
            print(f"{model:<40} {data['calls']:<10} ${data['cost']:<14.6f}")

        print(f"{'-'*80}")
        print(f"{'ИТОГО':<40} {'':<10} ${total_cost:<14.6f}")
        print(f"{'='*80}\n")

        return total_cost
