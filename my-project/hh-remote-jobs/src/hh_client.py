"""
HH.ru / HH.kz RSS Client — поиск удалённых вакансий.

Официальный REST API (api.hh.ru) блокируется DDoS-Guard с этой сети (проверено
30.07.2026: 403 на любой User-Agent, отдаёт `server: ddos-guard`). Обычный HTML
поиск (hh.ru/search/vacancy) тоже возвращает по сути заглушку для не-браузерных
клиентов. Единственный рабочий канал — RSS-фид поиска (hh.ru/search/vacancy/rss),
который отдаёт реальные вакансии, но с довольно строгим анти-бот лимитом частоты
запросов: несколько запросов подряд без паузы → пустой ответ (`<doc/>` вместо
`<rss>` с айтемами), но после ~15-20с пауза снимается. REQUEST_DELAY подобран
с запасом под это поведение.
"""

import html
import logging
import re
import time
import xml.etree.ElementTree as ET
from typing import Optional

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

HH_HOSTS = {
    "hh_ru": "hh.ru",
    "hh_kz": "hh.kz",
}

AREAS = {
    "ru": 113,
    "kz": 40,
    "uz": 97,
}

# hh.ru's own listing already indexes vacancies from CIS countries via the
# `area` filter — no need to hit the separate hh.kz host for coverage.
AREA_SOURCE_MAP = {113: "hh_ru", 40: "hh_kz", 97: "hh_uz"}

REQUEST_DELAY = 15  # seconds between RSS requests — see module docstring
MAX_RETRIES_ON_EMPTY = 2  # retry once more with a longer backoff if we get <doc/>
EMPTY_RETRY_DELAY = 25

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _make_vacancy_id(source: str, native_id: str) -> str:
    return f"{source}:{native_id}"


def _parse_description(desc_html: str) -> dict:
    """Extract company/region/salary from the RSS item's CDATA description.

    Real format seen from hh.ru RSS (2026-07-30):
    "<p>Вакансия компании: X</p> <p>Создана: date</p> <p>Регион: Y</p>
     <p>Предполагаемый уровень месячного дохода: от A до B $</p>"
    Fields are optional/inconsistently present — parse defensively.
    """
    text = html.unescape(desc_html or "")
    result = {"company": "", "region": "", "salary_from": None, "salary_to": None, "salary_currency": None}

    m = re.search(r"Вакансия компании:\s*([^<]+)", text)
    if m:
        result["company"] = m.group(1).strip()

    m = re.search(r"Регион:\s*([^<]+)", text)
    if m:
        result["region"] = m.group(1).strip()

    m = re.search(r"уровень месячного дохода:\s*([^<]+)", text)
    if m:
        salary_text = m.group(1).strip()
        currency = None
        if "$" in salary_text:
            currency = "USD"
        elif "€" in salary_text:
            currency = "EUR"
        elif "сум" in salary_text.lower():
            currency = "UZS"
        elif "руб" in salary_text.lower() or "₽" in salary_text:
            currency = "RUB"
        elif "₸" in salary_text or "тенге" in salary_text.lower():
            currency = "KZT"
        result["salary_currency"] = currency

        nums = re.findall(r"[\d\s]+\d", salary_text)
        nums = [int(n.replace(" ", "").replace("\xa0", "")) for n in nums]
        if "от" in salary_text and "до" in salary_text and len(nums) >= 2:
            result["salary_from"], result["salary_to"] = nums[0], nums[1]
        elif "от" in salary_text and nums:
            result["salary_from"] = nums[0]
        elif "до" in salary_text and nums:
            result["salary_to"] = nums[0]
        elif nums:
            result["salary_from"] = nums[0]

    return result


class HHClient:
    """RSS-based client for HH.ru / HH.kz vacancy search (read-only)."""

    def __init__(self):
        load_dotenv()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/xml, text/xml",
        })
        self._last_request_time = 0.0

    def _rate_limit_wait(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)

    def _fetch_rss(self, host: str, params: dict) -> list:
        """Fetch one RSS page, retrying with backoff if we hit the rate limit
        (signature: valid XML but zero <item> — the anti-bot guard returns an
        empty <doc/> body instead of an HTTP error, so a 200 with no items is
        ambiguous between "no results" and "throttled"; we retry once/twice
        to tell the difference before accepting the empty result)."""
        url = f"https://{host}/search/vacancy/rss"
        attempt = 0
        while True:
            self._rate_limit_wait()
            self._last_request_time = time.time()
            try:
                resp = self.session.get(url, params=params, timeout=20)
            except requests.RequestException as e:
                logger.error(f"RSS request failed: {host} {params.get('text')} — {e}")
                return []

            if resp.status_code != 200:
                logger.error(f"RSS HTTP {resp.status_code} for {host}: {params.get('text')}")
                return []

            try:
                root = ET.fromstring(resp.text)
            except ET.ParseError as e:
                logger.error(f"RSS parse error for {host}: {e}")
                return []

            items = root.findall(".//item")
            if items:
                return items

            if attempt >= MAX_RETRIES_ON_EMPTY:
                return []
            attempt += 1
            logger.info(f"  Empty RSS response (possibly rate-limited), retry {attempt}/{MAX_RETRIES_ON_EMPTY} after {EMPTY_RETRY_DELAY}s...")
            time.sleep(EMPTY_RETRY_DELAY)

    def search(
        self,
        keywords: str,
        schedule: str = "remote",
        period: int = 7,
        areas: list = None,
        **_ignored,
    ) -> list:
        """Search the hh.ru RSS feed for each keyword × area. `source` per
        result is derived from the area (AREA_SOURCE_MAP), matching the old
        REST-API design where hh.ru's own listing covers RU/KZ/UZ via the
        `area` filter — no separate hh.kz host needed.

        Returns list of dicts: {source, native_id, title, url, pub_date,
        description_raw}."""
        areas = areas or [AREAS["ru"]]
        keyword_groups = [k.strip() for k in keywords.split(",") if k.strip()]
        host = HH_HOSTS["hh_ru"]

        all_items = []
        seen_ids = set()

        for kw in keyword_groups:
            for area in areas:
                source = AREA_SOURCE_MAP.get(area, "hh_ru")
                params = {"text": kw, "area": area}
                if schedule:
                    params["schedule"] = schedule
                if period:
                    params["period"] = period

                logger.info(f"  RSS search: '{kw}' area={area} ({source})")
                items = self._fetch_rss(host, params)

                for item in items:
                    link_el = item.find("link")
                    if link_el is None or not link_el.text:
                        continue
                    m = re.search(r"/vacancy/(\d+)", link_el.text)
                    if not m:
                        continue
                    native_id = m.group(1)
                    uid = _make_vacancy_id(source, native_id)
                    if uid in seen_ids:
                        continue
                    seen_ids.add(uid)

                    title_el = item.find("title")
                    pubdate_el = item.find("pubDate")
                    desc_el = item.find("description")

                    all_items.append({
                        "source": source,
                        "native_id": native_id,
                        "title": (title_el.text or "").strip() if title_el is not None else "",
                        "url": link_el.text.strip().replace("hh.ru", "tashkent.hh.uz"),
                        "pub_date": (pubdate_el.text or "").strip() if pubdate_el is not None else "",
                        "description_raw": (desc_el.text or "") if desc_el is not None else "",
                    })

        logger.info(f"Total raw vacancies: {len(all_items)}")
        return all_items

    def enrich_vacancy(self, item: dict) -> dict:
        """Convert a raw RSS item into our internal vacancy dict (DB schema shape)."""
        parsed = _parse_description(item["description_raw"])
        raw_text = html.unescape(re.sub(r"<[^>]+>", " ", item["description_raw"] or ""))
        raw_text = re.sub(r"\s+", " ", raw_text).strip()

        return {
            "id": _make_vacancy_id(item["source"], item["native_id"]),
            "native_id": item["native_id"],
            "source": item["source"],
            "title": item["title"],
            "company": parsed["company"],
            "url": item["url"],
            "salary_raw": raw_text,
            "salary_from": parsed["salary_from"],
            "salary_to": parsed["salary_to"],
            "salary_currency": parsed["salary_currency"],
            "salary_gross": None,
            "experience": "",
            "employment_type": "",
            "area": parsed["region"],
            "professional_roles": "",
            "raw_text": f"{item['title']} {raw_text}",
            "created_at": item["pub_date"],
            "published_at": item["pub_date"],
        }

    def search_and_enrich(
        self,
        keywords: str,
        schedule: str = "remote",
        period: int = 7,
        areas: list = None,
        **kwargs,
    ) -> list:
        """Search RSS and enrich results into internal format."""
        raw = self.search(
            keywords=keywords,
            schedule=schedule,
            period=period,
            areas=areas,
        )
        return [self.enrich_vacancy(item) for item in raw]
