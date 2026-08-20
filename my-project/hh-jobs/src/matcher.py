"""
Vacancy Matcher — оценивает совпадение вакансии с профилем.

Алгоритм:
- Skills (weight 0.5): сколько навыков из профиля совпало
- Salary (weight 0.3): зарплата >= минимальной
- Experience (weight 0.2): требуемый опыт <= опыта кандидата
- Итог: skills * 0.5 + salary_match * 0.3 + experience_match * 0.2
"""

import re
import sys
import logging
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.models import Vacancy, MatchResult
from shared.db import Database

logger = logging.getLogger(__name__)

MATCH_THRESHOLD = 0.70
WEIGHTS = {
    "skills": 0.5,
    "salary": 0.3,
    "experience": 0.2,
}

# skills_score is matched-count / TARGET_SKILL_MATCHES (capped at 1.0), NOT
# matched-count / total-profile-skills. With a large personal skill
# inventory (200+ terms covering every tool ever used), no single vacancy
# will ever mention more than a handful — dividing by the full list size
# mathematically tanks every score regardless of fit quality. TARGET is
# "how many overlapping terms count as a strong match"; tune if scores
# skew too generous/strict after reviewing a batch of real results.
TARGET_SKILL_MATCHES = 10

# Approximate rates to UZS, for comparing salaries stated in other currencies
# against MIN_SALARY (which is set in UZS). Update periodically — this is not
# a live feed, just enough precision to avoid comparing raw numbers across
# currencies (e.g. treating a "$5000" offer as "5000 UZS").
UZS_PER_UNIT = {
    "UZS": 1,
    "USD": 12900,
    "RUB": 140,
}

# How much a SIGNAL_KEYWORDS hit nudges the skills score, and the cap. Small
# and additive — a tie-breaker for borderline vacancies, not a scoring
# category of its own (there's no separate weight for it in WEIGHTS).
SIGNAL_BONUS_PER_HIT = 0.05
SIGNAL_BONUS_MAX = 0.15

_CYRILLIC_RE = re.compile(r"[а-яё]", re.IGNORECASE)

# Руководящие/исполнительные должности. Если заголовок вакансии содержит
# один из этих титулов — это топ-приоритет независимо от score (RSS даёт
# только заголовки, без описаний, поэтому рядовые скиллы почти не
# совпадают, и без этого правила реально подходящие CIO/CTO/ИТ-директор
# позиции тонули бы под техническими).
EXECUTIVE_TITLES = [
    "cio", "cto", "cdto", "cdo", "coo",
    "chief information", "chief technology",
    "it director", "director of it", "director of tech",
    "director of engineering", "vp of engineering", "vp engineering",
    "head of it", "head of infrastructure", "head of digital",
    "head of operations", "it operations manager",
    "директор ит", "ит-директор", "ит директор", "директор по ит",
    "директор по информационн", "директор по цифров",
    "руководитель ит", "руководитель it", "руководитель it-",
    "руководитель информационн", "руководитель службы эксплуатации",
    "начальник ит", "начальник отдела ит", "начальник it",
    "технический директор", "операционный директор",
    "цифровой трансформации", "digital transformation",
    "it manager", "it-менеджер", "ит менеджер",
]
EXECUTIVE_FLOOR = 0.55  # минимальный score для руководящей позиции

# Второй уровень — приоритетные технические IT-позиции (сисадмин, ведущий
# инженер, DevOps, DBA и т.п.). Пользователь явно просил их ловить, но по
# RSS-заголовку они набирают ~0.29 (ниже порога 0.30) и пропадают.
SENIOR_IT_TITLES = [
    "системный администратор", "системный инженер", "системный архитектор",
    "сетевой инженер", "network engineer", "сетевой администратор",
    "devops", "sre", "site reliability",
    "инженер инфраструктур", "infrastructure engineer",
    "администратор баз данных", "database administrator", "dba",
    "администратор linux", "linux administrator", "администратор серверов",
    "администратор windows", "администратор сети", "администратор 1с",
    "ведущий инженер", "senior engineer", "lead engineer",
    "архитектор", "architect",
    "инженер по информационн", "специалист по информационн",
    "информационная безопасность", "information security",
    "head of corporate", "head of technology",
]
SENIOR_IT_FLOOR = 0.35  # минимальный score для приоритетной IT-позиции


def _skill_terms(skill: str) -> list:
    """Return the term(s) to match for a given skill.

    Russian nouns/adjectives decline by case ("виртуализация" ->
    "виртуализации", "сетевые" -> "сетевого"), so matching only the
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


def _skill_matches(skill: str, vac_text: str) -> bool:
    """True if `skill` (or an inflected form) occurs in vac_text.

    Short terms (<=4 chars — mostly acronyms like AI, L1, BI, AD, SAP) use a
    word-boundary regex instead of a raw substring check. A plain substring
    check on "AI" would false-positive inside "detAIl", "trAIning", etc.
    """
    for term in _skill_terms(skill):
        if len(term) <= 4:
            if re.search(rf"\b{re.escape(term)}\b", vac_text):
                return True
        elif term in vac_text:
            return True
    return False


class VacancyMatcher:
    """Match vacancies against a user profile."""

    def __init__(self, profile: dict):
        self.profile = profile
        self.skills = [s.strip().lower() for s in profile.get("skills", []) if s.strip()]
        self.min_salary = profile.get("min_salary", 0)
        self.experience_years = profile.get("experience_years", 0)
        self.locations = [l.strip().lower() for l in profile.get("locations", []) if l.strip()]
        self.signal_keywords = [s.strip().lower() for s in profile.get("signal_keywords", []) if s.strip()]

    def calculate_match(self, vacancy: Vacancy) -> MatchResult:
        """Calculate match score for a single vacancy."""
        matched_skills = []
        missing_skills = []
        reasons = []

        # 1. Skills match (weight 0.5) — matches Russian case-inflected forms
        # too, since HH.uz Tashkent listings are mostly in Russian (see
        # _skill_terms docstring).
        vac_text = f"{vacancy.title} {vacancy.description}".lower()
        for skill in self.skills:
            if _skill_matches(skill, vac_text):
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)

        skills_score = min(len(matched_skills) / TARGET_SKILL_MATCHES, 1.0)
        reasons.append(
            f"Skills: {len(matched_skills)}/{len(self.skills)} profile terms matched "
            f"(target {TARGET_SKILL_MATCHES}+ for full score) = {skills_score:.2f}"
        )

        # 1b. Signal keywords — small bonus for context that historically
        # correlates with a good-fit role (e.g. "построение с нуля",
        # "несколько филиалов"), even if it's not a discrete "skill".
        signal_hits = [s for s in self.signal_keywords if _skill_matches(s, vac_text)]
        if signal_hits:
            bonus = min(len(signal_hits) * SIGNAL_BONUS_PER_HIT, SIGNAL_BONUS_MAX)
            skills_score = min(skills_score + bonus, 1.0)
            reasons.append(f"Signal keywords matched: {signal_hits} (+{bonus:.2f} to skills)")

        # 2. Salary match (weight 0.3) — only scored if vacancy actually states a salary.
        # ~80% of HH.uz listings omit salary; those must not be penalized for it.
        # Offers are converted to UZS (via UZS_PER_UNIT) before comparing, since
        # some listings state salary in USD/RUB while MIN_SALARY is set in UZS.
        salary_match = False
        salary_highlight = False  # salary >$4000 highlighted separately
        salary_specified = bool(vacancy.salary_from or vacancy.salary_to)
        rate = UZS_PER_UNIT.get((vacancy.salary_currency or "UZS").upper(), 1)

        avg_salary = vacancy.avg_salary()
        avg_salary_uzs = avg_salary * rate if avg_salary else None
        if avg_salary_uzs:
            salary_match = avg_salary_uzs >= self.min_salary
            salary_highlight = avg_salary_uzs >= self.min_salary * 1.5  # >$6000
        elif vacancy.salary_to:
            salary_match = vacancy.salary_to * rate >= self.min_salary
            salary_highlight = vacancy.salary_to * rate >= self.min_salary * 1.5
        elif vacancy.salary_from:
            salary_match = vacancy.salary_from * rate >= self.min_salary * 0.8  # partial match
            salary_highlight = vacancy.salary_from * rate >= self.min_salary * 1.5

        salary_score = 1.0 if salary_match else 0.0
        if salary_specified:
            reasons.append(
                f"Salary: min={self.min_salary} UZS, offer={avg_salary} {vacancy.salary_currency or 'UZS'} "
                f"(~{avg_salary_uzs} UZS) -> {'match' if salary_match else 'no match'}"
            )
        else:
            reasons.append("Salary: not specified -> excluded from score, weight redistributed")

        # 3. Experience match (weight 0.2)
        experience_match = True
        vac_exp = self._parse_experience(vacancy.experience)
        if vac_exp is not None:
            experience_match = vac_exp <= self.experience_years
        experience_score = 1.0 if experience_match else 0.0
        reasons.append(f"Experience: need={vac_exp or 'any'}, have={self.experience_years} -> {'match' if experience_match else 'no match'}")

        # Total score — if salary is unspecified, drop its weight and renormalize
        # the remaining weights (skills, experience) so they sum back to 1.0.
        if salary_specified:
            active_weights = WEIGHTS
        else:
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

        # Руководящая позиция (CIO/CTO/ИТ-директор/Head of IT и т.п.) —
        # принудительный минимум score. RSS-фид даёт только заголовок без
        # описания, поэтому технические скиллы почти не совпадают, и без
        # этого флора реально подходящие топ-позиции проваливались бы ниже
        # порога и не попадали бы в уведомления.
        title_lower = vacancy.title.lower()
        if any(t in title_lower for t in EXECUTIVE_TITLES):
            if total < EXECUTIVE_FLOOR:
                reasons.append(
                    f"Executive title detected -> score raised to floor {EXECUTIVE_FLOOR}"
                )
                total = EXECUTIVE_FLOOR
        elif any(t in title_lower for t in SENIOR_IT_TITLES):
            if total < SENIOR_IT_FLOOR:
                reasons.append(
                    f"Senior IT title detected -> score raised to floor {SENIOR_IT_FLOOR}"
                )
                total = SENIOR_IT_FLOOR

        return MatchResult(
            vacancy=vacancy,
            score=total,
            matched_skills=matched_skills,
            missing_skills=[s for s in missing_skills if s not in matched_skills],
            salary_match=salary_match,
            reasons=reasons,
        )

    def _parse_experience(self, exp_text: str) -> Optional[int]:
        """Parse HH experience text to years. Returns None if unknown."""
        if not exp_text:
            return None

        text = exp_text.lower()
        if "более" in text or "more than" in text:
            return 6  # moreThan6
        if "1–3" in text or "1-3" in text or "1-3" in text:
            return 2
        if "3–6" in text or "3-6" in text:
            return 4
        if "нет опыта" in text or "без опыта" in text or "no experience" in text:
            return 0
        return None  # unknown

    def batch_match(self, vacancies: list) -> list:
        """Match multiple vacancies and save results to DB."""
        results = []
        for vac in vacancies:
            result = self.calculate_match(vac)
            results.append(result)

            # Save score to DB
            self._save_match_score(vac.id, result.score)

            status = "✅" if result.is_good_match(MATCH_THRESHOLD) else "⏳"
            logger.info(f"{status} [{result.score:.1%}] {vac.title} — {vac.company}")

        good_matches = [r for r in results if r.is_good_match(MATCH_THRESHOLD)]
        logger.info(f"Good matches: {len(good_matches)}/{len(results)}")
        return results

    def _save_match_score(self, vacancy_id: int, score: float):
        """Update vacancy with match score."""
        db = Database("data/hh.db")
        db.execute_update(
            "UPDATE vacancies SET matched_score = ? WHERE id = ?",
            (score, vacancy_id),
        )

    @classmethod
    def from_env(cls) -> "VacancyMatcher":
        """Create matcher from .env file."""
        from dotenv import load_dotenv
        load_dotenv()
        import os

        skills_str = os.getenv("MY_SKILLS", "")
        skills = [s.strip() for s in skills_str.split(",") if s.strip()]
        min_salary = int(os.getenv("MIN_SALARY", "0"))
        signal_str = os.getenv("SIGNAL_KEYWORDS", "")
        signal_keywords = [s.strip() for s in signal_str.split(",") if s.strip()]

        profile = {
            "skills": skills,
            "min_salary": min_salary,
            "experience_years": 19,
            "signal_keywords": signal_keywords,
            "locations": [os.getenv("PREFERRED_LOCATION", "Tashkent")],
        }
        return cls(profile)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    db = Database("data/hh.db")
    vacancies_data = db.execute(
        "SELECT * FROM vacancies WHERE matched_score = 0 ORDER BY created_at DESC"
    )

    if not vacancies_data:
        logger.info("No unprocessed vacancies.")
        return

    matcher = VacancyMatcher.from_env()
    results = []
    for v in vacancies_data:
        vac = Vacancy(
            id=v["id"],
            title=v["title"],
            company=v["company"],
            url=v["url"],
            salary_from=v.get("salary_from"),
            salary_to=v.get("salary_to"),
            salary_currency=v.get("salary_currency"),
            description=v.get("description", ""),
            experience=v.get("experience", ""),
            employment_type=v.get("employment_type", ""),
            skills=v.get("skills", "").split(", ") if v.get("skills") else [],
        )
        result = matcher.calculate_match(vac)
        results.append(result)
        matcher._save_match_score(vac.id, result.score)

        if result.is_good_match(MATCH_THRESHOLD):
            print(f"  ✅ [{result.score:.1%}] {vac.title} — {vac.company}")
        else:
            print(f"  ⏳ [{result.score:.1%}] {vac.title} — {vac.company}")


if __name__ == "__main__":
    main()
