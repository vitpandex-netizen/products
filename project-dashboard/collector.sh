#!/bin/zsh
# Metrics Collector — самодостаточная версия
export PATH="/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:/Users/vitaliyr/.local/bin:$PATH"

DATA_DIR="/Volumes/External/dev/project-dashboard/data"
mkdir -p "$DATA_DIR" || exit 1
TS=$(date +%Y-%m-%dT%H:%M:%S%z)
LOG="$DATA_DIR/metrics.jsonl"

# 1. Git dirty count
DIRTY=0; CLEAN=0; NOGIT=0
for d in /Volumes/External/dev/*/; do
  name=$(basename "$d")
  [ "$name" = ".backups" ] || [ "$name" = "project-dashboard" ] && continue
  if [ -d "$d/.git" ]; then
    c=$(cd "$d" && git status --short 2>/dev/null | wc -l | tr -d ' ')
    [ "$c" -gt 0 ] && DIRTY=$((DIRTY+1)) || CLEAN=$((CLEAN+1))
  else
    NOGIT=$((NOGIT+1))
  fi
done

# 2. CPU — safer version
CPU=$(ps -A -o %cpu 2>/dev/null | awk '{s+=$1} END {printf "%.1f", s}' 2>/dev/null || echo 0)

# 3. Disk
DISK_PCT=$(df -h / 2>/dev/null | tail -1 | awk '{print $5}' | tr -d '%' 2>/dev/null || echo 0)
DISK_USED=$(df -h / 2>/dev/null | tail -1 | awk '{print $3}' 2>/dev/null || echo '?')
DISK_TOTAL=$(df -h / 2>/dev/null | tail -1 | awk '{print $2}' 2>/dev/null || echo '?')

# 4. pm2 — count online
PM2_ONLINE=$(pm2 list 2>/dev/null | grep -c 'online' || echo 0)

# 5. Backup age
BACKUP_AGE=999
LAST_BACKUP=$(ls -1t /Volumes/External/dev/.backups/ 2>/dev/null | head -1)
if [ -n "$LAST_BACKUP" ]; then
  BACKUP_TS=$(stat -f "%m" "/Volumes/External/dev/.backups/$LAST_BACKUP" 2>/dev/null || echo 0)
  NOW_TS=$(date +%s)
  [ "$BACKUP_TS" -gt 0 ] && BACKUP_AGE=$(( (NOW_TS - BACKUP_TS) / 3600 ))
fi

# 6. Uptime
UPTIME=$(uptime | awk -F"up " '{print $2}' | awk -F"," '{print $1}' 2>/dev/null || echo '?')

echo '{"ts":"'"$TS"'","dirty":'"$DIRTY"',"clean":'"$CLEAN"',"nogit":'"$NOGIT"',"cpu":'"$CPU"',"disk_pct":'"$DISK_PCT"',"disk_used":"'"$DISK_USED"'","disk_total":"'"$DISK_TOTAL"'","pm2_online":'"$PM2_ONLINE"',"backup_age":'"$BACKUP_AGE"',"uptime":"'"$UPTIME"'"}' >> "$LOG"

# Keep last 30 days
tail -n 1440 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG" 2>/dev/null

echo "[$TS] ok dirty=$DIRTY clean=$CLEAN cpu=$CPU disk=$DISK_PCT% pm2=$PM2_ONLINE"
