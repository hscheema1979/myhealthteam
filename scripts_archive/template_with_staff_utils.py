#!/usr/bin/env python3
"""
Template: Updated Import Script Using Staff Utils
This shows how to refactor existing transfer scripts to use the centralized staff_codes table.
"""

import sqlite3
import os
from staff_utils import staff_manager, get_coordinator_code, get_provider_code

def transfer_with_staff_utilities():
    """Template showing how to use staff utilities in transfer scripts"""

    print("📤 TRANSFER WITH STAFF UTILITIES")
    print("=" * 50)

    # Connect to databases
    staging_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'staging.db')
    production_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'production.db')

    staging_conn = sqlite3.connect(staging_db)
    production_conn = sqlite3.connect(production_db)

    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()

    # Example 1: Fetch coordinator tasks and map using staff utilities
    print("\n👩‍💼 COORDINATOR TASKS TRANSFER (Using Staff Utils)")
    print("-" * 50)

    # Get staging data
    staging_cursor.execute("""
        SELECT coordinator_name, patient_name, patient_id, task_description, minutes_of_service, task_date
        FROM coordinator_tasks_staging
        WHERE source_system = 'staging_october_2025'
        LIMIT 5
    """)

    mapped_records = 0
    errors = 0

    for row in staging_cursor.fetchall():
        coordinator_name, patient_name, patient_id, task_description, minutes, task_date = row

        # Use staff utilities to get coordinator code
        coordinator_code = get_coordinator_code(coordinator_name)

        if coordinator_code:
            print(f"   ✅ {coordinator_name} → {coordinator_code}")

            # Example: Insert to production using mapped coordinator code
            # production_cursor.execute("""
            #     INSERT INTO coordinator_tasks (coordinator_code, patient_name, patient_id, ...)
            #     VALUES (?, ?, ?, ...)
            # """, (coordinator_code, patient_name, patient_id, ...))

            mapped_records += 1
        else:
            print(f"   ❌ {coordinator_name} - No coordinator code found")
            errors += 1

    print(f"   📊 Result: {mapped_records} mapped, {errors} errors")

    # Example 2: Fetch provider tasks and map using staff utilities
    print("\n👨‍⚕️ PROVIDER TASKS TRANSFER (Using Staff Utils)")
    print("-" * 50)

    # Get staging data
    staging_cursor.execute("""
        SELECT provider_name, patient_name, patient_id, service, billing_code, minutes_raw, activity_date
        FROM provider_tasks_staging
        WHERE source_system = 'staging_october_2025'
        LIMIT 5
    """)

    provider_mapped = 0
    provider_errors = 0

    for row in staging_cursor.fetchall():
        provider_name, patient_name, patient_id, service, billing_code, minutes, activity_date = row

        # Use staff utilities to get provider code
        provider_code = get_provider_code(provider_name)

        if provider_code:
            print(f"   ✅ {provider_name} → {provider_code}")

            # Example: Insert to production using mapped provider code
            # production_cursor.execute("""
            #     INSERT INTO provider_tasks (provider_name, patient_name, patient_id, ...)
            #     VALUES (?, ?, ?, ...)
            # """, (provider_name, patient_name, patient_id, ...))

            provider_mapped += 1
        else:
            print(f"   ❌ {provider_name} - No provider code found")
            provider_errors += 1

    print(f"   📊 Result: {provider_mapped} mapped, {provider_errors} errors")

    # Example 3: Validate staff codes before transfer
    print("\n🔍 STAFF CODE VALIDATION")
    print("-" * 50)

    # Check if we can validate codes we're about to use
    all_staff = staff_manager.get_all_staff()
    print(f"   📋 Total staff in database: {len(all_staff)}")

    # Show a few coordinator codes that will be validated
    staging_cursor.execute("SELECT DISTINCT coordinator_name FROM coordinator_tasks_staging LIMIT 3")
    sample_coords = staging_cursor.fetchall()

    for (coord_name,) in sample_coords:
        coord_code = get_coordinator_code(coord_name)
        if coord_code:
            is_valid = staff_manager.validate_coordinator_code(coord_code)
            print(f"   ✅ {coord_name} → {coord_code} (valid: {is_valid})")
        else:
            print(f"   ❌ {coord_name} - No code found")

    # Example 4: Adding new staff (future use case)
    print("\n➕ EXAMPLE: Adding New Staff")
    print("-" * 50)
    print("   # To add new staff member:")
    print("   staff_manager.add_staff_member(")
    print("       'John Doe', 'john@myhealthteam.org',")
    print("       'DOEJO000', 'Doe, John', 'Doe, John'")
    print("   )")

    staging_conn.close()
    production_conn.close()

    print(f"\n🎯 BENEFITS OF USING STAFF UTILITIES:")
    print(f"   • Single source of truth for all staff codes")
    print(f"   • Automatic validation before transfers")
    print(f"   • Easy staff additions/removals")
    print(f"   • Reduced hardcoding in scripts")
    print(f"   • Better error handling for unknown staff")

if __name__ == "__main__":
    transfer_with_staff_utilities()