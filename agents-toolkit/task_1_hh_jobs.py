"""
ЗАДАЧА 1: Поиск вакансий на HH (HH Jobs)

🎯 ОПТИМИЗАЦИЯ:
✅ Модель: Claude Sonnet (нужна скорость)
✅ Кэширование системного промпта (экономия 90%!)
✅ JSON output

📊 КЭШИРОВАНИЕ: Первый вызов платит, остальные 90% дешевле
"""

import os
import json
import anthropic
from cost_tracker import CostTracker

tracker = CostTracker("agent_costs.jsonl")
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# КЭШИРУЕМЫЙ СИСТЕМНЫЙ ПРОМПТ (один раз за сессию)
SYSTEM_CONTEXT_CACHED = """You are an expert job application assistant specializing in IT/LLM roles.

# YOUR PROFILE:
- Location: Tashkent, Uzbekistan
- Specialization: Python, LLM Engineering, AI/ML
- Experience: 5+ years in software development
- Salary expectation: $5000+ per month
- Work preference: Remote or hybrid
- Languages: Russian, English, Uzbek

# JOB MATCHING CRITERIA:
- Match job requirements to your skills
- Confidence threshold: > 0.7 means apply
- Generate personalized cover letter
- Response format: JSON only

# PREVIOUS SUCCESSFUL MATCHES:
- Mid-level to Senior Python Developer roles
- LLM/AI Engineer positions
- Tech companies with remote options
"""


def match_job_and_create_application(job_posting: str, use_cache: bool = True):
    """
    Анализировать вакансию и создать приложение
    (с опциональным кэшированием для экономии)
    """

    if not API_KEY:
        raise ValueError("❌ OPENROUTER_API_KEY не установлен!")

    client = anthropic.Anthropic(
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

    prompt = f"""Analyze this job posting and decide if I should apply:

{job_posting}

RESPOND ONLY WITH JSON:
{{
  "job_title": "string",
  "company": "string",
  "should_apply": true/false,
  "confidence": 0.0-1.0,
  "match_score": 0-100,
  "key_matches": ["skill1", "skill2"],
  "key_mismatches": ["skill3"],
  "salary_fit": "low|fair|good|excellent",
  "application_letter_ru": "Cover letter in Russian (max 300 words)"
}}"""

    # BUILD SYSTEM MESSAGE WITH OPTIONAL CACHING
    system_message = [
        {
            "type": "text",
            "text": SYSTEM_CONTEXT_CACHED,
        }
    ]

    if use_cache:
        # ДОБАВИТЬ КЭШИРОВАНИЕ
        system_message[0]["cache_control"] = {"type": "ephemeral"}

    try:
        response = client.messages.create(
            model="anthropic/claude-opus-5-fast",
            max_tokens=800,
            system=system_message,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        result = json.loads(response.content[0].text)

        # ИНФОРМАЦИЯ О КЭШЕ
        usage = response.usage
        cache_creation = getattr(usage, 'cache_creation_input_tokens', 0)
        cache_read = getattr(usage, 'cache_read_input_tokens', 0)

        cost = tracker.log_call(
            "task_1_hh_jobs",
            "anthropic/claude-3.5-sonnet",
            usage.input_tokens,
            usage.output_tokens
        )

        # ВЫВОД
        print(f"✅ {result.get('job_title', 'N/A')} @ {result.get('company', 'N/A')}")
        print(f"   Рекомендация: {'APPLY! 🎯' if result.get('should_apply') else 'PASS ❌'}")
        print(f"   Confidence: {result.get('confidence', 0):.1%}")

        # КЭШИРОВАНИЕ СТАТИСТИКА
        if cache_creation > 0:
            print(f"\n   🔄 КЭШИРОВАНИЕ СОЗДАНО:")
            print(f"      Токенов кэширована: {cache_creation}")
        if cache_read > 0:
            print(f"\n   ⚡ КЭШИРОВАНИЕ ИСПОЛЬЗОВАНО:")
            print(f"      Токенов из кэша: {cache_read}")
            savings = (cache_read * 3 * 0.9) / 1_000_000  # 90% скидка на Sonnet
            print(f"      Экономия: ${savings:.6f}")

        print(f"\n   Cost: ${cost:.6f}")

        return result

    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {str(e)}")
        return None

    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
        return None


if __name__ == "__main__":
    print("💼 Task 1: Поиск вакансий на HH\n")

    # ПРИМЕРЫ ВАКАНСИЙ
    jobs = [
        """
        Senior Python Developer
        Company: TechCorp Tashkent
        Salary: $6000-7000
        Location: Remote (CIS)

        Requirements:
        - 5+ years Python
        - LLM/AI experience
        - FastAPI
        - PostgreSQL
        """,
        """
        LLM Engineer
        Company: AI Startup
        Salary: $5000-6000
        Location: Remote

        Requirements:
        - Python expert
        - Prompt engineering
        - Vector databases
        - LangChain experience
        """,
    ]

    print("🚀 Первый вызов (создаст кэш)...\n")
    match_job_and_create_application(jobs[0], use_cache=True)

    print("\n" + "="*70)
    print("🚀 Второй вызов (использует кэш - 90% дешевле!)...\n")
    match_job_and_create_application(jobs[1], use_cache=True)

    print("\n" + "="*70)
    tracker.daily_report()
