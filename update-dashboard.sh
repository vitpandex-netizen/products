#!/bin/zsh
# Ежедневное обновление Project Dashboard
# Запускается в 17:00 через launchd

LOG="/Volumes/External/dev/project-dashboard/daily-update.log"
echo "[$(date)] === Daily Dashboard Update ===" >> "$LOG"

# 1. Обновить дашборд (перезапустить, чтобы подхватить новый код)
pm2 restart project-dashboard 2>&1 >> "$LOG"
echo "  ✅ pm2 restart" >> "$LOG"

# 2. Проверить что отвечает
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/ 2>/dev/null)
echo "  HTTP $STATUS" >> "$LOG"

# 3. Проверить git-статусы проектов и записать
echo "  --- Git status ---" >> "$LOG"
for d in /Volumes/External/dev/*/; do
  name=$(basename "$d")
  [ "$name" = ".backups" ] && continue
  if [ -d "$d/.git" ]; then
    dirty=$(cd "$d" 2>/dev/null && git status --short 2>/dev/null | wc -l | tr -d ' ')
    [ "$dirty" -gt 0 ] && echo "  ⚠️ $name: $dirty dirty" >> "$LOG"
  fi
done

# 4. Проверить pm2 процессы
echo "  --- pm2 ---" >> "$LOG"
pm2 list 2>/dev/null | grep -E 'online|errored' >> "$LOG"

# 5. Проверить launchd
echo "  --- launchd ---" >> "$LOG"
launchctl list | grep com.vitaliyr >> "$LOG"

# 6. Проверить бэкап
echo "  --- Backup ---" >> "$LOG"
ls -1t /Volumes/External/dev/.backups/ 2>/dev/null | head -3 >> "$LOG"

echo "[$(date)] === Done ===" >> "$LOG"
echo "" >> "$LOG"
