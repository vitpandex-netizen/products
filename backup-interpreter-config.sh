#!/bin/zsh
BACKUP_DIR="/Volumes/External/dev/.backups/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

cp /Users/vitaliyr/Library/Application\ Support/Interpreter/config.json "$BACKUP_DIR/config.json"
cp /Users/vitaliyr/Library/Application\ Support/interpreter/codex-home/memories/MEMORY.md "$BACKUP_DIR/MEMORY.md"
cp /Users/vitaliyr/Library/Application\ Support/interpreter/codex-home/memories/memory_summary.md "$BACKUP_DIR/memory_summary.md"
cp /Users/vitaliyr/Library/Application\ Support/Interpreter/browser-tabs.json "$BACKUP_DIR/browser-tabs.json" 2>/dev/null
cp /Volumes/External/dev/PROJECTS.md "$BACKUP_DIR/PROJECTS.md" 2>/dev/null

# Keep last 14 days, remove older
find /Volumes/External/dev/.backups -maxdepth 1 -type d -mtime +14 -exec rm -rf {} \; 2>/dev/null

echo "[$(date)] Backup done" >> /Volumes/External/dev/.backups/backup-log.txt
