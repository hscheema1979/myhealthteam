def get_coordinator_patient_minutes_for_month(coordinator_id, year, month):
    """Return a dict mapping patient_id to total minutes for this coordinator and month."""
    conn = get_db_connection()
    try:
        table_name = f"coordinator_tasks_{year}_{str(month).zfill(2)}"
        # Check if table exists
        table_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
        if not table_exists:
            return {}
        # Query sum of duration_minutes per patient for this coordinator
        query = f"""
            SELECT patient_id, SUM(duration_minutes) as total_minutes
            FROM {table_name}
            WHERE coordinator_id = ?
            GROUP BY patient_id
        """
        result = conn.execute(query, (coordinator_id,)).fetchall()
        return {row['patient_id']: row['total_minutes'] or 0 for row in result}
    except Exception as e:
        print(f"Error in get_coordinator_patient_minutes_for_month: {e}")
        return {}
    finally:
        conn.close()
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = 'production.db'

def get_coordinator_monthly_minutes_live():
    """
    Returns a list of dicts: [{ 'coordinator_id': ..., 'total_minutes': ... }]
    Aggregates sum of duration_minutes for each coordinator from the current month's coordinator_tasks table.
    """
    conn = get_db_connection()
    try:
        now = pd.Timestamp.now()
        year = now.year
        month = now.month
        table_name = f"coordinator_tasks_{year}_{str(month).zfill(2)}"
        # Check if table exists
        table_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
        if not table_exists:
            return []
        df = pd.read_sql_query(f"SELECT coordinator_id, duration_minutes FROM {table_name} WHERE duration_minutes IS NOT NULL AND duration_minutes > 0", conn)
        if df.empty:
            return []
        summary = df.groupby('coordinator_id').agg({'duration_minutes':'sum'}).reset_index()
        summary = summary.rename(columns={'coordinator_id':'coordinator_id','duration_minutes':'total_minutes'})
        return summary.to_dict(orient='records')
    finally:
        conn.close()


DB_PATH = 'production.db'

def get_db_connection(db_path: str = None):
    """Return a SQLite connection. If db_path provided, use that path (useful for update_data.db)."""
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_patient_id(patient_id, conn=None):
    """Normalize patient_id into the new canonical string format: "Last First YYYY-MM-DD".
    If patient_id is numeric (or numeric string), look up the patient and return "Last First DOB" (no commas).
    Otherwise, strip commas and collapse whitespace.
    """
    close_conn = False
    try:
        if conn is None:
            conn = get_db_connection()
            close_conn = True

        # If numeric, try to look up patient
        try:
            pid_int = int(patient_id)
        except Exception:
            pid_int = None

        if pid_int is not None:
            row = conn.execute("SELECT last_name, first_name, date_of_birth FROM patients WHERE patient_id = ?", (pid_int,)).fetchone()
            if row:
                last = (row['last_name'] or '').strip()
                first = (row['first_name'] or '').strip()
                dob = row['date_of_birth'] if 'date_of_birth' in row.keys() else None
                parts = []
                if last:
                    parts.append(last.replace(',', ''))
                if first:
                    parts.append(first.replace(',', ''))
                if dob:
                    parts.append(str(dob))
                return ' '.join(parts).strip()

        # Otherwise normalize string: remove commas and collapse whitespace
        s = str(patient_id or '')
        s = s.replace(',', ' ').strip()
        s = ' '.join(s.split())
        return s
    finally:
        if close_conn and conn:
            conn.close()


def generate_patient_id(first_name, last_name, date_of_birth):
    """Generate a proper patient_id in the format: LASTNAME FIRSTNAME MM/DD/YYYY
    
    Args:
        first_name (str): Patient's first name
        last_name (str): Patient's last name  
        date_of_birth (str): Patient's date of birth (YYYY-MM-DD format)
    
    Returns:
        str: Patient ID in format "LASTNAME FIRSTNAME MM/DD/YYYY"
    """
    # Clean and normalize the components (uppercase to match existing patient IDs)
    last = (last_name or '').strip().upper().replace(',', '').replace(' ', '')
    first = (first_name or '').strip().upper().replace(',', '').replace(' ', '')
    dob = str(date_of_birth or '').strip()
    
    # Convert date from YYYY-MM-DD to MM/DD/YYYY format
    if dob and len(dob) == 10 and dob.count('-') == 2:
        try:
            year, month, day = dob.split('-')
            dob = f"{month}/{day}/{year}"
        except:
            pass  # Keep original format if conversion fails
    
    # Build the patient_id
    parts = []
    if last:
        parts.append(last)
    if first:
        parts.append(first)
    if dob:
        parts.append(dob)
    
    return ' '.join(parts)


def get_all_users():
    conn = get_db_connection()
    users = conn.execute('SELECT user_id, username, full_name, first_name, last_name, email, status, hire_date FROM users ORDER BY hire_date DESC').fetchall()
    conn.close()
    return users

def get_all_roles():
    conn = get_db_connection()
    roles = conn.execute('SELECT role_id, role_name FROM roles').fetchall()
    conn.close()
    return roles

def get_user_roles_by_user_id(user_id):
    conn = get_db_connection()
    user_roles = conn.execute('SELECT r.role_name, r.role_id, ur.is_primary FROM roles r JOIN user_roles ur ON r.role_id = ur.role_id WHERE ur.user_id = ?', (user_id,)).fetchall()
    conn.close()
    return user_roles


def get_onboarding_queue_stats():
    """Get onboarding queue statistics"""
    conn = get_db_connection()
    try:
        # Get stats from onboarding_patients table
        onboarding_stats = conn.execute("""
            SELECT 
                COUNT(*) as total_onboarding,
                SUM(CASE WHEN patient_id IS NULL THEN 1 ELSE 0 END) as pending_provider_assignment,
                SUM(CASE WHEN stage1_complete = 0 THEN 1 ELSE 0 END) as pending_initial_contact,
                SUM(CASE WHEN stage2_complete = 0 AND stage1_complete = 1 THEN 1 ELSE 0 END) as pending_tv_visit,
                SUM(CASE WHEN stage3_complete = 0 AND stage2_complete = 1 THEN 1 ELSE 0 END) as pending_documentation,
                SUM(CASE WHEN assigned_pot_user_id IS NULL THEN 1 ELSE 0 END) as unassigned_pot
            FROM onboarding_patients 
            WHERE patient_status = 'Active'
        """).fetchone()
        
        # Get stats from regular patients who might be in onboarding
        patient_stats = conn.execute("""
            SELECT 
                COUNT(CASE WHEN p.status LIKE 'Active%' AND upa.user_id IS NULL THEN 1 END) as unassigned_active_patients,
                COUNT(CASE WHEN p.status = 'Active' AND p.created_date > date('now', '-30 days') THEN 1 END) as new_patients_30_days
            FROM patients p
            LEFT JOIN user_patient_assignments upa ON p.patient_id = upa.patient_id
        """).fetchone()
        
        return {
            'total_onboarding': onboarding_stats['total_onboarding'] or 0,
            'pending_provider_assignment': onboarding_stats['pending_provider_assignment'] or 0,
            'pending_initial_contact': onboarding_stats['pending_initial_contact'] or 0,
            'pending_tv_visit': onboarding_stats['pending_tv_visit'] or 0,
            'pending_documentation': onboarding_stats['pending_documentation'] or 0,
            'unassigned_pot': onboarding_stats['unassigned_pot'] or 0,
            'unassigned_active_patients': patient_stats['unassigned_active_patients'] or 0,
            'new_patients_30_days': patient_stats['new_patients_30_days'] or 0
        }
    finally:
        conn.close()

def get_onboarding_tasks_by_role(role_id, user_id=None):
    """Get onboarding tasks for a specific role or user"""
    conn = get_db_connection()
    try:
        if role_id == 36:  # Care Coordinator
            query = """
                SELECT 
                    op.first_name,
                    op.last_name,
                    op.created_date,
                    CASE 
                        WHEN op.stage1_complete = 0 THEN 'Initial Contact Needed'
                        WHEN op.stage2_complete = 0 THEN 'TV Visit Scheduling'
                        WHEN op.stage3_complete = 0 THEN 'Documentation Review'
                        ELSE 'Ready for Provider Assignment'
                    END as task_status
                FROM onboarding_patients op
                WHERE op.patient_status = 'Active'
                AND (op.assigned_pot_user_id = ? OR op.assigned_pot_user_id IS NULL)
                ORDER BY op.created_date ASC
            """
            tasks = conn.execute(query, (user_id,)).fetchall()
        elif role_id == 33:  # Care Provider
            query = """
                SELECT 
                    op.first_name,
                    op.last_name,
                    op.created_date,
                    'Provider Assignment Needed' as task_status
                FROM onboarding_patients op
                WHERE op.patient_status = 'Active'
                AND op.patient_id IS NULL
                AND op.stage2_complete = 1
                ORDER BY op.created_date ASC
            """
            tasks = conn.execute(query).fetchall()
        else:
            tasks = []
        
        return [dict(task) for task in tasks]
    finally:
        conn.close()

def get_onboarding_patient_details(onboarding_id):
    """Get detailed onboarding patient information for stepper display"""
    conn = get_db_connection()
    try:
        # Get onboarding patient data
        patient = conn.execute("""
            SELECT * FROM onboarding_patients 
            WHERE onboarding_id = ?
        """, (onboarding_id,)).fetchone()
        
        if patient:
            patient_dict = dict(patient)
            
            # Check if patient exists in patients table and get actual initial_tv_completed status
            if patient_dict.get('patient_id'):
                patients_data = conn.execute("""
                    SELECT initial_tv_completed, initial_tv_completed_date, initial_tv_notes
                    FROM patients 
                    WHERE patient_id = ?
                """, (patient_dict['patient_id'],)).fetchone()
                
                if patients_data:
                    # Override onboarding table values with actual patients table values
                    patient_dict['initial_tv_completed'] = patients_data['initial_tv_completed'] or False
                    patient_dict['initial_tv_completed_date'] = patients_data['initial_tv_completed_date']
                    patient_dict['initial_tv_notes'] = patients_data['initial_tv_notes']
            
            return patient_dict
        return None
    finally:
        conn.close()

def get_onboarding_queue():
    """Get the current onboarding queue with patient status and TV completion info"""
    conn = get_db_connection()
    try:
        queue = conn.execute("""
            SELECT 
                op.onboarding_id,
                op.patient_id,
                op.first_name || ' ' || op.last_name as patient_name,
                op.stage1_complete,
                op.stage2_complete,
                op.stage3_complete,
                op.stage4_complete,
                op.stage5_complete,
                op.created_date,
                op.updated_date,
                CASE 
                    WHEN NOT op.stage1_complete THEN 'Patient Registration'
                    WHEN NOT op.stage2_complete THEN 'Eligibility Verification'
                    WHEN NOT op.stage3_complete THEN 'Chart Creation'
                    WHEN NOT op.stage4_complete THEN 'Intake Processing'
                    WHEN NOT op.stage5_complete THEN 'TV Visit Scheduling'
                    ELSE 'Workflow Complete'
                END as current_stage,
                CASE 
                    WHEN op.created_date > datetime('now', '-1 day') THEN 'High'
                    WHEN op.created_date > datetime('now', '-3 days') THEN 'Medium'
                    ELSE 'Normal'
                END as priority_status,
                COALESCE(u.full_name, 'Unassigned') as assigned_pot_name,
                -- TV completion status from patients table
                COALESCE(p.initial_tv_completed, 0) as initial_tv_completed,
                p.initial_tv_completed_date,
                p.initial_tv_provider,
                -- Check if ready for Stage 5 completion
                CASE 
                    WHEN op.stage4_complete = 1 
                         AND op.stage5_complete = 0 
                         AND COALESCE(p.initial_tv_completed, 0) = 1 
                    THEN 1 
                    ELSE 0 
                END as ready_for_stage5_completion
            FROM onboarding_patients op
            LEFT JOIN users u ON op.assigned_pot_user_id = u.user_id
            LEFT JOIN patients p ON op.patient_id = p.patient_id
            WHERE op.patient_status = 'Active'
            ORDER BY op.created_date ASC
        """).fetchall()
        
        return [dict(row) for row in queue]
    finally:
        conn.close()

def add_user_role(user_id, role_id):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role_id))
        conn.commit()
    except sqlite3.IntegrityError:
        # User already has this role
        pass
    finally:
        conn.close()

def remove_user_role(user_id, role_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM user_roles WHERE user_id = ? AND role_id = ?", (user_id, role_id))
    conn.commit()
    conn.close()

def set_primary_role(user_id, role_id):
    conn = get_db_connection()
    # First, set all roles for the user to not be primary
    conn.execute("UPDATE user_roles SET is_primary = 0 WHERE user_id = ?", (user_id,))
    # Then, set the specified role to be primary
    conn.execute("UPDATE user_roles SET is_primary = 1 WHERE user_id = ? AND role_id = ?", (user_id, role_id))
    conn.commit()
    conn.close()

def get_user_roles():
    conn = get_db_connection()
    roles = conn.execute('SELECT * FROM roles').fetchall()
    conn.close()
    return roles

def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return users

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def get_users_by_role(role_identifier):
    """Get all users with a specific role - works with role_id (int) or role_name (string)"""
    conn = get_db_connection()
    try:
        if isinstance(role_identifier, int):
            # Handle role_id
            users = conn.execute("""
                SELECT u.user_id, u.username, u.full_name, r.role_name
                FROM users u
                JOIN user_roles ur ON u.user_id = ur.user_id
                JOIN roles r ON ur.role_id = r.role_id
                WHERE r.role_id = ?
            """, (role_identifier,)).fetchall()
        else:
            # Handle role_name (string)
            users = conn.execute("""
                SELECT u.user_id, u.username, u.full_name, r.role_name
                FROM users u
                JOIN user_roles ur ON u.user_id = ur.user_id
                JOIN roles r ON ur.role_id = r.role_id
                WHERE r.role_name = ?
            """, (role_identifier,)).fetchall()
        return [dict(user) for user in users]
    except Exception as e:
        print(f"Error in get_users_by_role: {e}")
        return []
    finally:
        conn.close()

def get_provider_onboarding_queue(provider_user_id):
    """Get onboarding patients assigned to a specific provider for initial TV visits"""
    conn = get_db_connection()
    try:
        # Get the provider's full name from user_id
        provider_cursor = conn.execute("""
            SELECT full_name FROM users WHERE user_id = ?
        """, (provider_user_id,))
        provider_result = provider_cursor.fetchone()
        
        if not provider_result:
            return []
            
        provider_full_name = provider_result[0]
        
        # Get onboarding patients assigned to this provider who need initial TV visit
        # Look for patients where initial_tv_provider matches provider's full name and initial_tv_completed = 0
        onboarding_patients = conn.execute("""
            SELECT 
                op.onboarding_id,
                op.patient_id,
                op.first_name,
                op.last_name,
                op.date_of_birth,
                op.phone_primary,
                op.email,
                op.hypertension,
                op.mental_health_concerns,
                op.dementia,
                op.annual_well_visit,
                op.created_date,
                op.tv_date,
                op.tv_time,
                op.assigned_provider_user_id,
                op.initial_tv_completed,
                op.initial_tv_provider
            FROM onboarding_patients op
            WHERE op.initial_tv_provider = ? 
            AND (op.initial_tv_completed = 0 OR op.initial_tv_completed IS NULL)
            AND op.patient_status IN ('Active', 'Active-Geri')
            ORDER BY op.tv_date ASC, op.created_date ASC
        """, (provider_full_name,)).fetchall()
        
        return [dict(patient) for patient in onboarding_patients]
        
    except Exception as e:
        print(f"Error getting provider onboarding queue: {e}")
        return []
    finally:
        conn.close()

def save_onboarding_tv_scheduling_progress(onboarding_id, form_data):
    """Save partial progress for TV scheduling form without completing the stage"""
    conn = get_db_connection()
    try:
        # Extract provider user_id from the selection format "Full Name (username)"
        provider_user_id = None
        if form_data.get('assigned_provider') and form_data['assigned_provider'] != "Select Provider...":
            # Get the username from the format "Full Name (username)"
            username = form_data['assigned_provider'].split('(')[-1].replace(')', '').strip()
            provider_cursor = conn.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            provider_result = provider_cursor.fetchone()
            if provider_result:
                provider_user_id = provider_result[0]
        
        # Extract coordinator user_id from the selection format "Full Name (username)"
        coordinator_user_id = None
        if form_data.get('assigned_coordinator') and form_data['assigned_coordinator'] != "Select Coordinator...":
            # Get the username from the format "Full Name (username)"
            username = form_data['assigned_coordinator'].split('(')[-1].replace(')', '').strip()
            coordinator_cursor = conn.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            coordinator_result = coordinator_cursor.fetchone()
            if coordinator_result:
                coordinator_user_id = coordinator_result[0]
        
        # Convert time object to string if needed
        tv_time = form_data.get('tv_time')
        if tv_time and hasattr(tv_time, 'strftime'):
            tv_time = tv_time.strftime('%H:%M:%S')
        
        # Convert date object to string if needed  
        tv_date = form_data.get('tv_date')
        if tv_date and hasattr(tv_date, 'strftime'):
            tv_date = tv_date.strftime('%Y-%m-%d')
        
        # Extract provider name for initial_tv_provider field
        initial_tv_provider = None
        if form_data.get('assigned_provider') and form_data['assigned_provider'] != "Select Provider...":
            # Extract the full name from the format "Full Name (username)"
            initial_tv_provider = form_data['assigned_provider'].split('(')[0].strip()

        # Update onboarding patient record with partial progress
        conn.execute("""
            UPDATE onboarding_patients
            SET tv_date = ?,
                tv_time = ?,
                assigned_provider_user_id = ?,
                assigned_coordinator_user_id = ?,
                initial_tv_provider = ?,
                updated_date = CURRENT_TIMESTAMP
            WHERE onboarding_id = ?
        """, (
            tv_date, 
            tv_time,
            provider_user_id,
            coordinator_user_id,
            initial_tv_provider,
            onboarding_id
        ))
        
        # Update checkbox fields if provided
        checkbox_data = {}
        if 'tv_scheduled' in form_data:
            checkbox_data['tv_scheduled'] = form_data['tv_scheduled']
        if 'patient_notified' in form_data:
            checkbox_data['patient_notified'] = form_data['patient_notified']
        if 'initial_tv_completed' in form_data:
            checkbox_data['initial_tv_completed'] = form_data['initial_tv_completed']
        
        # Update checkbox fields within the same transaction to avoid multiple connections
        if checkbox_data:
            update_fields = []
            update_params = []
            
            for field, value in checkbox_data.items():
                update_fields.append(f"{field} = ?")
                update_params.append(value)
            
            if update_fields:
                update_fields.append("updated_date = datetime('now')")
                update_params.append(onboarding_id)
                
                checkbox_query = f"""
                    UPDATE onboarding_patients 
                    SET {', '.join(update_fields)}
                    WHERE onboarding_id = ?
                """
                
                conn.execute(checkbox_query, update_params)
        
        # Create comprehensive patient records and assignments if provider or coordinator is assigned
        if provider_user_id or coordinator_user_id:
            # Get patient information to create text-based patient_id
            patient_info = conn.execute("""
                SELECT first_name, last_name, date_of_birth, patient_id, phone_primary, email, address_street, address_city, address_state, address_zip, insurance_provider, policy_number, emergency_contact_name, emergency_contact_phone
                FROM onboarding_patients 
                WHERE onboarding_id = ?
            """, (onboarding_id,)).fetchone()
            
            if patient_info:
                # Generate text-based patient_id using the same function as insert_patient_from_onboarding
                text_patient_id = generate_patient_id(
                    patient_info['first_name'] or '',
                    patient_info['last_name'] or '',
                    patient_info['date_of_birth'] or ''
                )
                
                # 1. Update the patient_id in onboarding_patients table
                conn.execute("""
                    UPDATE onboarding_patients 
                    SET patient_id = ? 
                    WHERE onboarding_id = ?
                """, (text_patient_id, onboarding_id))
                
                # 2. Create or update patient record in patients table
                conn.execute("""
                    INSERT OR REPLACE INTO patients (
                        patient_id, first_name, last_name, date_of_birth, phone_primary, email, 
                        address_street, address_city, address_state, address_zip, insurance_primary, insurance_policy_number,
                        emergency_contact_name, emergency_contact_phone, initial_tv_provider, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (
                    text_patient_id,
                    patient_info['first_name'],
                    patient_info['last_name'], 
                    patient_info['date_of_birth'],
                    patient_info['phone_primary'],
                    patient_info['email'],
                    patient_info['address_street'],
                    patient_info['address_city'],
                    patient_info['address_state'],
                    patient_info['address_zip'],
                    patient_info['insurance_provider'],
                    patient_info['policy_number'],
                    patient_info['emergency_contact_name'],
                    patient_info['emergency_contact_phone'],
                    initial_tv_provider
                ))
                
                # 3. Create or update patient assignment in patient_assignments table
                # Check if assignment already exists for this patient
                existing = conn.execute("""
                    SELECT assignment_id FROM patient_assignments 
                    WHERE patient_id = ? AND assignment_type = ? AND status = 'active'
                """, (text_patient_id, "onboarding")).fetchone()
                
                if existing:
                    # Update existing assignment
                    conn.execute("""
                        UPDATE patient_assignments 
                        SET provider_id = ?, coordinator_id = ?, priority_level = ?, 
                            notes = ?, updated_date = datetime('now'), updated_by = ?
                        WHERE assignment_id = ?
                    """, (provider_user_id, coordinator_user_id, "medium", 
                          "Assignment created from onboarding TV scheduling progress", None, existing['assignment_id']))
                else:
                    # Create new assignment
                    conn.execute("""
                        INSERT INTO patient_assignments (
                            patient_id, provider_id, coordinator_id, assignment_date, 
                            assignment_type, status, priority_level, notes, 
                            created_date, updated_date, created_by, updated_by
                        ) VALUES (?, ?, ?, datetime('now'), ?, ?, ?, ?, 
                                 datetime('now'), datetime('now'), ?, ?)
                    """, (text_patient_id, provider_user_id, coordinator_user_id, "onboarding", 
                          "active", "medium", "Assignment created from onboarding TV scheduling progress", None, None))
                
                # 4. Create or update assignments in patient_panel table
                if provider_user_id:
                    conn.execute("""
                        INSERT OR REPLACE INTO patient_panel (
                            patient_id, provider_id, status, created_date, updated_date
                        ) VALUES (?, ?, 'active', datetime('now'), datetime('now'))
                    """, (text_patient_id, provider_user_id))
                
                if coordinator_user_id:
                    conn.execute("""
                        INSERT OR REPLACE INTO patient_panel (
                            patient_id, coordinator_id, status, created_date, updated_date
                        ) VALUES (?, ?, 'active', datetime('now'), datetime('now'))
                    """, (text_patient_id, coordinator_user_id))
        
        conn.commit()
        return True
        
    except Exception as e:
        import traceback
        print(f"Error saving TV scheduling progress: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Traceback: {traceback.format_exc()}")
        print(f"Form data: {form_data}")
        print(f"Onboarding ID: {onboarding_id}")
        return False
    finally:
        conn.close()

def update_onboarding_stage5_completion(onboarding_id, tv_date, tv_time, assigned_provider, assigned_coordinator):
    """Update Stage 5 completion with provider assignment and TV scheduling details"""
    conn = get_db_connection()
    try:
        # Extract provider user_id from the selection format "Full Name (username)"
        provider_user_id = None
        if assigned_provider and assigned_provider != "Select Provider...":
            # Get the username from the format "Full Name (username)"
            username = assigned_provider.split('(')[-1].replace(')', '').strip()
            provider_cursor = conn.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            provider_result = provider_cursor.fetchone()
            if provider_result:
                provider_user_id = provider_result[0]
        
        # Extract coordinator user_id from the selection format "Full Name (username)"
        coordinator_user_id = None
        if assigned_coordinator and assigned_coordinator != "Select Coordinator...":
            # Get the username from the format "Full Name (username)"
            username = assigned_coordinator.split('(')[-1].replace(')', '').strip()
            coordinator_cursor = conn.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            coordinator_result = coordinator_cursor.fetchone()
            if coordinator_result:
                coordinator_user_id = coordinator_result[0]
        
        # Convert time and date objects to strings if needed
        if tv_time and hasattr(tv_time, 'strftime'):
            tv_time = tv_time.strftime('%H:%M:%S')
        if tv_date and hasattr(tv_date, 'strftime'):
            tv_date = tv_date.strftime('%Y-%m-%d')
        
        # Extract provider name for initial_tv_provider field
        initial_tv_provider = None
        if assigned_provider and assigned_provider != "Select Provider...":
            # Extract the full name from the format "Full Name (username)"
            initial_tv_provider = assigned_provider.split('(')[0].strip()
        
        # Update onboarding patient record
        conn.execute("""
            UPDATE onboarding_patients
            SET tv_date = ?,
                tv_time = ?,
                assigned_provider_user_id = ?,
                assigned_coordinator_user_id = ?,
                initial_tv_provider = ?,
                updated_date = CURRENT_TIMESTAMP
            WHERE onboarding_id = ?
        """, (tv_date, tv_time, provider_user_id, coordinator_user_id, initial_tv_provider, onboarding_id))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error updating Stage 5 completion: {e}")
        return False
    finally:
        conn.close()

def get_tasks_by_user(user_id):
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return tasks

def add_user(username, password, first_name, last_name, email, role_name):
    """
    Add a new user with plain text password (will be hashed)
    
    Args:
        username: User's username
        password: Plain text password (will be hashed)
        first_name: User's first name
        last_name: User's last name
        email: User's email
        role_name: Role name to assign
    """
    import hashlib
    
    # Hash the password before storing
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    conn = get_db_connection()
    try:
        role = conn.execute('SELECT role_id FROM roles WHERE role_name = ?', (role_name,)).fetchone()
        if role:
            role_id = role['role_id']
            cursor = conn.execute("INSERT INTO users (username, password, first_name, last_name, email, status, hire_date) VALUES (?, ?, ?, ?, ?, 'active', CURRENT_DATE)",
                                  (username, hashed_password, first_name, last_name, email))
            user_id = cursor.lastrowid
            conn.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                         (user_id, role_id))
            conn.commit()
            return user_id
        return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def add_user_with_hashed_password(username, hashed_password, first_name, last_name, email, role_name):
    """
    Add a new user with pre-hashed password
    
    Args:
        username: User's username
        hashed_password: Already hashed password
        first_name: User's first name
        last_name: User's last name
        email: User's email
        role_name: Role name to assign
    """
    conn = get_db_connection()
    try:
        role = conn.execute('SELECT role_id FROM roles WHERE role_name = ?', (role_name,)).fetchone()
        if role:
            role_id = role['role_id']
            cursor = conn.execute("INSERT INTO users (username, password, first_name, last_name, email, status, hire_date) VALUES (?, ?, ?, ?, ?, 'active', CURRENT_DATE)",
                                  (username, hashed_password, first_name, last_name, email))
            user_id = cursor.lastrowid
            conn.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                         (user_id, role_id))
            conn.commit()
            return user_id
        return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def get_user_patient_assignments(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            upa.patient_id,
            p.first_name || ' ' || p.last_name AS patient_name,
            upa.role_id,
            upa.user_id,
            p.address_street,
            p.address_city,
            p.address_state,
            p.address_zip,
            p.phone_primary,
            p.email,
            p.status AS patient_status
        FROM
            user_patient_assignments upa
        JOIN
            patients p ON upa.patient_id = p.patient_id
        WHERE
            upa.user_id = ?;
    """, (user_id,))
    assignments = cursor.fetchall()
    conn.close()
    return assignments

def get_coordinator_performance_metrics(user_id):
    conn = get_db_connection()
    try:
        query = """
            SELECT
                u.full_name,
                IFNULL(AVG(ct.duration_minutes), 0) AS avg_minutes_per_task,
                IFNULL(COUNT(ct.coordinator_task_id) * 1.0 / COUNT(DISTINCT DATE(ct.task_date)), 0) AS avg_tasks_per_day,
                IFNULL(SUM(ct.duration_minutes) * 1.0 / COUNT(DISTINCT DATE(ct.task_date)), 0) AS avg_minutes_per_day
            FROM users u
            LEFT JOIN coordinator_tasks_2025_09 ct ON u.user_id = ct.coordinator_id
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN roles r ON ur.role_id = r.role_id
            WHERE r.role_id IN (36, 40, 39) AND u.user_id = ?
            GROUP BY u.full_name;
        """
        metrics = conn.execute(query, (user_id,)).fetchall()
        return [dict(row) for row in metrics]
    finally:
        conn.close()

def get_care_plan(patient_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT plan_details FROM care_plans WHERE patient_name = ?", (patient_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else ""

def update_care_plan(patient_name, plan_details, updated_by):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO care_plans (patient_name, plan_details, updated_by, last_updated) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                   (patient_name, plan_details, updated_by))
    conn.commit()
    conn.close()


def get_provider_performance_metrics():
    conn = get_db_connection()
    try:
        # Updated to work with monthly partitioned tables - using provider_tasks_2025_09
        query = """
            SELECT
                u.full_name,
                COALESCE(COUNT(DISTINCT CASE WHEN STRFTIME('%Y-%m', pt.task_date) = STRFTIME('%Y-%m', 'now') THEN pt.patient_id END), 0) AS patients_visited_this_month,
                COALESCE(COUNT(DISTINCT upa.patient_id), 0) - COALESCE(COUNT(DISTINCT CASE WHEN STRFTIME('%Y-%m', pt.task_date) = STRFTIME('%Y-%m', 'now') THEN pt.patient_id END), 0) AS remaining_visits
            FROM users u
            LEFT JOIN provider_tasks_2025_09 pt ON u.user_id = pt.provider_id
            LEFT JOIN user_patient_assignments upa ON u.user_id = upa.user_id
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN roles r ON ur.role_id = r.role_id
            WHERE r.role_id IN (33, 38)  -- CP and CPM roles
            GROUP BY u.full_name;
        """
        metrics = conn.execute(query).fetchall()
        return [dict(row) for row in metrics]
    finally:
        conn.close()

def get_tasks_billing_codes():
    conn = get_db_connection()
    try:
        codes = conn.execute("SELECT code, description FROM task_billing_codes").fetchall()
        return [dict(row) for row in codes]
    finally:
        conn.close()

def get_tasks_billing_codes_by_service_type(service_type):
    """Get task billing codes filtered by service type"""
    conn = get_db_connection()
    try:
        codes = conn.execute("""
            SELECT code_id, task_description, billing_code, description 
            FROM task_billing_codes 
            WHERE service_type = ? 
            ORDER BY task_description
        """, (service_type,)).fetchall()
        return [dict(row) for row in codes]
    finally:
        conn.close()

def get_daily_tasks_for_coordinator():
    conn = get_db_connection()
    try:
        # Get all task descriptions for coordinator tasks from coordinator_task_definitions table
        tasks = conn.execute("SELECT task_description FROM coordinator_task_definitions WHERE task_description IS NOT NULL GROUP BY task_description").fetchall()
        return [dict(row) for row in tasks]
    finally:
        conn.close()

def get_coordinator_task_definitions():
    """Get coordinator task definitions for task dropdown"""
    conn = get_db_connection()
    try:
        tasks = conn.execute("""
            SELECT task_definition_id, task_category, task_description 
            FROM coordinator_task_definitions 
            ORDER BY task_description
        """).fetchall()
        return [dict(row) for row in tasks]
    finally:
        conn.close()


def get_provider_id_from_user_id(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT provider_id FROM providers WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def get_patient_details_by_id(patient_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_provider_counties(provider_id):
    """Get counties for a provider using the new dashboard mapping table"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT DISTINCT 
                dpc.county, 
                dpc.state,
                dpc.patient_count
            FROM dashboard_provider_county_map dpc
            WHERE dpc.provider_id = ? AND dpc.county IS NOT NULL AND dpc.county != ''
            ORDER BY dpc.county
        """, (provider_id,))
        counties = cursor.fetchall()
        return [(c[0], f"{c[0]}, {c[1]} [{c[2]}]") for c in counties]
    finally:
        conn.close()

def get_provider_zip_codes(provider_id):
    """Get zip codes for a provider using the new dashboard mapping table"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT DISTINCT 
                dpz.zip_code, 
                dpz.city, 
                dpz.state,
                dpz.patient_count
            FROM dashboard_provider_zip_map dpz
            WHERE dpz.provider_id = ? AND dpz.zip_code IS NOT NULL AND dpz.zip_code != ''
            ORDER BY dpz.zip_code
        """, (provider_id,))
        zip_codes = cursor.fetchall()
        return [(z[0], f"{z[0]} - {z[1]}, {z[2]} [{z[3]}]") for z in zip_codes]
    finally:
        conn.close()

def get_patient_counties(patient_id):
    """Get counties for a patient using the new dashboard mapping table"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT DISTINCT 
                dpc.county, 
                dpc.state
            FROM dashboard_patient_county_map dpc
            WHERE dpc.patient_id = ? AND dpc.county IS NOT NULL AND dpc.county != ''
            ORDER BY dpc.county
        """, (patient_id,))
        counties = cursor.fetchall()
        return [(c[0], f"{c[0]}, {c[1]}") for c in counties]
    finally:
        conn.close()

def get_patient_zip_codes(patient_id):
    """Get zip codes for a patient using the new dashboard mapping table"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT DISTINCT 
                dpz.zip_code, 
                dpz.city, 
                dpz.state
            FROM dashboard_patient_zip_map dpz
            WHERE dpz.patient_id = ? AND dpz.zip_code IS NOT NULL AND dpz.zip_code != ''
            ORDER BY dpz.zip_code
        """, (patient_id,))
        zip_codes = cursor.fetchall()
        return [(z[0], f"{z[0]} - {z[1]}, {z[2]}") for z in zip_codes]
    finally:
        conn.close()

def get_billing_codes(service_type=None, location_type=None, patient_type=None):
    """Return billing code rows filtered by service_type, location_type and patient_type.
    Each row is returned as a dict with keys matching the task_billing_codes columns.
    """
    conn = get_db_connection()
    try:
        # Check if is_default column exists in the table
        cursor = conn.execute("PRAGMA table_info(task_billing_codes)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Build query based on whether is_default column exists
        if 'is_default' in columns:
            query = "SELECT code_id, task_description, service_type, location_type, patient_type, min_minutes, max_minutes, billing_code, description, rate, COALESCE(is_default, 0) as is_default FROM task_billing_codes"
        else:
            query = "SELECT code_id, task_description, service_type, location_type, patient_type, min_minutes, max_minutes, billing_code, description, rate, 0 as is_default FROM task_billing_codes"
        
        conditions = []
        params = []
        if service_type:
            conditions.append("service_type = ?")
            params.append(service_type)
        if location_type:
            conditions.append("location_type = ?")
            params.append(location_type)
        if patient_type:
            conditions.append("patient_type = ?")
            params.append(patient_type)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY min_minutes DESC, max_minutes DESC"
        rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def set_default_billing_codes(billing_codes):
    """Set the is_default flag on task_billing_codes.
    This will clear is_default for all rows, then set is_default=1 for any billing_code in the provided list.
    If billing_codes is empty or None, all rows will be cleared.
    Returns True on success.
    """
    conn = get_db_connection()
    try:
        # Clear all defaults first
        conn.execute("UPDATE task_billing_codes SET is_default = 0")

        if billing_codes:
            # Ensure billing_codes is iterable
            codes = list(billing_codes)
            for code in codes:
                conn.execute("UPDATE task_billing_codes SET is_default = 1 WHERE billing_code = ?", (code,))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error setting default billing codes: {e}")
        return False
    finally:
        conn.close()


def save_daily_task(provider_id, patient_id, task_date, task_description, notes, billing_code=None):
    """Save a daily task for a provider to the provider_tasks table.
    If `billing_code` is provided, use it to look up duration and description. Otherwise fallback to lookup by task_description.
    """
    conn = get_db_connection()
    try:
        billing_data = None
        if billing_code:
            billing_cursor = conn.execute("""
                SELECT min_minutes, billing_code, rate, description
                FROM task_billing_codes
                WHERE billing_code = ?
                LIMIT 1
            """, (billing_code,))
            billing_data = billing_cursor.fetchone()

        if not billing_data:
            # Fallback to previous behavior: lookup by task_description
            billing_cursor = conn.execute("""
                SELECT min_minutes, billing_code, rate, description
                FROM task_billing_codes 
                WHERE task_description = ?
                LIMIT 1
            """, (task_description,))
            billing_data = billing_cursor.fetchone()

        if billing_data:
            duration_minutes = billing_data[0] if billing_data[0] is not None else 30
            billing_code_val = billing_data[1]
            rate = billing_data[2]
            billing_code_description = billing_data[3]
        else:
            duration_minutes = 30
            billing_code_val = billing_code if billing_code else "UNKNOWN"
            rate = 0
            billing_code_description = f"{task_description} - Default"

        # Normalize patient_id for storage and related lookups
        pid = normalize_patient_id(patient_id, conn=conn)

        # Insert into provider_tasks_2025_09 table (monthly partitioned table)
        conn.execute("""
            INSERT INTO provider_tasks_2025_09
            (provider_task_id, provider_id, patient_id, task_date, notes, minutes_of_service, task_description, billing_code_description, source_system, imported_at)
            VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, 'DATA_ENTRY', CURRENT_TIMESTAMP)
        """, (provider_id, pid, task_date, notes, duration_minutes, task_description, billing_code_description))

        # Also insert into tasks table for compatibility
        conn.execute("""
            INSERT INTO tasks 
            (patient_name, patient_id, user_id, full_name, staff_code, role_id, task_date, task_type, duration_minutes, service_code, notes, task_state)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("", pid, provider_id, "", "", 33, task_date, task_description, duration_minutes, billing_code_val, notes, "completed"))

        # If onboarding-specific task, handle onboarding workflow (legacy)
        if task_description == "PCP-Visit Telehealth (TE) (NEW pt)":
            onboarding_cursor = conn.execute("""
                SELECT onboarding_id 
                FROM onboarding_patients 
                WHERE patient_id = ? AND stage5_complete = 1 AND completed_date IS NULL
            """, (pid,))
            onboarding_match = onboarding_cursor.fetchone()
            if onboarding_match:
                conn.execute("""
                    UPDATE onboarding_patients 
                    SET initial_tv_completed = 1, initial_tv_completed_date = ?
                    WHERE onboarding_id = ?
                """, (task_date, onboarding_match[0]))

            # Get provider name for initial TV provider field
            provider_name = ""
            try:
                provider_cursor = conn.execute("""
                    SELECT full_name FROM users WHERE user_id = ?
                """, (provider_id,))
                provider_result = provider_cursor.fetchone()
                if provider_result:
                    provider_name = provider_result[0]
            except:
                provider_name = f"Provider ID {provider_id}"

            # Update initial TV fields in patients table
            conn.execute("""
                UPDATE patients 
                SET last_visit_date = ?,
                    initial_tv_completed_date = ?,
                    initial_tv_notes = ?,
                    initial_tv_provider = ?,
                    service_type = ?
                WHERE patient_id = ?
            """, (task_date, task_date, notes, provider_name, task_description, pid))

            # Update initial TV fields in patient_panel table
            conn.execute("""
                UPDATE patient_panel 
                SET last_visit_date = ?,
                    initial_tv_completed = 1,
                    initial_tv_completed_date = ?,
                    initial_tv_notes = ?,
                    initial_tv_provider = ?,
                    last_visit_service_type = ?
                WHERE patient_id = ?
            """, (task_date, task_date, notes, provider_name, task_description, pid))
        else:
            # For non-initial TV tasks, update last_visit_date and service_type
            # Update last_visit_date and service_type in patients table
            conn.execute("""
                UPDATE patients 
                SET last_visit_date = ?,
                    service_type = ?
                WHERE patient_id = ?
            """, (task_date, task_description, pid))

            # Update last_visit_date and service_type in patient_panel table
            conn.execute("""
                UPDATE patient_panel 
                SET last_visit_date = ?,
                    last_visit_service_type = ?
                WHERE patient_id = ?
            """, (task_date, task_description, pid))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving task: {e}")
        return False
    finally:
        conn.close()

def save_coordinator_task(coordinator_id, patient_id, task_date, task_description, duration_minutes, notes):
    """Save a daily task for a coordinator to the coordinator_tasks table"""
    conn = get_db_connection()
    try:
        # Insert into coordinator_tasks_2025_09 table (monthly partitioned table)
        # The table does have a notes column, so we'll include it
        # Normalize patient_id to the canonical string format before inserting
        pid = normalize_patient_id(patient_id, conn=conn)
        conn.execute("""
            INSERT INTO coordinator_tasks_2025_09
            (patient_id, coordinator_id, task_date, duration_minutes, task_type, notes, source_system, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, 'DATA_ENTRY', CURRENT_TIMESTAMP)
        """, (pid, coordinator_id, task_date, duration_minutes, task_description, notes))
        
        conn.commit()
        print(f"Coordinator task saved successfully for coordinator {coordinator_id}")
        return True
    except Exception as e:
        print(f"Error saving coordinator task: {e}")
        return False
    finally:
        conn.close()

def get_all_patients():
    """Get all patients from the database with their status type"""
    conn = get_db_connection()
    try:
        patients = conn.execute("""
            SELECT p.*, pst.status_name, pst.description as status_description
            FROM patients p
            LEFT JOIN patient_status_types pst ON p.status = pst.status_name
        """).fetchall()
        return [dict(row) for row in patients]
    finally:
        conn.close()

def get_all_patient_status_types():
    """Get all available patient status types"""
    conn = get_db_connection()
    try:
        status_types = conn.execute("""
            SELECT status_id, status_name, description 
            FROM patient_status_types 
            ORDER BY status_name
        """).fetchall()
        return [dict(row) for row in status_types]
    finally:
        conn.close()

def update_patient_status(patient_id, status):
    """Update the status of a patient"""
    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE patients 
            SET status = ?, updated_date = CURRENT_TIMESTAMP 
            WHERE patient_id = ?
        """, (status, patient_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating patient status: {e}")
        return False
    finally:
        conn.close()


# Onboarding Workflow Functions

def get_onboarding_queue():
    """Get all active onboarding patients with their current status"""
    conn = get_db_connection()
    try:
        query = """
        SELECT 
            op.onboarding_id,
            op.first_name || ' ' || op.last_name AS patient_name,
            op.patient_status,
            op.assigned_pot_user_id,
            u.full_name AS assigned_pot_name,
            wi.workflow_status AS workflow_status,
            CASE 
                WHEN op.stage5_complete = 1 THEN 'Completed'
                WHEN op.stage4_complete = 1 THEN 'Stage 5: TV Scheduling'
                WHEN op.stage3_complete = 1 THEN 'Stage 4: Intake Processing'
                WHEN op.stage2_complete = 1 THEN 'Stage 3: Chart Creation'
                WHEN op.stage1_complete = 1 THEN 'Stage 2: Eligibility Verification'
                ELSE 'Stage 1: Patient Registration'
            END AS current_stage,
            CASE
                WHEN op.completed_date IS NOT NULL THEN 'Completed'
                WHEN op.stage5_complete = 1 THEN 'Completed'
                ELSE 'In Progress'
            END AS priority_status,
            op.created_date,
            op.updated_date,
            op.completed_date,
            -- Stage completion flags
            op.stage1_complete,
            op.stage2_complete,
            op.stage3_complete,
            op.stage4_complete,
            op.stage5_complete,
            -- Stage 1 blockers (Patient Registration)
            op.first_name,
            op.last_name,
            op.date_of_birth,
            op.phone_primary,
            -- Stage 2 blockers (Eligibility Verification)
            op.insurance_provider,
            op.policy_number,
            op.eligibility_verified,
            op.insurance_cards_received,
            op.eligibility_status,
            -- Stage 3 blockers (Chart Creation)
            op.emed_chart_created,
            op.facility_confirmed,
            op.chart_id,
            -- Stage 4 blockers (Intake Processing)
            op.intake_call_completed,
            op.medical_records_requested,
            -- Stage 5 blockers (TV Visit Scheduling)
            op.assigned_provider_user_id,
            op.tv_scheduled,
            op.initial_tv_completed,
            op.initial_tv_provider,
            op.provider_completed_initial_tv,
            prov.full_name AS provider_name,
            -- Check for regional provider and coordinator assignments
            CASE WHEN pa_provider.provider_id IS NOT NULL THEN 1 ELSE 0 END AS regional_provider_assigned,
            CASE WHEN pa_coordinator.coordinator_id IS NOT NULL THEN 1 ELSE 0 END AS coordinator_assigned,
            reg_prov.full_name AS regional_provider_name,
            coord.full_name AS coordinator_name
        FROM onboarding_patients op
        LEFT JOIN workflow_instances wi ON op.workflow_instance_id = wi.instance_id
        LEFT JOIN users u ON op.assigned_pot_user_id = u.user_id
        LEFT JOIN users prov ON op.assigned_provider_user_id = prov.user_id
        LEFT JOIN patient_assignments pa_provider ON op.patient_id = pa_provider.patient_id 
            AND pa_provider.provider_id IS NOT NULL AND pa_provider.status = 'active'
        LEFT JOIN patient_assignments pa_coordinator ON op.patient_id = pa_coordinator.patient_id 
            AND pa_coordinator.coordinator_id IS NOT NULL AND pa_coordinator.status = 'active'
        LEFT JOIN users reg_prov ON pa_provider.provider_id = reg_prov.user_id
        LEFT JOIN users coord ON pa_coordinator.coordinator_id = coord.user_id
        WHERE op.completed_date IS NULL
        ORDER BY 
            CASE 
                WHEN op.stage5_complete = 1 THEN 1  -- Completed (highest priority)
                WHEN op.stage4_complete = 1 THEN 2  -- Almost done
                WHEN op.stage3_complete = 1 THEN 3
                WHEN op.stage2_complete = 1 THEN 4
                WHEN op.stage1_complete = 1 THEN 5
                ELSE 6  -- Just started (lowest priority)
            END,
            op.created_date DESC
        """
        result = conn.execute(query).fetchall()
        return [dict(row) for row in result]
    finally:
        conn.close()

def create_onboarding_workflow_instance(patient_data, pot_user_id):
    """Create a new workflow instance and onboarding patient record"""
    conn = get_db_connection()
    try:
        # Create onboarding patient record directly (no workflow_instances linkage)
        cursor = conn.execute("""
            INSERT INTO onboarding_patients (
                first_name, last_name, date_of_birth,
                phone_primary, email, gender, emergency_contact_name, emergency_contact_phone,
                address_street, address_city, address_state, address_zip,
                insurance_provider, policy_number, group_number,
                referral_source, referring_provider, referral_date,
                patient_status, facility_assignment, assigned_pot_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_data['first_name'], patient_data['last_name'], patient_data['date_of_birth'],
            patient_data.get('phone_primary'), patient_data.get('email'), patient_data.get('gender'),
            patient_data.get('emergency_contact_name'), patient_data.get('emergency_contact_phone'),
            patient_data.get('address_street'), patient_data.get('address_city'), 
            patient_data.get('address_state'), patient_data.get('address_zip'),
            patient_data.get('insurance_provider'), patient_data.get('policy_number'), 
            patient_data.get('group_number'),
            patient_data.get('referral_source'), patient_data.get('referring_provider'), 
            patient_data.get('referral_date'),
            patient_data.get('patient_status', 'Active'), 
            patient_data.get('facility_assignment'), pot_user_id
        ))

        onboarding_id = cursor.lastrowid
        
        # Create initial tasks for all workflow steps
        workflow_steps = conn.execute("""
            SELECT step_id, step_order, task_name FROM workflow_steps 
            WHERE template_id = 14 ORDER BY step_order
        """).fetchall()
        
        for step in workflow_steps:
            stage = ((step['step_order'] - 1) // 3) + 1  # Group steps into stages (3 steps per stage roughly)
            if step['step_order'] > 15:  # Handle stage 5 which has more steps
                stage = 5
            
            conn.execute("""
                INSERT INTO onboarding_tasks (
                    onboarding_id, workflow_step_id, task_name, task_stage, 
                    task_order, status, created_date, updated_date
                ) VALUES (?, ?, ?, ?, ?, 'Pending', datetime('now'), datetime('now'))
            """, (onboarding_id, step['step_id'], step['task_name'], stage, step['step_order']))
        
        conn.commit()
        return onboarding_id
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_onboarding_patient_details(onboarding_id):
    """Get detailed information for a specific onboarding patient"""
    conn = get_db_connection()
    try:
        # Get patient details
        patient = conn.execute("""
            SELECT * FROM onboarding_patients WHERE onboarding_id = ?
        """, (onboarding_id,)).fetchone()
        
        if not patient:
            return None
            
        patient_dict = dict(patient)
        
        # Get tasks for this patient
        tasks = conn.execute("""
            SELECT ot.*, ws.deliverable 
            FROM onboarding_tasks ot
            JOIN workflow_steps ws ON ot.workflow_step_id = ws.step_id
            WHERE ot.onboarding_id = ?
            ORDER BY ot.task_order
        """, (onboarding_id,)).fetchall()
        
        patient_dict['tasks'] = [dict(task) for task in tasks]
        return patient_dict
        
    finally:
        conn.close()

def update_onboarding_stage_completion(onboarding_id, stage_number, completed=True):
    """Update stage completion status"""
    conn = get_db_connection()
    try:
        stage_field = f"stage{stage_number}_complete"
        
        # If completing stage 5, also set completed_date to mark patient as fully completed
        if stage_number == 5 and completed:
            conn.execute(f"""
                UPDATE onboarding_patients 
                SET {stage_field} = ?, completed_date = datetime('now'), updated_date = datetime('now')
                WHERE onboarding_id = ?
            """, (completed, onboarding_id))
        else:
            conn.execute(f"""
                UPDATE onboarding_patients 
                SET {stage_field} = ?, updated_date = datetime('now')
                WHERE onboarding_id = ?
            """, (completed, onboarding_id))
        
        conn.commit()
    finally:
        conn.close()

def update_onboarding_task_status(task_id, status, user_id, checkbox_data=None):
    """Update individual task status and checkbox data"""
    conn = get_db_connection()
    try:
        query = """
            UPDATE onboarding_tasks 
            SET status = ?, completed_by_user_id = ?, updated_date = datetime('now')
        """
        params = [status, user_id]
        
        if status == 'Complete':
            query += ", completed_date = datetime('now')"
        
        # Update checkbox fields if provided
        if checkbox_data:
            for field, value in checkbox_data.items():
                if hasattr(checkbox_data, field):
                    query += f", {field} = ?"
                    params.append(value)
        
        query += " WHERE task_id = ?"
        params.append(task_id)
        
        conn.execute(query, params)
        conn.commit()
    finally:
        conn.close()

def update_onboarding_patient_assignment(onboarding_id, pot_user_id):
    """Assign an onboarding patient to a POT user"""
    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE onboarding_patients 
            SET assigned_pot_user_id = ?, updated_date = datetime('now')
            WHERE onboarding_id = ?
        """, (pot_user_id, onboarding_id))
        conn.commit()
    finally:
        conn.close()

def update_onboarding_checkbox_data(onboarding_id, checkbox_data):
    """Update checkbox data for an onboarding patient and sync to patients/patient_panel tables"""
    conn = get_db_connection()
    try:
        # Build dynamic query based on provided checkbox data
        update_fields = []
        params = []
        
        for field, value in checkbox_data.items():
            update_fields.append(f"{field} = ?")
            params.append(value)
        
        if update_fields:
            update_fields.append("updated_date = datetime('now')")
            params.append(onboarding_id)
            
            query = f"""
                UPDATE onboarding_patients 
                SET {', '.join(update_fields)}
                WHERE onboarding_id = ?
            """
            
            conn.execute(query, params)
            
            # Get the patient_id from onboarding record to sync data
            patient_result = conn.execute("""
                SELECT patient_id FROM onboarding_patients WHERE onboarding_id = ?
            """, (onboarding_id,)).fetchone()
            
            if patient_result and patient_result[0]:
                patient_id = patient_result[0]
                
                # Sync the same data to patients table if columns exist
                patients_update_fields = []
                patients_params = []
                
                for field, value in checkbox_data.items():
                    # Check if column exists in patients table
                    col_check = conn.execute("""
                        SELECT COUNT(*) FROM pragma_table_info('patients') WHERE name = ?
                    """, (field,)).fetchone()
                    
                    if col_check and col_check[0] > 0:
                        patients_update_fields.append(f"{field} = ?")
                        patients_params.append(value)
                
                if patients_update_fields:
                    patients_update_fields.append("updated_date = datetime('now')")
                    patients_params.append(patient_id)
                    
                    patients_query = f"""
                        UPDATE patients 
                        SET {', '.join(patients_update_fields)}
                        WHERE patient_id = ?
                    """
                    conn.execute(patients_query, patients_params)
                
                # Sync the same data to patient_panel table if columns exist
                panel_update_fields = []
                panel_params = []
                
                for field, value in checkbox_data.items():
                    # Check if column exists in patient_panel table
                    col_check = conn.execute("""
                        SELECT COUNT(*) FROM pragma_table_info('patient_panel') WHERE name = ?
                    """, (field,)).fetchone()
                    
                    if col_check and col_check[0] > 0:
                        panel_update_fields.append(f"{field} = ?")
                        panel_params.append(value)
                
                if panel_update_fields:
                    panel_update_fields.append("updated_date = datetime('now')")
                    panel_params.append(patient_id)
                    
                    panel_query = f"""
                        UPDATE patient_panel 
                        SET {', '.join(panel_update_fields)}
                        WHERE patient_id = ?
                    """
                    conn.execute(panel_query, panel_params)
            
            conn.commit()
    finally:
        conn.close()

def transfer_onboarding_to_patient_table(onboarding_id):
    """Transfer completed onboarding data to the main patients table"""
    print(f"DEBUG: Starting transfer_onboarding_to_patient_table with onboarding_id={onboarding_id}")
    conn = get_db_connection()
    try:
        # Get onboarding data
        onboarding = conn.execute("""
            SELECT * FROM onboarding_patients WHERE onboarding_id = ?
        """, (onboarding_id,)).fetchone()
        
        print(f"DEBUG: Retrieved onboarding record: {onboarding is not None}")
        if not onboarding:
            print(f"DEBUG: No onboarding record found for ID {onboarding_id}")
            return None
            
        onboarding_dict = dict(onboarding)

        # helper: get existing patients table columns
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(patients);")
        patients_cols = [r[1] for r in cur.fetchall()]

        # mapping of candidate patient columns to onboarding values
        candidate = {
            'first_name': onboarding_dict.get('first_name'),
            'last_name': onboarding_dict.get('last_name'),
            'date_of_birth': onboarding_dict.get('date_of_birth'),
            'gender': onboarding_dict.get('gender'),
            'phone_primary': onboarding_dict.get('phone_primary'),
            'email': onboarding_dict.get('email'),
            'address_street': onboarding_dict.get('address_street'),
            'address_city': onboarding_dict.get('address_city'),
            'address_state': onboarding_dict.get('address_state'),
            'address_zip': onboarding_dict.get('address_zip'),
            'emergency_contact_name': onboarding_dict.get('emergency_contact_name'),
            'emergency_contact_phone': onboarding_dict.get('emergency_contact_phone'),
            'insurance_primary': onboarding_dict.get('insurance_provider'),
            'insurance_policy_number': onboarding_dict.get('policy_number'),
            'medical_records_requested': onboarding_dict.get('medical_records_requested', False),
            'referral_documents_received': onboarding_dict.get('referral_documents_received', False),
            'insurance_cards_received': onboarding_dict.get('insurance_cards_received', False),
            'emed_signature_received': onboarding_dict.get('emed_signature_received', False),
            'hypertension': onboarding_dict.get('hypertension', False),
            'mental_health_concerns': onboarding_dict.get('mental_health_concerns', False),
            'dementia': onboarding_dict.get('dementia', False),
            'appointment_contact_name': onboarding_dict.get('appointment_contact_name'),
            'appointment_contact_phone': onboarding_dict.get('appointment_contact_phone'),
            'appointment_contact_email': onboarding_dict.get('appointment_contact_email'),
            'medical_contact_name': onboarding_dict.get('medical_contact_name'),
            'medical_contact_phone': onboarding_dict.get('medical_contact_phone'),
            'medical_contact_email': onboarding_dict.get('medical_contact_email'),
            'primary_care_provider': onboarding_dict.get('primary_care_provider'),
            'pcp_last_seen': onboarding_dict.get('pcp_last_seen'),
            'active_specialists': onboarding_dict.get('active_specialist'),
            'chronic_conditions_provider': onboarding_dict.get('chronic_conditions_onboarding'),
            'clinical_biometric': onboarding_dict.get('clinical_biometric'),
            'provider_mh_schizophrenia': onboarding_dict.get('mh_schizophrenia', False),
            'provider_mh_depression': onboarding_dict.get('mh_depression', False),
            'provider_mh_anxiety': onboarding_dict.get('mh_anxiety', False),
            'provider_mh_stress': onboarding_dict.get('mh_stress', False),
            'provider_mh_adhd': onboarding_dict.get('mh_adhd', False),
            'provider_mh_bipolar': onboarding_dict.get('mh_bipolar', False),
            'provider_mh_suicidal': onboarding_dict.get('mh_suicidal', False),
            'annual_well_visit': onboarding_dict.get('annual_well_visit', False),
            # New onboarding columns
            'eligibility_status': onboarding_dict.get('eligibility_status'),
            'eligibility_notes': onboarding_dict.get('eligibility_notes'),
            'eligibility_verified': onboarding_dict.get('eligibility_verified', False),
            'emed_chart_created': onboarding_dict.get('emed_chart_created', False),
            'chart_id': onboarding_dict.get('chart_id'),
            'facility_confirmed': onboarding_dict.get('facility_confirmed', False),
            'chart_notes': onboarding_dict.get('chart_notes'),
            'intake_call_completed': onboarding_dict.get('intake_call_completed', False),
            'intake_notes': onboarding_dict.get('intake_notes'),
        }

        patient_id = None
        existing_patient = None
        
        # First check if onboarding already has a valid patient_id
        if onboarding_dict.get('patient_id'):
            existing_patient = conn.execute("SELECT patient_id FROM patients WHERE patient_id = ?", (onboarding_dict['patient_id'],)).fetchone()
        
        # If no existing patient found by patient_id, check for duplicates by name and DOB
        if not existing_patient:
            first_name = onboarding_dict.get('first_name', '').strip()
            last_name = onboarding_dict.get('last_name', '').strip()
            date_of_birth = onboarding_dict.get('date_of_birth')
            
            if first_name and last_name and date_of_birth:
                # Generate the expected text-based patient_id for this patient
                expected_patient_id = generate_patient_id(first_name, last_name, date_of_birth)
                
                # Check for existing patient with same text-based patient_id OR same name and DOB
                existing_patient = conn.execute("""
                    SELECT patient_id FROM patients 
                    WHERE (patient_id = ? OR 
                           (LOWER(TRIM(first_name)) = LOWER(?) 
                            AND LOWER(TRIM(last_name)) = LOWER(?) 
                            AND date_of_birth = ?))
                    AND patient_id IS NOT NULL
                    LIMIT 1
                """, (expected_patient_id, first_name.lower(), last_name.lower(), date_of_birth)).fetchone()
                
                if existing_patient:
                    # Update onboarding record with found patient_id
                    patient_id = existing_patient[0]
                    conn.execute("UPDATE onboarding_patients SET patient_id = ? WHERE onboarding_id = ?", (patient_id, onboarding_id))

        if existing_patient:
            # Build dynamic UPDATE clauses for columns that exist in patients table
            set_clauses = []
            params = []
            for col, val in candidate.items():
                if col in patients_cols:
                    # preserve existing richer provider data using COALESCE for clinical/provider fields
                    if col.startswith('appointment_contact_') or col.startswith('medical_contact_') or col in ('primary_care_provider','pcp_last_seen','active_specialists','chronic_conditions_provider','clinical_biometric') or col.startswith('provider_mh_'):
                        set_clauses.append(f"{col} = COALESCE(?, {col})")
                        params.append(val)
                    else:
                        set_clauses.append(f"{col} = ?")
                        params.append(val)

            set_clauses.append("updated_date = datetime('now')")
            params.append(patient_id)

            if len(set_clauses) > 1:
                query = f"UPDATE patients SET {', '.join(set_clauses)} WHERE patient_id = ?"
                conn.execute(query, params)
        else:
            # Build dynamic INSERT columns/values based on existing patients columns
            insert_cols = []
            insert_vals = []
            for col, val in candidate.items():
                if col in patients_cols:
                    insert_cols.append(col)
                    insert_vals.append(val)

            # Ensure status/enrollment_date/created_date if available
            if 'enrollment_date' in patients_cols:
                insert_cols.append('enrollment_date')
                insert_vals.append(datetime.now().strftime('%Y-%m-%d'))
            if 'created_date' in patients_cols:
                insert_cols.append('created_date')
                insert_vals.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            if 'status' in patients_cols and 'status' not in insert_cols:
                insert_cols.append('status')
                insert_vals.append('Active')

            if not insert_cols:
                raise Exception('No matching patient columns found to insert')

            # Generate proper text-based patient_id
            patient_id = generate_patient_id(
                onboarding_dict.get('first_name', ''),
                onboarding_dict.get('last_name', ''),
                onboarding_dict.get('date_of_birth', '')
            )
            
            # Add patient_id to the insert if the column exists
            if 'patient_id' in patients_cols:
                insert_cols.append('patient_id')
                insert_vals.append(patient_id)
            
            placeholders = ','.join(['?'] * len(insert_cols))
            cols_sql = ','.join(insert_cols)
            cursor = conn.execute(f"INSERT INTO patients ({cols_sql}) VALUES ({placeholders})", tuple(insert_vals))
            
            # If patient_id column didn't exist in the original insert, update it now
            if 'patient_id' not in insert_cols:
                conn.execute("UPDATE patients SET patient_id = ? WHERE rowid = ?", (patient_id, cursor.lastrowid))
            
            # Update onboarding record with patient_id if column exists
            conn.execute("UPDATE onboarding_patients SET patient_id = ? WHERE onboarding_id = ?", (patient_id, onboarding_id))

        # Mark onboarding as complete
        conn.execute("""
            UPDATE onboarding_patients 
            SET completed_date = datetime('now'), updated_date = datetime('now')
            WHERE onboarding_id = ?
        """, (onboarding_id,))

        # Create patient assignments if provider or coordinator are assigned
        provider_id = onboarding_dict.get('assigned_provider_user_id')
        coordinator_id = onboarding_dict.get('assigned_coordinator_user_id')
        
        print(f"DEBUG: provider_id={provider_id}, coordinator_id={coordinator_id}")
        print(f"DEBUG: patient_id={patient_id}")
        
        if provider_id or coordinator_id:
            print(f"DEBUG: Creating patient assignment")
            # Check if assignment already exists
            existing_assignment = conn.execute("""
                SELECT assignment_id FROM patient_assignments 
                WHERE patient_id = ? AND assignment_type = 'onboarding' AND status = 'active'
            """, (patient_id,)).fetchone()
            
            if existing_assignment:
                print(f"DEBUG: Updating existing assignment {existing_assignment[0]}")
                # Update existing assignment
                conn.execute("""
                    UPDATE patient_assignments 
                    SET provider_id = ?, coordinator_id = ?, 
                        updated_date = datetime('now')
                    WHERE assignment_id = ?
                """, (provider_id, coordinator_id, existing_assignment[0]))
            else:
                print(f"DEBUG: Creating new assignment")
                # Create new assignment
                conn.execute("""
                    INSERT INTO patient_assignments (
                        patient_id, provider_id, coordinator_id, assignment_date, 
                        assignment_type, status, priority_level, notes, 
                        created_date, updated_date
                    ) VALUES (?, ?, ?, datetime('now'), 'onboarding', 'active', 'medium', 
                             'Assignment created from onboarding completion', 
                             datetime('now'), datetime('now'))
                """, (patient_id, provider_id, coordinator_id))
                print(f"DEBUG: Assignment created successfully")

        conn.commit()
        
        # Sync data to patient_panel table
        try:
            sync_onboarding_to_patient_panel(onboarding_id)
        except Exception as e:
            print(f"Warning: Failed to sync to patient_panel: {e}")
        
        return patient_id

    finally:
        conn.close()

def get_users_by_role_name(role_name):
    """Get all users with a specific role by role name"""
    conn = get_db_connection()
    try:
        users = conn.execute("""
            SELECT u.user_id, u.username, u.full_name 
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN roles r ON ur.role_id = r.role_id
            WHERE r.role_name = ?
        """, (role_name,)).fetchall()
        return [dict(user) for user in users]
    finally:
        conn.close()

def insert_patient_from_onboarding(onboarding_id):
    """Insert patient data into patients table from onboarding data while keeping onboarding record"""
    conn = get_db_connection()
    try:
        # Get onboarding data
        onboarding = conn.execute("""
            SELECT * FROM onboarding_patients WHERE onboarding_id = ?
        """, (onboarding_id,)).fetchone()
        
        if not onboarding:
            raise Exception(f"No onboarding patient found with ID {onboarding_id}")
            
        onboarding_dict = dict(onboarding)
        
        # Check if patient already exists in main table
        if onboarding_dict.get('patient_id'):
            existing_patient = conn.execute("""
                SELECT patient_id FROM patients WHERE patient_id = ?
            """, (onboarding_dict['patient_id'],)).fetchone()
            if existing_patient:
                # Update existing patient with latest onboarding data, including assigned_coordinator_id
                conn.execute("""
                    UPDATE patients SET
                        first_name = ?, last_name = ?, date_of_birth = ?, gender = ?,
                        phone_primary = ?, email = ?,
                        address_street = ?, address_city = ?, address_state = ?, address_zip = ?,
                        emergency_contact_name = ?, emergency_contact_phone = ?,
                        insurance_primary = ?, insurance_policy_number = ?,
                        medical_records_requested = ?, referral_documents_received = ?,
                        insurance_cards_received = ?, emed_signature_received = ?,
                        hypertension = ?, mental_health_concerns = ?, dementia = ?,
                        appointment_contact_name = COALESCE(?, appointment_contact_name),
                        appointment_contact_phone = COALESCE(?, appointment_contact_phone),
                        appointment_contact_email = COALESCE(?, appointment_contact_email),
                        medical_contact_name = COALESCE(?, medical_contact_name),
                        medical_contact_phone = COALESCE(?, medical_contact_phone),
                        medical_contact_email = COALESCE(?, medical_contact_email),
                        primary_care_provider = COALESCE(?, primary_care_provider),
                        pcp_last_seen = COALESCE(?, pcp_last_seen),
                        annual_well_visit = ?,
                        assigned_coordinator_id = ?,
                        updated_date = CURRENT_TIMESTAMP
                    WHERE patient_id = ?
                """,
                (
                    onboarding_dict['first_name'], onboarding_dict['last_name'],
                    onboarding_dict['date_of_birth'], onboarding_dict.get('gender'),
                    onboarding_dict.get('phone_primary'), onboarding_dict.get('email'),
                    onboarding_dict.get('address_street'), onboarding_dict.get('address_city'),
                    onboarding_dict.get('address_state'), onboarding_dict.get('address_zip'),
                    onboarding_dict.get('emergency_contact_name'), onboarding_dict.get('emergency_contact_phone'),
                    onboarding_dict.get('insurance_provider'), onboarding_dict.get('policy_number'),
                    onboarding_dict.get('medical_records_requested', False),
                    onboarding_dict.get('referral_documents_received', False),
                    onboarding_dict.get('insurance_cards_received', False),
                    onboarding_dict.get('emed_signature_received', False),
                    onboarding_dict.get('hypertension', False),
                    onboarding_dict.get('mental_health_concerns', False),
                    onboarding_dict.get('dementia', False),
                    onboarding_dict.get('appointment_contact_name'),
                    onboarding_dict.get('appointment_contact_phone'),
                    onboarding_dict.get('appointment_contact_email'),
                    onboarding_dict.get('medical_contact_name'),
                    onboarding_dict.get('medical_contact_phone'),
                    onboarding_dict.get('medical_contact_email'),
                    onboarding_dict.get('primary_care_provider'),
                    onboarding_dict.get('pcp_last_seen'),
                    onboarding_dict.get('annual_well_visit', False),
                    onboarding_dict.get('assigned_coordinator_user_id'),
                    onboarding_dict['patient_id']
                )
                )
                patient_id = onboarding_dict['patient_id']
        else:
            # Create new patient record, including assigned_coordinator_id
            cursor = conn.execute("""
                INSERT INTO patients (
                    first_name, last_name, date_of_birth, gender, phone_primary, email,
                    address_street, address_city, address_state, address_zip,
                    emergency_contact_name, emergency_contact_phone,
                    insurance_primary, insurance_policy_number,
                    medical_records_requested, referral_documents_received,
                    insurance_cards_received, emed_signature_received,
                    hypertension, mental_health_concerns, dementia,
                    appointment_contact_name, appointment_contact_phone, appointment_contact_email,
                    medical_contact_name, medical_contact_phone, medical_contact_email,
                    primary_care_provider, pcp_last_seen,
                    last_annual_wellness_visit,
                    assigned_coordinator_id,
                    enrollment_date, created_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'Active')
            """,
            (
                onboarding_dict['first_name'], onboarding_dict['last_name'],
                onboarding_dict['date_of_birth'], onboarding_dict.get('gender'),
                onboarding_dict.get('phone_primary'), onboarding_dict.get('email'),
                onboarding_dict.get('address_street'), onboarding_dict.get('address_city'),
                onboarding_dict.get('address_state'), onboarding_dict.get('address_zip'),
                onboarding_dict.get('emergency_contact_name'), onboarding_dict.get('emergency_contact_phone'),
                onboarding_dict.get('insurance_provider'), onboarding_dict.get('policy_number'),
                onboarding_dict.get('medical_records_requested', False),
                onboarding_dict.get('referral_documents_received', False),
                onboarding_dict.get('insurance_cards_received', False),
                onboarding_dict.get('emed_signature_received', False),
                onboarding_dict.get('hypertension', False),
                onboarding_dict.get('mental_health_concerns', False),
                onboarding_dict.get('dementia', False),
                onboarding_dict.get('appointment_contact_name'),
                onboarding_dict.get('appointment_contact_phone'),
                onboarding_dict.get('appointment_contact_email'),
                onboarding_dict.get('medical_contact_name'),
                onboarding_dict.get('medical_contact_phone'),
                onboarding_dict.get('medical_contact_email'),
                onboarding_dict.get('primary_care_provider'),
                onboarding_dict.get('pcp_last_seen'),
                onboarding_dict.get('annual_well_visit', False),
                onboarding_dict.get('assigned_coordinator_user_id'),
            ))
            integer_patient_id = cursor.lastrowid
            
            # Generate the text-based patient_id using the same function
            text_patient_id = generate_patient_id(
                onboarding_dict.get('first_name', ''),
                onboarding_dict.get('last_name', ''),
                onboarding_dict.get('date_of_birth', '')
            )
            
            # Update onboarding record with the integer patient_id (for backward compatibility)
            conn.execute("""
                UPDATE onboarding_patients SET patient_id = ? WHERE onboarding_id = ?
            """, (integer_patient_id, onboarding_id))
        
        # Create patient assignments in patient_assignments table using text-based patient_id
        provider_id = onboarding_dict.get('assigned_provider_user_id')
        coordinator_id = onboarding_dict.get('assigned_coordinator_user_id')
        
        print(f"DEBUG: provider_id={provider_id}, coordinator_id={coordinator_id}")
        print(f"DEBUG: text_patient_id={text_patient_id}")
        
        if provider_id or coordinator_id:
            print(f"DEBUG: Entering assignment creation logic")
            # Check if assignment already exists using text-based patient_id
            existing_assignment = conn.execute("""
                SELECT assignment_id FROM patient_assignments 
                WHERE patient_id = ? AND assignment_type = 'onboarding' AND status = 'active'
            """, (text_patient_id,)).fetchone()
            
            if existing_assignment:
                print(f"DEBUG: Updating existing assignment {existing_assignment['assignment_id']}")
                # Update existing assignment
                conn.execute("""
                    UPDATE patient_assignments 
                    SET provider_id = ?, coordinator_id = ?, 
                        updated_date = datetime('now')
                    WHERE assignment_id = ?
                """, (provider_id, coordinator_id, existing_assignment['assignment_id']))
            else:
                print(f"DEBUG: Creating new assignment for {text_patient_id}")
                # Create new assignment
                conn.execute("""
                    INSERT INTO patient_assignments (
                        patient_id, provider_id, coordinator_id, assignment_date, 
                        assignment_type, status, priority_level, notes, 
                        created_date, updated_date
                    ) VALUES (?, ?, ?, datetime('now'), 'onboarding', 'active', 'medium', 
                             'Assignment created from onboarding completion', 
                             datetime('now'), datetime('now'))
                """, (text_patient_id, provider_id, coordinator_id))
                print(f"DEBUG: Assignment created successfully")
        
        print(f"DEBUG: About to commit changes")
        conn.commit()
        print(f"DEBUG: Changes committed successfully")
        return text_patient_id
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_users_by_role(role_identifier):
    """Get all users with a specific role - works with role_id (int) or role_name (string)"""
    conn = get_db_connection()
    try:
        if isinstance(role_identifier, int):
            # Handle role_id
            users = conn.execute("""
                SELECT u.user_id, u.username, u.full_name 
                FROM users u
                JOIN user_roles ur ON u.user_id = ur.user_id
                JOIN roles r ON ur.role_id = r.role_id
                WHERE r.role_id = ?
            """, (role_identifier,)).fetchall()
        else:
            # Handle role_name (string)
            users = conn.execute("""
                SELECT u.user_id, u.username, u.full_name 
                FROM users u
                JOIN user_roles ur ON u.user_id = ur.user_id
                JOIN roles r ON ur.role_id = r.role_id
                WHERE r.role_name = ?
            """, (role_identifier,)).fetchall()
        return [dict(user) for user in users]
    finally:
        conn.close()

def get_coordinator_weekly_patient_minutes(coordinator_id, weeks_back=4):
    """Get minutes logged per patient per week for coordinator (P0 Enhancement)"""
    conn = get_db_connection()
    try:
        # Calculate the date range
        query = """
            SELECT
                ct.patient_id,
                COALESCE(p.first_name || ' ' || p.last_name, ct.patient_id) as patient_name,
                strftime('%Y-%W', ct.task_date) as week,
                strftime('%Y-%m-%d', ct.task_date) as task_date,
                SUM(CAST(ct.duration_minutes AS INTEGER)) as total_minutes,
                COUNT(*) as task_count
            FROM coordinator_tasks_2025_09 ct
            LEFT JOIN patients p ON CAST(ct.patient_id AS INTEGER) = p.patient_id
            WHERE ct.coordinator_id = ?
            AND ct.task_date >= date('now', '-' || ? || ' days')
            AND ct.duration_minutes IS NOT NULL
            AND CAST(ct.duration_minutes AS INTEGER) > 0
            GROUP BY ct.patient_id, strftime('%Y-%W', ct.task_date)
            ORDER BY week DESC, patient_name
        """
        
        days_back = weeks_back * 7
        result = conn.execute(query, (coordinator_id, days_back)).fetchall()
        return [dict(row) for row in result]
    finally:
        conn.close()

def get_coordinator_tasks_by_date_range(coordinator_id, start_date, end_date):
    """Get all coordinator tasks within date range
    
    Handles both numeric coordinator_ids and unmapped staff codes stored as coordinator_id.
    patient_id field may contain actual patient_id or "Last, First DOB" format for unmatched patients.
    """
    conn = get_db_connection()
    try:
        query = """
            SELECT
                ct.coordinator_task_id,
                ct.patient_id as patient_name,
                ct.task_date,
                ct.duration_minutes,
                ct.task_type,
                ct.notes,
                CASE
                    WHEN ct.patient_id GLOB '[0-9]*' THEN ct.patient_id
                    ELSE NULL
                END as actual_patient_id
            FROM coordinator_tasks_2025_09 ct
            WHERE ct.coordinator_id = CAST(? AS TEXT)
            AND date(ct.task_date) >= date(?)
            AND date(ct.task_date) <= date(?)
            ORDER BY ct.task_date DESC
        """
        return conn.execute(query, (str(coordinator_id), start_date, end_date)).fetchall()
    finally:
        conn.close()

def get_coordinator_monthly_summary_current_month(coordinator_id):
    """Get current month summary for coordinator
    
    Handles both numeric coordinator_ids and unmapped staff codes.
    For staff codes, coordinator_id in monthly summary table may not match since it uses INTEGER.
    """
    conn = get_db_connection()
    try:
        # First try direct coordinator_id match (for numeric IDs)
        # Note: This function primarily queries coordinator_monthly_summary table, not coordinator_tasks
        # The coordinator_monthly_summary table is not partitioned according to the migration plan
        query_numeric = """
            SELECT
                cms.patient_name,
                cms.total_minutes,
                cms.billing_code,
                cms.billing_code_description
            FROM coordinator_monthly_summary cms
            WHERE cms.coordinator_id = ?
            AND cms.year = CAST(strftime('%Y', 'now') AS INTEGER)
            AND cms.month = CAST(strftime('%m', 'now') AS INTEGER)
            ORDER BY cms.total_minutes DESC
        """
        
        # Try to convert coordinator_id to integer for monthly summary lookup
        try:
            numeric_coordinator_id = int(coordinator_id)
            results = conn.execute(query_numeric, (numeric_coordinator_id,)).fetchall()
            if results:
                return results
        except (ValueError, TypeError):
            # coordinator_id is not numeric (it's a staff code)
            pass
        
        # If no results or coordinator_id is a staff code, try to find by coordinator name
        # Get coordinator name from users/staff mapping
        try:
            staff_mapping = conn.execute("""
                SELECT u.full_name
                FROM staff_code_mapping scm
                JOIN users u ON scm.user_id = u.user_id
                WHERE scm.staff_code = ?
            """, (str(coordinator_id),)).fetchone()
            
            if staff_mapping:
                coordinator_name = staff_mapping[0]
                query_by_name = """
                    SELECT
                        cms.patient_name,
                        cms.total_minutes,
                        cms.billing_code,
                        cms.billing_code_description
                    FROM coordinator_monthly_summary cms
                    WHERE cms.coordinator_name = ?
                    AND cms.year = CAST(strftime('%Y', 'now') AS INTEGER)
                    AND cms.month = CAST(strftime('%m', 'now') AS INTEGER)
                    ORDER BY cms.total_minutes DESC
                """
                return conn.execute(query_by_name, (coordinator_name,)).fetchall()
        except:
            pass
        
        # Return empty list if no matches found
        return []
    finally:
        conn.close()

def get_coordinator_patient_service_analysis(coordinator_id=None, weeks_back=8):
    """Get detailed patient service analysis for coordinator with patient activity breakdown"""
    conn = get_db_connection()
    try:
        # Build coordinator filter condition
        if coordinator_id:
            # Handle both numeric coordinator_id and staff codes
            coordinator_filter = "WHERE CAST(ct.coordinator_id AS TEXT) = CAST(? AS TEXT)"
            params = [coordinator_id]
        else:
            coordinator_filter = ""
            params = []
        
        # Add date filter if weeks_back is specified
        if weeks_back:
            if coordinator_filter:
                coordinator_filter += " AND ct.task_date >= date('now', '-' || ? || ' days')"
            else:
                coordinator_filter = "WHERE ct.task_date >= date('now', '-' || ? || ' days')"
            params.append(weeks_back * 7)
        
        query = f"""
            SELECT
                ct.patient_id,
                ct.coordinator_id,
                ct.coordinator_name,
                COUNT(*) as total_tasks,
                SUM(ct.duration_minutes) as total_minutes,
                AVG(ct.duration_minutes) as avg_minutes_per_task,
                MIN(ct.task_date) as first_task_date,
                MAX(ct.task_date) as last_task_date,
                COUNT(DISTINCT ct.task_date) as active_days,
                GROUP_CONCAT(DISTINCT ct.task_type) as task_types
            FROM coordinator_tasks_2025_09 ct
            {coordinator_filter}
            AND ct.duration_minutes > 0
            GROUP BY ct.patient_id, ct.coordinator_id
            ORDER BY total_minutes DESC, total_tasks DESC
        """
        
        result = conn.execute(query, params).fetchall()
        return [dict(row) for row in result]
    except Exception as e:
        print(f"Error in get_coordinator_patient_service_analysis: {e}")
        return []
    finally:
        conn.close()

def add_coordinator_tasks_enhancements():
    """Add enhancements to coordinator_tasks table for differential imports"""
    conn = get_db_connection()
    try:
        # Add source_hash column if it doesn't exist
        try:
            conn.execute("ALTER TABLE coordinator_tasks ADD COLUMN source_hash TEXT;")
        except:
            pass  # Column might already exist
            
        # Add user_id column if it doesn't exist
        try:
            conn.execute("ALTER TABLE coordinator_tasks ADD COLUMN user_id INTEGER;")
        except:
            pass  # Column might already exist
            
        # Add coordinator_name column if it doesn't exist
        try:
            conn.execute("ALTER TABLE coordinator_tasks ADD COLUMN coordinator_name TEXT;")
        except:
            pass  # Column might already exist
            
        conn.commit()
    except Exception as e:
        print(f"Error enhancing coordinator_tasks table: {e}")
    finally:
        conn.close()

# ========================================
# P0 ENHANCEMENT FUNCTIONS
# ========================================

def get_providers_list():
    """Get list of providers for phone review dropdown (P0 Enhancement)"""
    conn = get_db_connection()
    try:
        query = """
            SELECT 
                u.user_id,
                u.full_name,
                u.email
            FROM users u
            JOIN user_roles ur ON u.user_id = ur.user_id
            WHERE ur.role_id = 33  -- Care Provider role
            AND u.status = 'Active'
            ORDER BY u.full_name
        """
        result = conn.execute(query).fetchall()
        return [dict(row) for row in result]
    finally:
        conn.close()

def save_coordinator_phone_review(coordinator_id, form_data):
    """Save phone review task for coordinator (P0 Enhancement)"""
    conn = get_db_connection()
    try:
        # Insert phone review task
        provider_as_pid = normalize_patient_id(form_data.get('provider_name', ''), conn=conn)
        conn.execute("""
            INSERT INTO coordinator_tasks_2025_09 (
                coordinator_id, patient_id, task_date, task_type,
                duration_minutes, notes, source_system, imported_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'PHONE_REVIEW', CURRENT_TIMESTAMP)
        """, (
            coordinator_id,
            provider_as_pid,
            form_data['task_date'].strftime('%Y-%m-%d'),
            "19|Communication|Communication: Phone",
            form_data['duration_minutes'],
            f"Phone review with {form_data.get('provider_name', '')}: {form_data.get('notes', '')}"
        ))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving phone review: {e}")
        return False
    finally:
        conn.close()

def get_available_workflows():
    """Get available workflow IDs for workflow management (P0 Enhancement)"""
    return [
        "Standard Onboarding",
        "Expedited Onboarding", 
        "Complex Medical Case",
        "Insurance Verification",
        "Provider Assignment"
    ]

def get_coordinator_monthly_patient_service_minutes(coordinator_id, months_back=3):
    """Get patient service minutes per month for CM/LC roles (P0 Enhancement)"""
    conn = get_db_connection()
    try:
        query = """
            SELECT
                cms.month,
                cms.year,
                cms.coordinator_id,
                cms.total_patients_served,
                cms.total_minutes_logged,
                cms.avg_minutes_per_patient,
                cms.total_tasks_completed
            FROM coordinator_monthly_summary cms
            WHERE cms.coordinator_id = ?
            AND cms.year >= strftime('%Y', date('now', '-' || ? || ' months'))
            ORDER BY cms.year DESC, cms.month DESC
        """
        
        result = conn.execute(query, (coordinator_id, months_back)).fetchall()
        return [dict(row) for row in result]
    finally:
        conn.close()

def get_provider_patient_panel_enhanced(user_id):
    """Get enhanced provider patient panel with new columns (P0 Enhancement)"""
    conn = get_db_connection()
    try:
        # Use a subquery to get distinct patient_ids for this user to avoid duplicate assignment rows
        # Join with patient_panel to get the correct last_visit_date that's used in admin dashboard
        query = """
            SELECT
                p.patient_id,
                p.first_name,
                p.last_name,
                p.date_of_birth,
                p.status,
                p.address_street,
                p.address_city,
                p.address_state,
                p.address_zip,
                p.phone_primary,
                p.email,
                p.facility AS facility,
                p.current_facility_id,
                COALESCE(pp.last_visit_date, p.last_visit_date) as last_visit_date,
                COALESCE(pp.last_visit_service_type, p.service_type) as service_type,
                pp.last_visit_service_type,
                pa.coordinator_id as assigned_coordinator_id,
                pa.provider_id as assigned_provider_id
            FROM patient_assignments pa
            JOIN patients p ON pa.patient_id = p.patient_id
            LEFT JOIN patient_panel pp ON p.patient_id = pp.patient_id
            WHERE pa.provider_id = ?
            ORDER BY p.last_name, p.first_name
        """
        result = conn.execute(query, (user_id,)).fetchall()
        return [dict(row) for row in result]
    except Exception as e:
        print(f"Error in get_provider_patient_panel_enhanced: {e}")
        # Return empty list if all else fails
        return []
    finally:
        conn.close()


def get_coordinator_patient_panel_enhanced(user_id):
    """Get enhanced coordinator patient panel with new columns (P0 Enhancement)"""
    conn = get_db_connection()
    try:
        # Use a subquery to get distinct patient_ids for this user to avoid duplicate assignment rows
        # Join with patient_panel to get the correct last_visit_date that's used in admin dashboard
        query = """
SELECT
    p.patient_id,
    p.first_name,
    p.last_name,
    p.date_of_birth,
    p.status,
    p.address_street,
    p.address_city,
    p.address_state,
    p.address_zip,
    p.phone_primary,
    p.email,
    p.facility AS facility,
    p.current_facility_id,
    COALESCE(pp.last_visit_date, p.last_visit_date) as last_visit_date,
    COALESCE(pp.last_visit_service_type, p.service_type) as service_type,
    pp.last_visit_service_type,
    p.appointment_contact_name,
    p.appointment_contact_phone,
    p.medical_contact_name,
    p.medical_contact_phone,
    pa.provider_id as assigned_provider_id,
    pa.coordinator_id as assigned_coordinator_id
FROM patient_assignments pa
JOIN patients p ON pa.patient_id = p.patient_id
LEFT JOIN patient_panel pp ON p.patient_id = pp.patient_id
WHERE pa.coordinator_id = ?
ORDER BY p.last_name, p.first_name
        """
        result = conn.execute(query, (user_id,)).fetchall()
        # Add POC-A and POC-M columns (name & phone combined)
        patients = []
        for row in result:
            d = dict(row)
            d['POC-A'] = f"{d.get('appointment_contact_name','') or ''} {d.get('appointment_contact_phone','') or ''}".strip()
            d['POC-M'] = f"{d.get('medical_contact_name','') or ''} {d.get('medical_contact_phone','') or ''}".strip()
            patients.append(d)
        return patients
    except Exception as e:
        print(f"Error in get_coordinator_patient_panel_enhanced: {e}")
        return []
    finally:
        conn.close()

def get_all_facilities():
    """Get all facilities from the facilities table"""
    conn = get_db_connection()
    try:
        query = """
            SELECT facility_id, facility_name
            FROM facilities
            ORDER BY facility_name
        """
        result = conn.execute(query).fetchall()
        return [dict(row) for row in result]
    except Exception as e:
        print(f"Error in get_all_facilities: {e}")
        # Return empty list if all else fails
        return []
    finally:
        conn.close()


def get_all_patients_simple():
    """Get all patients from the database - simple test function"""
    conn = get_db_connection()
    try:
        query = "SELECT patient_id, first_name, last_name, status FROM patients LIMIT 10"
        result = conn.execute(query).fetchall()
        return [dict(row) for row in result]
    finally:
        conn.close()


def get_user_patient_assignments_simple(user_id):
    """Get patient assignments for a user - simple test function"""
    conn = get_db_connection()
    try:
        query = """
            SELECT upa.patient_id, p.first_name, p.last_name, p.status
            FROM user_patient_assignments upa
            JOIN patients p ON upa.patient_id = p.patient_id
            WHERE upa.user_id = ?
            LIMIT 10
        """
        result = conn.execute(query, (user_id,)).fetchall()
        return [dict(row) for row in result]
    finally:
        conn.close()


def get_patient_facility_provider_info(patient_ids):
    """Return a mapping of patient_id -> {facility_name, provider_name, last_task_date}
    patient_ids: iterable of patient_id values (ints or strings)
    """
    if not patient_ids:
        return {}

    # Ensure we have a list
    ids = list(patient_ids)
    conn = get_db_connection()
    try:
        query = """
            SELECT * FROM patient_panel
        """
        result = conn.execute(query).fetchall()
        # Map last_visit_service_type to service_type for dashboard compatibility
        patients = []
        for row in result:
            d = dict(row)
            if 'last_visit_service_type' in d:
                d['service_type'] = d['last_visit_service_type']
            patients.append(d)
        return patients
    finally:
        conn.close()

def get_provider_panel_patients_by_month(provider_id, selected_month):
    """Get provider panel patients pre-loaded for specific month (P0 Enhancement)"""
    conn = get_db_connection()
    try:
        # Parse the selected month (format: "2025-09")
        year, month = selected_month.split('-')
        # Use distinct patient assignments and map facility and last task date
        query = """
            SELECT
                p.patient_id,
                p.first_name,
                p.last_name,
                COALESCE(p.last_visit_date, lp.last_task_date) AS last_visit_date,
                COALESCE(p.facility, f.facility_name, '') AS facility,
                p.status,
                p.phone_primary
            FROM (
                SELECT DISTINCT patient_id FROM user_patient_assignments WHERE user_id = ?
            ) upa
            JOIN patients p ON upa.patient_id = p.patient_id
            LEFT JOIN (
                SELECT patient_id, MAX(task_date) AS last_task_date
                FROM provider_tasks_2025_09
                GROUP BY patient_id
            ) lp ON p.patient_id = lp.patient_id
            LEFT JOIN facilities f ON p.current_facility_id = f.facility_id
            WHERE (p.last_visit_date IS NULL OR strftime('%Y-%m', COALESCE(p.last_visit_date, lp.last_task_date)) <= ?)
            ORDER BY p.last_name, p.first_name
        """

        result = conn.execute(query, (provider_id, selected_month)).fetchall()
        return [dict(row) for row in result]
    finally:
        conn.close()

def get_cpm_current_month_summary(user_id):
    """Get CPM monthly summary for current month (P0 Enhancement)"""
    conn = get_db_connection()
    try:
        current_month = datetime.now().strftime('%m')
        current_year = datetime.now().strftime('%Y')
        
        query = """
            SELECT
                pms.month,
                pms.year,
                pms.provider_id,
                pms.total_patients_seen,
                pms.total_minutes_logged,
                pms.total_visits_completed,
                pms.avg_minutes_per_visit
            FROM provider_monthly_summary pms
            JOIN providers pr ON pms.provider_id = pr.provider_id
            WHERE pr.user_id = ?
            AND pms.month = ?
            AND pms.year = ?
        """
        
        result = conn.execute(query, (user_id, current_month, current_year)).fetchall()
        return dict(result[0]) if result else None
    finally:
        conn.close()

def get_calendar_months():
    """Get calendar months for PSL subdivision (P0 Enhancement)"""
    from datetime import datetime, timedelta
    
    months = []
    current_date = datetime.now()
    
    # Generate last 12 months
    for i in range(12):
        month_date = current_date - timedelta(days=i*30)
        months.append({
            'value': month_date.strftime('%Y-%m'),
            'label': month_date.strftime('%B %Y')
        })
    
    return months


def get_all_patient_panel():
    """
    Get all patient records from the patient_panel table.
    Returns a list of dictionaries containing all patient panel data.
    """
    conn = get_db_connection()
    try:
        query = "SELECT * FROM patient_panel"
        df = pd.read_sql_query(query, conn)
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Error in get_all_patient_panel: {e}")
        return []
    finally:
        conn.close()


def sync_onboarding_to_patient_panel(onboarding_id):
    """Sync completed onboarding data to patient_panel table"""
    conn = get_db_connection()
    try:
        # Get onboarding data
        onboarding = conn.execute("""
            SELECT * FROM onboarding_patients WHERE onboarding_id = ?
        """, (onboarding_id,)).fetchone()
        
        if not onboarding:
            return None
            
        onboarding_dict = dict(onboarding)
        patient_id = onboarding_dict.get('patient_id')
        
        if not patient_id:
            # Call transfer_onboarding_to_patient_table to create patient_id if missing
            patient_id = transfer_onboarding_to_patient_table(onboarding_id)
            if not patient_id:
                return None

        # Get existing patient_panel columns
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(patient_panel);")
        panel_cols = [r[1] for r in cur.fetchall()]

        # Mapping of onboarding data to patient_panel columns
        panel_data = {
            'patient_id': patient_id,
            'first_name': onboarding_dict.get('first_name'),
            'last_name': onboarding_dict.get('last_name'),
            'date_of_birth': onboarding_dict.get('date_of_birth'),
            'gender': onboarding_dict.get('gender'),
            'phone_primary': onboarding_dict.get('phone_primary'),
            'email': onboarding_dict.get('email'),
            'address_street': onboarding_dict.get('address_street'),
            'address_city': onboarding_dict.get('address_city'),
            'address_state': onboarding_dict.get('address_state'),
            'address_zip': onboarding_dict.get('address_zip'),
            'emergency_contact_name': onboarding_dict.get('emergency_contact_name'),
            'emergency_contact_phone': onboarding_dict.get('emergency_contact_phone'),
            'insurance_primary': onboarding_dict.get('insurance_provider'),
            'insurance_policy_number': onboarding_dict.get('policy_number'),
            'assigned_coordinator_id': onboarding_dict.get('assigned_coordinator_id'),
            'assigned_provider_id': onboarding_dict.get('assigned_provider_id'),
            # New onboarding columns
            'eligibility_status': onboarding_dict.get('eligibility_status'),
            'eligibility_notes': onboarding_dict.get('eligibility_notes'),
            'eligibility_verified': onboarding_dict.get('eligibility_verified', False),
            'emed_chart_created': onboarding_dict.get('emed_chart_created', False),
            'chart_id': onboarding_dict.get('chart_id'),
            'facility_confirmed': onboarding_dict.get('facility_confirmed', False),
            'chart_notes': onboarding_dict.get('chart_notes'),
            'intake_call_completed': onboarding_dict.get('intake_call_completed', False),
            'intake_notes': onboarding_dict.get('intake_notes'),
        }

        # Check if patient already exists in patient_panel
        existing_panel = conn.execute("""
            SELECT patient_id FROM patient_panel WHERE patient_id = ?
        """, (patient_id,)).fetchone()

        if existing_panel:
            # Update existing record
            update_fields = []
            params = []
            
            for col, val in panel_data.items():
                if col in panel_cols and col != 'patient_id':
                    update_fields.append(f"{col} = ?")
                    params.append(val)
            
            if update_fields:
                update_fields.append("updated_date = datetime('now')")
                params.append(patient_id)
                
                query = f"""
                    UPDATE patient_panel 
                    SET {', '.join(update_fields)}
                    WHERE patient_id = ?
                """
                conn.execute(query, params)
        else:
            # Insert new record
            insert_cols = []
            insert_vals = []
            
            for col, val in panel_data.items():
                if col in panel_cols:
                    insert_cols.append(col)
                    insert_vals.append(val)
            
            # Add created_date if column exists
            if 'created_date' in panel_cols:
                insert_cols.append('created_date')
                insert_vals.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            if insert_cols:
                placeholders = ','.join(['?'] * len(insert_cols))
                cols_sql = ','.join(insert_cols)
                conn.execute(f"INSERT INTO patient_panel ({cols_sql}) VALUES ({placeholders})", tuple(insert_vals))

        conn.commit()
        return patient_id

    finally:
        conn.close()

def create_patient_assignment(patient_id, provider_id=None, coordinator_id=None, assignment_type="onboarding", status="active", priority_level="medium", notes=None, created_by=None):
    """Create a patient assignment in the patient_assignments table"""
    conn = get_db_connection()
    try:
        # Check if assignment already exists for this patient
        existing = conn.execute("""
            SELECT assignment_id FROM patient_assignments 
            WHERE patient_id = ? AND assignment_type = ? AND status = 'active'
        """, (patient_id, assignment_type)).fetchone()
        
        if existing:
            # Update existing assignment
            conn.execute("""
                UPDATE patient_assignments 
                SET provider_id = ?, coordinator_id = ?, priority_level = ?, 
                    notes = ?, updated_date = datetime('now'), updated_by = ?
                WHERE assignment_id = ?
            """, (provider_id, coordinator_id, priority_level, notes, created_by, existing['assignment_id']))
        else:
            # Create new assignment
            conn.execute("""
                INSERT INTO patient_assignments (
                    patient_id, provider_id, coordinator_id, assignment_date, 
                    assignment_type, status, priority_level, notes, 
                    created_date, updated_date, created_by, updated_by
                ) VALUES (?, ?, ?, datetime('now'), ?, ?, ?, ?, 
                         datetime('now'), datetime('now'), ?, ?)
            """, (patient_id, provider_id, coordinator_id, assignment_type, 
                  status, priority_level, notes, created_by, created_by))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating patient assignment: {e}")
        return False
    finally:
        conn.close()


def get_provider_billing_summary(provider_id):
    """Get billing summary for a specific provider from provider_weekly_summary_with_billing"""
    conn = get_db_connection()
    try:
        query = """
        SELECT 
            provider_id,
            provider_name,
            week_start_date,
            week_end_date,
            year,
            week_number,
            total_tasks_completed,
            total_time_spent_minutes,
            billing_code,
            billing_code_description,
            status,
            paid,
            created_date,
            updated_date
        FROM provider_weekly_summary_with_billing
        WHERE provider_id = ?
        ORDER BY year DESC, week_number DESC
        """
        
        df = pd.read_sql_query(query, conn, params=[provider_id])
        return df
    except Exception as e:
        print(f"Error getting provider billing summary: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_provider_unbilled_tasks(provider_id):
    """Get unbilled tasks for a specific provider"""
    conn = get_db_connection()
    try:
        query = """
        SELECT 
            provider_task_id,
            provider_id,
            provider_name,
            patient_name,
            patient_id,
            task_date,
            month,
            year,
            billing_code,
            billing_code_description,
            task_description,
            minutes_of_service,
            status,
            notes
        FROM provider_tasks
        WHERE provider_id = ?
        AND year >= 2024
        AND (billing_code IS NULL 
             OR billing_code = '' 
             OR billing_code = 'Not_Billable'
             OR billing_code = 'PENDING')
        ORDER BY task_date DESC
        """
        
        df = pd.read_sql_query(query, conn, params=[provider_id])
        return df
    except Exception as e:
        print(f"Error getting provider unbilled tasks: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def update_billing_status(provider_id, week_start_date, paid_status):
    """Update the billing status (paid field) for a provider's weekly summary"""
    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE provider_weekly_summary_with_billing 
            SET paid = ?, updated_date = CURRENT_TIMESTAMP
            WHERE provider_id = ? AND week_start_date = ?
        """, (paid_status, provider_id, week_start_date))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating billing status: {e}")
        return False
    finally:
        conn.close()


def update_onboarding_patient_status(onboarding_id, status):
    """Update the patient_status of an onboarding patient"""
    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE onboarding_patients 
            SET patient_status = ?, updated_date = CURRENT_TIMESTAMP 
            WHERE onboarding_id = ?
        """, (status, onboarding_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating onboarding patient status: {e}")
        return False
    finally:
        conn.close()