"""
Shared data models for all projects
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class Vacancy:
    """HH Vacancy model"""
    id: int
    title: str
    company: str
    url: str
    salary_from: Optional[int] = None
    salary_to: Optional[int] = None
    salary_currency: Optional[str] = None
    description: str = ""
    experience: str = ""
    employment_type: str = ""
    location: str = ""
    skills: List[str] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.created_at is None:
            self.created_at = datetime.now()

    def avg_salary(self) -> Optional[int]:
        """Calculate average salary"""
        if self.salary_from and self.salary_to:
            return (self.salary_from + self.salary_to) // 2
        return self.salary_from or self.salary_to

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "url": self.url,
            "salary_from": self.salary_from,
            "salary_to": self.salary_to,
            "description": self.description,
            "experience": self.experience,
            "employment_type": self.employment_type,
            "skills": ",".join(self.skills) if self.skills else "",
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class UserProfile:
    """User profile for matching"""
    name: str
    email: str
    phone: str
    skills: List[str]
    experience_years: int
    preferred_salary: Optional[int] = None
    preferred_companies: List[str] = None
    preferred_roles: List[str] = None
    languages: List[str] = None

    def __post_init__(self):
        if self.preferred_companies is None:
            self.preferred_companies = []
        if self.preferred_roles is None:
            self.preferred_roles = []
        if self.languages is None:
            self.languages = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "skills": self.skills,
            "experience_years": self.experience_years,
            "preferred_salary": self.preferred_salary,
            "preferred_companies": self.preferred_companies,
            "preferred_roles": self.preferred_roles,
            "languages": self.languages,
        }


@dataclass
class MatchResult:
    """Result of vacancy matching"""
    vacancy: Vacancy
    score: float  # 0.0 - 1.0
    matched_skills: List[str]
    missing_skills: List[str]
    salary_match: bool
    reasons: List[str]

    def is_good_match(self, threshold: float = 0.7) -> bool:
        return self.score >= threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vacancy_id": self.vacancy.id,
            "vacancy_title": self.vacancy.title,
            "score": self.score,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "salary_match": self.salary_match,
            "reasons": self.reasons,
        }


# Пример использования:
# vacancy = Vacancy(
#     id=123,
#     title="Senior Python Developer",
#     company="Acme Corp",
#     url="https://hh.ru/vacancy/123",
#     salary_from=150000,
#     salary_to=250000,
#     skills=["Python", "Django", "PostgreSQL"]
# )
