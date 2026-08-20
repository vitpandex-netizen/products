"""Researcher v3 — OpenRouter API + LLM + сообщества. Совместимость с vault DB."""

import sys, os, json, time, re, logging
from pathlib import Path
from typing import Optional
import requests
from dotenv import load_dotenv

_BASE = Path(__file__).resolve().parent.parent
load_dotenv(_BASE / '.env')
sys.path.insert(0, str(_BASE)); sys.path.insert(0, str(_BASE.parent))

from src.db import PassiveIncomeDB
from shared.net import force_ipv4
force_ipv4()

from shared.llm import llm as shared_llm
logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "пассивный доход Узбекистан 2026 идеи",
    "passive income ideas Uzbekistan 2026",
    "remote IT jobs infrastructure DevOps 2026",
    "how to make money online Uzbekistan 2026",
    "лучшие инвестиции Узбекистан 2026",
    "дистанционная работа из Узбекистана IT специалист",
    "digital nomad income sources Uzbekistan 2026",
    "аренда недвижимости Ташкент доходность 2026",
    "фриланс платформы для узбекистанцев удаленная работа",
]

COMMUNITY_SOURCES = [
    {"name": "r/passive_income", "query": "reddit passive income ideas 2026"},
    {"name": "r/digitalnomad", "query": "reddit digital nomad income remote"},
    {"name": "r/sidehustle", "query": "reddit side hustle passive income 2026"},
    {"name": "r/devops", "query": "reddit devops remote contract freelance 2026"},
    {"name": "r/freelance", "query": "reddit freelance remote IT 2026"},
    {"name": "r/Uzbekistan", "query": "reddit Uzbekistan business investment"},
    {"name": "Telegram/форумы UZ", "query": "форум Узбекистан пассивный доход"},
]

SEARCH_PROMPT = '''Ты — аналитик по пассивному доходу. Найди 1-2 идеи по теме: "{query}"
Контекст: IT Director, 19+ лет, Ташкент. Цель: пассивный доход или удалённая работа.
Для каждой: title, description, category (investments/real_estate/digital_products/content/affiliate/automated_biz/freelance/crypto/local_biz)
Ответь ТОЛЬКО JSON: [{{"title":"...","description":"...","category":"..."}}]'''

EVAL_PROMPT = '''Оцени идею 1-10: {title}
{description}
Источник: {source}
Контекст: IT Director из Ташкента.
Оцени: capital_needed(1-10), expected_return(1-10), effort_startup(1-10), effort_maint(1-10), payback_months(число), risk_level(1-10), applicability_local(1-10), remote_friendly(1-10)
Ответь ТОЛЬКО JSON: {{"capital":N,"return":N,"effort_start":N,"effort_maint":N,"payback":N,"risk":N,"local":N,"remote":N}}'''


class Researcher:
    def __init__(self, db: PassiveIncomeDB):
        self.db = db
        self._session = None

    def _llm(self, prompt, max_tokens=500, temp=0.5, task="text"):
        """LLM call via shared router (Ling-2.6-flash default)."""
        return shared_llm(prompt, task=task, max_tokens=max_tokens, temperature=temp) or ""

    def search_and_evaluate(self, max_ideas=15):
        logger.info("🔍 Research v3 starting...")
        results = []

        # Phase 1: Web search
        for q in SEARCH_QUERIES:
            content = self._llm(SEARCH_PROMPT.format(query=q), max_tokens=600, task="text")
            if not content:
                continue
            parsed = self._parse_json(content)
            if parsed:
                for item in parsed:
                    if isinstance(item, dict) and "title" in item:
                        results.append({**item, "source": f"web:{q[:30]}"})
            time.sleep(3)

        # Phase 2: Community sources
        for src in COMMUNITY_SOURCES:
            content = self._llm(SEARCH_PROMPT.format(query=src["query"]), max_tokens=600, task="text")
            if not content:
                continue
            parsed = self._parse_json(content)
            if parsed:
                for item in parsed:
                    if isinstance(item, dict) and "title" in item:
                        results.append({**item, "source": src["name"]})
            time.sleep(3)

        # Save to DB
        new_count = 0
        for item in results:
            if not self.db.idea_exists(item["title"]):
                idea_id = self.db.add_idea(
                    title=item["title"],
                    description=item.get("description", ""),
                    category=item.get("category", "other"),
                    source=item.get("source", ""),
                    source_url="",
                    source_type="llm"
                )
                if idea_id:
                    # Evaluate
                    eval_content = self._llm(
                        EVAL_PROMPT.format(title=item["title"], description=item.get("description","")[:200], source=item.get("source","")),
                        max_tokens=400, task="eval"
                    )
                    eval_data = self._parse_json(eval_content)
                    if eval_data and isinstance(eval_data, dict):
                        self.db.evaluate(
                            idea_id,
                            capital=eval_data.get("capital", 5),
                            expected_return=eval_data.get("return", 5),
                            effort_startup=eval_data.get("effort_start", 5),
                            effort_maint=eval_data.get("effort_maint", 5),
                            payback=eval_data.get("payback", 12),
                            risk=eval_data.get("risk", 5),
                            applicability=eval_data.get("local", 5),
                            remote=eval_data.get("remote", 5),
                        )
                    new_count += 1
                    time.sleep(2)

            if len([r for r in results if not self.db.idea_exists(r["title"])]) >= max_ideas:
                break

        logger.info(f"✅ Research done: {len(results)} total, {new_count} new")
        self.db.add_run("research", len(results), new_count, f"Research: {new_count} new ideas")
        return {"total": len(results), "total_new": new_count, "results": results}

    def _parse_json(self, text):
        """Safe JSON parser — handles code fence wrapping."""
        if not text:
            return None
        text = text.strip()
        # Remove ```json ... ``` fences
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try find first { or [
            for start_char, end_char in [('[', ']'), ('{', '}')]:
                start = text.find(start_char)
                if start >= 0:
                    end = text.rfind(end_char)
                    if end > start:
                        try:
                            return json.loads(text[start:end+1])
                        except json.JSONDecodeError:
                            pass
            logger.warning(f"JSON parse failed for: {text[:100]}...")
            return None

    def format_report(self, ideas):
        if not ideas:
            return "<i>Идей пока нет</i>"
        lines = ["<b>📊 Пассивный доход — рейтинг идей</b>", ""]
        for i, idea in enumerate(ideas[:15], 1):
            score = idea.get("total_score", 0) or 0
            cat = idea.get("category", "other")
            badge = "🆕" if idea.get("status") in ("new", None) else "🔄"
            bar_len = max(1, min(10, round(score / 10)))
            bar = "▓" * bar_len + "░" * (10 - bar_len)
            lines.append(f"{i}. {badge} <b>{idea['title'][:55]}</b>")
            lines.append(f"   {bar} {score:.0f}/100 | {cat}")
        return "\n".join(lines)
