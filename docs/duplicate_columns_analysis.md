# Duplicate Columns Analysis

This document analyzes columns that appear in multiple patient-related tables to identify data redundancy and consolidation opportunities.

## Tables Analyzed

- `patients` - Master patient table (source of truth)
- `patient_panel` - Denormalized view for dashboards (performance optimized)
- `onboarding_patients` - Patient onboarding data
- `patient_assignments` - Current coordinator/provider assignments
- `patient_assignment_history` - Assignment change tracking
- `patient_visits` - Visit records

## Summary

- **Total columns with duplicates**: 90
- **Total unique columns analyzed**: 157
- **Percentage of columns duplicated**: ~57%

---

## Columns Appearing in 6 Tables (Universal Identifiers)

| Column | Tables |
|--------|--------|
| `patient_id` | patients, patient_panel, onboarding_patients, patient_assignments, patient_assignment_history, patient_visits |

**Note**: `patient_id` is the primary key and correctly appears in all tables.

---

## Top 20 Most Common Columns

1. `patient_id` (6 tables)
2. `first_name` (3 tables)
3. `last_name` (3 tables)
4. `date_of_birth` (3 tables)
5. `phone_primary` (3 tables)
6. `created_date` (3 tables)
7. `updated_date` (3 tables)
8. `mental_health_concerns` (3 tables)
9. `status` (3 tables)
10. `last_visit_date` (3 tables)
11. `service_type` (3 tables)
12. `appointment_contact_name` (3 tables)
13. `appointment_contact_phone` (3 tables)
14. `medical_contact_name` (3 tables)
15. `medical_contact_phone` (3 tables)
16. `transportation` (3 tables)
17. `preferred_language` (3 tables)
18. `gender` (2 tables)
19. `email` (2 tables)
20. `address_street` (2 tables)

---

## Critical ZMO Columns

### Assignment-Related
| Column | Tables | Purpose |
|--------|--------|---------|
| `provider_id` | patient_panel, patient_assignments | Current provider |
| `coordinator_id` | patient_panel, patient_assignments | Current coordinator |
| `provider_name` | patient_panel | Display name (denormalized) |
| `coordinator_name` | patient_panel | Display name (denormalized) |

### Notes Columns (Editable in ZMO)
| Column | Tables | Updates To |
|--------|--------|-----------|
| `labs_notes` | patients, patient_panel | Both tables |
| `imaging_notes` | patients, patient_panel | Both tables |
| `general_notes` | patients, patient_panel | Both tables |
| `next_appointment_date` | patients, patient_panel | Both tables |

### Cascade Update Targets
When `provider_name` or `coordinator_name` is edited:
- `patient_panel` table
- `workflow_instances` table
- All `coordinator_tasks_*` tables
- All `provider_tasks_*` tables
- Monthly summary tables

---

## Key Insights

### Three-Tier Architecture

```
patients (master source)
    ↓
patient_panel (denormalized view for dashboards)
    ↓
onboarding_patients (onboarding workflow)
patient_assignments (current assignments)
```

### Data Synchronization

1. **patients** = source of truth
2. **patient_panel** = rebuilt during ETL refresh
3. **onboarding_patients** = synced during onboarding
4. **patient_assignments** = live assignment tracking

### Why Duplicates Exist

- Performance: Denormalized `patient_panel` avoids JOINs
- Convenience: Display names stored for easy UI
- History: `patient_assignment_history` tracks changes
- Workflow: `onboarding_patients` separate for intake process
