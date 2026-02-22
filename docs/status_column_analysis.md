# Status Column Analysis - Patient Tables

## Summary

Analysis of the `status` column across 4 patient-related tables revealing:
- **22 unique status values** across all tables
- **Data quality issues** with typos and inconsistent casing
- **756 total patients** in both `patients` and `patient_panel`

---

## Status Values by Table

### patients Table (756 patients)

| Status | Count | % | Category |
|--------|-------|---|----------|
| Active-PCP | 229 | 30.3% | Active |
| Active | 222 | 29.4% | Active |
| Active-Geri | 155 | 20.5% | Active |
| Canceled Services | 73 | 9.7% | Inactive |
| Deceased | 25 | 3.3% | Inactive |
| Inactiv e-Pt declined, Call0 | 18 | 2.4% | Inactive (typo) |
| Inactiv e-Ins changed, Call0 | 13 | 1.7% | Inactive (typo) |
| Inactiv e-Pt declined, Call1 | 9 | 1.2% | Inactive (typo) |
| Declined | 8 | 1.1% | Inactive |
| HOSPICE | 2 | 0.3% | Active |
| Inactiv e-Ins changed, Call1 | 1 | 0.1% | Inactive (typo) |
| Paused by HHC , Pt in hospital | 1 | 0.1% | Inactive |

### patient_panel Table (756 patients)

| Status | Count | % | Category |
|--------|-------|---|----------|
| Active-PCP | 225 | 29.8% | Active |
| Active | 176 | 23.3% | Active |
| Active-Geri | 153 | 20.2% | Active |
| Canceled Services | 73 | 9.7% | Inactive |
| **(empty)** | **38** | **5.0%** | **Missing** |
| Deceased | 28 | 3.7% | Inactive |
| Inactiv e-Pt declined, Call0 | 18 | 2.4% | Inactive (typo) |
| Inactiv e-Ins changed, Call0 | 12 | 1.6% | Inactive (typo) |
| Inactiv e-Pt declined, Call1 | 9 | 1.2% | Inactive (typo) |
| Declined | 8 | 1.1% | Inactive |
| Inactive | 4 | 0.5% | Inactive |
| Patient left practice | 3 | 0.4% | Inactive |
| HOSPICE | 2 | 0.3% | Active |
| **INACTIVE** | **2** | **0.3%** | **Case issue** |
| Cancelled Services | 1 | 0.1% | Inactive (case issue) |
| **DECEASED** | **1** | **0.1%** | **Case issue** |
| Inactiv e-Ins changed, Call1 | 1 | 0.1% | Inactive (typo) |
| Inactive - Cancelled Services | 1 | 0.1% | Inactive |
| Paused by HHC , Pt in hospital | 1 | 0.1% | Inactive |

### onboarding_patients Table (62 patients)

| patient_status | Count | % | Category |
|----------------|-------|---|----------|
| Completed | 45 | 72.6% | Completed |
| Active-Geri | 8 | 12.9% | Active |
| Active | 5 | 8.1% | Active |
| Active-PCP | 4 | 6.5% | Active |

### patient_assignments Table (760 patients)

| status | Count | % | Category |
|--------|-------|---|----------|
| active | 750 | 99.9% | Active |
| inactive | 10 | 1.3% | Inactive |

---

## Data Quality Issues

### 1. Typos (Extra Spaces in "Inactive")

**Current**: `Inactiv e-Pt declined, Call0`  
**Should be**: `Inactive-Pt declined, Call0`

**Current**: `Inactiv e-Ins changed, Call0`  
**Should be**: `Inactive-Ins changed, Call0`

**Current**: `Inactiv e-Pt declined, Call1`  
**Should be**: `Inactive-Pt declined, Call1`

**Current**: `Inactiv e-Ins changed, Call1`  
**Should be**: `Inactive-Ins changed, Call1`

**Affected**: 59 patients (31 in patients, 58 in patient_panel)

### 2. Inconsistent Casing

| Current | Should Be | Count (patient_panel) |
|---------|-----------|------------------------|
| HOSPICE | Hospice | 2 |
| INACTIVE | Inactive | 2 |
| Cancelled Services | Canceled Services | 1 |
| DECEASED | Deceased | 1 |

### 3. Empty Status Values

- **38 patients** in `patient_panel` have NULL/empty status
- These should likely be "Active" or another appropriate status

### 4. Redundant Status Values

Both "Inactive" and "Inactive - Cancelled Services" exist when they could be consolidated.

---

## Active Status Values (for ZMO Filtering)

The following should be considered **Active** patients:

- `Active` (222 patients)
- `Active-PCP` (229 patients)
- `Active-Geri` (155 patients)
- `HOSPICE` (2 patients)
- `Hospice` (should be standardized)

**Total Active**: 608 patients (80.4%)

---

## Inactive Status Values

The following are **Inactive** patients:

- `Canceled Services` (73 patients)
- `Deceased` (25 patients)
- `Declined` (8 patients)
- `Inactive` (4 patients)
- `Patient left practice` (3 patients)
- `Paused by HHC , Pt in hospital` (1 patient)
- Various "Inactive-" prefixed statuses

---

## Standardization Recommendations

### Priority 1: Fix Typos (Critical)

```sql
-- Fix "Inactiv e" typo
UPDATE patients SET status = REPLACE(status, 'Inactiv e', 'Inactive') WHERE status LIKE 'Inactiv e%';
UPDATE patient_panel SET status = REPLACE(status, 'Inactiv e', 'Inactive') WHERE status LIKE 'Inactiv e%';
```

### Priority 2: Standardize Casing

```sql
-- Standardize to title case
UPDATE patient_panel SET status = 'Hospice' WHERE status = 'HOSPICE';
UPDATE patient_panel SET status = 'Inactive' WHERE status = 'INACTIVE';
UPDATE patient_panel SET status = 'Deceased' WHERE status = 'DECEASED';
UPDATE patient_panel SET status = 'Canceled Services' WHERE status = 'Cancelled Services';
UPDATE patients SET status = 'Hospice' WHERE status = 'HOSPICE';
```

### Priority 3: Fill Empty Status Values

```sql
-- For 38 patients with empty status, investigate and set appropriate value
SELECT patient_id, first_name, last_name, status 
FROM patient_panel 
WHERE status IS NULL OR status = '';
```

---

## Status Definitions

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| `Active` | Standard active patient | None |
| `Active-PCP` | Assigned to PCP | None |
| `Active-Geri` | Geriatric patient | None |
| `Hospice` | Hospice care | Special handling |
| `Canceled Services` | Services canceled | May reactivate |
| `Deceased` | Patient passed away | Archive |
| `Declined` | Patient declined services | May reactivate |
| `Inactive` | General inactive status | May reactivate |
| `Patient left practice` | Left to other provider | Archive |
| `Paused by HHC` | Temporarily paused | Follow up needed |

---

## Impact on ZMO Module

### Current ZMO Filtering Logic

The ZMO module uses this logic to determine active patients:

```python
is_active = (
    status in active_statuses or  # ["Active", "Active-Geri", "Active-PCP", "Hospice", "HOSPICE"]
    status.startswith('Active') or  # Handles future Active-XXX types
    status.upper() == 'HOSPICE'     # Case-insensitive check
)
```

**This correctly handles**:
- Different Active types (Active, Active-PCP, Active-Geri)
- Case variations (HOSPICE, Hospice, hospice)
- Future Active-XXX statuses

**Issues to fix**:
- Typos with "Inactiv e" will be treated as Active (starts with "Inactiv") - BUG!
- Empty status values will not be Active - Correct behavior
- "Inactive" vs "INACTIVE" case differences - Handled by .upper()

---

## Generated

- **Date**: 2026-02-22
- **Database**: production.db (VPS2)
- **Total Patients Analyzed**: 756
