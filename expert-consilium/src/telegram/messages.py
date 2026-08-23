from __future__ import annotations

from typing import Any

WELCOME_MESSAGE = """🎯 *Консилиум Экспертов запущен!*

Я прогоняю твой вопрос через *5 ИИ-экспертов* и выдаю консолидированный ответ.

*Состав консилиума:*
🧠 *Стратег* — видит общую картину
📊 *Аналитик* — работает с данными и фактами
⚡ *Критик* — ищет риски и слабые места
💡 *Креативщик* — нестандартные углы
🎯 *Синтезатор* — собирает консенсус

*Команды:*
/deep — премиум-режим (для сложных вопросов)
/panel — состав экспертов
/history — последние запросы
/mode — текущий режим

Просто напиши вопрос в этот топик 👇"""

HELP_MESSAGE = """*🤖 Консилиум Экспертов — справка*

*Как это работает:*
1. Ты задаёшь вопрос
2. 5 ИИ-экспертов параллельно анализируют
3. Синтезатор собирает консолидированный ответ

*Режимы:*
🟢 *Базовый* — быстрые и бюджетные модели (по умолчанию)
🌟 *Премиум* — топовые модели для сложных вопросов
  • Включи командой /deep перед вопросом

*Примеры вопросов:*
• «Стоит ли сейчас покупать Bitcoin?»
• «Сравни архитектуру микросервисов и монолита»
• «Какие риски у этого стартапа?»

*Команды:*
/start — приветствие
/help — эта справка
/deep — премиум-режим
/panel — состав экспертов
/history — история запросов
/mode — текущий режим"""


def build_analysis_message(question: str, mode: str, total_experts: int = 5) -> str:
    """Build the initial 'analyzing' message."""
    mode_emoji = "⚡" if mode == "basic" else "🌟"
    mode_name = "Базовый" if mode == "basic" else "Премиум"
    return (
        f"🔍 *Анализирую...*\n\n"
        f"Вопрос: _{question[:200]}{'..' if len(question) > 200 else ''}_\n"
        f"Режим: {mode_emoji} {mode_name}\n"
        f"Опрошено экспертов: `0/{total_experts}`"
    )


def build_progress_message(completed: int, total: int, results: list[dict] | None = None) -> str:
    """Build progress update message."""
    status_icons = []
    if results:
        for r in results:
            if r.get("error"):
                status_icons.append(f"❌ {r.get('label', r['role'])}")
            else:
                status_icons.append(f"✅ {r.get('label', r['role'])}")
    
    status_text = "\n".join(status_icons) if status_icons else ""
    bars = "▓" * completed + "░" * (total - completed)
    msg = f"🔍 *Анализирую...*\n{bars} `{completed}/{total}`\n"
    if status_text:
        msg += f"\n{status_text}"
    return msg


def build_final_message(question: str, synthesized: dict[str, Any],
                        mode: str, total_cost: float = 0.0) -> str:
    """Build the final synthesized message."""
    mode_emoji = "⚡" if mode == "basic" else "🌟"
    mode_name = "Базовый" if mode == "basic" else "Премиум"
    confidence = synthesized.get("confidence", 3)
    stars = "⭐" * confidence + "☆" * (5 - confidence)
    cost_str = f"${total_cost:.4f}" if total_cost > 0 else "—"

    text = (
        f"🧠 *Консилиум Экспертов*\n\n"
        f"**Ваш вопрос:** {question}\n\n"
        f"{synthesized['synthesized_text']}\n\n"
        f"---\n"
        f"*Confidence:* {stars} ({confidence}/5) | Режим: {mode_emoji} {mode_name}\n"
        f"*Стоимость:* {cost_str}"
    )
    return text


def build_expert_info_text(role: str) -> str:
    """Build detailed expert info."""
    from src.telegram.keyboards import EXPERT_INFO
    info = EXPERT_INFO.get(role)
    if not info:
        return "Эксперт не найден"
    return (
        f"{info['emoji']} *{info['name']}*\n"
        f"Модель: `{info['model']}`\n"
        f"\n{info['desc']}"
    )


def build_mode_message(current_mode: str) -> str:
    """Build current mode status message."""
    if current_mode == "basic":
        return (
            "🟢 *Текущий режим: Базовый*\n\n"
            "Используются быстрые и бюджетные модели.\n"
            "Подходит для большинства вопросов.\n\n"
            "Для сложных вопросов используй /deep"
        )
    else:
        return (
            "🌟 *Текущий режим: Премиум*\n\n"
            "Используются топовые модели для глубокого анализа.\n"
            "Следующий вопрос будет обработан в премиум-режиме."
        )


def build_history_message(requests: list[dict]) -> str:
    """Build history message from recent requests."""
    if not requests:
        return "📋 *История запросов*\n\nПока нет запросов."
    
    lines = ["📋 *История запросов* (последние 5):\n"]
    for r in requests:
        mode_emoji = "⚡" if r.get("mode") == "basic" else "🌟"
        date = r.get("created_at", "").strftime("%d.%m %H:%M") if r.get("created_at") else ""
        q = r.get("question", "")[:80]
        lines.append(f"• {mode_emoji} `{date}` — _{q}_")
    
    return "\n".join(lines) + "\n\nПодробнее на дашборде: https://us.tailc8105c.ts.net/consilium/"