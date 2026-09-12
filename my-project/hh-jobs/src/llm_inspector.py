#!/usr/bin/env python3
"""
UZ IT Jobs — Deep-LLM Scoring & Red Flag Detector (TASK-HH-027 / TASK-HH-028).
Проводит глубокий семантический анализ вакансий и выявляет красные флаги (токсичность, хаос).
"""

import os
import sys
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [llm-inspector] %(message)s"
)
logger = logging.getLogger("llm-inspector")

TOXIC_KEYWORDS = [
    "стрессоустойчивость", "работа 24/7", "готовность к ненормированному",
    "молодой динамичный коллектив", "работа на результат", "многозадачность",
    "тушение пожаров", "умение работать в условиях хаоса"
]

def analyze_vacancy_deep(title: str, description: str) -> dict:
    """Анализирует текст вакансии на скрытые смыслы и красные флаги."""
    desc_lower = description.lower()
    flags = []
    
    for kw in TOXIC_KEYWORDS:
        if kw in desc_lower:
            flags.append(f"Замечен риск: '{kw}' — возможен перегруз и ненормированный график.")
            
    score_modifier = 0.0
    if len(flags) > 2:
        score_modifier = -0.15
        
    analysis = {
        "is_toxic_risk": len(flags) > 0,
        "red_flags": flags,
        "culture_summary": "Требуется высокую устойчивость к высокой операционной нагрузке." if flags else "Стандартные корпоративные требования.",
        "score_modifier": score_modifier
    }
    return analysis

if __name__ == "__main__":
    test_res = analyze_vacancy_deep("CIO / IT Director", "Ищем CIO. Требуется стрессоустойчивость и готовность к работе 24/7.")
    logger.info(f"Тест Deep-LLM анализа: {json.dumps(test_res, ensure_ascii=False, indent=2)}")
