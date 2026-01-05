"""
Migration script to fix missing columns in onboarding_patients table on VPS2
This script will:
1. Check for missing columns (patient_status, assigned_pot_user_id, etc.)
2. Add missing columns with appropriate defaults
3. Set default values for existing records
"""

import sqlite3
import os
from datetime import datetime

def fix_onboarding_patients_table(db_path):
    """Fix missing columns in onboarding_patients table"""
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Step 1: Get current table schema
        print("\nStep 1: Checking table schema...")
        cursor.execute("PRAGMA table_info(onboarding_patients)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {', '.join(columns)}")
        
        # Define required columns with their defaults
        required_columns = {
            'patient_status': "TEXT DEFAULT 'Active'",
            'assigned_pot_user_id': "INTEGER",
            'stage1_complete': "BOOLEAN DEFAULT 0",
            'stage2_complete': "BOOLEAN DEFAULT 0",
            'stage3_complete': "BOOLEAN DEFAULT 0",
            'stage4_complete': "BOOLEAN DEFAULT 0",
            'stage5_complete': "BOOLEAN DEFAULT 0",
            'completed_date': "TIMESTAMP",
            'updated_date': "TIMESTAMP",
            'insurance_provider': "TEXT",
            'policy_number': "TEXT",
            'group_number': "TEXT",
            'referral_source': "TEXT",
            'referring_provider': "TEXT",
            'referral_date': "DATE",
            'facility_assignment': "TEXT",
            'provider_completed_initial_tv': "BOOLEAN DEFAULT 0",
            'insurance_cards_received': "BOOLEAN DEFAULT 0",
            'medical_records_requested': "BOOLEAN DEFAULT 0",
            'referral_documents_received': "BOOLEAN DEFAULT 0",
            'emed_signature_received': "BOOLEAN DEFAULT 0",
            'gender': "TEXT",
            'emergency_contact_name': "TEXT",
            'emergency_contact_phone': "TEXT",
            'address_street': "TEXT",
            'address_city': "TEXT",
            'address_state': "TEXT",
            'address_zip': "TEXT",
            'workflow_instance_id': "INTEGER",
        }
        
        # Step 2: Check and add missing columns
        print("\nStep 2: Checking for missing columns...")
        missing_columns = [col for col in required_columns.keys() if col not in columns]
        
        if not missing_columns:
            print("✓ All required columns exist in onboarding_patients table")
            return True
        
        print(f"✗ Found {len(missing_columns)} missing columns:")
        for col in missing_columns:
            print(f"  - {col} ({required_columns[col]})")
        
        # Step 3: Add missing columns
        print("\nStep 3: Adding missing columns...")
        for col_name, col_def in required_columns.items():
            if col_name not in columns:
                cursor.execute(f"""
                    ALTER TABLE onboarding_patients 
                    ADD COLUMN {col_name} {col_def}
                """)
                print(f"✓ Successfully added column: {col_name}")
        
        # Step 4: Verify columns were added
        print("\nStep 4: Verifying column additions...")
        cursor.execute("PRAGMA table_info(onboarding_patients)")
        columns_after = [row[1] for row in cursor.fetchall()]
        
        still_missing = [col for col in missing_columns if col not in columns_after]
        if still_missing:
            print(f"✗ Failed to add columns: {', '.join(still_missing)}")
            return False
        
        print("✓ All missing columns successfully added")
        
        # Step 5: Update existing records with default values
        print("\nStep 5: Updating existing records with default values...")
        
        # Update patient_status
        if 'patient_status' in missing_columns:
            cursor.execute("""
                UPDATE onboarding_patients 
                SET patient_status = 'Active' 
                WHERE patient_status IS NULL
            """)
            print(f"✓ Updated {cursor.rowcount} records with patient_status = 'Active'")
        
        # Update stage completion flags
        for stage in ['stage1_complete', 'stage2_complete', 'stage3_complete', 'stage4_complete', 'stage5_complete']:
            if stage in missing_columns:
                cursor.execute(f"""
                    UPDATE onboarding_patients 
                    SET {stage} = 0 
                    WHERE {stage} IS NULL
                """)
                if cursor.rowcount > 0:
                    print(f"✓ Updated {cursor.rowcount} records with {stage} = 0")
        
        # Step 6: Add UNIQUE index on patient_id for INSERT OR REPLACE support
        print("\nStep 6: Adding UNIQUE index on patient_id...")
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_onboarding_patients_patient_id_unique 
            ON onboarding_patients(patient_id)
        """)
        print("✓ UNIQUE index on patient_id created (supports INSERT OR REPLACE)")
        
        # Step 7: Commit changes
        conn.commit()
        print("\n✓ All changes committed successfully")
        
        # Step 8: Verify data
        print("\nStep 6: Verifying data...")
        cursor.execute("""
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN patient_status = 'Active' THEN 1 ELSE 0 END) as active_count,
                   SUM(CASE WHEN patient_status IS NULL THEN 1 ELSE 0 END) as null_status_count,
                   SUM(CASE WHEN stage1_complete = 1 THEN 1 ELSE 0 END) as stage1_complete_count,
                   SUM(CASE WHEN stage2_complete = 1 THEN 1 ELSE 0 END) as stage2_complete_count,
                   SUM(CASE WHEN stage3_complete = 1 THEN 1 ELSE 0 END) as stage3_complete_count
            FROM onboarding_patients
        """)
        result = cursor.fetchone()
        
        print(f"Total records: {result[0]}")
        print(f"Active status: {result[1]}")
        print(f"NULL patient_status: {result[2]}")
        print(f"Stage 1 complete: {result[3]}")
        print(f"Stage 2 complete: {result[4]}")
        print(f"Stage 3 complete: {result[5]}")
        
        if result[2] == 0:
            print("\n✓ All records have valid patient_status values")
        else:
            print(f"\n⚠ Warning: {result[2]} records still have NULL patient_status")
        
        print("\n" + "="*60)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        import traceback
        print(traceback.format_exc())
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    """Main execution function"""
    print("="*60)
    print("VPS2 patient_status Column Fix Script")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check for USE_PROTOTYPE_MODE flag
    prototype_flag = os.path.join(os.path.dirname(__file__), "USE_PROTOTYPE_MODE")
    
    if os.path.exists(prototype_flag) or os.getenv("USE_PROTOTYPE") == "1":
        db_path = os.path.join(os.path.dirname(__file__), "prototype.db")
        print("⚠️  USING PROTOTYPE DATABASE")
    else:
        db_path = os.path.join(os.path.dirname(__file__), "production.db")
        print("Using PRODUCTION database")
    
    # Execute the fix
    success = fix_onboarding_patients_table(db_path)
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        print("\n✓ The onboarding queue error should now be resolved.")
        print("  Please restart your application to verify the fix.")
        return 0
    else:
        print("\n✗ Migration failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    exit(main())
