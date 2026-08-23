from __future__ import annotations

from typing import Any

# Synthesizer system prompt sent to the final model
SYNTHESIZER_SYSTEM_PROMPT = (
    "Ты — Синтезатор. Твоя задача — собрать ответы 5 ИИ-экспертов на вопрос пользователя "
    "и выдать единый консолидированный ответ.\n\n"
    "Формат ответа (строго соблюдай):\n\n"
    "### 📋 Консенсус\n"
    "[2-3 абзаца: в чём эксперты сошлись, общая картина]\n\n"
    "### ⚡ Расхождения\n"
    "- **Стратег vs Критик:** [в чём разошлись, если есть]\n"
    "- **Аналитик vs Креативщик:** [в чём разошлись, если есть]\n\n"
    "### 🎯 Рекомендация\n"
    "[Итоговая рекомендация на основе консенсуса]\n\n"
    "### 📊 Детали экспертов\n"
    "<details>\n"
    "<summary>🧠 Стратег</summary>\n"
    "[краткий тезис, 1-2 предложения]\n"
    "</details>\n"
    "... (по аналогии для всех экспертов)\n\n"
    "Важно: \n"
    "- Пиши на русском\n"
    "- Будь объективным\n"
    "- Если эксперты сильно разошлись — честно укажи это\n"
    "- Confidence оцени от 1 до 5\n"
)


def build_synthesizer_prompt(question: str, expert_responses: list[dict[str, Any]]) -> str:
    """Build the prompt for the synthesizer model."""
    experts_text = ""
    for resp in expert_responses:
        label = resp.get("label", resp["role"])
        if resp.get("error"):
            experts_text += f"\n--- {label} ---\n[Ошибка: {resp['error']}]\n"
        else:
            experts_text += f"\n--- {label} ---\n{resp['response_text']}\n"

    return (
        f"Вопрос пользователя: {question}\n\n"
        f"Ответы экспертов:\n{experts_text}\n\n"
        "Сформируй консолидированный ответ по формату."
    )


def parse_synthesized_response(response_text: str) -> dict[str, Any]:
    """Parse the synthesized response to extract structured data."""
    confidence = 3  # default
    if "⭐⭐⭐⭐⭐" in response_text or "5/5" in response_text or "Confidence: 5" in response_text:
        confidence = 5
    elif "⭐⭐⭐⭐" in response_text or "4/5" in response_text or "Confidence: 4" in response_text:
        confidence = 4
    elif "⭐⭐⭐" in response_text or "3/5" in response_text or "Confidence: 3" in response_text:
        confidence = 3
    elif "⭐⭐" in response_text or "2/5" in response_text or "Confidence: 2" in response_text:
        confidence = 2
    elif "⭐" in response_text or "1/5" in response_text or "Confidence: 1" in response_text:
        confidence = 1

    return {
        "synthesized_text": response_text,
        "confidence": confidence,
    }