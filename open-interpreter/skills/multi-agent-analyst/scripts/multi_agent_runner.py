#!/usr/bin/env python3
"""
Multi-Agent Runner — template for parallel agent spawning with shared context.

Read this before writing agent spawn code. Adapt for your specific task.

Usage: spawn_agent(agent_type="worker", message=task_msg, fork_context=True)
"""

# ─── Шаг 1: Общий system prompt ───
COMMON_SYSTEM = """
Ты аналитик. Отвечай ТОЛЬКО валидным JSON.
Никакого markdown, никаких объяснений, никаких code blocks.

Schema:
{
    "confidence": 0.0-1.0,
    "findings": ["string"],
    "sources": ["string"],
    "recommendation": "string"
}
"""

# ─── Шаг 2: Декомпозиция задачи ───
# Разбей запрос пользователя на независимые подзадачи
# Каждая должна быть решаема отдельно

tasks = [
    "Task: Analyze stock AAPL — price trends, news, analyst ratings",
    "Task: Latest tech news — AI, cloud, semiconductor",
    "Task: DevOps job market — requirements, salaries, demand"
]

# ─── Шаг 3: Запуск параллельных агентов ───
# for task in tasks:
#     spawn_agent(
#         agent_type="worker",
#         message=task,
#         fork_context=True  # ← наследует весь контекст (включая COMMON_SYSTEM)
#     )

# ─── Шаг 4: Сбор и фильтрация ───
def process_results(results):
    strong = []
    weak = []
    skipped = 0

    for r in results:
        conf = r.get("confidence", 0)
        if conf >= 0.7:
            strong.append(r)
        elif conf >= 0.4:
            weak.append({**r, "flagged": "low_confidence"})
        else:
            skipped += 1

    return {
        "strong": strong,
        "caveats": weak,
        "skipped": skipped,
        "total": len(results),
        "summary": (
            f"{len(strong)} strong signals, "
            f"{len(weak)} with caveats, "
            f"{skipped} skipped"
        )
    }


if __name__ == "__main__":
    print("Multi-Agent Runner Template")
    print("=" * 40)
    print(f"Shared system prompt: {len(COMMON_SYSTEM)} chars")
    print(f"Tasks to spawn: {len(tasks)}")
    print(f"\nTasks:")
    for i, t in enumerate(tasks, 1):
        print(f"  {i}. {t}")
    print(f"\nRun with spawn_agent(fork_context=True, agent_type='worker')")
