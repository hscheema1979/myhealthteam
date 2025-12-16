import sys

sys.path.insert(0, "D:/Git/myhealthteam2/Dev")

import pandas as pd

from src import database

print("=" * 80)
print("TESTING COORDINATOR FILTERING LOGIC")
print("=" * 80)

# Get all patient data
print("\n1. Fetching all patient data...")
patient_data = database.get_all_patient_panel()
print(f"   Total patients: {len(patient_data)}")

# Get all coordinators
print("\n2. Fetching all coordinators...")
all_coordinators = database.get_users_by_role(36)  # 36 = Care Coordinator
print(f"   Total coordinators: {len(all_coordinators)}")
for coord in all_coordinators:
    print(f"      - ID {coord['user_id']}: {coord['full_name']} ({coord['username']})")

# Create coordinator map
print("\n3. Building coordinator map...")
coordinator_map = {}
for coordinator in all_coordinators:
    coord_name = coordinator.get("full_name", coordinator.get("username", "Unknown"))
    coord_id = coordinator.get("user_id")
    coordinator_map[coord_name] = coord_id
    print(f"   {coord_name} -> {coord_id}")

# Test filtering for each coordinator
print("\n4. Testing filter for each coordinator...")
for coordinator in all_coordinators:
    coord_name = coordinator.get("full_name", coordinator.get("username", "Unknown"))
    coord_id = coordinator.get("user_id")

    # Simulate the filtering logic from dashboard (corrected with int conversion)
    filtered = []
    for p in patient_data:
        coord_id_from_patient = p.get("assigned_coordinator_id")
        try:
            # Handle NaN values from pandas
            if pd.isna(coord_id_from_patient):
                coord_id_from_patient = None

            if coord_id_from_patient is not None and int(coord_id_from_patient) == int(
                coord_id
            ):
                filtered.append(p)
        except (ValueError, TypeError):
            pass

    print(f"\n   Coordinator: {coord_name} (ID: {coord_id})")
    print(f"   Patients assigned: {len(filtered)}")

    if filtered:
        print(f"   Sample patient:")
        sample = filtered[0]
        print(f"      - ID: {sample.get('patient_id')}")
        print(f"      - Name: {sample.get('first_name')} {sample.get('last_name')}")
        print(
            f"      - Coordinator ID in record: {sample.get('assigned_coordinator_id')}"
        )
        print(f"      - Status: {sample.get('status')}")

# Test with "All Coordinators" filter
print("\n5. Testing 'All Coordinators' filter...")
filtered_all = [p for p in patient_data if p.get("assigned_coordinator_id") is not None]
print(f"   Patients with coordinator assignment: {len(filtered_all)}")

# Check for patients with None coordinator_id
print("\n6. Patients without coordinator assignment...")
no_coord = [
    p
    for p in patient_data
    if p.get("assigned_coordinator_id") is None
    or (
        isinstance(p.get("assigned_coordinator_id"), float)
        and pd.isna(p.get("assigned_coordinator_id"))
    )
]
print(f"   Count: {len(no_coord)}")

# Test search functionality
print("\n7. Testing search by name...")
search_query = "Ada"
filtered_search = [
    p
    for p in patient_data
    if (
        search_query.lower() in str(p.get("patient_id", "")).lower()
        or search_query.lower()
        in f"{p.get('first_name', '')} {p.get('last_name', '')}".lower()
    )
]
print(f"   Search for '{search_query}': {len(filtered_search)} results")
if filtered_search:
    for p in filtered_search[:3]:
        print(
            f"      - {p.get('first_name')} {p.get('last_name')} (Coordinator: {p.get('coordinator_name', 'Unassigned')})"
        )

print("\n" + "=" * 80)
print("COORDINATOR FILTERING TEST COMPLETE")
print("=" * 80)
