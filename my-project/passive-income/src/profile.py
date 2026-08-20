from pathlib import Path
"""Profile — твой профессиональный профиль для откликов на вакансии."""

PROFILE = {
    "name": "Виталий",
    "title": "IT Director / Head of IT Infrastructure",
    "location": "Ташкент, Узбекистан (UTC+5)",
    "experience_years": 19,
    "management_years": 10,
    "salary_expectation": "$4,000-6,000/net",
    "ready_to_relocate": False,
    "remote_only": True,
    "languages": ["Русский (native)", "Английский (Intermediate)"],
    "technologies": [
        "VMware vSphere", "Hyper-V", "Proxmox VE",
        "Microsoft 365 / Exchange Online",
        "Zero Trust Architecture", "ITSM / ITIL",
        "Active Directory", "Azure AD / Entra ID",
        "VPN / SD-WAN", "Network Security",
        "СКУД / СКС / Video Surveillance",
        "Zabbix", "Jira Service Management",
        "Docker / Proxmox Containers",
    ],
    "achievements": [
        "Построил IT-инфраструктуру с нуля в финтехе",
        "Управлял командами до 28 человек",
        "Внедрил Zero Trust архитектуру",
        "M365 миграция и администрирование",
        "ITSM процессы с нуля до ISO",
    ],
    "industries": [
        "Fintech", "Банкинг", "Ритейл",
        "Нефтегаз", "Промышленность", "HoReCa",
    ],
    "work_format": "Только удалённо / гибрид (Ташкент)",
}

def format_profile_html() -> str:
    """Генерирует HTML-страницу профиля."""
    t = PROFILE
    techs = " ".join(f'<span class="tag">{t}</span>' for t in t["technologies"])
    achievements = "".join(f'<li>{a}</li>' for a in t["achievements"])
    industries = " ".join(f'<span class="tag">{ind}</span>' for ind in t["industries"])

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t['title']} — {t['name']}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.6; }}
.container {{ max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
.header {{ text-align: center; margin-bottom: 40px; }}
.header h1 {{ font-size: 2.5em; color: #38bdf8; margin-bottom: 8px; }}
.header .title {{ font-size: 1.3em; color: #94a3b8; }}
.header .location {{ color: #64748b; margin-top: 4px; }}
.header .salary {{ display: inline-block; background: #1e293b; padding: 8px 20px; border-radius: 20px; margin-top: 12px; color: #4ade80; font-weight: bold; }}
.section {{ background: #1e293b; border-radius: 12px; padding: 24px; margin-bottom: 20px; }}
.section h2 {{ color: #38bdf8; margin-bottom: 16px; font-size: 1.2em; }}
.tags {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.tag {{ background: #334155; padding: 6px 14px; border-radius: 16px; font-size: 0.9em; color: #cbd5e1; }}
ul {{ list-style: none; }}
li {{ padding: 8px 0; border-bottom: 1px solid #334155; }}
li:last-child {{ border: none; }}
li::before {{ content: "→ "; color: #38bdf8; }}
.cta {{ text-align: center; margin-top: 30px; }}
.cta a {{ display: inline-block; background: #38bdf8; color: #0f172a; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1.1em; }}
.cta a:hover {{ background: #7dd3fc; }}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>{t['name']}</h1>
<div class="title">{t['title']}</div>
<div class="location">{t['location']} · {t['experience_years']} лет в IT · {t['management_years']} лет руководителем</div>
<div class="salary">💰 {t['salary_expectation']}</div>
</div>

<div class="section">
<h2>🛠 Технологии</h2>
<div class="tags">{techs}</div>
</div>

<div class="section">
<h2>🏆 Ключевые достижения</h2>
<ul>{achievements}</ul>
</div>

<div class="section">
<h2>🏭 Отрасли</h2>
<div class="tags">{industries}</div>
</div>

<div class="section">
<h2>🌐 Языки</h2>
<p>{' · '.join(t['languages'])}</p>
</div>

<div class="section">
<h2>📋 Формат работы</h2>
<p>{t['work_format']}</p>
</div>

<div class="cta">
<a href="https://www.linkedin.com">Создать профиль на LinkedIn</a>
</div>
</div>
</body>
</html>"""

def format_cover_letter(company: str, position: str) -> str:
    """Генерирует сопроводительное письмо."""
    return f"""Тема: Отклик на вакансию {position} в {company}

Здравствуйте!

Я — IT-директор с 19+ годами опыта в управлении IT-инфраструктурой, 
10 лет на руководящих позициях. Специализируюсь на:

• VMware vSphere, Hyper-V, Proxmox VE
• Microsoft 365 / Exchange Online, Zero Trust
• ITSM/ITIL, управление командами до 28 человек
• Построение инфраструктуры с нуля

Работаю удалённо из Ташкента (UTC+5), готов к гибкому графику.
Ожидания по зарплате: $4,000-6,000/net.

Буду рад обсудить детали на собеседовании.

С уважением,
Виталий"""


if __name__ == "__main__":
    # Сохраняю HTML-профиль
    html = format_profile_html()
    path = Path(__file__).resolve().parent.parent / "profile.html"
    path.write_text(html, encoding="utf-8")
    print(f"✅ Profile saved: {path}")
    print(f"📄 Размер: {len(html)} байт")
    
    # Пример письма
    print("\n=== Пример сопроводительного ===")
    print(format_cover_letter("Google", "IT Director, Infrastructure"))
