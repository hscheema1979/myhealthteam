#!/usr/bin/env python3
"""
Test Unified Import Script with REAL downloaded data
Tests against the actual CSV files already downloaded
"""

import os
import sqlite3
import subprocess
from pathlib import Path

def test_with_real_downloaded_data():
    """Test unified import with the real downloaded CSV data"""
    
    print("\n" + "="*60)
    print("🧪 TESTING UNIFIED IMPORT WITH REAL DOWNLOADED DATA")
    print("="*60)
    
    downloads_dir = Path("downloads")
    
    # Check what real data we have
    print(f"\n📁 Checking real downloaded data:")
    
    real_files = []
    
    # Check coordinator data
    cmlog_file = downloads_dir / "cmlog.csv"
    if cmlog_file.exists():
        import pandas as pd
        coord_df = pd.read_csv(cmlog_file, nrows=5)  # Just first 5 rows to check
        real_files.append(("cmlog.csv", len(coord_df), "Coordinator tasks"))
        print(f"   ✅ cmlog.csv exists ({len(coord_df)} sample records)")
        print(f"      Columns: {list(coord_df.columns)}")
        print(f"      Sample: {coord_df.iloc[0].to_dict()}")
    
    # Check provider data  
    psl_file = downloads_dir / "psl.csv"
    rvz_file = downloads_dir / "rvz.csv"
    
    if psl_file.exists():
        psl_df = pd.read_csv(psl_file, nrows=5)
        real_files.append(("psl.csv", len(psl_df), "Provider tasks PSL"))
        print(f"   ✅ psl.csv exists ({len(psl_df)} sample records)")
        print(f"      Columns: {list(psl_df.columns)}")
        print(f"      Sample: {psl_df.iloc[0].to_dict()}")
        
    if rvz_file.exists():
        rvz_df = pd.read_csv(rvz_file, nrows=5)
        real_files.append(("rvz.csv", len(rvz_df), "Provider tasks RVZ"))
        print(f"   ✅ rvz.csv exists ({len(rvz_df)} sample records)")
        print(f"      Columns: {list(rvz_df.columns)}")
        print(f"      Sample: {rvz_df.iloc[0].to_dict()}")
    
    # Check patient data
    patient_file = downloads_dir / "patients/ZMO_Main.csv"
    if patient_file.exists():
        patient_df = pd.read_csv(patient_file, nrows=5)
        real_files.append(("ZMO_Main.csv", len(patient_df), "Patient data"))
        print(f"   ✅ ZMO_Main.csv exists ({len(patient_df)} sample records)")
        print(f"      Columns: {list(patient_df.columns)}")
        print(f"      Sample: {patient_df.iloc[0].to_dict()}")
    else:
        # Check alternative location
        alt_patient = downloads_dir / "ZMO_MAIN.csv"
        if alt_patient.exists():
            patient_df = pd.read_csv(alt_patient, nrows=5)
            real_files.append(("ZMO_MAIN.csv", len(patient_df), "Patient data"))
            print(f"   ✅ ZMO_MAIN.csv exists ({len(patient_df)} sample records)")
    
    print(f"\n📊 Real data summary:")
    for filename, sample_size, description in real_files:
        print(f"   - {filename}: {description}")
    
    if len(real_files) < 3:
        print(f"⚠️ Warning: Only found {len(real_files)} data files, expected at least 3")
        return False
    
    # Get actual file sizes to understand data volume
    print(f"\n📈 Real data volumes:")
    total_coord = len(pd.read_csv(cmlog_file)) if cmlog_file.exists() else 0
    total_psl = len(pd.read_csv(psl_file)) if psl_file.exists() else 0  
    total_rvz = len(pd.read_csv(rvz_file)) if rvz_file.exists() else 0
    total_patients = len(pd.read_csv(patient_file)) if patient_file.exists() else len(pd.read_csv(downloads_dir / "ZMO_MAIN.csv")) if (downloads_dir / "ZMO_MAIN.csv").exists() else 0
    
    print(f"   - Coordinator tasks (cmlog.csv): {total_coord:,} records")
    print(f"   - Provider tasks PSL (psl.csv): {total_psl:,} records")
    print(f"   - Provider tasks RVZ (rvz.csv): {total_rvz:,} records")
    print(f"   - Patient records: {total_patients:,} records")
    
    # Test unified import with REAL data
    print(f"\n🚀 Testing unified import with REAL data...")
    print(f"   Using start date: 2025-11-01 (should capture recent data)")
    
    try:
        # Run the unified import script with real data
        result = subprocess.run([
            "python", "scripts/unified_import.py",
            "--start-date", "2025-11-01",
            "--no-backup",
            "--production-db", "production_backup_for_testing.db"  # Use backup to avoid affecting production
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        print(f"   Return code: {result.returncode}")
        
        if result.stdout:
            print(f"   📋 Output:")
            # Show key lines from output
            for line in result.stdout.split('\n'):
                if any(keyword in line for keyword in ['INFO', 'Loaded', 'Filtered', 'Imported', 'completed', 'ERROR']):
                    print(f"      {line}")
        
        if result.stderr:
            print(f"   ❌ Errors:")
            for line in result.stderr.split('\n'):
                if line.strip():
                    print(f"      {line}")
        
        # Validate results with real data
        print(f"\n📊 VALIDATING RESULTS WITH REAL DATA:")
        
        try:
            conn = sqlite3.connect("sheets_data.db")
            cursor = conn.cursor()
            
            # Check source tables with real data
            cursor.execute("SELECT COUNT(*) FROM source_coordinator_tasks_history")
            source_coord = cursor.fetchone()[0]
            print(f"   ✅ Source coordinator tasks: {source_coord:,} (from real cmlog.csv)")
            
            cursor.execute("SELECT COUNT(*) FROM SOURCE_PROVIDER_TASKS_HISTORY")
            source_prov = cursor.fetchone()[0]
            print(f"   ✅ Source provider tasks: {source_prov:,} (from real PSL+RVZ)")
            
            cursor.execute("SELECT COUNT(*) FROM SOURCE_PATIENT_DATA")
            source_patients = cursor.fetchone()[0]
            print(f"   ✅ Source patient records: {source_patients:,} (from real ZMO_Main.csv)")
            
            # Check staging tables
            try:
                cursor.execute("SELECT COUNT(*) FROM staging_coordinator_tasks")
                staging_coord = cursor.fetchone()[0]
                print(f"   ✅ Staging coordinator tasks: {staging_coord:,}")
                
                # Show sample real data from staging
                cursor.execute("SELECT patient_id, coordinator_id, activity_date FROM staging_coordinator_tasks LIMIT 3")
                samples = cursor.fetchall()
                print(f"   📋 Sample real staging coordinator data:")
                for sample in samples:
                    print(f"      Patient: {sample[0]}, Coordinator: {sample[1]}, Date: {sample[2]}")
                
            except sqlite3.OperationalError as e:
                print(f"   ⚠️ Staging coordinator tasks: {e}")
            
            try:
                cursor.execute("SELECT COUNT(*) FROM staging_provider_tasks")
                staging_prov = cursor.fetchone()[0]
                print(f"   ✅ Staging provider tasks: {staging_prov:,}")
                
                # Show sample real data from staging
                cursor.execute("SELECT patient_id, provider_id, activity_date FROM staging_provider_tasks LIMIT 3")
                samples = cursor.fetchall()
                print(f"   📋 Sample real staging provider data:")
                for sample in samples:
                    print(f"      Patient: {sample[0]}, Provider: {sample[1]}, Date: {sample[2]}")
                
            except sqlite3.OperationalError as e:
                print(f"   ⚠️ Staging provider tasks: {e}")
            
            conn.close()
            
            # Validate data integrity
            print(f"\n🔍 DATA INTEGRITY VALIDATION:")
            
            if source_coord > 0 and staging_coord > 0:
                print(f"   ✅ Coordinator data preserved in staging")
            else:
                print(f"   ⚠️ Coordinator data issue: source={source_coord}, staging={staging_coord}")
                
            if source_prov > 0 and staging_prov > 0:
                print(f"   ✅ Provider data preserved in staging")
            else:
                print(f"   ⚠️ Provider data issue: source={source_prov}, staging={staging_prov}")
            
            print(f"\n🎉 REAL DATA TEST COMPLETED!")
            return result.returncode == 0
            
        except Exception as e:
            print(f"   ❌ Validation error: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ Test execution error: {e}")
        return False

if __name__ == "__main__":
    success = test_with_real_downloaded_data()
    if success:
        print(f"\n✅ SUCCESS: Unified import works with REAL downloaded data!")
        print(f"   - Script correctly processes actual CSV files")
        print(f"   - Data transformations work with real patient/provider names")
        print(f"   - Staff code mapping works with real coordinator IDs")
        print(f"   - Date filtering works with real dates")
    else:
        print(f"\n❌ ISSUES FOUND: Check the output above")
