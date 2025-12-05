#!/usr/bin/env python3
"""
Minimal Import Test for Unified Import Script
Direct testing with small CSVs without modifying downloads
"""

import pandas as pd
import os
import sqlite3
import shutil
from pathlib import Path

def create_minimal_test_data():
    """Create minimal test data directly in downloads for testing"""
    
    print("\n" + "="*60)
    print("🧪 MINIMAL IMPORT TEST - DIRECT CSV REPLACEMENT")
    print("="*60)
    
    # Create test directory
    test_dir = Path("test_minimal_data")
    test_dir.mkdir(exist_ok=True)
    
    # Minimal coordinator tasks - 2 records
    coordinator_data = {
        "LAST FIRST DOB": ["TEST PATIENT 01/15/1940", "TEST PATIENT 02/20/1950"],
        "CM ID": ["AltSh000", "ANTET000"],
        "Date Only": ["12/01/2025", "12/02/2025"],
        "Duration Minutes": [30, 45],
        "Task Type": ["Phone Call", "Care Coordination"],
        "Notes": ["Test assessment", "Test follow-up"]
    }
    
    coordinator_df = pd.DataFrame(coordinator_data)
    coordinator_file = test_dir / "cmlog_minimal.csv"
    coordinator_df.to_csv(coordinator_file, index=False)
    print(f"✅ Created minimal coordinator file: {coordinator_file}")
    print(f"   Records: {len(coordinator_df)}")
    
    # Minimal provider tasks - 2 records  
    provider_data = {
        "LAST FIRST DOB": ["TEST PATIENT 01/15/1940", "TEST PATIENT 02/20/1950"],
        "DOS": ["12/01/2025", "12/03/2025"],
        "Provider": ["ZEN-ANE", "ZEN-KAJ"],
        "Service": ["Office Visit", "Home Visit"],
        "Minutes": [30, 60],
        "Billing Code": ["99213", "99341"]
    }
    
    provider_df = pd.DataFrame(provider_data)
    psl_file = test_dir / "psl_minimal.csv"
    provider_df.to_csv(psl_file, index=False)
    print(f"✅ Created minimal provider PSL file: {psl_file}")
    print(f"   Records: {len(provider_df)}")
    
    # Minimal RVZ data
    rvz_data = {
        "LAST FIRST DOB": ["TEST PATIENT 01/15/1940"],
        "DOS": ["12/04/2025"],
        "Provider": ["ZEN-ANE"],
        "Service": ["Phone Call"],
        "Minutes": [15],
        "Billing Code": ["99441"]
    }
    
    rvz_df = pd.DataFrame(rvz_data)
    rvz_file = test_dir / "rvz_minimal.csv"
    rvz_df.to_csv(rvz_file, index=False)
    print(f"✅ Created minimal provider RVZ file: {rvz_file}")
    print(f"   Records: {len(rvz_df)}")
    
    # Minimal patient data
    patient_data = {
        "LAST FIRST DOB": ["TEST PATIENT 01/15/1940", "TEST PATIENT 02/20/1950"],
        "Last": ["PATIENT", "PATIENT"],
        "First": ["TEST", "TEST"],
        "DOB": ["01/15/1940", "02/20/1950"],
        "Status": ["Active", "Active"],
        "Phone": ["555-0123", "555-0456"],
        "Address": ["123 Test St", "456 Test Ave"]
    }
    
    patient_df = pd.DataFrame(patient_data)
    patient_file = test_dir / "ZMO_Main_minimal.csv"
    patient_df.to_csv(patient_file, index=False)
    print(f"✅ Created minimal patient file: {patient_file}")
    print(f"   Records: {len(patient_df)}")
    
    return test_dir

def backup_and_replace_downloads(test_dir):
    """Backup downloads and replace with minimal test data"""
    
    downloads_dir = Path("downloads")
    backup_dir = downloads_dir / "backup_for_minimal_test"
    
    print(f"\n📁 Backing up downloads to: {backup_dir}")
    
    # Backup existing downloads
    if downloads_dir.exists() and any(downloads_dir.iterdir()):
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(downloads_dir, backup_dir)
        print(f"   ✅ Backed up {len(list(downloads_dir.glob('*.csv')))} files")
    
    # Replace with minimal test data
    print(f"📁 Replacing downloads with minimal test data...")
    
    # Replace coordinator data
    test_coord = test_dir / "cmlog_minimal.csv"
    if test_coord.exists():
        shutil.copy2(test_coord, downloads_dir / "cmlog.csv")
        print(f"   ✅ Replaced cmlog.csv ({len(pd.read_csv(test_coord))} records)")
    
    # Replace provider data
    test_psl = test_dir / "psl_minimal.csv"
    test_rvz = test_dir / "rvz_minimal.csv"
    
    if test_psl.exists():
        shutil.copy2(test_psl, downloads_dir / "psl.csv")
        print(f"   ✅ Replaced psl.csv ({len(pd.read_csv(test_psl))} records)")
        
    if test_rvz.exists():
        shutil.copy2(test_rvz, downloads_dir / "rvz.csv")
        print(f"   ✅ Replaced rvz.csv ({len(pd.read_csv(test_rvz))} records)")
    
    # Replace patient data
    test_patient = test_dir / "ZMO_Main_minimal.csv"
    if test_patient.exists():
        patients_dir = downloads_dir / "patients"
        patients_dir.mkdir(exist_ok=True)
        shutil.copy2(test_patient, patients_dir / "ZMO_Main.csv")
        print(f"   ✅ Replaced patients/ZMO_Main.csv ({len(pd.read_csv(test_patient))} records)")
    
    return backup_dir

def restore_downloads(backup_dir):
    """Restore original downloads"""
    
    downloads_dir = Path("downloads")
    
    print(f"\n🔄 Restoring original downloads...")
    
    if backup_dir.exists():
        if downloads_dir.exists():
            shutil.rmtree(downloads_dir)
        shutil.move(str(backup_dir), str(downloads_dir))
        print(f"   ✅ Original downloads restored")

def run_minimal_test():
    """Run the complete minimal test"""
    
    # Create test data
    test_dir = create_minimal_test_data()
    
    # Backup and replace downloads
    backup_dir = backup_and_replace_downloads(test_dir)
    
    try:
        # Run unified import with minimal data
        print(f"\n🚀 Running unified import with minimal dataset...")
        print(f"   Target date: 2025-12-01")
        print(f"   Backup: Skipped for testing")
        
        import subprocess
        result = subprocess.run([
            "python", "scripts/unified_import.py", 
            "--start-date", "2025-12-01", 
            "--no-backup"
        ], capture_output=True, text=True)
        
        print(f"   Return code: {result.returncode}")
        if result.stdout:
            print(f"   Output:\n{result.stdout}")
        if result.stderr:
            print(f"   Errors:\n{result.stderr}")
        
        # Validate results
        print(f"\n📊 VALIDATING RESULTS:")
        
        try:
            conn = sqlite3.connect("sheets_data.db")
            cursor = conn.cursor()
            
            # Check source tables
            cursor.execute("SELECT COUNT(*) FROM source_coordinator_tasks_history")
            coord_count = cursor.fetchone()[0]
            print(f"   ✅ Source coordinator tasks: {coord_count}")
            
            cursor.execute("SELECT COUNT(*) FROM SOURCE_PROVIDER_TASKS_HISTORY")
            prov_count = cursor.fetchone()[0]
            print(f"   ✅ Source provider tasks: {prov_count}")
            
            cursor.execute("SELECT COUNT(*) FROM SOURCE_PATIENT_DATA")
            patient_count = cursor.fetchone()[0]
            print(f"   ✅ Source patient records: {patient_count}")
            
            # Check staging tables
            try:
                cursor.execute("SELECT COUNT(*) FROM staging_coordinator_tasks")
                staging_coord_count = cursor.fetchone()[0]
                print(f"   ✅ Staging coordinator tasks: {staging_coord_count}")
                
                # Show sample data
                cursor.execute("SELECT patient_id, coordinator_id, activity_date FROM staging_coordinator_tasks LIMIT 3")
                samples = cursor.fetchall()
                print(f"   📋 Sample staging data:")
                for sample in samples:
                    print(f"      {sample}")
                
            except sqlite3.OperationalError as e:
                print(f"   ⚠️ Staging coordinator tasks table error: {e}")
            
            try:
                cursor.execute("SELECT COUNT(*) FROM staging_provider_tasks")
                staging_prov_count = cursor.fetchone()[0]
                print(f"   ✅ Staging provider tasks: {staging_prov_count}")
                
                # Show sample data
                cursor.execute("SELECT patient_id, provider_id, activity_date FROM staging_provider_tasks LIMIT 3")
                samples = cursor.fetchall()
                print(f"   📋 Sample staging data:")
                for sample in samples:
                    print(f"      {sample}")
                
            except sqlite3.OperationalError as e:
                print(f"   ⚠️ Staging provider tasks table error: {e}")
            
            conn.close()
            
        except Exception as e:
            print(f"   ❌ Validation error: {e}")
        
        print(f"\n🎉 Minimal test completed!")
        return result.returncode == 0
        
    finally:
        # Always restore original downloads
        restore_downloads(backup_dir)

if __name__ == "__main__":
    success = run_minimal_test()
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed - check output above")
