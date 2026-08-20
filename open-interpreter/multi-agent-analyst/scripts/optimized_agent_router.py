#!/usr/bin/env python3
"""
Optimised Agent Router — production module for OpenRouter multi-agent orchestration.

=== What this module does ===
1. Prompt caching (Anthropic models via OpenRouter) for shared system context
2. Strict JSON / Structured Output — max_tokens discipline, fallback parsing
3. Cascading Model Routing — Tier 1 (cheap) → Tier 2 (quality)
4. Confidence-based action filtering (≥0.7 → recommend, else → SKIP)
5. Cost & latency tracker with per-agent report
6. Retry logic with exponential backoff

=== Requirements ===
    pip install openai

=== Usage ===
    export OPENROUTER_API_KEY="sk-or-v1-..."

    router = OptimizedAgentRouter()
    result = router.execute_agent_turn(
        agent_id="hh_parser",
        system_prompt=COMMON_SYSTEM_PROMPT,
        user_input="Проверь вакансии DevOps в Ташкенте",
        model="deepseek/deepseek-chat",
        max_tokens=300,
        enable_cache=True
    )
    router.print_cost_report()
"""

import os
import json
import time
import sys
from typing import Any, Dict, Optional, List

try:
    from openai import OpenAI
except ImportError:
    print("❌ Установите openai: pip install openai")
    sys.exit(1)


# ──────────────────────────────────────────────
# Model pricing (OpenRouter approximate $/1M tokens)
# ──────────────────────────────────────────────
MODEL_PRICING = {
    "google/gemini-2.5-flash":               {"input": 0.05,  "output": 0.20},
    "google/gemini-2.0-flash-001":            {"input": 0.05,  "output": 0.20},
    "deepseek/deepseek-chat":                 {"input": 0.14,  "output": 0.28},
    "deepseek/deepseek-chat-v3-0324":        {"input": 0.14,  "output": 0.28},
    "deepseek/deepseek-v4-flash":            {"input": 0.08,  "output": 0.16},
    "anthropic/claude-sonnet-4-20250514":     {"input": 3.00,  "output": 15.00},
    "anthropic/claude-3.5-sonnet":            {"input": 3.00,  "output": 15.00},
    "anthropic/claude-3-haiku":               {"input": 0.25,  "output": 1.25},
    "qwen/qwen-2.5-7b-instruct":              {"input": 0.02,  "output": 0.04},
    "qwen/qwen-2.5-72b-instruct":             {"input": 0.20,  "output": 0.40},
}

# Models that support prompt caching via OpenRouter
CACHE_CAPABLE_MODELS = {
    "anthropic/claude-sonnet-4-20250514",
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-haiku",
    "anthropic/claude-opus-4",
}


class AgentStats:
    """Per-agent token + cost tracking."""

    def __init__(self):
        self.calls = 0
        self.prompt_tokens = 0
        self.cached_tokens = 0
        self.completion_tokens = 0
        self.latency_sum = 0.0
        self.errors = 0

    @property
    def estimated_cost_usd(self) -> float:
        """Approximate cost for the most common model (DeepSeek rates as fallback)."""
        return (self.prompt_tokens * 0.14 + self.completion_tokens * 0.28) / 1_000_000

    @property
    def saved_by_caching_usd(self) -> float:
        """90% discount on cached input tokens (Anthropic caching)."""
        return self.cached_tokens * 0.14 * 0.9 / 1_000_000


class OptimizedAgentRouter:
    """
    Multi-agent orchestrator with:
    - OpenRouter SDK (OpenAI-compatible)
    - Prompt caching (Anthropic models)
    - Structured JSON output
    - Cost & latency tracker
    - Retry logic
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        retries: int = 2,
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            print("⚠️  OPENROUTER_API_KEY не задан. Работа без API-ключа невозможна.")

        self.client = OpenAI(
            base_url=base_url,
            api_key=self.api_key,
            default_headers={
                "HTTP-Referer": "https://localhost",
                "X-Title": "MultiAgentAnalyst",
            },
        )
        self.retries = retries
        self.stats: Dict[str, AgentStats] = {}

    # ── main call ──────────────────────────────────────────

    def execute(
        self,
        agent_id: str,
        system_prompt: str,
        user_input: str,
        model: str = "deepseek/deepseek-chat",
        max_tokens: int = 400,
        temperature: float = 0.1,
        enable_cache: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute one agent turn and return parsed JSON.

        Parameters
        ----------
        agent_id : str
            Unique label for cost-tracking and logs.
        system_prompt : str
            Shared context / rules / schema for this agent.
        user_input : str
            The specific query for this agent.
        model : str
            OpenRouter model ID.
        max_tokens : int
            Hard limit on output (keeps costs predictable).
        temperature : float
            Low temp = stable JSON output.
        enable_cache : bool
            Send cache_control for Anthropic models.
        """
        if agent_id not in self.stats:
            self.stats[agent_id] = AgentStats()

        # ── build system block ──
        system_block = {"type": "text", "text": system_prompt}
        if enable_cache and model in CACHE_CAPABLE_MODELS:
            system_block["cache_control"] = {"type": "ephemeral"}

        # ── structured output instruction ──
        structured_input = (
            f"{user_input}\n\n"
            "STRICT REQUIREMENT: Ответь строго валидным JSON. "
            "Без markdown-разметки, без ```json блоков, без пояснений, без лишнего текста."
        )

        # ── attempt with retries ──
        last_error: Optional[str] = None
        for attempt in range(self.retries + 1):
            try:
                start = time.time()
                response = self.client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {
                            "role": "system",
                            "content": [system_block]
                            if enable_cache and model in CACHE_CAPABLE_MODELS
                            else system_prompt,
                        },
                        {"role": "user", "content": structured_input},
                    ],
                )
                latency = time.time() - start
                usage = response.usage
                raw = response.choices[0].message.content.strip()

                # ── log usage ──
                self._log(agent_id, usage, latency)

                # ── clean potential ```json wrappers ──
                cleaned = self._strip_json_fence(raw)

                # ── parse ──
                parsed = json.loads(cleaned)

                # ── validate has confidence (convention) ──
                if isinstance(parsed, dict) and "confidence" not in parsed:
                    parsed["confidence"] = 0.0

                return parsed

            except json.JSONDecodeError:
                last_error = f"JSONDecodeError: raw start → {raw[:120]}..."
                if attempt < self.retries:
                    wait = 1.0 * (attempt + 1)
                    print(f"  ⚠️  [{agent_id}] JSON error, retry {attempt+1}/{self.retries} "
                          f"after {wait:.0f}s")
                    time.sleep(wait)
                else:
                    self.stats[agent_id].errors += 1

            except Exception as exc:
                last_error = str(exc)
                self.stats[agent_id].errors += 1
                if attempt < self.retries:
                    wait = 2.0 * (attempt + 1)
                    print(f"  ⚠️  [{agent_id}] API error: {exc}, retry {attempt+1}/{self.retries} "
                          f"after {wait:.0f}s")
                    time.sleep(wait)

        print(f"  ❌ [{agent_id}] All retries exhausted. Last error: {last_error}")
        return None

    # ── internal helpers ──

    def _log(self, agent_id: str, usage: Any, latency: float):
        """Extract token counts from OpenRouter response."""
        stats = self.stats[agent_id]

        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        cached_tokens = 0

        # OpenRouter / Anthropic cached tokens
        details = getattr(usage, "prompt_tokens_details", None)
        if details:
            cached_tokens = getattr(details, "cached_tokens", 0) or 0
            if not cached_tokens:
                cached_tokens = getattr(details, "cache_read_input_tokens", 0) or 0

        stats.calls += 1
        stats.prompt_tokens += prompt_tokens
        stats.cached_tokens += cached_tokens
        stats.completion_tokens += completion_tokens
        stats.latency_sum += latency

    @staticmethod
    def _strip_json_fence(text: str) -> str:
        """Remove ```json ... ``` or ``` ... ``` wrappers."""
        t = text.strip()
        if t.startswith("```"):
            # Remove opening fence
            t = t.split("\n", 1)[-1] if "\n" in t else t[3:]
            # Remove closing fence
            if t.endswith("```"):
                t = t[:-3]
            # Handle ```json prefix
            if t.startswith("json"):
                t = t[4:]
        return t.strip()

    # ── utility methods ──

    def route(
        self,
        agent_id: str,
        system_prompt: str,
        user_input: str,
        tier1_model: str = "google/gemini-2.5-flash",
        tier2_model: str = "deepseek/deepseek-chat",
        tier1_max_tokens: int = 150,
        tier2_max_tokens: int = 400,
        threshold: float = 0.5,
    ) -> Optional[Dict[str, Any]]:
        """
        Cascade routing: try cheap Tier 1 first. If confidence < threshold,
        promote to expensive Tier 2.

        Parameters
        ----------
        threshold : float
            If Tier 1 returns confidence < threshold, route to Tier 2.
            Default 0.5 (low — let Tier 2 make the final call on anything uncertain).
        """
        # Tier 1 — fast + cheap
        tier1_result = self.execute(
            agent_id=f"{agent_id}_tier1",
            system_prompt=system_prompt,
            user_input=user_input,
            model=tier1_model,
            max_tokens=tier1_max_tokens,
            enable_cache=True,
        )

        if tier1_result is None:
            # Error → skip TIER 2 as well
            return None

        confidence = tier1_result.get("confidence", 0)
        action = tier1_result.get("action", "")

        if confidence >= threshold and action == "skip":
            # Cheap model confidently says skip — trust it
            return tier1_result

        if confidence >= threshold and action != "skip":
            # Cheap model confidently recommends action — return
            return tier1_result

        # Below threshold → promote to Tier 2
        print(f"  🔄 [{agent_id}] Promoted to Tier 2 (confidence={confidence:.2f} < {threshold})")
        tier2_result = self.execute(
            agent_id=f"{agent_id}_tier2",
            system_prompt=system_prompt,
            user_input=f"{user_input}\n\n[NOTE: Tier 1 returned low confidence. "
                       f"Provide thorough analysis.]",
            model=tier2_model,
            max_tokens=tier2_max_tokens,
            enable_cache=True,
        )
        return tier2_result

    def execute_batch(
        self,
        tasks: List[Dict[str, Any]],
        system_prompt: str,
        model: str = "deepseek/deepseek-chat",
        max_tokens: int = 300,
    ) -> List[Dict[str, Any]]:
        """
        Run multiple agents with the same system prompt.

        Each task dict: {"agent_id": str, "user_input": str, ...optional overrides}
        """
        results = []
        for task in tasks:
            result = self.execute(
                agent_id=task["agent_id"],
                system_prompt=system_prompt,
                user_input=task["user_input"],
                model=task.get("model", model),
                max_tokens=task.get("max_tokens", max_tokens),
            )
            if result:
                results.append(result)
        return results

    def print_report(self) -> None:
        """Print formatted cost report for all agents."""
        if not self.stats:
            print("\n📊 No agent data recorded.")
            return

        total_cost = 0.0
        total_saved = 0.0

        print(f"\n{'='*90}")
        print(f"{'AGENT ID':<22} {'CALLS':<6} {'IN TOK':<9} {'CACHED':<9} "
              f"{'OUT TOK':<9} {'AVG LAT':<9} {'EST $':<9} {'SAVED $':<9}")
        print(f"{'-'*90}")

        for agent_id, s in sorted(self.stats.items()):
            avg_lat = s.latency_sum / s.calls if s.calls > 0 else 0
            cost = s.estimated_cost_usd
            saved = s.saved_by_caching_usd
            total_cost += cost
            total_saved += saved
            err_mark = " ⚠️" if s.errors > 0 else ""
            print(f"{agent_id:<22} {s.calls:<6} {s.prompt_tokens:<9} {s.cached_tokens:<9} "
                  f"{s.completion_tokens:<9} {avg_lat:<9.2f} {cost:<9.6f} {saved:<9.6f}{err_mark}")

        print(f"{'='*90}")
        print(f"{'TOTAL':<22} {'':6} {'':9} {'':9} {'':9} {'':9} "
              f"{total_cost:<9.6f} {total_saved:<9.6f}")
        print(f"💰 Total estimated cost: ${total_cost:.6f}  |  Saved by caching: ${total_saved:.6f}")
        print(f"{'='*90}\n")


# ────────────────────────────────────────────────────────────
# CLI entry point
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import textwrap

    print("🚀 Multi-Agent Analyst — Demo\n")

    COMMON_PROMPT = textwrap.dedent("""\
    Ты финансовый аналитик. Анализируй запрос и ответь JSON.

    Правила:
    1. Используй минимум 2 источника информации.
    2. Если confidence < 0.7 → action = "skip".
    3. Отвечай ТОЛЬКО валидным JSON.

    Формат ответа:
    {
      "action": "buy|sell|skip",
      "ticker": "string",
      "price": 0.0,
      "confidence": 0.0,
      "reason": "string"
    }
    """)

    tasks = [
        {"agent_id": "hh_monitor",   "user_input": "Проверь новые вакансии DevOps в Ташкенте за последний час"},
        {"agent_id": "aapl_analyst", "user_input": "Дай рекомендацию по акциям AAPL на сегодня"},
        {"agent_id": "tsla_analyst", "user_input": "Дай рекомендацию по акциям TSLA на сегодня"},
        {"agent_id": "news_digest",  "user_input": "Сводка главных tech-новостей за сегодня"},
    ]

    router = OptimizedAgentRouter()
    if not router.api_key:
        print("⚠️  OPENROUTER_API_KEY не задан. Пропускаю вызовы API.\n")
        print("📋 Для реального запуска: export OPENROUTER_API_KEY=\"sk-or-v1-...\"")
        print("\n" + "=" * 60)
        print("📦 Структура ответа (один агент):")
        print(json.dumps({
            "action": "buy|sell|skip",
            "ticker": "AAPL",
            "price": 150.0,
            "confidence": 0.85,
            "reason": "Сильные квартальные результаты, рост выручки 15%"
        }, indent=2, ensure_ascii=False))
        sys.exit(0)

    results = router.execute_batch(tasks, system_prompt=COMMON_PROMPT, model="deepseek/deepseek-chat")

    print("\n📊 RESULTS:")
    for r in results:
        mark = "✅" if r.get("confidence", 0) >= 0.7 else "⏭️"
        print(f"  {mark} {r.get('ticker', r.get('action','?')):>8}  "
              f"conf={r.get('confidence',0):.2f}  → {r.get('action','?'):>6}  "
              f"| {r.get('reason','')[:80]}")

    router.print_report()
