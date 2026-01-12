# Database Health & Corruption Prevention Guide

## Overview
This document outlines the measures in place to prevent and handle database corruption on the production VPS2 server.

## Preventive Measures (Implemented)

### 1. WAL Mode (Write-Ahead Logging)
- **Status**: Enabled on VPS2
- **Benefit**: More resilient to corruption, better concurrency
- **Location**: `/opt/myhealthteam/production.db`
- **Verification**: `sqlite3 /opt/myhealthteam/production.db 'PRAGMA journal_mode;'` should return `wal`

### 2. Automated Health Checks
- **Script**: `/opt/myhealthteam/scripts/db_health_check.sh`
- **Schedule**: Every 30 minutes via cron
- **Actions**:
  - Runs `PRAGMA integrity_check`
  - Checks database file size
  - Creates daily backups
  - Runs WAL checkpoint
  - Creates alert flag if corruption detected

### 3. Automated Backups
- **Location**: `/opt/myhealthteam/backups/`
- **Retention**: 14 days of daily backups
- **Naming**: `production_daily_YYYYMMDD.db`

### 4. Alert Flags
- **Location**: `/opt/myhealthteam/flags/db_corruption_detected.flag`
- **Action**: Created automatically when corruption is detected

## Monitoring Commands

### Check Database Health
```bash
ssh server2 "sqlite3 /opt/myhealthteam/production.db 'PRAGMA integrity_check;'"
```

### Check WAL Mode
```bash
ssh server2 "sqlite3 /opt/myhealthteam/production.db 'PRAGMA journal_mode;'"
```

### View Health Logs
```bash
ssh server2 "tail -50 /opt/myhealthteam/logs/db_health.log"
```

### Check for Alert Flags
```bash
ssh server2 "ls -la /opt/myhealthteam/flags/db_corruption_detected.flag"
```

### List Recent Backups
```bash
ssh server2 "ls -la /opt/myhealthteam/backups/production_daily_*.db | tail -7"
```

## Recovery Procedures

### If Corruption is Detected

1. **Stop Streamlit**
   ```bash
   ssh server2 "killall streamlit"
   ```

2. **Check Health Log for Details**
   ```bash
   ssh server2 "cat /opt/myhealthteam/logs/db_health.log | tail -50"
   ```

3. **Identify Last Good Backup**
   ```bash
   ssh server2 "ls -lat /opt/myhealthteam/backups/production_daily_*.db | head -1"
   ```

4. **Restore from Backup**
   ```bash
   ssh server2 "
   cp /opt/myhealthteam/production.db /opt/myhealthteam/production.db.corrupted_before_restore
   cp /opt/myhealthteam/backups/production_daily_YYYYMMDD.db /opt/myhealthteam/production.db
   "
   ```

5. **Verify Restored Database**
   ```bash
   ssh server2 "sqlite3 /opt/myhealthteam/production.db 'PRAGMA integrity_check;'"
   ```

6. **Restart Streamlit**
   ```bash
   ssh server2 "
   cd /opt/myhealthteam
   nohup /opt/myhealthteam/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0 > /tmp/streamlit.log 2>&1 &
   "
   ```

### Attempting Data Recovery from Corrupted DB

If you need to recover data from the corrupted database:

1. **Try to dump recoverable data**
   ```bash
   ssh server2 "
   sqlite3 /opt/myhealthteam/production.db.corrupted '.dump' > /tmp/recovery_dump.sql
   "
   ```

2. **Import into new database**
   ```bash
   ssh server2 "
   sqlite3 /opt/myhealthteam/production_recovered.db < /tmp/recovery_dump.sql
   "
   ```

3. **Verify recovered data**
   ```bash
   ssh server2 "
   sqlite3 /opt/myhealthteam/production_recovered.db 'PRAGMA integrity_check;'
   "
   ```

## Root Cause Analysis

The corruption on Jan 9, 2026 was caused by:
- **Journal mode was `delete`** (default, less resilient)
- **No automated integrity checks** running
- **No WAL mode** enabled

Since then, the following have been implemented:
- ✅ WAL mode enabled
- ✅ Health checks every 30 minutes
- ✅ Daily automated backups
- ✅ Alert system for corruption detection

## Emergency Contacts

If corruption is detected and recovery is needed:
1. Check this document for recovery procedures
2. Review health logs: `/opt/myhealthteam/logs/db_health.log`
3. Use backups in: `/opt/myhealthteam/backups/`

## Cron Jobs

```bash
# View all cron jobs
crontab -l

# Current job for health checks:
*/30 * * * * /opt/myhealthteam/scripts/db_health_check.sh > /dev/null 2>&1
```

## Files and Locations

| Purpose | Path |
|---------|------|
| Production Database | `/opt/myhealthteam/production.db` |
| Health Check Script | `/opt/myhealthteam/scripts/db_health_check.sh` |
| Backups | `/opt/myhealthteam/backups/` |
| Health Logs | `/opt/myhealthteam/logs/db_health.log` |
| Alert Flags | `/opt/myhealthteam/flags/db_corruption_detected.flag` |
| Streamlit Logs | `/tmp/streamlit.log` |

## Maintenance Tasks

### Weekly
- Review health logs for any warnings
- Verify backup files are being created

### Monthly
- Test restore procedure from a backup
- Review and clean old logs if needed

### As Needed
- Monitor disk space (backups will accumulate 14 days of data)
- Update retention policy if needed (edit `MAX_BACKUPS` in health check script)
