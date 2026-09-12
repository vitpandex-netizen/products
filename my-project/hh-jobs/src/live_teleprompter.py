#!/usr/bin/env python3
"""
UZ IT Jobs — Real-Time Interview Teleprompter & Live Copilot (TASK-HH-041).
Архитектурный прототип сервера подписки по WebSocket / HTTP для подсказа на собеседовании.
Слушает вопрос интервьюера (STT/Whisper) и налету генерирует шпаргалки.
"""

import logging
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [teleprompter] %(message)s")
logger = logging.getLogger("teleprompter")

def generate_live_hint(transcript_text: str) -> dict:
    """Анализирует фразу интервьюера в реальном времени и выдает подсказку."""
    logger.info(f"Анализ вопроса интервьюера: '{transcript_text}'")
    
    text_lower = transcript_text.lower()
    hint = "Подчеркните 20-летний опыт управления ИТ-инфраструктурой и комплексный подход."
    
    if "бюджет" in text_lower or "opex" in text_lower or "capex" in text_lower:
        hint = "💡 Подсказка: Расскажите, как вы управляли CAPEX/OPEX бюджетами в Neftgazmontaj на 400+ юзеров и 17 филиалов."
    elif "безопасность" in text_lower or "zero trust" in text_lower or "dlp" in text_lower:
        hint = "💡 Подсказка: Сошлитесь на опыт построения Zero Trust ИБ с нуля и внедрение DLP SearchInform в банковском/промышленном секторе."
    elif "команда" in text_lower or "люди" in text_lower or "поддержка" in text_lower:
        hint = "💡 Подсказка: Упомяните построение службы SPOC / Jira Service Management и руководство командами до 125 специалистов (Innova Expert)."
    elif "цод" in text_lower or "виртуализация" in text_lower or "proxmox" in text_lower:
        hint = "💡 Подсказка: Расскажите про развертывание кластеров VMware vSphere/ESXi, Hyper-V и Proxmox для 22 локаций клиник."

    return {
        "status": "active",
        "question_detected": transcript_text,
        "live_hint": hint
    }

if __name__ == "__main__":
    res = generate_live_hint("Как вы выстраивали управление бюджетом и отчетами?")
    logger.info(f"Тест Live Teleprompter: {json.dumps(res, ensure_ascii=False, indent=2)}")
