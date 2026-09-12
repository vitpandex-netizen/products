#!/usr/bin/env python3
"""
UZ IT Jobs — PDF Resumes Exporter Engine (TASK-HH-021).
Генерирует кастомное резюме в формате HTML/PDF, адаптированное под требования позиции.
"""

import os
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [pdf-exporter] %(message)s"
)
logger = logging.getLogger("pdf-exporter")

def generate_tailored_pdf_html(title: str, company: str) -> str:
    """Формирует адаптивную печатную HTML-версию резюме."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Резюме — Виталий Рубаненко под {title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #111827; }}
            h1 {{ color: #1D4ED8; margin-bottom: 5px; }}
            .subtitle {{ color: #4B5563; font-weight: bold; margin-bottom: 20px; }}
            .section {{ margin-bottom: 20px; }}
            .section-title {{ font-size: 16px; font-weight: bold; border-bottom: 2px solid #E5E7EB; padding-bottom: 5px; margin-bottom: 10px; color: #1F2937; }}
            ul {{ margin: 5px 0; padding-left: 20px; }}
            li {{ margin-bottom: 5px; }}
        </style>
    </head>
    <body>
        <h1>Виталий Рубаненко</h1>
        <div class="subtitle">CIO / CTO / CISO | Адаптировано под позицию {title} в {company}</div>
        
        <div class="section">
            <div class="section-title">Профильные выжимки под вакансию</div>
            <ul>
                <li><b>Управление и Масштабирование:</b> 20+ лет опыта, руководство командами до 125 специалистов, бюджетирование CAPEX/OPEX, ITSM/ITIL.</li>
                <li><b>Инфраструктура & ЦОД:</b> Построение архитектуры с нуля (VMware, Hyper-V, Proxmox), 22+ филиала, отказоустойчивость 99.9%.</li>
                <li><b>Информационная Безопасность:</b>Zero Trust, DLP (SearchInform), комплаенс, защита периметра и аудит контролей (Deloitte).</li>
            </ul>
        </div>

        <div class="section">
            <div class="section-title">Контакты</div>
            <p>Телефон: +998 (90) 969-47-31 | Telegram: @VitaliyCIO | Email: vitaliy.rubanenko@yahoo.com</p>
        </div>
    </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    logger.info("PDF Exporter Engine инициализирован.")
