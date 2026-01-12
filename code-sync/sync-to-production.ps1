# sync-to-production.ps1
# Sync code changes to VPS2 production server
# Run this locally after committing changes to Git

param(
    [switch]$IncludeDb,
    [switch]$DryRun,
    [switch]$RestoreConfig  # If you accidentally overwrote prod config, use this to restore
)

$ErrorActionPreference = "Stop"

# Configuration
$VPS_HOST = "server2"
$VPS_USER = "root"
$REMOTE_PATH = "/opt/myhealthteam"
$LOCAL_PATH = "D:\Git\myhealthteam2\Dev"

# Files to NEVER sync (production-specific config)
$PROTECTED_FILES = @(
    "src/oauth_config.py",
    ".streamlit/secrets.toml",
    ".env"
)

# Files to sync (Python code only)
$CODE_FILES = @(
    "app.py",
    "requirements.txt",
    "src/database.py",
    "src/auth_module.py",
    "src/core_utils.py",
    "src/dashboards/*.py",
    "src/utils/*.py",
    ".streamlit/config.toml"
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Code Sync to Production" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Yellow

# Restore config option
if ($RestoreConfig) {
    Write-Host "[RESTORE MODE] Restoring protected configs from backup..." -ForegroundColor Yellow
    if (-not $DryRun) {
        $latestBackup = ssh $VPS_HOST "ls -t $REMOTE_PATH/backups/src-backup-* 2>/dev/null | head -1"
        if ($latestBackup) {
            foreach ($file in $PROTECTED_FILES) {
                $backupFile = "$latestBackup/$file"
                ssh $VPS_HOST "if [ -f '$backupFile' ]; then cp '$backupFile' '$REMOTE_PATH/$file'; echo 'Restored: $file'; fi"
            }
            Write-Host "  [OK] Config restored from $latestBackup`n" -ForegroundColor Green
        } else {
            Write-Host "  [WARN] No backup found to restore from`n" -ForegroundColor Yellow
        }
    }
    exit 0
}

if ($DryRun) {
    Write-Host "[DRY RUN] No actual changes will be made`n" -ForegroundColor Gray
}

# Step 1: Show protected files
Write-Host "[PROTECTED FILES] (will NOT be synced):" -ForegroundColor Yellow
foreach ($file in $PROTECTED_FILES) {
    Write-Host "  - $file" -ForegroundColor Red
}
Write-Host ""

# Step 2: Backup on remote (includes protected files)
Write-Host "[1/5] Creating remote backup..." -ForegroundColor Yellow
if (-not $DryRun) {
    ssh $VPS_HOST "mkdir -p $REMOTE_PATH/backups && cp -r $REMOTE_PATH/src $REMOTE_PATH/backups/src-backup-\$(date +%Y%m%d_%H%M%S) 2>/dev/null || true"
    Write-Host "  [OK] Backup created`n" -ForegroundColor Green
} else {
    Write-Host "  [SKIP] Backup (dry run)`n" -ForegroundColor Gray
}

# Step 3: Sync code files (excluding protected files)
Write-Host "[2/5] Syncing Python code files..." -ForegroundColor Yellow
Write-Host "  Excluding: $PROTECTED_FILES" -ForegroundColor Gray

if (-not $DryRun) {
    # Use rsync with exclusions
    $excludeArgs = ""
    foreach ($file in $PROTECTED_FILES) {
        $excludeArgs += "--exclude='$file' "
    }

    rsync -avz --progress $excludeArgs `
        --exclude='__pycache__' `
        --exclude='*.pyc' `
        --exclude='*.pyo' `
        app.py requirements.txt src/ .streamlit/ `
        $VPS_HOST`:$REMOTE_PATH/
    Write-Host ""
} else {
    Write-Host "  Command: rsync -avz --progress $excludeArgs --exclude='__pycache__' app.py requirements.txt src/ .streamlit/ $VPS_HOST`:$REMOTE_PATH/`n" -ForegroundColor Gray
}

# Step 4: Sync database (optional)
if ($IncludeDb) {
    Write-Host "[3/5] Syncing production.db..." -ForegroundColor Yellow
    Write-Host "  [WARN] Database sync will overwrite production data!" -ForegroundColor Red
    if (-not $DryRun) {
        ssh $VPS_HOST "cp $REMOTE_PATH/production.db $REMOTE_PATH/backups/production_backup_\$(date +%Y%m%d_%H%M%S).db"
        scp "production.db" "$VPS_HOST`:$REMOTE_PATH/production.db"
        Write-Host "  [OK] Database synced`n" -ForegroundColor Green
    } else {
        Write-Host "  [SKIP] Database (dry run)`n" -ForegroundColor Gray
    }
} else {
    Write-Host "[3/5] Skipping database sync (use -IncludeDb to enable)`n" -ForegroundColor Gray
}

# Step 5: Restart application
Write-Host "[4/5] Restarting Streamlit..." -ForegroundColor Yellow
if (-not $DryRun) {
    $restartResult = ssh $VPS_HOST "cd $REMOTE_PATH && pm2 restart myhealthteam 2>&1 || echo 'PM2 not configured'"
    Write-Host "  $restartResult`n" -ForegroundColor White
} else {
    Write-Host "  [SKIP] Restart (dry run)`n" -ForegroundColor Gray
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sync Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Protected files preserved:" -ForegroundColor Cyan
Write-Host "  - src/oauth_config.py (OAuth credentials)" -ForegroundColor Gray
Write-Host "  - .streamlit/secrets.toml (Streamlit secrets)" -ForegroundColor Gray
Write-Host "  - .env (Environment variables)" -ForegroundColor Gray
Write-Host ""
Write-Host "If you need to restore configs:" -ForegroundColor Yellow
Write-Host "  .\code-sync\sync-to-production.ps1 -RestoreConfig`n" -ForegroundColor Gray
