"""
Apply database migration to add billing_company and billed_by columns
"""
import sys
sys.path.insert(0, 'src')

from database import get_db_connection

def apply_migration():
    """Apply the billing columns migration"""
    conn = get_db_connection()
    
    print("\n" + "="*80)
    print("BILLING COLUMNS MIGRATION")
    print("="*80)
    
    try:
        # Check current schema
        print("\n1. Checking current schema...")
        query = "PRAGMA table_info(provider_task_billing_status)"
        result = conn.execute(query).fetchall()
        columns = {row[1]: row[2] for row in result}
        
        print("   Current columns in table:")
        for col_name in sorted(columns.keys()):
            print("     - {}".format(col_name))
        
        # Check if columns already exist
        has_billing_company = 'billing_company' in columns
        has_billed_by = 'billed_by' in columns
        
        print("\n2. Column status:")
        print("   billing_company: {}".format("EXISTS" if has_billing_company else "MISSING"))
        print("   billed_by: {}".format("EXISTS" if has_billed_by else "MISSING"))
        
        # Add billing_company if missing
        if not has_billing_company:
            print("\n3. Adding billing_company column...")
            try:
                conn.execute("ALTER TABLE provider_task_billing_status ADD COLUMN billing_company TEXT")
                conn.commit()
                print("   [SUCCESS] billing_company column added")
            except Exception as e:
                print("   [ERROR] {}".format(str(e)))
                return False
        
        # Add billed_by if missing
        if not has_billed_by:
            print("\n4. Adding billed_by column...")
            try:
                conn.execute("ALTER TABLE provider_task_billing_status ADD COLUMN billed_by INTEGER")
                conn.commit()
                print("   [SUCCESS] billed_by column added")
            except Exception as e:
                print("   [ERROR] {}".format(str(e)))
                return False
        
        # Create indexes
        print("\n5. Creating indexes...")
        try:
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_billing_company 
                ON provider_task_billing_status(billing_company)
            """)
            conn.commit()
            print("   [SUCCESS] billing_company index created")
        except Exception as e:
            print("   [WARNING] billing_company index: {}".format(str(e)))
        
        try:
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_billed_by 
                ON provider_task_billing_status(billed_by)
            """)
            conn.commit()
            print("   [SUCCESS] billed_by index created")
        except Exception as e:
            print("   [WARNING] billed_by index: {}".format(str(e)))
        
        # Verify migration
        print("\n6. Verifying migration...")
        result = conn.execute(query).fetchall()
        columns_after = {row[1]: row[2] for row in result}
        
        has_billing_company_after = 'billing_company' in columns_after
        has_billed_by_after = 'billed_by' in columns_after
        
        print("   billing_company: {}".format("OK" if has_billing_company_after else "FAILED"))
        print("   billed_by: {}".format("OK" if has_billed_by_after else "FAILED"))
        
        if has_billing_company_after and has_billed_by_after:
            print("\n" + "="*80)
            print("MIGRATION COMPLETED SUCCESSFULLY")
            print("="*80)
            return True
        else:
            print("\n" + "="*80)
            print("MIGRATION COMPLETED WITH ERRORS")
            print("="*80)
            return False
            
    except Exception as e:
        print("\n[ERROR] Migration failed: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
