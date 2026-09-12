"""Трекер первичных и вторичных публичных размещений акций (IPO/SPO) на UZSE (Sprint 5)."""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

TASHKENT = timezone(timedelta(hours=5))

class IPOTracker:
    def __init__(self, db=None):
        self.db = db

    def get_upcoming_ipos(self) -> List[Dict[str, Any]]:

        """Получить список анонсированных IPO/SPO размещений на Ташкентской РФБ."""
        # Каноническая программа приватизации и IPO рынка Узбекистана
        events = [
            {
                "ticker": "SQBN",
                "company_name": "ПАО «Узпромстройбанк» (SQB)",
                "type": "SPO / Privatization",
                "underwriter": "Rothschild & Co / J.P. Morgan",
                "expected_date": "2026-Q4",
                "shares_offered_pct": 15.0,
                "status": "in_preparation",
                "notes": "Приватизация государственного пакета акций 15% международным инвесторам"
            },
            {
                "ticker": "AGMK",
                "company_name": "Алмалыкский ГМК (АГМК)",
                "type": "IPO",
                "underwriter": "Freedom Capital / Capitall",
                "expected_date": "2027-Q1",
                "shares_offered_pct": 5.0,
                "status": "announced",
                "notes": "Народное IPO для граждан РУз и международных фонда"
            },
            {
                "ticker": "NKMK",
                "company_name": "Навоийский ГМК (НГМК)",
                "type": "IPO",
                "underwriter": "Citi / BofA",
                "expected_date": "2026-Q4",
                "shares_offered_pct": 5.0,
                "status": "in_preparation",
                "notes": "Крупнейшее размещение золотодобывающего гиганта Узбекистана"
            }
        ]
        return events
