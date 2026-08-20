"""
Seed — заполняет БД идеями из первого исследования и отправляет отчёт в Telegram.
Запуск: ./venv/bin/python3 src/seed.py
"""

import sys
import os
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent
os.chdir(str(_BASE))
sys.path.insert(0, str(_BASE))
sys.path.insert(0, str(_BASE.parent))

from dotenv import load_dotenv
load_dotenv(_BASE / '.env')

from src.db import PassiveIncomeDB
from src.researcher import Researcher
from src.telegram import TelegramNotifier

SEED_IDEAS = [
    {
        "title": "Дивидендные акции UZSE (Ташкентская биржа)",
        "category": "investments",
        "description": "Покупка акций узбекских компаний на UZSE. Порог входа минимальный (бумаги стоят копейки). Доступ через брокеров GoInvest, JETT. Дивидендный доход + потенциальный рост капитала.",
        "source_summary": "Подтверждено: порог входа нулевой, доступ через лицензированного брокера, паспорт + MyID. Источник: spot.uz"
    },
    {
        "title": "Инвестиции через зарубежных брокеров (IBKR, Freedom24)",
        "category": "investments",
        "description": "Открытие счёта у международного брокера (Interactive Brokers, Freedom24, Just2Trade). Доступ к мировым рынкам, ETF, дивидендным акциям. Резиденты Узбекистана принимаются.",
        "source_summary": "Подтверждено: Just2Trade, Freedom Finance Europe/Freedom24, IBKR, EXANTE, Finam принимают резидентов Узбекистана. Источник: allfinancelinks.com"
    },
    {
        "title": "Аренда недвижимости в Ташкенте",
        "category": "real_estate",
        "description": "Покупка квартиры/дома под сдачу. Налог от вменённой ставки 28 000 сум/кв.м (2025). Самый капиталоёмкий вариант, требует существенного первоначального взноса.",
        "source_summary": "Подтверждено: налог от вменённой ставки, не от фактической аренды. Ставка 28 000 сум/кв.м. Источник: gazeta.uz"
    },
    {
        "title": "Создание и продажа цифровых продуктов (шаблоны, курсы, книги)",
        "category": "digital_products",
        "description": "Создание Notion-шаблонов, онлайн-курсов, электронных книг, цифровых шаблонов на Etsy/Gumroad. Старт $0-500, первый доход через 1-3 мес. Требует постоянного производства контента.",
        "source_summary": "Не проверено: цифры из блогов. Notion-шаблоны до $20-100K/мес (не подтверждено). Реалистично $500-5000/мес."
    },
    {
        "title": "DevOps/IT инфраструктура — удалённый консалтинг",
        "category": "freelance",
        "description": "Удалённая работа/консалтинг по IT-инфраструктуре, M365, VMware, Proxmox, Zero Trust, ITSM. Огромный опыт (19+ лет IT, 10 лет руководителем). Можно работать на зарубежные компании.",
        "source_summary": "Прямое применение навыков: IT Director, управление командами до 28 человек, инфраструктура с нуля."
    },
    {
        "title": "Telegram-канал про IT/инвестиции для Узбекистана",
        "category": "content",
        "description": "Создание тематического канала про IT-инфраструктуру, инвестиции, удалённую работу. Монетизация через рекламу, партнёрские программы, платные подписки. Низкий порог входа, требует регулярного контента.",
        "source_summary": "Проверка не доехала. Партнёрские сайты с трафиком: $1K-5K/мес (не проверено)."
    },
    {
        "title": "Партнёрский маркетинг (affiliate) для IT-продуктов",
        "category": "affiliate",
        "description": "Продвижение SaaS, хостинга, VPS, облачных сервисов через партнёрские ссылки. Целевая аудитория — IT-специалисты в Узбекистане и СНГ. Полностью удалённо, пассивный доход после настройки воронки.",
        "source_summary": "Не проверено: маркетинговые цифры из блогов. Требует постоянного производства контента."
    },
    {
        "title": "Фриланс-платформы для IT-специалистов из Узбекистана",
        "category": "freelance",
        "description": "Работа через Upwork, Toptal, Fiverr в сфере IT/DevOps/инфраструктуры. Высокий спрос на специалистов по M365, VMware, облачным технологиям. Полностью удалённо, долларовый доход.",
        "source_summary": "Прямое применение навыков. Узбекистанские специалисты востребованы на международных платформах."
    },
    {
        "title": "Создание IT-продукта/SaaS для локального рынка",
        "category": "automated_biz",
        "description": "Разработка небольшого SaaS-продукта под нужды узбекского рынка (автоматизация бизнеса, учёт, CRM). Низкая конкуренция в локальных нишах. Высокий потенциал при правильном выборе ниши.",
        "source_summary": "Идея на основе анализа рынка. Требует исследования конкретной ниши."
    },
    {
        "title": "Стейкинг криптовалют и DeFi",
        "category": "crypto",
        "description": "Пассивный доход через стейкинг криптовалют (Ethereum, Solana и др.) или DeFi-протоколы. Высокий риск, высокая потенциальная доходность. Минимальный порог входа, полностью удалённо.",
        "source_summary": "Стандартный инструмент, требует понимания рынка и управления рисками."
    },
    {
        "title": "Пассивный доход через дивидендные ETF (VOO, VTI, SCHD)",
        "category": "investments",
        "description": "Покупка дивидендных ETF через зарубежного брокера. Правило 4%: для $4000/мес нужно $1.2M вложений. Низкие трудозатраты, высокий порог капитала для значимого дохода.",
        "source_summary": "Подтверждено: правило 4% — отрезвляющая математика. $48K/год = $1.2M капитала. Дивидендное инвестирование близко к 100% пассивному."
    },
    {
        "title": "Франшиза в Узбекистане (локальный бизнес)",
        "category": "local_biz",
        "description": "Покупка франшизы международного бренда для работы в Узбекистане. Требует капитала и управления. Высокий потенциал на растущем рынке, но низкая пассивность.",
        "source_summary": "Идея для рассмотрения. Требует исследования конкретных франшиз и рынка."
    },
]


def seed():
    db = PassiveIncomeDB()
    count = 0

    for idea in SEED_IDEAS:
        existing = db.execute("SELECT id FROM ideas WHERE title = ?", (idea["title"],))
        if existing:
            print(f"  ↪ Уже есть: {idea['title']}")
            continue

        idea_id = db.add_idea(
            title=idea["title"],
            category=idea["category"],
            description=idea["description"],
            source_summary=idea.get("source_summary", ""),
        )

        # Оценка по умолчанию (консервативная)
        db.evaluate_idea(
            idea_id=idea_id,
            capital=7 if idea["category"] in ("real_estate", "investments", "local_biz") else 3,
            expected_return=6 if idea["category"] in ("investments", "crypto", "automated_biz") else 5,
            effort_startup=8 if idea["category"] in ("digital_products", "automated_biz") else 4,
            effort_maintenance=4 if idea["category"] in ("investments", "crypto") else 6,
            payback_months=12 if idea["category"] in ("investments", "real_estate") else 6,
            risk=8 if idea["category"] == "crypto" else 5,
            applicability=8 if idea["category"] in ("local_biz", "real_estate") else 6,
            remote=9 if idea["category"] in ("freelance", "digital_products", "crypto", "affiliate") else 4,
            notes="Seed из первого исследования",
        )

        db.set_status(idea_id, "new", "Seed из первого исследования (2026-08-05)")
        count += 1
        print(f"  ✅ Добавлено: {idea['title']}")

    db.log_run("seed", len(SEED_IDEAS), count, f"Seed: {count} новых идей")
    print(f"\n✅ Всего добавлено: {count} идей")

    # Отправляем отчёт в Telegram
    from src.researcher import Researcher
    from src.telegram import TelegramNotifier
    researcher = Researcher(db)
    notifier = TelegramNotifier()

    ranked = db.get_ranked_ideas(limit=15)
    stats = db.get_stats()
    report = researcher.format_report(ranked)
    header = (
        f"🌱 <b>Passive Income — база идей загружена</b>\n"
        f"📅 {__import__('datetime').datetime.now(__import__('datetime').timezone(__import__('datetime').timedelta(hours=5))).strftime('%d.%m.%Y %H:%M')}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"Загружено: {count} идей | Всего в БД: {stats['total_ideas']}\n\n"
    )
    full_report = header + report
    notifier.send_report(full_report)
    print(full_report)


if __name__ == "__main__":
    seed()
