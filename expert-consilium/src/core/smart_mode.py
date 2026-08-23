from __future__ import annotations

COMPLEXITY_KEYWORDS = [
    "архитектур", "стратеги", "анализ", "оптимизаци",
    "risk", "design pattern", "алгоритм",
    "инфраструктур", "деплой", "security",
    "производительност", "масштабировани", "миграци",
    "trade-off", "компромис", "сравнен",
    "инвестици", "портфел", "диверсификаци",
    "бюджет", "forecast", "прогноз",
]


def is_complex_query(text: str) -> bool:
    """Определяет, нужен ли премиум-режим."""
    text_lower = text.lower()

    # Длинный вопрос = сложный
    if len(text) > 200:
        return True

    # Ключевые слова
    if any(kw in text_lower for kw in COMPLEXITY_KEYWORDS):
        return True

    return False


def calculate_complexity_score(text: str) -> float:
    """Calculate complexity score 0.0-1.0."""
    score = 0.0
    text_lower = text.lower()

    # Length factor
    if len(text) > 200:
        score += 0.3
    elif len(text) > 100:
        score += 0.15

    # Keyword factor
    keyword_hits = sum(1 for kw in COMPLEXITY_KEYWORDS if kw in text_lower)
    score += min(keyword_hits * 0.1, 0.4)

    # Question marks factor
    if "?" in text:
        score += 0.1
    if "?" in text and text.count("?") > 1:
        score += 0.1

    # Technical terms factor
    tech_terms = ["api", "docker", "python", "sql", "redis", "postgres",
                  "fastapi", "async", "microservice", "event", "queue",
                  "stream", "websocket", "graphql", "rest"]
    tech_hits = sum(1 for t in tech_terms if t in text_lower)
    score += min(tech_hits * 0.05, 0.2)

    return round(min(score, 1.0), 2)


def determine_mode(text: str, forced_mode: str | None = None) -> str:
    """Определяет режим: basic или premium."""
    if forced_mode == "premium":
        return "premium"
    if forced_mode == "basic":
        return "basic"
    if is_complex_query(text):
        return "premium"
    return "basic"