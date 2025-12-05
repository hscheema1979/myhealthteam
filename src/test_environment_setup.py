#!/usr/bin/env python3
"""
Safe Test Environment Setup for Admin Dashboard Enhancements
This script helps you quickly configure a safe testing environment without impacting production.
"""

import os
import sqlite3
import shutil
from datetime import datetime
import sys

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_option(number, title, description):
    print(f"\n{number}. {title}")
    print(f"   {description}")

def create_test_config():
    """Create test configuration file"""
    config_content = '''# Test Environment Configuration
# Generated automatically for safe testing

TEST_MODE = True
TEST_DB_PATH = 'test_admin_enhancements.db'
STAGING_DB_PATH = 'scripts/sheets_data.db'
PROD_DB_PATH = 'production.db'

# Environment detection
import os
USE_STAGING = os.getenv('MHT_USE_STAGING', 'false').lower() == 'true'
USE_TEST_COPY = os.getenv('MHT_USE_TEST_COPY', 'false').lower() == 'true'

if USE_STAGING:
    DB_PATH = STAGING_DB_PATH
elif USE_TEST_COPY:
    DB_PATH = TEST_DB_PATH
else:
    DB_PATH = PROD_DB_PATH

print(f"Test Environment Active - Database: {DB_PATH}")
'''
    
    with open('src/test_config.py', 'w') as f:
        f.write(config_content)
    
    print("✅ Created src/test_config.py")

def setup_staging_environment():
    """Set up staging environment"""
    print_header("Setting up STAGING Environment")
    
    # Set environment variable
    os.environ['MHT_USE_STAGING'] = 'true'
    os.environ['MHT_TEST_MODE'] = 'true'
    
    # Check if staging database exists
    staging_db = 'scripts/sheets_data.db'
    if os.path.exists(staging_db):
        print(f"✅ Staging database found: {staging_db}")
        
        # Verify it's a valid database
        try:
            conn = sqlite3.connect(staging_db)
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            conn.close()
            print(f"✅ Valid database with {len(tables)} tables")
            return True
        except Exception as e:
            print(f"❌ Error accessing staging database: {e}")
            return False
    else:
        print(f"❌ Staging database not found: {staging_db}")
        return False

def setup_test_copy_environment():
    """Set up test copy environment"""
    print_header("Setting up TEST COPY Environment")
    
    source_db = 'production.db'
    test_db = 'test_admin_enhancements.db'
    
    if not os.path.exists(source_db):
        print(f"❌ Production database not found: {source_db}")
        return False
    
    try:
        # Create backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_db = f'test_admin_enhancements_backup_{timestamp}.db'
        shutil.copy2(source_db, test_db)
        shutil.copy2(source_db, backup_db)
        
        # Set environment variables
        os.environ['MHT_USE_TEST_COPY'] = 'true'
        os.environ['MHT_TEST_MODE'] = 'true'
        
        print(f"✅ Test database created: {test_db}")
        print(f"✅ Backup created: {backup_db}")
        
        # Verify the copy
        conn = sqlite3.connect(test_db)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        conn.close()
        print(f"✅ Valid database copy with {len(tables)} tables")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test copy: {e}")
        return False

def validate_environment():
    """Validate the current test environment"""
    print_header("Validating Test Environment")
    
    # Check environment variables
    test_mode = os.getenv('MHT_TEST_MODE', 'false').lower() == 'true'
    use_staging = os.getenv('MHT_USE_STAGING', 'false').lower() == 'true'
    use_test_copy = os.getenv('MHT_USE_TEST_COPY', 'false').lower() == 'true'
    
    print(f"Test Mode: {test_mode}")
    print(f"Using Staging: {use_staging}")
    print(f"Using Test Copy: {use_test_copy}")
    
    # Determine database path
    if use_staging:
        db_path = 'scripts/sheets_data.db'
        environment = "STAGING"
    elif use_test_copy:
        db_path = 'test_admin_enhancements.db'
        environment = "TEST COPY"
    else:
        db_path = 'production.db'
        environment = "PRODUCTION"
    
    print(f"Active Environment: {environment}")
    print(f"Database Path: {db_path}")
    
    # Verify database access
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            # Test basic query
            result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1").fetchone()
            conn.close()
            
            if result:
                print(f"✅ Database accessible with tables")
                return True, environment, db_path
            else:
                print(f"⚠️ Database exists but may be empty")
                return True, environment, db_path
        except Exception as e:
            print(f"❌ Error accessing database: {e}")
            return False, environment, db_path
    else:
        print(f"❌ Database file not found: {db_path}")
        return False, environment, db_path

def show_testing_instructions(environment):
    """Show specific testing instructions for the environment"""
    print_header(f"Testing Instructions for {environment} Environment")
    
    if environment == "STAGING":
        print("📋 STAGING Environment - Safe for all testing")
        print("   • All read-only features can be tested safely")
        print("   • Write operations use test data from Oct/Nov 2025")
        print("   • Perfect for initial functionality validation")
        print("   • No impact on production data")
        
    elif environment == "TEST COPY":
        print("📋 TEST COPY Environment - Complete isolation")
        print("   • Full production data replica for realistic testing")
        print("   • Safe for all operations including writes")
        print("   • Complete isolation from production")
        print("   • Recommended for comprehensive testing")
        
    else:
        print("📋 PRODUCTION Environment - Use with extreme caution")
        print("   • ❌ NOT RECOMMENDED for testing")
        print("   • Live production data")
        print("   • Only for final validation after staging/testing")
    
    print(f"\n🔧 To test the Admin Dashboard enhancements:")
    print(f"   1. Run: streamlit run app.py")
    print(f"   2. Navigate to Admin Dashboard")
    print(f"   3. Test each enhancement systematically")
    print(f"   4. Monitor for any errors or unexpected behavior")

def main():
    """Main setup function"""
    print_header("Admin Dashboard Enhancement - Safe Test Environment Setup")
    
    print("This script will help you safely test the Admin Dashboard enhancements")
    print("without impacting your production environment.")
    
    print_option("1", "Use Staging Database", "Use existing scripts/sheets_data.db (Safest, limited data)")
    print_option("2", "Create Test Copy", "Copy production.db to test_admin_enhancements.db (Recommended)")
    print_option("3", "Validate Environment", "Check current environment setup")
    print_option("4", "Exit", "Cancel setup")
    
    while True:
        try:
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                success = setup_staging_environment()
                if success:
                    valid, env, db = validate_environment()
                    if valid:
                        create_test_config()
                        show_testing_instructions(env)
                break
                
            elif choice == "2":
                success = setup_test_copy_environment()
                if success:
                    valid, env, db = validate_environment()
                    if valid:
                        create_test_config()
                        show_testing_instructions(env)
                break
                
            elif choice == "3":
                valid, env, db = validate_environment()
                if valid:
                    create_test_config()
                    show_testing_instructions(env)
                break
                
            elif choice == "4":
                print("\n❌ Setup cancelled")
                break
                
            else:
                print("❌ Invalid choice. Please select 1-4.")
                
        except KeyboardInterrupt:
            print("\n\n❌ Setup cancelled by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            break
    
    print(f"\n{'='*60}")
    print("Setup complete! Happy testing! 🧪")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()