#!/bin/bash

# Script to run billing duplicates cleanup on VPS2/Server2
# This script will:
# 1. Copy cleanup scripts to VPS2
# 2. Run diagnostic
# 3. Run cleanup
# 4. Verify results

echo "================================================================================"
echo "BILLING DUPLICATES CLEANUP - VPS2/SERVER2"
echo "================================================================================"
echo "Timestamp: $(date)"

# Configuration
SERVER="server2"
REMOTE_DB_PATH="/opt/myhealthteam/production.db"
REMOTE_TEMP_DIR="/tmp/billing_cleanup_$$"
BACKUP_DIR="/opt/myhealthteam/backups"

# Create backup directory on remote if it doesn't exist
echo ""
echo "Setting up remote directories..."
ssh $SERVER "mkdir -p $BACKUP_DIR"

# Create temp directory for scripts
echo "Creating temp directory for cleanup scripts..."
ssh $SERVER "mkdir -p $REMOTE_TEMP_DIR"

# Copy cleanup scripts to remote
echo ""
echo "Copying cleanup scripts to VPS2..."
scp check_billing_duplicates.py ${SERVER}:${REMOTE_TEMP_DIR}/
scp fix_billing_duplicates.py ${SERVER}:${REMOTE_TEMP_DIR}/
scp fix_remaining_duplicates.py ${SERVER}:${REMOTE_TEMP_DIR}/

# Run diagnostic first
echo ""
echo "================================================================================"
echo "STEP 1: RUNNING DIAGNOSTIC ON VPS2"
echo "================================================================================"
ssh $SERVER "cd $REMOTE_TEMP_DIR && python3 check_billing_duplicates.py"

echo ""
echo "================================================================================"
echo "STEP 2: RUNNING CLEANUP ON VPS2"
echo "================================================================================"

# Run initial cleanup
ssh $SERVER "cd $REMOTE_TEMP_DIR && echo 'yes' | python3 fix_billing_duplicates.py"

# Check if remaining cleanup is needed
echo ""
echo "Checking for remaining duplicates..."
ssh $SERVER "cd $REMOTE_TEMP_DIR && python3 fix_remaining_duplicates.py"

# Final verification
echo ""
echo "================================================================================"
echo "STEP 3: FINAL VERIFICATION"
echo "================================================================================"
ssh $SERVER "cd $REMOTE_TEMP_DIR && python3 check_billing_duplicates.py"

# Cleanup temp directory
echo ""
echo "Cleaning up temporary files..."
ssh $SERVER "rm -rf $REMOTE_TEMP_DIR}"

# Get summary
echo ""
echo "================================================================================"
echo "CLEANUP SUMMARY FOR VPS2"
echo "================================================================================"
echo "Remote database: $REMOTE_DB_PATH"
echo "Backup location: $BACKUP_DIR"
echo ""
echo "Next steps:"
echo "1. Review the cleanup results above"
echo "2. Test billing reports in VPS2 dashboard"
echo "3. Sync cleaned database to local if needed"
echo ""

echo "✓ VPS2 cleanup complete!"
