"""
HH.uz Parser — scraping tashkent.hh.uz search results (API requires OAuth).
Парсит вакансии, сохраняет в SQLite.

Usage:
    python src/hh_parser.py --search "IT Manager" --min-salary 45000000
    python src/hh_parser.py --list          # show recent
"""

import html
import logging
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.models import Vacancy
from shared.db import Database

logger = logging.getLogger(__name__)


def _contains_excluded(text: str, keywords: list) -> bool:
    """True if any exclude keyword occurs in `text` (already lowercased) as
    a whole word/phrase. Uses word boundaries, not a raw substring check —
    otherwise a short exclude term like "техник" would false-match inside
    "техника безопасности" (standard boilerplate on nearly every posting)
    and wrongly drop good vacancies. Better to under-exclude than to
    silently hide a vacancy the user should have seen.
    """
    for kw in keywords:
        kw = kw.strip().lower()
        if not kw:
            continue
        if re.search(rf"\b{re.escape(kw)}\b", text):
            return True
    return False


# --- Constants ---
HH_BASE_URL = "https://tashkent.hh.uz"
HH_SEARCH_URL = f"{HH_BASE_URL}/search/vacancy"
REQUEST_DELAY = 1.5
MAX_PAGES = 5
PER_PAGE = 20

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}


class HHParser:
    """Scrape HH.uz vacancy search results."""

    def __init__(self, db: Database):
        self.db = db
        self._ensure_table()

    def _ensure_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY,
            title TEXT,
            company TEXT,
            url TEXT,
            salary_from INTEGER,
            salary_to INTEGER,
            salary_currency TEXT,
            description TEXT,
            skills TEXT,
            experience TEXT,
            employment_type TEXT,
            location TEXT,
            matched_score REAL DEFAULT 0,
            responded_at TEXT,
            notified_at TEXT,
            digested_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
        self.db.create_table(query)
        # Backfill columns for DBs created before notified_at/digested_at/location existed.
        existing = {row["name"] for row in self.db.execute("PRAGMA table_info(vacancies)")}
        for column in ("notified_at", "digested_at", "location"):
            if column not in existing:
                self.db.execute_update(f"ALTER TABLE vacancies ADD COLUMN {column} TEXT")

    def search(self, keywords: str, area: int = 0, min_salary: int = 0,
               period: int = 3, exclude_keywords: list = None) -> list:
        """Search vacancies, return list of Vacancy objects."""
        # Try RSS first (DDoS-Guard blocks HTML API)
        try:
            rss_results = self._rss_search(keywords, area, period)
            if rss_results:
                logger.info(f"RSS search returned {len(rss_results)} vacancies")
                return rss_results
        except Exception as e:
            logger.warning(f"RSS search failed, falling back to HTML: {e}")
        
        all_vacancies = []
        exclude = exclude_keywords or []

        # HH.uz search works best with a single short keyword.
        # Iterate through all keywords from the comma-separated list.
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip() and len(k.strip()) > 2]
        seen_ids = set()

        for search_text in keyword_list:
            logger.info(f"Searching HH.uz with: '{search_text}'")

            for page in range(MAX_PAGES):
                logger.info(f"  Page {page + 1}/{MAX_PAGES}...")
                params = {
                    "text": search_text,
                    "page": page,
                    "per_page": PER_PAGE,
                    "order_by": "publication_time",
                    "period": period,
                }
                if area > 0:
                    params["area"] = area
                if min_salary > 0:
                    params["salary"] = min_salary

                try:
                    resp = requests.get(
                        HH_SEARCH_URL, params=params, headers=HEADERS, timeout=20
                    )
                    resp.raise_for_status()
                except requests.RequestException as e:
                    logger.error(f"HTTP error on page {page + 1}: {e}")
                    break

                page_vacancies = self._parse_search_results(resp.text)

                if not page_vacancies:
                    logger.info("No vacancies found on this page.")
                    break

                # Filter exclude keywords (title/company/location — description
                # isn't available yet at this stage, see save_vacancies() for
                # the second, description-aware pass) + dedup
                for vac in page_vacancies:
                    if vac.id in seen_ids:
                        continue
                    combined = f"{vac.title} {vac.company} {vac.location}".lower()
                    if _contains_excluded(combined, exclude):
                        continue
                    seen_ids.add(vac.id)
                    all_vacancies.append(vac)

                # Check for next page
                soup = BeautifulSoup(resp.text, "lxml")
                next_page = soup.find("a", attrs={"data-qa": "pager-next"})
                if not next_page:
                    break

                time.sleep(REQUEST_DELAY)

        logger.info(f"Total unique vacancies found: {len(all_vacancies)} ({len(seen_ids)} unique)")
        return all_vacancies

    def _rss_search(self, keywords: str, area: int = 97, period: int = 7) -> list:
        """RSS-based search (bypasses DDoS-Guard)."""
        import requests as req
        import xml.etree.ElementTree as ET
        import html as html_mod
        all_vacancies = []
        seen_ids = set()
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        
        for keyword in keyword_list:
            url = f"https://hh.ru/search/vacancy/rss?text={keyword}&area={area}&period={period}"
            try:
                resp = req.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code != 200:
                    continue
                root = ET.fromstring(resp.content)
                for item in root.findall(".//item"):
                    title_el = item.find("title")
                    link_el = item.find("link")
                    desc_el = item.find("description")
                    title = title_el.text if title_el is not None else ""
                    link = link_el.text if link_el is not None else ""
                    # Fix domain: hh.ru → tashkent.hh.uz
                    link = link.replace("hh.ru", "tashkent.hh.uz")
                    desc = desc_el.text if desc_el is not None else ""
                    desc_clean = html_mod.unescape(desc) if desc else ""
                    company = ""
                    location = ""
                    for line in desc_clean.split("<p>"):
                        line_clean = line.replace("</p>", "").strip()
                        if "Вакансия компании:" in line_clean:
                            company = line_clean.split(":", 1)[1].strip()
                        elif "Регион:" in line_clean:
                            location = line_clean.split(":", 1)[1].strip()
                    
                    vac_id = 0
                    id_match = re.search(r'/vacancy/(\d+)', link)
                    if id_match:
                        vac_id = int(id_match.group(1))
                    
                    if vac_id and vac_id not in seen_ids:
                        seen_ids.add(vac_id)
                        from shared.models import Vacancy
                        vac = Vacancy(
                            id=vac_id,
                            title=title,
                            company=company or "",
                            url=link,
                            description=desc_clean[:500],
                            location=location,
                        )
                        all_vacancies.append(vac)
                time.sleep(1.5)
            except Exception as e:
                logger.warning(f"RSS error for '{keyword}': {e}")
                continue
        return all_vacancies
    
    def _parse_search_results(self, html: str) -> list:
        """Parse HTML search results page."""
        soup = BeautifulSoup(html, "lxml")
        vacancies = []

        # Primary: find by data-qa attribute
        cards = soup.find_all("div", attrs={"data-qa": "vacancy-serp__vacancy"})
        if not cards:
            # Fallback: vacancy-card class
            cards = soup.find_all("div", class_=lambda c: c and "vacancy-card" in (c or ""))

        for card in cards:
            try:
                vac = self._extract_from_card(card)
                if vac:
                    vacancies.append(vac)
            except Exception as e:
                logger.debug(f"Error parsing card: {e}")
                continue

        return vacancies

    def _extract_from_card(self, card) -> Optional[Vacancy]:
        """Extract Vacancy from a search result card."""
        # Vacancy ID from card id attribute or link
        card_id = card.get("id", "")
        if not card_id:
            # Try to find from link
            link_tag = card.find("a", attrs={"data-qa": "serp-item__title"})
            if not link_tag:
                link_tag = card.find("a", href=re.compile(r"/vacancy/\d+"))
            if not link_tag:
                return None
            href = link_tag.get("href", "")
            match = re.search(r"/vacancy/(\d+)", href)
            if not match:
                return None
            card_id = match.group(1)

        vac_id = int(card_id)

        # Title
        title = ""
        title_link = card.find("a", attrs={"data-qa": "serp-item__title"})
        if title_link:
            title_text = title_link.find("span", attrs={"data-qa": "serp-item__title-text"})
            title = title_text.get_text(strip=True) if title_text else title_link.get_text(strip=True)
        if not title:
            title_link = card.find("a", href=re.compile(r"/vacancy/"))
            title = title_link.get_text(strip=True) if title_link else ""

        # URL
        url = ""
        if title_link:
            url = title_link.get("href", "")
            if url and not url.startswith("http"):
                url = HH_BASE_URL + url

        # Company
        company = ""
        company_tag = card.find("a", attrs={"data-qa": "vacancy-serp__vacancy-employer"})
        if company_tag:
            company = company_tag.get_text(strip=True)
        if not company:
            company_tag = card.find("span", attrs={"data-qa": "vacancy-serp__vacancy-employer-text"})
            company = company_tag.get_text(strip=True) if company_tag else ""

        # Location
        location_tag = card.find("span", attrs={"data-qa": "vacancy-serp__vacancy-address"})
        location = location_tag.get_text(strip=True) if location_tag else ""

        # Salary — look for compensation text in the card
        salary_from = salary_to = salary_currency = None
        # Try to find salary in nested spans with typography
        salary_elements = card.find_all(
            "span", attrs={"data-qa": lambda v: v and "compensation" in (v or "").lower()}
        )
        for el in salary_elements:
            text = el.get_text(strip=True)
            parsed = self._parse_salary(text)
            if parsed.get("from") or parsed.get("to"):
                salary_from = parsed.get("from")
                salary_to = parsed.get("to")
                salary_currency = parsed.get("currency", "UZS")
                break

        # If not found, search any element in card with currency symbols
        if not salary_from and not salary_to:
            for el in card.find_all(string=lambda t: t and ("сум" in t.lower() or "₽" in t or "$" in t)):
                parsed = self._parse_salary(str(el))
                if parsed.get("from") or parsed.get("to"):
                    salary_from = parsed.get("from")
                    salary_to = parsed.get("to")
                    salary_currency = parsed.get("currency", "UZS")
                    break

        # Experience
        exp_tag = card.find("span", attrs={"data-qa": lambda v: v and "work-experience" in (v or "")})
        experience = exp_tag.get_text(strip=True) if exp_tag else ""

        return Vacancy(
            id=vac_id,
            title=title,
            company=company,
            url=url,
            salary_from=salary_from,
            salary_to=salary_to,
            salary_currency=salary_currency,
            description="",
            experience=experience,
            employment_type="",
            location=location,
            skills=[],
        )

    def _parse_salary(self, text: str) -> dict:
        """Parse salary text. HH.uz uses 'сум' (UZS)."""
        result = {"from": None, "to": None, "currency": None}

        if not text:
            return result

        text = text.replace("\u202f", " ").replace("\xa0", " ")

        # Determine currency
        if "сум" in text.lower() or "uzs" in text.lower():
            result["currency"] = "UZS"
        elif "₽" in text or "rub" in text.lower():
            result["currency"] = "RUB"
        elif "$" in text or "usd" in text.lower():
            result["currency"] = "USD"

        # Extract numbers
        numbers = re.findall(r"\d[\d\s]*\d", text)
        numbers = [int(n.replace(" ", "")) for n in numbers]

        text_lower = text.lower()
        if "от" in text_lower and numbers:
            result["from"] = numbers[0]
        elif "до" in text_lower and numbers:
            result["to"] = numbers[0]
        elif len(numbers) >= 2:
            result["from"] = numbers[0]
            result["to"] = numbers[1]
        elif len(numbers) == 1:
            result["from"] = numbers[0]

        return result

    def get_details(self, vacancy_id: int, session: requests.Session = None) -> dict:
        """Fetch and parse vacancy detail page for description and skills."""
        url = f"{HH_BASE_URL}/vacancy/{vacancy_id}"
        s = session or requests.Session()
        try:
            resp = s.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch details for {vacancy_id}: {e}")
            return {"description": "", "skills": []}

        soup = BeautifulSoup(resp.text, "lxml")
        result = {}

        # Description
        desc_tag = soup.find("div", attrs={"data-qa": "vacancy-description"})
        result["description"] = desc_tag.get_text("\n", strip=True)[:5000] if desc_tag else ""

        # Skills
        skills = []
        skill_tags = soup.find_all("span", attrs={"data-qa": lambda v: v and "skill" in (v or "").lower()})
        if skill_tags:
            skills = [s.get_text(strip=True) for s in skill_tags]
        else:
            skills_block = soup.find("div", class_=lambda c: c and "skills" in (c or "").lower())
            if skills_block:
                skills = [s.get_text(strip=True) for s in skills_block.find_all("span")]
        result["skills"] = skills

        # Experience detail
        exp_tag = soup.find("span", attrs={"data-qa": "vacancy-experience"})
        result["experience"] = exp_tag.get_text(strip=True) if exp_tag else ""

        # Employment type
        emp_tag = soup.find("p", attrs={"data-qa": "vacancy-view-employment-mode"})
        result["employment_type"] = emp_tag.get_text(strip=True) if emp_tag else ""

        return result

    def save_vacancies(self, vacancies: list, exclude_keywords: list = None) -> list:
        """Save to DB. Skip detail fetching (blocked by DDoS-Guard)."""
        exclude = exclude_keywords or []
        new = []
        skipped_excluded = 0
        for i, vac in enumerate(vacancies):
            existing = self.db.execute(
                "SELECT id FROM vacancies WHERE id = ?", (vac.id,)
            )
            if existing:
                continue

            combined = f"{vac.title} {vac.company} {vac.location}".lower()
            if _contains_excluded(combined, exclude):
                skipped_excluded += 1
                continue

            self.db.execute_insert(
                """INSERT OR IGNORE INTO vacancies
                   (id, title, company, url, salary_from, salary_to,
                    salary_currency, description, skills, experience, employment_type, location)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    vac.id, vac.title, vac.company, vac.url,
                    vac.salary_from, vac.salary_to, vac.salary_currency or "UZS",
                    vac.description or "",
                    ", ".join(vac.skills or []),
                    vac.experience or "",
                    vac.employment_type or "",
                    vac.location,
                ),
            )
            new.append(vac)
            time.sleep(REQUEST_DELAY / 2)

        if skipped_excluded:
            logger.info(f"Skipped {skipped_excluded} vacancies matching exclude keywords (found in description).")
        logger.info(f"New vacancies saved: {len(new)}")
        return new

    def list_recent(self, limit: int = 20) -> list:
        return self.db.execute(
            "SELECT * FROM vacancies ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )


def main():
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/hh-jobs.log"),
            logging.StreamHandler(),
        ],
    )

    parser = argparse.ArgumentParser(description="HH.uz Parser")
    parser.add_argument("--search", type=str, help="Search keywords")
    parser.add_argument("--min-salary", type=int, default=0, help="Min salary")
    parser.add_argument("--list", action="store_true", help="Recent vacancies")
    args = parser.parse_args()

    db = Database("data/hh.db")
    hp = HHParser(db)

    if args.list:
        rows = hp.list_recent()
        for r in rows:
            print(f"#{r['id']} {r['title']} — {r['company']} | "
                  f"{r.get('salary_from', '')}-{r.get('salary_to', '')}")
        return

    keywords = args.search or "IT Infrastructure Engineer"
    vacancies = hp.search(keywords, min_salary=args.min_salary)
    saved = hp.save_vacancies(vacancies)
    print(f"\nDone: {len(vacancies)} found, {len(saved)} new")


if __name__ == "__main__":
    main()
