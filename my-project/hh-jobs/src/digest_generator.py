import sqlite3
import os
import sys
from pathlib import Path
from matcher import VacancyMatcher
from shared.models import Vacancy

_BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DB_PATH", str(_BASE_DIR / "data" / "hh.db"))

def get_personal_digest(user_id: int, limit: int = 5) -> str:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            profile_row = conn.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
            
            if not profile_row or not profile_row["skills"]:
                return "⚠️ Ваш профиль не настроен. Используйте команду /set_profile <навыки через запятую>"
            
            skills_list = [s.strip() for s in profile_row["skills"].split(",")]
            loc = profile_row.get("location") or "Tashkent"
            is_remote = profile_row.get("is_remote") or 0
            
            profile_dict = {
                "skills": skills_list,
                "min_salary": profile_row["min_salary"] or 0,
                "experience_years": profile_row["experience_years"] or 0,
                "locations": [loc],
                "signal_keywords": []
            }
            
            matcher = VacancyMatcher(profile_dict)
            
            # Если юзер указал remote, ищем и удалёнку в базе, иначе обычные
            remote_filter = "AND (description LIKE '%удален%' OR description LIKE '%remote%')" if is_remote else ""
            
            query = f"SELECT * FROM vacancies WHERE is_archived = 0 AND datetime(created_at) >= datetime('now', '-14 days') {remote_filter}"
            vacancies_data = conn.execute(query).fetchall()
            
            if not vacancies_data:
                return "Нет свежих вакансий для анализа."
                
            scored_vacancies = []
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
                    skills=v.get("skills", "").split(", ") if v.get("skills") else []
                )
                result = matcher.calculate_match(vac)
                scored_vacancies.append(result)
                
            # Sort by score descending
            scored_vacancies.sort(key=lambda x: x.score, reverse=True)
            top_matches = [r for r in scored_vacancies if r.score >= 0.20][:limit]
            
            if not top_matches:
                return f"По вашим навыкам ({', '.join(skills_list)}) подходящих вакансий не найдено. Попробуйте изменить список навыков."
                
            text = f"<b>🎯 Ваш персональный дайджест</b>\nНавыки: {', '.join(skills_list)}\n\n"
            
            import html
            for i, r in enumerate(top_matches, 1):
                title = html.escape(r.vacancy.title or "")
                company = html.escape(r.vacancy.company or "")
                score = int(r.score * 100)
                url = r.vacancy.url
                
                salary_str = "По договорённости"
                if r.vacancy.salary_from or r.vacancy.salary_to:
                    s_from = f"{r.vacancy.salary_from:,}" if r.vacancy.salary_from else ""
                    s_to = f"{r.vacancy.salary_to:,}" if r.vacancy.salary_to else ""
                    curr = r.vacancy.salary_currency or "UZS"
                    if s_from and s_to:
                        salary_str = f"{s_from} – {s_to} {curr}"
                    elif s_from:
                        salary_str = f"от {s_from} {curr}"
                    elif s_to:
                        salary_str = f"до {s_to} {curr}"
                        
                text += f"{i}. <b>{title}</b>\n"
                text += f"🏢 Компания: {company}\n"
                text += f"💰 ЗП: {salary_str}\n"
                text += f"⚡️ Match: <b>{score}%</b>\n"
                text += f"🔗 <a href='{url}'>Смотреть</a>\n\n"
                
            return text
            
    except Exception as e:
        return f"⚠️ Ошибка генерации дайджеста: {e}"
