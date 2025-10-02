# Patient ID Format Analysis

## Overview
This document catalogs the different patient_id formats found across tables in the production database, which is causing foreign key integrity failures and data inconsistencies.

## Discovered Format Patterns

### Pattern 1: "LASTNAME FIRSTNAME MM/DD/YYYY" (No comma)
**Tables using this format:**
- `patients` (reference table)
- `patient_panel` 
- `patient_visits`

**Examples:**
- `PASTION PERRY 07/13/1955`
- `LARSON JENNIFER 03/01/1946`
- `ABROLE VIDYA 12/03/1942`

### Pattern 2: "LASTNAME, FIRSTNAME MM/DD/YYYY" (With comma)
**Tables using this format:**
- `coordinator_tasks`
- `provider_tasks`

**Examples:**
- `KNAPPIK, OLGA 07/22/1936`
- `FERNANDEZ, ROBERTO 10/14/1932`
- `MCNEILL, MICHELE 06/08/1953`

### Pattern 3: Test/Generated IDs
**Tables using this format:**
- `coordinator_tasks_2025_10`
- `provider_tasks_2025_10`

**Examples:**
- `TEST_PAT_20251001_014556`
- `TEST_PROV_VISIT_20251001_094153`
- `TEST_PROV_PHONE_20251001_094153`

### Pattern 4: Numeric IDs
**Tables using this format:**
- `coordinator_tasks_2024_12` (and likely other 2024 tables)

**Examples:**
- `669`
- `676`
- `784`

### Pattern 5: Mixed Format (September 2025)
**Tables using this format:**
- `coordinator_tasks_2025_09`
- `provider_tasks_2025_09`

**Examples:**
- `ROBLES ANAYA RAMON 11/28/1942` (Pattern 1 format)
- `SHAKNISAN MORVARID 04/08/1923`

## Critical Findings

**SEVERITY: HIGH** - The patient_id format inconsistencies are more extensive than initially identified:

1. **Five Different Formats**: At least 5 distinct patient_id formats exist across tables
2. **Historical Data Issues**: 2024 tables use completely different numeric IDs
3. **Recent Migration Issues**: 2025 tables show inconsistent migration patterns
4. **Empty Dashboard Tables**: Key dashboard tables are unpopulated, suggesting broken data pipelines

## Impact Analysis

### Foreign Key Failures
The format inconsistency between Pattern 1 (patients table) and Pattern 2 (task tables) means:
- Foreign key constraints fail because `PASTION PERRY 07/13/1955` ≠ `PASTION, PERRY 07/13/1955`
- Data integrity checks cannot validate relationships
- Joins between tables require complex string manipulation

### Affected Table Relationships
1. **patients** → **coordinator_tasks**: Format mismatch (no comma vs comma)
2. **patients** → **provider_tasks**: Format mismatch (no comma vs comma)
3. **patients** → **patient_panel**: Format match (both no comma)
4. **patients** → **patient_visits**: Format match (both no comma)

## Tables Requiring Investigation

### Core Tables ✓ (Analyzed)
- [x] patients
- [x] coordinator_tasks  
- [x] provider_tasks
- [x] patient_panel
- [x] patient_visits

### Monthly Tables (Partial Analysis)
- [x] coordinator_tasks_2025_10 (test data format)
- [x] provider_tasks_2025_10 (test data format)
- [ ] coordinator_tasks_2025_01 through 2025_09
- [ ] provider_tasks_2025_01 through 2025_09
- [ ] All 2024 monthly tables

### Dashboard Tables ✓ (Analyzed)
- [x] dashboard_patient_county_map (EMPTY - 0 records)
- [ ] dashboard_patient_zip_map
- [ ] dashboard_region_patient_assignment_summary
- [ ] dashboard_task_summary

### Backup/Archive Tables (Not Yet Analyzed)
- [ ] patients_backup
- [ ] patients_old
- [ ] coordinator_tasks_archive
- [ ] provider_tasks_backup
- [ ] patient_panel_old

## Recommended Actions

### Immediate Priority
1. **Standardize Core Tables**: Convert all patient_id values to consistent format
2. **Choose Standard Format**: Recommend Pattern 1 (no comma) as it matches the patients table
3. **Update Task Tables**: Convert coordinator_tasks and provider_tasks to use no-comma format

### Medium Priority
1. **Audit Monthly Tables**: Check all monthly tables for format consistency
2. **Update Dashboard Tables**: Ensure dashboard tables use standard format
3. **Re-enable Foreign Keys**: After standardization, re-enable foreign key constraints

### Long Term
1. **Implement Validation**: Add database constraints to prevent format inconsistencies
2. **Update Import Scripts**: Ensure all data import processes use standard format
3. **Create Migration Scripts**: Automate format standardization for future data

## Status
- **Analysis Started**: 2025-01-01
- **Core Tables**: Analyzed ✓
- **Monthly Tables**: Partial (2025-10 only)
- **Dashboard Tables**: Pending
- **Backup Tables**: Pending