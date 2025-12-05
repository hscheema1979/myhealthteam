#!/usr/bin/env python3
"""
Small Dataset Test for Unified Import Script
Creates minimal test CSVs with 1-2 records each
"""

import pandas as pd
import os
import sqlite3
from pathlib import Path

def create_test_csvs():
    """Create small test CSV files for validation"""
    
    # Create test directory
    test_dir = Path("test_small_data")
    test_dir.mkdir(exist_ok=True)
    
    # Test coordinator tasks - minimal data
    coordinator_data = {
        "LAST FIRST DOB": ["SMITH JOHN 01/15/1940", "DOE JANE 05/20/1950"],
        "CM ID": ["AltSh000", "ANTET000"],
        "Date Only": ["11/15/2025", "11/16/2025"],
        "Duration Minutes": [30, 45],
        "Task Type": ["Phone Call", "Care Coordination"],
        "Notes": ["Initial assessment", "Follow-up call"]
    }
    
    coordinator_df = pd.DataFrame(coordinator_data)
    coordinator_file = test_dir / "cmlog_test.csv"
    coordinator_df.to_csv(coordinator_file, index=False)
    print(f"✅ Created test coordinator file: {coordinator_file}")
    print(f"   Records: {len(coordinator_df)}")
    print(f"   Sample data:\n{coordinator_df.to_string()}")
    
    # Test provider tasks - minimal data  
    provider_data = {
        "LAST FIRST DOB": ["SMITH JOHN 01/15/1940", "JONES MARY 03/10/1960"],
        "DOS": ["11/15/2025", "11/17/2025"],
        "Provider": ["ZEN-ANE", "ZEN-KAJ"],
        "Service": ["Office Visit", "Home Visit"],
        "Minutes": [30, 60],
        "Billing Code": ["99213", "99341"]
    }
    
    provider_df = pd.DataFrame(provider_data)
    psl_file = test_dir / "psl_test.csv"
    provider_df.to_csv(psl_file, index=False)
    print(f"✅ Created test provider PSL file: {psl_file}")
    print(f"   Records: {len(provider_df)}")
    print(f"   Sample data:\n{provider_df.to_string()}")
    
    # Test RVZ data
    rvz_data = {
        "LAST FIRST DOB": ["SMITH JOHN 01/15/1940"],
        "DOS": ["11/18/2025"],
        "Provider": ["ZEN-ANE"],
        "Service": ["Phone Call"],
        "Minutes": [15],
        "Billing Code": ["99441"]
    }
    
    rvz_df = pd.DataFrame(rvz_data)
    rvz_file = test_dir / "rvz_test.csv"
    rvz_df.to_csv(rvz_file, index=False)
    print(f"✅ Created test provider RVZ file: {rvz_file}")
    print(f"   Records: {len(rvz_df)}")
    print(f"   Sample data:\n{rvz_df.to_string()}")
    
    # Test patient data
    patient_data = {
        "LAST FIRST DOB": ["SMITH JOHN 01/15/1940", "DOE JANE 05/20/1950", "JONES MARY 03/10/1960"],
        "Last": ["SMITH", "DOE", "JONES"],
        "First": ["JOHN", "JANE", "MARY"],
        "DOB": ["01/15/1940", "05/20/1950", "03/10/1960"],
        "Status": ["Active", "Active", "Active"],
        "Phone": ["555-0123", "555-0456", "555-0789"],
        "Address": ["123 Main St", "456 Oak Ave", "789 Pine Rd"]
    }
    
    patient_df = pd.DataFrame(patient_data)
    patient_file = test_dir / "ZMO_Main_test.csv"
    patient_df.to_csv(patient_file, index=False)
    print(f"✅ Created test patient file: {patient_file}")
    print(f"   Records: {len(patient_df)}")
    print(f"   Sample data:\n{patient_df.to_string()}")
    
    return test_dir

def test_with_small_data():
    """Test the unified import with small dataset"""
    
    print("\n" + "="*60)
    print("🧪 TESTING UNIFIED IMPORT WITH SMALL DATASET")
    print("="*60)
    
    # Create test CSVs
    test_dir = create_test_csvs()
    
    # Backup original downloads and replace with test data
    downloads_dir = Path("downloads")
    backup_dir = downloads_dir / "backup_original"
    
    print(f"\n📁 Backing up original downloads to: {backup_dir}")
    if downloads_dir.exists():
        if backup_dir.exists():
            import shutil
            shutil.rmtree(backup_dir)
        shutil.copytree(downloads_dir, backup_dir)
    
    # Replace with test data
    print(f"📁 Replacing downloads with test data from: {test_dir}")
    
    # Copy test files to downloads
    import shutil
    
    if (test_dir / "cmlog_test.csv").exists():
        shutil.copy2(test_dir / "cmlog_test.csv", downloads_dir / "cmlog.csv")
        print("   ✅ Replaced cmlog.csv")
    
    if (test_dir / "psl_test.csv").exists():
        shutil.copy2(test_dir / "psl_test.csv", downloads_dir / "psl.csv")
        print("   ✅ Replaced psl.csv")
        
    if (test_dir / "rvz_test.csv").exists():
        shutil.copy2(test_dir / "rvz_test.csv", downloads_dir / "rvz.csv")
        print("   ✅ Replaced rvz.csv")
    
    if (test_dir / "ZMO_Main_test.csv").exists():
        patients_dir = downloads_dir / "patients"
        patients_dir.mkdir(exist_ok=True)
        shutil.copy2(test_dir / "ZMO_Main_test.csv", patients_dir / "ZMO_Main.csv")
        print("   ✅ Replaced patients/ZMO_Main.csv")
    
    # Test with unified import script
    print(f"\n🚀 Running unified import with small dataset...")
    print(f"   Target date: 2025-11-01")
    print(f"   Backup: Skipped for testing")
    
    os.system("python scripts/unified_import.py --start-date 2025-11-01 --no-backup")
    
    # Validate results
    print(f"\n📊 VALIDATING RESULTS:")
    
    try:
        # Check staging database
        conn = sqlite3.connect("sheets_data.db")
        cursor = conn.cursor()
        
        # Check coordinator tasks
        cursor.execute("SELECT COUNT(*) FROM source_coordinator_tasks_history")
        coord_count = cursor.fetchone()[0]
        print(f"   Coordinator tasks imported: {coord_count}")
        
        # Check provider tasks
        cursor.execute("SELECT COUNT(*) FROM SOURCE_PROVIDER_TASKS_HISTORY")
        prov_count = cursor.fetchone()[0]
        print(f"   Provider tasks imported: {prov_count}")
        
        # Check patient data
        cursor.execute("SELECT COUNT(*) FROM SOURCE_PATIENT_DATA")
        patient_count = cursor.fetchone()[0]
        print(f"   Patient records imported: {patient_count}")
        
        # Check if transformation worked
        try:
            cursor.execute("SELECT COUNT(*) FROM staging_coordinator_tasks")
            staging_coord_count = cursor.fetchone()[0]
            print(f"   Staging coordinator tasks: {staging_coord_count}")
        except:
            print(f"   ⚠️ Staging coordinator tasks table not found")
            
        try:
            cursor.execute("SELECT COUNT(*) FROM staging_provider_tasks")
            staging_prov_count = cursor.fetchone()[0]
            print(f"   Staging provider tasks: {staging_prov_count}")
        except:
            print(f"   ⚠️ Staging provider tasks table not found")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error validating results: {e}")
    
    # Restore original downloads
    print(f"\n🔄 Restoring original downloads...")
    if backup_dir.exists():
        if downloads_dir.exists():
            shutil.rmtree(downloads_dir)
        shutil.move(str(backup_dir), str(downloads_dir))
        print(f"   ✅ Original downloads restored")
    
    print(f"\n✅ Small dataset test completed!")
    return True

if __name__ == "__main__":
    test_with_small_data()
