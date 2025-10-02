# Patient ID Normalization Plan

## Executive Summary
This document outlines the strategy to normalize patient_id formats across all tables in the production database to restore foreign key integrity and fix the 70 failed workflow iterations.

## Current State Analysis
- **5 Different Formats** identified across tables
- **Foreign Key Failures** due to format mismatches
- **Test Data Corruption** in October 2025 tables
- **Empty Dashboard Tables** due to broken relationships

## Normalization Strategy

### 1. Standard Format Selection
**Chosen Standard:** `LASTNAME FIRSTNAME MM/DD/YYYY`
- **Rationale:** Used by `patients` table (reference table), `patient_panel`, and `patient_visits`
- **Benefits:** Maintains consistency with core patient data
- **Format:** No comma between last and first name

### 2. Transformation Rules

#### Rule 1: Remove Comma Format
- **From:** `LASTNAME, FIRSTNAME MM/DD/YYYY`
- **To:** `LASTNAME FIRSTNAME MM/DD/YYYY`
- **SQL:** `REPLACE(patient_id, ', ', ' ')`
- **Affected Tables:** `coordinator_tasks`, `provider_tasks`

#### Rule 2: Handle Test Data
- **Pattern:** `TEST_*_YYYYMMDD_HHMMSS`
- **Action:** Remove all test records from production tables
- **Affected Tables:** `coordinator_tasks_2025_10`, `provider_tasks_2025_10`

#### Rule 3: Handle Numeric IDs
- **Pattern:** Numeric only (e.g., "669", "676")
- **Action:** Mark for manual review - these may be legacy IDs
- **Affected Tables:** `coordinator_tasks_2024_12`

#### Rule 4: Handle Mixed Formats
- **Pattern:** `FIRSTNAME MIDDLENAME LASTNAME MM/DD/YYYY`
- **Action:** Standardize to `LASTNAME FIRSTNAME MM/DD/YYYY` format
- **Affected Tables:** `coordinator_tasks_2025_09`, `provider_tasks_2025_09`

### 3. Implementation Priority

#### Phase 1: Critical Tables (Immediate)
1. `coordinator_tasks` - Remove comma format
2. `provider_tasks` - Remove comma format
3. `coordinator_tasks_2025_10` - Remove test data
4. `provider_tasks_2025_10` - Remove test data

#### Phase 2: Monthly Tables (Medium Priority)
1. `coordinator_tasks_2025_09` - Standardize format
2. `provider_tasks_2025_09` - Standardize format

#### Phase 3: Historical Tables (Low Priority)
1. `coordinator_tasks_2024_12` - Manual review of numeric IDs

### 4. Validation Strategy

#### Pre-Normalization Checks
- Count records in each table
- Sample patient_id formats
- Verify backup creation

#### Post-Normalization Validation
- Verify format consistency
- Test foreign key relationships
- Validate workflow execution
- Check dashboard data population

### 5. Rollback Plan
- Backup created: `production_backup_YYYYMMDD_HHMMSS.db`
- Rollback command: `Copy-Item "production_backup_*.db" "production.db"`
- Validation after rollback: Run schema checks

### 6. Risk Assessment

#### High Risk
- Data loss during transformation
- Breaking existing workflows during transition

#### Mitigation
- Complete backup before changes
- Test transformations on sample data
- Incremental validation after each phase

#### Low Risk
- Format standardization (reversible)
- Test data removal (improves data quality)

## Success Criteria
1. All patient_id formats follow `LASTNAME FIRSTNAME MM/DD/YYYY` standard
2. Foreign key constraints can be re-enabled without errors
3. Workflow success rate improves from 0% to >90%
4. Dashboard tables populate correctly
5. No data loss in production patient records

## Next Steps
1. Create SQL transformation scripts
2. Execute Phase 1 transformations
3. Validate results
4. Proceed to Phase 2 if successful