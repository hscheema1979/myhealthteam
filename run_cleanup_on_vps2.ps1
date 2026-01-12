# Script to run billing duplicates cleanup on VPS2/Server2
# This script will:
# 1. Copy cleanup scripts to VPS2
# 2. Run diagnostic
# 3. Run cleanup
# 4. Verify results

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "BILLING DUPLICATES CLEANUP - VPS2/SERVER2" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow

# Configuration
$SERVER = "server2"
$REMOTE_DB_PATH = "/opt/myhealthteam/production.db"
$REMOTE_TEMP_DIR = "/tmp/billing_cleanup_$$"
$BACKUP_DIR = "/opt/myhealthteam/backups"

# Create backup directory on remote if it doesn't exist
Write-Host ""
Write-Host "Setting up remote directories..." -ForegroundColor Green
ssh $SERVER "mkdir -p $BACKUP_DIR"

# Create temp directory for scripts
Write-Host "Creating temp directory for cleanup scripts..." -ForegroundColor Green
$TEMP_DIR = ssh $SERVER "mktemp -d"
Write-Host "Remote temp directory: $TEMP_DIR"

# Copy cleanup scripts to remote
Write-Host ""
Write-Host "Copying cleanup scripts to VPS2..." -ForegroundColor Green
scp check_billing_duplicates.py "${SERVER}:${TEMP_DIR}/"
scp fix_billing_duplicates.py "${SERVER}:${TEMP_DIR}/"
scp fix_remaining_duplicates.py "${SERVER}:${TEMP_DIR}/"

# Run diagnostic first
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "STEP 1: RUNNING DIAGNOSTIC ON VPS2" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
ssh $SERVER "cd $TEMP_DIR && python3 check_billing_duplicates.py"

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "STEP 2: RUNNING CLEANUP ON VPS2" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# Run initial cleanup
ssh $SERVER "cd $TEMP_DIR && echo 'yes' | python3 fix_billing_duplicates.py"

# Check if remaining cleanup is needed
Write-Host ""
Write-Host "Checking for remaining duplicates..." -ForegroundColor Yellow
ssh $SERVER "cd $TEMP_DIR && python3 fix_remaining_duplicates.py"

# Final verification
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "STEP 3: FINAL VERIFICATION" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
ssh $SERVER "cd $TEMP_DIR && python3 check_billing_duplicates.py"

# Cleanup temp directory
Write-Host ""
Write-Host "Cleaning up temporary files..." -ForegroundColor Green
ssh $SERVER "rm -rf $TEMP_DIR"

# Get summary
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "CLEANUP SUMMARY FOR VPS2" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Remote database: $REMOTE_DB_PATH" -ForegroundColor White
Write-Host "Backup location: $BACKUP_DIR" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review cleanup results above" -ForegroundColor White
Write-Host "2. Test billing reports in VPS2 dashboard" -ForegroundColor White
Write-Host "3. Sync cleaned database to local if needed" -ForegroundColor White
Write-Host ""

Write-Host "[OK] VPS2 cleanup complete!" -ForegroundColor Green
