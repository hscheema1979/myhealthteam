import sys
sys.path.append('src')
from src import database
import pandas as pd

def check_workflow_tables():
    """Check workflow tables and their data"""
    conn = database.get_db_connection()
    try:
        # Check if workflow_instances table exists
        table_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_instances'").fetchone()
        print(f'workflow_instances table exists: {table_check is not None}')
        
        if table_check:
            # Count total workflows
            count_result = conn.execute('SELECT COUNT(*) as count FROM workflow_instances').fetchone()
            print(f'Total workflows: {count_result[0] if count_result else 0}')
            
            # Show sample data
            sample = conn.execute('SELECT * FROM workflow_instances LIMIT 5').fetchall()
            if sample:
                print('Sample workflow data:')
                for row in sample:
                    print(f'  {dict(row)}')
            else:
                print('No workflow data found')
        
        # Check workflow_templates table
        template_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_templates'").fetchone()
        print(f'workflow_templates table exists: {template_check is not None}')
        
        if template_check:
            template_count = conn.execute('SELECT COUNT(*) as count FROM workflow_templates').fetchone()
            print(f'Total workflow templates: {template_count[0] if template_count else 0}')
            
            # Show templates
            templates = conn.execute('SELECT * FROM workflow_templates').fetchall()
            if templates:
                print('Available templates:')
                for template in templates:
                    print(f'  {dict(template)}')
        
        # Also check for any other workflow-related tables
        all_tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%workflow%'").fetchall()
        if all_tables:
            print(f'All workflow-related tables: {[t[0] for t in all_tables]}')
        
    finally:
        conn.close()

if __name__ == "__main__":
    check_workflow_tables()
