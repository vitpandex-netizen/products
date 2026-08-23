#!/usr/bin/env python3
"""System Change Log — CLI для записи изменений из терминала/cron.

Использование:
    python cli.py --author hermes --project datacore --type feature \\
        --summary "Добавлен Tool Calling шлюз" \\
        --reason "Нужен ad-hoc SQL-доступ для аналитики" \\
        --status completed

    # Сокращённая форма
    python cli.py -a hermes -p datacore -t feature -s "..." -r "..." --status in_progress
"""

import argparse
import json
import os
import sys

import httpx

API_URL = os.getenv("CHANGELOG_API_URL", "http://100.84.223.96:8300")

VALID_TYPES = ["feature", "fix", "config", "deploy", "infra", "decision"]
VALID_STATUSES = ["planned", "in_progress", "completed", "rolled_back", "failed"]
VALID_IMPACTS = ["system", "service", "user", "all"]


def main():
    parser = argparse.ArgumentParser(description="Записать изменение в System Change Log")
    parser.add_argument("-a", "--author", default="hermes", help="Кто сделал")
    parser.add_argument("-p", "--project", required=True, help="Проект")
    parser.add_argument("-t", "--type", required=True, choices=VALID_TYPES, help="Тип изменения")
    parser.add_argument("-s", "--summary", required=True, help="Краткое описание")
    parser.add_argument("-d", "--description", default="", help="Подробное описание")
    parser.add_argument("-r", "--reason", default="", help="Причина изменения")
    parser.add_argument("--impact", default="service", choices=VALID_IMPACTS, help="Зона влияния")
    parser.add_argument("--status", default="completed", choices=VALID_STATUSES, help="Статус")
    parser.add_argument("--links", default="[]", help='JSON-массив ссылок')
    parser.add_argument("--source", default="cli", help="Источник")
    parser.add_argument("--dry-run", action="store_true", help="Показать что будет отправлено")

    args = parser.parse_args()

    payload = {
        "author": args.author,
        "project": args.project,
        "change_type": args.type,
        "summary": args.summary,
        "description": args.description,
        "reason": args.reason,
        "impact": args.impact,
        "status": args.status,
        "links": args.links,
        "source": args.source,
    }

    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print(f"\n→ POST {API_URL}/changes")
        return

    try:
        resp = httpx.post(f"{API_URL}/changes", json=payload, timeout=10.0)
        resp.raise_for_status()
        result = resp.json()
        print(f"✅ Изменение зафиксировано: {result['id']}")
        print(f"   {result['summary']}")
        print(f"   {API_URL}/changes/{result['id']}")
    except httpx.HTTPError as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()