"""
ЗАДАЧА 2: Анализ локальных акций (Stocks Local)

🎯 ОПТИМИЗАЦИЯ: Claude Haiku, JSON, 500 max_tokens
Фокус на TASHKENT POWER, ARTEL, JIZZAKH REFINERIES, etc.
"""

import os
import json
import anthropic
from cost_tracker import CostTracker

tracker = CostTracker("agent_costs.jsonl")
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")


def analyze_local_stock(ticker: str, budget: float = 5000):
    """Анализировать локальную акцию (узбекские компании)"""

    if not API_KEY:
        raise ValueError("❌ OPENROUTER_API_KEY не установлен!")

    client = anthropic.Anthropic(
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

    prompt = f"""Analyze local Uzbekistan stock "{ticker}" for investment with budget ${budget}.

RESPOND ONLY WITH JSON:
{{
  "ticker": "{ticker}",
  "recommendation": "buy|hold|sell",
  "entry_price": number,
  "target_price": number,
  "stop_loss": number,
  "confidence": 0.0-1.0,
  "reasoning": "brief reason",
  "risk_level": "low|medium|high"
}}"""

    try:
        response = client.messages.create(
            model="anthropic/claude-opus-5-fast",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(response.content[0].text)

        cost = tracker.log_call(
            "task_2_stocks_local",
            "anthropic/claude-3.5-haiku",
            response.usage.input_tokens,
            response.usage.output_tokens
        )

        print(f"✅ {ticker}: {result.get('recommendation', 'N/A').upper()}")
        print(f"   Confidence: {result.get('confidence', 0):.1%}")
        print(f"   Cost: ${cost:.6f}")

        return result

    except Exception as e:
        print(f"❌ Ошибка: {str(e)[:100]}")
        return None


if __name__ == "__main__":
    print("📈 Task 2: Анализ локальных акций\n")

    local_stocks = ["TASHKENT POWER", "ARTEL", "ARTEL_AUTOS"]

    for ticker in local_stocks:
        print(f"\n📊 Акция: {ticker}")
        print("-" * 50)
        analyze_local_stock(ticker)

    tracker.daily_report()
