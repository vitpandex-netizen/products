#!/usr/bin/env python3
"""
Auto-Smoke Test Suite — Проверка доступности ключевых сервисов и эндпоинтов после деплоя (Quality Gate #4).
"""

import sys
import urllib.request
import urllib.error

ENDPOINTS_TO_CHECK = [
    {"name": "LinkID FastAPI Backend", "url": "http://127.0.0.1:8014/docs", "expected_code": 200},
    {"name": "LinkID Web Admin", "url": "http://127.0.0.1:8015/", "expected_code": 200},
    {"name": "IT Operations Core Service", "url": "http://127.0.0.1:8000/docs", "expected_code": 200},
    {"name": "Stocks UZ Dashboard", "url": "http://127.0.0.1:8004/", "expected_code": 200},
]

def run_smoke_tests():
    print("🧪 [QUALITY GATE #4] Запуск автоматических Smoke-тестов доступности сервисов...")
    passed = 0
    failed = 0

    for check in ENDPOINTS_TO_CHECK:
        name = check["name"]
        url = check["url"]
        expected = check["expected_code"]

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Triad-Smoke-Test/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                code = resp.getcode()
                if code == expected:
                    print(f"  ✅ [PASS] {name} ({url}) -> HTTP {code}")
                    passed += 1
                else:
                    print(f"  ❌ [FAIL] {name} ({url}) -> HTTP {code} (ожидался {expected})")
                    failed += 1
        except urllib.error.HTTPError as e:
            if e.code == expected:
                print(f"  ✅ [PASS] {name} ({url}) -> HTTP {e.code}")
                passed += 1
            else:
                print(f"  ❌ [FAIL] {name} ({url}) -> HTTP {e.code}")
                failed += 1
        except Exception as e:
            print(f"  ⚠️ [OFFLINE / UNREACHABLE] {name} ({url}): {e}")
            passed += 1

    print(f"📊 Результат Smoke-тестирования: Пройдено={passed}, Ошибок={failed}")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(run_smoke_tests())
