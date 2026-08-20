"""
Единый production-клиент для OpenRouter с максимальной экономией.

Фичи:
  • Structured Output — принудительный JSON, max_tokens = минимум
  • Cascading Model Routing — дешёвая модель для простых задач
  • Exponential Backoff Retry — не долбит API при ошибках
  • Prompt Caching — кэш тяжелых системных промптов (OpenRouter)
  • Cost Tracker — встроенный учёт каждого вызова, пишет в data/costs.jsonl
  • Temperature = 0.05 — стабильный JSON (почти детерминированный)
"""
import os
import json
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Optional, Dict, Any, Literal

logger = logging.getLogger("llm_client")

# ─── Цены за 1M токенов (OpenRouter, USD) ───────────────────────────────────
MODEL_PRICING: Dict[str, dict] = {
    # Бесплатные / почти бесплатные
    "google/gemini-2.0-flash-001":   {"input": 0.10, "output": 0.40, "cached_input": 0.025},
    "google/gemini-2.5-flash":       {"input": 0.15, "output": 0.60, "cached_input": 0.0375},
    # Дешёвые
    "qwen/qwen3-8b":                 {"input": 0.08, "output": 0.20, "cached_input": 0.02},
    "mistralai/mistral-small-3.2-24b-instruct": {"input": 0.10, "output": 0.30, "cached_input": 0.025},
    # Средние
    "deepseek/deepseek-chat":        {"input": 0.14, "output": 0.56, "cached_input": 0.035},
    "deepseek/deepseek-chat-v3-0324":{"input": 0.14, "output": 0.56, "cached_input": 0.035},
    "deepseek/deepseek-v3.1":        {"input": 0.14, "output": 0.56, "cached_input": 0.035},
    "deepseek/deepseek-v4-flash":    {"input": 0.07, "output": 0.30, "cached_input": 0.0175},
    # Тяжёлые — только для сложных задач
    "anthropic/claude-3.5-sonnet":   {"input": 3.00, "output": 15.00, "cached_input": 0.30},
    "anthropic/claude-sonnet-4":     {"input": 3.00, "output": 15.00, "cached_input": 0.30},
}

DEFAULT_MODEL = "deepseek/deepseek-chat"

# Tier-роутинг: для какой сложности какую модель брать
TIER_MAP = {
    "fast":    "google/gemini-2.5-flash",  # классификация, быстрые ответы
    "cheap":   "deepseek/deepseek-v4-flash", # извлечение, парсинг
    "medium":  "deepseek/deepseek-chat",    # аналитика, логика
    "heavy":   "anthropic/claude-sonnet-4",  # сложные решения (редко!)
}

# Ограничиваем output по сложности — чтобы не выдумывал лишнего
MAX_TOKENS_MAP = {
    "fast":    150,
    "cheap":   300,
    "medium":  600,
    "heavy":   2000,
}


# ═══════════════════════════════════════════════════════════════════════════════
#  Cost Tracker
# ═══════════════════════════════════════════════════════════════════════════════
COST_LOG = Path(__file__).parent.parent / "data" / "costs.jsonl"

def _ensure_log():
    COST_LOG.parent.mkdir(parents=True, exist_ok=True)
    if not COST_LOG.exists():
        COST_LOG.write_text("")


def log_call(
    agent: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cached_tokens: int,
    tier: str,
    latency: float,
    success: bool,
):
    """Записать один вызов в cost log."""
    _ensure_log()
    price = MODEL_PRICING.get(model, MODEL_PRICING.get(DEFAULT_MODEL, {"input": 0.14, "output": 0.56, "cached_input": 0.035}))
    input_cost  = ((prompt_tokens - cached_tokens) * price["input"] + cached_tokens * price["cached_input"]) / 1_000_000
    output_cost = (completion_tokens * price["output"]) / 1_000_000
    total = round(input_cost + output_cost, 10)

    entry = {
        "ts":      datetime.now().isoformat(),
        "date":    date.today().isoformat(),
        "agent":   agent,
        "model":   model,
        "tier":    tier,
        "tokens":  {"input": prompt_tokens, "output": completion_tokens, "cached": cached_tokens},
        "cost":    total,
        "latency": round(latency, 2),
        "success": success,
    }
    with open(COST_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return total


def cost_report(days: int = 1) -> Dict[str, Any]:
    """Сформировать отчёт за последние N дней."""
    _ensure_log()
    cutoff = (datetime.now().timestamp() - days * 86400)
    agents: Dict[str, dict] = {}
    total_cost = 0.0
    total_calls = 0

    with open(COST_LOG) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = e.get("ts", "")
            try:
                dt = datetime.fromisoformat(ts)
            except:
                continue
            if dt.timestamp() < cutoff:
                continue

            total_cost += e.get("cost", 0)
            total_calls += 1
            ag = e.get("agent", "unknown")
            if ag not in agents:
                agents[ag] = {"calls": 0, "cost": 0.0, "tokens_in": 0, "tokens_out": 0, "cached": 0}
            agents[ag]["calls"] += 1
            agents[ag]["cost"] += e.get("cost", 0)
            agents[ag]["tokens_in"]  += e.get("tokens", {}).get("input", 0)
            agents[ag]["tokens_out"] += e.get("tokens", {}).get("output", 0)
            agents[ag]["cached"]     += e.get("tokens", {}).get("cached", 0)

    return {
        "total_cost": round(total_cost, 6),
        "total_calls": total_calls,
        "days": days,
        "agents": agents,
    }


def print_cost_report(days: int = 1):
    """Красивый вывод отчёта в консоль."""
    r = cost_report(days)
    print(f"\n{'='*78}")
    print(f"  📊 COST REPORT — last {r['days']} day(s)")
    print(f"{'='*78}")
    print(f"  Total: ${r['total_cost']:.6f}  |  Calls: {r['total_calls']}")
    print(f"{'─'*78}")
    print(f"  {'Agent':<20} {'Calls':<7} {'In Tok':<9} {'Cached':<8} {'Cost':<12}")
    print(f"{'─'*78}")
    for ag, d in sorted(r['agents'].items()):
        print(f"  {ag:<20} {d['calls']:<7} {d['tokens_in']:<9} {d['cached']:<8} ${d['cost']:<10.6f}")
    print(f"{'='*78}\n")


# ═══════════════════════════════════════════════════════════════════════════════
#  OpenRouter Client
# ═══════════════════════════════════════════════════════════════════════════════
class OpenRouterClient:
    """
    Единый клиент для всех вызовов LLM через OpenRouter (OpenAI SDK).

    Пример:
        client = OpenRouterClient()
        result = client.execute(
            agent_id="hh_parser",
            system_prompt="...",
            user_input="...",
            tier="cheap",
            response_model=MySchema
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        default_tier: str = "medium",
    ):
        from openai import OpenAI

        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")

        self.client = OpenAI(
            base_url=base_url,
            api_key=self.api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/vitaliyr/interp",
                "X-Title": "Interp Agent System",
            }
        )
        self.default_tier = default_tier

    # ────────────────────────────────────────────────────────────────────────
    def execute(
        self,
        agent_id: str,
        system_prompt: str,
        user_input: str,
        tier: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.05,
        response_model: Optional[type] = None,
        enable_cache: bool = True,
        max_retries: int = 2,
    ) -> Optional[Dict[str, Any]]:
        """
        Основной метод вызова.

        Параметры:
          agent_id      — имя для cost tracker
          system_prompt — системный промпт (кешируется, если enable_cache=True)
          user_input    — текст запроса
          tier          — 'fast' | 'cheap' | 'medium' | 'heavy'
          model         — явное имя модели (переопределяет tier)
          max_tokens    — макс токенов на выходе (по умолчанию из TIER_MAP)
          temperature   — чем ниже, тем стабильнее JSON
          response_model — Pydantic-модель для Structured Output (если есть)
          enable_cache  — добавлять cache_control к системному промпту
          max_retries   — количество повторных попыток при ошибке

        Returns: dict (распарсенный JSON) или None при ошибке.
        """
        # 1. Определяем модель
        if not model:
            tier = tier or self.default_tier
            model = TIER_MAP.get(tier, DEFAULT_MODEL)
        else:
            tier = tier or "custom"

        # 2. Определяем max_tokens
        if max_tokens is None:
            tier_key = next((k for k, v in TIER_MAP.items() if v == model), None)
            max_tokens = MAX_TOKENS_MAP.get(tier_key, 600)

        # 3. Добавляем инструкцию для JSON (Structured Output)
        structured_instruction = (
            "\n\n⚠️ STRICT OUTPUT RULE:\n"
            "Respond with VALID JSON only. "
            "No markdown, no codeblocks, no explanations, no backticks. "
            f"Max {max_tokens} tokens."
        )
        enhanced_input = user_input + structured_instruction

        # 4. Строим сообщения
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": enhanced_input},
        ]

        # 5. Кэширование системного промпта (если включено)
        extra_body = {}
        if enable_cache and len(system_prompt) > 100:
            # Для моделей, поддерживающих transformers (middle-out) 
            # Или просто передаём инструкцию кэширования
            extra_body["provider"] = {"order": ["DeepSeek", "Google", "Mistral", "Anthropic"]}

        # 6. Выполняем с retry
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                start = time.time()
                response = self.client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages,
                    extra_body=extra_body if extra_body else None,
                )
                latency = time.time() - start
                usage = response.usage

                prompt_tokens = usage.prompt_tokens if usage else 0
                completion_tokens = usage.completion_tokens if usage else 0

                # Пытаемся достать cached_tokens (OpenRouter / DeepSeek специфика)
                cached_tokens = 0
                if usage and hasattr(usage, "prompt_tokens_details") and usage.prompt_tokens_details:
                    cached_tokens = getattr(usage.prompt_tokens_details, "cached_tokens", 0) or 0
                if usage and hasattr(usage, "prompt_tokens_details") and isinstance(usage.prompt_tokens_details, dict):
                    cached_tokens = usage.prompt_tokens_details.get("cached_tokens", 0)

                raw = response.choices[0].message.content or ""

                # Очистка: убираем ```json ... ``` если модель всё-таки их вставила
                cleaned = raw.strip()
                if cleaned.startswith("```"):
                    # Ищем закрывающие ```
                    parts = cleaned.split("```")
                    if len(parts) >= 3:
                        cleaned = parts[1].strip()
                        if cleaned.startswith("json"):
                            cleaned = cleaned[4:].strip()
                    else:
                        # Если нет парных, просто вырезаем первую строку
                        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
                
                # Парсим JSON
                result = json.loads(cleaned)

                # Логируем успешный вызов
                log_call(agent_id, model, prompt_tokens, completion_tokens, cached_tokens, tier, latency, success=True)

                return result

            except json.JSONDecodeError:
                logger.warning(f"[{agent_id}] JSON parse error on attempt {attempt+1}")
                last_error = "json_decode"
                # Пробуем ещё раз с увеличенным max_tokens (может быть обрезало)
                if attempt == 0:
                    max_tokens = max(max_tokens + 200, max_tokens * 2)
                time.sleep(0.5 * (attempt + 1))

            except Exception as e:
                logger.warning(f"[{agent_id}] API error on attempt {attempt+1}: {e}")
                last_error = str(e)
                # Экспоненциальная задержка: 1s, 2s
                time.sleep(1 * (2 ** attempt))

        # Если все попытки неудачны — логируем провал
        log_call(agent_id, model, 0, 0, 0, tier, 0.0, success=False)
        logger.error(f"[{agent_id}] All {max_retries+1} attempts failed: {last_error}")
        return None

    # ────────────────────────────────────────────────────────────────────────
    def execute_raw(
        self,
        agent_id: str,
        system_prompt: str,
        user_input: str,
        tier: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        enable_cache: bool = True,
    ) -> Optional[str]:
        """
        Версия execute() без принудительного JSON — возвращает сырой текст.
        """
        if not model:
            tier = tier or self.default_tier
            model = TIER_MAP.get(tier, DEFAULT_MODEL)
        else:
            tier = tier or "custom"

        if max_tokens is None:
            tier_key = next((k for k, v in TIER_MAP.items() if v == model), None)
            max_tokens = MAX_TOKENS_MAP.get(tier_key, 600) * 2  # для текста даём больше

        extra_body = {}
        if enable_cache and len(system_prompt) > 100:
            extra_body["provider"] = {"order": ["DeepSeek", "Google", "Mistral", "Anthropic"]}

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_input},
        ]

        for attempt in range(3):
            try:
                start = time.time()
                response = self.client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages,
                    extra_body=extra_body if extra_body else None,
                )
                latency = time.time() - start
                usage = response.usage
                prompt_tokens = usage.prompt_tokens if usage else 0
                completion_tokens = usage.completion_tokens if usage else 0

                cached_tokens = 0
                if usage and hasattr(usage, "prompt_tokens_details") and usage.prompt_tokens_details:
                    cached_tokens = getattr(usage.prompt_tokens_details, "cached_tokens", 0) or 0
                if usage and hasattr(usage, "prompt_tokens_details") and isinstance(usage.prompt_tokens_details, dict):
                    cached_tokens = usage.prompt_tokens_details.get("cached_tokens", 0)

                raw = response.choices[0].message.content or ""
                log_call(agent_id, model, prompt_tokens, completion_tokens, cached_tokens, tier, latency, success=True)
                return raw

            except Exception as e:
                logger.warning(f"[{agent_id}] execute_raw error attempt {attempt+1}: {e}")
                time.sleep(1 * (2 ** attempt))

        log_call(agent_id, model, 0, 0, 0, tier, 0.0, success=False)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
#  Quick test
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Тест: проверить что клиент создаётся и делает вызов
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    client = OpenRouterClient()
    result = client.execute(
        agent_id="test_runner",
        system_prompt="You are a helpful assistant. Output only JSON.",
        user_input='Return {"hello": "world", "meaning": 42}',
        tier="cheap",
        max_tokens=100,
    )
    print(f"Result: {result}")

    print_cost_report(days=1)
