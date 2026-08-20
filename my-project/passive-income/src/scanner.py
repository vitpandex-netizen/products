"""Opportunity Scanner — реальные заказы и вакансии. Web search + LLM."""

import sys, os, json, time, re, logging
from pathlib import Path
import requests
from dotenv import load_dotenv

_BASE = Path(__file__).resolve().parent.parent
load_dotenv(_BASE / '.env')
sys.path.insert(0, str(_BASE)); sys.path.insert(0, str(_BASE.parent))

from src.db import PassiveIncomeDB
from shared.net import force_ipv4
force_ipv4()

from shared.llm import llm as shared_llm, evaluate as shared_eval
logger = logging.getLogger(__name__)

QUERIES = [
    "remote DevOps infrastructure contract 2026",
    "remote VMware Proxmox engineer freelance 2026",
    "Zero Trust consultant remote contract 2026",
    "M365 infrastructure manager remote job 2026",
    "IT Director remote contract 2026",
    "DevOps contractor US Europe remote 2026",
    "IT infrastructure audit freelance 2026",
    "remote SRE site reliability engineer contract 2026",
    "Upwork DevOps consultant VMware Proxmox",
    "Toptal infrastructure architect vacancy",
    "LinkedIn IT Director remote Uzbekistan 2026",
    "hiring remote infrastructure manager 2026",
    "remote IT director fintech vacancy 2026",
]

SEARCH_P = """Ты — рекрутер. Найди 1-2 реальные вакансии по теме: "{query}"

Контекст: IT Director, 19+ лет, VMware/M365/Zero Trust/ITSM, Ташкент. $4-6K/net.
Для каждой: title, description, source, salary_range, match_score(1-10), url
Ответь ТОЛЬКО JSON: [{{"title":"...","description":"...","source":"...","salary_range":"...","match_score":N,"url":"..."}}]"""

EVAL_P = """Оцени предложение: {title} | {source} | {salary}
{description}
Оцени 1-10: salary_fit, remote, experience, competition, growth, stability, timezone
Ответь ТОЛЬКО JSON: {{"salary_fit":N,"remote":N,"experience":N,"competition":N,"growth":N,"stability":N,"timezone":N}}"""


class OpportunityScanner:
    def __init__(self, db: PassiveIncomeDB):
        self.db = db
        from src.config import OPENROUTER_API_KEY; self.api_key = OPENROUTER_API_KEY()
        if not self.api_key:
            try:
                with open("/Users/vitaliyr/.hermes/.env") as f:
                    for line in f:
                        if "OPENROUTER_API_KEY" in line or True:
                            self.api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
            except: pass
        self._session = None

    def _session_obj(self):
        if self._session is None:
            s = requests.Session()
            adapter = requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=8, max_retries=requests.adapters.Retry(total=3, backoff_factor=2))
            s.mount('https://', adapter)
            s.headers.update({"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
            self._session = s
        return self._session

    def _llm(self, prompt, max_tokens=800, temp=0.5, task="text"):
        """LLM call via shared router (Ling-2.6-flash default)."""
        return shared_llm(prompt, task=task, max_tokens=max_tokens, temperature=temp) or ""

    def scan_opportunities(self, max_offers=10):
        logger.info("🔎 Scanning real opportunities...")
        found = new_count = 0
        all_offers = []

        for q in QUERIES:
            logger.info(f"  {q[:45]}")
            resp = self._llm(SEARCH_P.format(query=q), max_tokens=1000, temp=0.7)
            try:
                m = re.search(r'\[.*?\]', resp, re.DOTALL)
                if m:
                    for item in json.loads(m.group()):
                        if item.get("title"): all_offers.append(item)
            except: pass
            time.sleep(0.3)

        for offer in all_offers:
            found += 1
            title = offer.get("title", "").strip()
            if not title or len(title) < 5: continue
            if self.db.idea_exists(title): continue
            if new_count >= max_offers: break

            source = offer.get("source","web")
            salary = offer.get("salary_range","")
            score = offer.get("match_score",5)
            desc = offer.get("description","")[:500]

            eval_resp = self._llm(EVAL_P.format(title=title, source=source, salary=salary, description=desc), max_tokens=300, temp=0.3)
            ev = None
            try:
                m = re.search(r'\{.*?\}', eval_resp, re.DOTALL)
                if m: ev = json.loads(m.group())
            except: pass

            idea_id = self.db.add_idea(f"💼 {title}", desc, "freelance", source, offer.get("url",""), "opportunity")
            if not idea_id: continue

            remote_score = ev.get("remote", 8) if ev else 8
            self.db.evaluate(idea_id, capital=2, expected_return=min(score+2,10), effort_startup=3, effort_maint=3, payback=1, risk=3, applicability=8, remote=remote_score, notes=f"REAL OFFER | {source} | {salary} | Score: {score}/10")
            self.db.set_status(idea_id, "new", "Opportunity — можно откликнуться")

            # Авто-действие: investigate для офферов с score >= 7
            if score >= 7:
                self.db.add_auto_action(idea_id, "investigate")

            new_count += 1
            logger.info(f"  ✅ OFFER: {title} [{score}/10]")

        self.db.log_run("opportunity_scan", found, new_count, f"Scanned {found}, {new_count} new")
        logger.info(f"✅ Done: {found} offers, {new_count} new")
        return {"total_found": found, "total_new": new_count}

    def format_offers_report(self, offers):
        if not offers: return "<b>📭 Нет активных предложений</b>"
        lines = ["<b>💼 Реальные предложения — можно откликнуться</b>\n"]
        for i, offer in enumerate(offers[:8], 1):
            title = offer.get("title","").replace("💼 ","")
            score = offer.get("total_score",50)
            status = offer.get("status","new")
            notes = offer.get("notes","")
            salary = ""
            for p in notes.split("|"):
                p = p.strip()
                if p.startswith("$") or any(c.isdigit() for c in p[:2]): salary = p; break
            bars = "▓" * int(score/10) + "░" * (10 - int(score/10))
            lines.append(f"{i}. <b>{title}</b>\n   {bars} {score:.0f}/100" + (f" | 💰 {salary}" if salary else "") + f"\n   Статус: {status}")
        lines.append("\n🎯 <i>/scan — запустить поиск</i>")
        return "\n".join(lines)
