# ZMO Patient Import Function
# Add this to transform_production_data_v3.py before the main() function

def process_zmo(file_path, conn, provider_map):
    """Import patient data from ZMO_Main.csv
    Creates patients, patient_panel, patient_assignments, onboarding_patients records
    Auto-updates facilities table with new facilities from ZMO
    """
    print(f"Processing ZMO: {os.path.basename(file_path)}")
    try:
        df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
        
        # Step 1: Update facilities table  
        facilities = df['Fac'].dropna().unique()
        for fac_name in facilities:
            fac_name = str(fac_name).strip()
            if fac_name and fac_name != 'Fac':
                existing = conn.execute("SELECT facility_id FROM facilities WHERE facility_name = ?", (fac_name,)).fetchone()
                if not existing:
                    conn.execute("INSERT INTO facilities (facility_name) VALUES (?)", (fac_name,))
                    print(f"  Added new facility: {fac_name}")
        
        # Step 2: Process patient records
        patients_data = []
        panel_data = []
        assignments_data = []
        onboarding_data = []
        
        for _, row in df.iterrows():
            patient_id = normalize_patient_id(row.get('LAST FIRST DOB', ''))
            if not patient_id or patient_id == 'LAST FIRST DOB':
                continue
            
            first_name = str(row.get('First', '')).strip() if pd.notna(row.get('First')) else None
            last_name = str(row.get('Last', '')).strip() if pd.notna(row.get('Last')) else None
            if not first_name or not last_name:
                continue
            
            # Map provider/coordinator
            assigned_prov = str(row.get('Assigned  Reg Prov', '')).strip().upper() if pd.notna(row.get('Assigned  Reg Prov')) else None
            assigned_cm = str(row.get('Assigned CM', '')).strip().upper() if pd.notna(row.get('Assigned CM')) else None
            
            provider_id = provider_map.get(assigned_prov) if assigned_prov else None
            if not provider_id and assigned_prov and len(assigned_prov) >= 3:
                provider_id = provider_map.get(assigned_prov[:3])
            
            coordinator_id = provider_map.get(assigned_cm) if assigned_cm else None
            if not coordinator_id and assigned_cm and len(assigned_cm) >= 3:
                coordinator_id = provider_map.get(assigned_cm[:3])
            
            # Get facility_id
            facility_name = str(row.get('Fac', '')).strip() if pd.notna(row.get('Fac')) else None
            facility_id = None
            if facility_name:
                fac_row = conn.execute("SELECT facility_id FROM facilities WHERE facility_name = ?", (facility_name,)).fetchone()
                if fac_row:
                    facility_id = fac_row[0]
            
            # Parse dates
            dob = parse_date(row.get('DOB'))
            initial_tv_date = parse_date(row.get('Initial TV Date'))
            phone = str(row.get('Phone', '')).strip() if pd.notna(row.get('Phone')) else None
            
            # Patients table - key fields only (simplified to avoid 102-column insert)
            patients_data.append((
                patient_id, first_name, last_name,
                dob.strftime('%Y-%m-%d') if dob else None,
                phone,
                str(row.get('Street', '')).strip() if pd.notna(row.get('Street')) else None,
                str(row.get('City', '')).strip() if pd.notna(row.get('City')) else None,
                str(row.get('State', '')).strip() if pd.notna(row.get('State')) else None,
                str(row.get('Zip', '')).strip() if pd.notna(row.get('Zip')) else None,
                str(row.get('Ins1', '')).strip() if pd.notna(row.get('Ins1')) else None,
                str(row.get('Policy', '')).strip() if pd.notna(row.get('Policy')) else None,
                facility_id, facility_name, coordinator_id,
                str(row.get('Pt Status', 'Active')).strip() if pd.notna(row.get('Pt Status')) else 'Active',
                initial_tv_date.strftime('%Y-%m-%d') if initial_tv_date else None,
                str(row.get('Initial TV Notes', '')).strip() if pd.notna(row.get('Initial TV Notes')) else None,
                str(row.get('Initial TV Prov', '')).strip() if pd.notna(row.get('Initial TV Prov')) else None
            ))
            
            # Patient panel
            panel_data.append((
                patient_id, first_name, last_name, dob.strftime('%Y-%m-%d') if dob else None,
                phone, facility_id, facility_name, provider_id, coordinator_id
            ))
            
            # Assignments
            if provider_id or coordinator_id:
                assignments_data.append((patient_id, provider_id, coordinator_id))
            
            # Onboarding
            onboarding_data.append((
                patient_id, first_name, last_name, dob.strftime('%Y-%m-%d') if dob else None,
                phone, provider_id, coordinator_id,
                initial_tv_date.strftime('%Y-%m-%d') if initial_tv_date else None,
                str(row.get('Initial TV Prov', '')).strip() if pd.notna(row.get('Initial TV Prov')) else None
            ))
        
        # Step 3: Insert data (DELETE first)
        conn.execute("DELETE FROM patients")
        conn.execute("DELETE FROM patient_panel")
        conn.execute("DELETE FROM patient_assignments")
        conn.execute("DELETE FROM onboarding_patients")
        
        # Insert patients (simplified - expand columns as needed)
        conn.executemany("""INSERT INTO patients (
            patient_id, first_name, last_name, date_of_birth, phone_primary,
            address_street, address_city, address_state, address_zip,
            insurance_primary, insurance_policy_number, current_facility_id, facility,
            assigned_coordinator_id, status, initial_tv_completed_date, initial_tv_notes, initial_tv_provider
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", patients_data)
        
        # Patient panel
        conn.executemany("""INSERT INTO patient_panel (
            patient_id, first_name, last_name, date_of_birth, phone_primary,
            current_facility_id, facility, provider_id, coordinator_id
        ) VALUES (?,?,?,?,?,?,?,?,?)""", panel_data)
        
        # Assignments
        conn.executemany("INSERT INTO patient_assignments (patient_id, provider_id, coordinator_id) VALUES (?,?,?)", assignments_data)
        
        # Onboarding
        conn.executemany("""INSERT INTO onboarding_patients (
            patient_id, first_name, last_name, date_of_birth, phone_primary,
            assigned_provider_user_id, assigned_coordinator_user_id, tv_date, initial_tv_provider
        ) VALUES (?,?,?,?,?,?,?,?,?)""", onboarding_data)
        
        print(f"  Imported {len(patients_data)} patients")
        return len(patients_data)
        
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return 0
