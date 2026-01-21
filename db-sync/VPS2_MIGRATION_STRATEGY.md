# VPS2 Production Migration Strategy
## Complete Data Architecture Migration - Safe & Clean

**Date:** 2026-01-20
**Goal:** Migrate VPS2 to new architecture with csv_* billing tables and clean operational tables

---

## Current State Analysis

### Local (Dev/SRVR) - Already Migrated
| Component | State | Details |
|-----------|-------|---------|
| csv_* tables | ✅ Complete | 48 tables, billing source of truth |
| Operational tables (2026) | ✅ Clean | coordinator_tasks: 0, provider_tasks: 755 (manual only) |
| Operational tables (pre-2026) | ✅ Clean | All CSV data removed |
| source_system column | ✅ Added | Distinguishes CSV vs manual data |

### VPS2 (Production) - Needs Migration
| Component | State | Details |
|-----------|-------|---------|
| csv_* tables | ❌ Don't exist | Need to create and populate |
| Operational tables (2026_01) | ⚠️ Mixed | coordinator: 1,191, provider: 279 (Laura's live data) |
| Operational tables (pre-2026) | ⚠️ CSV data | ~37K records (coordinator: 28K+, provider: 6K+) |
| source_system column | ❌ Missing | Cannot distinguish CSV vs manual |
| Views (coordinator_tasks) | ⚠️ Outdated | Missing 2025_12 and 2026_01 |
| Views (provider_tasks) | ⚠️ Outdated | Missing 2025_12 and 2026_01 |

---

## Migration Strategy

### Phase 1: Preparation (On Dev/SRVR)
**Goal:** Prepare migration scripts and verify data integrity

1. ✅ **Already Complete:**
   - csv_* tables created and populated
   - Local operational tables cleaned
   - Sync scripts created
   - Cleanup scripts created

### Phase 2: Pre-Migration Backup (On VPS2)
**Goal:** Create fallback point

```sql
-- Create backup before any changes
BACKUP: /opt/myhealthteam/backups/production_pre_migration_YYYYMMDD_HHMMSS.db
```

### Phase 3: Schema Updates (On VPS2)
**Goal:** Add missing columns and create csv_* tables

3.1 **Add source_system column to operational tables**
```sql
-- Add source_system column to all existing operational tables
-- Default NULL = legacy data (pre-migration)
-- Future entries will have 'DASHBOARD', 'MANUAL', 'WORKFLOW', etc.
```

3.2 **Create csv_* tables structure**
```sql
-- Run create_csv_billing_tables.sql to create all csv_* tables
-- These will be populated via sync from Dev
```

### Phase 4: Data Migration (On VPS2)
**Goal:** Move data to correct tables

4.1 **Migrate CSV data from operational to csv_* tables**
```sql
-- For 2025 and earlier: Copy data to csv_* tables
-- This preserves data before we delete from operational tables
-- Approach: Use data from Dev (more reliable) or copy from VPS2 operational
```

4.2 **Mark existing data with source_system**
```sql
-- For 2026_01 tables:
--   - All existing records marked as source_system = 'DASHBOARD' (Laura's data)
--   - Any CSV data will be replaced/handled separately
```

### Phase 5: Cleanup (On VPS2)
**Goal:** Remove duplication

5.1 **Delete CSV data from pre-2026 operational tables**
```sql
-- Delete all records from 2025 and earlier tables
-- This data now lives in csv_* tables
```

5.2 **Update views to include 2026_01 tables**
```sql
-- Recreate coordinator_tasks view (include 2025_12, 2026_01)
-- Recreate provider_tasks view (include 2025_12, 2026_01)
```

### Phase 6: Billing System Update (On VPS2)
**Goal:** Billing uses csv_* tables

6.1 **Update billing queries to use csv_* tables**
   - Coordinator billing: Use csv_coordinator_tasks_*
   - Provider billing: Use csv_provider_tasks_*

6.2 **Rebuild billing summary tables**
   - Run post-import processing to update summaries

### Phase 7: Verification (On VPS2)
**Goal:** Confirm everything works

7.1 **Data Integrity Checks**
```sql
-- Verify Laura's 2026 data preserved
-- Verify csv_* tables have correct data
-- Verify counts match Dev database
```

7.2 **Functional Checks**
- Test coordinator dashboard
- Test provider dashboard
- Test billing reports
- Test payroll calculations

---

## Detailed Migration Script

### Step 1: Backup
```powershell
ssh server2 "cp /opt/myhealthteam/production.db /opt/myhealthteam/backups/production_pre_migration_$(date +%Y%m%d_%H%M%S).db"
```

### Step 2: Add source_system column
```sql
-- Run on VPS2
BEGIN;

-- Add source_system column to all operational tables
ALTER TABLE coordinator_tasks_2026_01 ADD COLUMN source_system TEXT DEFAULT 'DASHBOARD';
ALTER TABLE provider_tasks_2026_01 ADD COLUMN source_system TEXT DEFAULT 'DASHBOARD';

-- For older tables, mark as CSV (they'll be deleted anyway)
ALTER TABLE coordinator_tasks_2025_12 ADD COLUMN source_system TEXT DEFAULT 'CSV_IMPORT';
-- (repeat for all 2025 tables)

COMMIT;
```

### Step 3: Sync csv_* tables
```powershell
# From Dev/SRVR
.\db-sync\bin\test_sync_safely.ps1 -ReallySync
```

### Step 4: Update views
```sql
-- Run on VPS2
DROP VIEW IF EXISTS coordinator_tasks;
CREATE VIEW coordinator_tasks AS
SELECT * FROM coordinator_tasks_2022_01
UNION ALL SELECT * FROM coordinator_tasks_2025_01
-- ... all 2025 tables ...
UNION ALL SELECT * FROM coordinator_tasks_2025_12
UNION ALL SELECT * FROM coordinator_tasks_2026_01;  -- NEW

-- Similar for provider_tasks view
```

### Step 5: Cleanup old data
```powershell
# From Dev/SRVR
.\db-sync\bin\test_sync_safely.ps1 -ReallySync -AlsoCleanup
```

### Step 6: Rebuild summaries
```sql
-- Run post_import_processing.sql on VPS2
```

---

## Risk Assessment & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Laura's data loss | Low | High | Backup created; verification script; manual confirmation required |
| Billing discrepancies | Medium | High | Use csv_* tables as source of truth; rebuild summaries after migration |
| View breakage | Medium | Medium | Update views immediately after schema changes |
| Application errors | Low | Medium | Test all dashboards after migration |

---

## Rollback Plan

If anything goes wrong:

```powershell
# Restore from backup
ssh server2 "cp /opt/myhealthteam/backups/production_pre_migration_YYYYMMDD_HHMMSS.db /opt/myhealthteam/production.db"

# Or use the restore script
.\db-sync\bin\restore_vps2_backup.ps1
```

---

## Post-Migration State

### VPS2 After Migration
| Component | State |
|-----------|-------|
| csv_* tables | ✅ Billing source of truth (48 tables) |
| Operational tables (2026_01) | ✅ Laura's live data only |
| Operational tables (pre-2026) | ✅ Empty (CSV data in csv_* tables) |
| source_system column | ✅ Added (DASHBOARD, MANUAL, WORKFLOW) |
| Views (coordinator_tasks) | ✅ Updated to include 2026_01 |
| Views (provider_tasks) | ✅ Updated to include 2026_01 |
| Billing summaries | ✅ Rebuilt from csv_* tables |

---

## Execution Checklist

- [ ] 1. Create pre-migration backup on VPS2
- [ ] 2. Add source_system column to VPS2 operational tables
- [ ] 3. Create csv_* table structures on VPS2
- [ ] 4. Sync csv_* data from Dev to VPS2
- [ ] 5. Update coordinator_tasks view on VPS2
- [ ] 6. Update provider_tasks view on VPS2
- [ ] 7. Cleanup pre-2026 operational tables on VPS2
- [ ] 8. Rebuild billing/payroll summaries on VPS2
- [ ] 9. Verify Laura's data (coordinator_tasks_2026_01: 1,191 records)
- [ ] 10. Verify csv_* tables populated correctly
- [ ] 11. Test coordinator dashboard
- [ ] 12. Test provider dashboard
- [ ] 13. Test billing reports
- [ ] 14. Test payroll calculations

---

## Files Created/Modified

### New Migration Files
1. `db-sync/bin/migration_phase1_add_source_system.sql` - Add source_system column
2. `db-sync/bin/migration_phase2_update_views.sql` - Update views for 2026
3. `db-sync/bin/migration_phase3_rebuild_summaries.sql` - Rebuild billing summaries
4. `db-sync/bin/run_full_migration.ps1` - Orchestrates all phases

### Existing Files (Created Previously)
1. `db-sync/bin/sync_csv_billing_tables.ps1` - Sync csv_* tables
2. `db-sync/bin/cleanup_vps2_operational_tables.sql` - Cleanup old data
3. `db-sync/bin/test_sync_safely.ps1` - Safe sync with backup
4. `db-sync/bin/restore_vps2_backup.ps1` - Quick restore

---

## Notes

- **Laura's data safety:** All 1,191 + 279 records in 2026_01 tables are marked as DASHBOARD source
- **Billing accuracy:** csv_* tables are the single source of truth for billing
- **Future data flow:** New entries go to operational tables, CSV imports go to csv_* tables
- **Payroll:** Calculated from csv_* tables for billing accuracy
