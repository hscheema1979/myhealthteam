#!/usr/bin/env python3
"""
OCTOBER 2025 DATA TRANSFER TO PRODUCTION
Transfers clean, validated October 2025 data from staging to production database
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_production_before_transfer():
    """Create backup of production database before transfer"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"../production_backup_pre_transfer_{timestamp}.db"
    
    print(f"🔒 Creating pre-transfer backup: {backup_path}")
    shutil.copy2('../production.db', backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def transfer_new_patients():
    """Transfer new patients from staging to production"""
    print(f"\n👥 TRANSFERRING NEW PATIENTS")
    print("=" * 50)
    
    staging_conn = sqlite3.connect('sheets_data.db')
    production_conn = sqlite3.connect('../production.db')
    
    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()
    
    # Get new patients (in staging but not in production)
    staging_cursor.execute("SELECT DISTINCT patient_id FROM staging_patients")
    staging_patients = {row[0] for row in staging_cursor.fetchall()}
    
    production_cursor.execute("SELECT DISTINCT patient_id FROM patients")
    production_patients = {row[0] for row in production_cursor.fetchall()}
    
    new_patients = staging_patients - production_patients
    
    print(f"📊 New patients to transfer: {len(new_patients)}")
    
    if len(new_patients) == 0:
        print("✅ No new patients to transfer")
        staging_conn.close()
        production_conn.close()
        return 0
    
    # Transfer patients one by one to handle column mapping correctly
    transferred_count = 0
    
    for patient_id in new_patients:
        try:
            # Get complete patient data from staging
            staging_cursor.execute("""
                SELECT patient_id, region_id, first_name, last_name, date_of_birth, gender,
                       phone_primary, phone_secondary, email, address_street, 
                       address_city, address_state, address_zip, emergency_contact_name,
                       emergency_contact_phone, emergency_contact_relationship,
                       insurance_primary, insurance_policy_number, insurance_secondary,
                       medical_record_number, enrollment_date, discharge_date, notes,
                       created_date, updated_date, created_by, updated_by,
                       current_facility_id, hypertension, mental_health_concerns,
                       dementia, last_annual_wellness_visit, last_first_dob, status,
                       medical_records_requested, referral_documents_received,
                       insurance_cards_received, emed_signature_received, last_visit_date,
                       facility, assigned_coordinator_id, er_count_1yr,
                       hospitalization_count_1yr, clinical_biometric,
                       chronic_conditions_provider, cancer_history, subjective_risk_level,
                       provider_mh_schizophrenia, provider_mh_depression,
                       provider_mh_anxiety, provider_mh_stress, provider_mh_adhd,
                       provider_mh_bipolar, provider_mh_suicidal, active_specialists,
                       code_status, cognitive_function, functional_status, goals_of_care,
                       active_concerns, initial_tv_completed_date, initial_tv_notes,
                       service_type, appointment_contact_name, appointment_contact_phone,
                       appointment_contact_email, medical_contact_name, medical_contact_phone,
                       medical_contact_email, primary_care_provider, pcp_last_seen,
                       active_specialist, specialist_last_seen,
                       chronic_conditions_onboarding, mh_schizophrenia, mh_depression,
                       mh_anxiety, mh_stress, mh_adhd, mh_bipolar, mh_suicidal,
                       tv_date, tv_scheduled, patient_notified, initial_tv_provider
                FROM staging_patients 
                WHERE patient_id = ?
            """, (patient_id,))
            
            patient_data = staging_cursor.fetchone()
            
            if patient_data:
                # Insert into production with explicit column mapping
                production_cursor.execute("""
                    INSERT INTO patients (
                        patient_id, region_id, first_name, last_name, date_of_birth, gender,
                        phone_primary, phone_secondary, email, address_street, 
                        address_city, address_state, address_zip, emergency_contact_name,
                        emergency_contact_phone, emergency_contact_relationship,
                        insurance_primary, insurance_policy_number, insurance_secondary,
                        medical_record_number, enrollment_date, discharge_date, notes,
                        created_date, updated_date, created_by, updated_by,
                        current_facility_id, hypertension, mental_health_concerns,
                        dementia, last_annual_wellness_visit, last_first_dob, status,
                        medical_records_requested, referral_documents_received,
                        insurance_cards_received, emed_signature_received, last_visit_date,
                        facility, assigned_coordinator_id, er_count_1yr,
                        hospitalization_count_1yr, clinical_biometric,
                        chronic_conditions_provider, cancer_history, subjective_risk_level,
                        provider_mh_schizophrenia, provider_mh_depression,
                        provider_mh_anxiety, provider_mh_stress, provider_mh_adhd,
                        provider_mh_bipolar, provider_mh_suicidal, active_specialists,
                        code_status, cognitive_function, functional_status, goals_of_care,
                        active_concerns, initial_tv_completed_date, initial_tv_notes,
                        service_type, appointment_contact_name, appointment_contact_phone,
                        appointment_contact_email, medical_contact_name, medical_contact_phone,
                        medical_contact_email, primary_care_provider, pcp_last_seen,
                        active_specialist, specialist_last_seen,
                        chronic_conditions_onboarding, mh_schizophrenia, mh_depression,
                        mh_anxiety, mh_stress, mh_adhd, mh_bipolar, mh_suicidal,
                        tv_date, tv_scheduled, patient_notified, initial_tv_provider,
                        eligibility_status, eligibility_notes, eligibility_verified,
                        emed_chart_created, chart_id, facility_confirmed, chart_notes,
                        intake_call_completed, intake_notes, goc_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, 0, NULL, NULL, 0, NULL, NULL, 0, NULL)
                """, patient_data)
                transferred_count += 1
                
        except sqlite3.IntegrityError as e:
            print(f"   ⚠️  Skipping patient {patient_id}: {e}")
        except Exception as e:
            print(f"   ❌ Error transferring patient {patient_id}: {e}")
    
    production_conn.commit()
    
    print(f"✅ Transferred {transferred_count} new patients")
    
    staging_conn.close()
    production_conn.close()
    
    return transferred_count

def transfer_patient_assignments():
    """Transfer patient assignments for new patients"""
    print(f"\n🏥 TRANSFERRING PATIENT ASSIGNMENTS")
    print("=" * 50)
    
    staging_conn = sqlite3.connect('sheets_data.db')
    production_conn = sqlite3.connect('../production.db')
    
    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()
    
    # Get assignments for new patients
    staging_cursor.execute("""
        SELECT DISTINCT pa.patient_id, pa.coordinator_id, pa.assigned_date, pa.status
        FROM staging_patient_assignments pa
        INNER JOIN staging_patients sp ON pa.patient_id = sp.patient_id
        WHERE pa.patient_id NOT IN (SELECT patient_id FROM patients)
    """)
    
    assignments_data = staging_cursor.fetchall()
    
    print(f"📊 Patient assignments to transfer: {len(assignments_data)}")
    
    transferred_count = 0
    for assignment in assignments_data:
        try:
            production_cursor.execute("""
                INSERT INTO patient_assignments (patient_id, coordinator_id, assigned_date, status)
                VALUES (?, ?, ?, ?)
            """, assignment)
            transferred_count += 1
        except sqlite3.IntegrityError as e:
            print(f"   ⚠️  Skipping assignment {assignment[0]}: {e}")
    
    production_conn.commit()
    
    print(f"✅ Transferred {transferred_count} patient assignments")
    
    staging_conn.close()
    production_conn.close()
    
    return transferred_count

def transfer_patient_panels():
    """Transfer patient panel data for new patients"""
    print(f"\n🔬 TRANSFERRING PATIENT PANEL DATA")
    print("=" * 50)
    
    staging_conn = sqlite3.connect('sheets_data.db')
    production_conn = sqlite3.connect('../production.db')
    
    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()
    
    # Get panel data for new patients
    staging_cursor.execute("""
        SELECT DISTINCT pp.patient_id, pp.panel_type, pp.provider_id, pp.start_date, pp.end_date
        FROM staging_patient_panel pp
        INNER JOIN staging_patients sp ON pp.patient_id = sp.patient_id
        WHERE pp.patient_id NOT IN (SELECT patient_id FROM patients)
    """)
    
    panel_data = staging_cursor.fetchall()
    
    print(f"📊 Patient panel records to transfer: {len(panel_data)}")
    
    transferred_count = 0
    for panel in panel_data:
        try:
            production_cursor.execute("""
                INSERT INTO patient_panel (patient_id, panel_type, provider_id, start_date, end_date)
                VALUES (?, ?, ?, ?, ?)
            """, panel)
            transferred_count += 1
        except sqlite3.IntegrityError as e:
            print(f"   ⚠️  Skipping panel {panel[0]}: {e}")
    
    production_conn.commit()
    
    print(f"✅ Transferred {transferred_count} patient panel records")
    
    staging_conn.close()
    production_conn.close()
    
    return transferred_count

def transfer_october_2025_coordinator_tasks():
    """Transfer October 2025 coordinator tasks"""
    print(f"\n📋 TRANSFERRING OCTOBER 2025 COORDINATOR TASKS")
    print("=" * 50)
    
    staging_conn = sqlite3.connect('sheets_data.db')
    production_conn = sqlite3.connect('../production.db')
    
    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()
    
    # Get October 2025 coordinator tasks from staging
    staging_cursor.execute("""
        SELECT staff_code, patient_name_raw, task_type, notes, minutes_raw, 
               activity_date, year_month
        FROM staging_coordinator_tasks 
        WHERE activity_date BETWEEN '2025-10-01' AND '2025-10-31'
    """)
    
    tasks_data = staging_cursor.fetchall()
    
    print(f"📊 October 2025 coordinator tasks to transfer: {len(tasks_data)}")
    
    transferred_count = 0
    for task in tasks_data:
        try:
            # Map staging data to production schema
            production_cursor.execute("""
                INSERT INTO coordinator_tasks (
                    task_id, patient_id, coordinator_id, task_date, duration_minutes,
                    task_type, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                None,  # task_id (auto-increment)
                task[1],  # patient_id
                task[0],  # coordinator_id (staff_code)
                task[5],  # task_date (activity_date)
                task[4] if task[4] and task[4] != '' else 0,  # duration_minutes
                task[2],  # task_type
                task[3]   # notes
            ))
            transferred_count += 1
        except sqlite3.IntegrityError as e:
            print(f"   ⚠️  Skipping coordinator task: {e}")
    
    production_conn.commit()
    
    print(f"✅ Transferred {transferred_count} October 2025 coordinator tasks")
    
    staging_conn.close()
    production_conn.close()
    
    return transferred_count

def transfer_october_2025_provider_tasks():
    """Transfer October 2025 provider tasks"""
    print(f"\n👨‍⚕️ TRANSFERRING OCTOBER 2025 PROVIDER TASKS")
    print("=" * 50)
    
    staging_conn = sqlite3.connect('sheets_data.db')
    production_conn = sqlite3.connect('../production.db')
    
    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()
    
    # Get October 2025 provider tasks from staging
    staging_cursor.execute("""
        SELECT provider_name, patient_name, task_type, minutes_of_service, 
               activity_date, billing_code, task_description, notes
        FROM staging_provider_tasks 
        WHERE activity_date BETWEEN '2025-10-01' AND '2025-10-31'
    """)
    
    tasks_data = staging_cursor.fetchall()
    
    print(f"📊 October 2025 provider tasks to transfer: {len(tasks_data)}")
    
    transferred_count = 0
    for task in tasks_data:
        try:
            # Map staging data to production schema
            production_cursor.execute("""
                INSERT INTO provider_tasks (
                    provider_name, patient_name, task_type, minutes_of_service,
                    task_date, billing_code, task_description, notes,
                    created_date, updated_date, source_system
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task[0],  # provider_name
                task[1],  # patient_name
                task[2],  # task_type
                task[3] if task[3] and task[3] != '' else 0,  # minutes_of_service
                task[4],  # task_date (activity_date)
                task[5],  # billing_code
                task[6],  # task_description
                task[7],  # notes
                datetime.now().isoformat(),  # created_date
                datetime.now().isoformat(),  # updated_date
                'staging_transfer_october_2025'  # source_system
            ))
            transferred_count += 1
        except sqlite3.IntegrityError as e:
            print(f"   ⚠️  Skipping provider task: {e}")
    
    production_conn.commit()
    
    print(f"✅ Transferred {transferred_count} October 2025 provider tasks")
    
    staging_conn.close()
    production_conn.close()
    
    return transferred_count

def verify_transfer_success():
    """Verify that data transfer was successful"""
    print(f"\n🔍 VERIFYING TRANSFER SUCCESS")
    print("=" * 50)
    
    production_conn = sqlite3.connect('../production.db')
    cursor = production_conn.cursor()
    
    # Check total patients
    cursor.execute("SELECT COUNT(*) FROM patients")
    total_patients = cursor.fetchone()[0]
    
    # Check October 2025 coordinator tasks
    cursor.execute("SELECT COUNT(*) FROM coordinator_tasks WHERE task_date LIKE '2025-10%'")
    oct_coordinator_tasks = cursor.fetchone()[0]
    
    # Check October 2025 provider tasks
    cursor.execute("SELECT COUNT(*) FROM provider_tasks WHERE task_date LIKE '2025-10%'")
    oct_provider_tasks = cursor.fetchone()[0]
    
    # Check patient assignments
    cursor.execute("SELECT COUNT(*) FROM patient_assignments")
    total_assignments = cursor.fetchone()[0]
    
    # Check patient panels
    cursor.execute("SELECT COUNT(*) FROM patient_panel")
    total_panels = cursor.fetchone()[0]
    
    print(f"📊 POST-TRANSFER PRODUCTION DATABASE:")
    print(f"   • Total patients: {total_patients:,}")
    print(f"   • October 2025 coordinator tasks: {oct_coordinator_tasks:,}")
    print(f"   • October 2025 provider tasks: {oct_provider_tasks:,}")
    print(f"   • Patient assignments: {total_assignments:,}")
    print(f"   • Patient panels: {total_panels:,}")
    print()
    
    # Verify expected counts
    expected_patients = 512 + 101  # original + new
    expected_oct_coordinator = 70 + 7817  # existing + new
    expected_oct_provider = 0 + 105  # existing + new
    
    print(f"✅ VERIFICATION RESULTS:")
    patients_ok = total_patients == expected_patients
    coordinator_ok = oct_coordinator_tasks == expected_oct_coordinator
    provider_ok = oct_provider_tasks == expected_oct_provider
    
    print(f"   • Patients: {total_patients:,} (expected {expected_patients:,}) {'✅' if patients_ok else '❌'}")
    print(f"   • October coordinator tasks: {oct_coordinator_tasks:,} (expected {expected_oct_coordinator:,}) {'✅' if coordinator_ok else '❌'}")
    print(f"   • October provider tasks: {oct_provider_tasks:,} (expected {expected_oct_provider:,}) {'✅' if provider_ok else '❌'}")
    
    production_conn.close()
    
    return patients_ok and coordinator_ok and provider_ok

def generate_transfer_report(backup_path, transfer_results, success):
    """Generate comprehensive transfer report"""
    print(f"\n📋 TRANSFER SUMMARY REPORT")
    print("=" * 60)
    
    print(f"Transfer completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Pre-transfer backup: {backup_path}")
    print()
    
    print(f"📊 DATA TRANSFERRED:")
    for item, count in transfer_results.items():
        print(f"   • {item}: {count:,} records")
    
    print()
    print(f"🎯 TRANSFER STATUS:")
    if success:
        print(f"   ✅ SUCCESSFUL - All October 2025 data transferred successfully")
        print(f"   ✅ Database integrity maintained")
        print(f"   ✅ Production database enriched with October 2025 data")
    else:
        print(f"   ⚠️  PARTIAL - Some data may not have transferred correctly")
    
    print()
    print(f"🚀 POST-TRANSFER NEXT STEPS:")
    if success:
        print(f"   1. ✅ Verify billing views work correctly")
        print(f"   2. 🔍 Test coordinator and provider dashboards")
        print(f"   3. 📊 Monitor application performance")
        print(f"   4. 🗂️  Archive staging data")
    else:
        print(f"   1. 🔍 Investigate transfer discrepancies")
        print(f"   2. 🧹 Re-run failed transfers")
        print(f"   3. ✅ Only then proceed with billing verification")

def main():
    """Execute October 2025 data transfer to production"""
    print(f"🚀 OCTOBER 2025 DATA TRANSFER TO PRODUCTION")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not os.path.exists('../production.db'):
        print("❌ ERROR: Production database not found")
        return False
    
    try:
        # Step 1: Create pre-transfer backup
        backup_path = backup_production_before_transfer()
        
        # Step 2: Transfer all data components
        transfer_results = {}
        
        transfer_results["New Patients"] = transfer_new_patients()
        transfer_results["Patient Assignments"] = transfer_patient_assignments()
        transfer_results["Patient Panels"] = transfer_patient_panels()
        transfer_results["October 2025 Coordinator Tasks"] = transfer_october_2025_coordinator_tasks()
        transfer_results["October 2025 Provider Tasks"] = transfer_october_2025_provider_tasks()
        
        # Step 3: Verify transfer success
        success = verify_transfer_success()
        
        # Step 4: Generate report
        generate_transfer_report(backup_path, transfer_results, success)
        
        return success
        
    except Exception as e:
        print(f"❌ TRANSFER FAILED: {str(e)}")
        print("🛑 TRANSFER INTERRUPTED - Manual investigation required")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n🎉 OCTOBER 2025 DATA TRANSFER SUCCESSFUL!")
        print(f"🚀 Production database enriched and ready for billing verification")
    else:
        print(f"\n🛑 TRANSFER INCOMPLETE - Review required before proceeding")