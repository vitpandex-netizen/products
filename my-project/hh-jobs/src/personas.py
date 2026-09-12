#!/usr/bin/env python3
"""
UZ IT Jobs — Multi-Persona Architecture (TASK-HH-031 / TASK-HH-032).
Управление профилями (CIO / CISO / CTO) и весами матчинга.
"""

import os
import sys
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [personas] %(message)s"
)
logger = logging.getLogger("personas")

PERSONAS = {
    "CIO": {
        "title": "Руководитель ИТ / CIO / IT Director",
        "keywords": ["CIO", "IT Director", "Руководитель ИТ", "ITSM", "ITIL", "Бюджетирование", "Управление командой"],
        "min_salary": 38700000
    },
    "CISO": {
        "title": "Директор по ИБ / CISO / Head of Security",
        "keywords": ["CISO", "Информационная безопасность", "Zero Trust", "DLP", "SearchInform", "SOC", "Аудит ИБ"],
        "min_salary": 38700000
    },
    "CTO": {
        "title": "Технический директор / CTO / VP of Engineering",
        "keywords": ["CTO", "Технический директор", "Архитектура", "HighLoad", "DevOps", "Proxmox", "VMware"],
        "min_salary": 38700000
    }
}

def get_active_persona(persona_name: str = "CIO") -> dict:
    return PERSONAS.get(persona_name.upper(), PERSONAS["CIO"])

if __name__ == "__main__":
    logger.info(f"Доступные персоны поиска: {list(PERSONAS.keys())}")
