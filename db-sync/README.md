# DB-Sync: Database Synchronization System

Smart synchronization of `production.db` between SRVR (Windows dev) and VPS2/Server2 (Linux production).

## Quick Start

```powershell
# Test connection
.\bin\test_connection.ps1

# Preview what would be synced
.\bin\sync_csv_data.ps1 -DryRun

# Execute sync
.\bin\sync_csv_data.ps1
```

## How It Works

The sync uses **smart CSV sync** which:
- Only syncs rows with `source_system = 'CSV_IMPORT'`
- Preserves `MANUAL`, `DASHBOARD`, and `WORKFLOW` entries on production
- Uses SQLite `.mode insert` for proper escaping of special characters

## Scripts

| Script | Purpose |
|--------|---------|
| `sync_csv_data.ps1` | Smart CSV sync (recommended) |
| `sync_production_db.ps1` | Full DB sync (use with caution) |
| `test_connection.ps1` | Verify SSH and database access |
| `setup_scheduled_task.ps1` | Configure automatic 15-min sync |

## Configuration

Edit `config/db-sync.json` to change paths or hosts.

Uses SSH alias `server2` from `~/.ssh/config` - no manual SSH key setup required.

## Scheduled Task

To enable automatic syncing (requires Administrator):

```powershell
.\bin\setup_scheduled_task.ps1
```

## Integration

Use with data refresh workflow:

```powershell
.\refresh_production_data.ps1 -SyncToProduction
```

## Directory Structure

```
db-sync/
├── bin/        # Scripts (tracked in git)
├── config/     # Configuration (tracked in git)
├── logs/       # Operation logs (git-ignored)
├── backups/    # Pre-sync backups (git-ignored)
├── temp/       # Temporary files (git-ignored)
└── flags/      # Trigger files (git-ignored)
```

## Troubleshooting

**SSH fails:** Verify `ssh server2 "echo OK"` works

**No tables found:** Check month format is `YYYY_MM`

**Parse errors:** Script handles special characters automatically via `.mode insert`

See `docs/CONSOLIDATED_SYSTEM_DOCUMENTATION.md` for full documentation.
