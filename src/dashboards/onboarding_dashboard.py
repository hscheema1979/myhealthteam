import streamlit as st
import pandas as pd
from src import database
from src import zmo_module
from datetime import datetime

# Define the onboarding workflow steps
ONBOARDING_STEPS = [
    {"step": 1, "title": "Patient Registration", "description": "Initial patient data entry", "stage_field": "stage1_complete"},
    {"step": 2, "title": "Eligibility Verification", "description": "Insurance and eligibility check", "stage_field": "stage2_complete"},
    {"step": 3, "title": "Chart Creation", "description": "Patient chart setup", "stage_field": "stage3_complete"},
    {"step": 4, "title": "Intake Processing", "description": "Medical records and documentation", "stage_field": "stage4_complete"},
    {"step": 5, "title": "Visit Scheduling", "description": "Initial visit appointment setup", "stage_field": "stage5_complete"}
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

def get_action_required_blockers(row):
    """Determine specific blockers preventing completion of the current stage"""
    current_stage = row['current_stage']
    blockers = []
    
    # Always check for POT assignment first (applies to all stages)
    if not row.get('assigned_pot_name') or row.get('assigned_pot_name') == 'Unassigned':
        blockers.append("Assign POT user")
    
    # Stage 1: Patient Registration blockers
    if current_stage == 'Stage 1: Patient Registration':
        if not row.get('first_name'):
            blockers.append("Enter patient first name")
        if not row.get('last_name'):
            blockers.append("Enter patient last name")
        if not row.get('date_of_birth'):
            blockers.append("Enter date of birth")
        if not row.get('phone_primary'):
            blockers.append("Enter primary phone number")
        if not row.get('address_street'):
            blockers.append("Enter street address")
        if not row.get('address_city'):
            blockers.append("Enter city")
        if not row.get('address_state'):
            blockers.append("Select state")
        if not row.get('address_zip'):
            blockers.append("Enter ZIP code")
    
    # Stage 2: Eligibility Verification blockers
    elif current_stage == 'Stage 2: Eligibility Verification':
        if not row.get('insurance_provider'):
            blockers.append("Enter insurance provider")
        if not row.get('policy_number'):
            blockers.append("Enter insurance policy number")
        if not row.get('eligibility_verified'):
            blockers.append("Verify insurance eligibility")
        if not row.get('insurance_cards_received'):
            blockers.append("Receive insurance cards/face sheet")
    
    # Stage 3: Chart Creation blockers
    elif current_stage == 'Stage 3: Chart Creation':
        if not row.get('emed_chart_created'):
            blockers.append("Create eMed patient chart")
        if not row.get('facility_confirmed'):
            blockers.append("Confirm facility assignment")
        if not row.get('chart_id'):
            blockers.append("Enter chart ID")
    
    # Stage 4: Intake Processing blockers
    elif current_stage == 'Stage 4: Intake Processing':
        if not row.get('intake_call_completed'):
            blockers.append("Complete intake call")
        if not row.get('insurance_cards_received'):
            blockers.append("Receive insurance cards/face sheet")
        if not row.get('medical_records_requested'):
            blockers.append("Request medical records")
    
    # Stage 5: TV Visit Scheduling blockers
    elif current_stage == 'Stage 5: TV Scheduling':
        if not row.get('assigned_provider_user_id'):
            blockers.append("Assign Initial TV Provider")
        elif not row.get('tv_scheduled'):
            blockers.append("Schedule Initial TV")
        elif not row.get('initial_tv_completed'):
            # Check if provider has completed the task automatically
            if row.get('provider_completed_initial_tv'):
                blockers.append("Click Complete")
            else:
                blockers.append("Complete Initial TV (by provider)")
        elif not row.get('regional_provider_assigned'):
            blockers.append("Assign Regional Provider")
        elif not row.get('coordinator_assigned'):
            blockers.append("Assign Coordinator")
    
    # Workflow Complete
    elif current_stage == 'Completed':
        return "Onboarding complete"
    
    # Return appropriate message based on blockers found
    if len(blockers) == 0:
        return "Ready to proceed"
    elif len(blockers) == 1:
        return blockers[0]
    else:
        # Show the first blocker with count of additional ones
        return f"{blockers[0]} (+{len(blockers)-1} more)"

def show_patient_intake_form(current_user_id, patient_details=None):
    """Show new patient intake form for Stage 1 registration.
    If patient_details is provided, pre-fill the form for editing existing patient.
    """
    # Determine if editing existing patient or creating new one
    is_edit_mode = patient_details is not None
    onboarding_id = patient_details.get('onboarding_id') if is_edit_mode else None

    # Helper function to safely parse dates
    def parse_date_value(date_val):
        if date_val:
            try:
                from datetime import datetime
                if isinstance(date_val, str):
                    return datetime.strptime(date_val, '%Y-%m-%d').date()
                elif hasattr(date_val, 'date'):
                    return date_val.date()
                return date_val
            except:
                return None
        return None

    with st.form("patient_intake_form"):
        # Form title
        if is_edit_mode:
            st.markdown("### Stage 1: Patient Registration (Edit Mode)")
            st.info("Complete the required fields (marked with *) to finish Stage 1 registration.")
        else:
            st.markdown("### Stage 1: New Patient Registration")

        # Basic Patient Information
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name*", value=patient_details.get('first_name', '') if is_edit_mode else '', key="first_name")
            last_name = st.text_input("Last Name*", value=patient_details.get('last_name', '') if is_edit_mode else '', key="last_name")
            date_of_birth = st.date_input("Date of Birth*", value=parse_date_value(patient_details.get('date_of_birth')) if is_edit_mode else None, key="dob", min_value=datetime(1900, 1, 1).date(), max_value=datetime(2100, 12, 31).date())
            phone_primary = st.text_input("Primary Phone*", value=patient_details.get('phone_primary', '') if is_edit_mode else '', key="phone_primary")

        with col2:
            email = st.text_input("Email", value=patient_details.get('email', '') if is_edit_mode else '', key="email")
            gender_options = ["Male", "Female", "Other", "Prefer not to say"]
            gender_index = 0
            if is_edit_mode and patient_details.get('gender') in gender_options:
                gender_index = gender_options.index(patient_details.get('gender'))
            gender = st.selectbox("Gender", gender_options, index=gender_index, key="gender")
            emergency_contact = st.text_input("Emergency Contact Name", value=patient_details.get('emergency_contact_name', '') if is_edit_mode else '', key="emergency_contact")
            emergency_phone = st.text_input("Emergency Contact Phone", value=patient_details.get('emergency_contact_phone', '') if is_edit_mode else '', key="emergency_phone")

        # Address Information
        st.markdown("### Address Information")
        address_street = st.text_input("Street Address*", value=patient_details.get('address_street', '') if is_edit_mode else '', key="address_street")
        address_city = st.text_input("City*", value=patient_details.get('address_city', '') if is_edit_mode else '', key="address_city")

        state_options = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL",
                        "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",
                        "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
                        "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
                        "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
        state_index = 4  # Default to CA
        if is_edit_mode and patient_details.get('address_state') in state_options:
            state_index = state_options.index(patient_details.get('address_state'))
        address_state = st.selectbox("State*", state_options, index=state_index, key="address_state")
        address_zip = st.text_input("ZIP Code*", value=patient_details.get('address_zip', '') if is_edit_mode else '', key="address_zip")

        # Referral Information
        st.markdown("### Referral Information")
        referral_source = st.text_input("Referral Source", value=patient_details.get('referral_source', '') if is_edit_mode else '', key="referral_source")
        referring_provider = st.text_input("Referring Provider", value=patient_details.get('referring_provider', '') if is_edit_mode else '', key="referral_provider")
        referral_date = st.date_input("Referral Date", value=parse_date_value(patient_details.get('referral_date')) if is_edit_mode else None, key="referral_date")
        
        # Facility Assignment - Get facilities from database
        st.markdown("### Facility Assignment")
        try:
            conn = database.get_db_connection()
            facilities = conn.execute("SELECT facility_name FROM facilities ORDER BY facility_name").fetchall()
            conn.close()
            facility_options = [f[0] for f in facilities] if facilities else []
            facility_options.append("Add New Facility")
        except Exception as e:
            facility_options = ["San Francisco", "Los Angeles", "San Diego", "Sacramento", "Add New Facility"]

        facility_index = 0
        if is_edit_mode and patient_details.get('facility_assignment') in facility_options:
            facility_index = facility_options.index(patient_details.get('facility_assignment'))
        facility_assignment = st.selectbox("Referring Facility", facility_options, index=facility_index, key="facility_assignment")

        # Submit buttons - different for edit mode vs new patient
        if is_edit_mode:
            # Edit mode: Save Progress, Complete Stage 1, and Cancel buttons
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                save_progress = st.form_submit_button("Save Progress")
            with col2:
                complete_stage = st.form_submit_button("Complete Stage 1", type="primary")
            with col3:
                if st.form_submit_button("Cancel"):
                    st.session_state['onboarding_mode'] = None
                    st.rerun()

            # Handle Save Progress
            if save_progress:
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
                    'referral_source': referral_source,
                    'referring_provider': referring_provider,
                    'referral_date': referral_date.isoformat() if referral_date else None,
                    'facility_assignment': facility_assignment if facility_assignment != "Add New Facility" else None
                }
                database.update_onboarding_checkbox_data(onboarding_id, patient_data)
                st.success("Progress saved! You can continue later.")

            # Handle Complete Stage 1
            if complete_stage:
                if not first_name or not last_name or not date_of_birth or not phone_primary or not address_street or not address_city or not address_zip:
                    st.error("Please fill in all required fields (marked with *)")
                else:
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
                        'referral_source': referral_source,
                        'referring_provider': referring_provider,
                        'referral_date': referral_date.isoformat() if referral_date else None,
                        'facility_assignment': facility_assignment if facility_assignment != "Add New Facility" else None
                    }
                    database.update_onboarding_checkbox_data(onboarding_id, patient_data)
                    database.update_onboarding_stage_completion(onboarding_id, 1, True)
                    st.success(f"Stage 1 Complete! Moving to Stage 2: Eligibility Verification...")
                    st.rerun()

        else:
            # New patient mode: Start Workflow and Cancel buttons
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
                            'referral_source': referral_source,
                            'referring_provider': referring_provider,
                            'referral_date': referral_date.isoformat() if referral_date else None,
                            'facility_assignment': facility_assignment if facility_assignment != "Add New Facility" else None
                        }

                        # Create onboarding workflow instance
                        onboarding_id = database.create_onboarding_workflow_instance(patient_data, current_user_id)

                        st.success(f"Patient {first_name} {last_name} onboarding workflow started!")

                        # Mark Stage 1 as complete since we just completed registration
                        database.update_onboarding_stage_completion(onboarding_id, 1, True)

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
    
    # Navigation
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("Resume workflow from current stage")
    with col2:
        if st.button("❌ Back to Queue", key="back_to_queue_resume"):
            st.session_state['onboarding_mode'] = None
            st.rerun()
    
    # Progress indicator
    stages = ['Registration', 'Eligibility', 'Chart Creation', 'Intake Processing', 'TV Scheduling']
    # Compute how many steps are completed
    completed_steps = sum(1 for s in stages if patient_details.get(f'stage{stages.index(s)+1}_complete', False))

    # All stages complete - onboarding workflow finished
    if completed_steps >= len(stages):
        st.success("🎉 Onboarding Complete! Patient has been successfully onboarded and assigned to regional provider.")
        if st.button("Return to Queue"):
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
        # Show editable intake form with existing patient data
        show_patient_intake_form(current_user_id, patient_details)
    elif current_stage == 2:
        try:
            show_eligibility_verification_form(patient_details, current_user_id)
        except Exception as e:
            st.error(f"Error loading Stage 2 form: {e}")
            import traceback
            st.code(traceback.format_exc())
    elif current_stage == 3:
        try:
            show_chart_creation_form(patient_details, current_user_id)
        except Exception as e:
            st.error(f"Error loading Stage 3 form: {e}")
            import traceback
            st.code(traceback.format_exc())
    elif current_stage == 4:
        try:
            show_intake_processing_form(patient_details, current_user_id)
        except Exception as e:
            st.error(f"Error loading Stage 4 form: {e}")
            import traceback
            st.code(traceback.format_exc())
    elif current_stage == 5:
        try:
            show_tv_scheduling_form(patient_details, current_user_id)
        except Exception as e:
            st.error(f"Error loading Stage 5 form: {e}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.error(f"Unknown stage: {current_stage}")

def show_eligibility_verification_form(patient_details, current_user_id):
    """Stage 2: Eligibility Verification"""
    st.markdown("### Stage 2: Insurance Eligibility Verification")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("Verify patient's insurance coverage and eligibility status")
    with col2:
        # Patient info card
        with st.expander("Patient Info", expanded=False):
            st.write(f"**Insurance:** {patient_details.get('insurance_provider', 'N/A')}")
            st.write(f"**Policy #:** {patient_details.get('policy_number', 'N/A')}")
            st.write(f"**Group #:** {patient_details.get('group_number', 'N/A')}")
    
    with st.form("eligibility_form"):
        st.markdown("#### Insurance Information")
        
        # Insurance input fields
        insurance_provider = st.text_input(
            "Primary Insurance Provider*", 
            value=patient_details.get('insurance_provider', ''),
            key="insurance_provider"
        )
        policy_number = st.text_input(
            "Policy Number*", 
            value=patient_details.get('policy_number', ''),
            key="policy_number"
        )
        group_number = st.text_input(
            "Group Number", 
            value=patient_details.get('group_number', ''),
            key="group_number"
        )
        
        st.markdown("#### Eligibility Check")
        
        # Get existing values with proper defaults
        existing_eligibility_status = patient_details.get('eligibility_status', 'Pending Verification')
        eligibility_options = ["Eligible", "Not Eligible", "Pending Verification", "Needs Follow-up"]
        
        # Find index of existing value, default to 'Pending Verification' if not found
        try:
            default_index = eligibility_options.index(existing_eligibility_status)
        except ValueError:
            default_index = eligibility_options.index('Pending Verification')
        
        eligibility_status = st.selectbox(
            "Eligibility Status*", 
            eligibility_options,
            index=default_index,
            key="eligibility_status"
        )
        
        eligibility_verified = st.checkbox(
            "Eligibility Verified", 
            value=patient_details.get('eligibility_verified', False),
            key="eligibility_verified"
        )
        
        eligibility_notes = st.text_area(
            "Verification Notes", 
            value=patient_details.get('eligibility_notes', ''),
            placeholder="Enter details about insurance verification, coverage limitations, etc.",
            key="eligibility_notes"
        )
        
        st.markdown("#### Annual Well Visit")
        
        # Handle existing annual well visit date
        existing_annual_well_visit = patient_details.get('annual_well_visit')
        annual_well_visit_value = None
        if existing_annual_well_visit:
            try:
                from datetime import datetime
                if isinstance(existing_annual_well_visit, str):
                    annual_well_visit_value = datetime.strptime(existing_annual_well_visit, '%Y-%m-%d').date()
                elif hasattr(existing_annual_well_visit, 'date'):
                    annual_well_visit_value = existing_annual_well_visit.date()
            except (ValueError, TypeError):
                annual_well_visit_value = None
        
        annual_well_visit = st.date_input(
            "Annual Well Visit Date", 
            value=annual_well_visit_value,
            help="Select the date for the patient's annual wellness visit",
            key="annual_well_visit"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.form_submit_button("Complete Stage 2", type="primary"):
                # Validate required insurance fields
                if not insurance_provider or not policy_number:
                    st.error("Please fill in all required insurance fields (marked with *)")
                else:
                    # Save insurance and eligibility fields including annual well visit
                    checkbox_payload = {
                        'insurance_provider': insurance_provider,
                        'policy_number': policy_number,
                        'group_number': group_number,
                        'eligibility_status': eligibility_status,
                        'eligibility_notes': eligibility_notes,
                        'eligibility_verified': eligibility_verified,
                        'annual_well_visit': annual_well_visit,
                    }
                    database.update_onboarding_checkbox_data(patient_details['onboarding_id'], checkbox_payload)
                    st.success('Stage 2 data saved')

                if eligibility_verified:
                    # First, create/update patient record in patients table now that patient is eligible
                    try:
                        patient_id = database.insert_patient_from_onboarding(patient_details['onboarding_id'])
                        if patient_id:
                            st.info(f"✓ Patient record created in patients table: {patient_id}")
                        else:
                            st.warning("Patient record already exists or was updated")
                    except Exception as e:
                        st.error(f"Error creating patient record: {str(e)}")

                    # Then sync to patient_panel table so patient appears in ZMO
                    try:
                        panel_patient_id = database.sync_onboarding_to_patient_panel(patient_details['onboarding_id'])
                        if panel_patient_id:
                            st.info(f"✓ Patient added to patient_panel (visible in ZMO)")
                    except Exception as e:
                        st.warning(f"Patient panel sync warning: {e}")

                    # Clear ZMO cache so patient appears immediately in ZMO tab
                    try:
                        zmo_module.get_patient_panel_data.clear()
                        zmo_module.get_patients_data.clear()
                    except Exception:
                        pass  # Cache clearing may fail if not yet loaded

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

                    st.success("Stage 2 Complete! Patient added to patients, patient_panel, and ZMO. Moving to Chart Creation...")
                    st.rerun()
                else:
                    st.error("Eligibility not verified. Data saved—please verify eligibility to proceed.")

        with col2:
            if st.form_submit_button("Save Progress"):
                # Save progress for Stage 2 (insurance, eligibility, and annual well visit)
                checkbox_payload = {
                    'insurance_provider': insurance_provider,
                    'policy_number': policy_number,
                    'group_number': group_number,
                    'eligibility_status': eligibility_status,
                    'eligibility_notes': eligibility_notes,
                    'eligibility_verified': eligibility_verified,
                    'annual_well_visit': annual_well_visit,
                }
                database.update_onboarding_checkbox_data(patient_details['onboarding_id'], checkbox_payload)

                # If patient already exists in patients table (from previous Stage 2 completion), update it
                if patient_details.get('patient_id'):
                    try:
                        database.insert_patient_from_onboarding(patient_details['onboarding_id'])
                        database.sync_onboarding_to_patient_panel(patient_details['onboarding_id'])
                        # Clear ZMO cache so changes appear immediately
                        try:
                            zmo_module.get_patient_panel_data.clear()
                            zmo_module.get_patients_data.clear()
                        except Exception:
                            pass
                        st.success("✓ Progress saved and patient data synced to ZMO!")
                    except Exception as e:
                        st.info(f"Progress saved! (ZMO sync skipped: {e})")
                else:
                    st.info("Progress saved! Patient will be added to ZMO after eligibility is verified.")

        with col3:
            if st.form_submit_button("Back to Queue"):
                st.session_state['onboarding_mode'] = None
                st.rerun()

def show_chart_creation_form(patient_details, current_user_id):
    """Stage 3: EMed Chart Creation"""
    st.markdown("### Stage 3: EMed Chart Creation")
    
    st.info("Create patient chart in EMed system and assign facility")
    
    with st.form("chart_creation_form"):
        
        emed_chart_created = st.checkbox(
            "EMed Chart Created", 
            value=patient_details.get('emed_chart_created', False),
            key="emed_chart_created"
        )
        chart_id = st.text_input(
            "EMed Chart ID", 
            value=patient_details.get('chart_id', ''),
            key="chart_id", 
            help="Enter the EMed chart ID number"
        )
        facility_confirmed = st.checkbox(
            "Facility Assignment Confirmed", 
            value=patient_details.get('facility_confirmed', False),
            key="facility_confirmed"
        )
        
        chart_notes = st.text_area(
            "Chart Creation Notes",
            value=patient_details.get('chart_notes', ''),
            placeholder="Enter any notes about chart creation, facility assignment, or issues encountered",
            key="chart_notes"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.form_submit_button("Complete Stage 3", type="primary"):
                # Save chart creation data
                chart_data = {
                    'emed_chart_created': emed_chart_created,
                    'chart_id': chart_id,
                    'facility_confirmed': facility_confirmed,
                    'chart_notes': chart_notes
                }
                database.update_onboarding_checkbox_data(patient_details['onboarding_id'], chart_data)
                
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
                # Save chart creation data
                chart_data = {
                    'emed_chart_created': emed_chart_created,
                    'chart_id': chart_id,
                    'facility_confirmed': facility_confirmed,
                    'chart_notes': chart_notes
                }
                database.update_onboarding_checkbox_data(patient_details['onboarding_id'], chart_data)

                # Sync patient data to tables if patient already exists (added after Stage 2)
                if patient_details.get('patient_id'):
                    try:
                        database.insert_patient_from_onboarding(patient_details['onboarding_id'])
                        database.sync_onboarding_to_patient_panel(patient_details['onboarding_id'])
                        # Clear ZMO cache so changes appear immediately
                        try:
                            zmo_module.get_patient_panel_data.clear()
                            zmo_module.get_patients_data.clear()
                        except Exception:
                            pass
                        st.success("✓ Progress saved and patient data synced to ZMO!")
                    except Exception as e:
                        st.info(f"Progress saved! (ZMO sync skipped: {e})")
                else:
                    st.info("Progress saved! (Patient not yet added to ZMO - complete Stage 2 eligibility first)")

        with col3:
            if st.form_submit_button("Back to Queue"):
                st.session_state['onboarding_mode'] = None
                st.rerun()

def show_intake_processing_form(patient_details, current_user_id):
    """Stage 4: Intake Processing & Documentation"""
    st.markdown("### Stage 4: Intake Processing & Documentation")
    
    st.info("Complete patient intake, collect documentation, and conduct intake call")
    
    with st.form("intake_processing_form"):
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Documentation")
            medical_records_requested = st.checkbox("Medical Records Requested", 
                                                   key="medical_records_requested",
                                                   value=patient_details.get('medical_records_requested', False))
            referral_documents_received = st.checkbox("Referral Documents Received", 
                                                     key="referral_documents_received",
                                                     value=patient_details.get('referral_documents_received', False))
            emed_signature_received = st.checkbox("EMED Signature Received", 
                                                key="emed_signature_received",
                                                value=patient_details.get('emed_signature_received', False))

        
        with col2:
            st.markdown("#### Patient Contact")
            intake_call_completed = st.checkbox(
                "Intake Call Completed", 
                value=patient_details.get('intake_call_completed', False),
                key="intake_call_completed"
            )
            
        intake_notes = st.text_area(
            "Intake Processing Notes",
            value=patient_details.get('intake_notes', ''),
            placeholder="Document any issues with medical records, patient contact attempts, special requirements, etc.",
            key="intake_notes"
        )
        
        # Appointment & Medical Contacts
        st.markdown("### Appointment & Medical Contacts")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Appointment Contact")
            appointment_contact_name = st.text_input(
                "Appointment Contact Name", 
                value=patient_details.get('appointment_contact_name', ''),
                key="appointment_contact_name"
            )
            appointment_contact_phone = st.text_input(
                "Appointment Contact Phone", 
                value=patient_details.get('appointment_contact_phone', ''),
                key="appointment_contact_phone"
            )
            appointment_contact_email = st.text_input(
                "Appointment Contact Email", 
                value=patient_details.get('appointment_contact_email', ''),
                key="appointment_contact_email"
            )
        
        with col2:
            st.markdown("#### Medical Contact")
            medical_contact_name = st.text_input(
                "Medical Contact Name",
                value=patient_details.get('medical_contact_name', ''),
                key="medical_contact_name"
            )
            medical_contact_phone = st.text_input(
                "Medical Contact Phone",
                value=patient_details.get('medical_contact_phone', ''),
                key="medical_contact_phone"
            )
            medical_contact_email = st.text_input(
                "Medical Contact Email",
                value=patient_details.get('medical_contact_email', ''),
                key="medical_contact_email"
            )

        # Facility Nurse Contact
        st.markdown("### Facility Nurse Contact")
        col1, col2, col3 = st.columns(3)

        with col1:
            facility_nurse_name = st.text_input(
                "Facility Nurse Name",
                value=patient_details.get('facility_nurse_name', ''),
                key="facility_nurse_name"
            )

        with col2:
            facility_nurse_phone = st.text_input(
                "Facility Nurse Phone",
                value=patient_details.get('facility_nurse_phone', ''),
                key="facility_nurse_phone"
            )

        with col3:
            facility_nurse_email = st.text_input(
                "Facility Nurse Email",
                value=patient_details.get('facility_nurse_email', ''),
                key="facility_nurse_email"
            )

        # Patient Status
        st.markdown("### Patient Status")
        patient_status = st.selectbox(
            "Patient Status", 
            ["Active", "Active-Geri", "Active-PCP"], 
            index=["Active", "Active-Geri", "Active-PCP"].index(patient_details.get('patient_status', 'Active')) if patient_details.get('patient_status') in ["Active", "Active-Geri", "Active-PCP"] else 0,
            key="patient_status"
        )
        
        # Stage 4 additions: Specialist and chronic conditions - TEMPORARILY COMMENTED OUT
        # st.markdown("### Specialist & Clinical Conditions")
        # active_specialist = st.text_input(
        #     "Active Specialist", 
        #     value=patient_details.get('active_specialist', ''),
        #     key="active_specialist"
        # )
        
        # # Handle date input with existing value
        # existing_specialist_date = patient_details.get('specialist_last_seen')
        # specialist_last_seen_value = None
        # if existing_specialist_date:
        #     try:
        #         from datetime import datetime
        #         specialist_last_seen_value = datetime.strptime(existing_specialist_date, '%Y-%m-%d').date()
        #     except (ValueError, TypeError):
        #         specialist_last_seen_value = None
        
        # specialist_last_seen = st.date_input(
        #     "Specialist Last Seen", 
        #     value=specialist_last_seen_value,
        #     key="specialist_last_seen"
        # )
        
        # chronic_conditions_onboarding = st.text_area(
        #     "Chronic Conditions (comma-separated)", 
        #     value=patient_details.get('chronic_conditions_onboarding', ''),
        #     key="chronic_conditions_onboarding"
        # )
        
        # Set default values for hidden specialist fields
        active_specialist = ''
        specialist_last_seen = None
        chronic_conditions_onboarding = ''
        
        # Clinical Section - moved from Stage 2
        st.markdown("### Clinical Information")
        primary_care_provider = st.text_input(
            "Primary Care Provider", 
            value=patient_details.get('primary_care_provider', ''),
            key="primary_care_provider"
        )
        
        # PCP Last Seen - TEMPORARILY COMMENTED OUT
        # # Handle date input with existing value
        # existing_pcp_date = patient_details.get('pcp_last_seen')
        # pcp_last_seen_value = None
        # if existing_pcp_date:
        #     try:
        #         from datetime import datetime
        #         pcp_last_seen_value = datetime.strptime(existing_pcp_date, '%Y-%m-%d').date()
        #     except (ValueError, TypeError):
        #         pcp_last_seen_value = None
        
        # pcp_last_seen = st.date_input(
        #     "PCP Last Seen", 
        #     value=pcp_last_seen_value,
        #     key="pcp_last_seen"
        # )
        
        # Set default value for hidden PCP Last Seen field
        pcp_last_seen = None

        # Mental Health Section - TEMPORARILY COMMENTED OUT
        # st.markdown("### Mental Health Conditions")
        # st.markdown("#### Check all that apply:")
        # mh_schizophrenia = st.checkbox(
        #     "Schizophrenia", 
        #     value=patient_details.get('mh_schizophrenia', False),
        #     key="mh_schizophrenia"
        # )
        # mh_depression = st.checkbox(
        #     "Depression", 
        #     value=patient_details.get('mh_depression', False),
        #     key="mh_depression"
        # )
        # mh_anxiety = st.checkbox(
        #     "Anxiety", 
        #     value=patient_details.get('mh_anxiety', False),
        #     key="mh_anxiety"
        # )
        # mh_stress = st.checkbox(
        #     "Stress", 
        #     value=patient_details.get('mh_stress', False),
        #     key="mh_stress"
        # )
        # mh_adhd = st.checkbox(
        #     "ADHD", 
        #     value=patient_details.get('mh_adhd', False),
        #     key="mh_adhd"
        # )
        # mh_bipolar = st.checkbox(
        #     "Bipolar", 
        #     value=patient_details.get('mh_bipolar', False),
        #     key="mh_bipolar"
        # )
        # mh_suicidal = st.checkbox(
        #     "Suicidal Ideation", 
        #     value=patient_details.get('mh_suicidal', False),
        #     key="mh_suicidal"
        # )
        
        # Set default values for hidden mental health fields
        mh_schizophrenia = False
        mh_depression = False
        mh_anxiety = False
        mh_stress = False
        mh_adhd = False
        mh_bipolar = False
        mh_suicidal = False
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.form_submit_button("Complete Stage 4", type="primary"):
                # Safe date conversion helper
                def safe_date_str(date_val):
                    if not date_val:
                        return None
                    if isinstance(date_val, str):
                        return date_val
                    try:
                        return date_val.strftime('%Y-%m-%d')
                    except:
                        return None

                # Save intake processing, clinical, and mental health fields
                checkbox_data = {
                    'medical_records_requested': medical_records_requested,
                    'referral_documents_received': referral_documents_received,
                    'emed_signature_received': emed_signature_received,
                    'intake_notes': intake_notes,
                    'intake_call_completed': intake_call_completed,
                    'appointment_contact_name': appointment_contact_name,
                    'appointment_contact_phone': appointment_contact_phone,
                    'appointment_contact_email': appointment_contact_email,
                    'medical_contact_name': medical_contact_name,
                    'medical_contact_phone': medical_contact_phone,
                    'medical_contact_email': medical_contact_email,
                    'facility_nurse_name': facility_nurse_name,
                    'facility_nurse_phone': facility_nurse_phone,
                    'facility_nurse_email': facility_nurse_email,
                    'patient_status': patient_status,
                    'active_specialist': active_specialist,
                    'specialist_last_seen': safe_date_str(specialist_last_seen),
                    'chronic_conditions_onboarding': chronic_conditions_onboarding,
                    'primary_care_provider': primary_care_provider,
                    'pcp_last_seen': safe_date_str(pcp_last_seen),
                    'mh_schizophrenia': mh_schizophrenia,
                    'mh_depression': mh_depression,
                    'mh_anxiety': mh_anxiety,
                    'mh_stress': mh_stress,
                    'mh_adhd': mh_adhd,
                    'mh_bipolar': mh_bipolar,
                    'mh_suicidal': mh_suicidal,
                }
                database.update_onboarding_checkbox_data(patient_details['onboarding_id'], checkbox_data)

                # Require intake call completion before completing
                if intake_call_completed:
                    # Update patient record with Stage 4 intake data (patient was created at Stage 2)
                    try:
                        patient_id = database.insert_patient_from_onboarding(patient_details['onboarding_id'])
                        if patient_id:
                            st.info(f"✓ Patient record updated with intake data: {patient_id}")
                        else:
                            st.warning("Patient record already exists or was updated")
                    except Exception as e:
                        st.error(f"Error updating patient record: {str(e)}")
                        # Don't prevent stage completion if patient update fails

                    # Also sync to patient_panel to ensure latest data
                    try:
                        database.sync_onboarding_to_patient_panel(patient_details['onboarding_id'])
                    except Exception as e:
                        st.warning(f"Patient panel sync warning: {e}")

                    database.update_onboarding_stage_completion(patient_details['onboarding_id'], 4, True)

                    # Update tasks
                    tasks = patient_details.get('tasks', [])
                    for task in tasks:
                        if task['task_stage'] == 4:
                            database.update_onboarding_task_status(
                                task['task_id'], 'Complete', current_user_id,
                                {'intake_call_completed': True}
                            )

                    st.success("Stage 4 Complete! Patient intake data synced. Moving to TV Scheduling...")
                    st.rerun()
                else:
                    st.error("Please complete the intake call before proceeding.")

        with col2:
            if st.form_submit_button("Save Progress"):
                # Safe date conversion helper
                def safe_date_str(date_val):
                    if not date_val:
                        return None
                    if isinstance(date_val, str):
                        return date_val
                    try:
                        return date_val.strftime('%Y-%m-%d')
                    except:
                        return None

                # Save checkbox data, clinical, and mental health fields when saving progress
                checkbox_data = {
                    'medical_records_requested': medical_records_requested,
                    'referral_documents_received': referral_documents_received,
                    'emed_signature_received': emed_signature_received,
                    'intake_notes': intake_notes,
                    'intake_call_completed': intake_call_completed,
                    'appointment_contact_name': appointment_contact_name,
                    'appointment_contact_phone': appointment_contact_phone,
                    'appointment_contact_email': appointment_contact_email,
                    'medical_contact_name': medical_contact_name,
                    'medical_contact_phone': medical_contact_phone,
                    'medical_contact_email': medical_contact_email,
                    'facility_nurse_name': facility_nurse_name,
                    'facility_nurse_phone': facility_nurse_phone,
                    'facility_nurse_email': facility_nurse_email,
                    'patient_status': patient_status,
                    'active_specialist': active_specialist,
                    'specialist_last_seen': safe_date_str(specialist_last_seen),
                    'chronic_conditions_onboarding': chronic_conditions_onboarding,
                    'primary_care_provider': primary_care_provider,
                    'pcp_last_seen': safe_date_str(pcp_last_seen),
                    'mh_schizophrenia': mh_schizophrenia,
                    'mh_depression': mh_depression,
                    'mh_anxiety': mh_anxiety,
                    'mh_stress': mh_stress,
                    'mh_adhd': mh_adhd,
                    'mh_bipolar': mh_bipolar,
                    'mh_suicidal': mh_suicidal,
                }
                database.update_onboarding_checkbox_data(patient_details['onboarding_id'], checkbox_data)

                # Sync patient data to tables if patient already exists
                if patient_details.get('patient_id'):
                    try:
                        database.insert_patient_from_onboarding(patient_details['onboarding_id'])
                        database.sync_onboarding_to_patient_panel(patient_details['onboarding_id'])
                        # Clear ZMO cache so changes appear immediately
                        try:
                            zmo_module.get_patient_panel_data.clear()
                            zmo_module.get_patients_data.clear()
                        except Exception:
                            pass
                        st.success("✓ Progress saved and patient data synced to ZMO!")
                    except Exception as e:
                        st.info(f"Progress saved! (ZMO sync skipped: {e})")
                else:
                    st.info("Progress saved! (Patient not yet added to ZMO)")

        with col3:
            if st.form_submit_button("Back to Queue"):
                st.session_state['onboarding_mode'] = None
                st.rerun()

def show_tv_scheduling_form(patient_details, current_user_id):
    """Stage 5: TV Scheduling & Provider + Coordinator Assignments"""
    st.markdown("### Stage 5: TV Scheduling & Provider + Coordinator Assignments")
    
    # Store form data in session state to persist across form submissions
    if 'tv_form_data' not in st.session_state:
        st.session_state.tv_form_data = {
            'tv_scheduled': patient_details.get('tv_scheduled', False),
            'tv_date': patient_details.get('tv_date'),
            'tv_time': patient_details.get('tv_time'),
            'patient_notified': patient_details.get('patient_notified', False),
            'initial_tv_completed': patient_details.get('initial_tv_completed', False),
            'assigned_provider': patient_details.get('assigned_provider', 'Select Provider...'),
            'assigned_coordinator': patient_details.get('assigned_coordinator', 'Select Coordinator...'),
            'visit_type': patient_details.get('visit_type', 'Home Visit'),  # Default to Home Visit
            'billing_code': patient_details.get('billing_code', '99345'),  # Default billing code for home visit
            'duration_minutes': patient_details.get('duration_minutes', 45)  # Default 45 minutes
        }
    
    st.info("Schedule initial visit and assign provider and coordinator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Visit Scheduling")
        
        # Visit Type Selection
        visit_type_options = ["Home Visit", "Telehealth Visit"]
        visit_type_index = 0
        if st.session_state.tv_form_data['visit_type'] in visit_type_options:
            visit_type_index = visit_type_options.index(st.session_state.tv_form_data['visit_type'])
        
        visit_type = st.selectbox("Visit Type", 
                                visit_type_options, 
                                index=visit_type_index,
                                key="visit_type")
        
        # Update billing code and duration based on visit type
        if visit_type == "Home Visit":
            billing_code = "99345"
            duration_minutes = 45
            st.info("Home Visit: Billing Code 99345, Duration 45 minutes")
        else:
            billing_code = st.session_state.tv_form_data.get('billing_code', '99201')
            duration_minutes = st.session_state.tv_form_data.get('duration_minutes', 30)
            st.info("Telehealth Visit: Standard telehealth billing applies")
        
        tv_scheduled = st.checkbox("Initial Visit Scheduled", 
                                 value=st.session_state.tv_form_data['tv_scheduled'],
                                 key="tv_scheduled")
        tv_date = st.date_input("Visit Appointment Date", 
                              value=st.session_state.tv_form_data['tv_date'],
                              key="tv_date")
        tv_time = st.time_input("Visit Appointment Time", 
                              value=st.session_state.tv_form_data['tv_time'],
                              key="tv_time")
        patient_notified = st.checkbox("Patient Notified of Visit Appointment", 
                                     value=st.session_state.tv_form_data['patient_notified'],
                                     key="patient_notified")
        initial_tv_completed = st.checkbox("Initial Visit Completed (Verify in EMED)", 
                                         value=st.session_state.tv_form_data['initial_tv_completed'],
                                         key="initial_tv_completed")
            
    with col2:
        st.markdown("#### Provider Assignment for Initial Visit")
        # Get Provider users from database
        try:
            provider_users = database.get_users_by_role("CP")  # Use role abbreviation CP for Care Provider
            provider_options = ["Select Provider..."] + [f"{u['full_name']} ({u['username']})" for u in provider_users] if provider_users else ["No Providers Available"]
        except:
            provider_options = ["Provider Assignment Needed"]
            
        # Find current selection index
        current_provider = st.session_state.tv_form_data['assigned_provider']
        provider_index = 0
        if current_provider in provider_options:
            provider_index = provider_options.index(current_provider)
            
        assigned_provider = st.selectbox("Assign Provider", provider_options, 
                                       index=provider_index,
                                       key="assigned_provider")
    
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
        
        # Find current selection index
        current_coordinator = st.session_state.tv_form_data['assigned_coordinator']
        coordinator_index = 0
        if current_coordinator in coordinator_options:
            coordinator_index = coordinator_options.index(current_coordinator)
            
        assigned_coordinator = st.selectbox("Assign Coordinator", coordinator_options,
                                          index=coordinator_index,
                                          key="assigned_coordinator")
    
    # Update session state with current form values
    # Include assigned_regional_provider which is stored in session_state by the selectbox key
    st.session_state.tv_form_data.update({
        'tv_scheduled': tv_scheduled,
        'tv_date': tv_date,
        'tv_time': tv_time,
        'patient_notified': patient_notified,
        'initial_tv_completed': initial_tv_completed,
        'assigned_provider': assigned_provider,
        'assigned_regional_provider': st.session_state.get('assigned_regional_provider', 'Select Regional Provider...'),
        'assigned_coordinator': assigned_coordinator,
        'visit_type': visit_type,
        'billing_code': billing_code,
        'duration_minutes': duration_minutes
    })
        
    # Action buttons in separate forms to avoid conflicts
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        with st.form("complete_stage5_form"):
            if st.form_submit_button("Complete Stage 5", type="primary"):
                # Stage 5 completion requirements: TV scheduled, patient notified, initial TV completed, AND regional assignments
                # Now that patient_id is created in Stage 4, we can check the patient_assignments table
                
                basic_requirements_met = (st.session_state.tv_form_data['tv_scheduled'] and 
                                        st.session_state.tv_form_data['patient_notified'] and
                                        st.session_state.tv_form_data['initial_tv_completed'])
                
                # Save dropdown selections to patient_assignments table before checking
                patient_id = patient_details.get('patient_id')
                regional_provider_assigned = False
                coordinator_assigned_in_patient_table = False

                # Fallback: If patient_id is missing (Stage 4 may not have set it), create it now
                if not patient_id:
                    try:
                        with st.spinner("Creating patient record..."):
                            patient_id = database.insert_patient_from_onboarding(patient_details['onboarding_id'])
                            if patient_id:
                                st.success(f"Patient record created: {patient_id}")
                                # Refresh patient_details to get the updated patient_id
                                patient_details['patient_id'] = patient_id
                            else:
                                st.error("Failed to create patient record. Please contact support.")
                                st.stop()
                    except Exception as e:
                        st.error(f"Error creating patient record: {e}")
                        st.stop()

                # Get selections from tv_form_data (not session_state directly to avoid stale values)
                regional_provider_selection = st.session_state.tv_form_data.get('assigned_regional_provider', 'Select Regional Provider...')
                coordinator_selection = st.session_state.tv_form_data.get('assigned_coordinator', 'Select Coordinator...')

                conn = database.get_db_connection()
                try:
                    # Extract user IDs from dropdown selections
                    provider_id = None
                    coordinator_id = None

                    # Get provider ID from dropdown selection
                    if (regional_provider_selection and
                        regional_provider_selection not in ['Select Regional Provider...', 'No Providers Available', 'Regional Provider Assignment Needed']):
                        try:
                            provider_users = database.get_users_by_role("CP")
                            provider_map = {f"{u['full_name']} ({u['username']})": u['user_id'] for u in provider_users}
                            provider_id = provider_map.get(regional_provider_selection)
                        except Exception as e:
                            st.warning(f"Provider lookup error: {e}")

                    # Get coordinator ID from dropdown selection
                    if (coordinator_selection and
                        coordinator_selection not in ['Select Coordinator...', 'No Coordinators Available', 'Coordinator Assignment Needed']):
                        try:
                            coordinator_users = database.get_users_by_role("CC")
                            coordinator_map = {f"{u['full_name']} ({u['username']})": u['user_id'] for u in coordinator_users}
                            coordinator_id = coordinator_map.get(coordinator_selection)
                        except Exception as e:
                            st.warning(f"Coordinator lookup error: {e}")

                    # Save assignments to patient_assignments table if selections were made
                    if provider_id or coordinator_id:
                        current_user_id = st.session_state.get('user_id', 1)  # Default to 1 if no user_id
                        database.create_patient_assignment(
                            patient_id=patient_id,
                            provider_id=provider_id,
                            coordinator_id=coordinator_id,
                            assignment_type="onboarding",
                            status="active",
                            created_by=current_user_id
                        )

                    # Now check for assignments in the patient_assignments table
                    provider_result = conn.execute("""
                        SELECT provider_id FROM patient_assignments
                        WHERE patient_id = ? AND provider_id IS NOT NULL AND status = 'active'
                    """, (patient_id,)).fetchall()
                    regional_provider_assigned = len(provider_result) > 0

                    coordinator_result = conn.execute("""
                        SELECT coordinator_id FROM patient_assignments
                        WHERE patient_id = ? AND coordinator_id IS NOT NULL AND status = 'active'
                    """, (patient_id,)).fetchall()
                    coordinator_assigned_in_patient_table = len(coordinator_result) > 0
                finally:
                    conn.close()

                assignments_complete = regional_provider_assigned and coordinator_assigned_in_patient_table

                if basic_requirements_met and assignments_complete:
                    # Save Stage 5 data including provider assignment
                    database.update_onboarding_stage5_completion(
                        patient_details['onboarding_id'],
                        st.session_state.tv_form_data['tv_date'],
                        st.session_state.tv_form_data['tv_time'],
                        st.session_state.tv_form_data['assigned_provider'],  # Initial TV provider
                        st.session_state.tv_form_data.get('assigned_regional_provider', 'Select Regional Provider...'),  # Regional provider from tv_form_data
                        st.session_state.tv_form_data['assigned_coordinator']
                    )

                    # COMPREHENSIVE SYNC: Update ALL tables at once (patients, patient_panel, ZMO, HHC, patient_assignments)
                    with st.spinner("Syncing patient data to all tables..."):
                        sync_result = database.sync_onboarding_to_all_tables(patient_details['onboarding_id'])

                    # Display sync results
                    if sync_result['success']:
                        st.success(f"✅ Patient synced to all tables:")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Patients Table", "✓" if sync_result['patients_table'] else "✗")
                        with col_b:
                            st.metric("Patient Panel (ZMO)", "✓" if sync_result['patient_panel'] else "✗")
                        with col_c:
                            st.metric("Patient Assignments", "✓" if sync_result['patient_assignments'] else "✗")
                        col_d, col_e = st.columns(2)
                        with col_d:
                            st.metric("HHC Export", "✓" if sync_result['hhc_export'] else "✗")
                        with col_e:
                            st.metric("Patient ID", sync_result.get('patient_id', 'N/A'))

                        if sync_result.get('message'):
                            st.info(sync_result['message'])
                    else:
                        st.error(f"❌ Sync failed: {sync_result.get('message', 'Unknown error')}")

                    # Complete Stage 5 and set patient status to 'Completed'
                    database.update_onboarding_stage_completion(patient_details['onboarding_id'], 5, True)
                    database.update_onboarding_patient_status(patient_details['onboarding_id'], 'Completed')

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

                    # Clear ZMO cache so patient appears immediately in ZMO tab
                    try:
                        zmo_module.get_patient_panel_data.clear()
                        zmo_module.get_patients_data.clear()
                    except Exception:
                        pass  # Cache clearing may fail if not yet loaded

                    st.success("🎉 Stage 5 Complete! Patient onboarding workflow finished.")
                    st.info(f"Patient ID: {sync_result.get('patient_id', 'N/A')} | Status: Completed | Synced to: patients, patient_panel (ZMO), HHC View, patient_assignments")
                    st.balloons()
                    st.session_state['onboarding_mode'] = None
                    st.rerun()
                else:
                    # Provide detailed error message about what's missing
                    missing_items = []
                    if not st.session_state.tv_form_data['tv_scheduled']:
                        missing_items.append("TV visit scheduled")
                    if not st.session_state.tv_form_data['patient_notified']:
                        missing_items.append("Patient notified")
                    if not st.session_state.tv_form_data['initial_tv_completed']:
                        missing_items.append("Initial TV visit completed")
                    if not regional_provider_assigned:
                        missing_items.append("Regional provider selected")
                    if not coordinator_assigned_in_patient_table:
                        missing_items.append("Coordinator selected")
                    
                    error_msg = "Cannot complete onboarding. Missing: " + ", ".join(missing_items)
                    st.error(error_msg)
    
    with col2:
        with st.form("save_progress_form"):
            if st.form_submit_button("Save Progress"):
                # Collect form data from session state
                form_data = {
                    'tv_date': st.session_state.tv_form_data['tv_date'],
                    'tv_time': st.session_state.tv_form_data['tv_time'],
                    'assigned_provider': st.session_state.tv_form_data['assigned_provider'],
                    'assigned_coordinator': st.session_state.tv_form_data['assigned_coordinator'],
                    'tv_scheduled': st.session_state.tv_form_data['tv_scheduled'],
                    'patient_notified': st.session_state.tv_form_data['patient_notified'],
                    'initial_tv_completed': st.session_state.tv_form_data['initial_tv_completed']
                }
                
                # Save the progress to database
                try:
                    result = database.save_onboarding_tv_scheduling_progress(patient_details['onboarding_id'], form_data)

                    if result:
                        # Sync patient data to tables if patient already exists
                        if patient_details.get('patient_id'):
                            try:
                                database.insert_patient_from_onboarding(patient_details['onboarding_id'])
                                database.sync_onboarding_to_patient_panel(patient_details['onboarding_id'])
                                # Clear ZMO cache so changes appear immediately
                                try:
                                    zmo_module.get_patient_panel_data.clear()
                                    zmo_module.get_patients_data.clear()
                                except Exception:
                                    pass
                                st.success("✅ Progress saved and patient data synced to ZMO!")
                            except Exception as e:
                                st.warning(f"Progress saved! (ZMO sync skipped: {e})")
                        else:
                            st.success("✅ Progress saved successfully! (Patient not yet added to ZMO)")

                        # Refresh the patient details to show updated data
                        st.session_state['view_patient_details'] = database.get_onboarding_patient_details(patient_details['onboarding_id'])
                        # Force queue refresh by setting a flag to reload queue data
                        st.session_state['force_queue_refresh'] = True
                        # Small delay to ensure database transaction is fully committed
                        import time
                        time.sleep(0.1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to save progress. Please try again.")
                except Exception as e:
                    st.error(f"❌ Exception during save: {e}")
                    # Show more detailed error information
                    import traceback
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())

    with col3:
        with st.form("back_to_queue_form"):
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
    tab1, tab2, tab3, tab4 = st.tabs(["Patient Queue", "Processing Status", "Facility Management", "ZMO"])
    
    # Tab 1: Patient Queue (Primary Tab)
    with tab1:
        st.subheader("Patient Onboarding Queue")
        
        # Get current onboarding queue
        try:
            # Check if we need to force refresh the queue data
            if st.session_state.get('force_queue_refresh', False):
                # Clear the flag
                st.session_state['force_queue_refresh'] = False
                # Add a small delay to ensure database changes are visible
                import time
                time.sleep(0.05)
            
            onboarding_queue = database.get_onboarding_queue()
            
            if onboarding_queue:
                # Create DataFrame for display
                queue_df = pd.DataFrame(onboarding_queue)
                
                # Format display columns with TV completion status
                display_df = pd.DataFrame({
                    "Patient": queue_df['patient_name'],
                    "Current Stage": queue_df['current_stage'], 
                    "Priority": queue_df['priority_status'],
                    "Assigned POT": queue_df['assigned_pot_name'].fillna('Unassigned'),
                    "TV Status": queue_df.apply(lambda row: 
                        "Completed" if row.get('initial_tv_completed') == 1 
                        else f"Assigned to {row.get('initial_tv_provider', 'Not Assigned')}" if row.get('initial_tv_provider') 
                        else "Not Assigned", axis=1),
                    "Action Required": queue_df.apply(get_action_required_blockers, axis=1),
                    "Created": pd.to_datetime(queue_df['created_date']).dt.strftime('%m/%d/%Y'),
                    "Last Update": pd.to_datetime(queue_df['updated_date']).dt.strftime('%m/%d/%Y %H:%M')
                })
                
                st.dataframe(
                    display_df, 
                    use_container_width=True,
                    column_config={
                        "Patient": st.column_config.TextColumn("Patient", width="medium"),
                        "Current Stage": st.column_config.TextColumn("Current Stage", width="medium"),
                        "Priority": st.column_config.TextColumn("Priority", width="small"),
                        "Assigned POT": st.column_config.TextColumn("Assigned POT", width="medium"),
                        "TV Status": st.column_config.TextColumn("TV Status", width="medium"),
                        "Action Required": st.column_config.TextColumn("Action Required", width="medium"),
                        "Created": st.column_config.TextColumn("Created", width="small"),
                        "Last Update": st.column_config.TextColumn("Last Update", width="medium")
                    },
                    hide_index=True
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
                        selected_stage = selected_patient.split(' - ')[1]
                        
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
                            # Additional actions can be added here if needed
                            pass
                        

                        
                        # Show patient workflow stepper if details are being viewed
                        if 'view_patient_details' in st.session_state:
                            patient_details = st.session_state['view_patient_details']
                            
                            # Only show if it's the same patient
                            if patient_details['onboarding_id'] == selected_id:
                                st.markdown("---")
                                st.markdown(f"## {patient_details['first_name']} {patient_details['last_name']}")
                                
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
                                st.markdown("### Next Actions")
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    if st.button("📝 Continue Workflow", key="continue_workflow"):
                                        st.session_state['current_onboarding_id'] = selected_id
                                        st.session_state['onboarding_mode'] = 'resume'
                                        st.success("Continuing workflow...")
                                        st.rerun()
                                
                                with col2:
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
                    'Completed'
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
                    hide_index=True
                )
                
                # Daily metrics
                st.markdown("### Daily Metrics")
                total_patients = len(onboarding_queue)
                completed_today = len([p for p in onboarding_queue if p['current_stage'] == 'Completed'])
                in_progress = total_patients - completed_today
                completion_rate = f"{(completed_today/total_patients)*100:.0f}%" if total_patients > 0 else "0%"
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Active Patients", total_patients)
                col2.metric("Completed Today", completed_today)
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

    # Tab 4: ZMO (Patient Data Management)
    with tab4:
        # Import and use the shared ZMO module
        from src.zmo_module import render_zmo_tab
        user_id = st.session_state.get("user_id", None)
        render_zmo_tab(user_id=user_id)

    # Add a quick reference section
    st.markdown("---")
    st.subheader("Onboarding Workflow Reference")
    st.write("""
    **ZEN Medical Onboarding Workflow (POT):**
    1. **Patient Registration** - Collect basic patient information
    2. **Eligibility Verification** - Verify insurance coverage
    3. **Chart Creation** - Create EMed patient chart
    4. **Intake Processing** - Collect medical records and documentation
    5. **TV Scheduling & Provider Assignment** - Schedule initial TV visit and assign regional provider
    """)
