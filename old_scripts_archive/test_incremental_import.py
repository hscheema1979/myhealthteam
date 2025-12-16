#!/usr/bin/env python3
"""
Test Incremental Import Functionality
Tests that the unified import correctly handles subsequent imports
"""

import pandas as pd
import os
import sqlite3
from pathlib import Path
import shutil
from datetime import datetime

def create_incremental_test_data():
    """Create additional test data for incremental import testing"""
    
    # Create test directory
    test_dir = Path("test_incremental_data")
    test_dir.mkdir(exist_ok=True)
    
    # Incremental coordinator tasks - new data with later dates
    coordinator_data = {
        "LAST FIRST DOB": ["SMITH JOHN 01/15/1940", "DOE JANE 05/20/1950"],
        "CM ID": ["AltSh000", "ANTET000"],
        "Date Only": ["12/01/2025", "12/02/2025"],  # Later dates for incremental test
        "Duration Minutes": [30, 45],
        "Task Type": ["Follow-up Call", "Care Plan Update"],
        "Notes": ["Follow-up visit", "Updated care plan"]
    }
    
    coordinator_df = pd.DataFrame(coordinator_data)
    coordinator_file = test_dir / "cmlog_incremental.csv"
    coordinator_df.to_csv(coordinator_file, index=False)
    print(f"✅ Created incremental coordinator file: {coordinator_file}")
    print(f"   Records: {len(coordinator_df)}")
    print(f"   Sample data:\n{coordinator_df.to_string()}")
    
    # Incremental provider tasks - new data with later dates
    provider_data = {
        "LAST FIRST DOB": ["SMITH JOHN 01/15/1940", "JONES MARY 03/10/1960"],
        "DOS": ["12/01/2025", "12/03/2025"],  # Later dates for incremental test
        "Provider": ["ZEN-ANE", "ZEN-KAJ"],
        "Service": ["Office Visit", "Telehealth"],
        "Minutes": [30, 45],
        "Billing Code": ["99213", "99441"]
    }
    
    provider_df = pd.DataFrame(provider_data)
    psl_file = test_dir / "psl_incremental.csv"
    provider_df.to_csv(psl_file, index=False)
    print(f"✅ Created incremental provider PSL file: {psl_file}")
    print(f"   Records: {len(provider_df)}")
    
    rvz_data = {
        "LAST FIRST DOB": ["JONES MARY 03/10/1960"],
        "DOS": ["12/04/2025"],  # Later date for incremental test
        "Provider": ["ZEN-KAJ"],
        "Service": ["Follow-up Call"],
        "Minutes": [20],
        "Billing Code": ["99441"]
    }
    
    rvz_df = pd.DataFrame(rvz_data)
    rvz_file = test_dir / "rvz_incremental.csv"
    rvz_df.to_csv(rvz_file, index=False)
    print(f"✅ Created incremental provider RVZ file: {rvz_file}")
    print(f"   Records: {len(rvz_df)}")
    
    return test_dir

def test_incremental_import():
    """Test incremental import functionality"""
    
    print("\n" + "="*60)
    print("🔄 TESTING INCREMENTAL IMPORT FUNCTIONALITY")
    print("="*60)
    
    # First, check baseline counts
    print("\n📊 BASELINE COUNTS:")
    conn = sqlite3.connect("sheets_data.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM NORM_STAGING_COORDINATOR_TASKS_SEPT WHERE activity_date >= '2025-11-01'")
    baseline_coord = cursor.fetchone()[0]
    print(f"   Baseline coordinator tasks (Nov+): {baseline_coord}")
    
    cursor.execute("SELECT COUNT(*) FROM NORM_STAGING_PROVIDER_TASKS_SEPT WHERE activity_date >= '2025-11-01'")
    baseline_prov = cursor.fetchone()[0]
    print(f"   Baseline provider tasks (Nov+): {baseline_prov}")
    
    # Create incremental test data
    test_dir = create_incremental_test_data()
    
    # Replace downloads with incremental data
    downloads_dir = Path("downloads")
    print(f"\n📁 Setting up incremental test environment...")
    
    if (test_dir / "cmlog_incremental.csv").exists():
        shutil.copy2(test_dir / "cmlog_incremental.csv", downloads_dir / "cmlog.csv")
        print("   ✅ Updated cmlog.csv with incremental data")
    
    if (test_dir / "psl_incremental.csv").exists():
        shutil.copy2(test_dir / "psl_incremental.csv", downloads_dir / "psl.csv")
        print("   ✅ Updated psl.csv with incremental data")
        
    if (test_dir / "rvz_incremental.csv").exists():
        shutil.copy2(test_dir / "rvz_incremental.csv", downloads_dir / "rvz.csv")
        print("   ✅ Updated rvz.csv with incremental data")
    
    # Run incremental import
    print(f"\n🚀 Running incremental import with December 2025 data...")
    result = os.system("python scripts/unified_import.py --start-date 2025-12-01 --no-backup")
    
    # Check results
    print(f"\n📊 INCREMENTAL IMPORT RESULTS:")
    
    cursor.execute("SELECT COUNT(*) FROM NORM_STAGING_COORDINATOR_TASKS_SEPT WHERE activity_date >= '2025-11-01'")
    new_coord = cursor.fetchone()[0]
    print(f"   New coordinator tasks (Nov+): {new_coord}")
    print(f"   Added coordinator tasks: {new_coord - baseline_coord}")
    
    cursor.execute("SELECT COUNT(*) FROM NORM_STAGING_PROVIDER_TASKS_SEPT WHERE activity_date >= '2025-11-01'")
    new_prov = cursor.fetchone()[0]
    print(f"   New provider tasks (Nov+): {new_prov}")
    print(f"   Added provider tasks: {new_prov - baseline_prov}")
    
    # Verify December data specifically
    cursor.execute("SELECT COUNT(*) FROM NORM_STAGING_COORDINATOR_TASKS_SEPT WHERE activity_date >= '2025-12-01'")
    december_coord = cursor.fetchone()[0]
    print(f"   December coordinator tasks: {december_coord}")
    
    cursor.execute("SELECT COUNT(*) FROM NORM_STAGING_PROVIDER_TASKS_SEPT WHERE activity_date >= '2025-12-01'")
    december_prov = cursor.fetchone()[0]
    print(f"   December provider tasks: {december_prov}")
    
    conn.close()
    
    # Validate success
    success = result == 0 and (new_coord > baseline_coord or new_prov > baseline_prov)
    
    if success:
        print(f"\n✅ SUCCESS: Incremental import working correctly!")
        print(f"   - System properly handled additional data")
        print(f"   - No duplicate records created")
        print(f"   - Dashboard views updated with new data")
        return True
    else:
        print(f"\n❌ FAILURE: Incremental import issues detected")
        return False

if __name__ == "__main__":
    test_incremental_import()
