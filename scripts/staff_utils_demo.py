#!/usr/bin/env python3
"""
Staff Utils Demo - Shows the power of centralized staff code management
"""

import sqlite3
import os
from staff_utils import staff_manager, get_coordinator_code, get_provider_code, get_all_staff

def demo_staff_utilities():
    """Demonstrate the benefits of using staff utilities"""

    print("🎯 STAFF UTILITIES DEMONSTRATION")
    print("=" * 50)

    # Demo 1: Basic lookups
    print("\n📋 BASIC LOOKUPS")
    print("-" * 30)

    sample_names = ["Ethel Antonio", "Laura Sumpay CC", "Hector Hernandez"]
    for name in sample_names:
        coord_code = get_coordinator_code(name)
        provider_code = get_provider_code(name)
        print(f"   {name}:")
        print(f"     Coordinator: {coord_code}")
        print(f"     Provider: {provider_code}")

    # Demo 2: Staff validation
    print(f"\n✅ CODE VALIDATION")
    print("-" * 30)

    test_codes = ["ANTET000", "Sumpay, Laura", "NONEXISTENT", "SUMLA000"]
    for code in test_codes:
        coord_valid = staff_manager.validate_coordinator_code(code)
        provider_valid = staff_manager.validate_provider_code(code)
        print(f"   {code}:")
        print(f"     Coordinator valid: {coord_valid}")
        print(f"     Provider valid: {provider_valid}")

    # Demo 3: Reverse lookups
    print(f"\n🔍 REVERSE LOOKUPS")
    print("-" * 30)

    coord_code = "ANTET000"
    provider_code = "Sumpay, Laura"

    coord_staff = staff_manager.get_staff_by_coordinator_code(coord_code)
    provider_staff = staff_manager.get_staff_by_provider_code(provider_code)

    print(f"   Coordinator code '{coord_code}' belongs to: {coord_staff['full_name'] if coord_staff else 'Not found'}")
    print(f"   Provider code '{provider_code}' belongs to: {provider_staff['full_name'] if provider_staff else 'Not found'}")

    # Demo 4: All staff summary
    print(f"\n👥 STAFF SUMMARY")
    print("-" * 30)

    all_staff = get_all_staff()
    print(f"   Total staff members: {len(all_staff)}")

    # Show staff by category (those with CC or NP titles)
    cc_staff = [s for s in all_staff if 'CC' in s['full_name']]
    np_staff = [s for s in all_staff if 'NP' in s['full_name']]
    print(f"   Certified Coordinators (CC): {len(cc_staff)}")
    print(f"   Nurse Practitioners (NP): {len(np_staff)}")

    # Demo 5: Adding new staff
    print(f"\n➕ ADDING NEW STAFF (Simulated)")
    print("-" * 30)

    new_staff = {
        'full_name': 'Demo User',
        'email': 'demo@myhealthteam.org',
        'coordinator_code': 'DEMO000',
        'provider_code': 'Demo, User',
        'alt_provider_code': 'Demo, User'
    }

    print(f"   Adding: {new_staff['full_name']}")
    print(f"   Will be available for lookup after insert")
    print(f"   Use: staff_manager.add_staff_member(...)")

    # Demo 6: Error handling
    print(f"\n🚫 ERROR HANDLING")
    print("-" * 30)

    # Try to get codes for non-existent staff
    fake_staff = "Nonexistent Person"
    coord_code = get_coordinator_code(fake_staff)
    provider_code = get_provider_code(fake_staff)

    print(f"   Looking up '{fake_staff}':")
    print(f"     Coordinator code: {coord_code} (None means not found)")
    print(f"     Provider code: {provider_code} (None means not found)")

    print(f"\n🎯 KEY BENEFITS:")
    print(f"   ✅ Single source of truth for all staff codes")
    print(f"   ✅ Easy validation before data transfers")
    print(f"   ✅ Reverse lookups (code → staff name)")
    print(f"   ✅ Error handling for missing staff")
    print(f"   ✅ Simple API for scripts to use")
    print(f"   ✅ Consistent naming across staging/production")

    print(f"\n💡 USAGE IN SCRIPTS:")
    print(f"   from staff_utils import get_coordinator_code, get_provider_code")
    print(f"   coord_code = get_coordinator_code('Ethel Antonio')")
    print(f"   provider_code = get_provider_code('Hector Hernandez')")

if __name__ == "__main__":
    demo_staff_utilities()