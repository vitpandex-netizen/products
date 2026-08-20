#!/bin/zsh
# Auto-verify: проверяет проект после изменений
# Использование: ./auto-verify.sh <project-path>

PROJECT="${1:-.}"
cd "$PROJECT" 2>/dev/null || { echo "❌ Проект не найден"; exit 1; }

echo "🔍 Auto-verify: $(basename $(pwd))"
echo "================================"

# 1. Git статус
if [ -d .git ]; then
    echo ""
    echo "📝 Git status:"
    git status --short 2>/dev/null | head -20
fi

# 2. Синтаксис Python
PY_FILES=$(find . -name "*.py" -maxdepth 3 2>/dev/null | head -10)
if [ -n "$PY_FILES" ]; then
    echo ""
    echo "🐍 Python syntax check:"
    for f in $PY_FILES; do
        python3 -m py_compile "$f" 2>&1 && echo "  ✅ $f" || echo "  ❌ $f — SYNTAX ERROR"
    done
fi

# 3. JSON валидация
JSON_FILES=$(find . -name "*.json" -maxdepth 2 2>/dev/null | head -5)
if [ -n "$JSON_FILES" ]; then
    echo ""
    echo "📦 JSON validation:"
    for f in $JSON_FILES; do
        python3 -m json.tool "$f" > /dev/null 2>&1 && echo "  ✅ $f" || echo "  ❌ $f — INVALID JSON"
    done
fi

# 4. Размер файлов — предупреждение о больших
echo ""
echo "📏 Large files (>100KB):"
find . -type f -size +100k -maxdepth 3 2>/dev/null | head -10

echo ""
echo "✅ Done"
