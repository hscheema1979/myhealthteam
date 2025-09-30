#!/usr/bin/env python3
"""
Database setup script for production deployment
Creates and populates the production database from schema and data files
"""

import sqlite3
import os
import sys
from pathlib import Path

def create_production_database():
    """Create production database from schema and initial data"""
    
    # Database path
    db_path = "production.db"
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        backup_name = f"{db_path}.backup_{int(time.time())}"
        os.rename(db_path, backup_name)
        print(f"Existing database backed up as {backup_name}")
    
    # Connect to new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Read and execute schema
        if os.path.exists("actual_schema.sql"):
            with open("actual_schema.sql", "r") as f:
                schema_sql = f.read()
            cursor.executescript(schema_sql)
            print("✓ Database schema created")
        
        # Execute any setup SQL files
        sql_files = [
            "sql/create_onboarding_tables.sql",
            "sql/create_pot_onboarding_workflow.sql", 
            "sql/insert_pot_workflow_steps.sql"
        ]
        
        for sql_file in sql_files:
            if os.path.exists(sql_file):
                with open(sql_file, "r") as f:
                    sql_content = f.read()
                cursor.executescript(sql_content)
                print(f"✓ Executed {sql_file}")
        
        # Import initial data if CSV files exist
        if os.path.exists("zip-codes.csv"):
            import pandas as pd
            zip_codes = pd.read_csv("zip-codes.csv")
            zip_codes.to_sql("zip_codes", conn, if_exists="replace", index=False)
            print("✓ Imported ZIP codes data")
        
        conn.commit()
        print("\n🎉 Production database created successfully!")
        print(f"Database location: {os.path.abspath(db_path)}")
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    import time
    create_production_database()