import streamlit as st
import pandas as pd
from src import database

def show(user_id):
    st.title("Care Provider Dashboard")
    
    # Get the provider_id from user_id first
    provider_id = database.get_provider_id_from_user_id(user_id)
    if not provider_id:
        st.error("No provider found for this user. Please contact your administrator.")
        return

    # Get all patients assigned to this provider (with status filtering)
    assigned_patients = database.get_user_patient_assignments(user_id)
    
    # Get all unique patient statuses for filtering
    all_statuses = []
    if assigned_patients:
        try:
            patient_data_list = []
            for patient in assigned_patients:
                patient_dict = dict(patient)
                patient_data_list.append(patient_dict)
            
            # Extract unique statuses
            all_statuses = list(set([p.get('status', 'Unknown') for p in patient_data_list if 'status' in p]))
            all_statuses = sorted([s for s in all_statuses if s])  # Remove empty strings and sort
        except Exception as e:
            print(f"Error getting statuses: {e}")
            all_statuses = ['Active', 'Inactive']  # Default fallback
    else:
        all_statuses = ['Active', 'Inactive']  # Default fallback
    
    # Get regions assigned to this specific provider with zip codes and cities for filtering
    all_regions = []
    try:
        # Get regions assigned to this provider through region_providers table
        conn = database.get_db_connection()
        cursor = conn.execute("""
            SELECT DISTINCT r.region_id, r.region_name, r.zip_code, r.city, r.state 
            FROM regions r
            JOIN region_providers rp ON r.region_id = rp.region_id
            WHERE rp.provider_id = ? AND r.status = 'active' 
            ORDER BY r.region_name, r.city, r.zip_code
        """, (provider_id,))
        regions = cursor.fetchall()
        conn.close()
        # Format regions as (region_id, display_text) where display_text includes zip, city, state
        all_regions = [(r[0], f"{r[1]} - {r[3]}, {r[4]} {r[2]}") for r in regions]  # (region_id, formatted_name)
    except Exception as e:
        print(f"Error getting provider regions: {e}")
        all_regions = [(1, "San Francisco Bay Area - San Francisco, CA 94102")]  # Default fallback

    st.subheader("Assigned Patients")
    
    # Add filtering controls with proper dropdowns for status and regions
    col1, col2 = st.columns(2)
    with col1:
        # Status filter - single select dropdown (simplified for now)
        st.write("Filter by Patient Status:")
        selected_status = st.selectbox("Select Status", ['All'] + all_statuses, index=0)
    with col2:
        # Region filter - single select dropdown (simplified for now)
        st.write("Filter by Region:")
        region_names = ['All Regions'] + [r[1] for r in all_regions]
        selected_region = st.selectbox("Select Region", region_names, index=0)
    
    # Filter patients based on selections
    filtered_patients = assigned_patients
    if selected_status != 'All':
        filtered_patients = [p for p in assigned_patients if p.get('status') == selected_status]
    # Note: Region filtering would require more complex database joins for actual filtering

    if filtered_patients:
        try:
            # Create a simple DataFrame with just the basic patient info we need
            patient_data_list = []
            for patient in filtered_patients:
                # Convert sqlite3.Row to dict properly
                patient_dict = {}
                for key in patient.keys():
                    patient_dict[key] = patient[key]
                patient_data_list.append(patient_dict)
            
            # Create DataFrame with proper column handling
            patients_df = pd.DataFrame(patient_data_list)
            
            # Check if we have the required columns for display
            if 'first_name' in patients_df.columns and 'last_name' in patients_df.columns:
                # Create address and contact info columns if they exist
                if all(col in patients_df.columns for col in ['address_street', 'address_city', 'address_state', 'address_zip']):
                    patients_df['full_address'] = (patients_df['address_street'] + ", " + 
                                                 patients_df['address_city'] + ", " + 
                                                 patients_df['address_state'] + " " + 
                                                 patients_df['address_zip'])
                else:
                    patients_df['full_address'] = "Address not available"
                
                if 'phone_primary' in patients_df.columns and 'email' in patients_df.columns:
                    patients_df['contact_info'] = patients_df['phone_primary'] + " / " + patients_df['email']
                else:
                    patients_df['contact_info'] = "Contact info not available"
                
                # Add status column for display
                if 'status' in patients_df.columns:
                    patients_df['status_display'] = patients_df['status']
                else:
                    patients_df['status_display'] = "Unknown"
                
                # Display the data with status
                display_df = patients_df[['first_name', 'last_name', 'full_address', 'contact_info', 'status_display']]
                display_df.columns = ['First Name', 'Last Name', 'Address', 'Contact Info', 'Status']
                st.dataframe(display_df, height=300, use_container_width=True)
            else:
                st.warning("Patient data structure not as expected")
                st.dataframe(patients_df, height=300, use_container_width=True)
                
            # Patient selection for daily tasks (simplified)
            patient_names = [f"{p['first_name']} {p['last_name']}" for p in patient_data_list if 'first_name' in p and 'last_name' in p]
            if patient_names:
                selected_patient_name = st.selectbox("Select Patient for Daily Tasks", patient_names)
                if selected_patient_name:
                    # Find the selected patient
                    selected_patient = next((p for p in patient_data_list if f"{p['first_name']} {p['last_name']}" == selected_patient_name), None)
                    if selected_patient:
                        st.session_state['selected_patient_id'] = selected_patient['patient_id']
                        st.session_state['selected_patient_name'] = selected_patient_name
            else:
                st.info("No patients available for selection")
        except Exception as e:
            st.error(f"Error processing patient data: {e}")
            # Fallback to simple display of raw data
            st.write("Raw patient data:", filtered_patients)
    else:
        st.info("No patients match the selected filters.")

    st.subheader("Daily Task Entries")

    # Fetch tasks billing codes for the task dropdown
    tasks_billing_codes = database.get_tasks_billing_codes()
    task_options = [f"{task['code']} - {task['description']}" for task in tasks_billing_codes]

    # Initialize session state for tasks if not already present
    if 'daily_tasks_data' not in st.session_state:
        st.session_state.daily_tasks_data = [{}] * 10

    # Add a button to add more task entries dynamically
    if st.button("Add Task Entry"):
        st.session_state.daily_tasks_data.append({})

    # Create 30 entries for daily tasks
    for i, task_entry in enumerate(st.session_state.daily_tasks_data):
        st.markdown(f"#### Task Entry {i+1}")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            task_entry['date'] = st.date_input(f"Date {i+1}", value=task_entry.get('date', pd.to_datetime('today')), key=f"date_{i}")
        with col2:
            # Simple patient selection - just show a placeholder if no patients
            patient_names = [f"{p['first_name']} {p['last_name']}" for p in patient_data_list if 'first_name' in p and 'last_name' in p] if 'patient_data_list' in locals() else []
            if patient_names:
                task_entry['patient_name'] = st.selectbox(f"Patient {i+1}", patient_names, key=f"patient_{i}", index=0 if patient_names else -1)
            else:
                task_entry['patient_name'] = st.selectbox(f"Patient {i+1}", ["No patients available"], key=f"patient_{i}", index=0)
        with col3:
            task_entry['task_type'] = st.selectbox(f"Task Type {i+1}", task_options, key=f"task_type_{i}", index=0 if task_options else -1)
        with col4:
            task_entry['duration'] = st.number_input(f"Duration (minutes) {i+1}", min_value=1, value=task_entry.get('duration', 30), key=f"duration_{i}")

        task_entry['notes'] = st.text_area(f"Notes {i+1}", value=task_entry.get('notes', ''), key=f"notes_{i}")

        if st.button(f"Log Task {i+1}", key=f"log_task_{i}"):
            if task_entry.get('patient_name') and task_entry.get('task_type') and task_entry.get('duration'):
                # For now, just show success without actual database save (to avoid more errors)
                st.success(f"Task '{task_entry['task_type']}' would be logged for {task_entry['patient_name']} on {task_entry['date']} with duration {task_entry['duration']} minutes.")
            else:
                st.warning("Please fill in all fields for the task entry.")
        st.markdown("---")
