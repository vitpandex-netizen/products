"""
Vacancy Matcher — оценивает совпадение удалённой вакансии с профилем.

Алгоритм:
1. Hard reject: EXCLUDE_KEYWORDS, HARD_STOP, REMOTE_ENGLISH_EXCLUDE_KEYWORDS
2. Skills score (weight 0.5): сколько навыков из профиля совпало
3. Salary score (weight 0.3): зарплата >= MIN_SALARY_USD (с зарплатной лестницей)
4. Experience score (weight 0.2): требуемый опыт <= опыта кандидата
5. Если зарплата не указана — вес перераспределяется на skills и experience
"""

import re
import os
import logging
from typing import Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

MATCH_THRESHOLD = 0.70
WEIGHTS = {
    "skills": 0.5,
    "salary": 0.3,
    "experience": 0.2,
}

# Skills score = matched-count / TARGET_SKILL_MATCHES (capped at 1.0), NOT
# matched-count / total-profile-skills. With a large skill inventory (200+
# terms covering every tool ever used), no single vacancy will ever mention
# more than a handful — dividing by the full list size mathematically tanks
# every score regardless of fit quality. TARGET is "how many overlapping
# terms count as a strong match"; tune if scores skew too generous/strict.
TARGET_SKILL_MATCHES = 10

# Approximate rates to USD for comparing salaries stated in other currencies
# against MIN_SALARY_USD.
USD_PER_UNIT = {
    "USD": 1,
    "RUB": 0.0116,   # ~1 USD = 86 RUB (July 2026)
    "KZT": 0.0021,   # ~1 USD = 476 KZT
    "EUR": 1.08,     # ~1.08 USD per EUR
}

SIGNAL_BONUS_PER_HIT = 0.05
SIGNAL_BONUS_MAX = 0.15

_CYRILLIC_RE = re.compile(r"[а-яё]", re.IGNORECASE)


def _skill_terms(skill: str) -> list:
    """Return the term(s) to match for a given skill.

    Russian nouns/adjectives decline by case ("виртуализация" →
    "виртуализации", "сетевые" → "сетевого"), so matching only the
    dictionary (nominative) form misses every inflected occurrence in
    real vacancy text. For single-word Russian skills we also try a
    truncated stem (drop the last 2 chars) which covers the common
    case endings without needing a hand-maintained synonym table.
    Multi-word phrases and non-Cyrillic (English) terms are left as-is.
    """
    terms = [skill]
    if " " not in skill and "-" not in skill and len(skill) > 6 and _CYRILLIC_RE.search(skill):
        terms.append(skill[:-2])
    return terms


def _term_in_text(term: str, text: str) -> bool:
    """True if `term` occurs in `text`.

    Short terms (<=4 chars — mostly acronyms like AI, L1, BI, AD, SAP) use a
    word-boundary regex instead of a raw substring check. A plain substring
    check on "AI" would false-positive inside "detAIl", "trAIning", etc.
    """
    if len(term) <= 4:
        return bool(re.search(rf"\b{re.escape(term)}\b", text))
    return term in text


def _any_term_in_text(terms: list, text: str) -> bool:
    """True if any of `terms` (checked with stem support) occurs in text."""
    if not terms:
        return False
    for term in terms:
        for stem in _skill_terms(term):
            if _term_in_text(stem, text):
                return True
    return False


def _parse_experience(exp_text: str) -> Optional[int]:
    """Parse HH experience text to years. Returns None if unknown."""
    if not exp_text:
        return None
    text = exp_text.lower()
    if "более" in text or "more than" in text:
        return 6  # moreThan6
    if "1–3" in text or "1-3" in text:
        return 2
    if "3–6" in text or "3-6" in text:
        return 4
    if "нет опыта" in text or "без опыта" in text or "no experience" in text:
        return 0
    return None


class VacancyMatcher:
    """Match remote vacancies against a user profile."""

    def __init__(self, profile: dict):
        self.profile = profile
        self.my_skills = [s.strip().lower() for s in profile.get("my_skills", []) if s.strip()]
        self.exclude_keywords = [s.strip().lower() for s in profile.get("exclude_keywords", []) if s.strip()]
        self.hard_stop = [s.strip().lower() for s in profile.get("hard_stop", []) if s.strip()]
        self.signal_keywords = [s.strip().lower() for s in profile.get("signal_keywords", []) if s.strip()]
        self.english_exclude_keywords = [s.strip().lower() for s in profile.get("english_exclude_keywords", []) if s.strip()]

        self.min_salary_usd = profile.get("min_salary_usd", 0)
        self.salary_soft_floor_usd = profile.get("salary_soft_floor_usd", 0)
        self.salary_target_usd = profile.get("salary_target_usd", 0)
        self.salary_accept_unspecified = profile.get("salary_accept_unspecified", True)
        self.english_required = profile.get("english_required", False)
        self.experience_years = profile.get("experience_years", 19)

    def _excluded(self, vac: dict) -> Optional[str]:
        """Check if a vacancy should be hard-rejected.

        Returns: None if OK, or a string reason if excluded.
        """
        title = (vac.get("title") or "").lower()
        company = (vac.get("company") or "").lower()
        area = (vac.get("area") or "").lower()
        raw_text = (vac.get("raw_text") or "").lower()
        combined = f"{title} {company} {area} {raw_text}"

        # HARD_STOP — unconditional reject
        for kw in self.hard_stop:
            if _term_in_text(kw, combined):
                return f"HARD_STOP: '{kw}'"

        # EXCLUDE_KEYWORDS
        for kw in self.exclude_keywords:
            if _term_in_text(kw, combined):
                return f"EXCLUDE: '{kw}'"

        # English requirement — if REMOTE_ENGLISH_REQUIRED=false and vacancy
        # mentions English, reject to avoid wasting time on roles that need
        # fluent English but aren't a fit
        if not self.english_required:
            for kw in self.english_exclude_keywords:
                if _term_in_text(kw, combined):
                    return f"ENGLISH EXCLUDE: '{kw}'"

        return None

    def calculate_match(self, vac: dict) -> Optional[dict]:
        """Score a single enriched vacancy dict.

        Returns:
            enriched dict with match fields added, or None if hard-rejected.
        """
        # 0. Hard reject check
        reject_reason = self._excluded(vac)
        if reject_reason:
            logger.info(f"  ❌ {reject_reason}: {vac.get('title', '?')} — {vac.get('company', '?')}")
            return None

        title = (vac.get("title") or "").lower()
        raw_text = (vac.get("raw_text") or "").lower()
        vac_text = f"{title} {raw_text}"

        matched_skills = []
        reasons = []

        # 1. Skills match (weight 0.5)
        for skill in self.my_skills:
            if _any_term_in_text([skill], vac_text):
                matched_skills.append(skill)

        skills_score = min(len(matched_skills) / TARGET_SKILL_MATCHES, 1.0)
        reasons.append(
            f"Skills: {len(matched_skills)}/{len(self.my_skills)} profile terms matched "
            f"(target {TARGET_SKILL_MATCHES}+ for full score) = {skills_score:.2f}"
        )

        # 1b. Signal keywords bonus
        signal_hits = [s for s in self.signal_keywords if _any_term_in_text([s], vac_text)]
        if signal_hits:
            bonus = min(len(signal_hits) * SIGNAL_BONUS_PER_HIT, SIGNAL_BONUS_MAX)
            skills_score = min(skills_score + bonus, 1.0)
            reasons.append(f"Signal keywords matched: {signal_hits} (+{bonus:.2f} to skills)")

        # 2. Salary match (weight 0.3)
        # Convert to USD before comparing
        salary_from = vac.get("salary_from")
        salary_to = vac.get("salary_to")
        salary_currency = (vac.get("salary_currency") or "USD").upper()
        rate = USD_PER_UNIT.get(salary_currency, 1)

        salary_match = False
        salary_specified = bool(salary_from or salary_to)

        if salary_specified:
            avg_salary = None
            if salary_from and salary_to:
                avg_salary = (salary_from + salary_to) / 2
            elif salary_from:
                avg_salary = salary_from
            elif salary_to:
                avg_salary = salary_to

            avg_salary_usd = avg_salary * rate if avg_salary else 0

            # Salary ladder:
            # - Hard floor: avg >= MIN_SALARY_USD → full match
            # - Soft floor: avg >= SALARY_SOFT_FLOOR_USD → partial (0.5)
            # - Below soft floor: no match
            if avg_salary_usd >= self.min_salary_usd:
                salary_match = True
                salary_score = 1.0
            elif avg_salary_usd >= self.salary_soft_floor_usd:
                salary_match = True
                salary_score = 0.5
                reasons.append(f"Salary: {avg_salary_usd:.0f} USD is below min ({self.min_salary_usd}) but >= soft floor ({self.salary_soft_floor_usd}) — partial match")
            else:
                salary_score = 0.0

            reasons.append(
                f"Salary: min={self.min_salary_usd} USD, offer={avg_salary:.0f} {salary_currency} "
                f"(~{avg_salary_usd:.0f} USD) -> {'match' if salary_match else 'no match'}"
            )
        else:
            salary_score = 0.0
            if not self.salary_accept_unspecified:
                reasons.append("Salary: not specified -> no match (SALARY_ACCEPT_UNSPECIFIED=false)")
            else:
                reasons.append("Salary: not specified -> excluded from score, weight redistributed")

        # 3. Experience match (weight 0.2)
        vac_exp = _parse_experience(vac.get("experience"))
        if vac_exp is not None:
            experience_match = vac_exp <= self.experience_years
        else:
            experience_match = True  # unknown experience = don't penalize
        experience_score = 1.0 if experience_match else 0.0
        reasons.append(f"Experience: need={vac_exp or 'any'}, have={self.experience_years} -> {'match' if experience_match else 'no match'}")

        # 4. Total score with weight redistribution
        if salary_specified or not self.salary_accept_unspecified:
            active_weights = WEIGHTS
        else:
            # Salary unspecified and accepted: redistribute weight
            remaining = WEIGHTS["skills"] + WEIGHTS["experience"]
            active_weights = {
                "skills": WEIGHTS["skills"] / remaining,
                "salary": 0.0,
                "experience": WEIGHTS["experience"] / remaining,
            }

        total = (
            skills_score * active_weights["skills"]
            + salary_score * active_weights["salary"]
            + experience_score * active_weights["experience"]
        )
        total = round(min(total, 1.0), 3)

        result = dict(vac)
        result.update({
            "matched_score": total,
            "matched_skills": matched_skills,
            "match_reasons": reasons,
            "salary_match": salary_match if salary_specified else None,
        })
        return result

    def batch_match(self, vacancies: list) -> list:
        """Match multiple vacancies. Skips hard-rejected ones."""
        results = []
        for vac in vacancies:
            result = self.calculate_match(vac)
            if result:
                results.append(result)
                status = "✅" if result["matched_score"] >= MATCH_THRESHOLD else "⏳"
                logger.info(f"{status} [{result['matched_score']:.1%}] {result.get('title', '?')} — {result.get('company', '?')}")
        good_matches = [r for r in results if r["matched_score"] >= MATCH_THRESHOLD]
        logger.info(f"Good matches: {len(good_matches)}/{len(results)} (hard-rejected: {len(vacancies) - len(results)})")
        return results

    @classmethod
    def from_env(cls) -> "VacancyMatcher":
        """Create matcher from .env file."""
        load_dotenv()

        my_skills = [s.strip() for s in os.getenv("MY_SKILLS", "").split(",") if s.strip()]
        exclude_keywords = [s.strip() for s in os.getenv("EXCLUDE_KEYWORDS", "").split(",") if s.strip()]
        hard_stop = [s.strip() for s in os.getenv("HARD_STOP", "").split(",") if s.strip()]
        signal_keywords = [s.strip() for s in os.getenv("SIGNAL_KEYWORDS", "").split(",") if s.strip()]
        english_exclude_keywords = [s.strip() for s in os.getenv("REMOTE_ENGLISH_EXCLUDE_KEYWORDS", "").split(",") if s.strip()]

        profile = {
            "my_skills": my_skills,
            "exclude_keywords": exclude_keywords,
            "hard_stop": hard_stop,
            "signal_keywords": signal_keywords,
            "english_exclude_keywords": english_exclude_keywords,
            "min_salary_usd": int(os.getenv("MIN_SALARY_USD", "3500")),
            "salary_soft_floor_usd": int(os.getenv("SALARY_SOFT_FLOOR_USD", "2800")),
            "salary_target_usd": int(os.getenv("SALARY_TARGET_USD", "5000")),
            "salary_accept_unspecified": os.getenv("SALARY_ACCEPT_UNSPECIFIED", "true").lower() == "true",
            "english_required": os.getenv("REMOTE_ENGLISH_REQUIRED", "false").lower() == "true",
            "experience_years": 19,
        }
        return cls(profile)
