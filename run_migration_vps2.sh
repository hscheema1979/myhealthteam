#!/bin/bash
# ============================================================================
# Migration Script: Contact Columns + created_at_pst
# ============================================================================
# Purpose: Run database migrations on VPS2 (production instance)
# Date: 2025-01-08
# ============================================================================

set -e

# VPS2 Configuration
VPS_USER="root"
VPS_HOST="vps2"
VPS_DB_PATH="/opt/myhealthteam/production.db"
LOCAL_MIGRATION_SCRIPT="./src/sql/add_appointment_contact_columns.sql"

echo "============================================================================"
echo "Running Database Migration on VPS2 (Production)"
echo "============================================================================"
echo ""
echo "VPS: ${VPS_USER}@${VPS_HOST}"
echo "Remote DB: ${VPS_DB_PATH}"
echo ""

# Check if local migration script exists
if [ ! -f "$LOCAL_MIGRATION_SCRIPT" ]; then
    echo "ERROR: Migration script not found at: $LOCAL_MIGRATION_SCRIPT"
    exit 1
fi

# Copy migration script to VPS2
echo "Copying migration script to VPS2..."
scp "$LOCAL_MIGRATION_SCRIPT" "${VPS_USER}@${VPS_HOST}:/tmp/migration.sql"

# Run migration on VPS2
echo ""
echo "Executing migration on VPS2..."
ssh -o LogLevel=QUIET -t "${VPS_USER}@${VPS_HOST}" << 'ENDSSH'
#!/bin/bash
set -e

DB_PATH="/opt/myhealthteam/production.db"
MIGRATION_SCRIPT="/tmp/migration.sql"

echo ""
echo "============================================================================"
echo "VPS2 Migration Execution"
echo "============================================================================"
echo ""

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "ERROR: Database not found at: $DB_PATH"
    exit 1
fi

echo "Database: $DB_PATH"
echo "Migration: $MIGRATION_SCRIPT"
echo ""

# Use sqlite3 to execute all statements - errors for duplicate columns are OK
# SQLite will continue executing after errors unless we use -bail
# We'll parse output to count successes

sqlite3 "$DB_PATH" < "$MIGRATION_SCRIPT" 2>&1 | while read -r line; do
    if echo "$line" | grep -qi "duplicate column"; then
        echo "[SKIP] $line"
    elif echo "$line" | grep -qi "no such table"; then
        echo "[INFO] $line"
    elif echo "$line" | grep -qi "Error"; then
        echo "[ERROR] $line"
    fi
done

echo ""
echo "============================================================================"
echo "Migration Complete"
echo "============================================================================"
echo ""

# Verify contact columns in onboarding_patients
echo "Verifying new columns in onboarding_patients table..."
sqlite3 -header "$DB_PATH" "PRAGMA table_info(onboarding_patients);" | grep -E "(appointment_contact|medical_contact|facility_nurse)" || echo "No contact columns found"

echo ""
echo "Verifying created_at_pst in coordinator_tasks_2026_01..."
sqlite3 -header "$DB_PATH" "PRAGMA table_info(coordinator_tasks_2026_01);" | grep created_at_pst || echo "Column not found"

echo ""
echo "Done!"

# Cleanup
rm -f "$MIGRATION_SCRIPT"

exit 0
ENDSSH

echo ""
echo "============================================================================"
echo "VPS2 Migration Complete"
echo "============================================================================"
