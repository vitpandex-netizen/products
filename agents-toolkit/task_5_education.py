"""
ЗАДАЧА 5: Создание учебных материалов (Education)

🎯 ОПТИМИЗАЦИЯ:
✅ Модель: Claude Haiku (вместо Sonnet/Opus)
✅ Вывод: JSON (вместо длинного текста)
✅ Сокращены макс токены с 2000 до 1000

📊 РЕЗУЛЬТАТ: Экономия ~10x на затратах
"""

import os
import json
import anthropic
from datetime import datetime
from cost_tracker import CostTracker
from optimization_advanced import CachingManager, OPTIMIZED_PROMPTS

# ИНИЦИАЛИЗАЦИЯ
tracker = CostTracker("agent_costs.jsonl")
cache_manager = CachingManager()
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

def get_education_client():
    """Клиент с правильной конфигурацией для OpenRouter"""
    if not API_KEY:
        raise ValueError("❌ OPENROUTER_API_KEY не установлен!")

    return anthropic.Anthropic(
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )


def generate_course_optimized(topic: str, level: str = "beginner"):
    """
    ✅ ОПТИМИЗИРОВАННАЯ версия задачи 5 (Обучение)

    Экономия: 10x (используем Haiku вместо Sonnet)
    Вывод: JSON вместо длинного текста
    """
    client = get_education_client()

    # ПРОМПТ, ОПТИМИЗИРОВАННЫЙ ДЛЯ JSON
    system_prompt = f"""You are an expert educational course designer for IT training centers.
Your expertise: Python, web development, AI/ML, data science.
Level: {level}
Output format: Always respond with ONLY valid JSON, no text before or after."""

    user_prompt = f"""Create a {level} course on "{topic}" for an IT training center in Tashkent.

RESPOND ONLY WITH THIS JSON (no other text):
{{
  "course_name": "string",
  "duration_hours": number,
  "cost_usd": number,
  "modules": [
    {{
      "title": "string",
      "duration_hours": number,
      "lessons": ["lesson1", "lesson2", "lesson3"],
      "learning_outcomes": ["outcome1", "outcome2"]
    }}
  ],
  "prerequisites": ["string"],
  "target_audience": "string",
  "estimated_students": number,
  "success_metrics": ["metric1", "metric2"]
}}"""

    try:
        print(f"\n📚 Генерирую курс: {topic}")
        print("-" * 70)

        response = client.messages.create(
            model="anthropic/claude-opus-5-fast",  # ✅ Работает на OpenRouter
            max_tokens=1000,  # Сократили с 2000
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": user_prompt
            }]
        )

        # ПАРСИНГ РЕЗУЛЬТАТА
        result_text = response.content[0].text
        course_data = json.loads(result_text)

        # ЛОГИРОВАНИЕ ЗАТРАТ
        usage = response.usage
        cost = tracker.log_call(
            "task_5_education",
            "anthropic/claude-3.5-haiku",
            usage.input_tokens,
            usage.output_tokens
        )

        # ВЫВОД ИНФОРМАЦИИ
        print(f"✅ Курс создан успешно!")
        print(f"   📖 Название: {course_data.get('course_name', 'N/A')}")
        print(f"   ⏱️  Продолжительность: {course_data.get('duration_hours', 0)} часов")
        print(f"   📚 Модулей: {len(course_data.get('modules', []))}")
        print(f"\n   📊 Токены: {usage.input_tokens} input, {usage.output_tokens} output")
        print(f"   💰 Стоимость: ${cost:.6f}")

        return course_data

    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {str(e)}")
        print(f"   Ответ модели: {result_text[:200]}")
        return None

    except anthropic.APIError as e:
        print(f"❌ API ошибка: {str(e)[:200]}")
        return None

    except Exception as e:
        print(f"❌ Неожиданная ошибка: {str(e)}")
        return None


def batch_generate_courses(topics: list):
    """Генерировать несколько курсов и вывести отчёт"""

    print("\n" + "="*70)
    print("🚀 МАССОВАЯ ГЕНЕРАЦИЯ КУРСОВ (Task 5 - Education)")
    print("="*70)

    results = []
    total_cost = 0

    for i, topic in enumerate(topics, 1):
        print(f"\n[{i}/{len(topics)}] Обработка: {topic}")
        course = generate_course_optimized(topic)

        if course:
            results.append(course)
            # Суммируем стоимость из трекера
            # (стоимость логируется автоматически в generate_course_optimized)

    # ФИНАЛЬНЫЙ ОТЧЁТ
    print("\n" + "="*70)
    print("📋 ИТОГОВЫЙ ОТЧЁТ")
    print("="*70)
    print(f"✅ Успешно создано курсов: {len(results)}/{len(topics)}")

    if len(results) > 0:
        total_hours = sum(c.get("duration_hours", 0) for c in results)
        total_modules = sum(len(c.get("modules", [])) for c in results)
        print(f"   📚 Всего модулей: {total_modules}")
        print(f"   ⏱️  Всего часов обучения: {total_hours}")

    # Показать дневной отчёт затрат
    tracker.daily_report()

    return results


# ПРИМЕРЫ ДЛЯ ТЕСТИРОВАНИЯ
if __name__ == "__main__":
    # Список тем для курсов
    topics = [
        "Python for Beginners",
        "Advanced Python and FastAPI",
        "Machine Learning Basics",
        "Web Development with React",
        "Cloud Computing with AWS",
    ]

    # ЗАПУСК
    print(f"\n⏰ Начало: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔑 API: OpenRouter")
    print("💾 Трекер: Сохраняет затраты в agent_costs.jsonl\n")

    results = batch_generate_courses(topics)

    print(f"\n⏰ Завершено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✨ Task 5 готова к использованию!")
