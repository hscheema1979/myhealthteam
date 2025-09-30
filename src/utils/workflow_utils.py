"""
workflow_utils.py
Business logic and data access for workflow management (no Streamlit UI code).
"""

from src import database
from src.dashboards.workflow_module import create_workflow_instance

def create_workflow_task(coordinator_id, patient_name, workflow_type, priority, notes, estimated_duration):
    """Create a workflow task using the proper workflow database integration"""
    try:
        # Get the template_id for the selected workflow type
        conn = database.get_db_connection()
        template = conn.execute("""
            SELECT template_id FROM workflow_templates 
            WHERE template_name = ?
        """, (workflow_type,)).fetchone()
        conn.close()
        
        if not template:
            raise ValueError(f"Workflow template '{workflow_type}' not found")
        
        # Find patient_id from patient name
        patient_id = None
        conn = database.get_db_connection()
        # Try to match patient by name format "FirstName LastName"
        name_parts = patient_name.split(' ', 1)
        if len(name_parts) == 2:
            first_name, last_name = name_parts
            patient = conn.execute("""
                SELECT patient_id FROM patients 
                WHERE first_name = ? AND last_name = ?
            """, (first_name, last_name)).fetchone()
            if patient:
                patient_id = patient['patient_id']
        conn.close()
        
        if not patient_id:
            # Fallback: use patient name as identifier if exact match not found
            patient_id = patient_name
        
        # Create workflow instance using workflow module function
        instance_id = create_workflow_instance(
            template_id=template['template_id'],
            patient_id=patient_id,
            coordinator_id=coordinator_id,
            notes=f"Priority: {priority} | {notes}"
        )
        
        return instance_id is not None
        
    except Exception as e:
        print(f"Error creating workflow task: {e}")
        return False

def get_ongoing_workflows(user_id, user_role_ids=None):
    """Get ongoing workflows for a user: all active workflows where the user is the coordinator or the current owner."""
    try:
        conn = database.get_db_connection()
        # If user_role_ids contains 40 (CM), show all active workflows
        if user_role_ids and 40 in user_role_ids:
            query = """
                SELECT *, (
                    SELECT COUNT(*) FROM workflow_steps ws WHERE ws.template_id = wi.template_id
                ) as total_steps
                FROM workflow_instances wi
                WHERE workflow_status = 'Active'
                ORDER BY created_at DESC
            """
            workflows = conn.execute(query).fetchall()
        else:
            query = """
                SELECT *, (
                    SELECT COUNT(*) FROM workflow_steps ws WHERE ws.template_id = wi.template_id
                ) as total_steps
                FROM workflow_instances wi
                WHERE workflow_status = 'Active' AND (coordinator_id = ? OR current_owner_user_id = ?)
                ORDER BY created_at DESC
            """
            workflows = conn.execute(query, (user_id, user_id)).fetchall()
        conn.close()
        formatted_workflows = []
        for wf in workflows:
            wf = dict(wf)
            # Step progress
            current_step = wf.get('current_step', 1)
            total_steps = wf.get('total_steps', 0)
            # Defensive: if current_step > total_steps, clamp
            if total_steps and current_step > total_steps:
                current_step = total_steps
            formatted_workflows.append({
                'instance_id': wf['instance_id'],
                'patient_name': wf.get('patient_name', 'Unknown'),
                'workflow_type': wf.get('template_name'),
                'coordinator_id': wf.get('coordinator_id'),
                'coordinator_name': wf.get('coordinator_name'),
                'current_owner_user_id': wf.get('current_owner_user_id'),
                'current_owner_name': wf.get('current_owner_name'),
                'current_step': current_step,
                'total_steps': total_steps,
                'step_progress': f"Step {current_step} of {total_steps}" if total_steps else "N/A",
                'priority': wf.get('priority', 'Medium'),
                'created_date': wf.get('created_at')[:10] if wf.get('created_at') else 'N/A',
                'workflow_status': wf.get('workflow_status', 'Active'),
            })
        return formatted_workflows
    except Exception as e:
        print(f"Error getting ongoing workflows: {e}")
        return []
