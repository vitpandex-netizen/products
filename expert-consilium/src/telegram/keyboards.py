from __future__ import annotations

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.config import settings

bot = Bot(token=settings.telegram_bot_token)


def get_mode_keyboard(current_mode: str) -> InlineKeyboardMarkup:
    """Keyboard showing current mode with toggle option."""
    mode_label = "⚡ Базовый" if current_mode == "basic" else "🌟 Премиум"
    kb = [
        [InlineKeyboardButton(text=f"Режим: {mode_label}", callback_data="toggle_mode")],
        [InlineKeyboardButton(text="📊 Дашборд", url="https://us.tailc8105c.ts.net/consilium/")],
        [InlineKeyboardButton(text="👥 Состав экспертов", callback_data="panel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_panel_keyboard() -> InlineKeyboardMarkup:
    """Keyboard with expert panel info."""
    kb = [
        [
            InlineKeyboardButton(text="🧠 Стратег", callback_data="expert_strategist"),
            InlineKeyboardButton(text="📊 Аналитик", callback_data="expert_analyst"),
        ],
        [
            InlineKeyboardButton(text="⚡ Критик", callback_data="expert_critic"),
            InlineKeyboardButton(text="💡 Креативщик", callback_data="expert_creative"),
        ],
        [InlineKeyboardButton(text="🎯 Синтезатор", callback_data="expert_synthesizer")],
        [InlineKeyboardButton(text="◀ Назад", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


EXPERT_INFO = {
    "strategist": {
        "emoji": "🧠",
        "name": "Стратег",
        "model": "DeepSeek V4 Flash",
        "desc": "Видит общую картину, долгосрочные тренды и стратегические выводы. Системное мышление.",
    },
    "analyst": {
        "emoji": "📊",
        "name": "Аналитик",
        "model": "Gemini 2.5 Flash",
        "desc": "Работает с данными, цифрами и фактами. Структурированный разбор и количественные оценки.",
    },
    "critic": {
        "emoji": "⚡",
        "name": "Критик",
        "model": "Claude 4 Haiku",
        "desc": "Ищет слабые места, риски и контраргументы. Конструктивная критика.",
    },
    "creative": {
        "emoji": "💡",
        "name": "Креативщик",
        "model": "GPT-4o-mini",
        "desc": "Нестандартные углы, скрытые возможности, альтернативные подходы.",
    },
    "synthesizer": {
        "emoji": "🎯",
        "name": "Синтезатор",
        "model": "Grok 3 mini",
        "desc": "Собирает ответы всех экспертов в единый консолидированный ответ.",
    },
}