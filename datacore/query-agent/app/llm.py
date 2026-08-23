"""LLM glue — generates SQL from natural language via OpenRouter."""

import json
import logging
import os
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEFAULT_MODEL = os.getenv("QUERY_MODEL", "qwen/qwen3.7-flash")
PRO_MODEL = os.getenv("QUERY_PRO_MODEL", "deepseek/deepseek-v4-pro-0813")


def _build_system_prompt(schema: list[dict]) -> str:
    lines = []
    for t in schema[:20]:
        cols = "\n    ".join(
            f"- {c['name']} ({c['type']}){' nullable' if c['nullable'] else ' NOT NULL'}"
            for c in t["columns"][:20]
        )
        lines.append(f"### {t['name']}\n    {cols}")
    return f"""Ты — DataCore SQL Agent. Генерируй PostgreSQL SELECT.

Схема БД:
{chr(10).join(lines)}

Правила:
- Только SELECT
- Используй существующие таблицы и колонки
- LIMIT 100 если не указано иное
- Если данных нет в схеме — ответь NEED_MORE_DATA: <что нужно>
- Ответь ТОЛЬКО SQL, без объяснений, без markdown"""


async def generate_sql(question: str, schema: list[dict],
                       model: Optional[str] = None,
                       temperature: float = 0.1) -> tuple[Optional[str], str, float]:
    """Returns (sql, explanation, generation_time_ms) or (None, error, time)."""
    selected = model or DEFAULT_MODEL
    logger.info("LLM: model=%s q='%s'", selected, question[:60])

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://datacore.query-agent",
    }
    payload = {
        "model": selected,
        "messages": [
            {"role": "system", "content": _build_system_prompt(schema)},
            {"role": "user", "content": question},
        ],
        "temperature": temperature,
        "max_tokens": 2000,
    }

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        logger.error("LLM call failed: %s", e)
        return None, str(e), round(elapsed, 1)

    elapsed = (time.monotonic() - start) * 1000
    content = data["choices"][0]["message"]["content"].strip()

    # Clean markdown fences
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    if content.upper().startswith("SELECT") or content.upper().startswith("WITH"):
        return content, "", round(elapsed, 1)

    return None, f"Unexpected response: {content[:200]}", round(elapsed, 1)


async def explain(question: str, sql: str, columns: list[str],
                  rows: list[list], model: Optional[str] = None) -> str:
    """Generate natural-language explanation of query results."""
    selected = model or DEFAULT_MODEL
    sample = f"Columns: {columns}\nFirst {min(5, len(rows))} rows: {rows[:5]}"
    prompt = (
        f"Question: {question}\nSQL: {sql}\n{sample}\n\n"
        f"Explain in Russian what this data shows. Keep it concise."
    )
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://datacore.query-agent",
    }
    payload = {
        "model": selected,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 500,
    }
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Could not generate explanation: {e}"