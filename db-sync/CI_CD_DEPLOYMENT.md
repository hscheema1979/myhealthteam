# CI/CD Deployment Guide

Automated deployment workflow for db-sync configuration and script changes with local and remote (Server 2) deployment, validation, testing, and rollback capabilities.

## Quick Start

```powershell
# Preview all changes (local + remote)
.\db-sync\bin\deploy_changes.ps1 -DryRun

# Deploy locally and to Server 2
.\db-sync\bin\deploy_changes.ps1

# Deploy to Server 2 only (skip local)
.\db-sync\bin\deploy_changes.ps1 -RemoteDeployOnly

# Skip remote deployment (local only)
.\db-sync\bin\deploy_changes.ps1 -SkipRemoteDeploy

# Force deployment with auto-rollback
.\db-sync\bin\deploy_changes.ps1 -Force -AutoRollback
```

## What It Does

The deployment script automates the complete deployment workflow:

**Local Deployment:**

1. **Validate Configuration** - Checks JSON syntax and required fields
2. **Backup Current Config** - Creates timestamped backup before changes
3. **Detect Changes** - Identifies modified files in db-sync directory
4. **Update Scheduled Tasks** - Verifies tasks are configured correctly
5. **Deploy Changes** - Applies configuration and script updates
6. **Post-Deployment Tests** - Validates connectivity and configuration

**Remote Deployment (Server 2):** 7. **SSH Connection Test** - Verifies connectivity to Server 2 8. **Package Creation** - Creates tar archive of db-sync files 9. **Remote Upload** - Uses SCP to transfer archive to Server 2 10. **Remote Extraction** - Extracts and deploys on Server 2 11. **Remote Backup** - Backs up old configuration before deployment 12. **Permissions Setup** - Sets executable permissions on scripts 13. **Verification** - Confirms deployment was successful

14. **Logging & Status** - Records all actions with timestamps

## Usage

### Basic Local Deployment

```powershell
# Change to project directory
cd D:\Git\myhealthteam2\Dev

# Run deployment (local changes only)
.\db-sync\bin\deploy_changes.ps1 -SkipRemoteDeploy
```

### Complete Deployment (Local + Remote)

```powershell
# Deploy changes locally AND to Server 2
.\db-sync\bin\deploy_changes.ps1
```

This will:

1. Validate configuration
2. Backup current config
3. Detect changes
4. Update scheduled tasks
5. Deploy locally
6. Create tar archive of db-sync
7. Upload to Server 2
8. Extract and deploy on Server 2
9. Verify remote installation

### Remote Deployment Only

If you only want to update Server 2 (skip local changes):

```powershell
.\db-sync\bin\deploy_changes.ps1 -RemoteDeployOnly
```

Useful when:

- Local and remote are out of sync
- You only need to update Server 2
- Testing remote deployment separately

### Preview Changes (Dry Run)

```powershell
# See what would be deployed without making changes
.\db-sync\bin\deploy_changes.ps1 -DryRun
```

Output:

```
========================================
  DB-Sync CI/CD Deployment
========================================

[timestamp] [INFO] Validating configuration...
[timestamp] [INFO] Configuration is valid
[timestamp] [INFO] Backing up current configuration...
[timestamp] [INFO] Configuration backed up to: db-sync/backups/db-sync-config-backup_20251219_052300.json

[timestamp] [INFO] DRY RUN: Would deploy 3 changed files
  db-sync/config/db-sync.json
  db-sync/bin/sync_csv_data.ps1
  db-sync/bin/deploy_changes.ps1

========================================
  No changes would be applied (DRY RUN)
========================================
```

### Force Deployment

When you want to redeploy even if no changes were detected:

```powershell
.\db-sync\bin\deploy_changes.ps1 -Force
```

This is useful when:

- Making manual changes to files (not tracked by git)
- Reapplying configuration after issues
- Testing the deployment workflow

### Advanced Options

```powershell
# Skip validation (faster, less safe)
.\db-sync\bin\deploy_changes.ps1 -SkipValidation

# Skip connectivity tests
.\db-sync\bin\deploy_changes.ps1 -SkipTests

# Enable automatic rollback on failure
.\db-sync\bin\deploy_changes.ps1 -AutoRollback

# Verbose logging (detailed output)
.\db-sync\bin\deploy_changes.ps1 -Verbose

# Combine flags
.\db-sync\bin\deploy_changes.ps1 -Force -DryRun -Verbose
```

## Configuration Workflow

### 1. Make Changes Locally

Edit files in `db-sync/`:

```powershell
# Example: Adjust sync schedule times
Edit-Content db-sync/config/db-sync.json

# Or modify a sync script
Edit-Content db-sync/bin/sync_csv_data.ps1
```

### 2. Preview Changes

```powershell
.\db-sync\bin\deploy_changes.ps1 -DryRun
```

Review the output:

- What configuration fields changed
- What scripts were updated
- Validation checks pass

### 3. Deploy Changes

```powershell
.\db-sync\bin\deploy_changes.ps1
```

The script will:

- Backup current configuration
- Validate new configuration
- Update scheduled tasks if needed
- Test SSH connectivity
- Record deployment in logs

### 4. Verify Deployment

```powershell
# Check logs
Get-Content db-sync/logs/deployment_status.json | ConvertFrom-Json

# View detailed deployment log
Get-Content db-sync/logs/deployments/deploy_20251219_052300.log

# Verify scheduled tasks
Get-ScheduledTask | Where-Object {$_.TaskName -match "Daily"}
```

## Deployment Logs

All deployments are logged to:

**Status Summary:**

```
db-sync/logs/deployment_status.json
```

**Detailed Logs:**

```
db-sync/logs/deployments/deploy_YYYYMMDD_HHMMSS.log
```

### Example Status File

```json
{
  "deployment_id": "deploy_20251219_052300",
  "status": "success",
  "message": "Deployment completed successfully",
  "timestamp": "2025-12-19T05:23:00.1234567-08:00",
  "log_file": "db-sync/logs/deployments/deploy_20251219_052300.log"
}
```

### Example Log File

```
[20251219_052300] [INFO] ========================================
[20251219_052300] [INFO] DB-Sync CI/CD Deployment Started
[20251219_052300] [INFO] ========================================
[20251219_052300] [INFO] Deployment ID: deploy_20251219_052300
[20251219_052300] [INFO] DryRun: False
[20251219_052300] [INFO] Force: False
[20251219_052300] [INFO]
[20251219_052300] [INFO] Validating configuration...
[20251219_052300] [INFO] Configuration is valid
[20251219_052300] [INFO]
[20251219_052300] [INFO] Backing up current configuration...
[20251219_052300] [INFO] Configuration backed up to: db-sync/backups/db-sync-config-backup_20251219_052300.json
[20251219_052300] [INFO]
[20251219_052300] [INFO] Detecting changed files in db-sync...
[20251219_052300] [INFO] Found 1 changed files
[20251219_052300] [INFO] Changes to deploy:
[20251219_052300] [INFO]   db-sync/config/db-sync.json
[20251219_052300] [INFO]
[20251219_052300] [INFO] Updating scheduled tasks...
[20251219_052300] [INFO] Daily refresh time: 05:00
[20251219_052300] [INFO] Daily sync time: 06:30
[20251219_052300] [INFO] Scheduled tasks found, validating...
[20251219_052300] [INFO] Scheduled tasks are configured and ready
[20251219_052300] [INFO]
[20251219_052300] [INFO] Deploying changes...
[20251219_052300] [INFO] Applying configuration changes...
[20251219_052300] [INFO] Deployment completed successfully
[20251219_052300] [INFO]
[20251219_052300] [INFO] Running post-deployment tests...
[20251219_052300] [INFO] Validating configuration...
[20251219_052300] [INFO] Configuration is valid
[20251219_052300] [INFO] Testing SSH connectivity to Server 2...
[20251219_052300] [INFO] SSH connection to server2: OK
[20251219_052300] [INFO] Post-deployment tests passed
[20251219_052300] [INFO]
[20251219_052300] [INFO] ========================================
[20251219_052300] [INFO] Deployment Successful
[20251219_052300] [INFO] ========================================
```

## Rollback Procedures

### Automatic Rollback

If deployment fails with `-AutoRollback`:

```powershell
.\db-sync\bin\deploy_changes.ps1 -AutoRollback
```

The script will automatically restore from the backup if any step fails.

### Manual Rollback

If you need to revert a deployment manually:

```powershell
# List available backups
Get-ChildItem db-sync/backups/*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 10

# Restore specific backup
Copy-Item db-sync/backups/db-sync-config-backup_20251219_050000.json `
          db-sync/config/db-sync.json -Force

# Verify restoration
Get-Content db-sync/config/db-sync.json | ConvertFrom-Json | Format-List
```

## Common Configuration Changes

### Adjust Sync Times

Edit [`db-sync/config/db-sync.json`](config/db-sync.json):

```json
{
  "schedule": {
    "daily_refresh_time": "06:00", // Change refresh time
    "daily_sync_time": "07:30" // Change sync time
  }
}
```

Then deploy:

```powershell
# Preview
.\db-sync\bin\deploy_changes.ps1 -DryRun

# Apply
.\db-sync\bin\deploy_changes.ps1
```

### Update Master Host

Edit [`db-sync/config/db-sync.json`](config/db-sync.json):

```json
{
  "sync": {
    "master_host": "new-server2-name", // Change Server 2 hostname
    "master_db_path": "/opt/myhealthteam/production.db"
  }
}
```

Deploy with connectivity tests:

```powershell
# This will verify SSH connection to new host
.\db-sync\bin\deploy_changes.ps1 -Force
```

### Update Sync Behavior

Edit [`db-sync/bin/sync_csv_data.ps1`](bin/sync_csv_data.ps1):

```powershell
# Make your changes to the script
# ...

# Deploy
.\db-sync\bin\deploy_changes.ps1 -Force
```

## Troubleshooting

### Deployment Stuck on Validation

```powershell
# Skip validation
.\db-sync\bin\deploy_changes.ps1 -SkipValidation

# Check configuration for issues
Get-Content db-sync/config/db-sync.json | ConvertFrom-Json | Format-List
```

### SSH Connection Failed in Post-Deployment Tests

```powershell
# Skip tests and check manually
.\db-sync\bin\deploy_changes.ps1 -SkipTests

# Test SSH separately
ssh server2 "echo OK"

# Fix SSH keys if needed
ssh-keygen -t ed25519 -C 'db-sync@srvr'
ssh-copy-id -i ~/.ssh/id_ed25519.pub server2
```

### Rollback Due to Failed Deployment

```powershell
# Check what failed
Get-Content db-sync/logs/deployment_status.json | ConvertFrom-Json

# View detailed error log
Get-Content db-sync/logs/deployments/deploy_LATEST_ID.log

# Restore from backup
Copy-Item db-sync/backups/db-sync-config-backup_TIMESTAMP.json `
          db-sync/config/db-sync.json -Force
```

### No Changes Detected

If deployment reports "no changes" but you made edits:

```powershell
# Force deployment
.\db-sync\bin\deploy_changes.ps1 -Force

# Or check if git is tracking your changes
git status db-sync/
```

## Integration with Manual Processes

### After Manual Refresh

If you manually run the refresh script:

```powershell
# Refresh data
.\refresh_production_data.ps1 -SkipBackup -SyncToProduction

# Deploy any config changes
.\db-sync\bin\deploy_changes.ps1
```

### After Manual Sync

If you manually sync data:

```powershell
# Sync data
.\db-sync\bin\sync_csv_data.ps1

# Verify deployment state
.\db-sync\bin\deploy_changes.ps1 -DryRun
```

## Automation with Task Scheduler

You can integrate deployment checks into your scheduled tasks:

```powershell
# Option 1: Run deployment before daily refresh
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File db-sync\bin\deploy_changes.ps1 -SkipTests"

# Option 2: Run deployment as separate daily task
$trigger = New-ScheduledTaskTrigger -Daily -At "04:30"
```

## Best Practices

1. **Always use DryRun first** before real deployments
2. **Keep backups** - they're automatic but check they exist
3. **Test SSH connectivity** if Server 2 hostname changes
4. **Review logs** after each deployment
5. **Use Force cautiously** - for overriding change detection only
6. **Automate deployments** with git commits (if using version control)
7. **Schedule deployments** during off-peak hours

## Script Options Reference

| Option              | Default | Purpose                                      |
| ------------------- | ------- | -------------------------------------------- |
| `-DryRun`           | false   | Preview changes without applying             |
| `-Force`            | false   | Deploy even if no changes detected           |
| `-SkipValidation`   | false   | Skip config validation checks                |
| `-SkipTests`        | false   | Skip post-deployment tests                   |
| `-AutoRollback`     | false   | Automatically restore from backup on failure |
| `-SkipRemoteDeploy` | false   | Skip Server 2 remote deployment              |
| `-RemoteDeployOnly` | false   | Deploy to Server 2 only (skip local)         |
| `-Verbose`          | false   | Detailed logging output                      |

## Remote Deployment Details

### What Gets Deployed to Server 2

The script packages and deploys:

- `config/db-sync.json` - Configuration file
- `bin/*.ps1` - PowerShell scripts
- `bin/*.sh` - Shell scripts (if any)
- `README.md` and other documentation
- All other files except:
  - `logs/` - Not needed on server
  - `backups/` - Local backups only
  - `temp/` - Temporary files
  - `flags/` - Trigger files

### Remote Deployment Process

1. **Archive Creation** - Packages db-sync files into compressed tar archive
2. **Upload via SCP** - Uses SCP to securely transfer archive to Server 2
3. **Remote Extraction** - SSH extracts archive in `/tmp` on Server 2
4. **Backup Existing** - Backs up old config and scripts before overwriting
5. **Copy to Production** - Deploys to `/opt/myhealthteam/db-sync`
6. **Set Permissions** - Makes scripts executable
7. **Verify Installation** - Confirms files exist and are readable

### Remote Location

Files are deployed to: `/opt/myhealthteam/db-sync`

Backups created at: `/opt/myhealthteam/db-sync/backups/config_backup_TIMESTAMP`

### SSH Requirements

Remote deployment requires:

- SSH key-based authentication to server2
- SSH alias configured in `~/.ssh/config`
- No password prompts (use ssh-agent or key with no passphrase)

Test connectivity:

```powershell
ssh server2 "echo OK"
```

## Common Remote Deployment Scenarios

### Sync Configuration After Manual Edit

If you edit `db-sync.json` manually and want to push to Server 2:

```powershell
.\db-sync\bin\deploy_changes.ps1 -Force -RemoteDeployOnly
```

### Test Changes Locally First

Deploy locally to test, then to Server 2:

```powershell
# Test locally
.\db-sync\bin\deploy_changes.ps1 -SkipRemoteDeploy

# If successful, deploy to Server 2
.\db-sync\bin\deploy_changes.ps1 -RemoteDeployOnly
```

### Update Scripts on Server 2 Only

If you updated sync scripts but not configuration:

```powershell
.\db-sync\bin\deploy_changes.ps1 -RemoteDeployOnly -DryRun

# Review, then:
.\db-sync\bin\deploy_changes.ps1 -RemoteDeployOnly
```

### Full Deployment with Auto-Rollback

For critical updates, use auto-rollback:

```powershell
.\db-sync\bin\deploy_changes.ps1 -AutoRollback
```

This will:

- Automatically rollback on local failure
- Automatically rollback on remote failure
- Restore from backup if anything goes wrong

### Emergency Rollback on Server 2

If remote deployment fails critically, restore manually:

```powershell
ssh server2 'bash -c "cd /opt/myhealthteam/db-sync/backups && ls -lh config_backup_*" | tail -1'

ssh server2 'bash -c "
  LATEST_BACKUP=\$(ls -t /opt/myhealthteam/db-sync/backups/config_backup_* | head -1)
  cp -r \$LATEST_BACKUP /opt/myhealthteam/db-sync/config
  echo \"Restored from: \$LATEST_BACKUP\"
"'
```

## Files Generated During Deployment

After a deployment, check these files:

```
db-sync/
├── logs/
│   ├── deployment_status.json          # Latest deployment status
│   └── deployments/
│       └── deploy_YYYYMMDD_HHMMSS.log  # Detailed deployment log
├── backups/
│   └── db-sync-config-backup_YYYYMMDD_HHMMSS.json  # Pre-deployment backup
├── config/
│   └── db-sync.json                    # Current configuration
└── bin/
    └── deploy_changes.ps1               # This script
```

## Next Steps

After successful deployment:

1. **Monitor logs** - Check `db-sync/logs/` for any issues
2. **Verify tasks** - Confirm scheduled tasks run at expected times
3. **Test manually** - Run refresh or sync manually to verify behavior
4. **Document changes** - Update [`DAILY_SYNC_SCHEDULE.md`](DAILY_SYNC_SCHEDULE.md) if configuration changed
5. **Commit to git** - If using version control, commit your changes
