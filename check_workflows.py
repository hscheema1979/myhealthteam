import sys
sys.path.append('src')
from database import get_db_connection

def check_workflow_templates():
    conn = get_db_connection()
    try:
        templates = conn.execute("SELECT template_id, template_name FROM workflow_templates WHERE template_name NOT LIKE '%Future%' ORDER BY template_name").fetchall()
        print('Available Workflow Templates (excluding Future):')
        for template in templates:
            print(f'ID: {template[0]}, Name: {template[1]}')
        print(f'\nTotal templates: {len(templates)}')
        return templates
    finally:
        conn.close()

if __name__ == "__main__":
    check_workflow_templates()