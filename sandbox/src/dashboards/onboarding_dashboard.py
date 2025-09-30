import streamlit as st
from src.dashboards.dashboard_display_config import ST_DF_AUTOSIZE_COLUMNS
import pandas as pd
from src import database
from datetime import datetime

# Define the onboarding workflow steps
ONBOARDING_STEPS = [
    {"step": 1, "title": "Patient Registration", "description": "Initial patient data entry", "stage_field": "stage1_complete"},
    {"step": 2, "title": "Eligibility Verification", "description": "Insurance and eligibility check", "stage_field": "stage2_complete"},
    {"step": 3, "title": "Chart Creation", "description": "Patient chart setup", "stage_field": "stage3_complete"},
    {"step": 4, "title": "Intake Processing", "description": "Medical records and documentation", "stage_field": "stage4_complete"},
    {"step": 5, "title": "TV Visit Scheduling", "description": "Telemedicine appointment setup", "stage_field": "stage5_complete"}
]

def show_workflow_stepper(patient_data):
    """Display a visual stepper showing the current progress of the onboarding workflow"""
    st.markdown("### Onboarding Progress")
    
    # Determine current step based on completion status
    current_step = 1
    for i, step_info in enumerate(ONBOARDING_STEPS):
        stage_field = step_info["stage_field"]
        if patient_data.get(stage_field, False):
            current_step = i + 2  # Next step after completed ones
        else:
            current_step = i + 1  # Current step to work on
            break
    
    # Cap at maximum step
    if current_step > len(ONBOARDING_STEPS):
        current_step = len(ONBOARDING_STEPS)
    
    # Create stepper visualization using columns
    cols = st.columns(len(ONBOARDING_STEPS))
    
    for i, (col, step_info) in enumerate(zip(cols, ONBOARDING_STEPS)):
        step_num = step_info["step"]
        title = step_info["title"]
        description = step_info["description"]
        is_completed = patient_data.get(step_info["stage_field"], False)
        is_current = step_num == current_step
        is_future = step_num > current_step
        
        with col:
            # Step circle styling
            if is_completed:
                circle_style = "background-color: #28a745; color: white;"
                icon = "✓"
            elif is_current:
                circle_style = "background-color: #007bff; color: white;"
                icon = str(step_num)
            else:
                circle_style = "background-color: #e9ecef; color: #6c757d;"
                icon = str(step_num)
            
            # Create the step circle
            st.markdown(f"""
                <div style="text-align: center; margin-bottom: 10px;">
                    <div style="
                        width: 40px; 
                        height: 40px; 
                        border-radius: 50%; 
                        {circle_style}
                        display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        font-weight: bold; 
                        margin: 0 auto;
                        font-size: 14px;
                    ">{icon}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Step title and description
            if is_current:
                st.markdown(f"**{title}**")
                st.markdown(f"<small style='color: #007bff;'>{description}</small>", unsafe_allow_html=True)
            elif is_completed:
                st.markdown(f"<span style='color: #28a745;'><b>{title}</b></span>", unsafe_allow_html=True)
                st.markdown(f"<small style='color: #28a745;'>{description}</small>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color: #6c757d;'>{title}</span>", unsafe_allow_html=True)
                st.markdown(f"<small style='color: #6c757d;'>{description}</small>", unsafe_allow_html=True)
    
    # Progress bar
    progress_percentage = ((current_step - 1) / len(ONBOARDING_STEPS))
    if patient_data.get('stage5_complete', False):  # All stages complete
        progress_percentage = 1.0
    
    st.progress(progress_percentage)
    
    # Status text
    if progress_percentage == 1.0:
        st.success("Onboarding workflow completed!")
    else:
        completed_steps = sum(1 for step in ONBOARDING_STEPS if patient_data.get(step["stage_field"], False))
        st.info(f"Progress: {completed_steps}/{len(ONBOARDING_STEPS)} steps completed")
    
    return current_step

def get_patient_current_stage_name(patient_data):
    """Get the current stage name for a patient based on their completion status"""
    for i, step_info in enumerate(ONBOARDING_STEPS):
        if not patient_data.get(step_info["stage_field"], False):
            return step_info["title"]
    return "Workflow Complete"

def show_patient_intake_form(current_user_id):
    """Show new patient intake form for Stage 1 registration"""
    with st.form("patient_intake_form"):
        # Basic Patient Information
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name*", key="first_name")
            last_name = st.text_input("Last Name*", key="last_name")
            date_of_birth = st.date_input("Date of Birth*", key="dob")
            phone_primary = st.text_input("Primary Phone*", key="phone_primary")
            
        with col2:
            email = st.text_input("Email", key="email")
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"], key="gender")
            emergency_contact = st.text_input("Emergency Contact Name", key="emergency_contact")
            emergency_phone = st.text_input("Emergency Contact Phone", key="emergency_phone")
        
        # Address Information
        st.markdown("### Address Information")
        address_street = st.text_input("Street Address*", key="address_street")
        address_city = st.text_input("City*", key="address_city")
        address_state = st.selectbox("State*", ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA"], key="address_state")
        address_zip = st.text_input("ZIP Code*", key="address_zip")
        
        # Insurance Information
        st.markdown("### Insurance Information")
        insurance_provider = st.text_input("Primary Insurance Provider", key="insurance_provider")
        policy_number = st.text_input("Policy Number", key="policy_number")
        group_number = st.text_input("Group Number", key="group_number")
        
        # Referral Information
        st.markdown("### Referral Information")
        referral_source = st.text_input("Referral Source", key="referral_source")
        referring_provider = st.text_input("Referring Provider", key="referring_provider")
        referral_date = st.date_input("Referral Date", key="referral_date")
        
        # Patient Status and Facility Assignment
        st.markdown("### Patient Status & Assignment")
        patient_status = st.selectbox("Patient Status", ["Active", "Inactive", "Deceased"], key="patient_status")
        
        # Facility Assignment - Get facilities from database
        try:
            conn = database.get_db_connection()
            facilities = conn.execute("SELECT facility_name FROM facilities ORDER BY facility_name").fetchall()
            conn.close()
            facility_options = [f[0] for f in facilities] if facilities else []
            facility_options.append("Add New Facility")
        except Exception as e:
            facility_options = ["San Francisco", "Los Angeles", "San Diego", "Sacramento", "Add New Facility"]
            
        facility_assignment = st.selectbox("Referring Facility", facility_options, key="facility_assignment")
        # Appointment & Medical Contact (P0 additions)
        st.markdown("### Appointment & Medical Contacts")
        appointment_contact_name = st.text_input("Appointment Contact Name", key="appointment_contact_name")
        appointment_contact_phone = st.text_input("Appointment Contact Phone", key="appointment_contact_phone")
        appointment_contact_email = st.text_input("Appointment Contact Email", key="appointment_contact_email")
        medical_contact_name = st.text_input("Medical Contact Name", key="medical_contact_name")
        medical_contact_phone = st.text_input("Medical Contact Phone", key="medical_contact_phone")
        medical_contact_email = st.text_input("Medical Contact Email", key="medical_contact_email")
        
        # Submit button
        col1, col2 = st.columns([1, 4])
        with col1:
            submitted = st.form_submit_button("Start Workflow", type="primary")
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state['show_intake_form'] = False
                st.session_state['onboarding_mode'] = None
                st.rerun()
        
        if submitted:
            if not first_name or not last_name or not date_of_birth or not phone_primary or not address_street or not address_city or not address_zip:
                st.error("Please fill in all required fields (marked with *)")
            else:
                try:
                    # Create patient data dictionary
                    patient_data = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'date_of_birth': date_of_birth.isoformat(),
                        'phone_primary': phone_primary,
                        'email': email,
                        'gender': gender,
                        'emergency_contact_name': emergency_contact,
                        'emergency_contact_phone': emergency_phone,
                        'address_street': address_street,
                        'address_city': address_city,
                        'address_state': address_state,
                        'address_zip': address_zip,
                        'insurance_provider': insurance_provider,
                        'policy_number': policy_number,
                        'group_number': group_number,
                        'referral_source': referral_source,
                        'referring_provider': referring_provider,
                        'referral_date': referral_date.isoformat() if referral_date else None,
                        'patient_status': patient_status,
                        'facility_assignment': facility_assignment if facility_assignment != "Add New Facility" else None
                    }
                    
                    # Create onboarding workflow instance
                    onboarding_id = database.create_onboarding_workflow_instance(patient_data, current_user_id)
                    
                    st.success(f"Patient {first_name} {last_name} onboarding workflow started!")
                    
                    # Mark Stage 1 as complete since we just completed registration
                    database.update_onboarding_stage_completion(onboarding_id, 1, True)
                    # Persist additional appointment/medical contact fields
                    database.update_onboarding_checkbox_data(onboarding_id, {
                        'appointment_contact_name': appointment_contact_name,
                        'appointment_contact_phone': appointment_contact_phone,
                        'appointment_contact_email': appointment_contact_email,
                        'medical_contact_name': medical_contact_name,
                        'medical_contact_phone': medical_contact_phone,
                        'medical_contact_email': medical_contact_email
                    })
                    
                    # Clear the intake form flag and switch to resume mode for next stage
                    st.session_state['show_intake_form'] = False
                    st.session_state['current_onboarding_id'] = onboarding_id
                    st.session_state['onboarding_mode'] = 'resume'
                    st.info("Proceeding to Stage 2: Eligibility Verification...")
                    st.rerun()
                        
                except Exception as e:
                    st.error(f"Error creating onboarding workflow: {e}")

def show_resume_onboarding_form(patient_details, current_user_id):
    """Show form for resuming existing onboarding with current state"""
    
    # Patient header info
    patient_name = f"{patient_details['first_name']} {patient_details['last_name']}"
    st.subheader(f"Continue Onboarding: {patient_name}")
    
    # Progress indicator
    stages = ['Registration', 'Eligibility', 'Chart Creation', 'Intake Processing', 'TV Scheduling']
    # Compute how many steps are completed
    completed_steps = sum(1 for s in stages if patient_details.get(f'stage{stages.index(s)+1}_complete', False))

    # If all steps complete, show handoff
    if completed_steps >= len(stages):
        st.success("All stages complete! Ready for handoff to PCPM.")
        if st.button("Complete Handoff"):
            # Mark as completed
            conn = database.get_db_connection()
            conn.execute("UPDATE onboarding_patients SET completed_date = datetime('now') WHERE onboarding_id = ?", 
                        (patient_details['onboarding_id'],))
            conn.commit()
            conn.close()
            st.session_state['onboarding_mode'] = None
            st.success("Patient successfully handed off to PCPM!")
            st.rerun()
        return

    # Otherwise show next incomplete stage
    current_stage = completed_steps + 1

    # Show progress bar
    progress_text = f"Stage {current_stage}/5: {stages[current_stage-1]}"
    st.progress((current_stage - 1) / len(stages))
    st.info(progress_text)

    # Stage-specific forms
    if current_stage == 1:
        st.info("Registration not yet completed. Please complete Stage 1 registration before proceeding.")
    elif current_stage == 2:
        show_eligibility_verification_form(patient_details, current_user_id)
    elif current_stage == 3:
        show_chart_creation_form(patient_details, current_user_id)
    elif current_stage == 4:
        show_intake_processing_form(patient_details, current_user_id)
    elif current_stage == 5:
        show_tv_scheduling_form(patient_details, current_user_id)

def show_eligibility_verification_form(patient_details, current_user_id):
    """Stage 2: Eligibility Verification"""
    st.markdown("### Stage 2: Insurance Eligibility Verification")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("Verify patient's insurance coverage and eligibility status")
        
    with col2:
        # Patient info card
        with st.expander("Patient Info", expanded=False):
            st.write(f"**Insurance:** {patient_details.get('insurance_provider', 'N/A')}")
            st.write(f"**Policy #:** {patient_details.get('policy_number', 'N/A')}")
            st.write(f"**Group #:** {patient_details.get('group_number', 'N/A')}")
    
    with st.form("eligibility_form"):
        st.markdown("#### Eligibility Check")
        
        eligibility_status = st.selectbox(
            "Eligibility Status*", 
            ["Eligible", "Not Eligible", "Pending Verification", "Needs Follow-up"],
            key="eligibility_status"
        )
        
        eligibility_verified = st.checkbox("Eligibility Verified", key="eligibility_verified")
        
        eligibility_notes = st.text_area(
            "Verification Notes", 
            placeholder="Enter details about insurance verification, coverage limitations, etc.",
            key="eligibility_notes"
        )

        # Stage 2 additions: Primary care and mental health checkboxes
        st.markdown("### Clinical & Mental Health Intake")
        primary_care_provider = st.text_input("Primary Care Provider", key="primary_care_provider")
        pcp_last_seen = st.date_input("PCP Last Seen", key="pcp_last_seen")

        st.markdown("#### Mental Health Conditions (check all that apply)")
        mh_schizophrenia = st.checkbox("Schizophrenia", key="mh_schizophrenia")
        mh_depression = st.checkbox("Depression", key="mh_depression")
        mh_anxiety = st.checkbox("Anxiety", key="mh_anxiety")
        mh_stress = st.checkbox("Stress", key="mh_stress")
        mh_adhd = st.checkbox("ADHD", key="mh_adhd")
        mh_bipolar = st.checkbox("Bipolar", key="mh_bipolar")
        mh_suicidal = st.checkbox("Suicidal Ideation", key="mh_suicidal")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.form_submit_button("Complete Stage 2", type="primary"):
                # Save eligibility and clinical fields (always save data)
                checkbox_payload = {
                    'eligibility_status': eligibility_status,
                    'eligibility_notes': eligibility_notes,
                    'eligibility_verified': eligibility_verified,
                    'mh_schizophrenia': mh_schizophrenia,
                    'mh_depression': mh_depression,
                    'mh_anxiety': mh_anxiety,
                    'mh_stress': mh_stress,
                    'mh_adhd': mh_adhd,
                    'mh_bipolar': mh_bipolar,
                    'mh_suicidal': mh_suicidal,
                    'primary_care_provider': primary_care_provider,
                    'pcp_last_seen': pcp_last_seen.strftime('%Y-%m-%d') if pcp_last_seen else None,
                }
                database.update_onboarding_checkbox_data(patient_details['onboarding_id'], checkbox_payload)
                st.success('Stage 2 data saved')

                if eligibility_verified:
                    # Mark stage complete and update related tasks
                    database.update_onboarding_stage_completion(patient_details['onboarding_id'], 2, True)

                    # Update task status - find eligibility tasks and mark complete
                    tasks = patient_details.get('tasks', [])
                    for task in tasks:
                        if task['task_stage'] == 2:
                            database.update_onboarding_task_status(
                                task['task_id'], 'Complete', current_user_id,
                                {'eligibility_verified': True}
                            )

                    st.success("Stage 2 Complete! Moving to Chart Creation...")
                    st.rerun()
                else:
                    st.error("Eligibility not verified. Data saved—please verify eligibility to proceed.")
        
        with col2:
            if st.form_submit_button("Save Progress"):
                # Save progress for Stage 2 (eligibility/clinical fields)
                checkbox_payload = {
                    'eligibility_status': eligibility_status,
                    'eligibility_notes': eligibility_notes,
                    'eligibility_verified': eligibility_verified,
                    'primary_care_provider': primary_care_provider,
                    'pcp_last_seen': pcp_last_seen.strftime('%Y-%m-%d') if pcp_last_seen else None,
                    'mh_schizophrenia': mh_schizophrenia,
                    'mh_depression': mh_depression,
                    'mh_anxiety': mh_anxiety,
                    'mh_stress': mh_stress,
                    'mh_adhd': mh_adhd,
                    'mh_bipolar': mh_bipolar,
                    'mh_suicidal': mh_suicidal
                }
                database.update_onboarding_checkbox_data(patient_details['onboarding_id'], checkbox_payload)
                st.info("Progress saved! You can resume later.")
        
        with col3:
            if st.form_submit_button("Back to Queue"):
                st.session_state['onboarding_mode'] = None
                st.rerun()

def show_chart_creation_form(patient_details, current_user_id):
    """Stage 3: EMed Chart Creation"""
    st.markdown("### Stage 3: EMed Chart Creation")
    
    with st.form("chart_creation_form"):
        st.info("Create patient chart in EMed system and assign facility")
        
        emed_chart_created = st.checkbox("EMed Chart Created", key="emed_chart_created")
        chart_id = st.text_input("EMed Chart ID", key="chart_id", help="Enter the EMed chart ID number")
        facility_confirmed = st.checkbox("Facility Assignment Confirmed", key="facility_confirmed")
        
        chart_notes = st.text_area(
            "Chart Creation Notes",
            placeholder="Enter any notes about chart creation, facility assignment, or issues encountered",
            key="chart_notes"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.form_submit_button("Complete Stage 3", type="primary"):
                if emed_chart_created and facility_confirmed:
                    database.update_onboarding_stage_completion(patient_details['onboarding_id'], 3, True)
                    
                    # Update tasks
                    tasks = patient_details.get('tasks', [])
                    for task in tasks:
                        if task['task_stage'] == 3:
                            database.update_onboarding_task_status(
                                task['task_id'], 'Complete', current_user_id,
                                {'emed_chart_created': True}
                            )
                    
                    st.success("Stage 3 Complete! Moving to Intake Processing...")
                    st.rerun()
                else:
                    st.error("Please confirm chart creation and facility assignment.")
        
        with col2:
            if st.form_submit_button("Save Progress"):
                st.info("Progress saved!")
        
        with col3:
            if st.form_submit_button("Back to Queue"):
                st.session_state['onboarding_mode'] = None
                st.rerun()

def show_intake_processing_form(patient_details, current_user_id):
    """Stage 4: Intake Processing & Documentation"""
    st.markdown("### Stage 4: Intake Processing & Documentation")
    
    with st.form("intake_processing_form"):
        st.info("Complete patient intake, collect documentation, and conduct intake call")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Documentation")
            medical_records_requested = st.checkbox("Medical Records Requested", 
                                                   key="medical_records_requested",
                                                   value=patient_details.get('medical_records_requested', False))
            referral_documents_received = st.checkbox("Referral Documents Received", 
                                                     key="referral_documents_received",
                                                     value=patient_details.get('referral_documents_received', False))
            insurance_cards_received = st.checkbox("Insurance Cards / Face Sheet Received", 
                                                  key="insurance_cards_received",
                                                  value=patient_details.get('insurance_cards_received', False))
            emed_signature_received = st.checkbox("EMED Signature Received", 
                                                key="emed_signature_received",
                                                value=patient_details.get('emed_signature_received', False))
            annual_well_visit = st.checkbox("Annual Well Visit", 
                                           key="annual_well_visit",
                                           value=patient_details.get('annual_well_visit', False))
        
        with col2:
            st.markdown("#### Patient Contact")
            intake_call_completed = st.checkbox("Intake Call Completed", key="intake_call_completed")
            
        intake_notes = st.text_area(
            "Intake Processing Notes",
            placeholder="Document any issues with medical records, patient contact attempts, special requirements, etc.",
            key="intake_notes"
        )
        # Stage 4 additions: Specialist and chronic conditions
        st.markdown("### Specialist & Clinical Conditions")
        active_specialist = st.text_input("Active Specialist", key="active_specialist")
        specialist_last_seen = st.date_input("Specialist Last Seen", key="specialist_last_seen")
        chronic_conditions_onboarding = st.text_area("Chronic Conditions (comma-separated)", key="chronic_conditions_onboarding")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.form_submit_button("Complete Stage 4", type="primary"):
                # Save intake processing checkbox/fields
                database.update_onboarding_checkbox_data(patient_details['onboarding_id'], {
                    'medical_records_requested': medical_records_requested,
                    'referral_documents_received': referral_documents_received,
                    'insurance_cards_received': insurance_cards_received,
                    'emed_signature_received': emed_signature_received,
                    'annual_well_visit': annual_well_visit,
                    'intake_notes': intake_notes,
                    'active_specialist': active_specialist,
                    'specialist_last_seen': specialist_last_seen.strftime('%Y-%m-%d') if specialist_last_seen else None,
                    'chronic_conditions_onboarding': chronic_conditions_onboarding
                })

                # Save all checkbox data
                checkbox_data = {
                    'medical_records_requested': medical_records_requested,
                    'referral_documents_received': referral_documents_received,
                    'insurance_cards_received': insurance_cards_received,
                    'emed_signature_received': emed_signature_received,
                    'annual_well_visit': annual_well_visit
                }
                database.update_onboarding_checkbox_data(patient_details['onboarding_id'], checkbox_data)

                # Require BOTH intake call completion AND insurance cards/face sheet before completing
                if intake_call_completed and insurance_cards_received:
                    database.update_onboarding_stage_completion(patient_details['onboarding_id'], 4, True)

                    # Update tasks
                    tasks = patient_details.get('tasks', [])
                    for task in tasks:
                        if task['task_stage'] == 4:
                            database.update_onboarding_task_status(
                                task['task_id'], 'Complete', current_user_id,
                                {'intake_call_completed': True, 'documents_received': True}
                            )

                    st.success("Stage 4 Complete! Moving to TV Scheduling...")
                    st.rerun()
                else:
                    st.error("Please complete the intake call and confirm insurance cards/face sheet are received before proceeding.")
        
        with col2:
            if st.form_submit_button("Save Progress"):
                # Save checkbox data and clinical fields when saving progress
                checkbox_data = {
                    'medical_records_requested': medical_records_requested,
                    'referral_documents_received': referral_documents_received,
                    'insurance_cards_received': insurance_cards_received,
                    'emed_signature_received': emed_signature_received,
                    'annual_well_visit': annual_well_visit,
                    'intake_notes': intake_notes,
                    'intake_call_completed': intake_call_completed,
                    'active_specialist': active_specialist,
                    'specialist_last_seen': specialist_last_seen.strftime('%Y-%m-%d') if specialist_last_seen else None,
                    'chronic_conditions_onboarding': chronic_conditions_onboarding
                }
                database.update_onboarding_checkbox_data(patient_details['onboarding_id'], checkbox_data)
                st.info("Progress saved!")
        
        with col3:
            if st.form_submit_button("Back to Queue"):
                st.session_state['onboarding_mode'] = None
                st.rerun()

def show_tv_scheduling_form(patient_details, current_user_id):
    """Stage 5: TV Scheduling & Provider + Coordinator Assignments"""
    st.markdown("### Stage 5: TV Scheduling & Provider + Coordinator Assignments")
    
    with st.form("tv_scheduling_form"):
        st.info("Schedule initial telehealth visit and assign provider and coordinator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### TV Scheduling")
            tv_scheduled = st.checkbox("Initial TV Scheduled", key="tv_scheduled")
            tv_date = st.date_input("TV Appointment Date", key="tv_date")
            tv_time = st.time_input("TV Appointment Time", key="tv_time")
            patient_notified = st.checkbox("Patient Notified of TV Appointment", key="patient_notified")
            initial_tv_completed = st.checkbox("Initial TV Visit Completed", key="initial_tv_completed")
            
        with col2:
            st.markdown("#### Provider Assignment for Initial TV")
            # Get Provider users from database
            try:
                provider_users = database.get_users_by_role("CP")  # Use role abbreviation CP for Care Provider
                provider_options = ["Select Provider..."] + [f"{u['full_name']} ({u['username']})" for u in provider_users] if provider_users else ["No Providers Available"]
            except:
                provider_options = ["Provider Assignment Needed"]
                
            assigned_provider = st.selectbox("Assign Provider", provider_options, key="assigned_provider")
        
        # Additional assignment sections
        st.markdown("#### Post-Initial TV Assignments")
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("**Regional Provider Assignment**")
            try:
                regional_provider_users = database.get_users_by_role("CP")  # Use CP role for providers
                regional_provider_options = ["Select Regional Provider..."] + [f"{u['full_name']} ({u['username']})" for u in regional_provider_users] if regional_provider_users else ["No Providers Available"]
            except:
                regional_provider_options = ["Regional Provider Assignment Needed"]
            
            assigned_regional_provider = st.selectbox("Assign Regional Provider", regional_provider_options, key="assigned_regional_provider")
        
        with col4:
            st.markdown("**Coordinator Assignment**")
            try:
                coordinator_users = database.get_users_by_role("CC")  # Use CC role for Care Coordinators
                coordinator_options = ["Select Coordinator..."] + [f"{u['full_name']} ({u['username']})" for u in coordinator_users] if coordinator_users else ["No Coordinators Available"]
            except:
                coordinator_options = ["Coordinator Assignment Needed"]
            
            assigned_coordinator = st.selectbox("Assign Coordinator", coordinator_options, key="assigned_coordinator")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.form_submit_button("Complete Stage 5", type="primary"):
                # Revised completion requirements: Check if regional provider and coordinator are assigned in patient table
                # (not just the onboarding form fields)
                
                # Check if patient exists in patients table and has regional provider + coordinator assigned
                patient_id = patient_details.get('patient_id')
                regional_provider_assigned = False
                coordinator_assigned_in_patient_table = False
                
                if patient_id:
                    conn = database.get_db_connection()
                    try:
                        # Check for regional provider assignment in patient table
                        cursor = conn.execute("""
                            SELECT upa.user_id, u.full_name 
                            FROM user_patient_assignments upa
                            JOIN users u ON upa.user_id = u.user_id
                            JOIN user_roles ur ON u.user_id = ur.user_id
                            WHERE upa.patient_id = ? AND ur.role_id = 33
                        """, (patient_id,))
                        regional_provider = cursor.fetchone()
                        regional_provider_assigned = regional_provider is not None
                        
                        # Check for coordinator assignment in patient table  
                        cursor = conn.execute("""
                            SELECT upa.user_id, u.full_name
                            FROM user_patient_assignments upa
                            JOIN users u ON upa.user_id = u.user_id
                            JOIN user_roles ur ON u.user_id = ur.user_id
                            WHERE upa.patient_id = ? AND ur.role_id = 34
                        """, (patient_id,))
                        coordinator = cursor.fetchone()
                        coordinator_assigned_in_patient_table = coordinator is not None
                        
                    except Exception as e:
                        st.error(f"Error checking patient assignments: {e}")
                    finally:
                        conn.close()
                
                # New completion requirements: Basic onboarding steps PLUS regional provider and coordinator in patient table
                basic_requirements_met = tv_scheduled and patient_notified and initial_tv_completed
                assignments_complete = regional_provider_assigned and coordinator_assigned_in_patient_table
                
                if basic_requirements_met and assignments_complete:
                    # Save Stage 5 data including provider assignment
                    database.update_onboarding_stage5_completion(
                        patient_details['onboarding_id'], 
                        tv_date, 
                        tv_time, 
                        assigned_provider, 
                        assigned_coordinator
                    )
                    
                    # Add patient to patients table and keep onboarding data
                    try:
                        database.insert_patient_from_onboarding(patient_details['onboarding_id'])
                    except Exception as e:
                        st.warning(f"Patient table insertion warning: {e}")
                    
                    database.update_onboarding_stage_completion(patient_details['onboarding_id'], 5, True)
                    
                    # Update tasks
                    tasks = patient_details.get('tasks', [])
                    for task in tasks:
                        if task['task_stage'] == 5:
                            database.update_onboarding_task_status(
                                task['task_id'], 'Complete', current_user_id,
                                {
                                    'tv_scheduled': True, 
                                    'initial_tv_completed': True,
                                    'provider_assigned': True,
                                    'coordinator_assigned': True
                                }
                            )
                    
                    st.success("Stage 5 Complete! Patient onboarding workflow finished.")
                    st.balloons()
                    st.session_state['onboarding_mode'] = None
                    st.rerun()
                else:
                    # Provide detailed error message about what's missing
                    missing_items = []
                    if not tv_scheduled:
                        missing_items.append("TV visit scheduled")
                    if not patient_notified:
                        missing_items.append("Patient notified")
                    if not initial_tv_completed:
                        missing_items.append("Initial TV visit completed")
                    if not regional_provider_assigned:
                        missing_items.append("Regional provider assigned in patient table (by onboarding team)")
                    if not coordinator_assigned_in_patient_table:
                        missing_items.append("Coordinator assigned in patient table (by onboarding team)")
                    
                    error_msg = "Cannot complete onboarding. Missing: " + ", ".join(missing_items)
                    st.error(error_msg)
                    
                    if not assignments_complete:
                        st.warning("⚠️ **Revised Workflow**: The onboarding team must assign a regional provider and coordinator in the patient table before onboarding can be completed. The 'Save Progress' button can be used to save partial progress.")
        
        with col2:
            if st.form_submit_button("Save Progress"):
                # Collect form data
                form_data = {
                    'tv_date': tv_date,
                    'tv_time': tv_time,
                    'assigned_provider': assigned_provider,
                    'assigned_coordinator': assigned_coordinator,
                    'tv_scheduled': tv_scheduled,
                    'patient_notified': patient_notified,
                    'initial_tv_completed': initial_tv_completed
                }
                
                # Save the progress to database
                if database.save_onboarding_tv_scheduling_progress(patient_details['onboarding_id'], form_data):
                    st.success("✅ Progress saved successfully! Your changes have been saved to the database.")
                    # Refresh the patient details to show updated data
                    st.session_state['view_patient_details'] = database.get_onboarding_patient_details(patient_details['onboarding_id'])
                    st.rerun()
                else:
                    st.error("❌ Failed to save progress. Please try again.")
        
        with col3:
            if st.form_submit_button("Back to Queue"):
                st.session_state['onboarding_mode'] = None
                st.rerun()

def show():
    st.title("Patient Onboarding Dashboard")
    
    # Get current user ID for POT assignment
    current_user_id = st.session_state.get('user_id', None)
    if not current_user_id:
        st.error("Please log in to access the onboarding dashboard.")
        return
    
    # Create tabs - Queue first!
    tab1, tab2, tab3 = st.tabs(["Patient Queue", "Processing Status", "Facility Management"])
    
    # Tab 1: Patient Queue (Primary Tab)
    with tab1:
        st.subheader("Patient Onboarding Queue")
        
        # Get current onboarding queue
        try:
            onboarding_queue = database.get_onboarding_queue()
            
            if onboarding_queue:
                # Create DataFrame for display
                queue_df = pd.DataFrame(onboarding_queue)
                
                # Format display columns
                display_df = pd.DataFrame({
                    "Patient": queue_df['patient_name'],
                    "Current Stage": queue_df['current_stage'], 
                    "Priority": queue_df['priority_status'],
                    "Assigned POT": queue_df['assigned_pot_name'].fillna('Unassigned'),
                    "Created": pd.to_datetime(queue_df['created_date']).dt.strftime('%m/%d/%Y'),
                    "Last Update": pd.to_datetime(queue_df['updated_date']).dt.strftime('%m/%d/%Y %H:%M')
                })
                
                st.dataframe(
                    display_df, 
                    use_container_width=True,
                    column_config={
                        "Patient ID": st.column_config.NumberColumn("Patient ID", format="%.0f", width="small"),
                        "First Name": st.column_config.TextColumn("First Name", width="medium"),
                        "Last Name": st.column_config.TextColumn("Last Name", width="medium"),
                        "Stage": st.column_config.TextColumn("Stage", width="medium"),
                        "Priority": st.column_config.TextColumn("Priority", width="small"),
                        "Status": st.column_config.TextColumn("Status", width="small"),
                        "Created": st.column_config.TextColumn("Created", width="small"),
                        "Last Update": st.column_config.TextColumn("Last Update", width="medium")
                    },
                    hide_index=True,
                    autosize_columns=ST_DF_AUTOSIZE_COLUMNS
                )
                
                # Patient selection for actions
                if len(onboarding_queue) > 0:
                    st.markdown("### Quick Actions")
                    
                    # Patient selector
                    patient_options = {f"{row['patient_name']} - {row['current_stage']}": row['onboarding_id'] 
                                     for row in onboarding_queue}
                    
                    selected_patient = st.selectbox(
                        "Select Patient for Action:",
                        options=list(patient_options.keys()),
                        key="selected_patient_queue"
                    )
                    
                    if selected_patient:
                        selected_id = patient_options[selected_patient]
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("Resume Onboarding", key="resume_onboarding"):
                                st.session_state['current_onboarding_id'] = selected_id
                                st.session_state['onboarding_mode'] = 'resume'
                                st.success(f"Loaded patient onboarding for: {selected_patient.split(' - ')[0]}")
                                st.rerun()
                        
                        with col2:
                            if st.button("View Details", key="view_details"):
                                patient_details = database.get_onboarding_patient_details(selected_id)
                                if patient_details:
                                    st.session_state['view_patient_details'] = patient_details
                                    st.rerun()
                        
                        with col3:
                            if st.button("Assign to Me", key="assign_to_me"):
                                database.update_onboarding_patient_assignment(selected_id, current_user_id)
                                st.success("Patient assigned to you!")
                                st.rerun()
                        
                        # Show patient workflow stepper if details are being viewed
                        if 'view_patient_details' in st.session_state:
                            patient_details = st.session_state['view_patient_details']
                            
                            # Only show if it's the same patient
                            if patient_details['onboarding_id'] == selected_id:
                                st.markdown("---")
                                st.markdown(f"## 👤 {patient_details['first_name']} {patient_details['last_name']}")
                                
                                # Show workflow stepper
                                current_step = show_workflow_stepper(patient_details)
                                
                                # Patient details in expandable sections
                                with st.expander("Patient Information", expanded=False):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**DOB:** {patient_details.get('date_of_birth', 'N/A')}")
                                        st.write(f"**Phone:** {patient_details.get('phone_primary', 'N/A')}")
                                        st.write(f"**Email:** {patient_details.get('email', 'N/A')}")
                                        st.write(f"**Gender:** {patient_details.get('gender', 'N/A')}")
                                    with col2:
                                        st.write(f"**Address:** {patient_details.get('address_street', '')}")
                                        st.write(f"**City, State ZIP:** {patient_details.get('address_city', '')} {patient_details.get('address_state', '')} {patient_details.get('address_zip', '')}")
                                        st.write(f"**Insurance:** {patient_details.get('insurance_provider', 'N/A')}")
                                        st.write(f"**Facility:** {patient_details.get('facility_assignment', 'N/A')}")
                                
                                with st.expander("Medical Information", expanded=False):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Hypertension:** {'Yes' if patient_details.get('hypertension', False) else 'No'}")
                                        st.write(f"**Mental Health Concerns:** {'Yes' if patient_details.get('mental_health_concerns', False) else 'No'}")
                                    with col2:
                                        st.write(f"**Dementia:** {'Yes' if patient_details.get('dementia', False) else 'No'}")
                                        st.write(f"**Emergency Contact:** {patient_details.get('emergency_contact_name', 'N/A')}")
                                
                                with st.expander("📄 Document Status", expanded=False):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Medical Records:** {'Received' if patient_details.get('medical_records_requested', False) else 'Pending'}")
                                        st.write(f"**Referral Documents:** {'Received' if patient_details.get('referral_documents_received', False) else 'Pending'}")
                                    with col2:
                                        st.write(f"**Insurance Cards:** {'Received' if patient_details.get('insurance_cards_received', False) else 'Pending'}")
                                        st.write(f"**eMed Signature:** {'Received' if patient_details.get('emed_signature_received', False) else 'Pending'}")
                                
                                # Action buttons for the current step
                                st.markdown("### 🎯 Next Actions")
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    if st.button("📝 Continue Workflow", key="continue_workflow"):
                                        st.session_state['current_onboarding_id'] = selected_id
                                        st.session_state['onboarding_mode'] = 'resume'
                                        st.success("Continuing workflow...")
                                        st.rerun()
                                
                                with col2:
                                    if st.button("✏️ Edit Patient Info", key="edit_patient"):
                                        st.session_state['current_onboarding_id'] = selected_id
                                        st.session_state['onboarding_mode'] = 'edit'
                                        st.success("Editing patient information...")
                                        st.rerun()
                                
                                with col3:
                                    if st.button("Assign POT", key="assign_pot"):
                                        # Add POT assignment logic here
                                        st.info("POT assignment functionality coming soon...")
                                
                                with col4:
                                    if st.button("❌ Close Details", key="close_details"):
                                        if 'view_patient_details' in st.session_state:
                                            del st.session_state['view_patient_details']
                                        st.rerun()
            else:
                st.info("No patients currently in the onboarding queue.")
                
        except Exception as e:
            st.error(f"Error loading onboarding queue: {e}")
        
        # Quick Start Section
        st.markdown("---")
        st.markdown("### Start New Patient Onboarding")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Begin the onboarding process for a new patient referral.")
        with col2:
            if st.button("🆕 Start New Patient", key="start_new_patient", type="primary"):
                st.session_state['show_intake_form'] = True
                st.success("Ready to start new patient onboarding!")
                st.rerun()
        
        # Show intake form popup at bottom of queue tab when requested
        if st.session_state.get('show_intake_form', False):
            st.markdown("---")
            st.markdown("## New Patient Registration - Stage 1")
            st.info("Complete the patient registration form to start the onboarding workflow.")
            
            # Show the intake form
            show_patient_intake_form(current_user_id)
            
            # Add a cancel button
            if st.button("❌ Cancel Registration", key="cancel_registration"):
                st.session_state['show_intake_form'] = False
                st.rerun()
        
        # Handle resume onboarding mode in the queue tab
        onboarding_mode = st.session_state.get('onboarding_mode', None)
        current_onboarding_id = st.session_state.get('current_onboarding_id', None)
        
        if onboarding_mode == 'resume' and current_onboarding_id:
            st.markdown("---")
            # Load existing patient data and show appropriate stage form
            patient_details = database.get_onboarding_patient_details(current_onboarding_id)
            if patient_details:
                show_resume_onboarding_form(patient_details, current_user_id)
            else:
                st.error("Could not load patient details for onboarding.")
                st.session_state['onboarding_mode'] = None

    # Tab 2: Processing Status 
    with tab2:
        st.subheader("Onboarding Processing Status")
        
        # Get processing status data from database
        try:
            onboarding_queue = database.get_onboarding_queue()
            
            if onboarding_queue:
                # Calculate status metrics
                status_counts = {}
                for patient in onboarding_queue:
                    stage = patient['current_stage']
                    status_counts[stage] = status_counts.get(stage, 0) + 1
                
                # Display status summary
                status_data = []
                stage_order = [
                    'Stage 1: Patient Registration',
                    'Stage 2: Eligibility Verification', 
                    'Stage 3: Chart Creation',
                    'Stage 4: Intake Processing',
                    'Stage 5: TV Scheduling',
                    'Completed - Ready for Handoff'
                ]
                
                for stage in stage_order:
                    count = status_counts.get(stage, 0)
                    status_data.append({
                        "Stage": stage,
                        "Count": count,
                        "Status": "Active" if count > 0 else "None"
                    })
                
                df = pd.DataFrame(status_data)
                st.dataframe(
                    df, 
                    use_container_width=True,
                    column_config={
                        "Stage": st.column_config.TextColumn("Stage", width="large"),
                        "Count": st.column_config.NumberColumn("Count", format="%.0f", width="small"),
                        "Status": st.column_config.TextColumn("Status", width="small")
                    },
                    hide_index=True,
                    autosize_columns=ST_DF_AUTOSIZE_COLUMNS
                )
                
                # Daily metrics
                st.markdown("### Daily Metrics")
                total_patients = len(onboarding_queue)
                completed_today = len([p for p in onboarding_queue if p['current_stage'] == 'Completed - Ready for Handoff'])
                in_progress = total_patients - completed_today
                completion_rate = f"{(completed_today/total_patients)*100:.0f}%" if total_patients > 0 else "0%"
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Active Patients", total_patients)
                col2.metric("Ready for Handoff", completed_today)
                col3.metric("In Progress", in_progress)
                col4.metric("Completion Rate", completion_rate)
                
            else:
                st.info("No active onboarding processes found.")
                
        except Exception as e:
            st.error(f"Error loading processing status: {e}")

    # Tab 3: Facility Management
    with tab3:
        st.subheader("Facility Management")
        st.markdown("### Add New Facility")
        
        with st.form("add_facility_form"):
            facility_name = st.text_input("Facility Name*", key="facility_name")
            facility_address = st.text_input("Facility Address", key="facility_address")
            facility_phone = st.text_input("Facility Phone", key="facility_phone")
            facility_email = st.text_input("Facility Email", key="facility_email")
            
            submitted = st.form_submit_button("Add Facility")
            
            if submitted:
                if facility_name:
                    try:
                        conn = database.get_db_connection()
                        conn.execute("""
                            INSERT INTO facilities (facility_name, address, phone, email, created_date) 
                            VALUES (?, ?, ?, ?, datetime('now'))
                        """, (facility_name, facility_address, facility_phone, facility_email))
                        conn.commit()
                        conn.close()
                        st.success(f"Facility '{facility_name}' added successfully!")
                    except Exception as e:
                        st.error(f"Error adding facility: {e}")
                else:
                    st.error("Facility name is required")

    # Add a quick reference section
    st.markdown("---")
    st.subheader("Onboarding Workflow Reference")
    st.write("""
    **ZEN Medical Onboarding Workflow (POT):**
    1. **Patient Registration** - Collect basic patient information
    2. **Eligibility Verification** - Verify insurance coverage
    3. **Chart Creation** - Create EMed patient chart
    4. **Intake Processing** - Collect medical records and documentation
    5. **Initial TV Scheduling** - Schedule provider visit
    6. **Handoff to PCPM** - Prepare patient for provider assignment
    """)
