"""
ЗАДАЧА 8: Финансовый анализ (Finances)

🎯 ОПТИМИЗАЦИЯ: Claude Haiku, JSON, 600 max_tokens
"""

import os
import json
import anthropic
from cost_tracker import CostTracker

tracker = CostTracker("agent_costs.jsonl")
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")


def analyze_finances(monthly_income: float, expenses: dict = None):
    """Анализировать личные финансы и давать рекомендации"""

    if not API_KEY:
        raise ValueError("❌ OPENROUTER_API_KEY не установлен!")

    if expenses is None:
        expenses = {"rent": 1000, "food": 400, "transport": 200, "entertainment": 300}

    client = anthropic.Anthropic(
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

    expenses_str = ", ".join([f"{k}: ${v}" for k, v in expenses.items()])

    prompt = f"""Analyze personal finances and provide recommendations.
Monthly income: ${monthly_income}
Expenses: {expenses_str}

RESPOND ONLY WITH JSON:
{{
  "total_expenses": number,
  "savings_potential": number,
  "savings_rate_percent": number,
  "financial_health": "poor|fair|good|excellent",
  "recommendations": [
    {{
      "category": "string",
      "action": "string",
      "potential_savings": number
    }}
  ],
  "emergency_fund_months": number
}}"""

    try:
        response = client.messages.create(
            model="anthropic/claude-opus-5-fast",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(response.content[0].text)

        cost = tracker.log_call(
            "task_8_finances",
            "anthropic/claude-3.5-haiku",
            response.usage.input_tokens,
            response.usage.output_tokens
        )

        print(f"✅ Анализ завершен")
        print(f"   Здоровье: {result.get('financial_health', 'N/A')}")
        print(f"   Сбережения: ${result.get('savings_potential', 0):.0f}/мес")
        print(f"   Cost: ${cost:.6f}")

        return result

    except Exception as e:
        print(f"❌ Ошибка: {str(e)[:100]}")
        return None


if __name__ == "__main__":
    print("💳 Task 8: Финансовый анализ\n")

    incomes = [3000, 5000, 8000]

    for income in incomes:
        print(f"\n💰 Доход: ${income}/месяц")
        print("-" * 50)
        analyze_finances(income)

    tracker.daily_report()
