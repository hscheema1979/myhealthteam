"""
Provider Payment Dashboard (P00)
Comprehensive payment management dashboard for Justin to track provider payments by week and month.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import calendar
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_db_connection
from config.ui_style_config import apply_custom_css, get_section_title, TextStyle, ColorScheme
from billing.weekly_billing_processor import WeeklyBillingProcessor

def get_provider_payment_summary():
    """Get provider payment summary with weekly/monthly breakdown"""
    conn = get_db_connection()
    
    query = """
    SELECT 
        billing_week,
        week_start_date,
        week_end_date,
        provider_name,
        COUNT(*) as total_tasks,
        SUM(minutes_of_service) as total_minutes,
        SUM(CASE WHEN is_billed = 1 THEN minutes_of_service ELSE 0 END) as billed_minutes,
        SUM(CASE WHEN is_paid = 1 THEN minutes_of_service ELSE 0 END) as paid_minutes,
        COUNT(CASE WHEN is_paid = 1 THEN 1 END) as paid_tasks,
        COUNT(CASE WHEN is_billed = 1 THEN 1 END) as billed_tasks,
        SUM(CASE WHEN is_paid = 1 THEN minutes_of_service ELSE 0 END) as total_paid_minutes,
        MIN(task_date) as earliest_task_date,
        MAX(task_date) as latest_task_date
    FROM provider_task_billing_status
    GROUP BY billing_week, week_start_date, week_end_date, provider_name
    ORDER BY billing_week DESC, provider_name
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Calculate financial metrics
    if not df.empty:
        # Assumed rate of $60 per hour (adjustable in UI)
        df['total_cost'] = (df['total_minutes'] / 60) * 60  # $60/hour
        df['paid_cost'] = (df['paid_minutes'] / 60) * 60
        df['unpaid_cost'] = df['total_cost'] - df['paid_cost']
        df['billing_percentage'] = (df['paid_minutes'] / df['total_minutes'] * 100).round(1)
    
    return df

def get_provider_monthly_summary():
    """Get provider payment summary by month"""
    conn = get_db_connection()
    
    query = """
    SELECT 
        strftime('%Y-%m', task_date) as month,
        strftime('%Y', task_date) as year,
        strftime('%m', task_date) as month_num,
        provider_name,
        COUNT(*) as total_tasks,
        SUM(minutes_of_service) as total_minutes,
        SUM(CASE WHEN is_billed = 1 THEN minutes_of_service ELSE 0 END) as billed_minutes,
        SUM(CASE WHEN is_paid = 1 THEN minutes_of_service ELSE 0 END) as paid_minutes,
        COUNT(CASE WHEN is_paid = 1 THEN 1 END) as paid_tasks,
        COUNT(CASE WHEN is_billed = 1 THEN 1 END) as billed_tasks,
        MIN(task_date) as month_start,
        MAX(task_date) as month_end
    FROM provider_task_billing_status
    GROUP BY strftime('%Y-%m', task_date), provider_name
    ORDER BY month DESC, provider_name
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Calculate financial metrics
    if not df.empty:
        df['total_cost'] = (df['total_minutes'] / 60) * 60  # $60/hour
        df['paid_cost'] = (df['paid_minutes'] / 60) * 60
        df['unpaid_cost'] = df['total_cost'] - df['paid_cost']
        df['billing_percentage'] = (df['paid_minutes'] / df['total_minutes'] * 100).round(1)
        df['month_name'] = df.apply(lambda x: f"{calendar.month_name[int(x['month_num'])]} {x['year']}", axis=1)
    
    return df

def get_outstanding_payments():
    """Get all outstanding (unpaid) tasks that need payment"""
    conn = get_db_connection()
    
    query = """
    SELECT 
        billing_status_id,
        provider_task_id,
        provider_name,
        patient_name,
        task_date,
        billing_week,
        task_description,
        minutes_of_service,
        billing_code,
        billing_status,
        CASE 
            WHEN minutes_of_service = 0 THEN 0.0
            ELSE (minutes_of_service / 60.0) * 60.0
        END as estimated_cost,
        CASE 
            WHEN is_billed = 1 THEN 'Ready for Payment'
            ELSE 'Pending Billing'
        END as payment_readiness,
        created_date
    FROM provider_task_billing_status
    WHERE is_paid = 0 OR is_paid IS NULL
    ORDER BY task_date DESC, provider_name
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

def update_provider_payment(billing_status_ids, payment_amount, payment_date, notes):
    """Update multiple provider tasks as paid"""
    try:
        processor = WeeklyBillingProcessor()
        
        success_count = 0
        for billing_status_id in billing_status_ids:
            if processor.update_billing_status(
                billing_status_id=billing_status_id,
                new_status='Paid',
                notes=notes,
                external_id=f"PAY_{payment_date.strftime('%Y%m%d')}_{len(billing_status_ids)}"
            ):
                success_count += 1
        
        return success_count == len(billing_status_ids)
    except Exception as e:
        st.error(f"Error updating payments: {str(e)}")
        return False

def create_payment_summary_chart(df, timeframe="weekly"):
    """Create payment summary chart"""
    if df.empty:
        return None
    
    fig = go.Figure()
    
    if timeframe == "weekly":
        # Weekly chart
        fig.add_trace(go.Bar(
            name='Total Cost',
            x=df['billing_week'],
            y=df['total_cost'],
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Paid Cost',
            x=df['billing_week'],
            y=df['paid_cost'],
            marker_color='green'
        ))
        
        fig.add_trace(go.Bar(
            name='Outstanding Cost',
            x=df['billing_week'],
            y=df['unpaid_cost'],
            marker_color='red'
        ))
        
        fig.update_layout(
            title="Weekly Payment Summary",
            xaxis_title="Billing Week",
            yaxis_title="Cost ($)",
            barmode='stack'
        )
    
    else:
        # Monthly chart
        fig.add_trace(go.Bar(
            name='Total Cost',
            x=df['month_name'],
            y=df['total_cost'],
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Paid Cost',
            x=df['month_name'],
            y=df['paid_cost'],
            marker_color='green'
        ))
        
        fig.add_trace(go.Bar(
            name='Outstanding Cost',
            x=df['month_name'],
            y=df['unpaid_cost'],
            marker_color='red'
        ))
        
        fig.update_layout(
            title="Monthly Payment Summary",
            xaxis_title="Month",
            yaxis_title="Cost ($)",
            barmode='stack'
        )
    
    return fig

def create_provider_outstanding_chart(df):
    """Create chart showing outstanding payments by provider"""
    if df.empty:
        return None
    
    # Group by provider
    provider_summary = df.groupby('provider_name').agg({
        'estimated_cost': 'sum',
        'minutes_of_service': 'sum',
        'billing_status_id': 'count'
    }).reset_index()
    
    provider_summary.columns = ['Provider', 'Outstanding Cost', 'Minutes Outstanding', 'Tasks Outstanding']
    
    fig = px.bar(
        provider_summary,
        y='Provider',
        x='Outstanding Cost',
        title="Outstanding Payments by Provider",
        labels={'Outstanding Cost': 'Cost ($)', 'Provider': 'Provider'},
        color='Outstanding Cost',
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(height=max(400, len(provider_summary) * 30))
    
    return fig

def display_provider_payment_dashboard():
    """Main function to display the provider payment dashboard"""
    apply_custom_css()
    
    st.title(get_section_title("Provider Payment Management Dashboard"))
    st.markdown("### Payment Tracking and Processing for Justin")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Rate per hour input
    hourly_rate = st.sidebar.number_input(
        "Hourly Rate ($)",
        min_value=10.0,
        max_value=200.0,
        value=60.0,
        step=5.0,
        help="Provider hourly rate for cost calculations"
    )
    
    # Load data
    with st.spinner("Loading payment data..."):
        weekly_df = get_provider_payment_summary()
        monthly_df = get_provider_monthly_summary()
        outstanding_df = get_outstanding_payments()
    
    # Update financial calculations with current rate
    if not weekly_df.empty:
        weekly_df['total_cost'] = (weekly_df['total_minutes'] / 60) * hourly_rate
        weekly_df['paid_cost'] = (weekly_df['paid_minutes'] / 60) * hourly_rate
        weekly_df['unpaid_cost'] = weekly_df['total_cost'] - weekly_df['paid_cost']
    
    if not monthly_df.empty:
        monthly_df['total_cost'] = (monthly_df['total_minutes'] / 60) * hourly_rate
        monthly_df['paid_cost'] = (monthly_df['paid_minutes'] / 60) * hourly_rate
        monthly_df['unpaid_cost'] = monthly_df['total_cost'] - monthly_df['paid_cost']
    
    if not outstanding_df.empty:
        outstanding_df['estimated_cost'] = (outstanding_df['minutes_of_service'] / 60) * hourly_rate
    
    # Summary metrics
    st.subheader(get_section_title("Payment Summary"))
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_cost = weekly_df['total_cost'].sum() if not weekly_df.empty else 0
    paid_cost = weekly_df['paid_cost'].sum() if not weekly_df.empty else 0
    outstanding_cost = weekly_df['unpaid_cost'].sum() if not weekly_df.empty else 0
    outstanding_tasks = len(outstanding_df)
    
    with col1:
        st.metric("Total Cost (All Time)", f"${total_cost:,.2f}")
    
    with col2:
        st.metric("Paid Amount", f"${paid_cost:,.2f}")
    
    with col3:
        st.metric("Outstanding Amount", f"${outstanding_cost:,.2f}", delta=f"{outstanding_tasks} tasks")
    
    with col4:
        payment_rate = (paid_cost / total_cost * 100) if total_cost > 0 else 0
        st.metric("Payment Rate", f"{payment_rate:.1f}%")
    
    # Payment management section
    st.subheader(get_section_title("Payment Processing"))
    
    if not outstanding_df.empty:
        # Outstanding payments table
        st.markdown("#### Outstanding Payments")
        
        # Allow selection for batch payment
        selected_payments = st.multiselect(
            "Select tasks to mark as paid:",
            options=outstanding_df['billing_status_id'].tolist(),
            format_func=lambda x: f"{outstanding_df[outstanding_df['billing_status_id']==x]['provider_name'].iloc[0]} - {outstanding_df[outstanding_df['billing_status_id']==x]['patient_name'].iloc[0]} - {outstanding_df[outstanding_df['billing_status_id']==x]['task_date'].iloc[0]} (${outstanding_df[outstanding_df['billing_status_id']==x]['estimated_cost'].iloc[0]:.2f})"
        )
        
        if selected_payments:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                payment_date = st.date_input("Payment Date", value=datetime.now().date())
            
            with col2:
                payment_notes = st.text_area("Payment Notes", placeholder="e.g., 'Payment via check #12345'")
            
            with col3:
                if st.button("Mark Selected as Paid", type="primary"):
                    if update_provider_payment(selected_payments, outstanding_df['estimated_cost'].sum(), payment_date, payment_notes):
                        st.success(f"Successfully marked {len(selected_payments)} tasks as paid!")
                        st.rerun()
                    else:
                        st.error("Failed to update payments")
        
        # Display outstanding tasks
        display_outstanding = outstanding_df[[
            'provider_name', 'patient_name', 'task_date', 'minutes_of_service', 
            'estimated_cost', 'payment_readiness', 'billing_status'
        ]].copy()
        
        display_outstanding.columns = ['Provider', 'Patient', 'Task Date', 'Minutes', 'Cost', 'Status', 'Billing Status']
        st.dataframe(display_outstanding, use_container_width=True)
    
    # Charts
    st.subheader(get_section_title("Payment Analytics"))
    
    # Timeframe selection
    chart_timeframe = st.selectbox("Select Chart Timeframe", ["Weekly", "Monthly"], index=0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Payment summary chart
        if chart_timeframe == "Weekly" and not weekly_df.empty:
            summary_chart = create_payment_summary_chart(weekly_df, "weekly")
        elif chart_timeframe == "Monthly" and not monthly_df.empty:
            summary_chart = create_payment_summary_chart(monthly_df, "monthly")
        else:
            summary_chart = None
        
        if summary_chart:
            st.plotly_chart(summary_chart, use_container_width=True)
    
    with col2:
        # Outstanding payments by provider
        if not outstanding_df.empty:
            outstanding_chart = create_provider_outstanding_chart(outstanding_df)
            if outstanding_chart:
                st.plotly_chart(outstanding_chart, use_container_width=True)
    
    # Weekly breakdown
    if not weekly_df.empty and chart_timeframe == "Weekly":
        st.subheader(get_section_title("Weekly Payment Breakdown"))
        
        # Allow week selection
        weeks = ['All Weeks'] + sorted(weekly_df['billing_week'].unique().tolist())
        selected_week = st.selectbox("Select Week", weeks)
        
        week_df = weekly_df.copy()
        if selected_week != 'All Weeks':
            week_df = week_df[week_df['billing_week'] == selected_week]
        
        display_week = week_df[[
            'billing_week', 'provider_name', 'total_tasks', 'total_minutes', 
            'total_cost', 'paid_cost', 'unpaid_cost', 'billing_percentage'
        ]].copy()
        
        display_week.columns = ['Week', 'Provider', 'Tasks', 'Minutes', 'Total Cost', 'Paid Cost', 'Outstanding', 'Payment %']
        
        # Format numbers
        display_week['Total Cost'] = display_week['Total Cost'].apply(lambda x: f"${x:,.2f}")
        display_week['Paid Cost'] = display_week['Paid Cost'].apply(lambda x: f"${x:,.2f}")
        display_week['Outstanding'] = display_week['Outstanding'].apply(lambda x: f"${x:,.2f}")
        display_week['Payment %'] = display_week['Payment %'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(display_week, use_container_width=True)
    
    # Monthly breakdown
    if not monthly_df.empty and chart_timeframe == "Monthly":
        st.subheader(get_section_title("Monthly Payment Breakdown"))
        
        # Allow month selection
        months = ['All Months'] + sorted(monthly_df['month_name'].unique().tolist())
        selected_month = st.selectbox("Select Month", months)
        
        month_df = monthly_df.copy()
        if selected_month != 'All Months':
            month_df = month_df[month_df['month_name'] == selected_month]
        
        display_month = month_df[[
            'month_name', 'provider_name', 'total_tasks', 'total_minutes',
            'total_cost', 'paid_cost', 'unpaid_cost', 'billing_percentage'
        ]].copy()
        
        display_month.columns = ['Month', 'Provider', 'Tasks', 'Minutes', 'Total Cost', 'Paid Cost', 'Outstanding', 'Payment %']
        
        # Format numbers
        display_month['Total Cost'] = display_month['Total Cost'].apply(lambda x: f"${x:,.2f}")
        display_month['Paid Cost'] = display_month['Paid Cost'].apply(lambda x: f"${x:,.2f}")
        display_month['Outstanding'] = display_month['Outstanding'].apply(lambda x: f"${x:,.2f}")
        display_month['Payment %'] = display_month['Payment %'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(display_month, use_container_width=True)

if __name__ == "__main__":
    display_provider_payment_dashboard()