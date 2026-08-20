"""Passive Income — Main. v4 с профилем, авто-действиями, сканером."""

import sys, os, logging
from pathlib import Path
from datetime import datetime, timezone, timedelta

_BASE = Path(__file__).resolve().parent.parent
os.chdir(str(_BASE)); sys.path.insert(0, str(_BASE)); sys.path.insert(0, str(_BASE.parent))

from dotenv import load_dotenv
load_dotenv(_BASE / '.env')
from shared.net import force_ipv4
from src.db import PassiveIncomeDB
from src.researcher import Researcher
from src.scanner import OpportunityScanner
from src.auto_actions import AutoActions
from src.telegram import TelegramNotifier
force_ipv4()

TASHKENT_TZ = timezone(timedelta(hours=5))
logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL","INFO")), format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.StreamHandler()])
logger = logging.getLogger("passive-income")


def show_report():
    db = PassiveIncomeDB(); researcher = Researcher(db); scanner = OpportunityScanner(db); notifier = TelegramNotifier()
    ranked = db.get_ranked_ideas(limit=20); stats = db.get_stats()
    ideas = [i for i in ranked if not i.get("title","").startswith("💼")]
    offers = [i for i in ranked if i.get("title","").startswith("💼")]
    report = researcher.format_report(ideas)
    offers_report = scanner.format_offers_report(offers) if offers else ""
    header = f"📊 <b>Passive Income — сводка</b>\n📅 {datetime.now(TASHKENT_TZ).strftime('%d.%m.%Y %H:%M')}\n━━━━━━━━━━━━━━━━━\nИдей: {stats['total_ideas']} | Офферов: {len(offers)} | В работе: {stats['in_progress']}\n\n"
    full = header + report
    if offers_report: full += "\n━━━━━━━━━━━━━━━━━\n\n" + offers_report
    print(full); notifier.send_report(full)


def run_research():
    logger.info("🚀 Research run started...")
    db = PassiveIncomeDB(); researcher = Researcher(db); scanner = OpportunityScanner(db); aa = AutoActions(db); notifier = TelegramNotifier()
    result = researcher.search_and_evaluate(max_ideas=15)
    scan_result = scanner.scan_opportunities(max_offers=10)
    n = aa.auto_trigger(min_score=70)
    aa.process_all()
    ranked = db.get_ranked_ideas(limit=20); stats = db.get_stats()
    ideas = [i for i in ranked if not i.get("title","").startswith("💼")]
    offers = [i for i in ranked if i.get("title","").startswith("💼")]
    report = researcher.format_report(ideas)
    offers_report = scanner.format_offers_report(offers) if offers else ""
    pending = db.get_pending_actions()
    header = f"🔬 <b>Passive Income — исследование + сканирование</b>\n📅 {datetime.now(TASHKENT_TZ).strftime('%d.%m.%Y %H:%M')}\n━━━━━━━━━━━━━━━━━\nНовых идей: {result['total_new']} | Офферов: {scan_result['total_new']} | Действий: {len(pending)}\n\n"
    full = header + report
    if offers_report: full += "\n━━━━━━━━━━━━━━━━━\n\n" + offers_report
    if pending: full += f"\n⚡ <b>Авто-действий в очереди:</b> {len(pending)}"
    print(full); notifier.send_report(full)
    research_dir = _BASE / "research"; research_file = research_dir / f"{datetime.now(TASHKENT_TZ).strftime('%Y-%m-%d-%H%M')}-research.md"
    research_file.write_text(f"# Research: {datetime.now(TASHKENT_TZ).strftime('%Y-%m-%d %H:%M')}\n\n{full}", encoding="utf-8")
    logger.info(f"📝 Saved to {research_file}")


if __name__ == "__main__":
    if "--research" in sys.argv: run_research()
    else: show_report()
