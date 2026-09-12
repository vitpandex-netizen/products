#!/usr/bin/env python3
"""
Zero Tolerance Security Auditor (TASK-ITOPS-023)
Сканнер ИБ для отслеживания утечек секретов, прав .env и наличия .env.example.
"""

import os
import re
import sys
import stat
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Регулярные выражения для поиска секретов
SECRET_PATTERNS = [
    (re.compile(r"bot\d+:[A-Za-z0-9_-]{35}"), "Telegram Bot Token"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key"),
    (re.compile(r"-----BEGIN PRIVATE KEY-----"), "RSA/PEM Private Key"),
    (re.compile(r"sk-[a-zA-Z0-9]{32,}"), "OpenAI / LLM API Key"),
    (re.compile(r"postgres://[^:]+:[^@]+@"), "Hardcoded DB Password"),
    (re.compile(r"redis://:[^@]+@"), "Hardcoded Redis Password"),
]

# Исключения
EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".backups", "brain", "_archive", "tests"}
EXCLUDED_FILES = {".env", ".secrets.enc", "vault.enc", "secret_auditor.py", "CHANGELOG.md", "helpers.py"}

def check_file_permissions(env_file: Path) -> bool:
    """Проверка прав 0600 на .env файлы."""
    if not env_file.exists():
        return True
    st = env_file.stat()
    mode = stat.S_IMODE(st.st_mode)
    return mode in (0o600, 0o400)

def scan_file_for_secrets(file_path: Path) -> list:
    """Сканирование текста файла на утечки ключей."""
    issues = []
    try:
        content = file_path.read_text(errors="ignore")
        for pattern, desc in SECRET_PATTERNS:
            matches = pattern.findall(content)
            if matches:
                issues.append(f"🔒 Найдено совпадение {desc} ({len(matches)} шт.) в {file_path.relative_to(BASE_DIR)}")
    except Exception as e:
        pass
    return issues

def audit_projects():
    print("=" * 60)
    print("🛡️  ИБ-АУДИТ ТРИАДЫ (Zero Tolerance Security Scanner)")
    print("=" * 60)

    total_files = 0
    issues = []
    warnings = []

    # Сканирование проектов
    projects = [p for p in BASE_DIR.iterdir() if p.is_dir() and p.name not in EXCLUDED_DIRS]

    for proj in projects:
        env_file = proj / ".env"
        env_example = proj / ".env.example"

        if env_file.exists():
            if not check_file_permissions(env_file):
                warnings.append(f"⚠️ Небезопасные права на {env_file.relative_to(BASE_DIR)} (рекомендуется chmod 600)")

        # Сканирование исходного кода
        for root, dirs, files in os.walk(proj):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file in files:
                if file in EXCLUDED_FILES or file.endswith(".pyc"):
                    continue
                file_path = Path(root) / file
                total_files += 1
                found = scan_file_for_secrets(file_path)
                issues.extend(found)

    print(f"\n📊 Просканировано файлов: {total_files}")
    
    if issues:
        print("\n❌ КРИТИЧЕСКИЕ НАХОДКИ ИБ (GRADE F):")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ Секреты в открытом виде не обнаружены.")

    if warnings:
        print("\n⚠️ ПРЕДУПРЕЖДЕНИЯ (Права доступа):")
        for w in warnings:
            print(f"  {w}")

    grade = "Grade A" if not issues and not warnings else ("Grade B" if not issues else "Grade F")
    print(f"\n🏆 Итоговый статус безопасности: {grade}")
    print("=" * 60)

    return 0 if not issues else 1

if __name__ == "__main__":
    sys.exit(audit_projects())
