#!/usr/bin/env python3
"""
Fix script to repopulate patient_panel table with correct provider/coordinator names.
This addresses the issue where patient_panel contains stale data.
"""

import sqlite3
import sys
from datetime import datetime

def get_db():
    return sqlite3.connect("production.db")

def log_print(*args, **kwargs):
    """Print function with timestamp"""
    message = " ".join(map(str, args))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def populate_patient_panel_fixed(conn):
    """
    Fixed version of populate_patient_panel() function to repopulate patient_panel table
    with correct provider/coordinator names from patient_assignments table.
    """
    log_print("Repopulating patient_panel table with correct provider/coordinator data...")
    try:
        # Drop and recreate the patient_panel table with unified schema
        log_print("  Dropping existing patient_panel table...")
        conn.execute("DROP TABLE IF EXISTS patient_panel")

        # Create clean patient_panel table with essential columns for My Patients view
        log_print("  Creating patient_panel table schema...")
        conn.execute("""
            CREATE TABLE patient_panel (
                -- Core patient identification
                patient_id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                date_of_birth TEXT,
                phone_primary TEXT,
                current_facility_id INTEGER,
                facility TEXT,
                status TEXT,
                created_date TEXT,

                -- Provider/Coordinator assignment
                provider_id INTEGER,
                coordinator_id INTEGER,
                provider_name TEXT,
                coordinator_name TEXT,
                last_visit_date TEXT,
                last_visit_service_type TEXT,

                -- Clinical fields needed for display
                goals_of_care TEXT,
                goc_value TEXT,
                code_status TEXT,
                subjective_risk_level TEXT,
                service_type TEXT,

                -- Healthcare utilization
                er_count_1yr INTEGER,
                hospitalization_count_1yr INTEGER,

                -- Mental health conditions (provider assessment)
                mental_health_concerns INTEGER,
                provider_mh_schizophrenia INTEGER,
                provider_mh_depression INTEGER,
                provider_mh_anxiety INTEGER,
                provider_mh_stress INTEGER,
                provider_mh_adhd INTEGER,
                provider_mh_bipolar INTEGER,
                provider_mh_suicidal INTEGER,

                -- Functional and cognitive status
                cognitive_function TEXT,
                functional_status TEXT,

                -- Care coordination fields
                active_specialists TEXT,
                active_concerns TEXT,
                chronic_conditions_provider TEXT,

                -- Contact information for care coordination
                appointment_contact_name TEXT,
                appointment_contact_phone TEXT,
                medical_contact_name TEXT,
                medical_contact_phone TEXT,

                -- Care team member names for easy display
                care_provider_name TEXT,
                care_coordinator_name TEXT,

                -- Metadata
                updated_date TEXT DEFAULT (datetime('now'))
            )
        """)

        # Create indexes for performance
        log_print("  Creating indexes...")
        conn.execute(
            "CREATE INDEX idx_patient_panel_patient_id ON patient_panel(patient_id)"
        )
        conn.execute(
            "CREATE INDEX idx_patient_panel_provider_id ON patient_panel(provider_id)"
        )
        conn.execute(
            "CREATE INDEX idx_patient_panel_coordinator_id ON patient_panel(coordinator_id)"
        )
        conn.execute("CREATE INDEX idx_patient_panel_status ON patient_panel(status)")
        conn.execute(
            "CREATE INDEX idx_patient_panel_facility ON patient_panel(facility)"
        )
        conn.execute(
            "CREATE INDEX idx_patient_panel_last_visit ON patient_panel(last_visit_date)"
        )

        log_print("  Populating patient_panel with current data...")

        # Build clean patient_panel with essential fields for My Patients view
        query = """
        INSERT INTO patient_panel
        SELECT
            -- Core patient fields from patients table
            p.patient_id,
            p.first_name,
            p.last_name,
            p.date_of_birth,
            p.phone_primary,
            p.current_facility_id,
            p.facility,
            p.status,
            p.created_date,

            -- Provider/Coordinator assignment from patient_assignments table
            COALESCE(pa.provider_id, 0) as provider_id,
            COALESCE(pa.coordinator_id, 0) as coordinator_id,
            CASE WHEN pa.provider_id > 0 THEN u_prov.full_name ELSE NULL END as provider_name,
            CASE WHEN pa.coordinator_id > 0 THEN u_coord.full_name ELSE NULL END as coordinator_name,
            p.last_visit_date,
            p.service_type as last_visit_service_type,

            -- Clinical fields for display
            p.goals_of_care,
            p.goc_value,
            p.code_status,
            p.subjective_risk_level,
            p.service_type,

            -- Healthcare utilization
            p.er_count_1yr,
            p.hospitalization_count_1yr,

            -- Mental health conditions (provider assessment)
            p.mental_health_concerns,
            p.provider_mh_schizophrenia,
            p.provider_mh_depression,
            p.provider_mh_anxiety,
            p.provider_mh_stress,
            p.provider_mh_adhd,
            p.provider_mh_bipolar,
            p.provider_mh_suicidal,

            -- Functional and cognitive status
            p.cognitive_function,
            p.functional_status,

            -- Care coordination fields
            p.active_specialists,
            p.active_concerns,
            p.chronic_conditions_provider,

            -- Contact information
            p.appointment_contact_name,
            p.appointment_contact_phone,
            p.medical_contact_name,
            p.medical_contact_phone,

            -- Care team member names (FIXED: use correct fields from patient_assignments table)
            CASE WHEN pa.provider_id > 0 THEN u_prov.full_name ELSE NULL END as care_provider_name,
            CASE WHEN pa.coordinator_id > 0 THEN u_coord.full_name ELSE NULL END as care_coordinator_name,

            -- Updated date
            datetime('now') as updated_date
        FROM patients p
        LEFT JOIN patient_assignments pa ON p.patient_id = pa.patient_id AND pa.status = 'active'
        LEFT JOIN users u_prov ON pa.provider_id = u_prov.user_id
        LEFT JOIN users u_coord ON pa.coordinator_id = u_coord.user_id
        """

        conn.execute(query)

        # Get count of records inserted
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patient_panel")
        panel_count = cursor.fetchone()[0]

        # Check how many records now have provider/coordinator names
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN care_provider_name IS NOT NULL AND care_provider_name != '' THEN 1 END) as with_provider,
                COUNT(CASE WHEN care_coordinator_name IS NOT NULL AND care_coordinator_name != '' THEN 1 END) as with_coordinator
            FROM patient_panel
        """)
        stats = cursor.fetchone()
        total, with_provider, with_coordinator = stats

        log_print(f"  Patient panel repopulated: {total} total records")
        log_print(f"  Records with provider names: {with_provider}")
        log_print(f"  Records with coordinator names: {with_coordinator}")
        log_print(f"  Records missing both: {total - max(with_provider, with_coordinator)}")

        return panel_count

    except Exception as e:
        log_print(f"  Error repopulating patient_panel: {e}")
        import traceback
        logger.error(f"Error: {e}", exc_info=True)
        logger.error(f"Error repopulating patient_panel: {e}", exc_info=True)
        return 0

def main():
    log_print("Starting patient_panel fix...")
    
    conn = get_db()
    
    # Get current stats before fix
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN care_provider_name IS NOT NULL AND care_provider_name != '' THEN 1 END) as with_provider,
            COUNT(CASE WHEN care_coordinator_name IS NOT NULL AND care_coordinator_name != '' THEN 1 END) as with_coordinator
        FROM patient_panel
    """)
    before_stats = cursor.fetchone()
    total_before, provider_before, coordinator_before = before_stats
    
    log_print(f"BEFORE FIX:")
    log_print(f"  Total records: {total_before}")
    log_print(f"  With provider names: {provider_before}")
    log_print(f"  With coordinator names: {coordinator_before}")
    log_print(f"  Missing both: {total_before - max(provider_before, coordinator_before)}")
    
    # Apply fix
    panel_count = populate_patient_panel_fixed(conn)
    
    if panel_count > 0:
        conn.commit()
        log_print("✅ Patient panel fix completed successfully!")
        
        # Verify fix
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN care_provider_name IS NOT NULL AND care_provider_name != '' THEN 1 END) as with_provider,
                COUNT(CASE WHEN care_coordinator_name IS NOT NULL AND care_coordinator_name != '' THEN 1 END) as with_coordinator
            FROM patient_panel
        """)
        after_stats = cursor.fetchone()
        total_after, provider_after, coordinator_after = after_stats
        
        log_print(f"AFTER FIX:")
        log_print(f"  Total records: {total_after}")
        log_print(f"  With provider names: {provider_after}")
        log_print(f"  With coordinator names: {coordinator_after}")
        log_print(f"  Missing both: {total_after - max(provider_after, coordinator_after)}")
        
        improvement = (total_before - max(provider_before, coordinator_before)) - (total_after - max(provider_after, coordinator_after))
        log_print(f"  Records fixed: {improvement}")
        
    else:
        log_print("❌ Patient panel fix failed!")
        conn.rollback()
    
    conn.close()

if __name__ == "__main__":
    main()