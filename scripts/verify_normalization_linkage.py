import sqlite3
import csv
import os
from datetime import datetime
from pathlib import Path
import argparse

# Inline normalization for coordinator Pt Name (read-only)
COORD_NORM_EXPR = (
    "UPPER(TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE("
    "TRIM(REPLACE(sc.patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), "
    "'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), "
    "'3PR-', ''), '3PR -', '')))"
)


def write_csv(path, rows, headers=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
        for r in rows:
            writer.writerow(r)


def append_living_doc(living_doc_path: Path, ts: str, staging_db: str, prod_db: str, summary_lines):
    try:
        with open(living_doc_path, 'a', encoding='utf-8') as f:
            f.write("\n\n### Normalization Linkage Verification (staging vs prod)\n")
            f.write(f"Timestamp: {ts}\n")
            f.write(f"Staging DB: {staging_db}\n")
            f.write(f"Production DB (attached as 'prod'): {prod_db}\n\n")
            for line in summary_lines:
                f.write(f"- {line}\n")
    except Exception:
        # Silent failure to avoid terminal noise; user can re-run if needed
        pass


def main():
    parser = argparse.ArgumentParser(description='Verify normalization linkage between staging (sheets_data.db) and production (production.db).')
    default_root = Path(os.path.dirname(__file__)).parent
    parser.add_argument('--staging-db', default=str(default_root / 'sheets_data.db'))
    parser.add_argument('--prod-db', default=str(default_root / 'production.db'))
    parser.add_argument('--report-dir', default=str(Path(os.path.dirname(__file__)) / 'outputs' / 'reports'))
    parser.add_argument('--no-living-doc', action='store_true', help='Do not append results to PROJECT_LIVING_DOCUMENT.md')
    parser.add_argument('--quick', action='store_true', help='Quick mode: reduce samples and skip collision audits')
    args = parser.parse_args()

    staging_db = os.path.abspath(args.staging_db)
    prod_db = os.path.abspath(args.prod_db)
    report_dir = os.path.abspath(args.report_dir)

    summary_lines = []

    if not os.path.exists(staging_db):
        # If staging DB is missing, abort quietly
        return

    os.makedirs(report_dir, exist_ok=True)
    conn = sqlite3.connect(staging_db)
    conn.row_factory = sqlite3.Row
    try:
        # Attach production for read-only joins
        if os.path.exists(prod_db):
            conn.execute(f"ATTACH DATABASE '{prod_db}' AS prod")
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 1) Provider linkage rate (staging provider tasks -> prod patients)
        total_provider = conn.execute("SELECT COUNT(*) AS c FROM staging_provider_tasks").fetchone()[0]
        matched_provider = conn.execute(
            "SELECT COUNT(*) AS c FROM staging_provider_tasks pt "
            "WHERE EXISTS (SELECT 1 FROM prod.patients p WHERE p.patient_id = pt.patient_id)"
        ).fetchone()[0]
        sample_limit = 50
        if args.quick:
            sample_limit = 25
        unmatched_provider_rows = conn.execute(
            "SELECT pt.patient_id, pt.patient_name_raw, pt.service, pt.billing_code "
            "FROM staging_provider_tasks pt "
            "LEFT JOIN prod.patients p ON p.patient_id = pt.patient_id "
            "WHERE p.patient_id IS NULL "
            f"LIMIT {sample_limit}"
        ).fetchall()
        write_csv(
            os.path.join(report_dir, 'provider_tasks_unmatched_samples.csv'),
            [(r['patient_id'], r['patient_name_raw'], r['service'], r['billing_code']) for r in unmatched_provider_rows],
            headers=['patient_id','patient_name_raw','service','billing_code']
        )
        summary_lines.append(
            f"Provider linkage: {matched_provider}/{total_provider} matched ({(matched_provider/total_provider*100 if total_provider else 0):.2f}%)."
        )

        # 2) Coordinator linkage rate (inline normalization -> prod patients)
        coord_total = conn.execute("SELECT COUNT(*) AS c FROM staging_coordinator_tasks").fetchone()[0]
        coord_matched = conn.execute(
            f"WITH norm AS ("
            f"  SELECT {COORD_NORM_EXPR} AS patient_id FROM staging_coordinator_tasks sc"
            f") SELECT COUNT(*) AS c FROM norm n WHERE EXISTS (SELECT 1 FROM prod.patients p WHERE p.patient_id = n.patient_id)"
        ).fetchone()[0]
        coord_unmatched_rows = conn.execute(
            f"WITH norm AS ("
            f"  SELECT {COORD_NORM_EXPR} AS patient_id, sc.patient_name_raw AS pt_name, sc.activity_date, sc.staff_code, sc.year_month "
            f"  FROM staging_coordinator_tasks sc"
            f") SELECT n.patient_id, n.pt_name, n.activity_date, n.staff_code, n.year_month "
            f"FROM norm n LEFT JOIN prod.patients p ON p.patient_id = n.patient_id "
            f"WHERE p.patient_id IS NULL LIMIT {sample_limit}"
        ).fetchall()
        write_csv(
            os.path.join(report_dir, 'coordinator_tasks_unmatched_samples.csv'),
            [(r['patient_id'], r['pt_name'], r['activity_date'], r['staff_code'], r['year_month']) for r in coord_unmatched_rows],
            headers=['patient_id','pt_name','activity_date','staff_code','year_month']
        )
        summary_lines.append(
            f"Coordinator linkage: {coord_matched}/{coord_total} matched ({(coord_matched/coord_total*100 if coord_total else 0):.2f}%)."
        )

        # 3) Panel consistency
        # Prefer staging panel if present; otherwise check against production panel
        sp_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='staging_patient_panel'"
        ).fetchone()
        if sp_exists:
            tasks_without_panel = conn.execute(
                "SELECT DISTINCT pt.patient_id FROM staging_provider_tasks pt "
                "LEFT JOIN staging_patient_panel sp ON sp.patient_id = pt.patient_id "
                "WHERE sp.patient_id IS NULL"
            ).fetchall()
            panel_without_tasks = conn.execute(
                "WITH norm_tasks AS (SELECT DISTINCT patient_id FROM staging_provider_tasks) "
                "SELECT sp.patient_id FROM staging_patient_panel sp "
                "LEFT JOIN norm_tasks nt ON nt.patient_id = sp.patient_id "
                "WHERE nt.patient_id IS NULL"
            ).fetchall()
        else:
            tasks_without_panel = conn.execute(
                "SELECT DISTINCT pt.patient_id FROM staging_provider_tasks pt "
                "LEFT JOIN prod.patient_panel sp ON sp.patient_id = pt.patient_id "
                "WHERE sp.patient_id IS NULL"
            ).fetchall()
            panel_without_tasks = conn.execute(
                "WITH norm_tasks AS (SELECT DISTINCT patient_id FROM staging_provider_tasks) "
                "SELECT sp.patient_id FROM prod.patient_panel sp "
                "LEFT JOIN norm_tasks nt ON nt.patient_id = sp.patient_id "
                "WHERE nt.patient_id IS NULL"
            ).fetchall()
        write_csv(
            os.path.join(report_dir, 'tasks_without_panel.csv'),
            [(r['patient_id'],) for r in tasks_without_panel],
            headers=['patient_id']
        )
        write_csv(
            os.path.join(report_dir, 'panel_without_tasks.csv'),
            [(r['patient_id'],) for r in panel_without_tasks],
            headers=['patient_id']
        )
        summary_lines.append(
            f"Tasks without panel: {len(tasks_without_panel)}; Panel without tasks: {len(panel_without_tasks)}."
        )

        # 4) Collision audits
        if not args.quick:
            provider_collisions = conn.execute(
                "SELECT patient_id, COUNT(DISTINCT patient_name_raw) AS distinct_raw_names, COUNT(*) AS task_rows "
                "FROM staging_provider_tasks GROUP BY patient_id HAVING distinct_raw_names > 1 "
                "ORDER BY distinct_raw_names DESC, task_rows DESC LIMIT 200"
            ).fetchall()
            write_csv(
                os.path.join(report_dir, 'normalization_collisions_provider.csv'),
                [(r['patient_id'], r['distinct_raw_names'], r['task_rows']) for r in provider_collisions],
                headers=['patient_id','distinct_raw_names','task_rows']
            )
            coord_collisions = conn.execute(
                f"WITH norm AS ("
                f"  SELECT {COORD_NORM_EXPR} AS patient_id, sc.patient_name_raw AS pt_name FROM staging_coordinator_tasks sc"
                f") SELECT patient_id, COUNT(DISTINCT pt_name) AS distinct_raw_names, COUNT(*) AS task_rows "
                f"FROM norm GROUP BY patient_id HAVING distinct_raw_names > 1 "
                f"ORDER BY distinct_raw_names DESC, task_rows DESC LIMIT 200"
            ).fetchall()
            write_csv(
                os.path.join(report_dir, 'normalization_collisions_coordinator.csv'),
                [(r['patient_id'], r['distinct_raw_names'], r['task_rows']) for r in coord_collisions],
                headers=['patient_id','distinct_raw_names','task_rows']
            )
            summary_lines.append(
                f"Provider collisions: {len(provider_collisions)}; Coordinator collisions: {len(coord_collisions)}."
            )

        # 5) Write a summary file and append to living document (no terminal prints)
        summary_path = os.path.join(report_dir, 'normalization_linkage_summary.txt')
        with open(summary_path, 'w', encoding='utf-8') as sf:
            sf.write(
                "Normalization linkage verification summary (read-only)\n"
            )
            sf.write(f"Timestamp: {ts}\n")
            sf.write(f"Staging DB: {staging_db}\n")
            sf.write(f"Production DB: {prod_db}\n\n")
            for line in summary_lines:
                sf.write(line + "\n")

        living_doc_path = Path(os.path.dirname(__file__)).parent / 'PROJECT_LIVING_DOCUMENT.md'
        if not args.no_living_doc and living_doc_path.exists():
            append_living_doc(living_doc_path, ts, staging_db, prod_db, summary_lines)
    finally:
        conn.close()


if __name__ == '__main__':
    main()