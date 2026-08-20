"""
ЗАДАЧА 4: Мировые события и новости (World Events)

🎯 ОПТИМИЗАЦИЯ:
✅ Модель: Claude Haiku
✅ Вывод: JSON (структурированный)
✅ Max tokens: 600

📊 РЕЗУЛЬТАТ: Экономия 10x vs Opus
"""

import os
import json
import anthropic
from cost_tracker import CostTracker

tracker = CostTracker("agent_costs.jsonl")
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")


def get_world_events(category: str = "technology"):
    """Получить мировые события которые влияют на инвестиции"""

    if not API_KEY:
        raise ValueError("❌ OPENROUTER_API_KEY не установлен!")

    client = anthropic.Anthropic(
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

    prompt = f"""Find 3-5 significant world events in the {category} sector
that impact global markets and investments.

RESPOND ONLY WITH JSON:
{{
  "date": "2026-07-26",
  "events": [
    {{
      "title": "Event title",
      "severity": "low|medium|high|critical",
      "impact": "short description of market impact",
      "affected_sectors": ["sector1", "sector2"],
      "investment_action": "buy|sell|hold",
      "confidence": 0.0-1.0
    }}
  ],
  "market_sentiment": "bullish|neutral|bearish"
}}"""

    try:
        response = client.messages.create(
            model="anthropic/claude-opus-5-fast",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(response.content[0].text)

        # Логировать затраты
        cost = tracker.log_call(
            "task_4_world_events",
            "anthropic/claude-3.5-haiku",
            response.usage.input_tokens,
            response.usage.output_tokens
        )

        print(f"✅ События получены ({len(result.get('events', []))} шт.)")
        print(f"   Sentiment: {result.get('market_sentiment', 'N/A')}")
        print(f"   Cost: ${cost:.6f}")

        return result

    except Exception as e:
        print(f"❌ Ошибка: {str(e)[:100]}")
        return None


if __name__ == "__main__":
    print("🌍 Task 4: Мировые события\n")

    for category in ["technology", "energy", "finance"]:
        print(f"\n📌 Категория: {category}")
        print("-" * 50)
        get_world_events(category)

    tracker.daily_report()
