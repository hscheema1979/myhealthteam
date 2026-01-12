#!/bin/bash
#
# Deployment script to fix missing patient_status column on VPS2
# Run this on the VPS2 server
#

set -e  # Exit on any error

echo "=============================================================================="
echo "VPS2 patient_status Column Fix Deployment"
echo "=============================================================================="
echo "Started at: $(date)"
echo ""

# Navigate to the application directory
APP_DIR="/path/to/myhealthteam2/Dev"  # UPDATE THIS PATH AS NEEDED
cd "$APP_DIR" || exit 1

echo "Current directory: $(pwd)"
echo ""

# Backup the database before making changes
echo "Step 1: Creating database backup..."
BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/db_backup_patient_status_fix_$(date +%Y%m%d_%H%M%S).db"

if [ -f "production.db" ]; then
    cp production.db "$BACKUP_FILE"
    echo "✓ Backup created: $BACKUP_FILE"
else
    echo "✗ production.db not found!"
    exit 1
fi
echo ""

# Run the migration script
echo "Step 2: Running migration script..."
if python3 fix_vps2_patient_status_column.py; then
    echo "✓ Migration completed successfully"
else
    echo "✗ Migration failed!"
    echo "Restoring from backup..."
    cp "$BACKUP_FILE" production.db
    echo "✓ Database restored from backup"
    exit 1
fi
echo ""

echo "Step 3: Restarting application..."
# Adjust the restart command based on how your app is deployed
# Example commands (uncomment as needed):
# systemctl restart myhealthteam
# supervisorctl restart myhealthteam
# pkill -f "streamlit run app.py"
echo "Please restart your application manually or adjust this script"
echo ""

echo "=============================================================================="
echo "Deployment completed successfully at: $(date)"
echo "=============================================================================="
echo ""
echo "Next steps:"
echo "1. Verify the application is running without errors"
echo "2. Check that onboarding queue loads correctly"
echo "3. Test onboarding workflow functions"
echo ""
