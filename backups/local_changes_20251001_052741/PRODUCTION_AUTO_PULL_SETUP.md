# Production Auto-Pull Setup

## Overview

This production environment has been configured to automatically pull changes from the GitHub repository instead of pushing changes. This ensures the production environment stays up-to-date with the latest development changes while preventing accidental pushes from production.

## Configuration

### Auto-Pull System
- **Scheduled Task**: `MyHealthTeam-AutoGitPull`
- **Frequency**: Every 30 minutes
- **Branch**: `main`
- **Status**: Active and Ready

### What It Does
1. **Checks for local changes** - Any uncommitted changes are detected
2. **Backs up local changes** - Creates timestamped backups in `backups/local_changes_YYYYMMDD_HHMMSS/`
3. **Stashes changes** - Temporarily saves local changes
4. **Fetches from remote** - Downloads latest changes from GitHub
5. **Pulls updates** - Merges remote changes into local repository
6. **Logs everything** - Detailed logs in `logs/auto_git_pull.log`

### Safety Features
- **Local change backup** - All local changes are backed up before pulling
- **Automatic stashing** - Local changes are preserved and can be recovered
- **Retry logic** - Up to 3 attempts for each Git operation
- **Comprehensive logging** - Full audit trail of all operations

## Manual Operations

### Trigger Manual Pull
```powershell
PowerShell.exe -ExecutionPolicy Bypass -File "scripts\auto_git_pull.ps1"
```

### Test Pull (Dry Run)
```powershell
PowerShell.exe -ExecutionPolicy Bypass -File "scripts\auto_git_pull.ps1" -DryRun
```

### Check Task Status
```powershell
Get-ScheduledTask -TaskName "MyHealthTeam-AutoGitPull"
```

### View Logs
```powershell
Get-Content "logs\auto_git_pull.log" -Tail 50
```

## Removing Auto-Pull Setup

If you need to disable the auto-pull system:

```powershell
PowerShell.exe -ExecutionPolicy Bypass -File "scripts\setup_auto_git_pull.ps1" -Remove
```

## Key Changes from Previous Setup

### Before (Auto-Commit/Push)
- ❌ Automatically committed and pushed changes every hour
- ❌ Could push unwanted changes to GitHub
- ❌ Risk of conflicts with development work

### Now (Auto-Pull)
- ✅ Automatically pulls latest changes every 30 minutes
- ✅ Backs up any local changes before pulling
- ✅ Keeps production environment up-to-date
- ✅ No risk of pushing unwanted changes
- ✅ Safe for production use

## File Locations

- **Auto-pull script**: `scripts/auto_git_pull.ps1`
- **Setup script**: `scripts/setup_auto_git_pull.ps1`
- **Logs**: `logs/auto_git_pull.log`
- **Backups**: `backups/local_changes_*/`

## Monitoring

The system logs all operations with timestamps and status levels:
- **INFO**: General information
- **SUCCESS**: Successful operations
- **WARNING**: Non-critical issues
- **ERROR**: Failed operations

Check the logs regularly to ensure the system is working correctly:

```powershell
# View recent log entries
Get-Content "logs\auto_git_pull.log" -Tail 20

# View only errors
Get-Content "logs\auto_git_pull.log" | Select-String "ERROR"
```

## Troubleshooting

### Common Issues

1. **Network connectivity** - Ensure internet connection is stable
2. **Git credentials** - Verify GitHub access is configured
3. **File permissions** - Check write permissions for backup directory
4. **Merge conflicts** - Manual resolution may be required for complex conflicts

### Recovery

If local changes are lost, check the backup directories:
```powershell
Get-ChildItem "backups\" | Sort-Object LastWriteTime -Descending
```

Each backup contains a complete copy of your local changes at the time of the pull operation.