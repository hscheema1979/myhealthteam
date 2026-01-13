import sqlite3

def migrate_provider_tasks_2026_01():
    """Migrate provider_tasks_2026_01 to match the correct schema."""
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    table_name = 'provider_tasks_2026_01'
    
    # Check if table exists
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if not cursor.fetchone():
        print(f"Table {table_name} does not exist. Skipping migration.")
        conn.close()
        return
    
    # Get current schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    current_cols = [row[1] for row in cursor.fetchall()]
    print(f"Current columns in {table_name}: {current_cols}")
    
    # Check if migration is needed (has deprecated columns)
    deprecated_cols = ['task_id', 'user_id', 'billing_code_id', 'created_date', 'updated_date', 'month', 'year']
    has_deprecated = any(col in current_cols for col in deprecated_cols)
    
    if not has_deprecated:
        print(f"Table {table_name} already has correct schema. Skipping migration.")
        conn.close()
        return
    
    print(f"Migrating {table_name} to correct schema...")
    
    # Create backup table with correct schema
    backup_table = f"{table_name}_backup"
    
    # Drop backup table if it exists from previous failed migration
    cursor.execute(f"DROP TABLE IF EXISTS {backup_table}")
    
    cursor.execute(f"""
        CREATE TABLE {backup_table} (
            provider_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id INTEGER,
            provider_name TEXT,
            patient_id TEXT,
            patient_name TEXT,
            task_date DATE,
            task_description TEXT,
            notes TEXT,
            minutes_of_service INTEGER,
            billing_code TEXT,
            billing_code_description TEXT,
            source_system TEXT DEFAULT 'CSV_IMPORT',
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'completed',
            is_deleted INTEGER DEFAULT 0
        )
    """)
    
    # Copy data from old table to new table (excluding deprecated columns)
    # Check if is_deleted column exists in old table
    has_is_deleted = 'is_deleted' in current_cols
    
    if has_is_deleted:
        cursor.execute(f"""
            INSERT INTO {backup_table} (
                provider_task_id, provider_id, provider_name, patient_id, patient_name,
                task_date, task_description, notes, minutes_of_service, billing_code,
                billing_code_description, source_system, imported_at, status, is_deleted
            )
            SELECT 
                provider_task_id, provider_id, provider_name, patient_id, patient_name,
                task_date, task_description, notes, minutes_of_service, billing_code,
                billing_code_description, source_system, imported_at, status, is_deleted
            FROM {table_name}
        """)
    else:
        cursor.execute(f"""
            INSERT INTO {backup_table} (
                provider_task_id, provider_id, provider_name, patient_id, patient_name,
                task_date, task_description, notes, minutes_of_service, billing_code,
                billing_code_description, source_system, imported_at, status, is_deleted
            )
            SELECT 
                provider_task_id, provider_id, provider_name, patient_id, patient_name,
                task_date, task_description, notes, minutes_of_service, billing_code,
                billing_code_description, source_system, imported_at, status, 0
            FROM {table_name}
        """)
    
    # Get row counts
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    old_count = cursor.fetchone()[0]
    cursor.execute(f"SELECT COUNT(*) FROM {backup_table}")
    new_count = cursor.fetchone()[0]
    
    print(f"Copied {new_count} rows from {table_name} to {backup_table} (original had {old_count} rows)")
    
    # Drop old table
    cursor.execute(f"DROP TABLE {table_name}")
    
    # Rename backup table to original name
    cursor.execute(f"ALTER TABLE {backup_table} RENAME TO {table_name}")
    
    # Create index
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_provider ON {table_name}(provider_id)")
    
    conn.commit()
    
    # Verify new schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    new_cols = [row[1] for row in cursor.fetchall()]
    print(f"New columns in {table_name}: {new_cols}")
    
    conn.close()
    print(f"Migration of {table_name} completed successfully!")

if __name__ == "__main__":
    migrate_provider_tasks_2026_01()
