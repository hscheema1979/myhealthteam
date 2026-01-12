#
# Deployment script to fix missing patient_status column on VPS2
# Run this on VPS2 server (Windows or Linux with PowerShell)
#

Write-Host "=============================================================================="
Write-Host "VPS2 patient_status Column Fix Deployment"
Write-Host "=============================================================================="
Write-Host "Started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# Navigate to application directory
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptPath

Write-Host "Current directory: $(Get-Location)"
Write-Host ""

# Backup database before making changes
Write-Host "Step 1: Creating database backup..."
$BackupDir = "backups"
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "$BackupDir\db_backup_patient_status_fix_$Timestamp.db"

if (Test-Path "production.db") {
    Copy-Item "production.db" $BackupFile
    Write-Host "✓ Backup created: $BackupFile"
} else {
    Write-Host "✗ production.db not found!"
    Write-Host "Please ensure you're running this script from the correct directory."
    exit 1
}
Write-Host ""

# Run migration script
Write-Host "Step 2: Running migration script..."
$MigrationResult = & python fix_vps2_patient_status_column.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Migration completed successfully"
} else {
    Write-Host "✗ Migration failed!"
    Write-Host "Restoring from backup..."
    Copy-Item $BackupFile "production.db" -Force
    Write-Host "✓ Database restored from backup"
    exit 1
}
Write-Host ""

Write-Host "Step 3: Restarting application..."
Write-Host "Please restart your application manually."
Write-Host ""

Write-Host "=============================================================================="
Write-Host "Deployment completed successfully at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "=============================================================================="
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Verify that application is running without errors"
Write-Host "2. Check that onboarding queue loads correctly"
Write-Host "3. Test onboarding workflow functions"
Write-Host ""
