# Quick Fix Reference - My Patients Blank Tables

## Problem
My Patients tables show blank regardless of filter selections in Provider and Coordinator dashboards.

## Root Cause
**Type mismatch in filtering logic:** Provider/Coordinator IDs being compared as strings when they should be integers.

```python
# BROKEN: str(9.0) = "9.0" ≠ "9"
if str(p["provider_id"]) in ["9", "2", "4"]:  # Never matches!

# FIXED: int(9.0) = 9 == 9
if int(p["provider_id"]) in [9, 2, 4]:  # Matches correctly!
```

## Files Changed

### 1. Dev/src/database.py (Line 3779)
```python
# BEFORE
query = "SELECT * FROM patient_panel"

# AFTER
query = """
SELECT
    p.*,
    COALESCE(pa.provider_id, NULL) as provider_id,
    COALESCE(pa.coordinator_id, NULL) as coordinator_id,
    u_prov.full_name as provider_name,
    u_coord.full_name as coordinator_name
FROM patients p
LEFT JOIN patient_assignments pa ON p.patient_id = pa.patient_id AND pa.status = 'active'
LEFT JOIN users u_prov ON pa.provider_id = u_prov.user_id
LEFT JOIN users u_coord ON pa.coordinator_id = u_coord.user_id
"""
df = pd.read_sql_query(query, conn)
df = df.where(pd.notnull(df), None)  # Replace NaN with None
return df.to_dict(orient="records")
```

### 2. Dev/src/dashboards/care_provider_dashboard_enhanced.py

**Line 18: Add import**
```python
import pandas as pd
```

**Lines 676-717: Fix filtering**
```python
# BEFORE
selected_provider_ids.append(str(provider_id))
...
filtered_patients = [
    p for p in filtered_patients
    if str(p.get("provider_id", "")) in selected_provider_ids
]

# AFTER
selected_provider_ids.append(int(provider_id))
...
filtered_by_provider = []
for p in filtered_patients:
    pid = p.get("provider_id")
    apid = p.get("assigned_provider_id")
    try:
        if pd.isna(pid):
            pid = None
        if pd.isna(apid):
            apid = None
        if (pid is not None and int(pid) in selected_provider_ids) or (
            apid is not None and int(apid) in selected_provider_ids
        ):
            filtered_by_provider.append(p)
    except (ValueError, TypeError):
        pass
filtered_patients = filtered_by_provider
```

**Lines 785-788: Fix column names**
```python
# BEFORE
("phone_medical", "MED POC"),
("phone_appointment", "Appt POC"),
("phone_medical_number", "Med phone #"),
("phone_appointment_number", "Appt phone #"),

# AFTER
("medical_contact_name", "Med POC"),
("appointment_contact_name", "Appt POC"),
("medical_contact_phone", "Med Phone"),
("appointment_contact_phone", "Appt Phone"),
```

### 3. Dev/src/dashboards/care_coordinator_dashboard_enhanced.py

**Lines 1250-1269: Fix filtering**
```python
# BEFORE
selected_coord_ids.append(str(coord_id))
...
filtered_patients = [
    p for p in filtered_patients
    if str(p.get("assigned_coordinator_id", "")) in selected_coord_ids
]

# AFTER
selected_coord_ids.append(int(coord_id))
...
filtered_by_coord = []
for p in filtered_patients:
    coord_id = p.get("assigned_coordinator_id")
    try:
        if pd.isna(coord_id):
            coord_id = None
        if coord_id is not None and int(coord_id) in selected_coord_ids:
            filtered_by_coord.append(p)
    except (ValueError, TypeError):
        pass
filtered_patients = filtered_by_coord
```

## Test Results
After fix:
- Provider 2: 195 patients ✓
- Provider 4: 51 patients ✓
- Provider 9: 39 patients ✓
- Provider 10: 64 patients ✓
- (and so on...)

## Key Points
1. Always use integer comparison for IDs: `int(id1) == int(id2)`
2. Handle pandas NaN with `pd.isna()` before type conversion
3. Database provider_id comes as float (9.0), not string ("9")
4. Empty list means filter logic broke, not missing data