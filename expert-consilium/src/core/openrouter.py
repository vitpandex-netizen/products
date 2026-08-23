from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from src.config import settings

# Expert roles with their system prompts
EXPERT_CONFIGS: list[dict[str, Any]] = [
    {
        "role": "strategist",
        "label": "🧠 Стратег",
        "system_prompt": (
            "Ты — Стратег. Твоя задача — видеть общую картину, долгосрочные тренды "
            "и стратегические выводы. Отвечай на вопрос пользователя, фокусируясь на:\n"
            "1. Общая картина и контекст\n"
            "2. Долгосрочные тренды и последствия\n"
            "3. Стратегические возможности\n"
            "4. Системное мышление — как разные части влияют друг на друга\n\n"
            "Будь лаконичен: 2-3 абзаца максимум. Пиши на русском."
        ),
    },
    {
        "role": "analyst",
        "label": "📊 Аналитик",
        "system_prompt": (
            "Ты — Аналитик. Твоя задача — работать с данными, цифрами, фактами "
            "и структурированным разбором. Отвечай на вопрос, фокусируясь на:\n"
            "1. Конкретные данные и факты\n"
            "2. Структурированный разбор (списки, сравнения)\n"
            "3. Количественные оценки там, где это возможно\n"
            "4. Причинно-следственные связи\n\n"
            "Будь лаконичен: 2-3 абзаца максимум. Пиши на русском."
        ),
    },
    {
        "role": "critic",
        "label": "⚡ Критик",
        "system_prompt": (
            "Ты — Критик. Твоя задача — искать слабые места, риски и контраргументы. "
            "Отвечай на вопрос, фокусируясь на:\n"
            "1. Потенциальные риски и «подводные камни»\n"
            "2. Слабые места в предлагаемых решениях\n"
            "3. Что может пойти не так\n"
            "4. Контраргументы к популярным мнениям\n\n"
            "Будь лаконичен: 2-3 абзаца максимум, но не будь токсичным — "
            "конструктивная критика. Пиши на русском."
        ),
    },
    {
        "role": "creative",
        "label": "💡 Креативщик",
        "system_prompt": (
            "Ты — Креативщик. Твоя задача — находить нестандартные углы, "
            "скрытые возможности и альтернативные подходы. Отвечай на вопрос, фокусируясь на:\n"
            "1. Нестандартные перспективы\n"
            "2. Скрытые возможности, которые упускают из виду\n"
            "3. Альтернативные подходы и «thinking outside the box»\n"
            "4. Креативные комбинации идей\n\n"
            "Будь лаконичен: 2-3 абзаца максимум. Пиши на русском."
        ),
    },
]


class OpenRouterClient:
    """Client for OpenRouter API."""

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.site_url,
            "X-Title": settings.site_name,
        }

    async def query_model(self, model: str, user_message: str,
                          system_prompt: str | None = None) -> dict[str, Any]:
        """Query a single model via OpenRouter."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        start_time = time.monotonic()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 1000,
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = int((time.monotonic() - start_time) * 1000)

        choice = data["choices"][0]
        content = choice["message"]["content"]
        usage = data.get("usage", {})

        return {
            "content": content,
            "tokens_in": usage.get("prompt_tokens", 0),
            "tokens_out": usage.get("completion_tokens", 0),
            "cost": self._calculate_cost(model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)),
            "latency_ms": latency_ms,
        }

    async def query_experts(self, question: str, mode: str = "basic") -> list[dict[str, Any]]:
        """Query all experts in parallel."""
        model_key = "premium" if mode == "premium" else "basic"

        async def _query_expert(config: dict) -> dict[str, Any]:
            model = getattr(settings, f"model_{config['role']}_{model_key}")
            try:
                result = await self.query_model(model, question, config["system_prompt"])
                return {
                    "role": config["role"],
                    "label": config["label"],
                    "model": model,
                    "response_text": result["content"],
                    "tokens_in": result["tokens_in"],
                    "tokens_out": result["tokens_out"],
                    "cost": result["cost"],
                    "latency_ms": result["latency_ms"],
                    "error": None,
                }
            except Exception as e:
                return {
                    "role": config["role"],
                    "label": config["label"],
                    "model": model,
                    "response_text": f"[Ошибка: {str(e)}]",
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "cost": 0.0,
                    "latency_ms": 0,
                    "error": str(e),
                }

        tasks = [_query_expert(config) for config in EXPERT_CONFIGS]
        results = await asyncio.gather(*tasks)
        return list(results)

    @staticmethod
    def _calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
        """Calculate approximate cost based on model pricing."""
        pricing = {
            # Basic models (per 1M tokens)
            "deepseek/deepseek-v4-flash": {"in": 0.35, "out": 0.40},
            "google/gemini-2.5-flash": {"in": 0.15, "out": 0.60},
            "anthropic/claude-4-haiku": {"in": 0.25, "out": 1.25},
            "openai/gpt-4o-mini": {"in": 0.15, "out": 0.60},
            "grok/grok-3-mini": {"in": 0.30, "out": 0.80},
            # Premium models
            "deepseek/deepseek-v4": {"in": 3.0, "out": 10.0},
            "google/gemini-2.5-pro": {"in": 1.25, "out": 10.0},
            "anthropic/claude-sonnet-4": {"in": 3.0, "out": 15.0},
            "openai/gpt-4o": {"in": 2.5, "out": 10.0},
            "grok/grok-3": {"in": 3.0, "out": 15.0},
        }

        price = pricing.get(model, {"in": 1.0, "out": 2.0})
        cost = (tokens_in / 1_000_000 * price["in"]) + (tokens_out / 1_000_000 * price["out"])
        return round(cost, 6)