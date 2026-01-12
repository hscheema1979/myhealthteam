#!/bin/bash
# Database Health Check Script for VPS2
# Run via cron: */30 * * * * /opt/myhealthteam/scripts/db_health_check.sh

DB_PATH="/opt/myhealthteam/production.db"
BACKUP_DIR="/opt/myhealthteam/backups"
LOG_FILE="/opt/myhealthteam/logs/db_health.log"
ALERT_FILE="/opt/myhealthteam/flags/db_corruption_detected.flag"
MAX_BACKUPS=14  # Keep 14 days of backups

# Ensure directories exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname $LOG_FILE)"
mkdir -p "$(dirname $ALERT_FILE)"

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log "=== Starting database health check ==="

# 1. Integrity check
log "Running integrity check..."
INTEGRITY_RESULT=$(sqlite3 "$DB_PATH" 'PRAGMA integrity_check;' 2>&1)
if [ "$INTEGRITY_RESULT" != "ok" ]; then
    log "ERROR: Database corruption detected!"
    log "$INTEGRITY_RESULT"

    # Create alert flag
    echo "$(date '+%Y-%m-%d %H:%M:%S')" > "$ALERT_FILE"

    # Create emergency backup
    cp "$DB_PATH" "$BACKUP_DIR/emergency_corruption_$(date +%Y%m%d_%H%M%S).db"
    log "Emergency backup created"

    # Exit with error code
    exit 1
fi
log "Integrity check: OK"

# 2. Check file size (detect zero-sized or truncated files)
FILE_SIZE=$(stat -f%z "$DB_PATH" 2>/dev/null || stat -c%s "$DB_PATH" 2>/dev/null)
if [ "$FILE_SIZE" -lt 1000000 ]; then
    log "WARNING: Database file suspiciously small ($FILE_SIZE bytes)"
    echo "$(date '+%Y-%m-%d %H:%M:%S')" > "$ALERT_FILE"
    exit 1
fi
log "File size: $FILE_SIZE bytes"

# 3. Daily backup (only once per day)
TODAY_BACKUP="$BACKUP_DIR/production_daily_$(date +%Y%m%d).db"
if [ ! -f "$TODAY_BACKUP" ]; then
    log "Creating daily backup..."
    cp "$DB_PATH" "$TODAY_BACKUP"

    # Clean old backups (keep $MAX_BACKUPS days)
    ls -t "$BACKUP_DIR"/production_daily_*.db 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm
    log "Old backups cleaned (keeping $MAX_BACKUPS days)"
else
    log "Daily backup already exists for today"
fi

# 4. WAL checkpoint (keep WAL file size manageable)
log "Running WAL checkpoint..."
sqlite3 "$DB_PATH" 'PRAGMA wal_checkpoint(TRUNCATE);' 2>/dev/null

# 5. Report stats
PAGE_COUNT=$(sqlite3 "$DB_PATH" 'PRAGMA page_count;')
FREE_PAGES=$(sqlite3 "$DB_PATH" 'PRAGMA freelist_count;')
log "Pages: $PAGE_COUNT, Free: $FREE_PAGES"

log "=== Health check completed ==="
exit 0
