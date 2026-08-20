"""
ЗАДАЧА 3: Анализ американских акций (Stocks USA)

🎯 ОПТИМИЗАЦИЯ: Claude Haiku, JSON, 500 max_tokens
Фокус на TECH: AAPL, GOOGL, MSFT, NVDA, TESLA
"""

import os
import json
import anthropic
from cost_tracker import CostTracker

tracker = CostTracker("agent_costs.jsonl")
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")


def analyze_usa_stock(ticker: str, budget: float = 5000):
    """Анализировать американскую акцию (Tech/Growth)"""

    if not API_KEY:
        raise ValueError("❌ OPENROUTER_API_KEY не установлен!")

    client = anthropic.Anthropic(
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

    prompt = f"""Analyze USA tech stock "{ticker}" for investment with budget ${budget}.
Focus on: growth potential, AI exposure, market position.

RESPOND ONLY WITH JSON:
{{
  "ticker": "{ticker}",
  "recommendation": "buy|hold|sell",
  "entry_price": number,
  "target_price": number,
  "stop_loss": number,
  "confidence": 0.0-1.0,
  "ai_exposure": "none|low|medium|high",
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
            "task_3_stocks_usa",
            "anthropic/claude-3.5-haiku",
            response.usage.input_tokens,
            response.usage.output_tokens
        )

        print(f"✅ {ticker}: {result.get('recommendation', 'N/A').upper()}")
        print(f"   AI Exposure: {result.get('ai_exposure', 'N/A')}")
        print(f"   Cost: ${cost:.6f}")

        return result

    except Exception as e:
        print(f"❌ Ошибка: {str(e)[:100]}")
        return None


if __name__ == "__main__":
    print("🇺🇸 Task 3: Анализ американских акций\n")

    usa_stocks = ["AAPL", "GOOGL", "MSFT", "NVDA", "TSLA"]

    for ticker in usa_stocks:
        print(f"\n📊 Акция: {ticker}")
        print("-" * 50)
        analyze_usa_stock(ticker)

    tracker.daily_report()
