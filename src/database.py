import calendar
import os
import sqlite3
from datetime import datetime, timedelta

import pandas as pd

# Database path toggle: Checks for 'USE_PROTOTYPE_MODE' file existence
# This is more reliable than environment variables in nested PowerShell contexts
PROTOTYPE_FLAG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "USE_PROTOTYPE_MODE"
)

if os.path.exists(PROTOTYPE_FLAG_FILE) or os.getenv("USE_PROTOTYPE") == "1":
    # Use relative path for cross-platform compatibility (Windows + Linux)
    # Assumes prototype.db is in the project root directory
    _base_db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "prototype.db"
    )
    print(
        f"⚠️  USING PROTOTYPE DATABASE (Flag file found: {os.path.exists(PROTOTYPE_FLAG_FILE)}) ⚠️"
    )
else:
    # Use relative path for cross-platform compatibility (Windows + Linux)
    # Assumes production.db is in the project root directory
    _base_db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "production.db"
    )

DB_PATH = os.getenv("DATABASE_PATH", _base_db_path)


def get_db_connection(db_path: str = None):
    """Return a SQLite connection. If db_path provided, use that path."""
    if db_path is None:
        db_path = DB_PATH

    print(f"Attempting to connect to DB: {db_path}")
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency (allows reads during writes)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
    conn.execute("PRAGMA synchronous=NORMAL")  # Faster than FULL, still safe
    return conn


def get_coordinator_patient_minutes_for_month(coordinator_id, year, month):
    """Return a dict mapping patient_id to total minutes for this coordinator and month."""
    conn = get_db_connection()
    try:
        table_name = f"coordinator_tasks_{year}_{str(month).zfill(2)}"
        # Check if table exists
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
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
        return {row["patient_id"]: row["total_minutes"] or 0 for row in result}
    except Exception as e:
        print(f"Error in get_coordinator_patient_minutes_for_month: {e}")
        return {}
    finally:
        conn.close()


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
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        if not table_exists:
            return []
        df = pd.read_sql_query(
            f"SELECT coordinator_id, duration_minutes FROM {table_name} WHERE duration_minutes IS NOT NULL AND duration_minutes > 0",
            conn,
        )
        if df.empty:
            return []
        summary = (
            df.groupby("coordinator_id").agg({"duration_minutes": "sum"}).reset_index()
        )
        summary = summary.rename(
            columns={
                "coordinator_id": "coordinator_id",
                "duration_minutes": "total_minutes",
            }
        )
        return summary.to_dict(orient="records")
    finally:
        conn.close()


def ensure_user_sessions_table(conn: sqlite3.Connection = None):
    close_conn = False
    try:
        if conn is None:
            conn = get_db_connection()
            close_conn = True
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            ("user_sessions",),
        ).fetchone()
        if not exists:
            conn.execute(
                """
                CREATE TABLE user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT,
                    expires_at TEXT,
                    last_activity TEXT
                )
                """
            )
            conn.commit()
    finally:
        if close_conn and conn:
            conn.close()


def create_user_session(user_id: int, days_valid: int = 30) -> str:
    import uuid
    from datetime import datetime, timedelta

    conn = get_db_connection()
    try:
        ensure_user_sessions_table(conn)
        sid = str(uuid.uuid4())
        now = datetime.now()
        expires = now + timedelta(days=days_valid)
        conn.execute(
            "INSERT INTO user_sessions(session_id, user_id, created_at, expires_at, last_activity) VALUES(?,?,?,?,?)",
            (sid, user_id, now.isoformat(), expires.isoformat(), now.isoformat()),
        )
        conn.commit()
        return sid
    finally:
        conn.close()


def get_user_by_session(session_id: str):
    from datetime import datetime

    conn = get_db_connection()
    try:
        ensure_user_sessions_table(conn)
        row = conn.execute(
            "SELECT u.user_id, u.username, u.email, u.first_name, u.last_name, u.full_name, u.status, s.expires_at FROM user_sessions s JOIN users u ON s.user_id = u.user_id WHERE s.session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        expires_at = row["expires_at"] if "expires_at" in row.keys() else row[7]
        try:
            if datetime.fromisoformat(expires_at) < datetime.now():
                return None
        except Exception:
            pass
        conn.execute(
            "UPDATE user_sessions SET last_activity = ? WHERE session_id = ?",
            (datetime.now().isoformat(), session_id),
        )
        conn.commit()
        return dict(row)
    finally:
        conn.close()


def delete_user_session(session_id: str):
    conn = get_db_connection()
    try:
        ensure_user_sessions_table(conn)
        conn.execute("DELETE FROM user_sessions WHERE session_id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()


def ensure_monthly_coordinator_tasks_table(
    year: int = None, month: int = None, conn: sqlite3.Connection = None
) -> str:
    """Ensure the monthly coordinator_tasks table for given year/month exists with required columns.
    - Creates the table if missing with full schema
    - Adds missing columns (source_system, imported_at, created_at_pst) if absent
    Returns the table_name.
    """
    close_conn = False
    try:
        if conn is None:
            conn = get_db_connection()
            close_conn = True
        if year is None or month is None:
            now = pd.Timestamp.now()
            year = int(year or now.year)
            month = int(month or now.month)
        table_name = f"coordinator_tasks_{year}_{str(month).zfill(2)}"
        # Check existence
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        if not exists:
            conn.execute(f"""
                CREATE TABLE {table_name} (
                    coordinator_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INT,
                    patient_id TEXT,
                    coordinator_id TEXT,
                    task_date TEXT,
                    duration_minutes INT,
                    task_type TEXT,
                    notes TEXT,
                    source_system TEXT,
                    imported_at TEXT,
                    created_at_pst TEXT
                )
            """)
            conn.commit()
        else:
            # Verify required columns exist; add if missing
            cols = conn.execute(f"PRAGMA table_info({table_name});").fetchall()
            # Using Row factory, access by name if available, else by index
            try:
                col_names = {row["name"] for row in cols}
            except Exception:
                col_names = {row[1] for row in cols}
            if "source_system" not in col_names:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN source_system TEXT;")
            if "imported_at" not in col_names:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN imported_at TEXT;")
            if "location_type" not in col_names:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN location_type TEXT;")
            if "patient_type" not in col_names:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN patient_type TEXT;")
            if "created_at_pst" not in col_names:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN created_at_pst TEXT;")
            # Add submission_status column for Daily Task Log feature
            if "submission_status" not in col_names:
                conn.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN submission_status TEXT DEFAULT 'pending';"
                )
            conn.commit()
        return table_name
    finally:
        if close_conn and conn:
            conn.close()


def ensure_monthly_provider_tasks_table(
    year: int = None, month: int = None, conn: sqlite3.Connection = None
) -> str:
    """Ensure the monthly provider_tasks table for given year/month exists with required columns.
    - Creates the table if missing with full schema matching transform_production_data_v3_fixed.py
    - Adds missing columns (source_system, imported_at, status, is_deleted) if absent
    Returns the table_name.
    """
    close_conn = False
    try:
        if conn is None:
            conn = get_db_connection()
            close_conn = True
        if year is None or month is None:
            now = pd.Timestamp.now()
            year = int(year or now.year)
            month = int(month or now.month)
        table_name = f"provider_tasks_{year}_{str(month).zfill(2)}"
        # Check existence
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        if not exists:
            conn.execute(f"""
                CREATE TABLE {table_name} (
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
                    icd_codes TEXT,
                    location_type TEXT,
                    patient_type TEXT,
                    source_system TEXT DEFAULT 'CSV_IMPORT',
                    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed',
                    is_deleted INTEGER DEFAULT 0,
                    UNIQUE(provider_id, patient_id, task_date, task_description)
                )
            """)
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_provider ON {table_name}(provider_id)"
            )
            conn.commit()
        else:
            # Verify required columns exist; add if missing
            cols = conn.execute(f"PRAGMA table_info({table_name});").fetchall()
            try:
                col_names = {row["name"] for row in cols}
            except Exception:
                col_names = {row[1] for row in cols}
            if "source_system" not in col_names:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN source_system TEXT;")
            if "imported_at" not in col_names:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN imported_at TEXT;")
            if "status" not in col_names:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN status TEXT DEFAULT 'completed';")
            if "is_deleted" not in col_names:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN is_deleted INTEGER DEFAULT 0;")
            if "icd_codes" not in col_names:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN icd_codes TEXT;")
            conn.commit()
        return table_name
    finally:
        if close_conn and conn:
            conn.close()


def get_monthly_task_tables(prefix: str, conn: sqlite3.Connection = None) -> list:
    """Return a list of table names that start with the given prefix."""
    close_conn = False
    try:
        if conn is None:
            conn = get_db_connection()
            close_conn = True
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ? ORDER BY name",
            (f"{prefix}%",),
        ).fetchall()
        return [row["name"] if "name" in row.keys() else row[0] for row in rows]
    finally:
        if close_conn and conn:
            conn.close()


def count_completed_steps(instance_id: int, conn: sqlite3.Connection = None) -> int:
    """Count completed workflow steps for an instance across all monthly coordinator_tasks tables."""
    close_conn = False
    try:
        if conn is None:
            conn = get_db_connection()
            close_conn = True
        tables = get_monthly_task_tables(prefix="coordinator_tasks_", conn=conn)
        total = 0
        for tn in tables:
            try:
                row = conn.execute(
                    f"SELECT COUNT(1) as c FROM {tn} WHERE task_type LIKE ?",
                    (f"WORKFLOW_STEP|{instance_id}|%",),
                ).fetchone()
                if row:
                    c = row["c"] if "c" in row.keys() else row[0]
                    total += int(c or 0)
            except Exception:
                # If table missing or malformed, skip
                pass
        return total
    finally:
        if close_conn and conn:
            conn.close()


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
            row = conn.execute(
                "SELECT last_name, first_name, date_of_birth FROM patients WHERE patient_id = ?",
                (pid_int,),
            ).fetchone()
            if row:
                last = (row["last_name"] or "").strip()
                first = (row["first_name"] or "").strip()
                dob = row["date_of_birth"] if "date_of_birth" in row.keys() else None
                parts = []
                if last:
                    parts.append(last.replace(",", ""))
                if first:
                    parts.append(first.replace(",", ""))
                if dob:
                    parts.append(str(dob))
                return " ".join(parts).strip()

        # Otherwise normalize string: remove commas and collapse whitespace
        s = str(patient_id or "")
        s = s.replace(",", " ").strip()
        s = " ".join(s.split())
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
    last = (last_name or "").strip().upper().replace(",", "").replace(" ", "")
    first = (first_name or "").strip().upper().replace(",", "").replace(" ", "")
    dob = str(date_of_birth or "").strip()

    # Convert date from YYYY-MM-DD to MM/DD/YYYY format
    if dob and len(dob) == 10 and dob.count("-") == 2:
        try:
            year, month, day = dob.split("-")
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

    return " ".join(parts)


def get_all_users():
    conn = get_db_connection()
    users = conn.execute(
        "SELECT user_id, username, full_name, email, status, hire_date FROM users ORDER BY hire_date DESC"
    ).fetchall()
    conn.close()
    return users


def get_all_roles():
    conn = get_db_connection()
    roles = conn.execute("SELECT role_id, role_name FROM roles").fetchall()
    conn.close()
    return roles


def get_user_roles_by_user_id(user_id):
    conn = get_db_connection()
    user_roles = conn.execute(
        "SELECT r.role_name, r.role_id, ur.is_primary FROM roles r JOIN user_roles ur ON r.role_id = ur.role_id WHERE ur.user_id = ?",
        (user_id,),
    ).fetchall()
    conn.close()
    return user_roles


def deactivate_user(user_id):
    """
    Deactivate a user by setting their status to 'inactive'

    Args:
        user_id: The user ID to deactivate

    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "UPDATE users SET status = 'inactive', updated_date = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()


def reactivate_user(user_id):
    """
    Reactivate a user by setting their status to 'active'

    Args:
        user_id: The user ID to reactivate

    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "UPDATE users SET status = 'active', updated_date = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()


def delete_user(user_id):
    """
    Permanently delete a user from the database

    WARNING: This is a permanent action that cannot be undone!

    Args:
        user_id: The user ID to delete

    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_db_connection()
    try:
        # First remove user from user_roles table
        conn.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))

        # Then remove the user from the users table
        cursor = conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()


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
                COUNT(CASE WHEN (p.status LIKE 'Active%' OR p.status = 'Hospice') AND upa.provider_id IS NULL THEN 1 END) as unassigned_active_patients,
                COUNT(CASE WHEN (p.status = 'Active' OR p.status = 'Hospice') AND p.created_date > date('now', '-30 days') THEN 1 END) as new_patients_30_days
            FROM patients p
            LEFT JOIN patient_assignments upa ON p.patient_id = upa.patient_id
        """).fetchone()

        return {
            "total_onboarding": onboarding_stats["total_onboarding"] or 0,
            "pending_provider_assignment": onboarding_stats[
                "pending_provider_assignment"
            ]
            or 0,
            "pending_initial_contact": onboarding_stats["pending_initial_contact"] or 0,
            "pending_tv_visit": onboarding_stats["pending_tv_visit"] or 0,
            "pending_documentation": onboarding_stats["pending_documentation"] or 0,
            "unassigned_pot": onboarding_stats["unassigned_pot"] or 0,
            "unassigned_active_patients": patient_stats["unassigned_active_patients"]
            or 0,
            "new_patients_30_days": patient_stats["new_patients_30_days"] or 0,
        }
    finally:
        conn.close()


def ensure_audit_log_table(conn: sqlite3.Connection = None):
    close_conn = False
    try:
        if conn is None:
            conn = get_db_connection()
            close_conn = True
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            ("audit_log",),
        ).fetchone()
        if not exists:
            conn.execute(
                """
                CREATE TABLE audit_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT
                )
                """
            )
            conn.commit()
    finally:
        if close_conn and conn:
            conn.close()


def log_audit_action(user_id: int, action: str, details: str = None):
    conn = get_db_connection()
    try:
        ensure_audit_log_table(conn)
        timestamp = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO audit_log(timestamp, user_id, action, details) VALUES(?,?,?,?)",
            (timestamp, user_id, action, details),
        )
        conn.commit()
    finally:
        conn.close()


def reassign_patient(patient_id: int, new_provider_id: int, admin_user_id: int) -> bool:
    conn = get_db_connection()
    try:
        # Get current provider for logging
        current_patient_info = conn.execute(
            "SELECT provider_id FROM patients WHERE patient_id = ?", (patient_id,)
        ).fetchone()
        old_provider_id = (
            current_patient_info["provider_id"] if current_patient_info else None
        )

        cursor = conn.execute(
            "UPDATE patients SET provider_id = ?, updated_date = CURRENT_TIMESTAMP WHERE patient_id = ?",
            (new_provider_id, patient_id),
        )
        conn.commit()

        if cursor.rowcount > 0:
            log_details = f"Patient {patient_id} reassigned from provider {old_provider_id} to {new_provider_id}"
            log_audit_action(admin_user_id, "Patient Reassignment", log_details)
            return True
        return False
    except sqlite3.Error as e:
        print(f"Database error during patient reassignment: {e}")
        return False
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
        patient = conn.execute(
            """
            SELECT * FROM onboarding_patients
            WHERE onboarding_id = ?
        """,
            (onboarding_id,),
        ).fetchone()

        if patient:
            patient_dict = dict(patient)

            # Check if patient exists in patients table and get actual initial_tv_completed status
            if patient_dict.get("patient_id"):
                patients_data = conn.execute(
                    """
                    SELECT initial_tv_completed, initial_tv_completed_date, initial_tv_notes
                    FROM patients
                    WHERE patient_id = ?
                """,
                    (patient_dict["patient_id"],),
                ).fetchone()

                if patients_data:
                    # Override onboarding table values with actual patients table values
                    patient_dict["initial_tv_completed"] = (
                        patients_data["initial_tv_completed"] or False
                    )
                    patient_dict["initial_tv_completed_date"] = patients_data[
                        "initial_tv_completed_date"
                    ]
                    patient_dict["initial_tv_notes"] = patients_data["initial_tv_notes"]

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
                    WHEN NOT op.stage1_complete THEN 'Stage 1: Patient Registration'
                    WHEN NOT op.stage2_complete THEN 'Stage 2: Patient Details'
                    WHEN NOT op.stage3_complete THEN 'Stage 3: Chart Creation'
                    WHEN NOT op.stage4_complete THEN 'Stage 4: Intake Processing'
                    WHEN NOT op.stage5_complete THEN 'Stage 5: Visit Scheduling'
                    ELSE 'Completed'
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
        conn.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
            (user_id, role_id),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # User already has this role
        pass
    finally:
        conn.close()


def remove_user_role(user_id, role_id):
    conn = get_db_connection()
    conn.execute(
        "DELETE FROM user_roles WHERE user_id = ? AND role_id = ?", (user_id, role_id)
    )
    conn.commit()
    conn.close()


def set_primary_role(user_id, role_id):
    conn = get_db_connection()
    # First, set all roles for the user to not be primary
    conn.execute("UPDATE user_roles SET is_primary = 0 WHERE user_id = ?", (user_id,))
    # Then, set the specified role to be primary
    conn.execute(
        "UPDATE user_roles SET is_primary = 1 WHERE user_id = ? AND role_id = ?",
        (user_id, role_id),
    )
    conn.commit()
    conn.close()


def get_user_roles():
    conn = get_db_connection()
    roles = conn.execute("SELECT * FROM roles").fetchall()
    conn.close()
    return roles


def get_users():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return users


def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def get_provider_onboarding_queue(provider_user_id):
    """Get onboarding patients assigned to a specific provider for initial TV visits"""
    conn = get_db_connection()
    try:
        # Get the provider's full name from user_id
        provider_cursor = conn.execute(
            """
            SELECT full_name FROM users WHERE user_id = ?
        """,
            (provider_user_id,),
        )
        provider_result = provider_cursor.fetchone()

        if not provider_result:
            return []

        provider_full_name = provider_result[0]

        # Get onboarding patients assigned to this provider who need initial visit
        # Look for patients where initial_tv_provider matches provider's full name and initial_tv_completed = 0
        onboarding_patients = conn.execute(
            """
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
                op.initial_tv_provider,
                op.visit_type,
                op.billing_code,
                op.duration_minutes
            FROM onboarding_patients op
            WHERE op.initial_tv_provider = ?
            AND (op.initial_tv_completed = 0 OR op.initial_tv_completed IS NULL)
            AND op.patient_status IN ('Active', 'Active-Geri')
            ORDER BY op.tv_date ASC, op.created_date ASC
        """,
            (provider_full_name,),
        ).fetchall()

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
        # IMPORTANT: Use assigned_regional_provider for the permanent assigned_provider_user_id
        # This is the provider who will be the ongoing care provider, not just the initial TV provider
        provider_user_id = None
        regional_provider_selection = form_data.get("assigned_regional_provider")
        if (
            regional_provider_selection
            and regional_provider_selection != "Select Regional Provider..."
            and regional_provider_selection != "No Providers Available"
            and regional_provider_selection != "Regional Provider Assignment Needed"
        ):
            # Get the username from the format "Full Name (username)"
            username = (
                regional_provider_selection.split("(")[-1].replace(")", "").strip()
            )
            provider_cursor = conn.execute(
                "SELECT user_id FROM users WHERE username = ?", (username,)
            )
            provider_result = provider_cursor.fetchone()
            if provider_result:
                provider_user_id = provider_result[0]

        # Extract coordinator user_id from the selection format "Full Name (username)"
        coordinator_user_id = None
        if (
            form_data.get("assigned_coordinator")
            and form_data["assigned_coordinator"] != "Select Coordinator..."
        ):
            # Get the username from the format "Full Name (username)"
            username = (
                form_data["assigned_coordinator"]
                .split("(")[-1]
                .replace(")", "")
                .strip()
            )
            coordinator_cursor = conn.execute(
                "SELECT user_id FROM users WHERE username = ?", (username,)
            )
            coordinator_result = coordinator_cursor.fetchone()
            if coordinator_result:
                coordinator_user_id = coordinator_result[0]

        # Convert time object to string if needed
        tv_time = form_data.get("tv_time")
        if tv_time and hasattr(tv_time, "strftime"):
            tv_time = tv_time.strftime("%H:%M:%S")

        # Convert date object to string if needed
        tv_date = form_data.get("tv_date")
        if tv_date and hasattr(tv_date, "strftime"):
            tv_date = tv_date.strftime("%Y-%m-%d")

        # Extract provider name for initial_tv_provider field
        initial_tv_provider = None
        if (
            form_data.get("assigned_provider")
            and form_data["assigned_provider"] != "Select Provider..."
        ):
            # Extract the full name from the format "Full Name (username)"
            initial_tv_provider = form_data["assigned_provider"].split("(")[0].strip()

        # Update onboarding patient record with partial progress
        conn.execute(
            """
            UPDATE onboarding_patients
            SET tv_date = ?,
                tv_time = ?,
                assigned_provider_user_id = ?,
                assigned_coordinator_user_id = ?,
                initial_tv_provider = ?,
                visit_type = ?,
                billing_code = ?,
                duration_minutes = ?,
                updated_date = CURRENT_TIMESTAMP
            WHERE onboarding_id = ?
        """,
            (
                tv_date,
                tv_time,
                provider_user_id,
                coordinator_user_id,
                initial_tv_provider,
                form_data.get("visit_type", "Home Visit"),
                form_data.get("billing_code", "99345"),
                form_data.get("duration_minutes", 45),
                onboarding_id,
            ),
        )

        # Update checkbox fields if provided
        checkbox_data = {}
        if "tv_scheduled" in form_data:
            checkbox_data["tv_scheduled"] = form_data["tv_scheduled"]
        if "patient_notified" in form_data:
            checkbox_data["patient_notified"] = form_data["patient_notified"]
        if "initial_tv_completed" in form_data:
            checkbox_data["initial_tv_completed"] = form_data["initial_tv_completed"]

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
            patient_info = conn.execute(
                """
                SELECT first_name, last_name, date_of_birth, patient_id, phone_primary, email, address_street, address_city, address_state, address_zip, insurance_provider, policy_number, emergency_contact_name, emergency_contact_phone
                FROM onboarding_patients
                WHERE onboarding_id = ?
            """,
                (onboarding_id,),
            ).fetchone()

            if patient_info:
                # Generate text-based patient_id for consistency
                text_patient_id = generate_patient_id(
                    patient_info["first_name"] or "",
                    patient_info["last_name"] or "",
                    patient_info["date_of_birth"] or "",
                )

                # Only update existing patient records - patient creation is handled by insert_patient_from_onboarding
                # Check if patient already exists in patients table
                existing_patient = conn.execute(
                    """
                    SELECT patient_id FROM patients WHERE patient_id = ?
                """,
                    (text_patient_id,),
                ).fetchone()

                if existing_patient:
                    # Patient exists - only update the initial_tv_provider and updated_date
                    # Preserve all other existing patient data
                    conn.execute(
                        """
                        UPDATE patients
                        SET initial_tv_provider = ?, updated_date = datetime('now')
                        WHERE patient_id = ?
                    """,
                        (initial_tv_provider, text_patient_id),
                    )

                    # Update patient assignment in patient_assignments table
                    # Check if assignment already exists for this patient
                    existing = conn.execute(
                        """
                        SELECT assignment_id FROM patient_assignments
                        WHERE patient_id = ? AND status = 'active'
                    """,
                        (text_patient_id,),
                    ).fetchone()

                    if existing:
                        # Update existing assignment - match actual table schema
                        conn.execute(
                            """
                            UPDATE patient_assignments
                            SET provider_id = ?, coordinator_id = ?, status = 'active'
                            WHERE assignment_id = ?
                        """,
                            (
                                provider_user_id,
                                coordinator_user_id,
                                existing["assignment_id"],
                            ),
                        )

                    # Update assignments in patient_panel table
                    if provider_user_id:
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO patient_panel (
                                patient_id, provider_id, status, created_date, updated_date
                            ) VALUES (?, ?, 'active', datetime('now'), datetime('now'))
                        """,
                            (text_patient_id, provider_user_id),
                        )

                    if coordinator_user_id:
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO patient_panel (
                                patient_id, coordinator_id, status, created_date, updated_date
                            ) VALUES (?, ?, 'active', datetime('now'), datetime('now'))
                        """,
                            (text_patient_id, coordinator_user_id),
                        )
                else:
                    # Patient doesn't exist yet - this is expected for revisions before Stage 5 completion
                    # Just update the onboarding record with provider/coordinator assignments
                    # Patient creation will be handled by insert_patient_from_onboarding during Stage 5 completion
                    pass

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


def update_onboarding_stage5_completion(
    onboarding_id,
    tv_date,
    tv_time,
    assigned_initial_tv_provider,
    assigned_regional_provider,
    assigned_coordinator,
):
    """Update Stage 5 completion with provider assignment and TV scheduling details"""
    conn = get_db_connection()
    try:
        # Extract initial TV provider user_id from the selection format "Full Name (username)"
        initial_tv_provider_user_id = None
        if (
            assigned_initial_tv_provider
            and assigned_initial_tv_provider != "Select Provider..."
        ):
            # Get the username from the format "Full Name (username)"
            username = (
                assigned_initial_tv_provider.split("(")[-1].replace(")", "").strip()
            )
            provider_cursor = conn.execute(
                "SELECT user_id FROM users WHERE username = ?", (username,)
            )
            provider_result = provider_cursor.fetchone()
            if provider_result:
                initial_tv_provider_user_id = provider_result[0]

        # Extract regional provider user_id from the selection format "Full Name (username)"
        regional_provider_user_id = None
        if (
            assigned_regional_provider
            and assigned_regional_provider != "Select Regional Provider..."
        ):
            # Get the username from the format "Full Name (username)"
            username = (
                assigned_regional_provider.split("(")[-1].replace(")", "").strip()
            )
            provider_cursor = conn.execute(
                "SELECT user_id FROM users WHERE username = ?", (username,)
            )
            provider_result = provider_cursor.fetchone()
            if provider_result:
                regional_provider_user_id = provider_result[0]

        # Extract coordinator user_id from the selection format "Full Name (username)"
        coordinator_user_id = None
        if assigned_coordinator and assigned_coordinator != "Select Coordinator...":
            # Get the username from the format "Full Name (username)"
            username = assigned_coordinator.split("(")[-1].replace(")", "").strip()
            coordinator_cursor = conn.execute(
                "SELECT user_id FROM users WHERE username = ?", (username,)
            )
            coordinator_result = coordinator_cursor.fetchone()
            if coordinator_result:
                coordinator_user_id = coordinator_result[0]

        # Convert time and date objects to strings if needed
        if tv_time and hasattr(tv_time, "strftime"):
            tv_time = tv_time.strftime("%H:%M:%S")
        if tv_date and hasattr(tv_date, "strftime"):
            tv_date = tv_date.strftime("%Y-%m-%d")

        # Extract provider name for initial_tv_provider field
        initial_tv_provider = None
        if (
            assigned_initial_tv_provider
            and assigned_initial_tv_provider != "Select Provider..."
        ):
            # Extract the full name from the format "Full Name (username)"
            initial_tv_provider = assigned_initial_tv_provider.split("(")[0].strip()

        # Get patient_id from onboarding record to create patient assignment
        patient_cursor = conn.execute(
            "SELECT patient_id FROM onboarding_patients WHERE onboarding_id = ?",
            (onboarding_id,),
        )
        patient_result = patient_cursor.fetchone()
        patient_id = patient_result[0] if patient_result else None

        # Update onboarding patient record - use regional provider for assigned_provider_user_id
        conn.execute(
            """
            UPDATE onboarding_patients
            SET tv_date = ?,
                tv_time = ?,
                assigned_provider_user_id = ?,
                assigned_coordinator_user_id = ?,
                initial_tv_provider = ?,
                updated_date = CURRENT_TIMESTAMP
            WHERE onboarding_id = ?
        """,
            (
                tv_date,
                tv_time,
                regional_provider_user_id,
                coordinator_user_id,
                initial_tv_provider,
                onboarding_id,
            ),
        )

        # Create or update patient assignment record if we have a patient_id and assignments
        if patient_id and (regional_provider_user_id or coordinator_user_id):
            # Check if assignment already exists for this patient
            # Note: patient_assignments table doesn't have assignment_type column, so we check by patient_id and status
            existing = conn.execute(
                """
                SELECT assignment_id FROM patient_assignments
                WHERE patient_id = ? AND status = 'active'
            """,
                (patient_id,),
            ).fetchone()

            if existing:
                # Update existing assignment
                conn.execute(
                    """
                    UPDATE patient_assignments
                    SET provider_id = ?, coordinator_id = ?, status = 'active'
                    WHERE assignment_id = ?
                """,
                    (
                        regional_provider_user_id,
                        coordinator_user_id,
                        existing["assignment_id"],
                    ),
                )
            else:
                # Create new assignment - match actual table schema
                conn.execute(
                    """
                    INSERT INTO patient_assignments (
                        patient_id, provider_id, coordinator_id, status
                    ) VALUES (?, ?, ?, 'active')
                """,
                    (patient_id, regional_provider_user_id, coordinator_user_id),
                )

        conn.commit()
        return True

    except Exception as e:
        print(f"Error updating Stage 5 completion: {e}")
        return False
    finally:
        conn.close()


def get_tasks_by_user(user_id):
    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,)).fetchall()
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
        role = conn.execute(
            "SELECT role_id FROM roles WHERE role_name = ?", (role_name,)
        ).fetchone()
        if role:
            role_id = role["role_id"]
            cursor = conn.execute(
                "INSERT INTO users (username, password, first_name, last_name, email, full_name, status, hire_date) VALUES (?, ?, ?, ?, ?, ?, 'active', CURRENT_DATE)",
                (
                    username,
                    hashed_password,
                    first_name,
                    last_name,
                    email,
                    f"{first_name} {last_name}",
                ),
            )
            user_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, role_id),
            )
            conn.commit()
            return user_id
        return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()


def add_user_with_hashed_password(
    username, hashed_password, first_name, last_name, email, role_name
):
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
        role = conn.execute(
            "SELECT role_id FROM roles WHERE role_name = ?", (role_name,)
        ).fetchone()
        if role:
            role_id = role["role_id"]
            cursor = conn.execute(
                "INSERT INTO users (username, password, first_name, last_name, email, full_name, status, hire_date) VALUES (?, ?, ?, ?, ?, ?, 'active', CURRENT_DATE)",
                (
                    username,
                    hashed_password,
                    first_name,
                    last_name,
                    email,
                    f"{first_name} {last_name}",
                ),
            )
            user_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, role_id),
            )
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
    cursor.execute(
        """
        SELECT
            upa.patient_id,
            p.first_name || ' ' || p.last_name AS patient_name,
            upa.provider_id as user_id,
            p.address_street,
            p.address_city,
            p.address_state,
            p.address_zip,
            p.phone_primary,
            p.status AS patient_status
        FROM
            patient_assignments upa
        JOIN
            patients p ON upa.patient_id = p.patient_id
        WHERE
            upa.provider_id = ?
    """,
        (user_id,),
    )
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
    cursor.execute(
        "SELECT plan_details FROM care_plans WHERE patient_name = ?", (patient_name,)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else ""


def update_care_plan(patient_name, plan_details, updated_by):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO care_plans (patient_name, plan_details, updated_by, last_updated) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
        (patient_name, plan_details, updated_by),
    )
    conn.commit()
    conn.close()


def get_provider_performance_metrics(start_date: datetime, end_date: datetime):
    conn = get_db_connection()
    try:
        all_task_tables = get_monthly_task_tables(prefix="provider_tasks_", conn=conn)

        # Filter tables that fall within the date range
        tables_to_query = []
        for table_name in all_task_tables:
            try:
                parts = table_name.split("_")
                year = int(parts[2])
                month = int(parts[3])

                table_date = datetime(year, month, 1).date()

                # Check if the table's month/year range overlaps with the query date range
                # A table is relevant if its month starts before or on end_date, and ends after or on start_date
                table_month_end = datetime(
                    year, month, calendar.monthrange(year, month)[1]
                ).date()

                if (
                    table_date <= end_date.date()
                    and table_month_end >= start_date.date()
                ):
                    tables_to_query.append(table_name)
            except Exception as e:
                print(f"Skipping malformed table name {table_name}: {e}")
                continue

        if not tables_to_query:
            return []  # No relevant tables found

        # Build UNION ALL query for all relevant tables
        union_queries = []
        for table_name in tables_to_query:
            union_queries.append(f"""
                SELECT
                    provider_id,
                    patient_id,
                    task_date,
                    task_type
                FROM {table_name}
                WHERE task_date BETWEEN ? AND ?
            """)

        full_query = " UNION ALL ".join(union_queries)

        query = f"""
            SELECT
                u.full_name,
                COUNT(DISTINCT combined_tasks.patient_id) AS total_patients_seen,
                GROUP_CONCAT(combined_tasks.task_type || ':' || combined_tasks.patient_id) AS visit_type_breakdown_raw
            FROM users u
            JOIN (
                {full_query}
            ) AS combined_tasks ON u.user_id = combined_tasks.provider_id
            JOIN user_roles ur ON u.user_id = ur.user_id
            JOIN roles r ON ur.role_id = r.role_id
            WHERE r.role_id IN (33, 38)  -- CP and CPM roles
            GROUP BY u.full_name;
        """

        # Prepare parameters for the BETWEEN clause (start_date and end_date for each unioned query)
        params = []
        for _ in tables_to_query:
            params.extend(
                [start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")]
            )

        metrics = conn.execute(query, params).fetchall()

        # Process visit_type_breakdown_raw to get counts per type
        processed_metrics = []
        for row in metrics:
            row_dict = dict(row)
            visit_type_counts = {}
            if row_dict["visit_type_breakdown_raw"]:
                # Split the raw string into individual "task_type:patient_id" entries
                entries = row_dict["visit_type_breakdown_raw"].split(",")

                # Use a set to count unique patients per task type
                unique_patients_per_type = {}
                for entry in entries:
                    try:
                        task_type, patient_id = entry.split(":", 1)
                        if task_type not in unique_patients_per_type:
                            unique_patients_per_type[task_type] = set()
                        unique_patients_per_type[task_type].add(patient_id)
                    except ValueError:
                        # Handle cases where entry might not split correctly
                        continue

                # Count unique patients for each task type
                for task_type, patient_ids in unique_patients_per_type.items():
                    visit_type_counts[task_type] = len(patient_ids)

            row_dict["visit_type_breakdown"] = visit_type_counts
            del row_dict["visit_type_breakdown_raw"]  # Remove raw data
            processed_metrics.append(row_dict)

        return processed_metrics
    finally:
        conn.close()


def get_tasks_billing_codes():
    conn = get_db_connection()
    try:
        codes = conn.execute(
            "SELECT code, description FROM task_billing_codes WHERE is_active = 1"
        ).fetchall()
        return [dict(row) for row in codes]
    finally:
        conn.close()


def get_tasks_billing_codes_by_service_type(service_type):
    """Get task billing codes filtered by service type"""
    conn = get_db_connection()
    try:
        codes = conn.execute(
            """
            SELECT code_id, task_description, billing_code, description
            FROM task_billing_codes
            WHERE service_type = ? AND is_active = 1
            ORDER BY task_description
        """,
            (service_type,),
        ).fetchall()
        return [dict(row) for row in codes]
    finally:
        conn.close()


def get_daily_tasks_for_coordinator():
    conn = get_db_connection()
    try:
        # Get all task descriptions for coordinator tasks from coordinator_task_definitions table
        tasks = conn.execute(
            "SELECT task_description FROM coordinator_task_definitions WHERE task_description IS NOT NULL GROUP BY task_description"
        ).fetchall()
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
        cursor = conn.execute(
            """
            SELECT DISTINCT
                dpc.county,
                dpc.state,
                dpc.patient_count
            FROM dashboard_provider_county_map dpc
            WHERE dpc.provider_id = ? AND dpc.county IS NOT NULL AND dpc.county != ''
            ORDER BY dpc.county
        """,
            (provider_id,),
        )
        counties = cursor.fetchall()
        return [(c[0], f"{c[0]}, {c[1]} [{c[2]}]") for c in counties]
    finally:
        conn.close()


def get_provider_zip_codes(provider_id):
    """Get zip codes for a provider using the new dashboard mapping table"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            SELECT DISTINCT
                dpz.zip_code,
                dpz.city,
                dpz.state,
                dpz.patient_count
            FROM dashboard_provider_zip_map dpz
            WHERE dpz.provider_id = ? AND dpz.zip_code IS NOT NULL AND dpz.zip_code != ''
            ORDER BY dpz.zip_code
        """,
            (provider_id,),
        )
        zip_codes = cursor.fetchall()
        return [(z[0], f"{z[0]} - {z[1]}, {z[2]} [{z[3]}]") for z in zip_codes]
    finally:
        conn.close()


def get_patient_counties(patient_id):
    """Get counties for a patient using the new dashboard mapping table"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            SELECT DISTINCT
                dpc.county,
                dpc.state
            FROM dashboard_patient_county_map dpc
            WHERE dpc.patient_id = ? AND dpc.county IS NOT NULL AND dpc.county != ''
            ORDER BY dpc.county
        """,
            (patient_id,),
        )
        counties = cursor.fetchall()
        return [(c[0], f"{c[0]}, {c[1]}") for c in counties]
    finally:
        conn.close()


def get_patient_zip_codes(patient_id):
    """Get zip codes for a patient using the new dashboard mapping table"""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            SELECT DISTINCT
                dpz.zip_code,
                dpz.city,
                dpz.state
            FROM dashboard_patient_zip_map dpz
            WHERE dpz.patient_id = ? AND dpz.zip_code IS NOT NULL AND dpz.zip_code != ''
            ORDER BY dpz.zip_code
        """,
            (patient_id,),
        )
        zip_codes = cursor.fetchall()
        return [(z[0], f"{z[0]} - {z[1]}, {z[2]}") for z in zip_codes]
    finally:
        conn.close()


def get_billing_codes(location_type=None, patient_type=None):
    """Return billing code rows filtered by location_type and patient_type.
    Each row is returned as a dict with keys matching the task_billing_codes columns.

    Note: service_type filtering removed - patient_type is sufficient for billing lookups.
    """
    conn = get_db_connection()
    try:
        # Check if is_default column exists in the table
        cursor = conn.execute("PRAGMA table_info(task_billing_codes)")
        columns = [column[1] for column in cursor.fetchall()]

        # Build query based on whether is_default column exists
        # Always filter by is_active = 1 to only show enabled billing codes
        if "is_default" in columns:
            query = "SELECT code_id, task_description, service_type, location_type, patient_type, min_minutes, max_minutes, billing_code, description, rate, COALESCE(is_default, 0) as is_default FROM task_billing_codes WHERE is_active = 1"
        else:
            query = "SELECT code_id, task_description, service_type, location_type, patient_type, min_minutes, max_minutes, billing_code, description, rate, 0 as is_default FROM task_billing_codes WHERE is_active = 1"

        conditions = []
        params = []
        if location_type:
            conditions.append("location_type = ?")
            params.append(location_type)
        if patient_type:
            conditions.append("patient_type = ?")
            params.append(patient_type)
        if conditions:
            query += " AND " + " AND ".join(conditions)
        query += " ORDER BY min_minutes DESC, max_minutes DESC"
        rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_billing_code_for_location_patient_type(conn, location_type: str, patient_type: str) -> str:
    """
    Find the appropriate billing_code for a given location_type and patient_type combination.

    Args:
        conn: Database connection (must be passed in to use existing connection)
        location_type: Home, Office, or Telehealth
        patient_type: Follow Up, New, Acute, Cognitive, TCM-7, or TCM-14

    Returns:
        The billing_code (e.g., '99350', '99214') or None if not found
    """
    try:
        query = """
        SELECT billing_code FROM task_billing_codes
        WHERE location_type = ? AND patient_type = ? AND is_active = 1
        LIMIT 1
        """
        row = conn.execute(query, (location_type, patient_type)).fetchone()
        return row['billing_code'] if row else None
    except Exception as e:
        print(f"Error finding billing code for {location_type}/{patient_type}: {e}")
        return None


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
                conn.execute(
                    "UPDATE task_billing_codes SET is_default = 1 WHERE billing_code = ?",
                    (code,),
                )

        conn.commit()
        return True
    except Exception as e:
        print(f"Error setting default billing codes: {e}")
        return False
    finally:
        conn.close()


def sync_patient_last_visit_all_tables(conn, patient_id, last_visit_date, service_type):
    """
    Synchronize last_visit_date and service_type across ALL patient-related tables.

    This ensures consistency when a new visit is recorded:
    - patients table (canonical source)
    - patient_panel table (denormalized for dashboards)
    - hhc_patients_export table (for HHC export views)

    Args:
        conn: Database connection
        patient_id: Patient ID to update
        last_visit_date: Date of the last visit
        service_type: Type of service from task_description
    """
    try:
        # 1. Update patients table (canonical source)
        conn.execute(
            """
            UPDATE patients
            SET last_visit_date = ?,
                service_type = ?
            WHERE patient_id = ?
        """,
            (last_visit_date, service_type, patient_id),
        )

        # 2. Update patient_panel table (denormalized for dashboard display)
        conn.execute(
            """
            UPDATE patient_panel
            SET last_visit_date = ?,
                last_visit_service_type = ?
            WHERE patient_id = ?
        """,
            (last_visit_date, service_type, patient_id),
        )

        # 3. Update hhc_patients_export table if it exists (for HHC export functionality)
        # Note: Since hhc_patients_export is materialized from hhc_export_view which queries
        # from the patients table, updates to patients table automatically propagate
        # The HHC export view will reflect the latest visit data on next query
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='hhc_patients_export'"
            )
            if cursor.fetchone():
                # Table exists - trigger a refresh by recreating from view
                # This ensures HHC export reflects the latest patient data
                conn.execute("DROP TABLE IF EXISTS hhc_patients_export")
                conn.execute(
                    """
                    CREATE TABLE hhc_patients_export AS
                    SELECT * FROM hhc_export_view
                    """
                )
                print(f"Refreshed hhc_patients_export for patient {patient_id}")
        except Exception as e:
            # HHC export table might not exist yet, which is OK
            print(f"Note: hhc_patients_export refresh skipped: {e}")

        print(
            f"Synced last visit ({last_visit_date}, service: {service_type}) across all patient tables for {patient_id}"
        )
        return True

    except Exception as e:
        print(f"Error syncing patient visit data across tables: {e}")
        return False


def save_daily_task(
    provider_id, patient_id, task_date, task_description, notes, billing_code=None, icd_codes=None,
    location_type=None, patient_type=None
):
    """Save a daily task for a provider to the provider_tasks table.
    If `billing_code` is provided, use it to look up duration and description. Otherwise fallback to lookup by task_description.
    `icd_codes` is an optional string of ICD-10 codes for billing purposes.
    `location_type` is the type of visit location (Home, Telehealth, Office).
    `patient_type` is the type of patient visit (New, Follow Up, Acute, Cognitive, TCM-7, TCM-14).
    """
    conn = get_db_connection()
    try:
        billing_data = None
        if billing_code:
            billing_cursor = conn.execute(
                """
                SELECT min_minutes, billing_code, rate, description
                FROM task_billing_codes
                WHERE billing_code = ? AND is_active = 1
                LIMIT 1
            """,
                (billing_code,),
            )
            billing_data = billing_cursor.fetchone()

        if not billing_data:
            # Fallback to previous behavior: lookup by task_description
            billing_cursor = conn.execute(
                """
                SELECT min_minutes, billing_code, rate, description
                FROM task_billing_codes
                WHERE task_description = ? AND is_active = 1
                LIMIT 1
            """,
                (task_description,),
            )
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

        # Extract year and month from task_date to ensure we insert into the correct monthly table
        try:
            task_dt = pd.to_datetime(task_date)
            task_year = task_dt.year
            task_month = task_dt.month
        except Exception:
            # Fallback to current date if task_date is invalid
            now = pd.Timestamp.now()
            task_year = now.year
            task_month = now.month

        # Get patient name for denormalization
        patient_name = ""
        try:
            p_cursor = conn.execute(
                "SELECT first_name, last_name FROM patients WHERE patient_id = ?",
                (pid,),
            )
            p_row = p_cursor.fetchone()
            if p_row:
                fn = p_row[0] if p_row[0] else ""
                ln = p_row[1] if p_row[1] else ""
                patient_name = f"{fn} {ln}".strip()
        except Exception as e:
            print(f"Error fetching patient name: {e}")

        # Strip billing code pattern from task_description before storing
        import re
        clean_task_description = re.sub(r'\s*-\s*\d{5}\s*$', '', task_description).strip()

        # Get provider name for denormalization
        provider_name = ""
        try:
            provider_name_result = conn.execute(
                "SELECT full_name FROM users WHERE user_id = ?", (provider_id,)
            ).fetchone()
            provider_name = provider_name_result[0] if provider_name_result else ""
        except Exception as e:
            print(f"Error fetching provider name: {e}")

        # Insert into monthly provider_tasks table dynamically
        table_name = ensure_monthly_provider_tasks_table(
            year=task_year, month=task_month, conn=conn
        )
        cursor = conn.execute(
            f"""
            INSERT INTO {table_name}
            (provider_id, provider_name, patient_id, patient_name, task_date, notes, minutes_of_service, task_description, billing_code, billing_code_description, icd_codes, location_type, patient_type, source_system, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DATA_ENTRY', CURRENT_TIMESTAMP)
        """,
            (
                provider_id,
                provider_name,
                pid,
                patient_name,
                task_date,
                notes,
                duration_minutes,
                clean_task_description,
                billing_code_val,
                billing_code_description,
                icd_codes,
                location_type,
                patient_type,
            ),
        )

        # Get the newly created provider_task_id
        new_provider_task_id = cursor.lastrowid

        # Also create billing status record for Medicare/insurance workflow tracking (if billable)
        if billing_code_val and billing_code_val != "Not_Billable":
            try:
                # Calculate billing week
                task_dt_obj = pd.to_datetime(task_date)
                billing_week = task_dt_obj.isocalendar()[1]
                week_start = task_dt_obj - pd.Timedelta(days=task_dt_obj.weekday())
                week_end = week_start + pd.Timedelta(days=6)

                conn.execute(
                    """
                    INSERT INTO provider_task_billing_status (
                        provider_task_id, provider_id, provider_name, patient_id, patient_name, task_date,
                        billing_week, week_start_date, week_end_date, task_description,
                        minutes_of_service, billing_code, billing_code_description, icd_codes,
                        billing_status, is_billed, is_invoiced, is_claim_submitted,
                        is_insurance_processed, is_approved_to_pay, is_paid, is_carried_over
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        new_provider_task_id,
                        provider_id,
                        provider_name,
                        pid,
                        patient_name,
                        task_date,
                        billing_week,
                        week_start.strftime("%Y-%m-%d"),
                        week_end.strftime("%Y-%m-%d"),
                        task_description,
                        duration_minutes,
                        billing_code_val,
                        billing_code_description,
                        icd_codes,
                        "Pending",
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                    ),
                )
            except Exception as e:
                print(f"Warning: Could not create billing status record: {e}")
                # Don't fail the whole task if billing status creation fails

        
        # If onboarding-specific task, handle onboarding workflow (legacy)
        if task_description == "PCP-Visit Telehealth (TE) (NEW pt)":
            onboarding_cursor = conn.execute(
                """
                SELECT onboarding_id
                FROM onboarding_patients
                WHERE patient_id = ? AND stage5_complete = 1 AND completed_date IS NULL
            """,
                (pid,),
            )
            onboarding_match = onboarding_cursor.fetchone()
            if onboarding_match:
                conn.execute(
                    """
                    UPDATE onboarding_patients
                    SET initial_tv_completed = 1, initial_tv_completed_date = ?
                    WHERE onboarding_id = ?
                """,
                    (task_date, onboarding_match[0]),
                )

            # Get provider name for initial TV provider field
            provider_name = ""
            try:
                provider_cursor = conn.execute(
                    """
                    SELECT full_name FROM users WHERE user_id = ?
                """,
                    (provider_id,),
                )
                provider_result = provider_cursor.fetchone()
                if provider_result:
                    provider_name = provider_result[0]
            except:
                provider_name = f"Provider ID {provider_id}"

            # Sync last visit data across ALL patient tables (patients, patient_panel, hhc_patients_export)
            sync_patient_last_visit_all_tables(conn, pid, task_date, task_description)

            # Also update initial TV specific fields in patient_panel
            conn.execute(
                """
                UPDATE patient_panel
                SET initial_tv_completed = 1,
                    initial_tv_completed_date = ?,
                    initial_tv_notes = ?,
                    initial_tv_provider = ?
                WHERE patient_id = ?
            """,
                (task_date, notes, provider_name, pid),
            )

            # Update initial TV fields in patients table
            conn.execute(
                """
                UPDATE patients
                SET initial_tv_completed_date = ?,
                    initial_tv_notes = ?,
                    initial_tv_provider = ?
                WHERE patient_id = ?
            """,
                (task_date, notes, provider_name, pid),
            )
        else:
            # For non-initial TV tasks, sync last_visit_date and service_type across all tables
            sync_patient_last_visit_all_tables(conn, pid, task_date, task_description)

        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving task: {e}")
        return False
    finally:
        conn.close()


def save_coordinator_task(
    coordinator_id, patient_id, task_date, task_description, duration_minutes, notes
):
    """Save a daily task for a coordinator to the coordinator_tasks table"""
    conn = get_db_connection()
    try:
        # Normalize patient_id to the canonical string format before inserting
        pid = normalize_patient_id(patient_id, conn=conn)

        # Extract year and month from task_date to ensure we insert into the correct monthly table
        try:
            task_dt = pd.to_datetime(task_date)
            task_year = task_dt.year
            task_month = task_dt.month
        except Exception:
            # Fallback to current date if task_date is invalid
            now = pd.Timestamp.now()
            task_year = now.year
            task_month = now.month

        # Insert into monthly coordinator_tasks table dynamically
        table_name = ensure_monthly_coordinator_tasks_table(
            year=task_year, month=task_month, conn=conn
        )

        # Generate PST timestamp for unique entry identification
        now = pd.Timestamp.now()
        now_pst = now.tz_localize('UTC').tz_convert('America/Los_Angeles')

        conn.execute(
            f"""
            INSERT INTO {table_name}
            (patient_id, coordinator_id, task_date, duration_minutes, task_type, notes, source_system, imported_at, created_at_pst)
            VALUES (?, ?, ?, ?, ?, ?, 'DATA_ENTRY', CURRENT_TIMESTAMP, ?)
        """,
            (pid, coordinator_id, task_date, duration_minutes, task_description, notes, now_pst.strftime("%Y-%m-%d %H:%M:%S")),
        )

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
    """Update the status of a patient (without history tracking - use update_patient_status_with_history for tracking)"""
    conn = get_db_connection()
    try:
        # Update status in patients table
        conn.execute(
            """
            UPDATE patients
            SET status = ?, updated_date = CURRENT_TIMESTAMP
            WHERE patient_id = ?
        """,
            (status, patient_id),
        )
        # Also update status in patient_panel table for consistency
        conn.execute(
            """
            UPDATE patient_panel
            SET status = ?, updated_date = CURRENT_TIMESTAMP
            WHERE patient_id = ?
        """,
            (status, patient_id),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating patient status: {e}")
        return False
    finally:
        conn.close()


def update_patient_status_with_history(patient_id, new_status, user_id=None, change_reason=None, source_system="MANUAL"):
    """
    Update patient status and record the change in history.

    This is the RECOMMENDED way to change patient status as it maintains
    a complete audit trail of all status changes over time.

    Args:
        patient_id: The patient ID to update
        new_status: The new status value
        user_id: Optional ID of the user making the change
        change_reason: Optional reason for the status change
        source_system: Source system (e.g., 'ZMO_MODULE', 'ADMIN_DASHBOARD', 'CC_DASHBOARD', 'MANUAL')

    Returns:
        dict: {'success': bool, 'old_status': str, 'new_status': str, 'history_id': int or None}
    """
    conn = get_db_connection()
    try:
        # Get current status before updating
        current = conn.execute(
            "SELECT status FROM patients WHERE patient_id = ?",
            (patient_id,)
        ).fetchone()

        if not current:
            return {'success': False, 'error': 'Patient not found'}

        old_status = current[0]

        # If status isn't actually changing, just return success
        if old_status == new_status:
            return {
                'success': True,
                'old_status': old_status,
                'new_status': new_status,
                'message': 'Status unchanged, no history recorded'
            }

        # Update the patient status in patients table
        conn.execute(
            """
            UPDATE patients
            SET status = ?, updated_date = CURRENT_TIMESTAMP
            WHERE patient_id = ?
        """,
            (new_status, patient_id),
        )

        # Also update status in patient_panel table for consistency
        conn.execute(
            """
            UPDATE patient_panel
            SET status = ?, updated_date = CURRENT_TIMESTAMP
            WHERE patient_id = ?
        """,
            (new_status, patient_id),
        )

        # Record the change in history
        cursor = conn.execute(
            """
            INSERT INTO patient_status_history
            (patient_id, old_status, new_status, changed_by, change_reason, source_system)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (patient_id, old_status, new_status, user_id, change_reason, source_system)
        )

        history_id = cursor.lastrowid
        conn.commit()

        return {
            'success': True,
            'old_status': old_status,
            'new_status': new_status,
            'history_id': history_id
        }

    except Exception as e:
        conn.rollback()
        print(f"Error updating patient status with history: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()


def get_patient_status_history(patient_id):
    """
    Get the status change history for a patient.

    Args:
        patient_id: The patient ID to get history for

    Returns:
        list: Dicts with keys: history_id, old_status, new_status, changed_at, changed_by, change_reason, source_system, changer_name
    """
    conn = get_db_connection()
    try:
        query = """
        SELECT
            h.history_id,
            h.old_status,
            h.new_status,
            h.changed_at,
            h.changed_by,
            h.change_reason,
            h.source_system,
            u.full_name as changer_name
        FROM patient_status_history h
        LEFT JOIN users u ON h.changed_by = u.user_id
        WHERE h.patient_id = ?
        ORDER BY h.changed_at DESC
        """
        rows = conn.execute(query, (patient_id,)).fetchall()
        return [dict(row) for row in rows]
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
                WHEN op.stage4_complete = 1 THEN 'Stage 5: Visit Scheduling'
                WHEN op.stage3_complete = 1 THEN 'Stage 4: Intake Processing'
                WHEN op.stage2_complete = 1 THEN 'Stage 3: Chart Creation'
                WHEN op.stage1_complete = 1 THEN 'Stage 2: Patient Details'
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
            -- Stage 1 blockers (Patient Registration: Basic Info + Insurance + Eligibility)
            op.first_name,
            op.last_name,
            op.date_of_birth,
            op.insurance_provider,
            op.policy_number,
            op.eligibility_verified,
            -- Stage 2 blockers (Patient Details: Contact + Address)
            op.phone_primary,
            op.address_street,
            op.address_city,
            op.address_state,
            op.address_zip,
            -- Stage 3 blockers (Chart Creation)
            op.emed_chart_created,
            op.facility_confirmed,
            op.chart_id,
            -- Stage 4 blockers (Intake Processing)
            op.intake_call_completed,
            op.medical_records_requested,
            -- Stage 5 blockers (Visit Scheduling)
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
        cursor = conn.execute(
            """
            INSERT INTO onboarding_patients (
                first_name, last_name, date_of_birth,
                phone_primary, email, gender, emergency_contact_name, emergency_contact_phone,
                address_street, address_city, address_state, address_zip,
                insurance_provider, policy_number, group_number,
                referral_source, referring_provider, referral_date,
                patient_status, facility_assignment, assigned_pot_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                patient_data["first_name"],
                patient_data["last_name"],
                patient_data["date_of_birth"],
                patient_data.get("phone_primary"),
                patient_data.get("email"),
                patient_data.get("gender"),
                patient_data.get("emergency_contact_name"),
                patient_data.get("emergency_contact_phone"),
                patient_data.get("address_street"),
                patient_data.get("address_city"),
                patient_data.get("address_state"),
                patient_data.get("address_zip"),
                patient_data.get("insurance_provider"),
                patient_data.get("policy_number"),
                patient_data.get("group_number"),
                patient_data.get("referral_source"),
                patient_data.get("referring_provider"),
                patient_data.get("referral_date"),
                patient_data.get("patient_status", "Active"),
                patient_data.get("facility_assignment"),
                pot_user_id,
            ),
        )

        onboarding_id = cursor.lastrowid

        # Create initial tasks for all workflow steps
        workflow_steps = conn.execute("""
            SELECT step_id, step_order, task_name FROM workflow_steps
            WHERE template_id = 14 ORDER BY step_order
        """).fetchall()

        for step in workflow_steps:
            stage = (
                (step["step_order"] - 1) // 3
            ) + 1  # Group steps into stages (3 steps per stage roughly)
            if step["step_order"] > 15:  # Handle stage 5 which has more steps
                stage = 5

            conn.execute(
                """
                INSERT INTO onboarding_tasks (
                    onboarding_id, workflow_step_id, task_name, task_stage,
                    task_order, status, created_date, updated_date
                ) VALUES (?, ?, ?, ?, ?, 'Pending', datetime('now'), datetime('now'))
            """,
                (
                    onboarding_id,
                    step["step_id"],
                    step["task_name"],
                    stage,
                    step["step_order"],
                ),
            )

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
        patient = conn.execute(
            """
            SELECT * FROM onboarding_patients WHERE onboarding_id = ?
        """,
            (onboarding_id,),
        ).fetchone()

        if not patient:
            return None

        patient_dict = dict(patient)

        # Get tasks for this patient
        tasks = conn.execute(
            """
            SELECT ot.*, ws.deliverable
            FROM onboarding_tasks ot
            JOIN workflow_steps ws ON ot.workflow_step_id = ws.step_id
            WHERE ot.onboarding_id = ?
            ORDER BY ot.task_order
        """,
            (onboarding_id,),
        ).fetchall()

        patient_dict["tasks"] = [dict(task) for task in tasks]
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
            conn.execute(
                f"""
                UPDATE onboarding_patients
                SET {stage_field} = ?, completed_date = datetime('now'), updated_date = datetime('now')
                WHERE onboarding_id = ?
            """,
                (completed, onboarding_id),
            )
        else:
            conn.execute(
                f"""
                UPDATE onboarding_patients
                SET {stage_field} = ?, updated_date = datetime('now')
                WHERE onboarding_id = ?
            """,
                (completed, onboarding_id),
            )

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

        if status == "Complete":
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
        conn.execute(
            """
            UPDATE onboarding_patients
            SET assigned_pot_user_id = ?, updated_date = datetime('now')
            WHERE onboarding_id = ?
        """,
            (pot_user_id, onboarding_id),
        )
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
            patient_result = conn.execute(
                """
                SELECT patient_id FROM onboarding_patients WHERE onboarding_id = ?
            """,
                (onboarding_id,),
            ).fetchone()

            if patient_result and patient_result[0]:
                patient_id = patient_result[0]

                # Sync the same data to patients table if columns exist
                patients_update_fields = []
                patients_params = []

                for field, value in checkbox_data.items():
                    # Check if column exists in patients table
                    col_check = conn.execute(
                        """
                        SELECT COUNT(*) FROM pragma_table_info('patients') WHERE name = ?
                    """,
                        (field,),
                    ).fetchone()

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
                    col_check = conn.execute(
                        """
                        SELECT COUNT(*) FROM pragma_table_info('patient_panel') WHERE name = ?
                    """,
                        (field,),
                    ).fetchone()

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
    print(
        f"DEBUG: Starting transfer_onboarding_to_patient_table with onboarding_id={onboarding_id}"
    )
    conn = get_db_connection()
    try:
        # Get onboarding data
        onboarding = conn.execute(
            """
            SELECT * FROM onboarding_patients WHERE onboarding_id = ?
        """,
            (onboarding_id,),
        ).fetchone()

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
            "first_name": onboarding_dict.get("first_name"),
            "last_name": onboarding_dict.get("last_name"),
            "date_of_birth": onboarding_dict.get("date_of_birth"),
            "gender": onboarding_dict.get("gender"),
            "phone_primary": onboarding_dict.get("phone_primary"),
            "email": onboarding_dict.get("email"),
            "address_street": onboarding_dict.get("address_street"),
            "address_city": onboarding_dict.get("address_city"),
            "address_state": onboarding_dict.get("address_state"),
            "address_zip": onboarding_dict.get("address_zip"),
            "emergency_contact_name": onboarding_dict.get("emergency_contact_name"),
            "emergency_contact_phone": onboarding_dict.get("emergency_contact_phone"),
            "insurance_primary": onboarding_dict.get("insurance_provider"),
            "insurance_policy_number": onboarding_dict.get("policy_number"),
            "medical_records_requested": onboarding_dict.get(
                "medical_records_requested", False
            ),
            "referral_documents_received": onboarding_dict.get(
                "referral_documents_received", False
            ),
            "insurance_cards_received": onboarding_dict.get(
                "insurance_cards_received", False
            ),
            "emed_signature_received": onboarding_dict.get(
                "emed_signature_received", False
            ),
            "hypertension": onboarding_dict.get("hypertension", False),
            "mental_health_concerns": onboarding_dict.get(
                "mental_health_concerns", False
            ),
            "dementia": onboarding_dict.get("dementia", False),
            "appointment_contact_name": onboarding_dict.get("appointment_contact_name"),
            "appointment_contact_phone": onboarding_dict.get(
                "appointment_contact_phone"
            ),
            "appointment_contact_email": onboarding_dict.get(
                "appointment_contact_email"
            ),
            "medical_contact_name": onboarding_dict.get("medical_contact_name"),
            "medical_contact_phone": onboarding_dict.get("medical_contact_phone"),
            "medical_contact_email": onboarding_dict.get("medical_contact_email"),
            "facility_nurse_name": onboarding_dict.get("facility_nurse_name"),
            "facility_nurse_phone": onboarding_dict.get("facility_nurse_phone"),
            "facility_nurse_email": onboarding_dict.get("facility_nurse_email"),
            "primary_care_provider": onboarding_dict.get("primary_care_provider"),
            "pcp_last_seen": onboarding_dict.get("pcp_last_seen"),
            "specialist_last_seen": onboarding_dict.get("specialist_last_seen"),
            "active_specialists": onboarding_dict.get("active_specialist"),
            "chronic_conditions_provider": onboarding_dict.get(
                "chronic_conditions_onboarding"
            ),
            "clinical_biometric": onboarding_dict.get("clinical_biometric"),
            "provider_mh_schizophrenia": onboarding_dict.get("mh_schizophrenia", False),
            "provider_mh_depression": onboarding_dict.get("mh_depression", False),
            "provider_mh_anxiety": onboarding_dict.get("mh_anxiety", False),
            "provider_mh_stress": onboarding_dict.get("mh_stress", False),
            "provider_mh_adhd": onboarding_dict.get("mh_adhd", False),
            "provider_mh_bipolar": onboarding_dict.get("mh_bipolar", False),
            "provider_mh_suicidal": onboarding_dict.get("mh_suicidal", False),
            "annual_well_visit": onboarding_dict.get("annual_well_visit", False),
            # CRITICAL MISSING FIELDS - Adding these now
            "facility": onboarding_dict.get(
                "facility_assignment"
            ),  # Map facility_assignment to facility
            "tv_date": onboarding_dict.get("tv_date"),
            "tv_time": onboarding_dict.get("tv_time"),
            "initial_tv_provider": onboarding_dict.get("initial_tv_provider"),
            "assigned_coordinator_id": onboarding_dict.get(
                "assigned_coordinator_user_id"
            ),  # Map coordinator
            # New onboarding columns
            "eligibility_status": onboarding_dict.get("eligibility_status"),
            "eligibility_notes": onboarding_dict.get("eligibility_notes"),
            "eligibility_verified": onboarding_dict.get("eligibility_verified", False),
            "emed_chart_created": onboarding_dict.get("emed_chart_created", False),
            "chart_id": onboarding_dict.get("chart_id"),
            "facility_confirmed": onboarding_dict.get("facility_confirmed", False),
            "chart_notes": onboarding_dict.get("chart_notes"),
            "intake_call_completed": onboarding_dict.get(
                "intake_call_completed", False
            ),
            "intake_notes": onboarding_dict.get("intake_notes"),
        }

        patient_id = None
        existing_patient = None

        # First check if onboarding already has a valid patient_id
        if onboarding_dict.get("patient_id"):
            existing_patient = conn.execute(
                "SELECT patient_id FROM patients WHERE patient_id = ?",
                (onboarding_dict["patient_id"],),
            ).fetchone()
            if existing_patient:
                # Use the existing patient_id immediately and sync onboarding record
                patient_id = existing_patient[0]
                conn.execute(
                    "UPDATE onboarding_patients SET patient_id = ? WHERE onboarding_id = ?",
                    (patient_id, onboarding_id),
                )

        # If no existing patient found by patient_id, check for duplicates by name and DOB
        if not existing_patient:
            first_name = onboarding_dict.get("first_name", "").strip()
            last_name = onboarding_dict.get("last_name", "").strip()
            date_of_birth = onboarding_dict.get("date_of_birth")

            if first_name and last_name and date_of_birth:
                # Generate the expected text-based patient_id for this patient
                expected_patient_id = generate_patient_id(
                    first_name, last_name, date_of_birth
                )

                # Check for existing patient with same text-based patient_id OR same name and DOB
                existing_patient = conn.execute(
                    """
                    SELECT patient_id FROM patients
                    WHERE (patient_id = ? OR
                           (LOWER(TRIM(first_name)) = LOWER(?)
                            AND LOWER(TRIM(last_name)) = LOWER(?)
                            AND date_of_birth = ?))
                    AND patient_id IS NOT NULL
                    LIMIT 1
                """,
                    (
                        expected_patient_id,
                        first_name.lower(),
                        last_name.lower(),
                        date_of_birth,
                    ),
                ).fetchone()

                if existing_patient:
                    # Update onboarding record with found patient_id
                    patient_id = existing_patient[0]
                    conn.execute(
                        "UPDATE onboarding_patients SET patient_id = ? WHERE onboarding_id = ?",
                        (patient_id, onboarding_id),
                    )

        if existing_patient:
            # Build dynamic UPDATE clauses for columns that exist in patients table
            set_clauses = []
            params = []
            for col, val in candidate.items():
                if col in patients_cols:
                    # preserve existing richer provider data using COALESCE for clinical/provider fields
                    if (
                        col.startswith("appointment_contact_")
                        or col.startswith("medical_contact_")
                        or col
                        in (
                            "primary_care_provider",
                            "pcp_last_seen",
                            "active_specialists",
                            "chronic_conditions_provider",
                            "clinical_biometric",
                        )
                        or col.startswith("provider_mh_")
                    ):
                        set_clauses.append(f"{col} = COALESCE(?, {col})")
                        params.append(val)
                    else:
                        set_clauses.append(f"{col} = ?")
                        params.append(val)

            set_clauses.append("updated_date = datetime('now')")
            params.append(patient_id)

            if len(set_clauses) > 1:
                query = (
                    f"UPDATE patients SET {', '.join(set_clauses)} WHERE patient_id = ?"
                )
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
            if "enrollment_date" in patients_cols:
                insert_cols.append("enrollment_date")
                insert_vals.append(datetime.now().strftime("%Y-%m-%d"))
            if "created_date" in patients_cols:
                insert_cols.append("created_date")
                insert_vals.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            if "status" in patients_cols and "status" not in insert_cols:
                insert_cols.append("status")
                insert_vals.append("Active")

            if not insert_cols:
                raise Exception("No matching patient columns found to insert")

            # Generate proper text-based patient_id
            patient_id = generate_patient_id(
                onboarding_dict.get("first_name", ""),
                onboarding_dict.get("last_name", ""),
                onboarding_dict.get("date_of_birth", ""),
            )

            # Add patient_id to the insert if the column exists
            if "patient_id" in patients_cols:
                insert_cols.append("patient_id")
                insert_vals.append(patient_id)

            placeholders = ",".join(["?"] * len(insert_cols))
            cols_sql = ",".join(insert_cols)
            cursor = conn.execute(
                f"INSERT INTO patients ({cols_sql}) VALUES ({placeholders})",
                tuple(insert_vals),
            )

            # If patient_id column didn't exist in the original insert, update it now
            if "patient_id" not in insert_cols:
                conn.execute(
                    "UPDATE patients SET patient_id = ? WHERE rowid = ?",
                    (patient_id, cursor.lastrowid),
                )

            # Update onboarding record with patient_id if column exists
            conn.execute(
                "UPDATE onboarding_patients SET patient_id = ? WHERE onboarding_id = ?",
                (patient_id, onboarding_id),
            )

        # Mark onboarding as complete
        conn.execute(
            """
            UPDATE onboarding_patients
            SET completed_date = datetime('now'), updated_date = datetime('now')
            WHERE onboarding_id = ?
        """,
            (onboarding_id,),
        )

        # Create patient assignments if provider or coordinator are assigned
        provider_id = onboarding_dict.get("assigned_provider_user_id")
        coordinator_id = onboarding_dict.get("assigned_coordinator_user_id")

        print(f"DEBUG: provider_id={provider_id}, coordinator_id={coordinator_id}")
        print(f"DEBUG: patient_id={patient_id}")

        if provider_id or coordinator_id:
            print(f"DEBUG: Creating patient assignment")
            # Check if assignment already exists - match actual table schema
            existing_assignment = conn.execute(
                """
                SELECT assignment_id FROM patient_assignments
                WHERE patient_id = ? AND status = 'active'
            """,
                (patient_id,),
            ).fetchone()

            if existing_assignment:
                print(f"DEBUG: Updating existing assignment {existing_assignment[0]}")
                # Update existing assignment - match actual table schema
                conn.execute(
                    """
                    UPDATE patient_assignments
                    SET provider_id = ?, coordinator_id = ?, status = 'active'
                    WHERE assignment_id = ?
                """,
                    (provider_id, coordinator_id, existing_assignment[0]),
                )
            else:
                print(f"DEBUG: Creating new assignment")
                # Create new assignment - match actual table schema
                conn.execute(
                    """
                    INSERT INTO patient_assignments (
                        patient_id, provider_id, coordinator_id, status
                    ) VALUES (?, ?, ?, 'active')
                """,
                    (patient_id, provider_id, coordinator_id),
                )
                print(f"DEBUG: Assignment created successfully")

        conn.commit()

        return patient_id

    finally:
        conn.close()


def insert_patient_from_onboarding(onboarding_id):
    """Insert patient data into patients table from onboarding data while keeping onboarding record"""
    conn = get_db_connection()
    try:
        # Get onboarding data
        onboarding = conn.execute(
            """
            SELECT * FROM onboarding_patients WHERE onboarding_id = ?
        """,
            (onboarding_id,),
        ).fetchone()

        if not onboarding:
            raise Exception(f"No onboarding patient found with ID {onboarding_id}")

        onboarding_dict = dict(onboarding)

        # Check if patient already exists in main table by name and DOB first
        existing_patient = conn.execute(
            """
            SELECT patient_id FROM patients
            WHERE first_name = ? AND last_name = ? AND date_of_birth = ?
            AND patient_id IS NOT NULL
            ORDER BY patient_id
            LIMIT 1
        """,
            (
                onboarding_dict["first_name"],
                onboarding_dict["last_name"],
                onboarding_dict["date_of_birth"],
            ),
        ).fetchone()

        if existing_patient:
            # Use existing patient - update with latest onboarding data
            text_patient_id = existing_patient["patient_id"]
            conn.execute(
                """
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
                    last_annual_wellness_visit = ?,
                    assigned_coordinator_id = ?,
                    transportation = COALESCE(?, transportation),
                    preferred_language = COALESCE(?, preferred_language),
                    updated_date = CURRENT_TIMESTAMP
                WHERE patient_id = ?
            """,
                (
                    onboarding_dict["first_name"],
                    onboarding_dict["last_name"],
                    onboarding_dict["date_of_birth"],
                    onboarding_dict.get("gender"),
                    onboarding_dict.get("phone_primary"),
                    onboarding_dict.get("email"),
                    onboarding_dict.get("address_street"),
                    onboarding_dict.get("address_city"),
                    onboarding_dict.get("address_state"),
                    onboarding_dict.get("address_zip"),
                    onboarding_dict.get("emergency_contact_name"),
                    onboarding_dict.get("emergency_contact_phone"),
                    onboarding_dict.get("insurance_provider"),
                    onboarding_dict.get("policy_number"),
                    onboarding_dict.get("medical_records_requested", False),
                    onboarding_dict.get("referral_documents_received", False),
                    onboarding_dict.get("insurance_cards_received", False),
                    onboarding_dict.get("emed_signature_received", False),
                    onboarding_dict.get("hypertension", False),
                    onboarding_dict.get("mental_health_concerns", False),
                    onboarding_dict.get("dementia", False),
                    onboarding_dict.get("appointment_contact_name"),
                    onboarding_dict.get("appointment_contact_phone"),
                    onboarding_dict.get("appointment_contact_email"),
                    onboarding_dict.get("medical_contact_name"),
                    onboarding_dict.get("medical_contact_phone"),
                    onboarding_dict.get("medical_contact_email"),
                    onboarding_dict.get("primary_care_provider"),
                    onboarding_dict.get("pcp_last_seen"),
                    onboarding_dict.get("annual_well_visit", False),
                    onboarding_dict.get("assigned_coordinator_user_id"),
                    onboarding_dict.get("transportation"),
                    onboarding_dict.get("preferred_language"),
                    text_patient_id,
                ),
            )

            # Update onboarding record with the existing patient_id
            conn.execute(
                """
                UPDATE onboarding_patients SET patient_id = ? WHERE onboarding_id = ?
            """,
                (text_patient_id, onboarding_id),
            )
        else:
            # Create new patient record, including assigned_coordinator_id
            cursor = conn.execute(
                """
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
                    transportation, preferred_language,
                    enrollment_date, created_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'Active')
            """,
                (
                    onboarding_dict["first_name"],
                    onboarding_dict["last_name"],
                    onboarding_dict["date_of_birth"],
                    onboarding_dict.get("gender"),
                    onboarding_dict.get("phone_primary"),
                    onboarding_dict.get("email"),
                    onboarding_dict.get("address_street"),
                    onboarding_dict.get("address_city"),
                    onboarding_dict.get("address_state"),
                    onboarding_dict.get("address_zip"),
                    onboarding_dict.get("emergency_contact_name"),
                    onboarding_dict.get("emergency_contact_phone"),
                    onboarding_dict.get("insurance_provider"),
                    onboarding_dict.get("policy_number"),
                    onboarding_dict.get("medical_records_requested", False),
                    onboarding_dict.get("referral_documents_received", False),
                    onboarding_dict.get("insurance_cards_received", False),
                    onboarding_dict.get("emed_signature_received", False),
                    onboarding_dict.get("hypertension", False),
                    onboarding_dict.get("mental_health_concerns", False),
                    onboarding_dict.get("dementia", False),
                    onboarding_dict.get("appointment_contact_name"),
                    onboarding_dict.get("appointment_contact_phone"),
                    onboarding_dict.get("appointment_contact_email"),
                    onboarding_dict.get("medical_contact_name"),
                    onboarding_dict.get("medical_contact_phone"),
                    onboarding_dict.get("medical_contact_email"),
                    onboarding_dict.get("primary_care_provider"),
                    onboarding_dict.get("pcp_last_seen"),
                    onboarding_dict.get("annual_well_visit", False),
                    onboarding_dict.get("assigned_coordinator_user_id"),
                    onboarding_dict.get("transportation"),
                    onboarding_dict.get("preferred_language"),
                ),
            )
            integer_patient_id = cursor.lastrowid

            # Generate the text-based patient_id using the same function
            text_patient_id = generate_patient_id(
                onboarding_dict.get("first_name", ""),
                onboarding_dict.get("last_name", ""),
                onboarding_dict.get("date_of_birth", ""),
            )

            # Update the patient record with the generated text-based patient_id
            conn.execute(
                """
                UPDATE patients SET patient_id = ? WHERE ROWID = ?
            """,
                (text_patient_id, integer_patient_id),
            )

            # Update onboarding record with the text-based patient_id
            conn.execute(
                """
                UPDATE onboarding_patients SET patient_id = ? WHERE onboarding_id = ?
            """,
                (text_patient_id, onboarding_id),
            )

        # Create patient assignments in patient_assignments table using text-based patient_id
        provider_id = onboarding_dict.get("assigned_provider_user_id")
        coordinator_id = onboarding_dict.get("assigned_coordinator_user_id")

        print(f"DEBUG: provider_id={provider_id}, coordinator_id={coordinator_id}")
        print(f"DEBUG: text_patient_id={text_patient_id}")

        if provider_id or coordinator_id:
            print(f"DEBUG: Entering assignment creation logic")
            # Check if assignment already exists using text-based patient_id - match actual table schema
            existing_assignment = conn.execute(
                """
                SELECT assignment_id FROM patient_assignments
                WHERE patient_id = ? AND status = 'active'
            """,
                (text_patient_id,),
            ).fetchone()

            if existing_assignment:
                print(
                    f"DEBUG: Updating existing assignment {existing_assignment['assignment_id']}"
                )
                # Update existing assignment - match actual table schema
                conn.execute(
                    """
                    UPDATE patient_assignments
                    SET provider_id = ?, coordinator_id = ?, status = 'active'
                    WHERE assignment_id = ?
                """,
                    (provider_id, coordinator_id, existing_assignment["assignment_id"]),
                )
            else:
                print(f"DEBUG: Creating new assignment for {text_patient_id}")
                # Create new assignment - match actual table schema
                conn.execute(
                    """
                    INSERT INTO patient_assignments (
                        patient_id, provider_id, coordinator_id, status
                    ) VALUES (?, ?, ?, 'active')
                """,
                    (text_patient_id, provider_id, coordinator_id),
                )
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
    """
    Get all users with a specific role.

    Supports multiple input patterns:
    - Role ID (int): get_users_by_role(33) or get_users_by_role(36)
    - Role Constant: get_users_by_role(ROLE_CARE_PROVIDER)
    - Role Abbreviation (str): get_users_by_role("CP") or get_users_by_role("CC")
    - Full Role Name (str): get_users_by_role("Care Coordinator")

    Args:
        role_identifier: Either role_id (int) or role_name (str)

    Returns:
        List of dicts with keys: user_id, username, full_name

    Examples:
        >>> get_users_by_role(33)
        >>> get_users_by_role("CP")
        >>> get_users_by_role("Care Coordinator")
    """
    conn = get_db_connection()
    try:
        if isinstance(role_identifier, int):
            # Handle role_id
            users = conn.execute(
                """
                SELECT u.user_id, u.username, u.full_name
                FROM users u
                JOIN user_roles ur ON u.user_id = ur.user_id
                JOIN roles r ON ur.role_id = r.role_id
                WHERE r.role_id = ?
            """,
                (role_identifier,),
            ).fetchall()
        else:
            # Handle role_name (string)
            users = conn.execute(
                """
                SELECT u.user_id, u.username, u.full_name
                FROM users u
                JOIN user_roles ur ON u.user_id = ur.user_id
                JOIN roles r ON ur.role_id = r.role_id
                WHERE r.role_name = ?
            """,
                (role_identifier,),
            ).fetchall()
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
        return conn.execute(
            query, (str(coordinator_id), start_date, end_date)
        ).fetchall()
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
            staff_mapping = conn.execute(
                """
                SELECT u.full_name
                FROM staff_code_mapping scm
                JOIN users u ON scm.user_id = u.user_id
                WHERE scm.staff_code = ?
            """,
                (str(coordinator_id),),
            ).fetchone()

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
            coordinator_filter = (
                "WHERE CAST(ct.coordinator_id AS TEXT) = CAST(? AS TEXT)"
            )
            params = [coordinator_id]
        else:
            coordinator_filter = ""
            params = []

        # Add date filter if weeks_back is specified
        if weeks_back:
            if coordinator_filter:
                coordinator_filter += (
                    " AND ct.task_date >= date('now', '-' || ? || ' days')"
                )
            else:
                coordinator_filter = (
                    "WHERE ct.task_date >= date('now', '-' || ? || ' days')"
                )
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
            conn.execute(
                "ALTER TABLE coordinator_tasks ADD COLUMN coordinator_name TEXT;"
            )
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
        provider_as_pid = normalize_patient_id(
            form_data.get("provider_name", ""), conn=conn
        )

        # Generate PST timestamp for unique entry identification
        now = pd.Timestamp.now()
        now_pst = now.tz_localize('UTC').tz_convert('America/Los_Angeles')

        # Determine correct monthly table based on task_date
        task_year = form_data["task_date"].year
        task_month = form_data["task_date"].month
        table_name = ensure_monthly_coordinator_tasks_table(
            year=task_year, month=task_month, conn=conn
        )

        conn.execute(
            f"""
            INSERT INTO {table_name} (
                coordinator_id, patient_id, task_date, task_type,
                duration_minutes, notes, source_system, imported_at, created_at_pst
            ) VALUES (?, ?, ?, ?, ?, ?, 'PHONE_REVIEW', CURRENT_TIMESTAMP, ?)
        """,
            (
                coordinator_id,
                provider_as_pid,
                form_data["task_date"].strftime("%Y-%m-%d"),
                "19|Communication|Communication: Phone",
                form_data["duration_minutes"],
                f"Phone review with {form_data.get('provider_name', '')}: {form_data.get('notes', '')}",
                now_pst.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

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
        "Provider Assignment",
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
    """Get all patients from unified patient_panel table for Provider dashboard filtering"""
    conn = get_db_connection()
    try:
        # Return ALL patients from unified patient_panel - UI will filter by provider_id
        query = """
            SELECT
                patient_id,
                first_name,
                last_name,
                date_of_birth,
                phone_primary as phone,
                facility,
                status,
                last_visit_date as last_visited_date_display,
                last_visit_date,
                service_type,
                provider_name as care_provider_name,
                coordinator_name as care_coordinator_name,
                code_status,
                goc_value,
                subjective_risk_level,
                provider_id,
                coordinator_id,
                goals_of_care,
                appointment_contact_name,
                appointment_contact_phone,
                medical_contact_name,
                medical_contact_phone,
                nurse_poc_name,
                nurse_phone
            FROM patient_panel
            ORDER BY last_name, first_name
        """
        result = conn.execute(query).fetchall()
        return [dict(row) for row in result]
    except Exception as e:
        print(f"Error in get_provider_patient_panel_enhanced: {e}")
        return []
    finally:
        conn.close()


def get_coordinator_patient_panel_enhanced(user_id):
    """Get all patients from unified patient_panel table for Coordinator dashboard filtering"""
    conn = get_db_connection()
    try:
        # Return ALL patients from unified patient_panel - UI will filter by coordinator_id
        query = """
            SELECT
                patient_id,
                first_name,
                last_name,
                date_of_birth,
                phone_primary as phone,
                facility,
                status,
                last_visit_date as last_visited_date_display,
                last_visit_date,
                service_type,
                provider_name as care_provider_name,
                coordinator_name as care_coordinator_name,
                code_status,
                goc_value,
                subjective_risk_level,
                provider_id,
                coordinator_id,
                goals_of_care,
                appointment_contact_name,
                appointment_contact_phone,
                medical_contact_name,
                medical_contact_phone,
                care_provider_name,
                care_coordinator_name
            FROM patient_panel
            ORDER BY last_name, first_name
        """
        result = conn.execute(query).fetchall()
        return [dict(row) for row in result]
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


def get_hhc_export_data(selected_statuses=None):
    """Get comprehensive HHC export data for admin dashboard"""
    conn = get_db_connection()
    try:
        if not selected_statuses:
            selected_statuses = ["Active", "Active-PCP", "Active-Geri", "HOSPICE"]

        # Build parameter list for SQL IN clause
        placeholders = ",".join(["?" for _ in selected_statuses])

        query = f"""
        SELECT
            patient_id,
            status as "Pt Status",
            last_visit_date as "Last Visit",
            service_type as "Last Visit Type",
            COALESCE(last_name || ' ' || first_name || ' ' || COALESCE(date_of_birth, ''), last_name || ' ' || first_name) as "LAST FIRST DOB",
            last_name as "Last",
            first_name as "First",
            phone_primary as "Contact",
            (first_name || ' ' || last_name) as "Name",
            facility as "Fac",
            goals_of_care as "Goals of Care",
            goc_value as "goc",
            code_status as "code",
            subjective_risk_level as "Risk",
            provider_name as "Prov",
            coordinator_name as "Care Coordinator",
            appointment_contact_phone as "Appt POC",
            medical_contact_phone as "Medical POC",
            CASE WHEN coordinator_id IS NOT NULL THEN 'Yes' ELSE 'No' END as "Assigned"
        FROM patient_panel
        WHERE status IN ({placeholders})
        ORDER BY last_name, first_name
        """

        result = conn.execute(query, selected_statuses).fetchall()
        return [dict(row) for row in result]
    except Exception as e:
        print(f"Error in get_hhc_export_data: {e}")
        return []
    finally:
        conn.close()


def get_all_patients_simple():
    """Get all patients from the database - simple test function"""
    conn = get_db_connection()
    try:
        query = (
            "SELECT patient_id, first_name, last_name, status FROM patients LIMIT 10"
        )
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
            FROM patient_assignments upa
            JOIN patients p ON upa.patient_id = p.patient_id
            WHERE upa.provider_id = ?
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
            if "last_visit_service_type" in d:
                d["service_type"] = d["last_visit_service_type"]
            patients.append(d)
        return patients
    finally:
        conn.close()


def get_provider_panel_patients_by_month(provider_id, selected_month):
    """Get provider panel patients pre-loaded for specific month (P0 Enhancement)"""
    conn = get_db_connection()
    try:
        # Parse the selected month (format: "2025-09")
        year, month = selected_month.split("-")
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
                SELECT DISTINCT patient_id FROM patient_assignments WHERE provider_id = ?
            ) assigned
            JOIN patients p ON assigned.patient_id = p.patient_id
            LEFT JOIN (
                SELECT patient_id, MAX(task_date) as last_task_date
                FROM provider_tasks_2025_09
                WHERE provider_id = ?
                GROUP BY patient_id
            ) lp ON p.patient_id = lp.patient_id
            LEFT JOIN facilities f ON p.facility_id = f.facility_id
            WHERE (p.status LIKE 'Active%' OR p.status = 'Hospice')
        """

        result = conn.execute(query, (provider_id, selected_month)).fetchall()
        return [dict(row) for row in result]
    finally:
        conn.close()


def get_cpm_current_month_summary(user_id):
    """Get CPM monthly summary for current month (P0 Enhancement)"""
    conn = get_db_connection()
    try:
        current_month = datetime.now().strftime("%m")
        current_year = datetime.now().strftime("%Y")

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
        month_date = current_date - timedelta(days=i * 30)
        months.append(
            {
                "value": month_date.strftime("%Y-%m"),
                "label": month_date.strftime("%B %Y"),
            }
        )

    return months


def get_all_patient_panel():
    """
    Get all patient records from the patient_panel table.
    Returns a list of dictionaries containing patient data with assigned provider/coordinator info.
    """
    conn = get_db_connection()
    try:
        query = """
        SELECT
            patient_id,
            first_name,
            last_name,
            date_of_birth,
            phone_primary,
            facility,
            status,
            last_visit_date,
            last_visit_service_type,
            provider_id,
            coordinator_id,
            provider_name,
            coordinator_name,
            COALESCE(provider_name, '') as care_provider_name,
            COALESCE(coordinator_name, '') as care_coordinator_name,
            goals_of_care,
            goc_value,
            code_status,
            subjective_risk_level,
            service_type,
            appointment_contact_name,
            appointment_contact_phone,
            medical_contact_name,
            medical_contact_phone,
            nurse_poc_name,
            nurse_phone,
            labs_notes,
            imaging_notes,
            general_notes,
            next_appointment_date,
            updated_date
        FROM patient_panel
        ORDER BY last_name, first_name
        """
        df = pd.read_sql_query(query, conn)
        # Replace NaN with None for proper filtering
        df = df.where(pd.notnull(df), None)

        # Convert provider_id and coordinator_id to proper integers (not float)
        # Handle None values properly - convert None to 0 for unassigned patients
        for col in ["provider_id", "coordinator_id"]:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: int(x) if x is not None and not pd.isna(x) else 0
                )

        return df.to_dict(orient="records")
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
        onboarding = conn.execute(
            """
            SELECT * FROM onboarding_patients WHERE onboarding_id = ?
        """,
            (onboarding_id,),
        ).fetchone()

        if not onboarding:
            return None

        onboarding_dict = dict(onboarding)
        patient_id = onboarding_dict.get("patient_id")

        # Always call transfer_onboarding_to_patient_table to ensure patients table is populated
        transferred_patient_id = transfer_onboarding_to_patient_table(onboarding_id)
        if transferred_patient_id:
            patient_id = transferred_patient_id
        elif not patient_id:
            return None

        # Get existing patient_panel columns
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(patient_panel);")
        panel_cols = [r[1] for r in cur.fetchall()]

        # Derive provider_name and coordinator_name from users table if IDs exist
        provider_user_id = onboarding_dict.get("assigned_provider_user_id")
        coordinator_user_id = onboarding_dict.get("assigned_coordinator_user_id")
        provider_name = None
        coordinator_name = None
        if provider_user_id:
            row = conn.execute(
                "SELECT full_name FROM users WHERE user_id = ?", (provider_user_id,)
            ).fetchone()
            if row:
                try:
                    provider_name = (
                        row["full_name"] if isinstance(row, dict) else row[0]
                    )
                except Exception:
                    provider_name = row[0]
        if coordinator_user_id:
            row2 = conn.execute(
                "SELECT full_name FROM users WHERE user_id = ?", (coordinator_user_id,)
            ).fetchone()
            if row2:
                try:
                    coordinator_name = (
                        row2["full_name"] if isinstance(row2, dict) else row2[0]
                    )
                except Exception:
                    coordinator_name = row2[0]

        # Mapping of onboarding data to patient_panel columns
        panel_data = {
            "patient_id": patient_id,
            "first_name": onboarding_dict.get("first_name"),
            "last_name": onboarding_dict.get("last_name"),
            "date_of_birth": onboarding_dict.get("date_of_birth"),
            "gender": onboarding_dict.get("gender"),
            "phone_primary": onboarding_dict.get("phone_primary"),
            "email": onboarding_dict.get("email"),
            "address_street": onboarding_dict.get("address_street"),
            "address_city": onboarding_dict.get("address_city"),
            "address_state": onboarding_dict.get("address_state"),
            "address_zip": onboarding_dict.get("address_zip"),
            "emergency_contact_name": onboarding_dict.get("emergency_contact_name"),
            "emergency_contact_phone": onboarding_dict.get("emergency_contact_phone"),
            "insurance_primary": onboarding_dict.get("insurance_provider"),
            "insurance_policy_number": onboarding_dict.get("policy_number"),
            # CRITICAL MISSING FIELDS - Adding these now
            "facility": onboarding_dict.get(
                "facility_assignment"
            ),  # Map facility_assignment to facility
            "current_facility_id": onboarding_dict.get(
                "facility_assignment"
            ),  # Also map to current_facility_id
            "provider_id": provider_user_id,  # Map provider
            "coordinator_id": coordinator_user_id,  # Map coordinator
            "provider_name": provider_name,
            "coordinator_name": coordinator_name,
            "initial_tv_completed_date": onboarding_dict.get("tv_date"),  # Map TV date
            "initial_tv_provider": onboarding_dict.get("initial_tv_provider"),
            "assigned_coordinator_id": onboarding_dict.get(
                "assigned_coordinator_user_id"
            ),  # Legacy field
            "assigned_provider_id": onboarding_dict.get(
                "assigned_provider_user_id"
            ),  # Legacy field
            # Medical conditions
            "hypertension": onboarding_dict.get("hypertension", False),
            "mental_health_concerns": onboarding_dict.get(
                "mental_health_concerns", False
            ),
            "dementia": onboarding_dict.get("dementia", False),
            # New onboarding columns
            "eligibility_status": onboarding_dict.get("eligibility_status"),
            "eligibility_notes": onboarding_dict.get("eligibility_notes"),
            "eligibility_verified": onboarding_dict.get("eligibility_verified", False),
            "emed_chart_created": onboarding_dict.get("emed_chart_created", False),
            "chart_id": onboarding_dict.get("chart_id"),
            "facility_confirmed": onboarding_dict.get("facility_confirmed", False),
            "chart_notes": onboarding_dict.get("chart_notes"),
            "intake_call_completed": onboarding_dict.get(
                "intake_call_completed", False
            ),
            "intake_notes": onboarding_dict.get("intake_notes"),
            # Contact fields
            "appointment_contact_name": onboarding_dict.get("appointment_contact_name"),
            "appointment_contact_phone": onboarding_dict.get("appointment_contact_phone"),
            "appointment_contact_email": onboarding_dict.get("appointment_contact_email"),
            "medical_contact_name": onboarding_dict.get("medical_contact_name"),
            "medical_contact_phone": onboarding_dict.get("medical_contact_phone"),
            "medical_contact_email": onboarding_dict.get("medical_contact_email"),
            "facility_nurse_name": onboarding_dict.get("facility_nurse_name"),
            "facility_nurse_phone": onboarding_dict.get("facility_nurse_phone"),
            "facility_nurse_email": onboarding_dict.get("facility_nurse_email"),
            # TV Scheduling columns (newly added to patient_panel)
            "tv_date": onboarding_dict.get("tv_date"),
            "tv_time": onboarding_dict.get("tv_time"),
            "tv_scheduled": onboarding_dict.get("tv_scheduled", False),
            "patient_notified": onboarding_dict.get("patient_notified", False),
            "initial_tv_completed": onboarding_dict.get("initial_tv_completed", False),
            "initial_tv_completed_date": onboarding_dict.get("initial_tv_completed_date"),
            "initial_tv_provider": onboarding_dict.get("initial_tv_provider"),
            "initial_tv_notes": onboarding_dict.get("initial_tv_notes"),
            "provider_completed_initial_tv": onboarding_dict.get("provider_completed_initial_tv", False),
            # Additional fields
            "active_specialist": onboarding_dict.get("active_specialist"),
            "specialist_last_seen": onboarding_dict.get("specialist_last_seen"),
            "chronic_conditions_onboarding": onboarding_dict.get("chronic_conditions_onboarding"),
            "primary_care_provider": onboarding_dict.get("primary_care_provider"),
            "pcp_last_seen": onboarding_dict.get("pcp_last_seen"),
        }

        # Check if patient already exists in patient_panel
        existing_panel = conn.execute(
            """
            SELECT patient_id FROM patient_panel WHERE patient_id = ?
        """,
            (patient_id,),
        ).fetchone()

        if existing_panel:
            # Update existing record
            update_fields = []
            params = []

            for col, val in panel_data.items():
                if col in panel_cols and col != "patient_id":
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
            if "created_date" in panel_cols:
                insert_cols.append("created_date")
                insert_vals.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            if insert_cols:
                placeholders = ",".join(["?"] * len(insert_cols))
                cols_sql = ",".join(insert_cols)
                conn.execute(
                    f"INSERT INTO patient_panel ({cols_sql}) VALUES ({placeholders})",
                    tuple(insert_vals),
                )

        conn.commit()
        return patient_id

    finally:
        conn.close()


def sync_onboarding_to_all_tables(onboarding_id):
    """
    Comprehensive sync function that updates ALL patient tables when onboarding is complete.

    This function ensures the patient data from onboarding is propagated to:
    1. patients table (canonical source)
    2. patient_panel table (denormalized for dashboards/ZMO)
    3. HHC export tables (for HHC View Template)
    4. patient_assignments table (ensures provider/coordinator assignments exist)

    Call this function at Stage 5 completion to ensure all views are up to date.

    Args:
        onboarding_id: The onboarding_patients.onboarding_id

    Returns:
        dict with status of each sync operation:
        {
            'patient_id': str or None,
            'patients_table': bool,
            'patient_panel': bool,
            'patient_assignments': bool,
            'hhc_export': bool,
            'success': bool,
            'message': str
        }
    """
    result = {
        'patient_id': None,
        'patients_table': False,
        'patient_panel': False,
        'patient_assignments': False,
        'hhc_export': False,
        'success': False,
        'message': ''
    }

    conn = get_db_connection()
    try:
        # Get onboarding data
        onboarding = conn.execute(
            """
            SELECT * FROM onboarding_patients WHERE onboarding_id = ?
        """,
            (onboarding_id,),
        ).fetchone()

        if not onboarding:
            result['message'] = f"No onboarding patient found with ID {onboarding_id}"
            return result

        onboarding_dict = dict(onboarding)

        # Step 1: Ensure patient_id exists in patients table
        patient_id = onboarding_dict.get("patient_id")
        if not patient_id:
            # First, create/update patient record to get patient_id
            conn.commit()  # Commit any pending before calling other function
            conn.close()
            patient_id = insert_patient_from_onboarding(onboarding_id)
            conn = get_db_connection()
            result['message'] += f"Created patient record: {patient_id}. "

        result['patient_id'] = patient_id

        # Step 2: Update patients table with latest onboarding data
        # Note: assigned_provider_id is not in patients table, only assigned_coordinator_id
        # Provider assignments are tracked in patient_assignments table instead
        conn.execute(
            """
            UPDATE patients SET
                tv_date = COALESCE(?, tv_date),
                tv_scheduled = COALESCE(?, tv_scheduled),
                initial_tv_provider = COALESCE(?, initial_tv_provider),
                initial_tv_completed_date = COALESCE(?, initial_tv_completed_date),
                assigned_coordinator_id = COALESCE(?, assigned_coordinator_id),
                facility = COALESCE(?, facility),
                current_facility_id = COALESCE(?, current_facility_id),
                eligibility_status = COALESCE(?, eligibility_status),
                eligibility_verified = COALESCE(?, eligibility_verified),
                emed_chart_created = COALESCE(?, emed_chart_created),
                chart_id = COALESCE(?, chart_id),
                facility_confirmed = COALESCE(?, facility_confirmed),
                chart_notes = COALESCE(?, chart_notes),
                intake_call_completed = COALESCE(?, intake_call_completed),
                intake_notes = COALESCE(?, intake_notes),
                transportation = COALESCE(?, transportation),
                preferred_language = COALESCE(?, preferred_language),
                updated_date = CURRENT_TIMESTAMP
            WHERE patient_id = ?
            """,
            (
                onboarding_dict.get('tv_date'),
                onboarding_dict.get('tv_scheduled', False),
                onboarding_dict.get('initial_tv_provider'),
                onboarding_dict.get('tv_date'),  # Use tv_date for initial_tv_completed_date
                onboarding_dict.get('assigned_coordinator_user_id'),
                onboarding_dict.get('facility_assignment'),
                onboarding_dict.get('facility_assignment'),
                onboarding_dict.get('eligibility_status'),
                onboarding_dict.get('eligibility_verified', False),
                onboarding_dict.get('emed_chart_created', False),
                onboarding_dict.get('chart_id'),
                onboarding_dict.get('facility_confirmed', False),
                onboarding_dict.get('chart_notes'),
                onboarding_dict.get('intake_call_completed', False),
                onboarding_dict.get('intake_notes'),
                onboarding_dict.get('transportation'),
                onboarding_dict.get('preferred_language'),
                patient_id,
            ),
        )
        result['patients_table'] = True

        # Step 3: Sync to patient_panel (ZMO view reads from here)
        conn.commit()  # Commit before calling sync function
        conn.close()
        panel_patient_id = sync_onboarding_to_patient_panel(onboarding_id)
        conn = get_db_connection()
        result['patient_panel'] = (panel_patient_id == patient_id)

        # Step 4: Ensure patient_assignments exists with correct provider/coordinator
        provider_id = onboarding_dict.get('assigned_provider_user_id')
        coordinator_id = onboarding_dict.get('assigned_coordinator_user_id')

        if provider_id or coordinator_id:
            # Check if assignment exists
            existing_assignment = conn.execute(
                """
                SELECT assignment_id FROM patient_assignments
                WHERE patient_id = ? AND status = 'active'
            """,
                (patient_id,),
            ).fetchone()

            if existing_assignment:
                # Update existing assignment - match actual table schema
                conn.execute(
                    """
                    UPDATE patient_assignments
                    SET provider_id = COALESCE(?, provider_id),
                        coordinator_id = COALESCE(?, coordinator_id),
                        status = 'active'
                    WHERE assignment_id = ?
                """,
                    (provider_id, coordinator_id, existing_assignment['assignment_id']),
                )
                result['message'] += f"Updated assignment {existing_assignment['assignment_id']}. "
            else:
                # Create new assignment - match actual table schema
                conn.execute(
                    """
                    INSERT INTO patient_assignments (
                        patient_id, provider_id, coordinator_id, status
                    ) VALUES (?, ?, ?, 'active')
                """,
                    (patient_id, provider_id, coordinator_id),
                )
                result['message'] += f"Created new assignment. "
            result['patient_assignments'] = True
        else:
            result['message'] += "No provider/coordinator to assign. "

        # Step 5: Refresh HHC export table if it exists
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='hhc_patients_export'"
            )
            if cursor.fetchone():
                # Table exists - trigger a refresh by recreating from view
                conn.execute("DROP TABLE IF EXISTS hhc_patients_export")
                conn.execute(
                    """
                    CREATE TABLE hhc_patients_export AS
                    SELECT * FROM hhc_export_view
                """
                )
                result['hhc_export'] = True
                result['message'] += "HHC export refreshed. "
        except Exception as e:
            # HHC export table might not exist yet, which is OK
            result['message'] += f"HHC refresh skipped: {e}. "

        conn.commit()
        result['success'] = True

    except Exception as e:
        conn.rollback()
        result['message'] = f"Error during sync: {str(e)}"
        print(f"Error in sync_onboarding_to_all_tables: {e}")
    finally:
        conn.close()

    return result


def create_patient_assignment(
    patient_id,
    provider_id=None,
    coordinator_id=None,
    assignment_type="onboarding",  # Note: not used in actual schema, kept for API compatibility
    status="active",
    priority_level="medium",  # Note: not used in actual schema, kept for API compatibility
    notes=None,  # Note: not used in actual schema, kept for API compatibility
    created_by=None,  # Note: not used in actual schema, kept for API compatibility
):
    """Create a patient assignment in the patient_assignments table

    Note: The actual patient_assignments table only has: assignment_id, patient_id, provider_id,
    coordinator_id, status, source, imported_at. Parameters like assignment_type, priority_level,
    notes, created_by are accepted for API compatibility but not stored.
    """
    conn = get_db_connection()
    try:
        # Check if assignment already exists for this patient - match actual table schema
        existing = conn.execute(
            """
            SELECT assignment_id FROM patient_assignments
            WHERE patient_id = ? AND status = 'active'
        """,
            (patient_id,),
        ).fetchone()

        if existing:
            # Update existing assignment - match actual table schema
            conn.execute(
                """
                UPDATE patient_assignments
                SET provider_id = ?, coordinator_id = ?, status = 'active'
                WHERE assignment_id = ?
            """,
                (provider_id, coordinator_id, existing["assignment_id"]),
            )
        else:
            # Create new assignment - match actual table schema
            conn.execute(
                """
                INSERT INTO patient_assignments (
                    patient_id, provider_id, coordinator_id, status
                ) VALUES (?, ?, ?, ?)
            """,
                (patient_id, provider_id, coordinator_id, status),
            )

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
        conn.execute(
            """
            UPDATE provider_weekly_summary_with_billing
            SET paid = ?, updated_date = CURRENT_TIMESTAMP
            WHERE provider_id = ? AND week_start_date = ?
        """,
            (paid_status, provider_id, week_start_date),
        )

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
        conn.execute(
            """
            UPDATE onboarding_patients
            SET patient_status = ?, updated_date = CURRENT_TIMESTAMP
            WHERE onboarding_id = ?
        """,
            (status, onboarding_id),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating onboarding patient status: {e}")
        return False
    finally:
        conn.close()


def calculate_billing_week(task_date_str):
    """Calculate billing week in YYYY-WW format from task date string"""
    try:
        task_date = datetime.strptime(task_date_str, "%Y-%m-%d")
        year = task_date.year
        # Get the Monday of the week containing the task date
        monday = task_date - timedelta(days=task_date.weekday())
        # Calculate ISO week number
        iso_week = task_date.isocalendar()[1]
        return f"{year}-{iso_week:02d}"
    except:
        return None


def get_raw_provider_tasks(start_date, end_date):
    """Get raw provider task data from provider_tasks tables for date range"""
    conn = get_db_connection()

    # Get data from all provider_tasks tables that overlap with date range
    tables_to_query = []

    # Determine which monthly tables to query
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    current_dt = start_dt.replace(day=1)  # Start of month
    while current_dt <= end_dt:
        table_name = f"provider_tasks_{current_dt.year}_{current_dt.month:02d}"
        # Check if table exists
        table_exists = conn.execute(
            """
            SELECT name FROM sqlite_master WHERE type='table' AND name=?
        """,
            (table_name,),
        ).fetchone()
        if table_exists:
            tables_to_query.append(table_name)

        # Move to next month
        if current_dt.month == 12:
            current_dt = current_dt.replace(year=current_dt.year + 1, month=1)
        else:
            current_dt = current_dt.replace(month=current_dt.month + 1)

    all_data = []
    for table_name in tables_to_query:
        try:
            query = f"""
                SELECT
                    provider_task_id,
                    provider_id,
                    provider_name,
                    patient_id,
                    patient_name,
                    task_date,
                    task_description,
                    minutes_of_service,
                    billing_code,
                    billing_code_description,
                    '{table_name}' as source_table
                FROM {table_name}
                WHERE task_date BETWEEN ? AND ?
                  AND task_date IS NOT NULL
                  AND provider_id IS NOT NULL
            """
            df = pd.read_sql_query(query, conn, params=(start_date, end_date))
            if not df.empty:
                all_data.append(df)
        except Exception as e:
            print(f"Error querying {table_name}: {e}")
            continue

    conn.close()

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        return combined_df
    else:
        return pd.DataFrame()


def transform_raw_tasks_to_billing_format(raw_tasks_df):
    """Transform raw provider task data into billing-ready format with default status"""
    if raw_tasks_df.empty:
        return raw_tasks_df

    # Create billing-ready dataframe
    billing_df = raw_tasks_df.copy()

    # Calculate billing week for each task
    billing_df["billing_week"] = billing_df["task_date"].apply(calculate_billing_week)

    # Add billing week start and end dates
    def get_week_dates(billing_week):
        if not billing_week:
            return None, None
        try:
            year, week = billing_week.split("-")
            # Get Monday of the week
            jan_1 = datetime(int(year), 1, 1)
            # Calculate Monday of the given week
            week_start = jan_1 + timedelta(days=(int(week) - 1) * 7)
            week_start = week_start - timedelta(days=week_start.weekday())
            week_end = week_start + timedelta(days=6)
            return week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")
        except:
            return None, None

    billing_df[["week_start_date", "week_end_date"]] = billing_df["billing_week"].apply(
        lambda x: pd.Series(get_week_dates(x))
    )

    # Add billing status columns with default values
    billing_df["billing_status"] = "Not Billed"
    billing_df["is_billed"] = 0
    billing_df["is_invoiced"] = 0
    billing_df["is_claim_submitted"] = 0
    billing_df["is_insurance_processed"] = 0
    billing_df["is_approved_to_pay"] = 0
    billing_df["is_paid"] = 0
    billing_df["is_carried_over"] = 0
    billing_df["provider_paid"] = 0
    billing_df["original_billing_week"] = None
    billing_df["carryover_reason"] = None
    billing_df["billing_notes"] = None
    billing_df["billed_date"] = None
    billing_df["invoiced_date"] = None
    billing_df["claim_submitted_date"] = None
    billing_df["insurance_processed_date"] = None
    billing_df["approved_to_pay_date"] = None
    billing_df["paid_date"] = None

    # Add billing_status_id as a unique identifier
    billing_df["billing_status_id"] = range(1, len(billing_df) + 1)

    # Add timestamps
    billing_df["created_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    billing_df["updated_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return billing_df


def generate_provider_billing_data_on_demand(start_date, end_date):
    """Generate billing-ready data on-demand from raw provider tasks"""
    print(f"Generating billing data for {start_date} to {end_date}")

    # Get raw task data
    raw_tasks = get_raw_provider_tasks(start_date, end_date)

    if raw_tasks.empty:
        print("No raw task data found for the specified date range")
        return pd.DataFrame()

    print(f"Found {len(raw_tasks)} raw task records")

    # Transform to billing format
    billing_data = transform_raw_tasks_to_billing_format(raw_tasks)

    print(f"Transformed {len(billing_data)} records to billing format")
    return billing_data


def get_provider_billing_status_realtime(start_date=None, end_date=None):
    """Get provider billing status with real-time data generation"""
    if not start_date:
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # Generate fresh billing data on-demand
    billing_data = generate_provider_billing_data_on_demand(start_date, end_date)

    # Try to get existing processed data and merge
    try:
        conn = get_db_connection()
        query = """
            SELECT
                billing_status_id,
                provider_task_id,
                provider_id,
                provider_name,
                patient_name,
                task_date,
                billing_week,
                week_start_date,
                week_end_date,
                task_description,
                minutes_of_service,
                billing_code,
                billing_code_description,
                billing_status,
                is_billed,
                is_invoiced,
                is_claim_submitted,
                is_insurance_processed,
                is_approved_to_pay,
                is_paid,
                is_carried_over,
                original_billing_week,
                carryover_reason,
                billing_notes,
                created_date,
                updated_date
            FROM provider_task_billing_status
            WHERE task_date BETWEEN ? AND ?
            ORDER BY billing_week DESC, task_date DESC
        """
        existing_data = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()

        # If we have existing processed data, use it
        if not existing_data.empty:
            print(f"Using {len(existing_data)} existing processed billing records")
            return existing_data
    except Exception as e:
        print(f"Error getting existing billing data: {e}")

    # Otherwise, use generated data
    print("Using generated real-time billing data")
    return billing_data


def get_weekly_billing_summary_realtime():
    """Get weekly billing summary with real-time data generation"""
    # Get last 12 weeks of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    billing_data = get_provider_billing_status_realtime(
        start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    )

    if billing_data.empty:
        return pd.DataFrame()

    # Aggregate by billing week
    weekly_summary = (
        billing_data.groupby("billing_week")
        .agg(
            {
                "billing_status_id": "count",
                "week_start_date": "first",
                "week_end_date": "first",
                "is_billed": "sum",
                "billing_status": lambda x: len(x),
                "created_date": "first",
            }
        )
        .reset_index()
    )

    weekly_summary.columns = [
        "billing_week",
        "total_tasks",
        "week_start_date",
        "week_end_date",
        "total_billed_tasks",
        "report_status",
        "created_date",
    ]

    # Calculate unbilled tasks and percentage
    weekly_summary["total_unbilled_tasks"] = (
        weekly_summary["total_tasks"] - weekly_summary["total_billed_tasks"]
    )
    weekly_summary["billing_percentage"] = (
        weekly_summary["total_billed_tasks"] * 100.0 / weekly_summary["total_tasks"]
    ).round(2)

    # Sort by billing week descending
    weekly_summary = weekly_summary.sort_values("billing_week", ascending=False)

    return weekly_summary.head(12)


# ========================================
# DAILY TASK LOG FUNCTIONS
# ========================================


def get_todays_tasks(user_id: int, role: str) -> list[dict]:
    """
    Returns today's tasks for given user filtered by role
    Uses local timezone (America/Los_Angeles) for "today"
    Only returns tasks with submission_status = 'pending'
    """
    import pytz
    from zoneinfo import ZoneInfo

    # Get today's date in local timezone
    try:
        # Try Python 3.9+ zoneinfo
        local_tz = ZoneInfo("America/Los_Angeles")
    except ImportError:
        # Fallback to pytz
        local_tz = pytz.timezone("America/Los_Angeles")

    today = datetime.now(local_tz).date()
    today_str = today.isoformat()

    conn = get_db_connection()
    try:
        # Determine which table to query based on role
        if role.lower() == "provider":
            table_name = ensure_monthly_provider_tasks_table(conn=conn)
            user_field = "provider_id"
        elif role.lower() == "coordinator":
            table_name = ensure_monthly_coordinator_tasks_table(conn=conn)
            user_field = "coordinator_id"
        else:
            return []

        # Query today's tasks that are still pending
        query = f"""
            SELECT
                task_date,
                patient_id,
                task_type,
                duration_minutes,
                notes,
                task_description,
                billing_code,
                submission_status
            FROM {table_name}
            WHERE {user_field} = ?
            AND date(task_date) = date(?)
            AND (submission_status IS NULL OR submission_status = 'pending')
            ORDER BY task_date DESC
        """

        result = conn.execute(query, (user_id, today_str)).fetchall()

        tasks = []
        for row in result:
            task_dict = dict(row)

            # Resolve patient name from patient_id
            if task_dict.get("patient_id"):
                try:
                    patient = conn.execute(
                        """
                        SELECT first_name, last_name
                        FROM patients
                        WHERE patient_id = ?
                        LIMIT 1
                    """,
                        (task_dict["patient_id"],),
                    ).fetchone()

                    if patient:
                        task_dict["patient_name"] = (
                            f"{patient['first_name'] or ''} {patient['last_name'] or ''}".strip()
                        )
                    else:
                        task_dict["patient_name"] = str(task_dict["patient_id"])
                except Exception:
                    task_dict["patient_name"] = str(task_dict["patient_id"])
            else:
                task_dict["patient_name"] = "Unknown Patient"

            tasks.append(task_dict)

        return tasks

    finally:
        conn.close()


def submit_daily_tasks(user_id: int, role: str) -> bool:
    """
    Marks today's tasks as submitted (kept as 'pending' status to allow future edits).
    Returns True if successful.
    Note: Status remains 'pending' indefinitely so coordinators can always edit their tasks.
    """
    import pytz
    from zoneinfo import ZoneInfo

    # Get today's date in local timezone
    try:
        # Try Python 3.9+ zoneinfo
        local_tz = ZoneInfo("America/Los_Angeles")
    except ImportError:
        # Fallback to pytz
        local_tz = pytz.timezone("America/Los_Angeles")

    today = datetime.now(local_tz).date()
    today_str = today.isoformat()

    conn = get_db_connection()
    try:
        # Determine which table to update based on role
        if role.lower() == "provider":
            table_name = ensure_monthly_provider_tasks_table(conn=conn)
            user_field = "provider_id"
        elif role.lower() == "coordinator":
            table_name = ensure_monthly_coordinator_tasks_table(conn=conn)
            user_field = "coordinator_id"
        else:
            return False

        # Set status to 'pending' (not 'submitted') so tasks remain editable
        # Also update the timestamp to record when the "submit" action was taken
        query = f"""
            UPDATE {table_name}
            SET submission_status = 'pending',
                imported_at = CURRENT_TIMESTAMP
            WHERE {user_field} = ?
            AND date(task_date) = date(?)
            AND (submission_status IS NULL OR submission_status = 'pending')
        """

        cursor = conn.execute(query, (user_id, today_str))
        conn.commit()

        return cursor.rowcount > 0

    except Exception as e:
        print(f"Error submitting daily tasks: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def update_task_details(task_id: int, role: str, updates: dict) -> bool:
    """
    Updates task details (minutes, task_type, notes)
    Only allowed for 'pending' status tasks
    """
    conn = get_db_connection()
    try:
        # Determine which table to update based on role
        if role.lower() == "provider":
            table_name = ensure_monthly_provider_tasks_table(conn=conn)
            id_field = "provider_task_id"
        elif role.lower() == "coordinator":
            table_name = ensure_monthly_coordinator_tasks_table(conn=conn)
            id_field = "coordinator_task_id"
        else:
            return False

        # Build update query dynamically
        update_fields = []
        params = []

        allowed_fields = [
            "duration_minutes",
            "task_type",
            "notes",
            "minutes_of_service",
            "location_type",
            "patient_type",
        ]
        for field, value in updates.items():
            if field in allowed_fields:
                if field == "duration_minutes":
                    update_fields.append("duration_minutes = ?")
                    update_fields.append("minutes_of_service = ?")  # Update both fields
                    params.extend([value, value])
                else:
                    update_fields.append(f"{field} = ?")
                    params.append(value)

        if not update_fields:
            return False

        # Add timestamp update
        update_fields.append("imported_at = CURRENT_TIMESTAMP")
        params.append(task_id)

        query = f"""
            UPDATE {table_name}
            SET {', '.join(update_fields)}
            WHERE {id_field} = ?
            AND (submission_status IS NULL OR submission_status = 'pending')
        """

        cursor = conn.execute(query, params)
        conn.commit()

        return cursor.rowcount > 0

    except Exception as e:
        print(f"Error updating task details: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


# ============================================================================
# WORKFLOW STATE UPDATE FUNCTIONS - Phase 2
# ============================================================================
# These functions manage the state transitions for billing and payroll workflows
# ============================================================================


def mark_provider_tasks_as_billed(billing_status_ids, user_id):
    """
    Mark selected provider tasks as billed in the provider_task_billing_status table.

    Args:
        billing_status_ids: List of billing_status_id values to mark as billed
        user_id: ID of user marking as billed (must be Harpreet/Admin or Justin)

    Returns:
        Tuple (success: bool, message: str, updated_count: int)

    Updates:
        - is_billed = TRUE
        - billed_date = CURRENT_TIMESTAMP
        - billed_by = user_id
        - billing_status = 'Billed'
        - updated_date = CURRENT_TIMESTAMP
    """
    if not billing_status_ids:
        return (False, "No billing IDs provided", 0)

    conn = get_db_connection()
    try:
        # Build placeholders for SQL IN clause
        placeholders = ",".join("?" * len(billing_status_ids))
        params = [user_id] + billing_status_ids

        query = f"""
            UPDATE provider_task_billing_status
            SET
                is_billed = TRUE,
                billed_date = CURRENT_TIMESTAMP,
                billed_by = ?,
                billing_status = 'Billed',
                updated_date = CURRENT_TIMESTAMP
            WHERE billing_status_id IN ({placeholders})
            AND is_billed = FALSE
        """

        cursor = conn.execute(query, params)
        conn.commit()

        updated_count = cursor.rowcount
        message = f"Successfully marked {updated_count} provider tasks as billed"
        return (True, message, updated_count)

    except Exception as e:
        conn.rollback()
        message = f"Error marking provider tasks as billed: {str(e)}"
        return (False, message, 0)
    finally:
        conn.close()


def mark_coordinator_tasks_as_billed(summary_ids, user_id):
    """
    Mark selected coordinator tasks as billed in the coordinator_monthly_summary table.

    Args:
        summary_ids: List of summary_id values to mark as billed
        user_id: ID of user marking as billed (must be Harpreet/Admin or Justin)

    Returns:
        Tuple (success: bool, message: str, updated_count: int)

    Updates:
        - is_billed = TRUE
        - billed_date = CURRENT_TIMESTAMP
        - billed_by = user_id
        - billing_status = 'Billed'
        - updated_date = CURRENT_TIMESTAMP
    """
    if not summary_ids:
        return (False, "No summary IDs provided", 0)

    conn = get_db_connection()
    try:
        # Build placeholders for SQL IN clause
        placeholders = ",".join("?" * len(summary_ids))
        params = [user_id] + summary_ids

        query = f"""
            UPDATE coordinator_monthly_summary
            SET
                is_billed = TRUE,
                billed_date = CURRENT_TIMESTAMP,
                billed_by = ?,
                billing_status = 'Billed',
                updated_date = CURRENT_TIMESTAMP
            WHERE summary_id IN ({placeholders})
            AND is_billed = FALSE
        """

        cursor = conn.execute(query, params)
        conn.commit()

        updated_count = cursor.rowcount
        message = f"Successfully marked {updated_count} coordinator tasks as billed"
        return (True, message, updated_count)

    except Exception as e:
        conn.rollback()
        message = f"Error marking coordinator tasks as billed: {str(e)}"
        return (False, message, 0)
    finally:
        conn.close()


def recalculate_coordinator_monthly_summary(year, month, coordinator_id=None):
    """
    Recalculate coordinator_monthly_summary for a specific month/year after task edits.
    This should be called after tasks are edited in the Task Review to update billing summaries.

    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
        coordinator_id: Optional coordinator ID to filter. If None, recalculates for all coordinators.

    Returns:
        Tuple (success: bool, message: str, affected_count: int)
    """
    conn = get_db_connection()
    try:
        coord_table = f"coordinator_tasks_{year}_{str(month).zfill(2)}"
        summary_table = "coordinator_monthly_summary"

        # Check if the coordinator tasks table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
            (coord_table,),
        )
        if not cursor.fetchone():
            return (False, f"Coordinator table {coord_table} does not exist", 0)

        # Build WHERE clause for optional coordinator_id filter
        where_clause = ""
        params = []
        if coordinator_id:
            where_clause = "AND ct.coordinator_id = ?"
            params.append(coordinator_id)

        # Delete existing summary records for this month/year (and coordinator if specified)
        delete_params = [year, month]
        if coordinator_id:
            delete_params.append(coordinator_id)

        delete_sql = f"""
            DELETE FROM {summary_table}
            WHERE year = ? AND month = ?
        """
        if coordinator_id:
            delete_sql += " AND coordinator_id = ?"

        conn.execute(delete_sql, delete_params)

        # Re-insert aggregated data from coordinator tasks
        insert_sql = f"""
            INSERT INTO {summary_table} (
                coordinator_id, coordinator_name, patient_id, patient_name,
                year, month, month_start_date, month_end_date,
                total_tasks_completed, total_time_spent_minutes,
                billing_code, billing_code_description,
                billing_status, is_billed, billed_by,
                created_date, updated_date
            )
            SELECT
                ct.coordinator_id,
                ct.coordinator_name,
                ct.patient_id,
                ct.patient_id as patient_name,
                ? as year,
                ? as month,
                DATE(? || '-' || PRINTF('%02d', ?) || '-01') as month_start_date,
                DATE(? || '-' || PRINTF('%02d', ?) || '-01', '+1 month', '-1 day') as month_end_date,
                COUNT(*) as total_tasks_completed,
                CAST(SUM(COALESCE(ct.duration_minutes, 0)) AS INTEGER) as total_time_spent_minutes,
                CASE
                    WHEN SUM(COALESCE(ct.duration_minutes, 0)) >= 50 THEN '99492'
                    WHEN SUM(COALESCE(ct.duration_minutes, 0)) >= 20 THEN '99491'
                    ELSE '99490'
                END as billing_code,
                CASE
                    WHEN SUM(COALESCE(ct.duration_minutes, 0)) >= 50 THEN 'Care Management - Complex'
                    WHEN SUM(COALESCE(ct.duration_minutes, 0)) >= 20 THEN 'Care Management - Moderate'
                    ELSE 'Care Management - Basic'
                END as billing_code_description,
                'Pending' as billing_status,
                FALSE as is_billed,
                NULL as billed_by,
                CURRENT_TIMESTAMP as created_date,
                CURRENT_TIMESTAMP as updated_date
            FROM {coord_table} ct
            WHERE ct.coordinator_id IS NOT NULL
                AND ct.patient_id IS NOT NULL
                AND TRIM(ct.patient_id) != ''
                {where_clause}
            GROUP BY ct.coordinator_id, ct.coordinator_name, ct.patient_id
        """

        insert_params = [year, month, year, month, year, month] + params
        cursor = conn.execute(insert_sql, insert_params)
        conn.commit()

        affected_count = cursor.rowcount
        message = f"Successfully recalculated {affected_count} coordinator summary records for {year}-{month:02d}"
        return (True, message, affected_count)

    except Exception as e:
        conn.rollback()
        message = f"Error recalculating coordinator monthly summary: {str(e)}"
        return (False, message, 0)
    finally:
        conn.close()


def recalculate_provider_monthly_summary(year, month, provider_id=None):
    """
    Recalculate provider_monthly_summary for a specific month/year after task edits.
    This should be called after tasks are edited in the Task Review to update summaries.

    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
        provider_id: Optional provider ID to filter. If None, recalculates for all providers.

    Returns:
        Tuple (success: bool, message: str, affected_count: int)
    """
    conn = get_db_connection()
    try:
        provider_table = f"provider_tasks_{year}_{str(month).zfill(2)}"
        summary_table = "provider_monthly_summary"

        # Check if the provider tasks table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
            (provider_table,),
        )
        if not cursor.fetchone():
            return (False, f"Provider table {provider_table} does not exist", 0)

        # Build WHERE clause for optional provider_id filter
        where_clause = ""
        params = []
        if provider_id:
            where_clause = "AND pt.provider_id = ?"
            params.append(provider_id)

        # Delete existing summary records for this month/year (and provider if specified)
        delete_params = [year, month]
        if provider_id:
            delete_params.append(provider_id)

        delete_sql = f"""
            DELETE FROM {summary_table}
            WHERE year = ? AND month = ?
        """
        if provider_id:
            delete_sql += " AND provider_id = ?"

        conn.execute(delete_sql, delete_params)

        # Re-insert aggregated data from provider tasks
        insert_sql = f"""
            INSERT INTO {summary_table} (
                provider_id, provider_name, month, year,
                total_tasks_completed, total_time_spent_minutes,
                created_date, updated_date
            )
            SELECT
                pt.provider_id,
                pt.provider_name,
                ? as month,
                ? as year,
                COUNT(*) as total_tasks_completed,
                CAST(SUM(COALESCE(pt.minutes_of_service, 0)) AS INTEGER) as total_time_spent_minutes,
                CURRENT_TIMESTAMP as created_date,
                CURRENT_TIMESTAMP as updated_date
            FROM {provider_table} pt
            WHERE pt.provider_id IS NOT NULL
                {where_clause}
            GROUP BY pt.provider_id, pt.provider_name
        """

        insert_params = [month, year] + params
        cursor = conn.execute(insert_sql, insert_params)
        conn.commit()

        affected_count = cursor.rowcount
        message = f"Successfully recalculated {affected_count} provider summary records for {year}-{month:02d}"
        return (True, message, affected_count)

    except Exception as e:
        conn.rollback()
        message = f"Error recalculating provider monthly summary: {str(e)}"
        return (False, message, 0)
    finally:
        conn.close()


def approve_provider_payroll(payroll_ids, user_id):
    """
    Approve selected provider payroll records (Justin only).

    Args:
        payroll_ids: List of payroll_id values to approve
        user_id: ID of user approving (must be Justin)

    Returns:
        Tuple (success: bool, message: str, updated_count: int)

    Updates:
        - is_approved = TRUE
        - approved_date = CURRENT_TIMESTAMP
        - approved_by = user_id
        - payroll_status = 'Approved'
        - updated_date = CURRENT_TIMESTAMP
    """
    if not payroll_ids:
        return (False, "No payroll IDs provided", 0)

    conn = get_db_connection()
    try:
        # Build placeholders for SQL IN clause
        placeholders = ",".join("?" * len(payroll_ids))
        params = [user_id] + payroll_ids

        query = f"""
            UPDATE provider_weekly_payroll_status
            SET
                is_approved = TRUE,
                approved_date = CURRENT_TIMESTAMP,
                approved_by = ?,
                payroll_status = 'Approved',
                updated_date = CURRENT_TIMESTAMP
            WHERE payroll_id IN ({placeholders})
            AND is_approved = FALSE
        """

        cursor = conn.execute(query, params)
        conn.commit()

        updated_count = cursor.rowcount
        message = f"Successfully approved {updated_count} payroll records"
        return (True, message, updated_count)

    except Exception as e:
        conn.rollback()
        message = f"Error approving payroll: {str(e)}"
        return (False, message, 0)
    finally:
        conn.close()


def mark_provider_payroll_as_paid(
    payroll_ids, user_id, payment_method=None, payment_reference=None
):
    """
    Mark selected provider payroll records as paid (Justin only).

    Args:
        payroll_ids: List of payroll_id values to mark as paid
        user_id: ID of user processing payment (must be Justin)
        payment_method: Optional payment method (e.g., 'ACH', 'Check', 'Direct Deposit')
        payment_reference: Optional reference info (e.g., Check #, ACH ID)

    Returns:
        Tuple (success: bool, message: str, updated_count: int)

    Updates:
        - is_paid = TRUE
        - paid_date = CURRENT_TIMESTAMP
        - paid_by = user_id
        - payroll_status = 'Paid'
        - payment_method = payment_method (if provided)
        - payment_reference = payment_reference (if provided)
        - updated_date = CURRENT_TIMESTAMP
    """
    if not payroll_ids:
        return (False, "No payroll IDs provided", 0)

    conn = get_db_connection()
    try:
        # Build placeholders for SQL IN clause
        placeholders = ",".join("?" * len(payroll_ids))

        # Build update clause based on whether optional fields are provided
        update_parts = [
            "is_paid = TRUE",
            "paid_date = CURRENT_TIMESTAMP",
            "paid_by = ?",
            "payroll_status = 'Paid'",
            "updated_date = CURRENT_TIMESTAMP",
        ]

        params = [user_id]

        # Add optional fields if provided
        if payment_method:
            update_parts.append("payment_method = ?")
            params.append(payment_method)

        if payment_reference:
            update_parts.append("payment_reference = ?")
            params.append(payment_reference)

        # Build placeholders for SQL IN clause
        placeholders = ",".join("?" * len(payroll_ids))

        # Add payroll IDs to params for WHERE clause
        params.extend(payroll_ids)

        update_clause = ", ".join(update_parts)

        query = f"""
            UPDATE provider_weekly_payroll_status
            SET {update_clause}
            WHERE payroll_id IN ({placeholders})
            AND is_paid = FALSE
        """

        cursor = conn.execute(query, params)
        conn.commit()

        updated_count = cursor.rowcount
        message = f"Successfully marked {updated_count} payroll records as paid"
        return (True, message, updated_count)

    except Exception as e:
        conn.rollback()
        message = f"Error marking payroll as paid: {str(e)}"
        return (False, message, 0)
    finally:
        conn.close()


def update_billing_company(billing_status_ids, billing_company, user_id):
   """
   Update billing company for selected provider tasks in provider_task_billing_status table.

   Args:
       billing_status_ids: List of billing_status_id values to update
       billing_company: Name of the Medicare billing company
       user_id: ID of user making the change (must be Harpreet/Admin or Justin)

   Returns:
       Tuple (success: bool, message: str, updated_count: int)

   Updates:
       - billing_company = billing_company
       - updated_date = CURRENT_TIMESTAMP
   """
   if not billing_status_ids:
       return (False, "No billing IDs provided", 0)
   
   if not billing_company or not billing_company.strip():
       return (False, "Billing company name cannot be empty", 0)

   conn = get_db_connection()
   try:
       # Build placeholders for SQL IN clause
       placeholders = ",".join("?" * len(billing_status_ids))
       params = [billing_company] + billing_status_ids
       
       query = f"""
           UPDATE provider_task_billing_status
           SET
               billing_company = ?,
               updated_date = CURRENT_TIMESTAMP
           WHERE billing_status_id IN ({placeholders})
       """
       
       cursor = conn.execute(query, params)
       conn.commit()
       
       updated_count = cursor.rowcount
       message = f"Successfully updated billing company for {updated_count} tasks to '{billing_company}'"
       return (True, message, updated_count)
       
   except Exception as e:
       conn.rollback()
       message = f"Error updating billing company: {str(e)}"
       return (False, message, 0)
   finally:
       conn.close()


def refresh_all_summaries(year, month):
    """
    Refresh all summary tables for a given month.
    This is the central function to call after tasks are saved/edited.
    
    Updates:
    - provider_monthly_summary
    - coordinator_monthly_summary
    
    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
        
    Returns:
        Tuple (success: bool, message: str, affected_count: int)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    conn = get_db_connection()
    try:
        total_affected = 0
        
        # 1. Recalculate provider monthly summary
        try:
            success, msg, count = recalculate_provider_monthly_summary(year, month)
            if success:
                total_affected += count
                logger.info(f'Provider monthly summary: {msg}')
        except Exception as e:
            logger.warning(f'Could not recalculate provider monthly summary: {e}')
        
        # 2. Recalculate coordinator monthly summary
        try:
            success, msg, count = recalculate_coordinator_monthly_summary(year, month)
            if success:
                total_affected += count
                logger.info(f'Coordinator monthly summary: {msg}')
        except Exception as e:
            logger.warning(f'Could not recalculate coordinator monthly summary: {e}')
        
        return (True, f'Refreshed summaries for {year}-{str(month).zfill(2)}', total_affected)
        
    except Exception as e:
        logger.error(f'Error refreshing summaries: {e}')
        return (False, f'Error: {str(e)}', 0)
    finally:
        conn.close()



# =============================================================================
# FACILITY REVIEW DASHBOARD FUNCTIONS
# =============================================================================

ROLE_FACILITY = 42


def get_user_facility(user_id):
    """
    Get the primary facility assigned to a user.
    For facility users (role 42), derives facility_id from username.
    For other users, checks user_facility_assignments.

    Args:
        user_id: User ID to look up

    Returns:
        facility_id or None if not assigned
    """
    conn = get_db_connection()
    try:
        # Check if user is a facility user (role 42)
        role_check = conn.execute("""
            SELECT 1 FROM user_roles WHERE user_id = ? AND role_id = 42
        """, (user_id,)).fetchone()

        if role_check:
            # Facility user: derive facility from username
            user_info = conn.execute("""
                SELECT username FROM users WHERE user_id = ?
            """, (user_id,)).fetchone()

            if user_info and user_info['username']:
                # Username format: facilityname_facility
                # Extract facility name by removing '_facility' suffix
                username = user_info['username']
                if username.endswith('_facility'):
                    facility_slug = username[:-9]  # Remove '_facility'
                    # Find facility by matching slugified name
                    facility = conn.execute("""
                        SELECT facility_id FROM facilities
                        WHERE LOWER(REPLACE(facility_name, ' ', '_')) = ?
                        LIMIT 1
                    """, (facility_slug,)).fetchone()
                    if facility:
                        return facility['facility_id']

        # Non-facility user: check user_facility_assignments
        result = conn.execute("""
            SELECT facility_id FROM user_facility_assignments
            WHERE user_id = ? AND assignment_type = 'primary'
            LIMIT 1
        """, (user_id,)).fetchone()
        return result['facility_id'] if result else None
    except Exception as e:
        print(f"Error getting user facility: {e}")
        return None
    finally:
        conn.close()


def get_user_facilities(user_id):
    """
    Get all facilities assigned to a user.
    
    Args:
        user_id: User ID to look up
        
    Returns:
        List of facility dicts with facility_id, facility_name, assignment_type
    """
    conn = get_db_connection()
    try:
        results = conn.execute("""
            SELECT f.facility_id, f.facility_name, ufa.assignment_type
            FROM user_facility_assignments ufa
            JOIN facilities f ON ufa.facility_id = f.facility_id
            WHERE ufa.user_id = ?
            ORDER BY ufa.assignment_type = 'primary' DESC, f.facility_name
        """, (user_id,)).fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting user facilities: {e}")
        return []
    finally:
        conn.close()


def assign_user_to_facility(user_id, facility_id, assignment_type='primary'):
    """
    Assign a user to a facility.
    
    Args:
        user_id: User ID
        facility_id: Facility ID
        assignment_type: 'primary' or 'secondary'
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO user_facility_assignments 
            (user_id, facility_id, assignment_type, assigned_date)
            VALUES (?, ?, ?, datetime('now'))
        """, (user_id, facility_id, assignment_type))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error assigning user to facility: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def remove_user_from_facility(user_id, facility_id):
    """
    Remove a user's facility assignment.
    
    Args:
        user_id: User ID
        facility_id: Facility ID
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_db_connection()
    try:
        conn.execute("""
            DELETE FROM user_facility_assignments
            WHERE user_id = ? AND facility_id = ?
        """, (user_id, facility_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error removing user from facility: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_patients_by_facility(facility_id, status_filter=None, search_term=None):
    """
    Get all patients assigned to a facility.
    
    Args:
        facility_id: Facility ID
        status_filter: Optional list of statuses to filter by
        search_term: Optional search term for patient name
        
    Returns:
        List of patient dicts
    """
    conn = get_db_connection()
    try:
        query = """
            SELECT 
                p.patient_id,
                p.first_name,
                p.last_name,
                p.date_of_birth,
                p.phone_primary,
                p.status,
                p.facility as facility_name,
                p.assigned_facility_id,
                p.last_visit_date,
                p.goc_value,
                p.goals_of_care,
                p.code_status,
                p.cognitive_function,
                p.functional_status,
                p.mental_health_concerns,
                p.subjective_risk_level,
                p.active_concerns,
                p.active_specialists,
                p.er_count_1yr,
                p.hospitalization_count_1yr,
                p.labs_notes,
                p.imaging_notes,
                p.general_notes,
                p.provider_name as assigned_provider,
                p.coordinator_name as assigned_coordinator
            FROM patient_panel p
            WHERE p.facility = (
                SELECT facility_name FROM facilities WHERE facility_id = ?
               )
        """
        params = [facility_id]
        
        if status_filter:
            placeholders = ','.join(['?' for _ in status_filter])
            query += f" AND p.status IN ({placeholders})"
            params.extend(status_filter)
        
        if search_term:
            query += """ AND (
                LOWER(p.first_name) LIKE ? OR 
                LOWER(p.last_name) LIKE ? OR
                LOWER(p.patient_id) LIKE ?
            )"""
            search_pattern = f"%{search_term.lower()}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        query += " ORDER BY p.last_name, p.first_name"
        
        results = conn.execute(query, params).fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting patients by facility: {e}")
        return []
    finally:
        conn.close()


def get_facility_pending_intake_patients(facility_id):
    """
    Get patients at facility who need intake kickoff.
    Statuses: Pending, Referral Received, New, or intake_call_completed = 0
    
    Args:
        facility_id: Facility ID
        
    Returns:
        List of patient dicts
    """
    conn = get_db_connection()
    try:
        results = conn.execute("""
            SELECT 
                p.patient_id,
                p.first_name,
                p.last_name,
                p.date_of_birth,
                p.phone_primary,
                p.status,
                p.facility,
                p.intake_call_completed,
                p.emed_chart_created,
                p.created_date,
                CASE 
                    WHEN op.onboarding_id IS NOT NULL THEN 'In Progress'
                    ELSE 'Pending'
                END as onboarding_status,
                op.onboarding_id,
                op.stage1_complete,
                op.stage2_complete,
                op.stage3_complete,
                op.stage4_complete,
                op.stage5_complete
            FROM patient_panel p
            LEFT JOIN onboarding_patients op ON p.patient_id = op.patient_id
            WHERE (p.assigned_facility_id = ? OR p.facility = (
                SELECT facility_name FROM facilities WHERE facility_id = ?
            ))
            AND (
                p.status IN ('Pending', 'Referral Received', 'New', 'Onboarding')
                OR p.intake_call_completed = 0
                OR p.emed_chart_created = 0
                OR op.onboarding_id IS NOT NULL
            )
            ORDER BY p.created_date DESC
        """, (facility_id, facility_id)).fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting facility pending intake patients: {e}")
        return []
    finally:
        conn.close()


def get_facility_intake_history(facility_id, days_back=30):
    """
    Get intake submission history for a facility.
    
    Args:
        facility_id: Facility ID
        days_back: Number of days to look back
        
    Returns:
        List of intake submission dicts
    """
    conn = get_db_connection()
    try:
        results = conn.execute("""
            SELECT 
                op.onboarding_id,
                op.first_name,
                op.last_name,
                op.date_of_birth,
                op.intake_submitted_date,
                op.intake_priority,
                op.facility_notes,
                op.stage1_complete,
                op.stage2_complete,
                op.stage3_complete,
                op.stage4_complete,
                op.stage5_complete,
                op.completed_date,
                u.full_name as submitted_by_name,
                CASE 
                    WHEN op.completed_date IS NOT NULL THEN 'Complete'
                    WHEN op.stage5_complete = 1 THEN 'Stage 5'
                    WHEN op.stage4_complete = 1 THEN 'Stage 4'
                    WHEN op.stage3_complete = 1 THEN 'Stage 3'
                    WHEN op.stage2_complete = 1 THEN 'Stage 2'
                    WHEN op.stage1_complete = 1 THEN 'Stage 1'
                    ELSE 'Pending'
                END as current_stage
            FROM onboarding_patients op
            LEFT JOIN users u ON op.submitted_by_facility_user_id = u.user_id
            WHERE op.source_facility_id = ?
            AND op.intake_submitted_date >= datetime('now', ?)
            ORDER BY op.intake_submitted_date DESC
        """, (facility_id, f'-{days_back} days')).fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting facility intake history: {e}")
        return []
    finally:
        conn.close()


def submit_facility_intake(facility_user_id, facility_id, patient_data, 
                          priority='Normal', notes=None):
    """
    Submit a new patient intake from a facility.
    Creates onboarding workflow and returns onboarding_id.
    
    Args:
        facility_user_id: User ID of facility staff submitting
        facility_id: Facility ID
        patient_data: Dict with first_name, last_name, date_of_birth, etc.
        priority: 'Normal', 'High', or 'Urgent'
        notes: Additional notes for onboarding team
        
    Returns:
        Dict with success status and onboarding_id or error message
    """
    conn = get_db_connection()
    try:
        # Create onboarding patient record
        cursor = conn.execute("""
            INSERT INTO onboarding_patients (
                first_name, last_name, date_of_birth,
                phone_primary, email, gender,
                insurance_provider, policy_number, group_number,
                source_facility_id,
                submitted_by_facility_user_id,
                intake_priority,
                facility_notes,
                intake_submitted_date,
                patient_status,
                facility_assignment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 'Active', ?)
        """, (
            patient_data.get('first_name'),
            patient_data.get('last_name'),
            patient_data.get('date_of_birth'),
            patient_data.get('phone_primary'),
            patient_data.get('email'),
            patient_data.get('gender'),
            patient_data.get('insurance_provider'),
            patient_data.get('policy_number'),
            patient_data.get('group_number'),
            facility_id,
            facility_user_id,
            priority,
            notes,
            patient_data.get('facility_name', '')
        ))
        
        onboarding_id = cursor.lastrowid
        
        # Create workflow steps/tasks if workflow_steps table has entries for onboarding
        # (Using template_id 14 for POT_Patient_Onboarding)
        workflow_steps = conn.execute("""
            SELECT step_id, step_order, task_name FROM workflow_steps
            WHERE template_id = 14 ORDER BY step_order
        """).fetchall()
        
        for step in workflow_steps:
            stage = ((step['step_order'] - 1) // 3) + 1
            if step['step_order'] > 15:
                stage = 5
                
            conn.execute("""
                INSERT INTO onboarding_tasks (
                    onboarding_id, workflow_step_id, task_name, task_stage,
                    task_order, status, created_date, updated_date
                ) VALUES (?, ?, ?, ?, ?, 'Pending', datetime('now'), datetime('now'))
            """, (
                onboarding_id,
                step['step_id'],
                step['task_name'],
                stage,
                step['step_order']
            ))
        
        # Log the intake submission
        conn.execute("""
            INSERT INTO facility_intake_audit (
                facility_user_id, facility_id, onboarding_id,
                patient_name, action, notes
            ) VALUES (?, ?, ?, ?, 'SUBMITTED', ?)
        """, (
            facility_user_id,
            facility_id,
            onboarding_id,
            f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}",
            notes
        ))
        
        conn.commit()
        return {
            'success': True,
            'onboarding_id': onboarding_id,
            'message': f"Intake submitted successfully. Onboarding ID: {onboarding_id}"
        }
        
    except Exception as e:
        print(f"Error submitting facility intake: {e}")
        conn.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        conn.close()


def update_facility_intake_documents(onboarding_id, document_paths):
    """
    Update document paths for a facility intake.
    
    Args:
        onboarding_id: Onboarding ID
        document_paths: Dict with keys: insurance_card_front_path, 
                       insurance_card_back_path, id_document_path
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE onboarding_patients SET
                insurance_card_front_path = ?,
                insurance_card_back_path = ?,
                id_document_path = ?,
                updated_date = datetime('now')
            WHERE onboarding_id = ?
        """, (
            document_paths.get('insurance_card_front_path'),
            document_paths.get('insurance_card_back_path'),
            document_paths.get('id_document_path'),
            onboarding_id
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating facility intake documents: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_patient_workflow_history(patient_id):
    """
    Get workflow history for a patient.
    
    Args:
        patient_id: Patient ID
        
    Returns:
        List of workflow instance dicts
    """
    conn = get_db_connection()
    try:
        results = conn.execute("""
            SELECT 
                wi.instance_id,
                wi.template_name,
                wi.workflow_status,
                wi.current_step,
                wi.created_at,
                wi.completed_at,
                wi.coordinator_name,
                wi.step1_date,
                wi.step1_complete,
                wi.step1_notes,
                wi.step2_date,
                wi.step2_complete,
                wi.step2_notes,
                wi.step3_date,
                wi.step3_complete,
                wi.step3_notes,
                wi.step4_date,
                wi.step4_complete,
                wi.step4_notes,
                wi.step5_date,
                wi.step5_complete,
                wi.step5_notes,
                wi.step6_date,
                wi.step6_complete,
                wi.step6_notes
            FROM workflow_instances wi
            WHERE wi.patient_id = ?
            ORDER BY wi.created_at DESC
        """, (patient_id,)).fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting patient workflow history: {e}")
        return []
    finally:
        conn.close()


def get_latest_provider_visit(patient_id):
    """
    Get the most recent provider visit for a patient.
    
    Args:
        patient_id: Patient ID
        
    Returns:
        Provider visit dict or None
    """
    conn = get_db_connection()
    try:
        # Get list of provider task tables
        tables = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name LIKE 'provider_tasks_20%'
            ORDER BY name DESC
        """).fetchall()
        
        latest_visit = None
        
        for table in tables:
            table_name = table[0]
            try:
                result = conn.execute(f"""
                    SELECT 
                        '{table_name}' as source_table,
                        patient_id,
                        date as visit_date,
                        service_type,
                        task_description as notes,
                        provider_id,
                        minutes_of_service as duration_minutes,
                        billing_code,
                        location_type,
                        patient_type
                    FROM {table_name}
                    WHERE patient_id = ?
                    ORDER BY date DESC
                    LIMIT 1
                """, (patient_id,)).fetchone()
                
                if result:
                    visit_dict = dict(result)
                    # Get provider name
                    if visit_dict.get('provider_id'):
                        provider = conn.execute("""
                            SELECT full_name FROM users WHERE user_id = ?
                        """, (visit_dict['provider_id'],)).fetchone()
                        if provider:
                            visit_dict['provider_name'] = provider['full_name']
                    
                    if not latest_visit or (visit_dict.get('visit_date') and 
                        (latest_visit.get('visit_date') is None or visit_dict['visit_date'] > latest_visit.get('visit_date'))):
                        latest_visit = visit_dict
                        
            except Exception as e:
                continue
        
        return latest_visit
    except Exception as e:
        print(f"Error getting latest provider visit: {e}")
        return None
    finally:
        conn.close()


def get_all_facilities():
    """
    Get all facilities for dropdown selection.
    
    Returns:
        List of facility dicts
    """
    conn = get_db_connection()
    try:
        results = conn.execute("""
            SELECT facility_id, facility_name, address, phone, email
            FROM facilities
            ORDER BY facility_name
        """).fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting all facilities: {e}")
        return []
    finally:
        conn.close()


def log_facility_audit(facility_user_id, facility_id, action, onboarding_id=None, 
                      patient_name=None, notes=None):
    """
    Log an audit entry for facility actions.
    
    Args:
        facility_user_id: User ID
        facility_id: Facility ID
        action: Action type (SUBMITTED, VIEWED, etc.)
        onboarding_id: Optional onboarding ID
        patient_name: Optional patient name
        notes: Optional notes
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO facility_intake_audit (
                facility_user_id, facility_id, onboarding_id,
                patient_name, action, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (facility_user_id, facility_id, onboarding_id, patient_name, action, notes))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error logging facility audit: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
