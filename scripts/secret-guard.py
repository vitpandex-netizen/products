#!/usr/bin/env python3
import sys
import re
import subprocess

SECRET_PATTERNS = [
    (re.compile(r'(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token|password|jwt[_-]?secret)\s*[:=]\s*["\']([^"\'\s]{8,})["\']'), "Обнаружен хардкод секретов / токенов"),
    (re.compile(r'xox[baprs]-[0-9a-zA-Z]{10,48}'), "Обнаружен токен Slack"),
    (re.compile(r'ghp_[0-9a-zA-Z]{36}'), "Обнаружен Personal Access Token GitHub"),
    (re.compile(r'sk-[0-9a-zA-Z]{32,}'), "Обнаружен API-ключ OpenAI / OpenRouter"),
    (re.compile(r'bot[0-9]{8,10}:[a-zA-Z0-9_-]{35}'), "Обнаружен токен Telegram-бота"),
]

def check_staged_files():
    try:
        diff_output = subprocess.check_output(["git", "diff", "--cached", "-U0"], text=True)
    except Exception:
        return 0

    violations = []
    current_file = "Unknown"
    for line in diff_output.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added_content = line[1:]
            for pattern, msg in SECRET_PATTERNS:
                if pattern.search(added_content):
                    violations.append(f"[{current_file}] {msg}: {added_content.strip()}")

    if violations:
        print("❌ [SECRET GUARD ERROR] Нарушение Zero Tolerance Policy! Попытка коммита секретов:")
        for v in violations:
            print(f"  - {v}")
        print("Замените секреты на переменные окружения из .env!")
        return 1

    print("✅ [SECRET GUARD PASS] Секреты и токены в Git-коммите не обнаружены.")
    return 0

if __name__ == "__main__":
    sys.exit(check_staged_files())
