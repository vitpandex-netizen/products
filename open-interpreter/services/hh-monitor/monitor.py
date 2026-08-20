"""HH.ru vacancy monitor - checks new vacancies and auto-generates cover letters."""
import sys
import json
import time
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.db import get_conn
from shared.utils import notify, format_salary, get_config, send_hermes_message

import requests

def search_vacancies(query="Python developer", area=113, per_page=20):
    """Search HH vacancies. area=113 is Russia, 1 is Moscow."""
    url = "https://api.hh.ru/vacancies"
    headers = {"User-Agent": "InterpBot/1.0 (analytics-bot)"}
    params = {
        "text": query,
        "area": area,
        "per_page": per_page,
        "order_by": "publication_time",
        "search_field": "name,description"
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", [])
    except Exception as e:
        print(f"[HH] Error searching: {e}")
        return []

def process_vacancies(vacancies, service="hh-monitor"):
    """Process and store new vacancies."""
    conn = get_conn()
    new_count = 0
    match_count = 0
    
    for v in vacancies:
        v_id = v.get("id")
        if not v_id:
            continue
            
        title = v.get("name", "No title")
        company = v.get("employer", {}).get("name", "Unknown")
        url = v.get("alternate_url", "")
        
        salary_info = v.get("salary") or {}
        salary_min = salary_info.get("from")
        salary_max = salary_info.get("to")
        currency = salary_info.get("currency", "RUB")
        
        snippet = v.get("snippet") or {}
        skills_text = f"{snippet.get('requirement', '')} {snippet.get('responsibility', '')}"
        
        # Check if already seen
        existing = conn.execute(
            "SELECT id FROM jobs WHERE service=? AND url=?", 
            (service, url)
        ).fetchone()
        
        if existing:
            continue
        
        # Auto-match based on keywords
        keywords = get_config(f"{service}_keywords", ["python", "sql", "api", "docker", "git"])
        score = sum(1 for kw in keywords if kw.lower() in skills_text.lower() or kw.lower() in title.lower())
        matched = 1 if score >= 2 else 0
        
        conn.execute("""
            INSERT OR IGNORE INTO jobs 
            (service, title, company, url, skills, salary_min, salary_max, currency, location, matched)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (service, title, company, url, skills_text[:500], salary_min, salary_max,
              currency, v.get("area", {}).get("name"), matched))
        
        new_count += 1
        if matched:
            match_count += 1
    
    conn.commit()
    conn.close()
    return new_count, match_count

def generate_cover_letter(vacancy):
    """Generate cover letter using local Ollama."""
    title = vacancy.get("name", "")
    company = vacancy.get("employer", {}).get("name", "")
    skills = vacancy.get("snippet", {}).get("requirement", "")
    
    prompt = f"""Напиши короткое сопроводительное письмо (3-4 предложения) для вакансии {title} в компанию {company}.
Требования: {skills}
Письмо должно быть профессиональным, на русском языке, от кандидата с опытом Python разработки."""

    try:
        import requests as r
        resp = r.post("http://localhost:11434/api/generate", json={
            "model": "qwen3.5:4b",
            "prompt": prompt,
            "stream": False
        }, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[HH] Ollama error: {e}")
    return ""

def run_once():
    """Single run for cron usage."""
    query = get_config("hh_query", "Python developer")
    area = get_config("hh_area", 113)
    
    print(f"[HH] Searching for: {query}")
    vacancies = search_vacancies(query, area, 20)
    print(f"[HH] Found {len(vacancies)} vacancies")
    
    new, matched = process_vacancies(vacancies)
    print(f"[HH] New: {new}, Matched: {matched}")
    
    if matched > 0:
        # Get matched vacancies
        conn = get_conn()
        matches = conn.execute(
            "SELECT * FROM jobs WHERE service='hh-monitor' AND matched=1 AND seen=0 ORDER BY id DESC LIMIT 5"
        ).fetchall()
        conn.close()
        
        for m in matches:
            cv = generate_cover_letter(dict(m))
            msg = f"🔔 Совпадение вакансии!\n{m['title']} - {m['company']}\n{m['url']}\n\nСопроводительное:\n{cv[:500]}"
            send_hermes_message(msg)
            notify("hh-monitor", m['title'], f"Матчинг: {m['company']}", "info")
    
    print(f"[HH] Done. Stats: new={new}, matched={matched}")
    return {"new": new, "matched": matched}

if __name__ == "__main__":
    run_once()
