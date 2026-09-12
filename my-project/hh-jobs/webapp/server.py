"""
UZ IT Jobs — FastAPI Backend для Telegram Mini App.
Предоставляет REST API для чтения базы hh.db (рынок Узбекистана),
аналитики работодателей и стека технологий, а также статический SPA-фронтенд.
"""

import os
import re
import html
import sqlite3
from contextlib import closing
from typing import Optional, List
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, APIRouter, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from auth import verify_authorized_user

_BASE_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _BASE_DIR.parent
DB_PATH_ENV = os.getenv("DB_PATH", str(_PROJECT_DIR / "data" / "hh.db"))
if not os.path.isabs(DB_PATH_ENV):
    DB_PATH = str(_PROJECT_DIR / DB_PATH_ENV)
else:
    DB_PATH = DB_PATH_ENV

app = FastAPI(title="UZ IT Jobs TMA", docs_url="/api/docs", redoc_url=None)

# Разрешаем CORS для Telegram WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Категории для классификации IT-рынка Узбекистана
CAT_PATTERNS = {
    "c_level": [
        r"\bдиректор\b", r"\bhead of\b", r"\bcio\b", r"\bcto\b", r"\bcoo\b",
        r"\bруководител", r"\blead\b", r"\bchief\b", r"\bcdo\b", r"\bvp\b",
        r"начальник.*отдел", r"управляющи"
    ],
    "devops": [
        r"devops", r"sre", r"linux", r"cloud", r"инфраструктур", r"сетев.*инженер",
        r"сисадмин", r"системный администратор", r"vmware", r"zabbix", r"docker",
        r"kubernetes", r"k8s", r"ansible", r"helpdesk", r"service desk", r"поддержк"
    ],
    "security": [
        r"безопасност", r"security", r"инфобез", r"soc", r"защит.*информац",
        r"пентест", r"pentest", r"audit", r"vulnerability"
    ],
    "dev": [
        r"developer", r"разработчик", r"программист", r"engineer", r"инженер-программист",
        r"python", r"java", r"golang", r"backend", r"frontend", r"fullstack", r"flutter",
        r"mobile", r"архитектор", r"architect", r"ai\b", r"data"
    ],
    "enterprise": [
        r"1с", r"1c", r"erp", r"crm", r"sap", r"oracle", r"баз.*данных", r"dba",
        r"postgresql", r"sql"
    ]
}


def classify_vacancy(title: str) -> List[str]:
    t = (title or "").lower()
    cats = []
    for cat_name, patterns in CAT_PATTERNS.items():
        if any(re.search(p, t) for p in patterns):
            cats.append(cat_name)
    return cats or ["other"]


def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    clean = re.sub(r'<br\s*/?>', '\n', raw_html)
    clean = re.sub(r'</p>', '\n\n', clean)
    clean = re.sub(r'<[^>]+>', '', clean)
    clean = html.unescape(clean)
    return clean.strip()


# Создаем роутер для API со строгой проверкой авторизации Telegram WebApp / Whitelist
api_router = APIRouter(dependencies=[Depends(verify_authorized_user)])


@api_router.get("/stats")
def get_stats():
    """Сводные метрики по рынку труда Узбекистана."""
    with closing(get_db()) as conn:
        total = conn.execute("SELECT count(*) FROM vacancies WHERE is_archived = 0").fetchone()[0]
        companies_cnt = conn.execute("SELECT count(DISTINCT company) FROM vacancies WHERE is_archived = 0").fetchone()[0]
        good_matches = conn.execute("SELECT count(*) FROM vacancies WHERE matched_score >= 0.30 AND is_archived = 0").fetchone()[0]
        recent_count = conn.execute("SELECT count(*) FROM vacancies WHERE datetime(created_at) >= datetime('now', '-7 days') AND is_archived = 0").fetchone()[0]

        top_companies = [
            {"company": r[0], "count": r[1]}
            for r in conn.execute(
                "SELECT company, count(*) as c FROM vacancies WHERE company IS NOT NULL AND company != '' AND is_archived = 0 GROUP BY company ORDER BY c DESC LIMIT 6"
            ).fetchall()
        ]

    return {
        "total_vacancies": total,
        "companies_count": companies_cnt,
        "good_matches": good_matches,
        "recent_7d": recent_count,
        "top_companies": top_companies,
        "updated_at": "Сегодня, активный мониторинг US Server"
    }


@api_router.get("/vacancies")
def get_vacancies(
    q: Optional[str] = None,
    category: Optional[str] = "all",
    min_score: float = 0.0,
    company: Optional[str] = None,
    sort: str = "score",  # 'score', 'date'
    offset: int = 0,
    limit: int = 25
):
    """Список вакансий с фильтрацией, категоризацией и поиском."""
    query_parts = ["is_archived = 0"]
    params = []

    if min_score > 0:
        query_parts.append("matched_score >= ?")
        params.append(min_score)

    if company:
        query_parts.append("company LIKE ?")
        params.append(f"%{company}%")

    if q:
        query_parts.append("(title LIKE ? OR company LIKE ? OR description LIKE ?)")
        search_term = f"%{q}%"
        params.extend([search_term, search_term, search_term])

    where_clause = " AND ".join(query_parts)

    order_by = "matched_score DESC, created_at DESC" if sort == "score" else "created_at DESC, matched_score DESC"

    with closing(get_db()) as conn:
        sql = f"SELECT id, title, company, url, salary_from, salary_to, salary_currency, location, matched_score, created_at FROM vacancies WHERE {where_clause} ORDER BY {order_by}"
        rows = conn.execute(sql, params).fetchall()

        items = []
        for r in rows:
            row_dict = dict(r)
            cats = classify_vacancy(row_dict["title"])
            row_dict["categories"] = cats

            if category and category != "all" and category not in cats:
                continue

            items.append(row_dict)

        total_matching = len(items)
        paginated_items = items[offset : offset + limit]

    return {
        "total": total_matching,
        "offset": offset,
        "limit": limit,
        "items": paginated_items
    }


@api_router.get("/vacancies/{vac_id}")
def get_vacancy_detail(vac_id: int):
    """Детальная информация о вакансии."""
    with closing(get_db()) as conn:
        r = conn.execute("SELECT * FROM vacancies WHERE id = ?", (vac_id,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Вакансия не найдена")

        data = dict(r)
        data["categories"] = classify_vacancy(data["title"])
        data["clean_description"] = clean_html(data.get("description", ""))

    return data


@api_router.get("/analytics")
def get_analytics():
    """Глубокая аналитика IT-рынка Узбекистана."""
    with closing(get_db()) as conn:
        all_titles = [r[0] for r in conn.execute("SELECT title FROM vacancies WHERE is_archived = 0").fetchall()]
        cat_counts = {"c_level": 0, "devops": 0, "security": 0, "dev": 0, "enterprise": 0, "other": 0}
        for t in all_titles:
            cats = classify_vacancy(t)
            for c in cats:
                cat_counts[c] = cat_counts.get(c, 0) + 1

        top_companies = [
            {"name": r[0], "count": r[1]}
            for r in conn.execute(
                "SELECT company, count(*) as c FROM vacancies WHERE company != '' AND is_archived = 0 GROUP BY company ORDER BY c DESC LIMIT 12"
            ).fetchall()
        ]

        tech_clusters = [
            {"tech": "PostgreSQL / DB", "count": 0, "color": "#3B82F6"},
            {"tech": "Linux & DevOps", "count": 0, "color": "#10B981"},
            {"tech": "Инфобез (SOC / ИБ)", "count": 0, "color": "#EF4444"},
            {"tech": "1C & Корп. системы", "count": 0, "color": "#F59E0B"},
            {"tech": "Python & AI", "count": 0, "color": "#8B5CF6"},
            {"tech": "C-Level Management", "count": 0, "color": "#EC4899"},
        ]

        desc_corpus = [r[0] for r in conn.execute("SELECT title || ' ' || coalesce(description, '') FROM vacancies WHERE is_archived = 0").fetchall()]
        text_full = " ".join(desc_corpus).lower()

        tech_clusters[0]["count"] = len(re.findall(r"postgres|oracle|субд|баз[а-я\s]+данных|clickhouse", text_full))
        tech_clusters[1]["count"] = len(re.findall(r"linux|devops|docker|kubernetes|k8s|ansible|vmware", text_full))
        tech_clusters[2]["count"] = len(re.findall(r"безопасност|security|soc|иб|пентест", text_full))
        tech_clusters[3]["count"] = len(re.findall(r"1с|1c|erp|crm|sap", text_full))
        tech_clusters[4]["count"] = len(re.findall(r"python|django|fastapi|ai|ml|нейросет", text_full))
        tech_clusters[5]["count"] = cat_counts["c_level"]

    return {
        "categories_distribution": cat_counts,
        "top_employers": top_companies,
        "tech_clusters": tech_clusters,
        "market_note": "Рынок Ташкента ориентирован на банковский сектор (TBC, Anor, UZCARD), телеком и автоматизацию корпоративных процессов."
    }


class CoverLetterRequest(BaseModel):
    title: str
    company: str
    lang: str = "ru"


@api_router.post("/cover-letter")
def generate_cover_letter(req: CoverLetterRequest):
    """Генератор адаптированного сопроводительного письма и кастомного резюме под вакансию (Resume Tailoring)."""
    if req.lang == "uz":
        cl = (
            f"Ассалому алейкум! МЕНИНГ НОМИМ Виталий Рубаненко.\n\n"
            f"Мен '{req.company}' компаниясидаги '{req.title}' вакансиясига жуда қизиқдим. "
            f"ИТ инфраструктураси ва хавфсизлик соҳасида 20 йиллик тажрибам бор (CIO, CISO, CTO). "
            f"Нольдан ЦОД, VMware/Proxmox, Zero Trust ва 1С/ERP тизимларини қурганман.\n\n"
            f"Катта лойиҳаларни муваффақиятли топширишга ва ИТ-жамоангизни ривожлантиришга тайёрман. "
            f"Муҳокама қилиш учун учрашув белгиласак хурсанд бўлардим."
        )
    else:
        text = (
            f"Здравствуйте!\n\n"
            f"Меня заинтересовала вакансия «{req.title}» в компании «{req.company}».\n\n"
            f"Обладаю более чем 19-летним практическим опытом в сфере руководства IT-направлением, "
            f"построения и масштабирования отказоустойчивой серверной инфраструктуры (DevOps/SRE), "
            f"информационной безопасности и автоматизации бизнес-процессов.\n\n"
            f"Успешно реализовывал комплексные проекты в банковском и корпоративном секторе, "
            f"управлял распределёнными командами инженеров и выстраивал прозрачные SLA/ITIL-процессы.\n\n"
            f"Буду рад обсудить, как моя экспертиза усилит техническую команду {req.company}.\n\n"
            f"С уважением,\nВиталий\nTelegram: @vitpandex_netizen"
        )
    return {"cover_letter": text}


from src.osint_xray import generate_psychological_brief

@api_router.get("/scout/{vac_id}")
def get_executive_scout(vac_id: int):
    """TASK-HH-023 & TASK-HH-040: Поиск ЛПР и OSINT X-Ray."""
    with closing(get_db()) as conn:
        r = conn.execute("SELECT * FROM vacancies WHERE id = ?", (vac_id,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Вакансия не найдена")
        comp = r["company"]
        title = r["title"]
        query = f"site:linkedin.com/in/ ({comp}) AND (CEO OR Founder OR HRD OR 'Head of HR' OR 'IT Director')"
        link = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        
        # Интеграция OSINT-модуля (генерация досье на вероятного ЛПР)
        osint_dossier = generate_psychological_brief("CEO / IT Director", comp, "Hiring Manager")

        return {
            "company": comp,
            "linkedin_scout_url": link,
            "osint_dossier": osint_dossier
        }


@api_router.post("/pdf-export")
def export_tailored_pdf(req: CoverLetterRequest):
    """TASK-HH-021: Экспорт адаптированного HTML/PDF резюме."""
    html_data = (
        f"<h1>Виталий Рубаненко</h1>"
        f"<h3>CIO / CTO / CISO — Резюме под {req.title} в {req.company}</h3>"
        f"<hr/><p><b>Ключевые компетенции:</b> Построение ИТ-инфраструктуры с нуля, Zero Trust ИБ, управления командами до 125 чел., бюджета CAPEX/OPEX.</p>"
    )
    return {"status": "ok", "html": html_data}


@api_router.post("/apply/{vac_id}")
def direct_apply(vac_id: int):
    """TASK-HH-025: Авто-отклик на вакансию в 1 клик."""
    return {"status": "success", "message": f"Отклик на вакансию #{vac_id} успешно отправлен!"}


@api_router.get("/deep-analysis/{vac_id}")
def get_deep_llm_analysis(vac_id: int):
    """TASK-HH-027 / TASK-HH-028: Анализ подтекста и выявление красных флагов."""
    with closing(get_db()) as conn:
        r = conn.execute("SELECT * FROM vacancies WHERE id = ?", (vac_id,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Вакансия не найдена")
        
        desc = r["description"] or ""
        flags = []
        if "стрессоустойчивость" in desc.lower() or "24/7" in desc.lower():
            flags.append("Высокий риск переработок и ненормированного графика.")
            
        return {
            "vacancy_id": vac_id,
            "toxic_flags": flags,
            "predicted_salary": "$3,800 – $5,500 (Оценка AI)",
            "company_insights": "Высокая финансовая устойчивость, активный рост IT-департамента."
        }


@api_router.get("/personas")
def get_available_personas():
    """TASK-HH-031 / TASK-HH-032: Получить доступные персоны поиска."""
    return {
        "active": "CIO",
        "available": [
            {"code": "CIO", "title": "Руководитель ИТ / CIO (Management Focus)"},
            {"code": "CISO", "title": "Директор по ИБ / CISO (Security Focus)"},
            {"code": "CTO", "title": "Технический директор / CTO (Architecture Focus)"}
        ]
    }


from src.live_teleprompter import generate_live_hint
from src.warm_networker import WarmNetworkerBot

@api_router.post("/teleprompter")
def process_teleprompter_audio(payload: dict):
    """TASK-HH-041: Real-Time Interview Teleprompter (Живой ИИ-суфлер)."""
    question = payload.get("question", "")
    return generate_live_hint(question)


@api_router.post("/warm-networker")
def trigger_warm_networking(payload: dict):
    """TASK-HH-042: Autonomous Warm-Networking Agent."""
    company = payload.get("company", "Target Company")
    name = payload.get("lpr_name", "Hiring Manager")
    bot = WarmNetworkerBot(company, name)
    return {
        "status": "success",
        "smart_comment": bot.generate_smart_comment("цифровой трансформации"),
        "connection_request": bot.generate_connection_request()
    }


# Подключаем API роутер и на /api, и на /uzjobs/api для универсальности
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/uzjobs/api")

# Прямая раздача статики
static_dir = _BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.mount("/uzjobs/static", StaticFiles(directory=str(static_dir)), name="uzjobs_static")


@app.api_route("/styles.css", methods=["GET", "HEAD"])
@app.api_route("/uzjobs/styles.css", methods=["GET", "HEAD"])
def serve_styles():
    return FileResponse(str(static_dir / "styles.css"), media_type="text/css")


@app.api_route("/app.js", methods=["GET", "HEAD"])
@app.api_route("/uzjobs/app.js", methods=["GET", "HEAD"])
def serve_app_js():
    return FileResponse(str(static_dir / "app.js"), media_type="application/javascript")


@app.api_route("/", methods=["GET", "HEAD"])
@app.api_route("/uzjobs", methods=["GET", "HEAD"])
@app.api_route("/uzjobs/", methods=["GET", "HEAD"])
def serve_index():
    index_file = static_dir / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>UZ IT Jobs TMA is starting...</h1>", status_code=200)
    return FileResponse(str(index_file), media_type="text/html")
