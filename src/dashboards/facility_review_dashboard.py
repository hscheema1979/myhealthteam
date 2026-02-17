"""
Facility Review Dashboard

For facility staff to:
1. View their facility's patients (HHC-style view)
2. Review patient status, visits, and workflows
3. Submit new patient intakes to onboarding team

Role: FACILITY (42)
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import base64
from io import BytesIO

from src import database as db
from src.config.ui_style_config import get_section_title, TextStyle, apply_custom_css
from src.dashboards.workflow_module import get_active_workflow_instances

# Role constant
ROLE_FACILITY = 42

# Ensure uploads directory exists
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "onboarding")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_facility_for_user(user_id):
    """Get facility ID for logged-in facility user"""
    return db.get_user_facility(user_id)


def save_uploaded_file(uploaded_file, onboarding_id, file_type):
    """Save uploaded file and return path"""
    if uploaded_file is None:
        return None
    
    # Create directory for this onboarding
    onboarding_dir = os.path.join(UPLOAD_DIR, str(onboarding_id))
    os.makedirs(onboarding_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = uploaded_file.name.split('.')[-1] if '.' in uploaded_file.name else 'pdf'
    filename = f"{file_type}_{timestamp}.{file_ext}"
    filepath = os.path.join(onboarding_dir, filename)
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return filepath


def show_facility_header(facility_id):
    """Display facility dashboard header"""
    # Get facility name
    facilities = db.get_all_facilities()
    facility_name = "Unknown Facility"
    for f in facilities:
        if f['facility_id'] == facility_id:
            facility_name = f['facility_name']
            break
    
    st.title(get_section_title(f"Facility Dashboard: {facility_name}"))
    st.markdown("---")


def tab_facility_patients(facility_id):
    """
    Tab 1: HHC-style view of all patients at this facility
    """
    st.header(get_section_title("My Facility's Patients"))
    st.markdown("View all patients currently managed at your facility.")
    
    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        search_term = st.text_input("Search by Name or ID", key="facility_patient_search")
    
    with col2:
        # Get available statuses
        conn = db.get_db_connection()
        try:
            status_rows = conn.execute("""
                SELECT DISTINCT status FROM patient_panel 
                WHERE status IS NOT NULL AND status != ''
                ORDER BY status
            """).fetchall()
            available_statuses = [s[0] for s in status_rows]
        except:
            available_statuses = ['Active', 'Active-PCP', 'Active-Geri', 'HOSPICE', 'Pending', 'New']
        finally:
            conn.close()
        
        default_statuses = [s for s in available_statuses if s in ['Active', 'Active-PCP', 'Active-Geri', 'HOSPICE']]
        selected_statuses = st.multiselect(
            "Filter by Status",
            options=available_statuses,
            default=default_statuses,
            key="facility_status_filter"
        )
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("Refresh", key="facility_refresh_patients")
    
    # Load patients
    try:
        patients = db.get_patients_by_facility(
            facility_id,
            status_filter=selected_statuses if selected_statuses else None,
            search_term=search_term if search_term else None
        )
        
        if not patients:
            st.info("No patients found for your facility with the selected filters.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(patients)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Patients", len(df))
        with col2:
            active_count = len(df[df['status'].isin(['Active', 'Active-PCP', 'Active-Geri'])]) if 'status' in df.columns else 0
            st.metric("Active", active_count)
        with col3:
            high_risk = len(df[df['subjective_risk_level'] == 'High']) if 'subjective_risk_level' in df.columns else 0
            st.metric("High Risk", high_risk)
        with col4:
            mh_concerns = len(df[df['mental_health_concerns'] == 1]) if 'mental_health_concerns' in df.columns else 0
            st.metric("MH Concerns", mh_concerns)
        
        st.markdown("---")
        
        # Display key columns
        display_cols = [
            'patient_id', 'last_name', 'first_name', 'date_of_birth',
            'status', 'assigned_provider', 'assigned_coordinator',
            'last_visit_date', 'goc_value', 'subjective_risk_level'
        ]
        
        # Filter to columns that exist
        display_cols = [c for c in display_cols if c in df.columns]
        
        # Rename columns for display
        column_config = {
            'patient_id': st.column_config.TextColumn("Patient ID", width="small"),
            'last_name': st.column_config.TextColumn("Last Name"),
            'first_name': st.column_config.TextColumn("First Name"),
            'date_of_birth': st.column_config.TextColumn("DOB"),
            'status': st.column_config.TextColumn("Status"),
            'assigned_provider': st.column_config.TextColumn("Provider"),
            'assigned_coordinator': st.column_config.TextColumn("Coordinator"),
            'last_visit_date': st.column_config.TextColumn("Last Visit"),
            'goc_value': st.column_config.TextColumn("GoC"),
            'subjective_risk_level': st.column_config.TextColumn("Risk"),
        }
        
        st.dataframe(
            df[display_cols],
            column_config=column_config,
            use_container_width=True,
            height=500,
            hide_index=True
        )
        
        # Export option
        col1, col2 = st.columns([1, 3])
        with col1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download CSV",
                csv,
                f"facility_patients_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
        
    except Exception as e:
        st.error(f"Error loading patients: {e}")


def tab_patient_status_review(facility_id):
    """
    Tab 2: Detailed patient status review
    Shows: GoC, Mental Health, Code Status, Last Notes, Provider Visits, Coordinator Workflows
    """
    st.header(get_section_title("Patient Status & Visits Review"))
    st.markdown("Deep dive into individual patient status, clinical information, and care history.")
    
    # Patient selector
    try:
        patients = db.get_patients_by_facility(facility_id)
        if not patients:
            st.info("No patients found for your facility.")
            return

        # Format patient names as "Last, First (DOB: YYYY-MM-DD)" to handle patients with same name and birthday
        def format_patient_name_for_facility(p):
            last = (p.get('last_name', '') or '').strip()
            first = (p.get('first_name', '') or '').strip()
            dob = p.get('date_of_birth', '')
            # Format DOB for display (handle various formats)
            if dob:
                try:
                    dob_formatted = pd.to_datetime(dob, errors='coerce').strftime('%Y-%m-%d') if pd.notna(pd.to_datetime(dob, errors='coerce')) else str(dob)
                except:
                    dob_formatted = str(dob) if dob else ''
            else:
                dob_formatted = ''
            return f"{last}, {first} (DOB: {dob_formatted})" if dob_formatted else f"{last}, {first}"

        patient_options = {format_patient_name_for_facility(p): p['patient_id']
                          for p in patients}
        
        selected_patient_display = st.selectbox(
            "Select Patient to Review",
            options=list(patient_options.keys()),
            key="facility_patient_selector"
        )
        
        if not selected_patient_display:
            return
        
        patient_id = patient_options[selected_patient_display]
        patient = next((p for p in patients if p['patient_id'] == patient_id), None)
        
        if not patient:
            st.error("Patient not found.")
            return
        
        # Display patient info in expandable sections
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader(f"{patient['first_name']} {patient['last_name']}")
            st.caption(f"Patient ID: {patient_id}")
            st.caption(f"DOB: {patient.get('date_of_birth', 'N/A')}")
            st.caption(f"Status: {patient.get('status', 'N/A')}")
        
        with col2:
            st.markdown("**Care Team**")
            st.caption(f"Provider: {patient.get('assigned_provider', 'Unassigned')}")
            st.caption(f"Coordinator: {patient.get('assigned_coordinator', 'Unassigned')}")
            st.caption(f"Last Visit: {patient.get('last_visit_date', 'N/A')}")
        
        st.markdown("---")
        
        # Clinical Status Panel
        with st.expander("Clinical Status", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Goals of Care**")
                st.info(f"Status: {patient.get('goc_value', 'Not Set')}")
                if patient.get('goals_of_care'):
                    st.caption(patient['goals_of_care'])
                
                st.markdown("**Code Status**")
                st.info(patient.get('code_status', 'Not Set'))
            
            with col2:
                st.markdown("**Mental Health**")
                if patient.get('mental_health_concerns'):
                    st.warning("Mental Health Concerns: Yes")
                else:
                    st.success("Mental Health Concerns: No")
                
                st.markdown("**Cognitive Function**")
                st.info(patient.get('cognitive_function', 'Not Assessed'))
                
                st.markdown("**Functional Status**")
                st.info(patient.get('functional_status', 'Not Assessed'))
            
            with col3:
                st.markdown("**Risk Level**")
                risk = patient.get('subjective_risk_level', 'Unknown')
                if risk == 'High':
                    st.error(f"Risk: {risk}")
                elif risk == 'Medium':
                    st.warning(f"Risk: {risk}")
                else:
                    st.success(f"Risk: {risk}")
                
                st.markdown("**Utilization (12mo)**")
                st.caption(f"ER Visits: {patient.get('er_count_1yr', 0)}")
                st.caption(f"Hospitalizations: {patient.get('hospitalization_count_1yr', 0)}")
        
        # Active Concerns & Specialists
        with st.expander("Active Concerns & Specialists"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Active Concerns**")
                if patient.get('active_concerns'):
                    st.write(patient['active_concerns'])
                else:
                    st.caption("No active concerns recorded")
            
            with col2:
                st.markdown("**Active Specialists**")
                if patient.get('active_specialists'):
                    st.write(patient['active_specialists'])
                else:
                    st.caption("No active specialists recorded")
        
        # Notes Panel
        with st.expander("Clinical Notes"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Labs Notes**")
                st.text_area("", value=patient.get('labs_notes', 'No labs notes'), 
                           height=100, disabled=True, key=f"labs_notes_{patient_id}")
            
            with col2:
                st.markdown("**Imaging Notes**")
                st.text_area("", value=patient.get('imaging_notes', 'No imaging notes'), 
                           height=100, disabled=True, key=f"imaging_notes_{patient_id}")
            
            with col3:
                st.markdown("**General Notes**")
                st.text_area("", value=patient.get('general_notes', 'No general notes'), 
                           height=100, disabled=True, key=f"general_notes_{patient_id}")
        
        # Provider Visits Panel
        with st.expander("Recent Provider Visits"):
            latest_visit = db.get_latest_provider_visit(patient_id)
            if latest_visit:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**Last Visit**")
                    st.info(f"Date: {latest_visit.get('visit_date', 'N/A')}")
                    st.caption(f"Type: {latest_visit.get('service_type', 'N/A')}")
                with col2:
                    st.markdown("**Provider**")
                    st.info(latest_visit.get('provider_name', 'Unknown'))
                    st.caption(f"Duration: {latest_visit.get('duration_minutes', 'N/A')} min")
                with col3:
                    st.markdown("**Visit Details**")
                    st.caption(f"Location: {latest_visit.get('location_type', 'N/A')}")
                    st.caption(f"Billing Code: {latest_visit.get('billing_code', 'N/A')}")
                
                if latest_visit.get('notes'):
                    st.markdown("**Visit Notes**")
                    st.text_area("", value=latest_visit['notes'], height=80, 
                               disabled=True, key=f"visit_notes_{patient_id}")
            else:
                st.info("No provider visits found for this patient.")
        
        # Coordinator Workflows Panel
        with st.expander("Coordinator Workflows"):
            workflows = db.get_patient_workflow_history(patient_id)
            if workflows:
                for wf in workflows:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"**{wf.get('template_name', 'Unknown Workflow')}**")
                        st.caption(f"Coordinator: {wf.get('coordinator_name', 'Unassigned')}")
                    with col2:
                        status = wf.get('workflow_status', 'Unknown')
                        if status == 'Active':
                            st.info(f"Status: {status}")
                        elif status == 'Completed':
                            st.success(f"Status: {status}")
                        else:
                            st.warning(f"Status: {status}")
                    with col3:
                        st.caption(f"Step: {wf.get('current_step', 'N/A')}")
                        if wf.get('created_at'):
                            st.caption(f"Started: {wf['created_at'][:10]}")
                    
                    # Show step completion status
                    steps_complete = sum([
                        wf.get('step1_complete', 0),
                        wf.get('step2_complete', 0),
                        wf.get('step3_complete', 0),
                        wf.get('step4_complete', 0),
                        wf.get('step5_complete', 0),
                        wf.get('step6_complete', 0)
                    ])
                    st.progress(steps_complete / 6, text=f"Steps Complete: {steps_complete}/6")
                    st.markdown("---")
            else:
                st.info("No active workflows for this patient.")
        
    except Exception as e:
        st.error(f"Error loading patient review: {e}")
        import traceback
        st.error(traceback.format_exc())


def tab_intake_kickoff(facility_id, user_id):
    """
    Tab 3: New Patient Intake Kickoff
    Form to submit new patient to onboarding team
    """
    st.header(get_section_title("New Patient Intake Kickoff"))
    st.markdown("Submit new patient information and documents to the Onboarding Team.")
    
    # Two columns: Form and Recent Submissions
    col_form, col_history = st.columns([2, 1])
    
    with col_form:
        with st.form("facility_intake_form", clear_on_submit=True):
            st.subheader("Patient Information")
            
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name *", key="intake_first_name")
                date_of_birth = st.date_input("Date of Birth *", 
                                            value=None,
                                            max_value=datetime.now(),
                                            key="intake_dob")
            with col2:
                last_name = st.text_input("Last Name *", key="intake_last_name")
                phone = st.text_input("Phone Number", key="intake_phone")
            
            email = st.text_input("Email (optional)", key="intake_email")
            
            st.markdown("---")
            st.subheader("Insurance Information")
            
            insurance_provider = st.text_input("Primary Insurance Provider *", 
                                             key="intake_insurance")
            
            col1, col2 = st.columns(2)
            with col1:
                policy_number = st.text_input("Policy Number *", key="intake_policy")
            with col2:
                group_number = st.text_input("Group Number", key="intake_group")
            
            secondary_insurance = st.text_area("Secondary Insurance (optional)", 
                                              key="intake_secondary")
            
            st.markdown("---")
            st.subheader("Document Uploads")
            
            col1, col2 = st.columns(2)
            with col1:
                insurance_front = st.file_uploader("Insurance Card - Front *", 
                                                  type=['pdf', 'jpg', 'jpeg', 'png'],
                                                  key="intake_ins_front")
            with col2:
                insurance_back = st.file_uploader("Insurance Card - Back *", 
                                                 type=['pdf', 'jpg', 'jpeg', 'png'],
                                                 key="intake_ins_back")
            
            id_document = st.file_uploader("Driver's License / ID *", 
                                          type=['pdf', 'jpg', 'jpeg', 'png'],
                                          key="intake_id")
            
            st.markdown("---")
            st.subheader("Additional Information")
            
            col1, col2 = st.columns(2)
            with col1:
                priority = st.selectbox("Priority Level", 
                                       options=['Normal', 'High', 'Urgent'],
                                       index=0,
                                       key="intake_priority")
            with col2:
                gender = st.selectbox("Gender", 
                                     options=['', 'Male', 'Female', 'Other'],
                                     index=0,
                                     key="intake_gender")
            
            notes = st.text_area("Notes for Onboarding Team", 
                               height=100,
                               key="intake_notes")
            
            st.markdown("---")
            submitted = st.form_submit_button("Submit to Onboarding Team", 
                                             use_container_width=True,
                                             type="primary")
            
            if submitted:
                # Validation
                if not first_name or not last_name or not date_of_birth:
                    st.error("Please fill in required fields: First Name, Last Name, Date of Birth")
                    return
                
                if not insurance_provider or not policy_number:
                    st.error("Please fill in required insurance information")
                    return
                
                if not insurance_front or not insurance_back or not id_document:
                    st.error("Please upload all required documents")
                    return
                
                # Prepare patient data
                patient_data = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'date_of_birth': date_of_birth.strftime('%Y-%m-%d') if date_of_birth else None,
                    'phone_primary': phone,
                    'email': email,
                    'gender': gender,
                    'insurance_provider': insurance_provider,
                    'policy_number': policy_number,
                    'group_number': group_number,
                    'facility_name': None  # Will be filled from facility_id
                }
                
                # Get facility name
                facilities = db.get_all_facilities()
                for f in facilities:
                    if f['facility_id'] == facility_id:
                        patient_data['facility_name'] = f['facility_name']
                        break
                
                # Submit intake
                result = db.submit_facility_intake(
                    facility_user_id=user_id,
                    facility_id=facility_id,
                    patient_data=patient_data,
                    priority=priority,
                    notes=notes
                )
                
                if result['success']:
                    onboarding_id = result['onboarding_id']
                    
                    # Save uploaded files
                    doc_paths = {}
                    if insurance_front:
                        doc_paths['insurance_card_front_path'] = save_uploaded_file(
                            insurance_front, onboarding_id, "insurance_front")
                    if insurance_back:
                        doc_paths['insurance_card_back_path'] = save_uploaded_file(
                            insurance_back, onboarding_id, "insurance_back")
                    if id_document:
                        doc_paths['id_document_path'] = save_uploaded_file(
                            id_document, onboarding_id, "id_document")
                    
                    # Update document paths in database
                    if doc_paths:
                        db.update_facility_intake_documents(onboarding_id, doc_paths)
                    
                    st.success(f"✅ Intake submitted successfully! Onboarding ID: {onboarding_id}")
                    st.info("The Onboarding Team has been notified and will begin processing.")
                else:
                    st.error(f"❌ Error submitting intake: {result.get('error', 'Unknown error')}")
    
    with col_history:
        st.subheader("Recent Submissions")
        
        try:
            history = db.get_facility_intake_history(facility_id, days_back=30)
            
            if not history:
                st.info("No intake submissions in the last 30 days.")
            else:
                for item in history[:10]:  # Show last 10
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{item['last_name']}, {item['first_name']}**")
                            st.caption(f"Submitted: {item['intake_submitted_date'][:10] if item['intake_submitted_date'] else 'N/A'}")
                        with col2:
                            # Status badge
                            stage = item.get('current_stage', 'Pending')
                            if stage == 'Complete':
                                st.success("Complete")
                            elif stage == 'Pending':
                                st.info("Pending")
                            else:
                                st.warning(stage)
                        
                        st.caption(f"Priority: {item.get('intake_priority', 'Normal')} | Stage: {stage}")
                        st.markdown("---")
        
        except Exception as e:
            st.error(f"Error loading history: {e}")


def show(user_id, user_role_ids):
    """
    Main entry point for Facility Review Dashboard
    
    Args:
        user_id: Logged in user ID
        user_role_ids: List of role IDs for the user
    """
    # Apply custom CSS
    apply_custom_css()
    
    # Check if user has facility role
    if ROLE_FACILITY not in user_role_ids:
        st.error("You do not have permission to access the Facility Dashboard.")
        return
    
    # Get facility for this user
    facility_id = get_facility_for_user(user_id)
    
    if not facility_id:
        st.error("You are not assigned to a facility. Please contact your administrator.")
        return
    
    # Show header
    show_facility_header(facility_id)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "My Facility's Patients",
        "Patient Status Review", 
        "New Patient Intake Kickoff"
    ])
    
    with tab1:
        tab_facility_patients(facility_id)
    
    with tab2:
        tab_patient_status_review(facility_id)
    
    with tab3:
        tab_intake_kickoff(facility_id, user_id)


# For direct testing
if __name__ == "__main__":
    # Test with mock data
    st.set_page_config(page_title="Facility Dashboard", layout="wide")
    show(1, [42])
