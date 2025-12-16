import calendar
import glob
import os
import re
import sqlite3
from datetime import datetime

import pandas as pd

DB_PATH = "production.db"
CSV_DIR = "downloads"  # Points to d:\Git\myhealthteam2\Dev\downloads


def get_db():
    return sqlite3.connect(DB_PATH)


def create_provider_table(conn, year, month):
    table_name = f"provider_tasks_{year}_{str(month).zfill(2)}"
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
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
            is_deleted INTEGER DEFAULT 0,
            UNIQUE(provider_id, patient_id, task_date, task_description)
        )
    """)
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_provider ON {table_name}(provider_id)"
    )
    return table_name


def create_coordinator_table(conn, year, month):
    table_name = f"coordinator_tasks_{year}_{str(month).zfill(2)}"
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            coordinator_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            coordinator_id INTEGER,
            coordinator_name TEXT,
            patient_id TEXT, -- Acts as Patient Name for now based on Dashboard usage
            task_date DATE,
            duration_minutes REAL,
            task_type TEXT,
            notes TEXT,
            source_system TEXT DEFAULT 'CSV_IMPORT',
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(coordinator_id, patient_id, task_date, task_type)
        )
    """)
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_coordinator ON {table_name}(coordinator_id)"
    )
    return table_name


def process_minutes_range(minutes_str):
    """Extract minimum minutes from range format (e.g., '40-49' → 40)"""
    if not minutes_str or minutes_str == "0":
        return 0

    # Handle range format like "40-49" - just use the minimum
    if "-" in str(minutes_str):
        try:
            parts = str(minutes_str).split("-")
            if len(parts) == 2:
                return int(parts[0])  # Use minimum value
        except (ValueError, IndexError):
            pass

    # Handle single number
    try:
        return int(float(minutes_str))
    except (ValueError, TypeError):
        return 0


def auto_assign_billing_code(service_description, minutes, billing_codes_map):
    """Auto-assign billing code based on service description and minutes"""
    if not service_description:
        return "PENDING"

    # Clean up service description for matching
    clean_description = service_description.replace(" mins", "")

    # Look for exact match in billing codes
    if clean_description in billing_codes_map:
        candidates = billing_codes_map[clean_description]
        if candidates:
            # For now, return the first billing code that matches
            # In future, could select based on minutes range
            return candidates[0]["billing_code"]

    # If no exact match, try partial matching
    for task_desc, candidates in billing_codes_map.items():
        if task_desc in clean_description or clean_description in task_desc:
            if candidates:
                return candidates[0]["billing_code"]

    return "PENDING"


def normalize_name_key(name):
    """Normalize name for matching: remove punctuation, titles, extra spaces"""
    if not name:
        return ""
    # Uppercase
    name = name.upper()
    # Remove punctuation
    for char in [",", ".", "-", "_"]:
        name = name.replace(char, " ")
    # Remove titles/suffixes
    for title in [" NP", " PA", " MD", " DO", " ZZ", " DDS", " RN"]:
        name = name.replace(title, " ")
    # Normalize spaces
    return " ".join(name.split())


def build_provider_map(conn):
    """Build mapping from provider codes AND normalized full names to user_id"""
    provis = {}
    id_to_name = {}  # Reverse mapping: user_id -> full_name

    cursor = conn.execute(
        "SELECT user_id, first_name, last_name, full_name, username, alias FROM users WHERE status != 'deleted'"
    )
    users = cursor.fetchall()

    for row in users:
        uid, fn, ln, full_name, uname, alias = row
        fn = fn or ""
        ln = ln or ""
        full_name = full_name or f"{fn} {ln}".strip()
        uname = uname or ""
        alias = alias or ""

        # Store reverse mapping
        id_to_name[uid] = full_name

        # 1. Standard Codes from users table
        # Last Name start 3
        if ln:
            code = ln[:3].upper()
            if code not in provis:
                provis[code] = uid
        # Username parts
        parts = uname.split(".")
        for p in parts:
            if len(p) >= 3:
                provis[p[:3].upper()] = uid

        # Also map full username and alias for exact matches (like AteDi000)
        if uname:
            provis[uname.upper()] = uid
        if alias:
            provis[alias.upper()] = uid

        # 2. MATCHING LOGIC FOR ZMO (and general full name matching)
        # Generate varied keys to catch "Szalas NP, Andrew", "Andrew Szalas", "Szalas Andrew", etc.

        # A. Full Name Exact
        if full_name:
            provis[full_name.upper()] = uid
            provis[normalize_name_key(full_name)] = uid

        # B. First Last and Last First
        if fn and ln:
            f_l = f"{fn} {ln}".upper()
            l_f = f"{ln} {fn}".upper()
            provis[normalize_name_key(f_l)] = uid
            provis[normalize_name_key(l_f)] = uid

        # 3. Add mappings from staff_code_mapping table (for both coordinators and providers)

        # FIXED: Changed match_type to mapping_type to match actual table schema

        # FIXED: Include both COORDINATOR and PROVIDER mappings to cover all staff codes
        cursor = conn.execute(
            "SELECT staff_code, user_id, mapping_type FROM staff_code_mapping WHERE mapping_type IN ('COORDINATOR', 'PROVIDER')"
        )

        staff_mappings = cursor.fetchall()

        for staff_code, user_id, mapping_type in staff_mappings:
            if staff_code:
                provis[staff_code.upper()] = user_id

            # Ensure id_to_name has the full name for these staff members
            if user_id not in id_to_name:
                # Try to get full name from users table if not already there

                user_cursor = conn.execute(
                    "SELECT full_name, first_name, last_name FROM users WHERE user_id = ?",
                    (user_id,),
                ).fetchone()

                if user_cursor:
                    full_name_from_users = (
                        user_cursor[0] or f"{user_cursor[1]} {user_cursor[2]}".strip()
                    )

                    id_to_name[user_id] = full_name_from_users

        return provis, id_to_name


def parse_date(date_str):
    if pd.isna(date_str):
        return None
    date_str = str(date_str).strip()
    if not date_str:
        return None
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%m/%d/%y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def normalize_patient_id(patient_str):
    """Normalize patient ID to match populate_patients.sql logic"""
    if pd.isna(patient_str) or not patient_str:
        return None

    # Convert to string and strip
    patient_str = str(patient_str).strip()

    # Remove prefixes (order matters - longer prefixes first)
    prefixes = [
        "BLESSEDCARE-",
        "BLEESSEDCARE-",
        "BLESSEDCARE ",
        "BLEESSEDCARE ",
        "ZEN-",
        "PM-",
        "ZMN-",
        "3PR-",
        "3PR ",
    ]
    for prefix in prefixes:
        if patient_str.startswith(prefix):
            patient_str = patient_str[len(prefix) :]

    # Remove commas and normalize spacing
    patient_str = patient_str.replace(", ", " ").replace(",", " ")
    patient_str = patient_str.replace("  ", " ").strip()

    return patient_str


def create_patient_assignments_table(conn):
    """Create patient_assignments table"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patient_assignments (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            provider_id INTEGER NOT NULL,
            assignment_date DATE DEFAULT CURRENT_DATE,
            status TEXT DEFAULT 'active',
            source TEXT DEFAULT 'CSV_IMPORT',
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_patient_assignments_patient ON patient_assignments(patient_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_patient_assignments_provider ON patient_assignments(provider_id)"
    )


def build_first_name_provider_map(conn):
    """Build mapping from provider first names to user_id"""
    first_name_map = {}
    cursor = conn.execute(
        "SELECT user_id, first_name, full_name FROM users WHERE status != 'deleted'"
    )
    users = cursor.fetchall()

    for uid, fname, full_name in users:
        if fname:
            first_name_map[fname.upper()] = (uid, full_name or f"{fname}")
    return first_name_map


# def process_provider_assignments(csv_dir, conn):
#     """Process provider assignment files (ANGELA.csv, LOURDES.csv, etc.)
#     UPDATES patient_assignments to refine ZMO baseline with provider tab data
#     NOTE: Must run AFTER process_zmo which creates baseline assignments from ZMO
#     """
#     first_name_map = build_first_name_provider_map(conn)

#     all_files = glob.glob(os.path.join(csv_dir, "*.csv"))
#     assignment_files = []
#     exclude_patterns = [
#         "PSL_",
#         "RVZ_",
#         "CMLog_",
#         "ZMO_",
#         "index",
#         "psl",
#         "rvz",
#         "cmlog",
#     ]

#     for f in all_files:
#         basename = os.path.basename(f)
#         if not any(basename.startswith(p) for p in exclude_patterns):
#             name_part = basename.replace(".csv", "").strip()
#             if name_part and name_part[0].isupper():
#                 assignment_files.append(f)

#     print(f"  Found {len(assignment_files)} provider assignment files")
#     assignments_created = 0

#     for file_path in assignment_files:
#         basename = os.path.basename(file_path)
#         provider_first_name = (
#             basename.replace(".csv", "").strip().replace(" ", "").upper()
#         )
#         print(f"  Processing: {basename}")

#         provider_info = first_name_map.get(provider_first_name)
#         if not provider_info:
#             print(f"    ⚠️  Provider '{provider_first_name}' not found - skipping")
#             continue

#         provider_id, provider_full_name = provider_info
#         print(f"    -> {provider_full_name} (ID: {provider_id})")

#         try:
#             df = pd.read_csv(
#                 file_path, encoding="utf-8", on_bad_lines="skip", header=None
#             )
#             if df.empty:
#                 continue

#             file_assignments = 0
#             for idx, row in df.iterrows():
#                 try:
#                     # Column positions: 0=Status, 1=NameField (could be "NAME DOB" or just name), 2=DOB or FirstName, 3=DOB or Address
#                     status = str(row.iloc[0] if len(row) > 0 else "").strip()
#                     if "Active" not in status:
#                         continue

#                     # Column 2 usually has DOB
#                     dob = str(row.iloc[2] if len(row) > 2 else "").strip()

#                     # Column 1 might be "LASTNAME FIRSTNAME DOB" combined or separate
#                     name_field = str(row.iloc[1] if len(row) > 1 else "").strip()

#                     # If name_field contains the DOB, it's combined format - extract name part
#                     if dob and dob in name_field:
#                         # Format: "LASTNAME FIRSTNAME DOB" - remove DOB to get name
#                         name_part = name_field.replace(dob, "").strip()
#                         # Split into last and first name
#                         name_parts = name_part.split(None, 1)  # Split on first space
#                         if len(name_parts) >= 2:
#                             last_name = name_parts[0]
#                             first_name = name_parts[1]
#                         else:
#                             continue
#                     else:
#                         # Separate columns format
#                         last_name = name_field
#                         first_name = str(row.iloc[2] if len(row) > 2 else "").strip()
#                         dob = str(row.iloc[3] if len(row) > 3 else "").strip()

#                     if not last_name or not first_name or not dob:
#                         continue

#                     # Create patient_id: LASTNAME FIRSTNAME DOB format (uppercase)
#                     patient_id = (
#                         f"{last_name.upper()} {first_name.upper()} {dob}".strip()
#                     )
#                     if len(patient_id) < 5:
#                         continue
#                     # UPDATE assignment (refine ZMO baseline with provider tab data)
#                     # Only update if patient exists (from ZMO)
#                     result = conn.execute(
#                         "UPDATE patient_assignments SET provider_id = ? WHERE patient_id = ?",
#                         (provider_id, patient_id),
#                     )
#                     if result.rowcount > 0:
#                         file_assignments += 1
#                 except:
#                     continue

#             print(f"    Created {file_assignments} assignments")
#             assignments_created += file_assignments
#         except Exception as e:
#             print(f"    ❌ Error: {e}")

#     conn.commit()
#     return assignments_created


def process_psl(file_path, conn, provider_map, id_to_name):
    print(f"Processing PSL: {os.path.basename(file_path)}")
    try:
        df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")
        # Header check: If 1st row starts with '1', it might be correct.
        # Check columns
        if "DOS" not in df.columns:
            print(f"  Skipping (No DOS column)")
            return 0

        count = 0
        records_by_table = {}

        # Extract Provider from filename if possible
        filename = os.path.basename(file_path)
        prov_code_file = None
        match = re.search(r"PSL_ZEN-([A-Z]+)", filename)
        if match:
            prov_code_file = match.group(1)

        for _, row in df.iterrows():
            dos = parse_date(row.get("DOS"))
            if not dos:
                continue

            table = f"provider_tasks_{dos.year}_{str(dos.month).zfill(2)}"
            if table not in records_by_table:
                records_by_table[table] = []

            # Provider
            p_code_raw = str(row.get("Prov", "")).strip().upper()
            p_code = p_code_raw.replace("ZEN-", "").strip()
            if not p_code and prov_code_file:
                p_code = prov_code_file

            p_id = provider_map.get(p_code)
            # If not found, try with ZEN- prefix (for codes like ZEN-ANE vs ANE)
            if not p_id and p_code:
                p_id = provider_map.get(f"ZEN-{p_code}")
            # If still not found, try 3-char fallback
            if not p_id and p_code:
                p_id = provider_map.get(p_code[:3])

            pat_name = normalize_patient_id(row.get("Patient Last, First DOB", ""))
            if not pat_name:
                continue

            provider_name = id_to_name.get(p_id, p_code)

            # Process minutes from range format (e.g., "40-49" → 40)
            raw_minutes = str(row.get("Minutes", "0"))
            processed_minutes = process_minutes_range(raw_minutes)

            # Get service description and billing code from CSV
            service_description = str(row.get("Service", ""))
            csv_billing_code = str(row.get("Coding", "")).strip()
            final_billing_code = csv_billing_code if csv_billing_code else "PENDING"

            records_by_table[table].append(
                (
                    p_id,
                    provider_name,
                    pat_name,
                    pat_name,
                    dos.strftime("%Y-%m-%d"),
                    service_description,
                    str(row.get("Notes", "")),
                    processed_minutes,
                    final_billing_code,
                )
            )

        for table, recs in records_by_table.items():
            parts = table.split("_")
            create_provider_table(conn, int(parts[2]), int(parts[3]))

            # FIXED: Use INSERT OR IGNORE instead of DELETE + INSERT
            # This makes the process truly incremental and prevents data loss
            # The table should have a UNIQUE constraint on (provider_id, patient_id, task_date, task_description)
            # to prevent duplicates while preserving existing data
            inserted = conn.executemany(
                f"INSERT OR IGNORE INTO {table} (provider_id, provider_name, patient_id, patient_name, task_date, task_description, notes, minutes_of_service, billing_code) VALUES (?,?,?,?,?,?,?,?,?)",
                recs,
            ).rowcount
            count += inserted
            if inserted < len(recs):
                print(f"    Skipped {len(recs) - inserted} duplicate records")
        return count
    except Exception as e:
        print(f"  Error: {e}")
        return 0


def populate_provider_billing_status(conn, year, month):
    """Populate provider_task_billing_status table from provider_tasks_YYYY_MM table during transform"""
    try:
        provider_table = f"provider_tasks_{year}_{str(month).zfill(2)}"
        billing_status_table = "provider_task_billing_status"

        # Check if provider table exists
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
            (provider_table,),
        )
        if not cursor.fetchone():
            print(
                f"  Provider table {provider_table} does not exist, skipping billing status population"
            )
            return 0

        print(f"  Populating billing status from {provider_table}...")

        # Insert billing status records for billable tasks
        cursor.execute(f"""
            INSERT OR IGNORE INTO {billing_status_table} (
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
                created_date
            )
            SELECT pt.provider_task_id,
                pt.provider_id,
                pt.provider_name,
                pt.patient_name,
                pt.task_date,
                CAST(strftime('%W', pt.task_date) AS INTEGER) as billing_week,
                DATE(pt.task_date, 'weekday 0', '-6 days') as week_start_date,
                DATE(pt.task_date, 'weekday 0') as week_end_date,
                pt.task_description,
                pt.minutes_of_service,
                pt.billing_code,
                COALESCE(tbc.description, 'Unknown') as billing_code_description,
                'Pending' as billing_status,
                FALSE as is_billed,
                FALSE as is_invoiced,
                FALSE as is_claim_submitted,
                FALSE as is_insurance_processed,
                FALSE as is_approved_to_pay,
                FALSE as is_paid,
                FALSE as is_carried_over,
                CURRENT_TIMESTAMP as created_date
            FROM {provider_table} pt
            LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
            WHERE pt.billing_code IS NOT NULL
                AND pt.billing_code != 'Not_Billable'
                AND pt.billing_code != ''
                AND pt.billing_code != 'PENDING'
                AND pt.billing_code != 'nan'
            ORDER BY pt.task_date DESC, pt.provider_id
        """)

        inserted_count = cursor.rowcount

        # Show summary
        cursor.execute(f"""
            SELECT COUNT(*) as total_billable_tasks,
                COUNT(DISTINCT provider_id) as unique_providers,
                MIN(task_date) as earliest_task,
                MAX(task_date) as latest_task
            FROM {billing_status_table}
            WHERE task_date >= (SELECT MIN(task_date) FROM {provider_table})
        """)

        summary = cursor.fetchone()
        if summary:
            total_tasks, unique_providers, earliest, latest = summary
            print(
                f"    Billing status populated: {inserted_count} tasks, {unique_providers} providers"
            )
            if earliest and latest:
                print(f"    Date range: {earliest} to {latest}")

        return inserted_count

    except Exception as e:
        print(f"  Error populating billing status: {e}")
        return 0


def populate_coordinator_monthly_summary(conn, year, month):
    """Populate coordinator_monthly_summary from coordinator_tasks_YYYY_MM"""
    try:
        coord_table = f"coordinator_tasks_{year}_{str(month).zfill(2)}"
        summary_table = "coordinator_monthly_summary"

        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
            (coord_table,),
        )
        if not cursor.fetchone():
            print(f"  Coordinator table {coord_table} does not exist, skipping")
            return 0

        print(f"  Populating coordinator billing summary from {coord_table}...")

        # Check if records already exist for this month
        cursor.execute(
            f"""
            SELECT COUNT(*) FROM {summary_table}
            WHERE year = ? AND month = ?
        """,
            (year, month),
        )
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            print(
                f"    Clearing {existing_count} existing records for {year}-{month:02d}"
            )
            cursor.execute(
                f"""
                DELETE FROM {summary_table}
                WHERE year = ? AND month = ?
            """,
                (year, month),
            )

        # Aggregate coordinator tasks by patient/month
        cursor.execute(
            f"""
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
                AND COALESCE(ct.duration_minutes, 0) > 0
            GROUP BY ct.coordinator_id, ct.coordinator_name, ct.patient_id
        """,
            (year, month, year, month, year, month),
        )

        inserted_count = cursor.rowcount
        print(f"    Inserted/updated {inserted_count} coordinator billing records")

        return inserted_count

    except Exception as e:
        print(f"  Error populating coordinator billing summary: {e}")
        import traceback

        traceback.print_exc()
        return 0


def populate_provider_weekly_payroll(conn, year, month):
    """Populate provider_weekly_payroll_status from provider_task_billing_status"""
    try:
        payroll_table = "provider_weekly_payroll_status"

        cursor = conn.cursor()

        print(f"  Populating provider weekly payroll for {year}-{month:02d}...")

        # Check if records exist for this month and delete them first
        cursor.execute(
            f"""
            SELECT COUNT(*) FROM {payroll_table}
            WHERE CAST(strftime('%Y', pay_week_start_date) AS INTEGER) = ?
                AND CAST(strftime('%m', pay_week_start_date) AS INTEGER) = ?
        """,
            (year, month),
        )
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            print(
                f"    Clearing {existing_count} existing payroll records for {year}-{month:02d}"
            )
            cursor.execute(
                f"""
                DELETE FROM {payroll_table}
                WHERE CAST(strftime('%Y', pay_week_start_date) AS INTEGER) = ?
                    AND CAST(strftime('%m', pay_week_start_date) AS INTEGER) = ?
            """,
                (year, month),
            )

        # Aggregate provider tasks by week and visit type from provider_task_billing_status
        cursor.execute(
            f"""
            INSERT INTO {payroll_table} (
                provider_id, provider_name,
                pay_week_start_date, pay_week_end_date,
                pay_week_number, pay_year, visit_type,
                task_count, total_minutes_of_service,
                payroll_status, created_date
            )
            SELECT
                ptbs.provider_id,
                ptbs.provider_name,
                ptbs.week_start_date,
                ptbs.week_end_date,
                ptbs.billing_week,
                CAST(strftime('%Y', ptbs.task_date) AS INTEGER),
                ptbs.task_description as visit_type,
                COUNT(*) as task_count,
                SUM(COALESCE(ptbs.minutes_of_service, 0)) as total_minutes,
                'Pending' as payroll_status,
                CURRENT_TIMESTAMP as created_date
            FROM provider_task_billing_status ptbs
            WHERE CAST(strftime('%Y', ptbs.task_date) AS INTEGER) = ?
                AND CAST(strftime('%m', ptbs.task_date) AS INTEGER) = ?
                AND ptbs.provider_id IS NOT NULL
                AND COALESCE(ptbs.minutes_of_service, 0) > 0
            GROUP BY ptbs.provider_id, ptbs.provider_name,
                ptbs.week_start_date, ptbs.week_end_date,
                ptbs.task_description
        """,
            (year, month),
        )

        inserted_count = cursor.rowcount
        print(f"    Inserted {inserted_count} payroll records")

        return inserted_count

    except Exception as e:
        print(f"  Error populating payroll: {e}")
        import traceback

        traceback.print_exc()
        return 0


def process_rvz(file_path, conn, provider_map, id_to_name):
    print(f"Processing RVZ: {os.path.basename(file_path)}")
    try:
        # RVZ header is weird. Row 1: A,Provider... Row 2: "Last, First DOB"... Row 3: Data.
        # But 'Date Only' is in Row 1.
        df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")

        col_date = "Date Only"
        col_mins = "Mins B"  # Per LIVING_REFERENCE_DOC.MD - use Mins B, not Total Mins
        col_pt = "Pt Name"
        col_type = "Type"
        col_notes = "Notes"

        if col_date not in df.columns:
            print(f"  Skipping (No 'Date Only' column)")
            return 0

        count = 0
        records_by_table = {}

        filename = os.path.basename(file_path)
        prov_code_file = None
        coordinator_from_filename = None

        # Check if this is a CMLog file - use filename-based coordinator
        match_cm = re.search(r"CMLog_([A-Za-z0-9]+)\.csv", filename)
        if match_cm:
            coordinator_from_filename = match_cm.group(1)  # e.g. AteDi000
            print(
                f"  CMLog file detected - using coordinator from filename: {coordinator_from_filename}"
            )
        else:
            # Try RVZ pattern: RVZ_ZEN-([A-Z]+)
            match = re.search(r"RVZ_ZEN-([A-Z]+)", filename)
            if match:
                prov_code_file = match.group(1)

        for _, row in df.iterrows():
            pt_name = normalize_patient_id(row.get(col_pt, ""))
            prov_val = str(row.get("Provider", "")).strip()
            if not prov_val:
                prov_val = str(row.get("Staff", "")).strip()  # CMLog uses Staff

            if (
                not pt_name
                or not prov_val
                or "Place holder" in str(pt_name)
                or "Last, First DOB" in str(pt_name)
            ):
                continue

            dos = parse_date(row.get(col_date))
            if not dos:
                continue

            table = f"coordinator_tasks_{dos.year}_{str(dos.month).zfill(2)}"
            if table not in records_by_table:
                records_by_table[table] = []

            # For CMLog files, use coordinator from filename instead of CSV rows
            if coordinator_from_filename:
                p_code = coordinator_from_filename
            else:
                # Map Provider to Coordinator ID using the comprehensive provider_map
                p_code_raw = str(row.get("Provider", "")).strip().upper()
                p_code = p_code_raw.replace("ZEN-", "").strip()
                if not p_code:
                    p_code = str(row.get("Staff", "")).strip()

            # If empty in row, use filename code for RVZ files
            if not p_code and prov_code_file:
                p_code = prov_code_file

            # Use the comprehensive provider_map which now includes staff_code_mapping entries
            p_id = provider_map.get(p_code.upper())  # Try uppercase exact match
            # If not found, try with ZEN- prefix (for codes like ZEN-ANE vs ANE)
            if not p_id and p_code:
                p_id = provider_map.get(f"ZEN-{p_code}")
            # If still not found, try 3-char fallback
            if not p_id and p_code and len(p_code) >= 3:
                p_id = provider_map.get(p_code[:3].upper())  # Try 3-char fallback

            mins = row.get(col_mins, 0)
            try:
                mins = float(mins)
            except:
                mins = 0

            coordinator_name = id_to_name.get(p_id, p_code)

            records_by_table[table].append(
                (
                    p_id,
                    coordinator_name,
                    pt_name,
                    dos.strftime("%Y-%m-%d"),
                    mins,
                    str(row.get(col_type, "")),
                    str(row.get(col_notes, "")),
                )
            )

        for table, recs in records_by_table.items():
            parts = table.split("_")
            create_coordinator_table(conn, int(parts[2]), int(parts[3]))

            # FIXED: Use INSERT OR IGNORE instead of DELETE + INSERT
            # This makes the process truly incremental and prevents data loss
            # The table should have a UNIQUE constraint on (coordinator_id, patient_id, task_date, task_type)
            # to prevent duplicates while preserving existing data
            inserted = conn.executemany(
                f"INSERT OR IGNORE INTO {table} (coordinator_id, coordinator_name, patient_id, task_date, duration_minutes, task_type, notes) VALUES (?,?,?,?,?,?,?)",
                recs,
            ).rowcount
            count += inserted
            if inserted < len(recs):
                print(f"    Skipped {len(recs) - inserted} duplicate records")
        return count

    except Exception as e:
        print(f"  Error: {e}")
        return 0


def process_zmo(file_path, conn, provider_map):
    """Import patient data from ZMO_Main.csv
    Creates patients, patient_panel, patient_assignments, onboarding_patients records
    Auto-updates facilities table with new facilities from ZMO
    """
    print(f"Processing ZMO: {os.path.basename(file_path)}")
    try:
        df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")

        # Step 1: Update facilities table
        facilities = df["Fac"].dropna().unique()
        for fac_name in facilities:
            fac_name = str(fac_name).strip()
            if fac_name and fac_name != "Fac":
                existing = conn.execute(
                    "SELECT facility_id FROM facilities WHERE facility_name = ?",
                    (fac_name,),
                ).fetchone()
                if not existing:
                    conn.execute(
                        "INSERT INTO facilities (facility_name) VALUES (?)", (fac_name,)
                    )
                    print(f"  Added new facility: {fac_name}")

        # Step 2: Process patient records
        patients_data = []
        assignments_data = []
        onboarding_data = []

        # Track patient_ids to handle duplicates
        seen_patient_ids = {}
        duplicate_count = 0

        for _, row in df.iterrows():
            # Construct patient_id from separate columns (SQL ref: line 121 uses 'LAST FIRST DOB' but CSV has separate cols)
            last_name = (
                str(row.get("Last", "")).strip() if pd.notna(row.get("Last")) else None
            )
            first_name = (
                str(row.get("First", "")).strip()
                if pd.notna(row.get("First"))
                else None
            )
            dob_str = (
                str(row.get("DOB", "")).strip() if pd.notna(row.get("DOB")) else None
            )

            if not last_name or not first_name or not dob_str:
                continue

            # Construct combined "LAST FIRST DOB" string to match SQL logic
            combined_id = f"{last_name} {first_name} {dob_str}"
            patient_id = normalize_patient_id(combined_id)

            if not patient_id:
                continue

            # Handle duplicate patient_ids by appending -1, -2, etc.
            original_patient_id = patient_id
            if patient_id in seen_patient_ids:
                seen_patient_ids[patient_id] += 1
                patient_id = f"{patient_id}-{seen_patient_ids[patient_id]}"
                duplicate_count += 1
                print(f"  Duplicate found: {original_patient_id} -> {patient_id}")
            else:
                seen_patient_ids[patient_id] = 0

            # Map provider/coordinator (FIXED: column names have line breaks!)
            assigned_prov = (
                str(row.get("Assigned \nReg Prov", "")).strip().upper()
                if pd.notna(row.get("Assigned \nReg Prov"))
                else None
            )
            assigned_cm = (
                str(row.get("Assigned\nCM", "")).strip().upper()
                if pd.notna(row.get("Assigned\nCM"))
                else None
            )

            # Provider lookup with normalization
            provider_id = None
            if assigned_prov:
                provider_id = provider_map.get(assigned_prov)  # Try exact
                if not provider_id:
                    provider_id = provider_map.get(
                        normalize_name_key(assigned_prov)
                    )  # Try normalized
                if not provider_id and len(assigned_prov) >= 3:
                    provider_id = provider_map.get(
                        assigned_prov[:3]
                    )  # Try 3-char fallback

            # Coordinator lookup with normalization
            coordinator_id = None
            if assigned_cm:
                coordinator_id = provider_map.get(assigned_cm)
                if not coordinator_id:
                    coordinator_id = provider_map.get(normalize_name_key(assigned_cm))
                if not coordinator_id and len(assigned_cm) >= 3:
                    coordinator_id = provider_map.get(assigned_cm[:3])

            # Get facility_id
            facility_name = (
                str(row.get("Fac", "")).strip() if pd.notna(row.get("Fac")) else None
            )
            facility_id = None
            if facility_name:
                fac_row = conn.execute(
                    "SELECT facility_id FROM facilities WHERE facility_name = ?",
                    (facility_name,),
                ).fetchone()
                if fac_row:
                    facility_id = fac_row[0]

            # Parse dates (FIXED: column names have line breaks!)
            dob = parse_date(row.get("DOB"))
            initial_tv_date = parse_date(row.get("Initial TV\nDate"))
            phone = (
                str(row.get("Phone", "")).strip()
                if pd.notna(row.get("Phone"))
                else None
            )

            # Patients table - key fields only (simplified to avoid 102-column insert)
            patients_data.append(
                (
                    patient_id,
                    first_name,
                    last_name,
                    dob.strftime("%Y-%m-%d") if dob else None,
                    phone,
                    str(row.get("Street", "")).strip()
                    if pd.notna(row.get("Street"))
                    else None,
                    str(row.get("City", "")).strip()
                    if pd.notna(row.get("City"))
                    else None,
                    str(row.get("State", "")).strip()
                    if pd.notna(row.get("State"))
                    else None,
                    str(row.get("Zip", "")).strip()
                    if pd.notna(row.get("Zip"))
                    else None,
                    str(row.get("Ins1", "")).strip()
                    if pd.notna(row.get("Ins1"))
                    else None,
                    str(row.get("Policy", "")).strip()
                    if pd.notna(row.get("Policy"))
                    else None,
                    facility_id,
                    facility_name,
                    coordinator_id,
                    str(row.get("Pt Status", "Active")).strip()
                    if pd.notna(row.get("Pt Status"))
                    else "Active",
                    initial_tv_date.strftime("%Y-%m-%d") if initial_tv_date else None,
                    str(row.get("Initial TV\nNotes", "")).strip()
                    if pd.notna(row.get("Initial TV\nNotes"))
                    else None,
                    str(row.get("Initial TV\nProv", "")).strip()
                    if pd.notna(row.get("Initial TV\nProv"))
                    else None,
                )
            )

            # Patient panel - REMOVED: rebuilt by populate_patient_panel.sql from patients table

            # Assignments
            if provider_id or coordinator_id:
                assignments_data.append((patient_id, provider_id, coordinator_id))

            # Onboarding
            onboarding_data.append(
                (
                    patient_id,
                    first_name,
                    last_name,
                    dob.strftime("%Y-%m-%d") if dob else None,
                    phone,
                    provider_id,
                    coordinator_id,
                    initial_tv_date.strftime("%Y-%m-%d") if initial_tv_date else None,
                    str(row.get("Initial TV\nProv", "")).strip()
                    if pd.notna(row.get("Initial TV\nProv"))
                    else None,
                )
            )

        # Step 3: Insert data (DELETE first)
        conn.execute("DELETE FROM patients")
        # NOTE: patient_assignments is now handled by process_provider_assignments_from_zmo
        conn.execute("DELETE FROM patient_assignments")
        conn.execute("DELETE FROM onboarding_patients")
        # NOTE: patient_panel is NOT deleted here - it will be rebuilt by post_import_processing.sql

        # Insert patients (simplified - expand columns as needed)
        conn.executemany(
            """INSERT INTO patients (
            patient_id, first_name, last_name, date_of_birth, phone_primary,
            address_street, address_city, address_state, address_zip,
            insurance_primary, insurance_policy_number, current_facility_id, facility,
            assigned_coordinator_id, status, initial_tv_completed_date, initial_tv_notes, initial_tv_provider
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            patients_data,
        )

        # Patient panel - REMOVED: rebuilt by populate_patient_panel.sql from patients table with ALL columns

        # Assignments - Use proper table structure with source tracking
        if assignments_data:
            conn.executemany(
                """INSERT INTO patient_assignments (
                    patient_id, provider_id, coordinator_id, status, source
                ) VALUES (?, ?, ?, 'active', 'ZMO_IMPORT')""",
                assignments_data,
            )

        # Onboarding
        conn.executemany(
            """INSERT INTO onboarding_patients (
            patient_id, first_name, last_name, date_of_birth, phone_primary,
            assigned_provider_user_id, assigned_coordinator_user_id, tv_date, initial_tv_provider
        ) VALUES (?,?,?,?,?,?,?,?,?)""",
            onboarding_data,
        )

        print(f"  Imported {len(patients_data)} patients")
        print(f"  Created {len(assignments_data)} provider assignments")
        if duplicate_count > 0:
            print(
                f"  [WARNING] Found {duplicate_count} duplicate patient_ids (appended -1, -2, etc.)"
            )
        return len(patients_data), len(assignments_data)

    except Exception as e:
        print(f"  Error: {e}")
        import traceback

        traceback.print_exc()
        return 0


def main():
    conn = get_db()
    pmap, id_to_name = build_provider_map(conn)

    # STEP 1: Import patient data from ZMO (BASELINE - creates patients + assignments)
    print("\n" + "=" * 60)
    print("STEP 1: Importing Patient Data from ZMO (Baseline)")
    print("=" * 60)
    zmo_file = os.path.join(CSV_DIR, "ZMO_MAIN.csv")
    total_patients = 0
    total_assignments = 0
    if os.path.exists(zmo_file):
        total_patients, total_assignments = process_zmo(zmo_file, conn, pmap)
    else:
        print(f"⚠️  Warning: {zmo_file} not found - skipping patient import")

    # STEP 2: Provider Assignments are now handled entirely within process_zmo()
    # No need for separate provider CSV file processing anymore
    print("\n" + "=" * 60)
    print("STEP 2: Provider Assignments (Handled in ZMO Processing)")
    print("=" * 60)
    print("  [OK] Provider assignments processed from ZMO data in Step 1")

    # STEP 3: Import task data
    print("\n" + "=" * 60)
    print("STEP 3: Importing Task Data")
    print("=" * 60)
    psl_files = glob.glob(os.path.join(CSV_DIR, "PSL_ZEN-*.csv"))
    rvz_files = glob.glob(os.path.join(CSV_DIR, "RVZ_ZEN-*.csv"))
    cmlog_files = glob.glob(os.path.join(CSV_DIR, "CMLog_*.csv"))

    total_psl = 0
    total_rvz = 0

    for f in psl_files:
        total_psl += process_psl(f, conn, pmap, id_to_name)
    for f in rvz_files:
        total_rvz += process_rvz(f, conn, pmap, id_to_name)
    for f in cmlog_files:
        total_rvz += process_rvz(f, conn, pmap, id_to_name)  # Process CMLog same as RVZ

    # STEP 4: Populate billing status for all provider task months
    print("\n" + "=" * 60)
    print("STEP 4: Populating Provider Billing Status")
    print("=" * 60)

    # Get all unique months that were processed from PSL files
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT substr(name, 16, 4) as year_month
        FROM sqlite_master
        WHERE type='table'
        AND name LIKE 'provider_tasks_20%'
        ORDER BY year_month DESC
    """)

    processed_months = cursor.fetchall()
    total_billing_records = 0

    for (year_month,) in processed_months:
        try:
            if not year_month or len(year_month) != 6:
                continue
            year = int(year_month[:4])
            month = int(year_month[4:6])
            if month < 1 or month > 12:
                continue
            print(f"  Processing {calendar.month_name[month]} {year}...")
            billing_count = populate_provider_billing_status(conn, year, month)
            total_billing_records += billing_count
        except (ValueError, IndexError) as e:
            print(f"  Warning: Skipping invalid year_month format: {year_month}")
            continue

    if total_billing_records > 0:
        print(f"  Total billing status records created: {total_billing_records}")
    else:
        print("  No billing status records created (no provider tasks found)")

    # STEP 5: Populate coordinator monthly summary
    print("\n" + "=" * 60)
    print("STEP 5: Populating Coordinator Monthly Summary")
    print("=" * 60)

    cursor.execute("""
        SELECT DISTINCT substr(name, 19, 4) as year_month
        FROM sqlite_master
        WHERE type='table'
        AND name LIKE 'coordinator_tasks_20%'
        ORDER BY year_month DESC
    """)

    processed_coord_months = cursor.fetchall()
    total_coordinator_summary = 0

    for (year_month,) in processed_coord_months:
        try:
            if not year_month or len(year_month) != 6:
                continue
            year = int(year_month[:4])
            month = int(year_month[4:6])
            if month < 1 or month > 12:
                continue
            print(f"  Processing {calendar.month_name[month]} {year}...")
            summary_count = populate_coordinator_monthly_summary(conn, year, month)
            total_coordinator_summary += summary_count
        except (ValueError, IndexError) as e:
            print(f"  Warning: Skipping invalid year_month: {year_month}")
            continue

    if total_coordinator_summary > 0:
        print(f"  Total coordinator summary records: {total_coordinator_summary}")
    else:
        print("  No coordinator summary records created")

    # STEP 6: Populate provider weekly payroll
    print("\n" + "=" * 60)
    print("STEP 6: Populating Provider Weekly Payroll")
    print("=" * 60)

    total_payroll_records = 0

    for (year_month,) in processed_months:
        try:
            if not year_month or len(year_month) != 6:
                continue
            year = int(year_month[:4])
            month = int(year_month[4:6])
            if month < 1 or month > 12:
                continue
            print(f"  Processing {calendar.month_name[month]} {year}...")
            payroll_count = populate_provider_weekly_payroll(conn, year, month)
            total_payroll_records += payroll_count
        except (ValueError, IndexError) as e:
            print(f"  Warning: Skipping invalid year_month: {year_month}")
            continue

    if total_payroll_records > 0:
        print(f"  Total payroll records created: {total_payroll_records}")
    else:
        print("  No payroll records created")

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"  Provider Assignments: {total_assignments}")
    print(f"  Patients Imported:    {total_patients}")
    print(f"  Provider Tasks:       {total_psl}")
    print(f"  Coordinator Tasks:    {total_rvz}")
    print(f"  Billing Status Records: {total_billing_records}")
    print(f"  Coordinator Summary:  {total_coordinator_summary}")
    print(f"  Payroll Records:      {total_payroll_records}")
    print(
        f"  Total Records:        {total_assignments + total_patients + total_psl + total_rvz + total_billing_records + total_coordinator_summary + total_payroll_records}"
    )
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
