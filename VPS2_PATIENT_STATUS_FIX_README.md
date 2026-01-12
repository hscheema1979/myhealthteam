# VPS2 patient_status Column Fix - Deployment Guide

## Problem Summary

**Error:** `Error loading onboarding queue: no such column: op.patient_status`

**Root Cause:** The `onboarding_patients` table on VPS2 is missing the `patient_status` column, which is referenced in multiple database queries throughout the application.

## Files Created

1. **fix_vps2_patient_status_column.py** - Migration script that:
   - Checks if `patient_status` column exists
   - Adds the column if missing
   - Sets default value 'Active' for existing records
   - Verifies the fix

2. **run_patient_status_fix_on_vps2.sh** - Bash deployment script (Linux/Unix)
3. **run_patient_status_fix_on_vps2.ps1** - PowerShell deployment script (Windows)

## Deployment Instructions

### Option 1: Deploy to VPS2 via SSH (Recommended)

#### Prerequisites
- SSH access to VPS2 server
- Application directory location on VPS2
- Python 3 installed on VPS2

#### Steps

1. **Upload files to VPS2:**
   ```bash
   # From your local machine
   scp fix_vps2_patient_status_column.py user@vps2:/path/to/myhealthteam2/Dev/
   scp run_patient_status_fix_on_vps2.sh user@vps2:/path/to/myhealthteam2/Dev/
   ```

2. **SSH into VPS2:**
   ```bash
   ssh user@vps2
   ```

3. **Navigate to application directory:**
   ```bash
   cd /path/to/myhealthteam2/Dev
   ```

4. **Make deployment script executable:**
   ```bash
   chmod +x run_patient_status_fix_on_vps2.sh
   ```

5. **Edit deployment script to set correct path:**
   ```bash
   nano run_patient_status_fix_on_vps2.sh
   # Update the APP_DIR variable to your actual path
   # Save and exit (Ctrl+X, Y, Enter)
   ```

6. **Run the deployment script:**
   ```bash
   ./run_patient_status_fix_on_vps2.sh
   ```

7. **Verify the output:**
   - Backup should be created
   - Migration should complete successfully
   - No errors should appear

8. **Restart your application:**
   ```bash
   # Adjust based on your deployment method
   systemctl restart myhealthteam
   # or
   supervisorctl restart myhealthteam
   ```

### Option 2: Manual Migration (Alternative)

If you prefer manual execution:

1. **SSH into VPS2 and navigate to app directory:**
   ```bash
   ssh user@vps2
   cd /path/to/myhealthteam2/Dev
   ```

2. **Create backup:**
   ```bash
   cp production.db backups/db_backup_$(date +%Y%m%d_%H%M%S).db
   ```

3. **Run migration script directly:**
   ```bash
   python3 fix_vps2_patient_status_column.py
   ```

4. **Restart application**

### Option 3: Run Migration Locally (If App Runs Locally)

If your development environment mimics VPS2:

1. **Open terminal in project directory:**
   ```bash
   cd d:/Git/myhealthteam2/Dev
   ```

2. **Run the PowerShell deployment script:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File run_patient_status_fix_on_vps2.ps1
   ```

   Or run the migration script directly:
   ```bash
   python fix_vps2_patient_status_column.py
   ```

## What the Migration Does

1. **Checks current schema** - Examines `onboarding_patients` table structure
2. **Adds missing column** - If `patient_status` doesn't exist, adds it with default value 'Active'
3. **Updates existing records** - Sets all existing records to 'Active' status
4. **Verifies data** - Confirms all records have valid `patient_status` values
5. **Creates backup** - Automatically backs up database before any changes

## Verification Steps

After deployment, verify the fix:

1. **Check application logs:**
   - No "no such column: op.patient_status" errors
   - Onboarding queue loads successfully

2. **Test onboarding features:**
   - View onboarding queue in dashboard
   - Create new onboarding patient
   - Update patient status
   - Complete workflow stages

3. **Verify database:**
   ```bash
   sqlite3 production.db "SELECT patient_status, COUNT(*) FROM onboarding_patients GROUP BY patient_status;"
   ```
   Expected output: All records should have 'Active' status (or other valid statuses)

## Rollback Instructions

If anything goes wrong:

1. **Restore from backup:**
   ```bash
   # Find the latest backup
   ls -lt backups/db_backup_patient_status_fix_*
   
   # Restore (replace with actual backup filename)
   cp backups/db_backup_patient_status_fix_20250105_123456.db production.db
   ```

2. **Restart application**

3. **Check backup location:**
   - Backups are stored in `backups/` directory
   - Backup format: `db_backup_patient_status_fix_YYYYMMDD_HHMMSS.db`

## Troubleshooting

### Error: "production.db not found"
- Ensure you're in the correct application directory
- Check that database file exists
- Update the path in deployment script if needed

### Error: "Permission denied"
- Ensure deployment script has execute permission: `chmod +x run_patient_status_fix_on_vps2.sh`
- Check database file permissions

### Error: "Column already exists"
- This is expected if migration was already run
- The script will detect this and exit successfully

### Application still shows error after fix
- Restart the application (required to reload database schema)
- Clear any application cache
- Check that you're running against the correct database

## Related Database Queries

The following functions reference `patient_status` column:

- `get_onboarding_queue_stats()` - Statistics function
- `get_onboarding_tasks_by_role()` - Role-based task filtering
- `get_provider_onboarding_queue()` - Provider-specific queue
- `get_onboarding_queue()` - Main onboarding queue
- Various onboarding dashboard queries

All these queries filter by `patient_status = 'Active'` to show active patients only.

## Technical Details

**Column Definition:**
```sql
patient_status TEXT DEFAULT 'Active'
```

**Valid Values:**
- 'Active' - Default, patient in active onboarding
- 'Active-Geri' - Geriatric patients
- 'Active-PCP' - PCP-referred patients
- 'Completed' - Fully onboarded patients
- 'On Hold' - Temporarily paused

**Impact:**
- This column is critical for filtering onboarding queue
- Missing column causes all onboarding-related queries to fail
- Default value ensures backward compatibility with existing data

## Support

If you encounter any issues not covered in this guide:

1. Check the error messages in the migration script output
2. Review the backup directory for rollback option
3. Verify Python and SQLite versions
4. Contact development team with:
   - Error messages
   - Migration script output
   - Database schema (if available)

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-05  
**Issue Reference:** VPS2 patient_status Missing Column
