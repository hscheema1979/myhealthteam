"""
Script to create dashboard mapping tables for counties and zip codes
"""

import sqlite3
import os

DB_PATH = 'production.db'

def create_dashboard_mapping_tables():
    """Create the required dashboard mapping tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create dashboard_provider_county_map table
    create_provider_county_table = """
    CREATE TABLE IF NOT EXISTS "dashboard_provider_county_map" (
        map_id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_id INTEGER NOT NULL,
        county TEXT NOT NULL,
        state TEXT NOT NULL,
        patient_count INTEGER DEFAULT 0,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (provider_id) REFERENCES "providers"(provider_id)
    );
    """
    
    # Create dashboard_patient_county_map table
    create_patient_county_table = """
    CREATE TABLE IF NOT EXISTS "dashboard_patient_county_map" (
        map_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        county TEXT NOT NULL,
        state TEXT NOT NULL,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES "patients"(patient_id)
    );
    """
    
    # Create dashboard_patient_zip_map table
    create_patient_zip_table = """
    CREATE TABLE IF NOT EXISTS "dashboard_patient_zip_map" (
        map_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        zip_code TEXT NOT NULL,
        city TEXT,
        state TEXT,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES "patients"(patient_id)
    );
    """
    
    # Create dashboard_provider_zip_map table
    create_provider_zip_table = """
    CREATE TABLE IF NOT EXISTS "dashboard_provider_zip_map" (
        map_id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_id INTEGER NOT NULL,
        zip_code TEXT NOT NULL,
        city TEXT,
        state TEXT,
        patient_count INTEGER DEFAULT 0,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (provider_id) REFERENCES "providers"(provider_id)
    );
    """
    
    try:
        # Create all tables
        cursor.execute(create_provider_county_table)
        cursor.execute(create_patient_county_table)
        cursor.execute(create_patient_zip_table)
        cursor.execute(create_provider_zip_table)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_provider_county_map_provider ON dashboard_provider_county_map(provider_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_provider_county_map_county ON dashboard_provider_county_map(county, state)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patient_county_map_patient ON dashboard_patient_county_map(patient_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patient_county_map_county ON dashboard_patient_county_map(county, state)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patient_zip_map_patient ON dashboard_patient_zip_map(patient_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patient_zip_map_zip ON dashboard_patient_zip_map(zip_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_provider_zip_map_provider ON dashboard_provider_zip_map(provider_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_provider_zip_map_zip ON dashboard_provider_zip_map(zip_code)")
        
        conn.commit()
        print("✓ All dashboard mapping tables created successfully")
        return True
    except sqlite3.Error as e:
        print(f"✗ Error creating dashboard mapping tables: {e}")
        return False
    finally:
        conn.close()

def populate_dashboard_mapping_tables():
    """Populate the dashboard mapping tables with data from existing tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Populate dashboard_provider_county_map
        print("Populating dashboard_provider_county_map...")
        cursor.execute("""
            INSERT OR REPLACE INTO dashboard_provider_county_map 
            (provider_id, county, state, patient_count)
            SELECT 
                rp.provider_id,
                r.county,
                r.state,
                COUNT(DISTINCT p.patient_id) as patient_count
            FROM region_providers rp
            JOIN regions r ON rp.region_id = r.region_id
            LEFT JOIN patients p ON r.region_id = p.region_id
            WHERE r.county IS NOT NULL AND r.county != ''
            GROUP BY rp.provider_id, r.county, r.state
        """)
        
        # Populate dashboard_patient_county_map
        print("Populating dashboard_patient_county_map...")
        cursor.execute("""
            INSERT OR REPLACE INTO dashboard_patient_county_map 
            (patient_id, county, state)
            SELECT 
                p.patient_id,
                r.county,
                r.state
            FROM patients p
            JOIN regions r ON p.region_id = r.region_id
            WHERE r.county IS NOT NULL AND r.county != ''
        """)
        
        # Populate dashboard_patient_zip_map
        print("Populating dashboard_patient_zip_map...")
        cursor.execute("""
            INSERT OR REPLACE INTO dashboard_patient_zip_map 
            (patient_id, zip_code, city, state)
            SELECT 
                p.patient_id,
                r.zip_code,
                r.city,
                r.state
            FROM patients p
            JOIN regions r ON p.region_id = r.region_id
            WHERE r.zip_code IS NOT NULL AND r.zip_code != ''
        """)
        
        # Populate dashboard_provider_zip_map
        print("Populating dashboard_provider_zip_map...")
        cursor.execute("""
            INSERT OR REPLACE INTO dashboard_provider_zip_map 
            (provider_id, zip_code, city, state, patient_count)
            SELECT 
                rp.provider_id,
                r.zip_code,
                r.city,
                r.state,
                COUNT(DISTINCT p.patient_id) as patient_count
            FROM region_providers rp
            JOIN regions r ON rp.region_id = r.region_id
            LEFT JOIN patients p ON r.region_id = p.region_id
            WHERE r.zip_code IS NOT NULL AND r.zip_code != ''
            GROUP BY rp.provider_id, r.zip_code, r.city, r.state
        """)
        
        conn.commit()
        print("✓ All dashboard mapping tables populated successfully")
        return True
    except sqlite3.Error as e:
        print(f"✗ Error populating dashboard mapping tables: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("Creating dashboard mapping tables...")
    if create_dashboard_mapping_tables():
        print("Tables created successfully. Populating with data...")
        populate_dashboard_mapping_tables()
        print("Dashboard mapping tables setup complete!")
    else:
        print("Failed to create dashboard mapping tables")
