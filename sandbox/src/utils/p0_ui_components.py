"""
ZEN Medical System - UI Components for P0 Enhancements
Professional healthcare UI components without emojis
Date: September 22, 2025
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src import database
from src.config.ui_style_config import TextStyle, get_section_title, get_metric_label

def mental_health_checkboxes(key_prefix="mh", existing_data=None):
    """
    Reusable mental health assessment checkboxes component
    Args:
        key_prefix: Unique prefix for checkbox keys
        existing_data: Dict with existing checkbox values
    Returns:
        Dict with checkbox values
    """
    st.subheader(get_section_title("Mental Health Assessment"))
    
    # Default values
    defaults = existing_data or {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        schizophrenia = st.checkbox(
            "Schizophrenia", 
            value=defaults.get('schizophrenia', False),
            key=f"{key_prefix}_schizophrenia"
        )
        depression = st.checkbox(
            "Depression", 
            value=defaults.get('depression', False),
            key=f"{key_prefix}_depression"
        )
        anxiety = st.checkbox(
            "Anxiety", 
            value=defaults.get('anxiety', False),
            key=f"{key_prefix}_anxiety"
        )
        stress = st.checkbox(
            "Stress", 
            value=defaults.get('stress', False),
            key=f"{key_prefix}_stress"
        )
    
    with col2:
        adhd = st.checkbox(
            "ADHD", 
            value=defaults.get('adhd', False),
            key=f"{key_prefix}_adhd"
        )
        bipolar = st.checkbox(
            "Bipolar Disorder", 
            value=defaults.get('bipolar', False),
            key=f"{key_prefix}_bipolar"
        )
        suicidal = st.checkbox(
            "Suicidal Ideation", 
            value=defaults.get('suicidal', False),
            key=f"{key_prefix}_suicidal"
        )
    
    return {
        'schizophrenia': schizophrenia,
        'depression': depression,
        'anxiety': anxiety,
        'stress': stress,
        'adhd': adhd,
        'bipolar': bipolar,
        'suicidal': suicidal
    }

def subjective_risk_level_assessment(current_level=None):
    """
    Subjective risk level assessment component (1-6 scale)
    Args:
        current_level: Current risk level (1-6)
    Returns:
        Selected risk level
    """
    st.subheader(get_section_title("Subjective Risk Level Assessment"))
    
    risk_levels = [
        (6, "Level 6 - In danger of dying or institutionalized within 1 yr"),
        (5, "Level 5 - Complications of chronic conditions or high risk social determinants"),
        (4, "Level 4 - Unstable chronic conditions but no complications"),
        (3, "Level 3 - Stable chronic conditions"),
        (2, "Level 2 - Healthy, some out of range biometrics"),
        (1, "Level 1 - Healthy, in range biometrics")
    ]
    
    # Find current index
    current_index = 0
    if current_level:
        for i, (level, _) in enumerate(risk_levels):
            if level == current_level:
                current_index = i
                break
    
    selected_label = st.selectbox(
        get_metric_label("Risk Level"),
        [label for _, label in risk_levels],
        index=current_index,
        help="Select the patient's current risk level based on clinical assessment"
    )
    
    # Return the numeric level
    for level, label in risk_levels:
        if label == selected_label:
            return level
    
    return 1

def weekly_patient_minutes_table(coordinator_id):
    """
    Weekly patient minutes tracking table component
    Args:
        coordinator_id: Coordinator ID to get data for
    """
    st.subheader(get_section_title("Weekly Patient Minutes Tracking"))
    
    try:
        # Get weekly data
        weekly_data = database.get_coordinator_weekly_patient_minutes(coordinator_id, weeks_back=4)
        
        if weekly_data:
            df = pd.DataFrame(weekly_data)
            
            # Create pivot table for better display
            if not df.empty:
                pivot_df = df.pivot_table(
                    index='patient_name',
                    columns='week',
                    values='total_minutes',
                    aggfunc='sum',
                    fill_value=0
                )
                
                # Display table
                st.dataframe(
                    pivot_df,
                    use_container_width=True,
                    height=400
                )
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_minutes = df['total_minutes'].sum()
                    st.metric(get_metric_label("Total Minutes (4 weeks)"), f"{total_minutes:,}")
                
                with col2:
                    unique_patients = df['patient_id'].nunique()
                    st.metric(get_metric_label("Patients Served"), unique_patients)
                
                with col3:
                    avg_minutes = total_minutes / unique_patients if unique_patients > 0 else 0
                    st.metric(get_metric_label("Avg Minutes per Patient"), f"{avg_minutes:.1f}")
            else:
                st.info(f"{TextStyle.INFO_INDICATOR} No patient minutes data available for the last 4 weeks.")
        else:
            st.info(f"{TextStyle.INFO_INDICATOR} No patient minutes recorded in the last 4 weeks.")
            
    except Exception as e:
        st.error(f"Error loading weekly patient minutes: {str(e)}")

def phone_reviews_form(coordinator_id):
    """
    Phone reviews form component for coordinators
    Args:
        coordinator_id: Coordinator ID for logging the review
    """
    st.subheader(get_section_title("Phone Reviews"))
    
    with st.form("phone_review_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            review_date = st.date_input(
                get_metric_label("Review Date"),
                value=datetime.now().date(),
                help="Date of the phone review"
            )
            
            # Get providers list
            try:
                providers = database.get_providers_list()
                provider_options = [f"{p['full_name']} ({p['email']})" for p in providers]
            except:
                provider_options = ["No providers available"]
            
            selected_provider = st.selectbox(
                get_metric_label("Provider Name"),
                provider_options,
                help="Select the provider for this phone review"
            )
        
        with col2:
            duration = st.number_input(
                get_metric_label("Duration (minutes)"),
                min_value=1,
                max_value=240,
                value=15,
                help="Duration of the phone review in minutes"
            )
        
        review_notes = st.text_area(
            get_metric_label("Review Notes"),
            height=100,
            help="Notes from the phone review discussion"
        )
        
        submitted = st.form_submit_button("Log Phone Review", use_container_width=True)
        
        if submitted:
            if selected_provider and review_notes.strip():
                form_data = {
                    'task_date': review_date,
                    'provider_name': selected_provider,
                    'duration_minutes': duration,
                    'notes': review_notes
                }
                
                try:
                    success = database.save_coordinator_phone_review(coordinator_id, form_data)
                    if success:
                        st.success("Phone review logged successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to log phone review. Please try again.")
                except Exception as e:
                    st.error(f"Error logging phone review: {str(e)}")
            else:
                st.warning("Please select a provider and add review notes.")

def workflow_management_section():
    """
    Workflow management controls component
    """
    st.subheader(get_section_title("Workflow Management"))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Kick Off Workflow", use_container_width=True):
            st.info("Workflow initiation feature coming soon...")
    
    with col2:
        if st.button("Resume Workflow", use_container_width=True):
            st.info("Workflow resume feature coming soon...")
    
    with col3:
        workflows = database.get_available_workflows()
        selected_workflow = st.selectbox(
            get_metric_label("Workflow ID"),
            workflows,
            help="Select workflow type for daily tasks"
        )
    
    return selected_workflow

def monthly_time_tracking_chart(coordinator_id, months_back=3):
    """
    Monthly time tracking chart component
    Args:
        coordinator_id: Coordinator ID
        months_back: Number of months to show
    """
    try:
        monthly_data = database.get_coordinator_monthly_patient_service_minutes(coordinator_id, months_back)
        
        if monthly_data:
            df = pd.DataFrame(monthly_data)
            
            # Create chart
            fig = px.bar(
                df,
                x='month',
                y='total_minutes_logged',
                title="Monthly Patient Service Minutes",
                labels={
                    'month': 'Month',
                    'total_minutes_logged': 'Total Minutes'
                }
            )
            
            fig.update_layout(
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary table
            st.dataframe(
                df[['month', 'year', 'total_patients_served', 'total_minutes_logged', 'total_tasks_completed']],
                use_container_width=True
            )
        else:
            st.info(f"{TextStyle.INFO_INDICATOR} No monthly summary data available.")
            
    except Exception as e:
        st.error(f"Error loading monthly time tracking: {str(e)}")

def psl_calendar_month_selector():
    """
    PSL Calendar month subdivision component
    Returns:
        Dict with selected month, visit type, and patient type
    """
    st.subheader(get_section_title("Patient Service Log - Monthly View"))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        months = database.get_calendar_months()
        selected_month = st.selectbox(
            get_metric_label("DOS Month"),
            [m['value'] for m in months],
            format_func=lambda x: next(m['label'] for m in months if m['value'] == x)
        )
    
    with col2:
        visit_type = st.selectbox(
            get_metric_label("Visit Type"),
            ["Home", "Tele", "Office"]
        )
    
    with col3:
        patient_type = st.selectbox(
            get_metric_label("Patient Type"),
            ["New", "Established"]
        )
    
    return {
        'selected_month': selected_month,
        'visit_type': visit_type,
        'patient_type': patient_type
    }

def contact_information_form(key_prefix="contact", existing_data=None):
    """
    Contact information form for onboarding Stage 1
    Args:
        key_prefix: Unique prefix for form keys
        existing_data: Dict with existing form values
    Returns:
        Dict with form data
    """
    st.subheader(get_section_title("Contact Information"))
    
    defaults = existing_data or {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Appointment Contact**")
        appointment_name = st.text_input(
            get_metric_label("Contact Name"),
            value=defaults.get('appointment_contact_name', ''),
            key=f"{key_prefix}_appt_name"
        )
        appointment_phone = st.text_input(
            get_metric_label("Phone Number"),
            value=defaults.get('appointment_contact_phone', ''),
            key=f"{key_prefix}_appt_phone"
        )
        appointment_email = st.text_input(
            get_metric_label("Email Address"),
            value=defaults.get('appointment_contact_email', ''),
            key=f"{key_prefix}_appt_email"
        )
    
    with col2:
        st.markdown("**Medical Contact**")
        medical_name = st.text_input(
            get_metric_label("Contact Name"),
            value=defaults.get('medical_contact_name', ''),
            key=f"{key_prefix}_med_name"
        )
        medical_phone = st.text_input(
            get_metric_label("Phone Number"),
            value=defaults.get('medical_contact_phone', ''),
            key=f"{key_prefix}_med_phone"
        )
        medical_email = st.text_input(
            get_metric_label("Email Address"),
            value=defaults.get('medical_contact_email', ''),
            key=f"{key_prefix}_med_email"
        )
    
    return {
        'appointment_contact_name': appointment_name,
        'appointment_contact_phone': appointment_phone,
        'appointment_contact_email': appointment_email,
        'medical_contact_name': medical_name,
        'medical_contact_phone': medical_phone,
        'medical_contact_email': medical_email
    }

def provider_information_form(key_prefix="provider", existing_data=None):
    """
    Provider information form for onboarding Stage 2
    Args:
        key_prefix: Unique prefix for form keys
        existing_data: Dict with existing form values
    Returns:
        Dict with form data
    """
    st.subheader(get_section_title("Provider Information"))
    
    defaults = existing_data or {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        pcp = st.text_input(
            get_metric_label("Primary Care Provider"),
            value=defaults.get('primary_care_provider', ''),
            key=f"{key_prefix}_pcp"
        )
        pcp_last_seen = st.date_input(
            get_metric_label("PCP Last Seen"),
            value=defaults.get('pcp_last_seen'),
            key=f"{key_prefix}_pcp_date"
        )
    
    with col2:
        specialist = st.text_input(
            get_metric_label("Active Specialist"),
            value=defaults.get('active_specialist', ''),
            key=f"{key_prefix}_specialist"
        )
        specialist_last_seen = st.date_input(
            get_metric_label("Specialist Last Seen"),
            value=defaults.get('specialist_last_seen'),
            key=f"{key_prefix}_specialist_date"
        )
    
    chronic_conditions = st.text_area(
        get_metric_label("Chronic Conditions"),
        value=defaults.get('chronic_conditions_onboarding', ''),
        key=f"{key_prefix}_conditions",
        height=100
    )
    
    return {
        'primary_care_provider': pcp,
        'pcp_last_seen': pcp_last_seen,
        'active_specialist': specialist,
        'specialist_last_seen': specialist_last_seen,
        'chronic_conditions_onboarding': chronic_conditions
    }