#!/bin/zsh
# Quick status всех проектов
# Использование: ./quick-status.sh [project-name]

echo "╔════════════════════════════════════════════════╗"
echo "║     📊 Project Status Dashboard               ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

if [ -n "$1" ]; then
    # Статус одного проекта
    PROJECT="/Volumes/External/dev/$1"
    if [ ! -d "$PROJECT" ]; then
        echo "❌ Проект не найден: $1"
        exit 1
    fi
    echo "📁 $1"
    echo "──────────────────────────────"
    
    # Git статус
    if [ -d "$PROJECT/.git" ]; then
        cd "$PROJECT"
        echo "  Git: $(git branch --show-current 2>/dev/null)"
        UNCOMMITTED=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
        [ "$UNCOMMITTED" -gt 0 ] && echo "  ⚠️ $UNCOMMITTED незакоммиченных файлов" || echo "  ✅ Чисто"
        echo "  Последний коммит: $(git log -1 --format='%ar' 2>/dev/null)"
    fi
    
    # .interpreter-rules
    [ -f "$PROJECT/.interpreter-rules" ] && echo "  ✅ .interpreter-rules" || echo "  ⚠️ Нет .interpreter-rules"
    
    # Размер
    SIZE=$(du -sh "$PROJECT" 2>/dev/null | cut -f1)
    echo "  Размер: $SIZE"
else
    # Статус всех проектов
    for project in /Volumes/External/dev/*/; do
        name=$(basename "$project")
        [ "$name" = "backups" ] || [ "$name" = ".backups" ] && continue
        
        echo "📁 $name"
        
        if [ -d "$project/.git" ]; then
            cd "$project" 2>/dev/null
            BRANCH=$(git branch --show-current 2>/dev/null)
            UNCOMMITTED=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
            LAST=$(git log -1 --format='%ar' 2>/dev/null)
            echo "  ├─ Ветка: $BRANCH"
            [ "$UNCOMMITTED" -gt 0 ] && echo "  ├─ ⚠️ $UNCOMMITTED файлов не закоммичено" || echo "  ├─ ✅ Чисто"
            echo "  └─ Последний коммит: $LAST"
        else
            echo "  └─ ⚠️ Не git репозиторий"
        fi
        echo ""
    done
fi
