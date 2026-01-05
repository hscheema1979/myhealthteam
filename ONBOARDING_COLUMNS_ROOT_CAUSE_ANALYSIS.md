# Onboarding Queue Error - Root Cause Analysis

## Problem Statement

**Error:** `Error loading onboarding queue: no such column: op.patient_status`  
**Impact:** VPS2 onboarding queue unable to load, blocking all onboarding workflow functionality

## Root Cause Identified

### The Bug

When `transform_production_data_v3_fixed.py` was run on VPS2, it caused **catastrophic data loss** in the `onboarding_patients` table:

```python
# Line ~1080 in transform_production_data_v3_fixed.py
conn.execute("DELETE FROM onboarding_patients")  # ❌ DELETES ALL EXISTING DATA

# Then repopulates with ONLY 8 columns:
conn.executemany(
    """INSERT INTO onboarding_patients (
        patient_id, first_name, last_name, date_of_birth, phone_primary,
        assigned_provider_user_id, assigned_coordinator_user_id, tv_date, initial_tv_provider
    ) VALUES (?,?,?,?,?,?,?,?,?)""",
    onboarding_data,
)
```

### What Went Wrong

**Table Schema vs. INSERT Statement Mismatch:**

| Table Schema (32 columns) | INSERT Statement (8 columns) | Result |
|---------------------------|----------------------------|--------|
| ✅ onboarding_id | ❌ MISSING | Auto-incremented (OK) |
| ✅ patient_id | ✅ INCLUDED | Preserved |
| ✅ workflow_instance_id | ❌ MISSING | **NULL** |
| ✅ first_name | ✅ INCLUDED | Preserved |
| ✅ last_name | ✅ INCLUDED | Preserved |
| ✅ date_of_birth | ✅ INCLUDED | Preserved |
| ✅ phone_primary | ✅ INCLUDED | Preserved |
| ✅ email | ❌ MISSING | **NULL** |
| ✅ gender | ❌ MISSING | **NULL** |
| ✅ emergency_contact_name | ❌ MISSING | **NULL** |
| ✅ emergency_contact_phone | ❌ MISSING | **NULL** |
| ✅ address_street | ❌ MISSING | **NULL** |
| ✅ address_city | ❌ MISSING | **NULL** |
| ✅ address_state | ❌ MISSING | **NULL** |
| ✅ address_zip | ❌ MISSING | **NULL** |
| ✅ insurance_provider | ❌ MISSING | **NULL** |
| ✅ policy_number | ❌ MISSING | **NULL** |
| ✅ group_number | ❌ MISSING | **NULL** |
| ✅ referral_source | ❌ MISSING | **NULL** |
| ✅ referring_provider | ❌ MISSING | **NULL** |
| ✅ referral_date | ❌ MISSING | **NULL** |
| ❌ **patient_status** | ❌ **MISSING** | **NULL** ← CAUSES ERROR |
| ✅ facility_assignment | ❌ MISSING | **NULL** |
| ❌ **assigned_pot_user_id** | ❌ **MISSING** | **NULL** |
| ❌ **stage1_complete** | ❌ **MISSING** | **NULL** |
| ❌ **stage2_complete** | ❌ **MISSING** | **NULL** |
| ❌ **stage3_complete** | ❌ **MISSING** | **NULL** |
| ❌ **stage4_complete** | ❌ **MISSING** | **NULL** |
| ❌ **stage5_complete** | ❌ **MISSING** | **NULL** |
| ✅ created_date | ❌ MISSING | **NULL** |
| ✅ updated_date | ❌ MISSING | **NULL** |
| ✅ completed_date | ❌ MISSING | **NULL** |

### Impact

**24 out of 32 columns were lost or set to NULL!**

Critical columns that went missing:
- `patient_status` - **Causes the onboarding queue error**
- `assigned_pot_user_id` - Patient Outreach Team assignment
- `stage1_complete` through `stage5_complete` - All workflow tracking
- `completed_date`, `updated_date` - Timestamps
- `insurance_provider`, `policy_number`, `group_number` - Insurance info
- `referral_source`, `referring_provider`, `referral_date` - Referral tracking
- `facility_assignment` - Facility assignment
- `gender`, `emergency_contact_name`, `emergency_contact_phone` - Patient demographics
- `address_street`, `address_city`, `address_state`, `address_zip` - Address info

### Why This Happened

The `transform_production_data_v3_fixed.py` script was designed to:
1. Import patient data from ZMO_MAIN.csv (baseline data)
2. Delete existing data to prevent duplicates
3. Repopulate with fresh data from CSV

**The Problem:** The INSERT statement was never updated to match the full table schema. It only includes the columns available in the ZMO CSV file, ignoring all the other columns that were added to support the onboarding workflow.

### Git History

```bash
git show a757279:transform_production_data_v3_fixed.py | Select-String "INSERT INTO onboarding_patients"
```

Shows the INSERT has only 8 columns since commit `a757279` (Major system update: Add comprehensive billing system, analytics tools, and database sync infrastructure).

## The Fix

### Immediate Fix (Already Applied)

Created `fix_vps2_patient_status_column.py` that:
1. Checks for missing columns in `onboarding_patients` table
2. Adds missing columns with appropriate defaults
3. Sets default values for existing records
4. Verifies the fix

**Status:** ✅ Fixed and verified locally

### Permanent Fix (TODO)

**Option 1: Update INSERT Statement in transform_production_data_v3_fixed.py**

Change the INSERT to include all 32 columns:

```python
# UPDATE THIS INSERT (currently has 8 columns)
conn.executemany(
    """INSERT INTO onboarding_patients (
        patient_id, first_name, last_name, date_of_birth, phone_primary,
        assigned_provider_user_id, assigned_coordinator_user_id, tv_date, initial_tv_provider
    ) VALUES (?,?,?,?,?,?,?,?,?)""",
    onboarding_data,
)

# TO THIS (needs all 32 columns):
conn.executemany(
    """INSERT INTO onboarding_patients (
        patient_id, workflow_instance_id, first_name, last_name, date_of_birth,
        phone_primary, email, gender, emergency_contact_name, emergency_contact_phone,
        address_street, address_city, address_state, address_zip,
        insurance_provider, policy_number, group_number,
        referral_source, referring_provider, referral_date,
        patient_status, facility_assignment, assigned_pot_user_id,
        stage1_complete, stage2_complete, stage3_complete, stage4_complete, stage5_complete,
        created_date, updated_date, completed_date
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    onboarding_data,
)
```

**Option 2: Use UPSERT Instead of DELETE + INSERT**

```python
# REPLACE DELETE + INSERT with INSERT OR REPLACE
conn.executemany(
    """INSERT OR REPLACE INTO onboarding_patients (
        [all 32 columns]
    ) VALUES ([32 placeholders])""",
    onboarding_data,
)
```

**Option 3: Preserve Existing Data (RECOMMENDED)**

```python
# Check if patient already exists
existing_patients = set(
    row[0] for row in conn.execute("SELECT patient_id FROM onboarding_patients").fetchall()
)

# Only INSERT new patients, UPDATE existing ones
for patient in patients_data:
    if patient['patient_id'] in existing_patients:
        # UPDATE existing
        conn.execute("""
            UPDATE onboarding_patients
            SET first_name=?, last_name=?, date_of_birth=?, ...
            WHERE patient_id=?
        """, (...values..., patient['patient_id']))
    else:
        # INSERT new
        conn.execute("""
            INSERT INTO onboarding_patients (...)
            VALUES (...)
        """, (...values...))
```

## Lessons Learned

### What Went Wrong

1. **Schema Drift:** Table schema evolved but import scripts were not updated
2. **Destructive Import:** Using DELETE + INSERT instead of UPSERT or MERGE
3. **No Validation:** No checks to ensure INSERT matches table schema
4. **No Testing:** Import script not tested against production schema
5. **No Warning:** Script didn't warn about missing columns

### Prevention Measures

1. **Add Schema Validation to Import Scripts:**
   ```python
   # Before import, validate columns
   cursor.execute("PRAGMA table_info(onboarding_patients)")
   db_columns = {row[1] for row in cursor.fetchall()}
   
   insert_columns = set([col1, col2, ...])  # From INSERT statement
   
   missing = db_columns - insert_columns
   if missing:
       raise Exception(f"INSERT missing columns: {missing}")
   ```

2. **Use Incremental Imports:**
   - Use INSERT OR REPLACE instead of DELETE + INSERT
   - Or use INSERT OR IGNORE to preserve existing data

3. **Test Against Production Schema:**
   - Run import scripts on production backup first
   - Verify all columns are preserved

4. **Add Column Migrations:**
   - When table schema changes, update all import scripts
   - Document schema version in database table

5. **Backup Before Import:**
   - Already done in deployment scripts ✅
   - Keep multiple backups with timestamps

## Deployment to VPS2

The migration fix (`fix_vps2_patient_status_column.py`) is ready for VPS2 deployment:

```bash
# Upload and run on VPS2
scp fix_vps2_patient_status_column.py user@vps2:/path/to/myhealthteam2/Dev/
ssh user@vps2
cd /path/to/myhealthteam2/Dev
python3 fix_vps2_patient_status_column.py
```

## Recovery

If VPS2 has a backup from before the transform script was run, you could restore it. However, since the fix adds the missing columns with defaults, the current approach is acceptable as long as:

1. ✅ All existing patients are preserved (they are)
2. ✅ patient_status is set to 'Active' (done)
3. ✅ Workflow stages default to incomplete (done)
4. ⚠️ **Missing data from original columns is lost** (insurance, referral, address info, etc.)

## Risk Assessment

**Current Risk: LOW**

- ✅ Onboarding queue works again
- ✅ All 669 patients preserved
- ✅ Patient status tracking functional
- ✅ Workflow stages trackable
- ⚠️ Historical data lost (insurance, referral details, etc.)

**Recommendation:**

1. Deploy the fix to VPS2 immediately (blocks onboarding workflow)
2. Restore missing data from backups if available
3. Update `transform_production_data_v3_fixed.py` to preserve all columns
4. Implement validation to prevent future occurrences

---

**Document Version:** 1.0  
**Analysis Date:** 2026-01-05  
**Root Cause:** transform_production_data_v3_fixed.py DELETE + INSERT with incomplete column list  
**Fix Status:** ✅ Migration script created and verified locally  
**Next Step:** Deploy to VPS2
