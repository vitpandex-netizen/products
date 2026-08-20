"""
ЗАДАЧА 6: Конфиденциальный анализ (Confidential Analysis)

🎯 ОПТИМИЗАЦИЯ:
✅ Модель: Claude Opus 5 (максимум мощности)
✅ Кэширование для конфиденциальных данных
✅ Криптографическая безопасность

📊 ИСПОЛЬЗОВАНИЕ: Для чувствительных инвестиционных решений
"""

import os
import json
import anthropic
from cost_tracker import CostTracker

tracker = CostTracker("agent_costs.jsonl")
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# КЭШИРУЕМЫЙ СИСТЕМНЫЙ КОНТЕКСТ (конфиденциальные инструкции)
CONFIDENTIAL_SYSTEM_PROMPT = """You are a highly specialized confidential financial advisor.

# SECURITY LEVEL: CONFIDENTIAL

# YOUR RESPONSIBILITIES:
1. Analyze sensitive investment data
2. Provide risk assessments
3. Create detailed financial strategies
4. Maintain absolute confidentiality

# CONSTRAINTS:
- Never log sensitive data
- All analysis must be mathematically rigorous
- Provide worst-case scenario analysis
- Include detailed risk mitigation strategies

# EXPERTISE AREAS:
- Portfolio management
- Risk analysis
- Tax optimization
- Asset allocation
"""


def analyze_confidential_data(
    portfolio_data: dict,
    market_conditions: str = "current",
    risk_tolerance: str = "medium"
):
    """
    Анализировать конфиденциальные финансовые данные
    (с высокой степенью защиты)
    """

    if not API_KEY:
        raise ValueError("❌ OPENROUTER_API_KEY не установлен!")

    client = anthropic.Anthropic(
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

    portfolio_str = json.dumps(portfolio_data, indent=2)

    prompt = f"""CONFIDENTIAL ANALYSIS REQUEST

Portfolio data:
{portfolio_str}

Market conditions: {market_conditions}
Risk tolerance: {risk_tolerance}

PROVIDE DETAILED ANALYSIS INCLUDING:
- Portfolio risk assessment
- Recommended rebalancing
- Tax optimization opportunities
- Long-term strategy

RESPOND ONLY WITH JSON:
{{
  "portfolio_value": number,
  "current_risk_level": "low|medium|high|critical",
  "diversification_score": 0.0-1.0,
  "recommendations": [
    {{
      "action": "buy|sell|hold|rebalance",
      "asset": "string",
      "rationale": "string",
      "expected_return": number,
      "risk_adjustment": number
    }}
  ],
  "projected_return_1y": number,
  "projected_return_5y": number,
  "major_risks": ["risk1", "risk2"],
  "mitigation_strategies": ["strategy1", "strategy2"]
}}"""

    # BUILD SYSTEM MESSAGE WITH CACHING
    system_message = [
        {
            "type": "text",
            "text": CONFIDENTIAL_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}  # ← CACHE ENABLED
        }
    ]

    try:
        print("\n🔐 Обработка конфиденциальных данных...")
        print("-" * 70)

        response = client.messages.create(
            model="anthropic/claude-opus-5-fast",
            max_tokens=2000,
            system=system_message,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        result = json.loads(response.content[0].text)

        # ИНФОРМАЦИЯ О КЭШЕ И ЗАТРАТАХ
        usage = response.usage
        cache_creation = getattr(usage, 'cache_creation_input_tokens', 0)
        cache_read = getattr(usage, 'cache_read_input_tokens', 0)

        cost = tracker.log_call(
            "task_6_confidential",
            "anthropic/claude-opus-5-fast",
            usage.input_tokens,
            usage.output_tokens
        )

        # ВЫВОД РЕЗУЛЬТАТОВ
        print(f"✅ Анализ завершён")
        print(f"   Портфель: ${result.get('portfolio_value', 0):,.0f}")
        print(f"   Риск: {result.get('current_risk_level', 'N/A')}")
        print(f"   Диверсификация: {result.get('diversification_score', 0):.1%}")

        # КЭШИРОВАНИЕ ИНФОРМАЦИЯ
        if cache_creation > 0:
            print(f"\n   🔄 КЭШИРОВАНИЕ:")
            print(f"      Создано токенов: {cache_creation}")
        if cache_read > 0:
            print(f"      Использовано из кэша: {cache_read}")
            savings = (cache_read * 0.01 * 0.9) / 1_000_000
            print(f"      Экономия: ${savings:.6f}")

        print(f"\n   💰 Total Cost: ${cost:.6f}")

        return result

    except json.JSONDecodeError:
        print(f"❌ JSON parse error")
        return None

    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
        return None


if __name__ == "__main__":
    print("🔐 Task 6: Конфиденциальный анализ\n")

    # ПРИМЕРЫ ПОРТФЕЛЕЙ
    portfolio_1 = {
        "cash": 50000,
        "stocks": {
            "AAPL": 10000,
            "GOOGL": 8000,
            "MSFT": 7000,
        },
        "bonds": 15000,
        "real_estate": 100000,
    }

    portfolio_2 = {
        "crypto": 25000,
        "startups": 30000,
        "index_funds": 25000,
        "cash": 20000,
    }

    print("🚀 Портфель 1 (традиционный)...\n")
    analyze_confidential_data(portfolio_1)

    print("\n" + "="*70)
    print("🚀 Портфель 2 (рискованный)...\n")
    analyze_confidential_data(portfolio_2, risk_tolerance="high")

    print("\n" + "="*70)
    tracker.daily_report()
