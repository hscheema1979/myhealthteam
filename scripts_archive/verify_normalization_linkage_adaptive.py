import sqlite3
import csv
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'production.db')
REPORT_DIR = os.path.join(os.path.dirname(__file__), 'outputs', 'reports')

DB_PATH = os.path.abspath(DB_PATH)
REPORT_DIR = os.path.abspath(REPORT_DIR)

os.makedirs(REPORT_DIR, exist_ok=True)

def write_csv(path, rows, headers=None):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if headers:
            w.writerow(headers)
        for r in rows:
            w.writerow(r)

def has_column(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info({table})")
    for row in cur.fetchall():
        if row[1] == column:
            return True
    return False

def find_existing_column(conn, table, candidates):
    cur = conn.execute(f"PRAGMA table_info({table})")
    cols = {row[1] for row in cur.fetchall()}
    for c in candidates:
        if c in cols:
            return c
    return None

def sql_ident(col_name):
    # Quote identifier if it contains non-alphanumeric/underscore or uppercase+spaces
    if not col_name.replace('_', '').isalnum() or ' ' in col_name:
        return f'"{col_name}"'
    return col_name

# Inline normalization expressions (read-only)
# PROVIDER_NORM_EXPR will be composed in main() because raw column name may vary
# COORD_NORM_EXPR will also be composed in main()

summary_lines = []


def main():
    print("Starting verification script...")
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return
    print(f"Connecting to database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    print("Database connected.")
    try:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Determine raw name columns for normalization
        print("Determining raw name columns for normalization...")
        provider_raw_col = find_existing_column(conn, 'staging_provider_tasks', [
            'patient_name_raw', 'Patient Last, First DOB', 'patient_name', 'pt_name'
        ])
        coord_raw_col = find_existing_column(conn, 'staging_coordinator_tasks', [
            'Pt Name', 'patient_name_raw', 'patient_name', 'pt_name'
        ])
        if provider_raw_col is None:
            print('ERROR: Could not find a raw patient name column in staging_provider_tasks.')
            return
        if coord_raw_col is None:
            print('ERROR: Could not find a raw patient name column in staging_coordinator_tasks.')
            return
        print("Raw name columns determined.")

        # Shared prefixes to strip from raw patient identifiers
        prefixes = ['ZEN-', 'PM-', 'ZMN-', 'BlessedCare-', 'BLESSEDCARE-', 'BleessedCare-', 'BLEESSEDCARE-', '3PR-', '3PR -']

        # Provider normalization: comma to space, strip known prefixes, trim and uppercase
        base_provider = f"TRIM(REPLACE(pt.{sql_ident(provider_raw_col)}, ',', ' '))"
        expr_p = base_provider
        for p in prefixes:
            expr_p = f"REPLACE({expr_p}, '{p}', '')"
        # collapse multiple spaces to single spaces (apply a few times)
        expr_p = f"REPLACE(REPLACE(REPLACE({expr_p}, '  ', ' '), '  ', ' '), '  ', ' ')"
        PROVIDER_NORM_EXPR = f"UPPER(TRIM({expr_p}))"

        # Build coordinator normalization expression incrementally to avoid complex nested string bugs
        base_coord = f"TRIM(REPLACE(sc.{sql_ident(coord_raw_col)}, ',', ' '))"
        expr = base_coord
        for p in prefixes:
            expr = f"REPLACE({expr}, '{p}', '')"
        # collapse multiple spaces to single spaces
        expr = f"REPLACE(REPLACE(REPLACE({expr}, '  ', ' '), '  ', ' '), '  ', ' ')"
        COORD_NORM_EXPR = f"UPPER(TRIM({expr}))"

        # Provider linkage rate (adaptive)
        print("Calculating provider linkage rate...")
        total_provider = conn.execute("SELECT COUNT(*) AS c FROM staging_provider_tasks").fetchone()[0]
        # Always use normalized provider identifier for matching to avoid relying on a possibly non-standard patient_id column
        provider_matched_sql = (
            "SELECT COUNT(*) AS c FROM staging_provider_tasks pt "
            "WHERE EXISTS (SELECT 1 FROM staging_patient_panel p WHERE UPPER(CAST(p.patient_id AS TEXT)) = UPPER(CAST("
            f"{PROVIDER_NORM_EXPR} AS TEXT)))"
        )
        print("--- Provider matched SQL ---")
        print(provider_matched_sql)
        print("--------------------------------")
        matched_provider = conn.execute(provider_matched_sql).fetchone()[0]
        provider_unmatched_sql = (
            "SELECT norm.patient_id, norm.patient_name_raw, norm.service, norm.billing_code "
            "FROM ("
            f"  SELECT {PROVIDER_NORM_EXPR} AS patient_id, pt.{sql_ident(provider_raw_col)} AS patient_name_raw, pt.service, pt.billing_code "
            "  FROM staging_provider_tasks pt"
            ") AS norm "
            "LEFT JOIN staging_patient_panel p ON UPPER(CAST(p.patient_id AS TEXT)) = UPPER(CAST(norm.patient_id AS TEXT)) "
            "WHERE p.patient_id IS NULL LIMIT 50"
        )
        print("--- Provider unmatched SQL ---")
        print(provider_unmatched_sql)
        print("--------------------------------")
        unmatched_provider_rows = conn.execute(provider_unmatched_sql).fetchall()
        print("Provider linkage calculated. Writing unmatched provider samples...")
        write_csv(
            os.path.join(REPORT_DIR, 'provider_tasks_unmatched_samples.csv'),
            [(r['patient_id'], r['patient_name_raw'], r['service'], r['billing_code']) for r in unmatched_provider_rows],
            headers=['patient_id','patient_name_raw','service','billing_code']
        )
        summary_lines.append(f"Provider linkage: {matched_provider}/{total_provider} matched ({(matched_provider/total_provider*100 if total_provider else 0):.2f}%).")
        print("Unmatched provider samples written.")

        # Coordinator linkage rate (inline normalization)
        print("Calculating coordinator linkage rate...")
        coord_total = conn.execute("SELECT COUNT(*) AS c FROM staging_coordinator_tasks").fetchone()[0]
        coord_sql_matched = (
            "SELECT COUNT(*) AS c FROM staging_coordinator_tasks sc "
            "WHERE EXISTS ("
            "  SELECT 1 FROM staging_patient_panel p "
            f"  WHERE UPPER(CAST(p.patient_id AS TEXT)) = UPPER(CAST({COORD_NORM_EXPR} AS TEXT))"
            ")"
        )
        print("--- Coordinator matched SQL ---")
        print(coord_sql_matched)
        print("--------------------------------")
        coord_matched = conn.execute(coord_sql_matched).fetchone()[0]
        coord_unmatched_sql = (
            "SELECT norm.patient_id, norm.pt_name, norm.activity_date, norm.staff_code, norm.year_month "
            "FROM ("
            f"  SELECT {COORD_NORM_EXPR} AS patient_id, sc.{sql_ident(coord_raw_col)} AS pt_name, sc.activity_date, sc.staff_code, sc.year_month "
            "  FROM staging_coordinator_tasks sc"
            ") AS norm "
            "LEFT JOIN staging_patient_panel p ON UPPER(CAST(p.patient_id AS TEXT)) = UPPER(CAST(norm.patient_id AS TEXT)) "
            "WHERE p.patient_id IS NULL LIMIT 50"
        )
        print("--- Coordinator unmatched SQL ---")
        print(coord_unmatched_sql)
        print("---------------------------------")
        coord_unmatched_rows = conn.execute(coord_unmatched_sql).fetchall()
        print("Coordinator linkage calculated. Writing unmatched coordinator samples...")
        write_csv(
            os.path.join(REPORT_DIR, 'coordinator_tasks_unmatched_samples.csv'),
            [(r['patient_id'], r['pt_name'], r['activity_date'], r['staff_code'], r['year_month']) for r in coord_unmatched_rows],
            headers=['patient_id','pt_name','activity_date','staff_code','year_month']
        )
        summary_lines.append(f"Coordinator linkage: {coord_matched}/{coord_total} matched ({(coord_matched/coord_total*100 if coord_total else 0):.2f}%).")
        print("Unmatched coordinator samples written.")

        # Panel consistency (provider tasks vs staging panel)
        print("Checking panel consistency...")
        tasks_without_panel_sql = (
            "SELECT DISTINCT np.patient_id FROM ("
            f"SELECT {PROVIDER_NORM_EXPR} AS patient_id FROM staging_provider_tasks pt"
            ") AS np "
            + "LEFT JOIN staging_patient_panel sp ON UPPER(CAST(sp.patient_id AS TEXT)) = UPPER(CAST(np.patient_id AS TEXT)) "
            + "WHERE sp.patient_id IS NULL"
        )
        print("--- Tasks without panel SQL ---")
        print(tasks_without_panel_sql)
        print("-------------------------------")
        tasks_without_panel = conn.execute(tasks_without_panel_sql).fetchall()
        print("Panel consistency check complete. Writing tasks_without_panel.csv...")
        write_csv(
            os.path.join(REPORT_DIR, 'tasks_without_panel.csv'),
            [(r['patient_id'],) for r in tasks_without_panel],
            headers=['patient_id']
        )
        print("tasks_without_panel.csv written. Continuing consistency check...")
        panel_without_tasks_sql = (
            "SELECT sp.patient_id FROM staging_patient_panel sp "
            "LEFT JOIN ("
            f"SELECT DISTINCT {PROVIDER_NORM_EXPR} AS patient_id FROM staging_provider_tasks pt"
            ") AS nt ON UPPER(CAST(nt.patient_id AS TEXT)) = UPPER(CAST(sp.patient_id AS TEXT)) "
            "WHERE nt.patient_id IS NULL"
        )
        print("--- Panel without tasks SQL ---")
        print(panel_without_tasks_sql)
        print("-------------------------------")
        panel_without_tasks = conn.execute(panel_without_tasks_sql).fetchall()
        print("Consistency check continued. Writing panel_without_tasks.csv...")
        write_csv(
            os.path.join(REPORT_DIR, 'panel_without_tasks.csv'),
            [(r['patient_id'],) for r in panel_without_tasks],
            headers=['patient_id']
        )
        summary_lines.append(f"Tasks without panel: {len(tasks_without_panel)}; Panel without tasks: {len(panel_without_tasks)}.")
        print("panel_without_tasks.csv written.")

        # Collision audits
        print("Running collision audits...")
        provider_collisions_sql = (
            "SELECT patient_id, COUNT(DISTINCT patient_name_raw) AS distinct_raw_names, COUNT(*) AS task_rows "
            "FROM ("
            f"SELECT pt.patient_id AS patient_id, pt.patient_name_raw FROM staging_provider_tasks pt"
            ") AS norm_provider "
            "GROUP BY patient_id HAVING distinct_raw_names > 1 "
            "ORDER BY distinct_raw_names DESC, task_rows DESC LIMIT 200"
        )
        print("--- Provider collisions SQL ---")
        print(provider_collisions_sql)
        print("--------------------------------")
        provider_collisions = conn.execute(provider_collisions_sql).fetchall()
        print("Provider collision audit complete. Writing normalization_collisions_provider.csv...")
        write_csv(
            os.path.join(REPORT_DIR, 'normalization_collisions_provider.csv'),
            [(r['patient_id'], r['distinct_raw_names'], r['task_rows']) for r in provider_collisions],
            headers=['patient_id','distinct_raw_names','task_rows']
        )
        print("normalization_collisions_provider.csv written. Running coordinator collision audit...")
        coord_collisions_sql = (
            "SELECT patient_id, COUNT(DISTINCT pt_name) AS distinct_raw_names, COUNT(*) AS task_rows "
            "FROM ("
            f"  SELECT {COORD_NORM_EXPR} AS patient_id, sc.{sql_ident(coord_raw_col)} AS pt_name "
            "  FROM staging_coordinator_tasks sc"
            ") AS norm "
            "GROUP BY patient_id HAVING distinct_raw_names > 1 "
            "ORDER BY distinct_raw_names DESC, task_rows DESC LIMIT 200"
        )
        print("--- Coordinator collisions SQL ---")
        print(coord_collisions_sql)
        print("----------------------------------")
        coord_collisions = conn.execute(coord_collisions_sql).fetchall()
        print("Coordinator collision audit complete. Writing normalization_collisions_coordinator.csv...")
        write_csv(
            os.path.join(REPORT_DIR, 'normalization_collisions_coordinator.csv'),
            [(r['patient_id'], r['distinct_raw_names'], r['task_rows']) for r in coord_collisions],
            headers=['patient_id','distinct_raw_names','task_rows']
        )
        summary_lines.append(f"Provider collisions: {len(provider_collisions)}; Coordinator collisions: {len(coord_collisions)}.")
        print("normalization_collisions_coordinator.csv written.")

        # Summary
        print("Writing summary...")
        summary_path = os.path.join(REPORT_DIR, 'normalization_linkage_summary.txt')
        with open(summary_path, 'w', encoding='utf-8') as sf:
            sf.write(f"Normalization linkage verification summary (read-only)\nTimestamp: {ts}\nDatabase: {DB_PATH}\n\n")
            for line in summary_lines:
                sf.write(line + "\n")
        print("Verification complete.")
        for line in summary_lines:
            print(line)
        print(f"CSV outputs written to: {REPORT_DIR}")
        print("Script finished.")
    finally:
        conn.close()
        print("Database connection closed.")

if __name__ == '__main__':
    main()