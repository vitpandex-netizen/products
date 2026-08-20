"""
ЗАДАЧА 7: Идеи пассивного дохода (Passive Income)

🎯 ОПТИМИЗАЦИЯ: Claude Haiku, JSON, 800 max_tokens
"""

import os
import json
import anthropic
from cost_tracker import CostTracker

tracker = CostTracker("agent_costs.jsonl")
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")


def generate_passive_income_ideas(initial_capital: float = 5000, risk_level: str = "medium"):
    """Генерировать идеи пассивного дохода"""

    if not API_KEY:
        raise ValueError("❌ OPENROUTER_API_KEY не установлен!")

    client = anthropic.Anthropic(
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

    prompt = f"""Generate 3-5 passive income ideas for someone with ${initial_capital} capital
and {risk_level} risk tolerance, located in Tashkent.

RESPOND ONLY WITH JSON:
{{
  "ideas": [
    {{
      "title": "Idea name",
      "initial_investment": number,
      "monthly_income": number,
      "time_to_profit": "months",
      "effort_level": "low|medium|high",
      "risks": ["risk1", "risk2"],
      "profitability_score": 0.0-1.0
    }}
  ],
  "best_idea": "title of best idea"
}}"""

    try:
        response = client.messages.create(
            model="anthropic/claude-opus-5-fast",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(response.content[0].text)

        cost = tracker.log_call(
            "task_7_passive_income",
            "anthropic/claude-3.5-haiku",
            response.usage.input_tokens,
            response.usage.output_tokens
        )

        print(f"✅ Идеи созданы ({len(result.get('ideas', []))} шт.)")
        print(f"   Лучшая: {result.get('best_idea', 'N/A')}")
        print(f"   Cost: ${cost:.6f}")

        return result

    except Exception as e:
        print(f"❌ Ошибка: {str(e)[:100]}")
        return None


if __name__ == "__main__":
    print("💰 Task 7: Пассивный доход\n")

    for capital in [5000, 10000, 50000]:
        print(f"\n💵 Капитал: ${capital}")
        print("-" * 50)
        generate_passive_income_ideas(capital)

    tracker.daily_report()
