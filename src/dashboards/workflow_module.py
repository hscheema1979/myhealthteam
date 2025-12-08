import pandas as pd
from src.database import get_db_connection, normalize_patient_id, ensure_monthly_coordinator_tasks_table, count_completed_steps
import src.database as database

# --- Workflow Management Functions (moved from database.py) ---
def get_workflow_templates():
    """Get all available workflow templates from database"""
    conn = get_db_connection()
    try:
        templates = conn.execute("""
            SELECT template_id, template_name 
            FROM workflow_templates 
            ORDER BY template_name
        """).fetchall()
        return [dict(row) for row in templates]
    finally:
        conn.close()

def get_workflow_template_steps(template_id):
    """Get all steps for a specific workflow template"""
    conn = get_db_connection()
    try:
        steps = conn.execute("""
            SELECT step_id, step_order, task_name, owner, deliverable, cycle_time
            FROM workflow_steps 
            WHERE template_id = ?
            ORDER BY step_order
        """, (template_id,)).fetchall()
        return [dict(row) for row in steps]
    finally:
        conn.close()

def create_workflow_instance(template_id, patient_id, coordinator_id, notes=None):
    """Create a new workflow instance and return instance_id"""
    conn = get_db_connection()
    try:
        tmpl = conn.execute("SELECT template_name FROM workflow_templates WHERE template_id = ?", (template_id,)).fetchone()
        template_name = tmpl['template_name'] if tmpl is not None and 'template_name' in tmpl.keys() else None

        patient_name = None
        try:
            pid_row = conn.execute("SELECT first_name, last_name FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
            if pid_row:
                patient_name = f"{pid_row['first_name']} {pid_row['last_name']}".strip()
        except Exception:
            patient_name = None
        if not patient_name:
            patient_name = str(patient_id)

        coord_name = None
        try:
            coord_row = conn.execute("SELECT first_name, last_name FROM coordinators WHERE coordinator_id = ?", (coordinator_id,)).fetchone()
            if coord_row:
                coord_name = f"{coord_row['first_name']} {coord_row['last_name']}".strip()
        except Exception:
            coord_name = None

        patient_id_to_store = normalize_patient_id(patient_id, conn=conn)
        cursor = conn.execute("""
            INSERT INTO workflow_instances (template_id, template_name, patient_id, patient_name, coordinator_id, coordinator_name, workflow_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Active', datetime('now'))
        """, (template_id, template_name, patient_id_to_store, patient_name, coordinator_id, coord_name))
        instance_id = cursor.lastrowid
        conn.commit()

        pid_for_task = normalize_patient_id(patient_id, conn=conn)
        table_name = ensure_monthly_coordinator_tasks_table(conn=conn)
        conn.execute(f"""
            INSERT INTO {table_name} (
                coordinator_id, patient_id, task_date, task_type,
                duration_minutes, notes, source_system, imported_at
            ) VALUES (?, ?, date('now'), ?, 0, ?, 'WORKFLOW', CURRENT_TIMESTAMP)
        """, (
            coordinator_id,
            pid_for_task,
            f"WORKFLOW_START|{instance_id}",
            f"Workflow Instance {instance_id} started. {notes or ''}"
        ))
        conn.commit()
        return instance_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_active_workflow_instances(coordinator_id=None, patient_id=None):
    """Get active workflow instances with template information and computed completed steps."""
    conn = get_db_connection()
    try:
        # Base instances with total steps per template
        query = """
            SELECT 
                wi.instance_id,
                wi.template_id,
                wt.template_name,
                wi.workflow_status AS workflow_status,
                wi.created_at,
                p.first_name,
                p.last_name,
                wi.coordinator_id,
                COUNT(ws.step_id) as total_steps
            FROM workflow_instances wi
            JOIN workflow_templates wt ON wi.template_id = wt.template_id
            LEFT JOIN patients p ON wi.patient_id = p.patient_id
            LEFT JOIN workflow_steps ws ON wt.template_id = ws.template_id
            WHERE wi.workflow_status = 'Active'
        """
        params = []
        if patient_id:
            query += " AND wi.patient_id = ?"
            params.append(patient_id)
        if coordinator_id:
            query += " AND wi.coordinator_id = ?"
            params.append(coordinator_id)
        query += " GROUP BY wi.instance_id ORDER BY wi.created_at DESC"
        rows = conn.execute(query, tuple(params)).fetchall()

        # Compute completed steps across all monthly coordinator_tasks tables
        instances = []
        for r in rows:
            row = dict(r)
            try:
                completed = count_completed_steps(row['instance_id'], conn=conn)
            except Exception:
                completed = 0
            row['completed_steps'] = completed
            instances.append(row)
        return instances
    finally:
        conn.close()

def get_existing_progress_notes(instance_id, step_id):
    """Get existing progress notes for a workflow step from workflow_instances table"""
    conn = get_db_connection()
    try:
        # Get the step order to determine which step column to use
        step_info = conn.execute("""
            SELECT ws.step_order
            FROM workflow_steps ws
            JOIN workflow_instances wi ON wi.template_id = ws.template_id
            WHERE ws.step_id = ? AND wi.instance_id = ?
        """, (step_id, instance_id)).fetchone()
        
        if not step_info:
            return ""
        
        step_order = step_info['step_order']
        notes_column = f"step{step_order}_notes"
        
        # Get existing notes from workflow_instances table
        existing_notes = conn.execute(f"""
            SELECT {notes_column} FROM workflow_instances 
            WHERE instance_id = ?
        """, (instance_id,)).fetchone()
        
        return existing_notes[notes_column] if existing_notes and existing_notes[notes_column] else ""
        
    except Exception as e:
        print(f"Error retrieving progress notes: {e}")
        return ""
    finally:
        conn.close()

def save_progress_step(instance_id, step_id, coordinator_id, duration_minutes=0, notes=""):
    """Save progress on a workflow step by updating the workflow_instances table and optionally recording duration in coordinator_tasks"""
    conn = get_db_connection()
    try:
        # Get step information
        step_info = conn.execute("""
            SELECT ws.step_order, ws.task_name, wt.template_name
            FROM workflow_steps ws
            JOIN workflow_templates wt ON ws.template_id = wt.template_id
            JOIN workflow_instances wi ON wi.template_id = ws.template_id
            WHERE ws.step_id = ? AND wi.instance_id = ?
        """, (step_id, instance_id)).fetchone()
        
        if not step_info:
            raise ValueError("Step not found for this workflow instance")
        
        step_order = step_info['step_order']
        notes_column = f"step{step_order}_notes"
        
        # Get existing notes from workflow_instances
        existing_notes = conn.execute(f"""
            SELECT {notes_column} FROM workflow_instances 
            WHERE instance_id = ?
        """, (instance_id,)).fetchone()
        
        # Format the new progress entry with timestamp and special characters
        now = pd.Timestamp.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        progress_entry = f"▶ [{timestamp}] {notes}"
        
        # Append to existing notes or create new
        if existing_notes and existing_notes[notes_column]:
            combined_notes = f"{existing_notes[notes_column]}\n{progress_entry}"
        else:
            combined_notes = progress_entry
        
        # Update the workflow_instances table with the new notes
        conn.execute(f"""
            UPDATE workflow_instances 
            SET {notes_column} = ?, updated_at = CURRENT_TIMESTAMP
            WHERE instance_id = ?
        """, (combined_notes, instance_id))
        
        # Optionally record duration in coordinator_tasks if duration > 0
        if duration_minutes > 0:
            workflow_info = conn.execute("SELECT patient_id FROM workflow_instances WHERE instance_id = ?", (instance_id,)).fetchone()
            if workflow_info:
                now = pd.Timestamp.now()
                table_name = ensure_monthly_coordinator_tasks_table(year=now.year, month=now.month, conn=conn)
                
                # Insert duration record
                conn.execute(f"""
                    INSERT INTO {table_name} (
                        coordinator_id, patient_id, task_date, duration_minutes, 
                        task_type, notes, source_system, imported_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    coordinator_id,
                    workflow_info['patient_id'],
                    now.strftime('%Y-%m-%d'),
                    duration_minutes,
                    f'WORKFLOW_PROGRESS|{instance_id}|{step_id}',
                    f"Progress on {step_info['task_name']}: {notes}",
                    'workflow_module',
                    now.strftime('%Y-%m-%d %H:%M:%S')
                ))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        error_msg = f"Error saving workflow step progress: {e}"
        print(error_msg)
        # Also log to streamlit for debugging
        import streamlit as st
        st.error(f"Debug: {error_msg}")
        return False
    finally:
        conn.close()


def complete_workflow_step(instance_id, step_id, coordinator_id, duration_minutes=0, notes=""):
    """Mark a workflow step as completed by creating a coordinator task"""
    conn = get_db_connection()
    try:
        step_info = conn.execute("""
            SELECT ws.task_name, ws.step_order, wt.template_name
            FROM workflow_steps ws
            JOIN workflow_templates wt ON ws.template_id = wt.template_id
            JOIN workflow_instances wi ON wi.template_id = wt.template_id
            WHERE ws.step_id = ? AND wi.instance_id = ?
        """, (step_id, instance_id)).fetchone()
        if not step_info:
            raise ValueError("Step not found for this workflow instance")
        workflow_info = conn.execute("SELECT patient_id FROM workflow_instances WHERE instance_id = ?", (instance_id,)).fetchone()
        if not workflow_info:
            workflow_info = conn.execute("SELECT ct.patient_id FROM coordinator_tasks_2025_09 ct WHERE ct.task_type LIKE 'WORKFLOW_START|' || ? LIMIT 1", (instance_id,)).fetchone()
        if not workflow_info:
            raise ValueError("Workflow instance not found")
        patient_id = workflow_info['patient_id']
        pid_for_task = normalize_patient_id(patient_id, conn=conn)
        now = pd.Timestamp.now()
        table_name = ensure_monthly_coordinator_tasks_table(year=now.year, month=now.month, conn=conn)
        conn.execute(f"""
            INSERT INTO {table_name} (
                coordinator_id, patient_id, task_date, task_type,
                duration_minutes, notes, source_system, imported_at
            ) VALUES (?, ?, date('now'), ?, ?, ?, 'WORKFLOW', CURRENT_TIMESTAMP)
        """, (
            coordinator_id,
            pid_for_task,
            f"WORKFLOW_STEP|{instance_id}|{step_id}",
            duration_minutes,
            f"Completed: {step_info['task_name']} (Step {step_info['step_order']}). {notes}"
        ))
        conn.commit()
        try:
            step_order = step_info['step_order']
            step_col = f"step{step_order}_complete"
            notes_col = f"step{step_order}_notes"
            date_col = f"step{step_order}_date"
            duration_col = f"step{step_order}_duration_minutes"
            update_sql = f"UPDATE workflow_instances SET {step_col} = 1, {notes_col} = ?, {date_col} = date('now'), {duration_col} = ? WHERE instance_id = ?"
            conn.execute(update_sql, (notes, duration_minutes, instance_id))
            conn.commit()
        except Exception:
            pass
        total_steps = conn.execute("""
            SELECT COUNT(*) as count
            FROM workflow_steps ws
            JOIN workflow_instances wi ON ws.template_id = wi.template_id
            WHERE wi.instance_id = ?
        """, (instance_id,)).fetchone()['count']
        completed_steps = conn.execute(f"""
            SELECT COUNT(*) as count
            FROM {table_name} ct
            WHERE ct.task_type LIKE 'WORKFLOW_STEP|' || ? || '|%'
        """, (instance_id,)).fetchone()['count']
        if completed_steps >= total_steps:
            conn.execute("""
                    UPDATE workflow_instances 
                    SET workflow_status = 'Completed'
                    WHERE instance_id = ?
                """, (instance_id,))
            conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_workflow_progress(instance_id):
    """Get progress information for a specific workflow instance"""
    conn = get_db_connection()
    try:
        wi_row = conn.execute("SELECT * FROM workflow_instances WHERE instance_id = ?", (instance_id,)).fetchone()
        table_name = None
        if wi_row is not None and 'created_at' in wi_row.keys() and wi_row['created_at']:
            try:
                created_dt = pd.to_datetime(wi_row['created_at'])
                table_name = f"coordinator_tasks_{created_dt.year}_{str(created_dt.month).zfill(2)}"
            except Exception:
                table_name = None
        if not table_name:
            now = pd.Timestamp.now()
            table_name = f"coordinator_tasks_{now.year}_{str(now.month).zfill(2)}"
        table_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
        steps = conn.execute("""
            SELECT ws.step_id, ws.step_order, ws.task_name, ws.owner, ws.deliverable, ws.cycle_time, wt.template_name, wi.workflow_status, wi.created_at
            FROM workflow_steps ws
            JOIN workflow_templates wt ON ws.template_id = wt.template_id
            JOIN workflow_instances wi ON wi.template_id = wt.template_id
            WHERE wi.instance_id = ?
            ORDER BY ws.step_order
        """, (instance_id,)).fetchall()
        result = []
        for s in steps:
            s = dict(s)
            step_id = s['step_id']
            step_order = s['step_order']
            task_name = s['task_name']
            owner = s['owner']
            ct_row = None
            if table_exists:
                try:
                    ct_row = conn.execute(f"SELECT coordinator_task_id, task_date, duration_minutes, notes FROM {table_name} WHERE task_type = ? LIMIT 1", (f'WORKFLOW_STEP|{instance_id}|{step_id}',)).fetchone()
                except Exception:
                    ct_row = None
            completed = False
            completion_date = None
            duration_minutes = None
            completion_notes = None
            try:
                step_col = f'step{step_order}_complete'
                notes_col = f'step{step_order}_notes'
                if wi_row is not None and step_col in wi_row.keys() and wi_row[step_col]:
                    completed = True
                    completion_notes = wi_row[notes_col] if notes_col in wi_row.keys() else None
                elif ct_row is not None:
                    completed = True
                    completion_date = ct_row['task_date']
                    duration_minutes = ct_row['duration_minutes']
                    completion_notes = ct_row['notes']
            except Exception:
                if ct_row is not None:
                    completed = True
                    completion_date = ct_row['task_date']
                    duration_minutes = ct_row['duration_minutes']
                    completion_notes = ct_row['notes']
            result.append({
                'instance_id': wi_row['instance_id'] if wi_row is not None and 'instance_id' in wi_row.keys() else instance_id,
                'template_name': s.get('template_name'),
                'step_id': step_id,
                'step_order': step_order,
                'task_name': task_name,
                'owner': owner,
                'deliverable': s.get('deliverable'),
                'cycle_time': s.get('cycle_time'),
                'completed': completed,
                'completed_date': completion_date,
                'duration_minutes': duration_minutes,
                'completion_notes': completion_notes,
            })
        return result
    finally:
        conn.close()

def get_coordinator_workflow_tasks(coordinator_id, start_date=None, end_date=None):
    """Get workflow-related tasks for a coordinator within a date range"""
    conn = get_db_connection()
    try:
        query = """
            SELECT 
                ct.coordinator_task_id,
                ct.task_date,
                ct.task_type,
                ct.duration_minutes,
                ct.notes,
                ct.patient_id,
                p.first_name,
                p.last_name,
                CASE 
                    WHEN ct.task_type LIKE 'WORKFLOW_START|%' THEN 'Workflow Started'
                    WHEN ct.task_type LIKE 'WORKFLOW_STEP|%' THEN 'Step Completed'
                    ELSE 'Other Task'
                END as task_category
            FROM coordinator_tasks_2025_09 ct
            LEFT JOIN patients p ON ct.patient_id = p.patient_id
            WHERE ct.coordinator_id = ?
            AND (ct.task_type LIKE 'WORKFLOW_%')
        """
        params = [coordinator_id]
        if start_date:
            query += " AND ct.task_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND ct.task_date <= ?"
            params.append(end_date)
        query += " ORDER BY ct.task_date DESC"
        tasks = conn.execute(query, params).fetchall()
        return [dict(row) for row in tasks]
    finally:
        conn.close()
def get_display_workflows(user_id, coordinator_id, user_role_ids):
    """
    Returns a DataFrame and display columns for ongoing workflows, filtered by user role.
    CMs (role 40) see all, others see only their own/coordinator's workflows.
    """
    from src.utils.workflow_utils import get_ongoing_workflows
    # CM (role 40) sees all, others see only their own/coordinator's
    if user_role_ids and 40 in user_role_ids:
        ongoing_workflows = get_ongoing_workflows(None, user_role_ids=user_role_ids)
    else:
        # Pass user_id so workflow_utils maps to coordinator_id correctly
        ongoing_workflows = get_ongoing_workflows(user_id, user_role_ids=user_role_ids)
    workflow_data = []
    for wf in ongoing_workflows or []:
        workflow_data.append({
            'instance_id': wf.get('instance_id', ''),
            'patient_name': wf.get('patient_name', ''),
            'workflow_type': wf.get('workflow_type', ''),
            'coordinator_id': wf.get('coordinator_id', ''),
            'coordinator_name': wf.get('coordinator_name', ''),
            'current_owner_user_id': wf.get('current_owner_user_id', ''),
            'current_owner_name': wf.get('current_owner_name', ''),
            'current_step': wf.get('current_step', ''),
            'total_steps': wf.get('total_steps', ''),
            'step_progress': wf.get('step_progress', ''),
            'priority': wf.get('priority', ''),
            'created_date': wf.get('created_date', ''),
            'workflow_status': wf.get('workflow_status', ''),
        })
    df = pd.DataFrame(workflow_data)
    display_cols = [
        'instance_id', 'patient_name', 'workflow_type',
        'coordinator_id', 'coordinator_name',
        'current_owner_user_id', 'current_owner_name',
        'current_step', 'total_steps', 'step_progress',
        'priority', 'created_date', 'workflow_status'
    ]
    return df, display_cols

def render_workflow_table(df, display_cols, empty_message="No ongoing workflows found."):
    if not df.empty:
        st.dataframe(
            df[display_cols],
            use_container_width=True,
            height=400,
            column_config={
                "instance_id": st.column_config.TextColumn("Workflow Instance ID", width="small"),
                "patient_name": st.column_config.TextColumn("Patient", width="medium"),
                "workflow_type": st.column_config.TextColumn("Workflow Type", width="large"),
                "coordinator_id": st.column_config.TextColumn("Coordinator ID", width="small"),
                "coordinator_name": st.column_config.TextColumn("Coordinator Name", width="medium"),
                "current_owner_user_id": st.column_config.TextColumn("Current Owner User ID", width="small"),
                "current_owner_name": st.column_config.TextColumn("Current Owner Name", width="medium"),
                "current_step": st.column_config.NumberColumn("Current Step", width="small"),
                "total_steps": st.column_config.NumberColumn("Total Steps", width="small"),
                "step_progress": st.column_config.TextColumn("Step Progress", width="medium"),
                "priority": st.column_config.TextColumn("Priority", width="small"),
                "created_date": st.column_config.TextColumn("Created", width="small"),
                "workflow_status": st.column_config.TextColumn("Status", width="small"),
            },
            hide_index=True
        )
    else:
        st.info(empty_message)
        # Always show the table, even if empty
        empty_df = pd.DataFrame(columns=display_cols)
        st.dataframe(
            empty_df,
            use_container_width=True,
            height=200,
            column_config={
                "instance_id": st.column_config.TextColumn("Workflow Instance ID", width="small"),
                "patient_name": st.column_config.TextColumn("Patient", width="medium"),
                "workflow_type": st.column_config.TextColumn("Workflow Type", width="large"),
                "coordinator_id": st.column_config.TextColumn("Coordinator ID", width="small"),
                "coordinator_name": st.column_config.TextColumn("Coordinator Name", width="medium"),
                "current_owner_user_id": st.column_config.TextColumn("Current Owner User ID", width="small"),
                "current_owner_name": st.column_config.TextColumn("Current Owner Name", width="medium"),
                "current_step": st.column_config.NumberColumn("Current Step", width="small"),
                "total_steps": st.column_config.NumberColumn("Total Steps", width="small"),
                "step_progress": st.column_config.TextColumn("Step Progress", width="medium"),
                "priority": st.column_config.TextColumn("Priority", width="small"),
                "created_date": st.column_config.TextColumn("Created", width="small"),
                "workflow_status": st.column_config.TextColumn("Status", width="small"),
            },
            hide_index=True
        )
import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
from src import database


def show_workflow_management(user_id, coordinator_id, active_patients, filtered_patients=None, user_role_ids=None):
    from src.utils.workflow_utils import get_ongoing_workflows
    workflow_data = get_ongoing_workflows(user_id, user_role_ids)
    
    # Filter workflows to only show those for patients currently visible in the patient filter
    if filtered_patients and len(filtered_patients) > 0:
        # Get patient IDs from filtered patients
        filtered_patient_ids = set()
        for patient in filtered_patients:
            patient_id = patient.get('patient_id')
            if patient_id:
                filtered_patient_ids.add(str(patient_id))
        
        # Filter workflow data to only include workflows for filtered patients
        filtered_workflow_data = []
        for wf in workflow_data or []:
            wf_patient_id = str(wf.get('patient_id', ''))
            if wf_patient_id in filtered_patient_ids:
                filtered_workflow_data.append(wf)
        
        workflow_data = filtered_workflow_data

    # --- Add custom CSS for workflow action buttons ---
    st.markdown("""
        <style>
        .workflow-action-btn button {
            min-width: 160px !important;
            white-space: nowrap !important;
        }
        </style>
    """, unsafe_allow_html=True)
    """
    Modular workflow management UI: quick start, ongoing workflows, and workflow actions.
    """
    # --- Top row: Quick Actions (col1) and Ongoing Workflows (col2) ---
    top_col1, top_col2 = st.columns([1, 2])

    with top_col1:
        st.markdown("**Quick Start Workflow**")
        with st.form("quick_start_workflow_form"):
            # Patient selection
            if active_patients and isinstance(active_patients, list):
                patient_options = ["Select Patient..."] + active_patients
            else:
                patient_options = ["Select Patient..."]
            selected_patient = st.selectbox("Patient", patient_options, index=0)

            # Workflow type selection - get from database
            try:
                conn = get_db_connection()
                cursor = conn.execute("SELECT template_name FROM workflow_templates ORDER BY template_name")
                workflow_templates = cursor.fetchall()
                conn.close()
                onboarding_workflow_names = [
                    "POT_Patient_Onboarding",
                    "Patient Onboarding",
                    "Onboarding",
                ]
                workflow_types = [
                    template[0] for template in workflow_templates
                    if template[0] not in onboarding_workflow_names
                    and not template[0].lower().startswith("onboarding")
                    and "onboard" not in template[0].lower()
                    and "future" not in template[0].lower()
                ]
            except Exception:
                workflow_types = [
                    "LAB ROUTINE", "LAB URGENT",
                    "IMAGING ROUTINE", "IMAGING URGENT",
                    "DME REFERRAL", "HHC REFERRAL", "SPECIALIST REFERRAL",
                    "MEDICAL RECORDS", "PRIOR AUTHORIZATION",
                    "MEDICATION REFILL", "MEDICATION PROBLEM"
                ]
            selected_workflow = st.selectbox("Workflow Type", workflow_types)

            # Priority level
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Urgent"])

            # Task notes
            task_notes = st.text_area("Task Notes", height=80, placeholder="Enter task details or special instructions...")

            submitted = st.form_submit_button("Start Workflow", use_container_width=True)

            if submitted:
                if selected_patient != "Select Patient..." and task_notes.strip():
                    try:
                        # Create workflow task in database
                        success = create_workflow_task(
                            user_id=user_id,
                            patient_name=selected_patient,
                            workflow_type=selected_workflow,
                            priority=priority,
                            notes=task_notes,
                            estimated_duration=0  # Not needed for workflow kickoff
                        )
                        if success:
                            st.success(f"Workflow started: {selected_workflow} for {selected_patient}")
                            st.rerun()
                        else:
                            st.error("Failed to start workflow")
                    except Exception as e:
                        st.error(f"Error starting workflow: {str(e)}")
                else:
                    st.warning("Please select a patient and add workflow notes")

    with top_col2:
        st.markdown("**Ongoing Workflows**")
        if st.button("Refresh Workflows", key="refresh_workflows_btn"):
            st.rerun()
        df, display_cols = get_display_workflows(user_id, coordinator_id, user_role_ids)
        render_workflow_table(df, display_cols)

    # --- Second row: Workflow selection dropdown (left) and workflow steps/details (right) ---
    st.markdown("---")
    left_col, right_col = st.columns([3, 3])

    # Prepare workflow options for dropdown
    workflow_options = {}
    if not df.empty:
        for _, row in df.iterrows():
            label = f"{row['patient_name']} - {row['workflow_type']} (ID: {row['instance_id']})"
            workflow_options[label] = row['instance_id']

    with left_col:
        selected_instance_id = None
        if workflow_options:
            selected_workflow_text = st.selectbox(
                "Select Ongoing Workflow:",
                list(workflow_options.keys()),
                key="workflow_action_select_dropdown",
                label_visibility="visible"
            )
            selected_instance_id = workflow_options[selected_workflow_text]
            # --- Place Resume Workflow, Complete Next Step, and Assign to Me in a single row ---
            if selected_instance_id:
                resume_btn_key = f"resume_workflow_{selected_instance_id}"
                resume_state_key = f"resume_state_{selected_instance_id}"
                if resume_state_key not in st.session_state:
                    st.session_state[resume_state_key] = False
                
                # Check if user has permission to assign workflows (only Jan and Jose)
                can_assign_workflows = False
                try:
                    # Get current user info to check permissions
                    from src.database import get_user_by_id
                    current_user = get_user_by_id(user_id)
                    if current_user:
                        # Access full_name (works for both sqlite3.Row and dict)
                        user_name = current_user['full_name'] if 'full_name' in current_user.keys() else current_user.get('full_name', 'Unknown User')
                        # Check if user is Jan or Jose (supervisors/managers)
                        can_assign_workflows = user_name in ['Estomo, Jan', 'Soberanis, Jose']
                except Exception:
                    can_assign_workflows = False
                
                btn_col1, btn_col2 = st.columns([1, 1])
                with btn_col1:
                    if st.button("Resume Workflow", key=resume_btn_key):
                        st.session_state[resume_state_key] = True
                with btn_col2:
                    if st.button("Complete Next Step", key=f"complete_next_{selected_instance_id}"):
                        try:
                            msg = complete_next_step(selected_instance_id, user_id)
                            st.success(msg)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                
                # Show assignment controls only for supervisors
                if can_assign_workflows:
                    st.markdown("---")
                    st.markdown("### Workflow Assignment")
                    
                    # Get list of all coordinators for assignment
                    try:
                        from src.database import get_users_by_role
                        all_coordinators = get_users_by_role(36)  # 36 = Care Coordinator role
                        coordinator_options = {}
                        for coord in all_coordinators:
                            coord_name = f"{coord.get('full_name', coord.get('username', 'Unknown'))}"
                            coord_id = coord.get('user_id')
                            if coord_id:
                                coordinator_options[coord_name] = coord_id
                        
                        # Remove current user from options for assignment (can't assign to self)
                        current_user = get_user_by_id(user_id)
                        if current_user:
                            current_user_name = current_user['full_name'] if 'full_name' in current_user.keys() else current_user.get('full_name', '')
                            coordinator_options.pop(current_user_name, None)
                        
                        if coordinator_options:
                            assignment_col1, assignment_col2 = st.columns([2, 1])
                            with assignment_col1:
                                selected_coord_name = st.selectbox(
                                    "Assign workflow to:",
                                    list(coordinator_options.keys()),
                                    key=f"assign_to_select_{selected_instance_id}"
                                )
                            with assignment_col2:
                                if st.button("Assign", key=f"assign_workflow_{selected_instance_id}"):
                                    try:
                                        target_coordinator_id = coordinator_options[selected_coord_name]
                                        msg = assign_workflow_to_user(selected_instance_id, target_coordinator_id)
                                        st.success(msg)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        else:
                            st.info("No other coordinators available for assignment.")
                    except Exception as e:
                        st.error(f"Error loading coordinator list: {e}")
                st.markdown("<div style='height: 0.5em'></div>", unsafe_allow_html=True)
                # Add Note form below the button row
                with st.form(f"add_note_form_{selected_instance_id}", clear_on_submit=True):
                    note = st.text_area("Add Note", key=f"note_{selected_instance_id}", height=68, label_visibility="collapsed")
                    submitted = st.form_submit_button("Add Note")
                    if submitted and note.strip():
                        try:
                            msg = add_note_to_workflow(selected_instance_id, user_id, note)
                            st.success(msg)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                st.markdown("<div style='height: 0.5em'></div>", unsafe_allow_html=True)
                if st.button("Complete Workflow", key=f"complete_workflow_{selected_instance_id}"):
                    try:
                        msg = complete_workflow(selected_instance_id, user_id)
                        st.success(msg)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.info("No ongoing workflows to select.")

    # Only render steps in right column if Resume Workflow is clicked
    if selected_instance_id:
        resume_state_key = f"resume_state_{selected_instance_id}"
        if resume_state_key in st.session_state and st.session_state[resume_state_key]:
            with right_col:
                render_workflow_steps(selected_instance_id, user_id, user_role_ids)
        else:
            with right_col:
                st.empty()

# --- Modular function to render workflow steps/details ---
def render_workflow_steps(instance_id, user_id, user_role_ids):
    try:
        progress = get_workflow_progress(instance_id)
    except Exception as e:
        st.error(f"Error loading workflow progress: {e}")
        return
    if not progress:
        st.info("No steps found for this workflow.")
        return
    st.subheader(f"Resume Workflow - {progress[0]['template_name'] if progress and 'template_name' in progress[0] else instance_id}")

    # Get patient name for this workflow
    patient_name = "Unknown Patient"
    try:
        conn = get_db_connection()
        patient_row = conn.execute("""
            SELECT p.first_name || ' ' || p.last_name as patient_name
            FROM workflow_instances wi
            JOIN patients p ON wi.patient_id = p.patient_id
            WHERE wi.instance_id = ?
        """, (instance_id,)).fetchone()
        if patient_row:
            patient_name = patient_row['patient_name']
        conn.close()
    except Exception as e:
        print(f"Error getting patient name: {e}")

    for p in progress:
        step_id = p.get('step_id')
        step_order = p.get('step_order')
        task_name = p.get('task_name')
        owner = p.get('owner')
        completed = p.get('completed')
        completed_date = p.get('completed_date')

        st.markdown("---")
        st.markdown(f"#### Step {step_order}: {task_name}")

        # Patient and Task in same row - disabled dropdowns for familiar visual
        pat_col, task_col = st.columns(2)
        with pat_col:
            st.selectbox(
                "Patient",
                [patient_name],
                index=0,
                disabled=True,
                key=f"patient_select_{step_id}",
                label_visibility="collapsed"
            )
        with task_col:
            st.selectbox(
                "Task",
                [task_name],
                index=0,
                disabled=True,
                key=f"task_select_{step_id}",
                label_visibility="collapsed"
            )

        st.caption(f"Owner: {owner}")

        if completed:
            st.success(f"Completed on: {completed_date}")
            # Display completion notes in read-only format
            completion_notes = p.get('completion_notes', '').strip()
            if completion_notes:
                st.info(f"**Notes:** {completion_notes}")
        else:
            # Timer state keys
            timer_key = f"wf_{instance_id}_step_{step_id}_timer"
            start_key = f"{timer_key}_start"
            stop_key = f"{timer_key}_stop"
            running_key = f"{timer_key}_running"

            # Initialize timer state
            if start_key not in st.session_state:
                st.session_state[start_key] = None
            if stop_key not in st.session_state:
                st.session_state[stop_key] = None
            if running_key not in st.session_state:
                st.session_state[running_key] = False

            # Calculate duration in seconds
            from datetime import datetime
            start_time = st.session_state[start_key]
            stop_time = st.session_state[stop_key]
            is_running = st.session_state[running_key]

            if is_running and start_time:
                duration_seconds = int((datetime.now() - start_time).total_seconds())
            elif stop_time and start_time:
                total_duration = (stop_time - start_time).total_seconds()
                duration_seconds = int(total_duration)
            else:
                duration_seconds = 0

            # Timer controls - 4 columns: timer, start/stop, reset, duration
            timer_display_col, start_stop_col, reset_col, duration_col = st.columns([1, 1, 1, 1])

            with timer_display_col:
                minutes, seconds = divmod(duration_seconds, 60)
                st.markdown(f"**{minutes:02d}:{seconds:02d}**")

            with start_stop_col:
                if not is_running:
                    if st.button("Start", key=f"start_{instance_id}_{step_id}"):
                        st.session_state[start_key] = datetime.now()
                        st.session_state[running_key] = True
                        st.session_state[stop_key] = None
                else:
                    if st.button("Stop", key=f"stop_{instance_id}_{step_id}"):
                        st.session_state[stop_key] = datetime.now()
                        st.session_state[running_key] = False

            with reset_col:
                if st.button("Reset", key=f"reset_{instance_id}_{step_id}"):
                    st.session_state[start_key] = None
                    st.session_state[stop_key] = None
                    st.session_state[running_key] = False

            with duration_col:
                st.number_input("", min_value=0, value=duration_seconds//60 if duration_seconds else 30, key=f"duration_{instance_id}_{step_id}", label_visibility="collapsed")

            # Notes area with existing progress display
            note_key = f"wf_{instance_id}_step_{step_id}_note"
            clear_flag_key = f"clear_notes_{instance_id}_{step_id}"
            
            # Get existing progress notes
            existing_notes = get_existing_progress_notes(instance_id, step_id)
            
            # Show existing progress if any
            if existing_notes:
                st.markdown("**Previous Progress:**")
                st.text_area("", value=existing_notes, height=100, disabled=True, key=f"existing_{instance_id}_{step_id}", label_visibility="collapsed")
            
            # Show today's date and format guide
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            st.markdown(f"**Add New Notes** (will be saved as: ▶ [{today}] your_notes_here)")
            
            # Check if we need to clear notes from previous save
            if st.session_state.get(clear_flag_key, False):
                st.session_state[note_key] = ""
                st.session_state[clear_flag_key] = False
            
            notes = st.text_area("", value=st.session_state.get(note_key, ""), key=note_key, height=80, label_visibility="collapsed", placeholder="Enter your progress notes here...")

            # Save Progress and Complete Step buttons in two columns
            save_col, complete_col = st.columns(2)
            
            with save_col:
                if st.button("Save Progress", key=f"save_progress_{instance_id}_{step_id}", use_container_width=True, type="secondary"):
                    try:
                        # Use duration from number_input if available
                        duration = st.session_state.get(f"duration_{instance_id}_{step_id}", 30)
                        if notes.strip():  # Only save if there are notes
                            success = save_progress_step(instance_id, step_id, user_id, duration_minutes=duration, notes=notes)
                            if success:
                                st.success("Progress saved!")
                                # Set a flag to clear notes on next rerun
                                st.session_state[f"clear_notes_{instance_id}_{step_id}"] = True
                                st.rerun()
                            else:
                                st.error("Failed to save progress. Please try again.")
                        else:
                            st.warning("Please add notes before saving progress.")
                    except Exception as e:
                        st.error(f"Error saving progress: {e}")
            
            with complete_col:
                if st.button(f"Complete Step", key=f"complete_step_{instance_id}_{step_id}", use_container_width=True, type="primary"):
                    try:
                        # Use duration from number_input if available
                        duration = st.session_state.get(f"duration_{instance_id}_{step_id}", 30)
                        complete_workflow_step(instance_id, step_id, user_id, duration_minutes=duration, notes=notes)
                        st.success(f"Step {step_order} marked complete.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error completing step: {e}")

# --- Modular function to render workflow actions ---

# --- Helper functions for workflow actions ---
def complete_next_step(instance_id, user_id):
    """Mark the next incomplete step as complete."""
    progress = get_workflow_progress(instance_id)
    next_step = None
    for step in progress:
        if not step.get('completed'):
            next_step = step
            break
    if not next_step:
        return "All steps already completed."
    # For demo, use 30 min and generic note
    complete_workflow_step(instance_id, next_step['step_id'], user_id, duration_minutes=30, notes="Auto-completed via UI.")
    return f"Step {next_step['step_order']} marked complete."

def assign_workflow_to_me(instance_id, user_id):
    """Assign the workflow to the current user (if supported)."""
    # For demo, update coordinator_id in workflow_instances
    conn = get_db_connection()
    try:
        conn.execute("UPDATE workflow_instances SET coordinator_id = ? WHERE instance_id = ?", (user_id, instance_id))
        conn.commit()
        return "Workflow assigned to you."
    finally:
        conn.close()

def assign_workflow_to_user(instance_id, target_coordinator_id):
    """Assign the workflow to a specific coordinator."""
    conn = get_db_connection()
    try:
        # Get coordinator name for the success message
        coord_row = conn.execute("SELECT full_name FROM users WHERE user_id = ?", (target_coordinator_id,)).fetchone()
        coord_name = coord_row['full_name'] if coord_row and 'full_name' in coord_row.keys() else coord_row.get('full_name', 'Unknown') if coord_row else 'Unknown User'
        
        conn.execute("UPDATE workflow_instances SET coordinator_id = ? WHERE instance_id = ?", (target_coordinator_id, instance_id))
        conn.commit()
        return f"Workflow assigned to {coord_name}."
    finally:
        conn.close()

def add_note_to_workflow(instance_id, user_id, note):
    """Add a note to the workflow (as a coordinator task)."""
    conn = get_db_connection()
    try:
        # Get patient_id for this workflow
        row = conn.execute("SELECT patient_id FROM workflow_instances WHERE instance_id = ?", (instance_id,)).fetchone()
        patient_id = row['patient_id'] if row else None
        if not patient_id:
            raise Exception("Patient not found for workflow.")
        table_name = ensure_monthly_coordinator_tasks_table(conn=conn)
        # Insert the note entry
        conn.execute(f"""
            INSERT INTO {table_name} (
                coordinator_id, patient_id, task_date, task_type,
                duration_minutes, notes, source_system, imported_at
            ) VALUES (?, ?, date('now'), ?, 0, ?, 'WORKFLOW', CURRENT_TIMESTAMP)
        """, (
            user_id,
            patient_id,
            f"WORKFLOW_NOTE|{instance_id}",
            note
        ))
        conn.commit()
        return "Note added to workflow."
    finally:
        conn.close()

def complete_workflow(instance_id, user_id):
    """Force-complete the workflow (set status to Completed)."""
    conn = get_db_connection()
    try:
        conn.execute("UPDATE workflow_instances SET workflow_status = 'Completed' WHERE instance_id = ?", (instance_id,))
        conn.commit()
        return "Workflow marked as completed!"
    finally:
        conn.close()

# Helper functions moved from dashboard
from src.utils.workflow_utils import create_workflow_task

from src.utils.workflow_utils import get_ongoing_workflows

# You can also move helper functions like create_workflow_task, get_ongoing_workflows, etc. here as needed.


