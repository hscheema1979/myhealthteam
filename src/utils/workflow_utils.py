"""
workflow_utils.py
Business logic and data access for workflow management (no Streamlit UI code).
"""

import pandas as pd
from datetime import datetime
from src import database

# Role constants for better maintainability
ROLE_ADMIN = 34
ROLE_CARE_PROVIDER = 33
ROLE_CARE_COORDINATOR = 36
ROLE_COORDINATOR_MANAGER = 40
ROLE_ONBOARDING_TEAM = 37
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

def get_user_coordinator_id(user_id):
    """Get coordinator_id for a user_id, return None if not found"""
    if not user_id:
        return None
    
    conn = database.get_db_connection()
    try:
        # Check if user is a coordinator (role 36)
        user_roles = conn.execute(
            "SELECT role_id FROM user_roles WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        
        role_ids = [r['role_id'] for r in user_roles]
        if ROLE_CARE_COORDINATOR in role_ids:  # User is a coordinator, use their user_id
            return user_id
        
        # Check if user has any workflow assignments (they might be a coordinator even without role 36)
        workflow_check = conn.execute(
            "SELECT 1 FROM workflow_instances WHERE coordinator_id = ? LIMIT 1",
            (str(user_id),)
        ).fetchone()
        
        if workflow_check:
            return user_id  # User has workflow assignments, treat as coordinator
        
        return None  # No valid coordinator mapping
    finally:
        conn.close()


def get_ongoing_workflows(user_id, user_role_ids=None):
    """Get ongoing workflows for a user: all active workflows where the user is the coordinator or the current owner."""
    try:
        conn = database.get_db_connection()
        
        # For workflow reassignment, admin and coordinator managers should see ALL workflows
        if user_role_ids and (ROLE_COORDINATOR_MANAGER in user_role_ids or ROLE_ADMIN in user_role_ids):
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
            # For regular coordinators, show only their workflows
            # Exclude workflows where the current step belongs to a different role (e.g., RR)
            coordinator_id = get_user_coordinator_id(user_id)

            if coordinator_id:
                query = """
                    SELECT *, (
                        SELECT COUNT(*) FROM workflow_steps ws WHERE ws.template_id = wi.template_id
                    ) as total_steps
                    FROM workflow_instances wi
                    WHERE workflow_status = 'Active' AND (
                        CAST(coordinator_id AS TEXT) = CAST(? AS TEXT) OR
                        CAST(current_owner_user_id AS TEXT) = CAST(? AS TEXT)
                    )
                    AND (
                        wi.current_owner_role IS NULL
                        OR wi.current_owner_role = ''
                        OR wi.current_owner_role = 'CC'
                    )
                    ORDER BY created_at DESC
                """
                workflows = conn.execute(query, (str(coordinator_id), str(user_id))).fetchall()
            else:
                # No valid coordinator mapping, return empty
                workflows = []
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


def get_workflows_for_reassignment(user_id, user_role_ids=None):
    """
    Get workflows that can be reassigned, with proper filtering for user permissions.
    
    Args:
        user_id: User ID of the person requesting reassignment
        user_role_ids: List of role IDs for permission checking
        
    Returns:
        DataFrame with workflows ready for reassignment
    """
    # Use existing get_ongoing_workflows to get real workflow data
    workflows_data = get_ongoing_workflows(user_id, user_role_ids)
    
    if not workflows_data:
        return pd.DataFrame()
    
    # Convert to DataFrame
    workflows_df = pd.DataFrame(workflows_data)
    
    if not workflows_df.empty:
        # Keep original column names that the UI expects
        # The workflow_reassignment_ui.py expects these exact column names
        expected_columns = [
            'instance_id', 'workflow_type', 'patient_name', 'patient_id',
            'coordinator_name', 'coordinator_id', 'workflow_status', 
            'current_step', 'total_steps', 'priority', 'created_date'
        ]
        
        # Ensure all expected columns exist, add missing ones with None
        for col in expected_columns:
            if col not in workflows_df.columns:
                workflows_df[col] = None
        
        # Reorder columns to match expected order
        workflows_df = workflows_df[expected_columns]
        
        # Format dates nicely
        if 'created_date' in workflows_df.columns:
            workflows_df['created_date'] = pd.to_datetime(workflows_df['created_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
    return workflows_df


def get_available_coordinators():
    """
    Get list of coordinators available for reassignment.
    
    Returns:
        List of dicts with coordinator info
    """
    conn = database.get_db_connection()
    try:
        coordinators = conn.execute("""
            SELECT u.user_id, u.full_name, u.email 
            FROM users u 
            JOIN user_roles ur ON u.user_id = ur.user_id 
            WHERE ur.role_id = 36 
            AND u.status = 'active'
            ORDER BY u.full_name
        """).fetchall()
        
        return [dict(row) for row in coordinators]
    finally:
        conn.close()


def execute_workflow_reassignment(selected_instance_ids, target_coordinator_id, user_id, notes=None):
    """
    Execute bulk workflow reassignment with proper audit logging.
    
    Args:
        selected_instance_ids: List of workflow instance IDs to reassign
        target_coordinator_id: User ID of target coordinator
        user_id: User ID performing the reassignment (for audit)
        notes: Optional notes about the reassignment
        
    Returns:
        Integer count of successfully reassigned workflows (for UI compatibility)
        
    Raises:
        ValueError: If target coordinator is invalid
        Exception: For database or other errors
    """
    if not selected_instance_ids:
        return 0
    
    if not target_coordinator_id:
        raise ValueError("Target coordinator ID is required")
    
    import pandas as pd
    from datetime import datetime
    
    conn = database.get_db_connection()
    try:
        # Validate target coordinator exists and is active
        target_coordinator = conn.execute(
            """SELECT u.user_id, u.full_name, u.status 
               FROM users u 
               JOIN user_roles ur ON u.user_id = ur.user_id 
               WHERE u.user_id = ? AND ur.role_id = ? AND u.status = 'active'""",
            (target_coordinator_id, ROLE_CARE_COORDINATOR)
        ).fetchone()
        
        if not target_coordinator:
            # Check if user exists but is not a coordinator
            user_check = conn.execute(
                "SELECT full_name, status FROM users WHERE user_id = ?",
                (target_coordinator_id,)
            ).fetchone()
            
            if not user_check:
                raise ValueError(f"User ID {target_coordinator_id} not found")
            elif user_check['status'] != 'active':
                raise ValueError(f"User {user_check['full_name']} is not active")
            else:
                # Check if user has coordinator role
                role_check = conn.execute(
                    "SELECT 1 FROM user_roles WHERE user_id = ? AND role_id = ?",
                    (target_coordinator_id, ROLE_CARE_COORDINATOR)
                ).fetchone()
                if not role_check:
                    raise ValueError(f"User {user_check['full_name']} is not a coordinator")
                else:
                    raise ValueError(f"Coordinator validation failed for user {user_check['full_name']}")
            
        target_name = target_coordinator['full_name']
            
        target_name = target_coordinator['full_name']
        success_count = 0
        
        for instance_id in selected_instance_ids:
            try:
                # Get current assignment for audit
                current = conn.execute(
                    """SELECT coordinator_id, coordinator_name 
                       FROM workflow_instances 
                       WHERE instance_id = ?""",
                    (instance_id,)
                ).fetchone()
                
                if not current:
                    continue
                
                current_name = current['coordinator_name']
                
                # Skip if already assigned to target
                if str(current['coordinator_id']) == str(target_coordinator_id):
                    continue
                
                # Perform the reassignment
                conn.execute(
                    """UPDATE workflow_instances 
                       SET coordinator_id = ?, coordinator_name = ?, updated_at = CURRENT_TIMESTAMP 
                       WHERE instance_id = ?""",
                    (target_coordinator_id, target_name, instance_id)
                )
                
                # Log audit trail
                conn.execute(
                    """INSERT INTO audit_log (action_type, table_name, record_id, old_value, new_value, user_id, timestamp, description)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        "WORKFLOW_REASSIGNMENT",
                        "workflow_instances",
                        instance_id,
                        f"Coordinator: {current_name}",
                        f"Coordinator: {target_name}",
                        user_id,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        f"Bulk reassignment: Workflow {instance_id} reassigned from {current_name} to {target_name}"
                    )
                )
                
                success_count += 1
                
            except Exception as e:
                print(f"Error reassigning workflow {instance_id}: {str(e)}")
                conn.rollback()
        
        conn.commit()
        return success_count
        
    finally:
        conn.close()


def get_reassignment_summary(workflows_df):
    """
    Generate summary statistics for the current workflow assignments.
    
    Args:
        workflows_df: DataFrame with workflow data
        
    Returns:
        Dict with summary statistics
    """
    if workflows_df.empty:
        return {
            'total_workflows': 0,
            'by_coordinator': {},
            'by_workflow_type': {},
            'by_status': {},
            'avg_steps': 0
        }
    
    return {
        'total_workflows': len(workflows_df),
        'by_coordinator': workflows_df['coordinator_name'].value_counts().to_dict() if 'coordinator_name' in workflows_df.columns else {},
        'by_workflow_type': workflows_df['workflow_type'].value_counts().to_dict() if 'workflow_type' in workflows_df.columns else {},
        'by_status': workflows_df['workflow_status'].value_counts().to_dict() if 'workflow_status' in workflows_df.columns else {},
        'avg_steps': workflows_df['current_step'].mean() if 'current_step' in workflows_df.columns else 0
    }
