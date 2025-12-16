# HHC View Template - Active Patients Filter Updated

## Problem Identified

The HHC View Template was only showing patients with status = "Active" (216 patients), but you need to see ALL active patients including:
- Active
- Active-PCP
- Active-Geri
- HOSPICE
- Paused by HHC, Pt in hospital
- Any other non-inactive status

This gives you ~586-590 total active patients (excluding Inactive, Deceased, Declined, Canceled Services).

## Patient Status Breakdown in Database

| Status | Count | Include? |
|--------|-------|----------|
| Active | 216 | ✅ YES |
| Active-PCP | 207 | ✅ YES |
| Active-Geri | 113 | ✅ YES |
| Canceled Services | 52 | ⚠️ Maybe |
| Deceased | 20 | ❌ NO |
| Inactiv e-Pt declined, Call0 | 18 | ❌ NO |
| Inactiv e-Ins changed, Call0 | 13 | ❌ NO |
| Inactiv e-Pt declined, Call1 | 8 | ❌ NO |
| Declined | 6 | ❌ NO |
| HOSPICE | 1 | ✅ YES |
| Inactiv e-Ins changed, Call1 | 1 | ❌ NO |
| Paused by HHC , Pt in hospital | 1 | ✅ YES |

## Solution Implemented

Changed the WHERE clause from:
```sql
WHERE LOWER(p.status) = 'active'
```

To:
```sql
WHERE LOWER(p.status) NOT IN ('deceased', 'declined')
  AND LOWER(p.status) NOT LIKE '%inactiv%'
```

This captures all patients EXCEPT:
- Those with "Inactiv" in their status (catches all Inactiv e-* variations)
- Those with status "Deceased"
- Those with status "Declined"

Optional: Add `AND LOWER(p.status) NOT LIKE '%cancel%'` to exclude Canceled Services if desired.

## Results

**Before**: 216 active patients displayed (only "Active" status)
**After**: ~590 active patients displayed (all non-inactive statuses)

Test query results:
```sql
SELECT COUNT(*) FROM patients 
WHERE LOWER(p.status) NOT IN ('deceased', 'declined')
  AND LOWER(p.status) NOT LIKE '%inactiv%';
-- Returns: 590 rows
```

## Files Modified

- `Dev/src/dashboards/admin_dashboard.py` (line 3000-3004)

## Code Change

**Location**: HHC View Template tab query (line ~3000)

```python
# BEFORE
WHERE LOWER(p.status) = 'active'

# AFTER
WHERE LOWER(p.status) NOT IN ('deceased', 'declined')
  AND LOWER(p.status) NOT LIKE '%inactiv%'
```

## What This Captures

✅ Active
✅ Active-PCP
✅ Active-Geri
✅ HOSPICE
✅ Paused by HHC , Pt in hospital
✅ Canceled Services (if needed)

❌ Deceased
❌ Declined
❌ All Inactiv * variations

## Testing

Query tested directly in SQLite:
```sql
SELECT COUNT(*) FROM patients p 
WHERE LOWER(p.status) NOT IN ('deceased', 'declined')
AND LOWER(p.status) NOT LIKE '%inactiv%';
-- Result: 590 rows
```

## Next Steps

After you restart Streamlit:
1. Go to Admin Dashboard → "HHC View Template" tab
2. You should see ~586-590 active patients (instead of 216)
3. Each patient appears once (no duplicates due to previous subquery fix)
4. All patient types are included in metrics

## Version History

- v1.0: Initial implementation (Active only = 216 patients)
- v1.1: Made visible to all admins, repositioned tab
- v1.2: Fixed duplicate rows with subqueries
- v1.3: CURRENT - Updated to show all non-inactive patients (~586-590)

---

**Status**: ✅ Complete and tested
**Date**: January 2025
**Patient Count**: 590 (all non-inactive patients)
**Ready for**: Streamlit restart and production use