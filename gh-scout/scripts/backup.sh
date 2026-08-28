#!/bin/bash
# GH Scout — Backup System v1.0
# Авто-бэкап всех баз данных на US Server
# Запуск: bash backup.sh
# Cron: 0 3 * * * bash /home/us/scripts/backup.sh

set -e

BACKUP_DIR="/home/us/backups"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$BACKUP_DIR/backup.log"

mkdir -p "$BACKUP_DIR"/{pg,data,config}
mkdir -p "$BACKUP_DIR/daily/$(date +%Y%m%d)"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Backup started ==="

# ─── 1. PostgreSQL базы ───

backup_pg() {
    local container=$1
    local db_name=$2
    local output="$BACKUP_DIR/pg/${db_name}_${TIMESTAMP}.sql.gz"
    
    log "Backing up PostgreSQL: $container / $db_name"
    docker exec "$container" pg_dump -U "$db_name" -d "$db_name" 2>/dev/null | gzip > "$output"
    
    if [ -s "$output" ]; then
        local size=$(du -h "$output" | cut -f1)
        log "  ✅ $db_name → $output ($size)"
        # Copy to daily
        cp "$output" "$BACKUP_DIR/daily/$(date +%Y%m%d)/"
    else
        log "  ❌ $db_name — backup failed or empty"
        rm -f "$output"
    fi
}

# Detect and backup all PostgreSQL databases
log "Detecting PostgreSQL containers..."
PG_CONTAINERS=$(docker ps --format '{{.Names}}' | grep -E 'pg|postgres')

if [ -z "$PG_CONTAINERS" ]; then
    log "  No PostgreSQL containers found"
else
    for container in $PG_CONTAINERS; do
        case "$container" in
            datacore-pg)    backup_pg "$container" "datacore" ;;
            ghscout-pg)     backup_pg "$container" "ghscout" ;;
            anyidea-pg)     backup_pg "$container" "anyidea" ;;
            consilium-postgres) backup_pg "$container" "consilium" ;;
            *)              
                # Try to detect database name
                db_name=$(docker inspect "$container" --format '{{range .Config.Env}}{{if eq "POSTGRES_DB" (slice . 0 11)}}{{slice . 12}}{{end}}{{end}}' 2>/dev/null)
                if [ -n "$db_name" ]; then
                    backup_pg "$container" "$db_name"
                else
                    log "  ⏭️  $container — unknown DB, skipping"
                fi
                ;;
        esac
    done
fi

# ─── 2. Context DB (SQLite) ───

log "Backing up Context DB..."
if docker exec context-db test -f /app/data/context.db 2>/dev/null; then
    docker cp context-db:/app/data/context.db "$BACKUP_DIR/data/context_${TIMESTAMP}.db"
    gzip "$BACKUP_DIR/data/context_${TIMESTAMP}.db"
    log "  ✅ context-db → $BACKUP_DIR/data/context_${TIMESTAMP}.db.gz"
else
    log "  ⏭️  context-db not found"
fi

# ─── 3. Конфиги ───

log "Backing up configs..."
tar czf "$BACKUP_DIR/config/configs_${TIMESTAMP}.tar.gz" \
    /home/us/.env* \
    /home/us/datacore/.env \
    /home/us/dev/gh-scout/.env \
    /home/us/dev/anyidea/.env \
    2>/dev/null || log "  ⏭️  some configs not found"

# ─── 4. Docker volumes (метаданные) ───

log "Backing up Docker metadata..."
docker ps --format '{{.Names}} {{.Image}} {{.Status}}' > "$BACKUP_DIR/data/containers_${TIMESTAMP}.txt"
docker volume ls > "$BACKUP_DIR/data/volumes_${TIMESTAMP}.txt"
log "  ✅ Container list saved"

# ─── 5. Ротация (удаление старых бэкапов) ───

log "Rotating backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR/pg" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR/data" -name "*.db.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR/config" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR/daily" -maxdepth 1 -type d -mtime +$RETENTION_DAYS -exec rm -rf {} +
log "  ✅ Old backups cleaned"

# ─── 6. Итог ───

TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
BACKUP_COUNT=$(find "$BACKUP_DIR/pg" -name "*.sql.gz" | wc -l)

log "=== Backup complete ==="
log "  Directory: $BACKUP_DIR"
log "  DB backups: $BACKUP_COUNT"
log "  Total size: $TOTAL_SIZE"
log "  Retention: $RETENTION_DAYS days"
echo ""
echo "📊 Backup Summary"
echo "  Size: $TOTAL_SIZE"
echo "  DBs: $BACKUP_COUNT"
echo "  Location: $BACKUP_DIR"