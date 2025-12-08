"""
workflow_utils.py
Business logic and data access for workflow management (no Streamlit UI code).
"""

from src import database
# Temporarily commented out to fix circular import for testing
# from src.dashboards.workflow_module import create_workflow_instance

def create_workflow_task(user_id, patient_name, workflow_type, priority, notes, estimated_duration):
    """Create a workflow task using the proper workflow database integration"""
    try:
        conn = database.get_db_connection()
        
        # Use user_id directly as coordinator_id (no separate coordinator table lookup needed)
        coordinator_id = user_id
        
        # Get the template_id for the selected workflow type
        template = conn.execute("""
            SELECT template_id FROM workflow_templates 
            WHERE template_name = ?
        """, (workflow_type,)).fetchone()
        
        if not template:
            conn.close()
            raise ValueError(f"Workflow template '{workflow_type}' not found")
        
        # Find patient_id from patient name
        patient_id = None
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
        
        if not patient_id:
            # Fallback: use patient name as identifier if exact match not found
            patient_id = patient_name
        
        conn.close()
        
        # Import here to avoid circular import
        from src.dashboards.workflow_module import create_workflow_instance
        
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
        
        # Map user_id to coordinator_id when possible; fall back to user_id if no mapping
        coordinator_id = None
        if user_id is not None:
            try:
                row = conn.execute(
                    "SELECT coordinator_id FROM coordinators WHERE user_id = ?",
                    (user_id,)
                ).fetchone()
                if row and 'coordinator_id' in row.keys():
                    coordinator_id = row['coordinator_id']
                else:
                    coordinator_id = user_id
            except Exception:
                coordinator_id = user_id
        
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
                WHERE workflow_status = 'Active' AND (
                    CAST(coordinator_id AS TEXT) = CAST(? AS TEXT) OR
                    CAST(current_owner_user_id AS TEXT) = CAST(? AS TEXT)
                )
                ORDER BY created_at DESC
            """
            workflows = conn.execute(query, (str(coordinator_id), str(user_id))).fetchall()
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
                'patient_id': wf.get('patient_id'),  # Added for filtering by patient
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
