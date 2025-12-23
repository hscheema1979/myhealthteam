# Daily Sync Schedule

**Effective:** Replaces the previous 15-minute sync interval

## Overview

The system now performs a daily data synchronization cycle optimized for data freshness and production stability:

1. **5:00 AM** - Download latest data and import locally
2. **6:30 AM** - Sync refreshed data to Server 2 production

This 1.5-hour window allows the import process to complete before pushing to production.

## Schedule Details

### Task 1: Daily-Data-Refresh (5:00 AM)

**Script:** `refresh_production_data.ps1`

**What it does:**

- Backs up current `production.db`
- Downloads latest healthcare data CSVs from Google Sheets
- Transforms and imports CSV data into local `production.db`
- Runs post-import processing (views, patient updates, summaries)
- Triggers sync to production (via `-SyncToProduction` flag)

**Command:**

```powershell
.\refresh_production_data.ps1 -SkipBackup -SyncToProduction
```

**Logs:** `db-sync/logs/`

**Trigger:** Daily at 5:00 AM Pacific Time

---

### Task 2: Daily-DB-Sync (6:30 AM)

**Script:** `db-sync/bin/sync_csv_data.ps1`

**What it does:**

- Connects to Server 2 via SSH
- Exports CSV_IMPORT rows from local task tables (current month)
- Uploads and executes import on Server 2's production.db
- Preserves MANUAL, DASHBOARD, and WORKFLOW entries on production
- Cleans up temporary files and removes trigger flags

**Purpose:** Push refreshed CSV data to production Server 2

**Logs:** `db-sync/logs/csv_sync_*.log`

**Trigger:** Daily at 6:30 AM Pacific Time

---

## Key Differences from Previous 15-Minute Schedule

| Aspect         | Old (15-min)              | New (Daily)                   |
| -------------- | ------------------------- | ----------------------------- |
| Frequency      | Every 15 minutes          | Once per day                  |
| Data freshness | Latest from Server 2      | Latest CSVs imported fresh    |
| Server load    | Continuous, high overhead | Single cycle during off-hours |
| Sync direction | Pull from prod (master)   | Push (after import)           |
| Impact         | Frequent interruptions    | Predictable, scheduled        |

---

## Managing the Tasks

### View Task Status

```powershell
Get-ScheduledTask -TaskName "Daily-Data-Refresh"
Get-ScheduledTask -TaskName "Daily-DB-Sync"
```

### Run Tasks Manually

```powershell
# Run refresh now
Start-ScheduledTask -TaskName "Daily-Data-Refresh"

# Or run refresh script directly
.\refresh_production_data.ps1 -SkipBackup -SyncToProduction

# Run sync now
Start-ScheduledTask -TaskName "Daily-DB-Sync"

# Or run sync script directly
.\db-sync\bin\sync_csv_data.ps1
```

### Disable/Enable Tasks

```powershell
# Disable a task (won't run automatically)
Disable-ScheduledTask -TaskName "Daily-Data-Refresh"

# Enable it again
Enable-ScheduledTask -TaskName "Daily-Data-Refresh"
```

### Remove/Recreate Tasks

```powershell
# Remove both tasks
Unregister-ScheduledTask -TaskName "Daily-Data-Refresh" -Confirm:$false
Unregister-ScheduledTask -TaskName "Daily-DB-Sync" -Confirm:$false

# Recreate them
.\db-sync\bin\setup_daily_tasks.ps1
```

---

## Troubleshooting

### Tasks Not Running

1. **Check if tasks exist:**

   ```powershell
   Get-ScheduledTask | Where-Object {$_.TaskName -match "Daily"}
   ```

2. **Check task history:**

   ```powershell
   Get-ScheduledTaskInfo -TaskName "Daily-Data-Refresh"
   ```

3. **Run task manually to see errors:**

   ```powershell
   Start-ScheduledTask -TaskName "Daily-Data-Refresh"
   ```

4. **Check logs:**
   ```
   db-sync/logs/
   backups/
   ```

### SSH Connection Fails

If sync task fails with SSH errors:

```powershell
# Verify SSH works
ssh server2 "echo OK"

# Check keys are set up
ssh-keygen -t ed25519 -C 'db-sync@srvr'
ssh-copy-id -i ~/.ssh/id_ed25519.pub server2
```

### Import Fails

If refresh task fails:

1. Check `refresh_production_data.ps1` logs
2. Verify CSV files downloaded correctly
3. Check `production.db` integrity
4. Restore from backup if needed:
   ```powershell
   Copy-Item 'backups/production_backup_YYYYMMDD_HHMMSS.db' 'production.db' -Force
   ```

---

## Configuration

Edit `db-sync/config/db-sync.json` to adjust:

- `sync_interval_minutes`: Changed from 15 to 1440 (daily)
- `daily_refresh_time`: "05:00"
- `daily_sync_time`: "06:30"
- `timezone`: "America/Los_Angeles"

---

## Integration with `refresh_production_data.ps1`

The refresh script now has:

**New option:**

```powershell
-SyncToProduction  # Automatically triggers sync to Server 2 after import
```

**Example workflow:**

```powershell
# Full cycle (download → import → sync)
.\refresh_production_data.ps1 -SyncToProduction

# Import only (skip download)
.\refresh_production_data.ps1 -SkipDownload -SyncToProduction

# Download and import, skip sync
.\refresh_production_data.ps1
```

---

## Expected Output

### 5:00 AM Refresh

```
========================================
  Healthcare Data Refresh Workflow
========================================

[1/4] Creating backup...
  [OK] Backup created: backups/production_backup_20251219_050000.db (XX.XX MB)

[2/4] Downloading fresh data from Google Sheets...
  [OK] Downloaded to downloads/

[3/4] Transforming and importing data...
  [OK] Import complete

[4/4] Running post-import processing...
  [OK] Views created, patient data updated, summaries populated

[5/5] Syncing CSV data to production (VPS2)...
  Using smart sync (preserves manual entries on VPS2)
  [OK] CSV data synced to production

========================================
  Workflow Complete!
  Duration: 02:45
========================================
```

### 6:30 AM Sync (if running separately)

```
========================================
Smart CSV Sync - 2025_12
========================================
Source: D:\Git\myhealthteam2\Dev\production.db
Target: server2:/opt/myhealthteam/production.db

Testing SSH connection...
SSH connection: OK

Found 2 task table(s) to sync:
  provider_tasks_2025_12
  coordinator_tasks_2025_12

Processing: provider_tasks_2025_12
  Local: 425 CSV_IMPORT rows, 18 manual rows
  Exporting 425 rows...
  Export file: 45.2 KB
  Uploading to master...
  Executing on master...
  SUCCESS: 425 rows synced to master

Processing: coordinator_tasks_2025_12
  Local: 312 CSV_IMPORT rows, 5 manual rows
  Exporting 312 rows...
  Export file: 31.8 KB
  Uploading to master...
  Executing on master...
  SUCCESS: 312 rows synced to master

========================================
Sync Complete
Synced 737 rows across 2 table(s)
Log file: db-sync/logs/csv_sync_20251219_063000.log
========================================
```

---

## Monitoring

The system logs all activities to:

- `db-sync/logs/` - Sync operation logs
- `backups/` - Database backups with timestamps

Check these folders regularly to monitor:

- Data freshness timestamps
- Import success/failure rates
- Sync error messages
