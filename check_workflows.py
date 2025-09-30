"""
Script to check available workflow templates in the database.
Excludes workflows with "Future" in their names.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import get_db_connection

def check_workflows():
    """Query database for workflow templates, excluding those with 'Future' in name."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query workflow templates excluding those with "Future" in name
        cursor.execute("""
            SELECT template_id, template_name 
            FROM workflow_templates 
            WHERE template_name NOT LIKE '%Future%'
            ORDER BY template_name
        """)
        
        workflows = cursor.fetchall()
        
        print(f"Found {len(workflows)} workflow templates (excluding Future workflows):")
        print("-" * 60)
        
        for template_id, template_name in workflows:
            print(f"ID: {template_id:2d} | Name: {template_name}")
        
        conn.close()
        return workflows
        
    except Exception as e:
        print(f"Error checking workflows: {e}")
        return []

if __name__ == "__main__":
    workflows = check_workflows()