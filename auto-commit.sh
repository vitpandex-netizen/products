#!/bin/zsh
# Auto-commit: git add + commit с сообщением
# Использование: ./auto-commit.sh "что сделано"

PROJECT="${1:-.}"
MSG="${2:-auto-update}"
cd "$PROJECT" 2>/dev/null || { echo "❌ Проект не найден: $PROJECT"; exit 1; }

# Проверяем, что это git репозиторий
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "⏭️ Не git репозиторий"
    exit 0
fi

# Проверяем, есть ли изменения
if git diff --quiet && git diff --cached --quiet; then
    echo "ℹ️ Нет изменений"
    exit 0
fi

# Показываем diff
echo "📝 Изменения:"
git diff --stat

# Коммитим
git add -A
git commit -m "$MSG" --no-verify 2>&1
echo "✅ Закоммичено: $MSG"
