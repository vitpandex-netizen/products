#!/usr/bin/env python3
"""
МАСТЕР СКРИПТ: Запустить все 8 задач и показать отчёт

🎯 Использование:
    python3 run_all.py [task_id]
    python3 run_all.py all          # Запустить все
    python3 run_all.py task_5       # Запустить Task 5
    python3 run_all.py report       # Показать отчёт
"""

import sys
import os
from datetime import datetime
from cost_tracker import CostTracker

# Импортируем задачи
from task_1_hh_jobs import match_job_and_create_application
from task_2_stocks_local import analyze_local_stock
from task_3_stocks_usa import analyze_usa_stock
from task_4_world_events import get_world_events
from task_5_education import generate_course_optimized
from task_6_confidential import analyze_confidential_data
from task_7_passive_income import generate_passive_income_ideas
from task_8_finances import analyze_finances

tracker = CostTracker("agent_costs.jsonl")

def show_welcome():
    """Показать приветствие"""
    print("\n" + "="*70)
    print("🚀 МАСТЕР СКРИПТ: ВСЕ 8 ЗАДАЧ")
    print("="*70)
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 API: OpenRouter")
    print(f"📊 Трекер: agent_costs.jsonl\n")


def run_task_5():
    """Запустить Task 5 (обучение)"""
    print("\n" + "="*70)
    print("📚 TASK 5: ОБУЧЕНИЕ (Education)")
    print("="*70)

    topics = ["Python Basics", "FastAPI", "Machine Learning"]

    for topic in topics:
        print(f"\n🎓 {topic}")
        generate_course_optimized(topic)


def run_task_4():
    """Запустить Task 4 (события)"""
    print("\n" + "="*70)
    print("🌍 TASK 4: МИРОВЫЕ СОБЫТИЯ (World Events)")
    print("="*70)

    for category in ["technology", "energy"]:
        print(f"\n📌 {category.upper()}")
        get_world_events(category)


def run_task_7():
    """Запустить Task 7 (пассивный доход)"""
    print("\n" + "="*70)
    print("💰 TASK 7: ПАССИВНЫЙ ДОХОД (Passive Income)")
    print("="*70)

    for capital in [5000, 10000]:
        print(f"\n💵 ${capital}")
        generate_passive_income_ideas(capital)


def run_task_8():
    """Запустить Task 8 (финансы)"""
    print("\n" + "="*70)
    print("💳 TASK 8: ФИНАНСОВЫЙ АНАЛИЗ (Finances)")
    print("="*70)

    for income in [3000, 5000]:
        print(f"\n💰 ${income}/месяц")
        analyze_finances(income)


def run_task_2():
    """Запустить Task 2 (локальные акции)"""
    print("\n" + "="*70)
    print("📈 TASK 2: ЛОКАЛЬНЫЕ АКЦИИ (Stocks Local)")
    print("="*70)

    for ticker in ["TASHKENT POWER", "ARTEL"]:
        print(f"\n📊 {ticker}")
        analyze_local_stock(ticker)


def run_task_3():
    """Запустить Task 3 (US акции)"""
    print("\n" + "="*70)
    print("🇺🇸 TASK 3: АМЕРИКАНСКИЕ АКЦИИ (Stocks USA)")
    print("="*70)

    for ticker in ["AAPL", "GOOGL"]:
        print(f"\n📊 {ticker}")
        analyze_usa_stock(ticker)


def run_task_1():
    """Запустить Task 1 (HH Jobs)"""
    print("\n" + "="*70)
    print("💼 TASK 1: ВАКАНСИИ HH (HH Jobs)")
    print("="*70)

    job = """
    Python Developer
    Company: TechCorp
    Salary: $6000
    Requirements: Python, FastAPI, 5+ years
    """

    print("\n💼 Вакансия 1")
    match_job_and_create_application(job)


def run_task_6():
    """Запустить Task 6 (конфиденциальный анализ)"""
    print("\n" + "="*70)
    print("🔐 TASK 6: КОНФИДЕНЦИАЛЬНЫЙ АНАЛИЗ (Confidential)")
    print("="*70)

    portfolio = {
        "cash": 50000,
        "stocks": {"AAPL": 10000, "GOOGL": 8000},
        "bonds": 15000,
    }

    print("\n💎 Портфель")
    analyze_confidential_data(portfolio)


def run_all_tasks():
    """Запустить все 8 задач"""
    show_welcome()

    tasks = [
        ("Task 1 (HH Jobs)", run_task_1),
        ("Task 2 (Stocks Local)", run_task_2),
        ("Task 3 (Stocks USA)", run_task_3),
        ("Task 4 (World Events)", run_task_4),
        ("Task 5 (Education)", run_task_5),
        ("Task 6 (Confidential)", run_task_6),
        ("Task 7 (Passive Income)", run_task_7),
        ("Task 8 (Finances)", run_task_8),
    ]

    print(f"🎯 Запускаю {len(tasks)} задач...\n")

    completed = 0
    for task_name, task_func in tasks:
        try:
            task_func()
            completed += 1
        except Exception as e:
            print(f"\n❌ {task_name} ошибка: {str(e)[:100]}")

    # ФИНАЛЬНЫЙ ОТЧЁТ
    print("\n" + "="*70)
    print("✅ ЗАВЕРШЕНО")
    print("="*70)
    print(f"✓ {completed}/{len(tasks)} задач выполнено")

    tracker.daily_report()
    tracker.monthly_summary()


def show_help():
    """Показать справку"""
    print("""
    ИСПОЛЬЗОВАНИЕ: python3 run_all.py [OPTION]

    ОПЦИИ:
        all                 Запустить все 8 задач
        task_1              Запустить Task 1 (HH Jobs)
        task_2              Запустить Task 2 (Stocks Local)
        task_3              Запустить Task 3 (Stocks USA)
        task_4              Запустить Task 4 (World Events)
        task_5              Запустить Task 5 (Education)
        task_6              Запустить Task 6 (Confidential)
        task_7              Запустить Task 7 (Passive Income)
        task_8              Запустить Task 8 (Finances)
        report              Показать отчёт затрат
        help                Показать эту справку

    ПРИМЕРЫ:
        python3 run_all.py all          # Запустить всё
        python3 run_all.py task_5       # Только обучение
        python3 run_all.py report       # Посмотреть затраты
    """)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "all":
        run_all_tasks()
    elif command == "task_1":
        show_welcome()
        run_task_1()
        tracker.daily_report()
    elif command == "task_2":
        show_welcome()
        run_task_2()
        tracker.daily_report()
    elif command == "task_3":
        show_welcome()
        run_task_3()
        tracker.daily_report()
    elif command == "task_4":
        show_welcome()
        run_task_4()
        tracker.daily_report()
    elif command == "task_5":
        show_welcome()
        run_task_5()
        tracker.daily_report()
    elif command == "task_6":
        show_welcome()
        run_task_6()
        tracker.daily_report()
    elif command == "task_7":
        show_welcome()
        run_task_7()
        tracker.daily_report()
    elif command == "task_8":
        show_welcome()
        run_task_8()
        tracker.daily_report()
    elif command == "report":
        show_welcome()
        tracker.daily_report()
        tracker.monthly_summary()
    elif command == "help":
        show_help()
    else:
        print(f"❌ Неизвестная команда: {command}\n")
        show_help()
