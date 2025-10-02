import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_db_connection
from config.ui_style_config import apply_custom_css, get_section_title, TextStyle, ColorScheme

def get_weekly_billing_summary():
    """Get weekly billing summary from the new weekly billing system"""
    conn = get_db_connection()
    
    query = """
    SELECT 
        billing_week,
        week_start_date,
        week_end_date,
        total_tasks,
        total_billed_tasks,
        (total_tasks - total_billed_tasks) as total_unbilled_tasks,
        CASE 
            WHEN total_tasks > 0 THEN ROUND((total_billed_tasks * 100.0 / total_tasks), 2)
            ELSE 0 
        END as billing_percentage,
        report_generated_date as created_date,
        report_status
    FROM weekly_billing_reports
    ORDER BY billing_week DESC
    LIMIT 12
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_provider_billing_status():
    """Get provider-level billing status from the transformed billing system"""
    conn = get_db_connection()
    
    query = """
    SELECT 
        billing_status_id,
        provider_task_id,
        provider_name,
        patient_name,
        task_date,
        billing_week,
        week_start_date,
        week_end_date,
        task_description,
        minutes_of_service,
        billing_code,
        billing_code_description,
        billing_status,
        is_billed,
        is_invoiced,
        is_claim_submitted,
        is_insurance_processed,
        is_approved_to_pay,
        is_paid,
        is_carried_over,
        original_billing_week,
        carryover_reason,
        billing_notes,
        created_date,
        updated_date
    FROM provider_task_billing_status
    ORDER BY billing_week DESC, task_date DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_current_week_summary():
    """Get current week billing summary"""
    conn = get_db_connection()
    
    query = """
    SELECT 
        COUNT(*) as total_tasks,
        SUM(CASE WHEN is_billed = 1 THEN 1 ELSE 0 END) as billed_tasks,
        SUM(CASE WHEN billing_status = 'Not Billable' THEN 1 ELSE 0 END) as not_billable_tasks,
        SUM(CASE WHEN billing_status = 'Requires Attention' THEN 1 ELSE 0 END) as attention_tasks,
        SUM(CASE WHEN is_carried_over = 1 THEN 1 ELSE 0 END) as carryover_tasks
    FROM provider_task_billing_status
    WHERE billing_week = (
        SELECT MAX(billing_week) FROM provider_task_billing_status
    )
    """
    
    result = conn.execute(query).fetchone()
    conn.close()
    return result

def create_weekly_trend_chart(df):
    """Create weekly billing trend chart"""
    if df.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['billing_week'],
        y=df['billing_percentage'],
        mode='lines+markers',
        name='Billing Percentage',
        line=dict(color=ColorScheme.PRIMARY_BLUE, width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Weekly Billing Percentage Trend",
        xaxis_title="Billing Week",
        yaxis_title="Billing Percentage (%)",
        height=400,
        yaxis=dict(range=[0, 100])
    )
    
    return fig

def create_billing_status_distribution(df):
    """Create billing status distribution chart"""
    if df.empty:
        return None
    
    # Calculate status distribution
    billed = len(df[df['is_billed'] == 1])
    not_billable = len(df[df['billing_status'] == 'Not Billable'])
    unbilled = len(df[(df['is_billed'] == 0) & (df['billing_status'] != 'Not Billable')])
    
    labels = ['Billed', 'Not Billable', 'Unbilled']
    values = [billed, not_billable, unbilled]
    colors = [ColorScheme.SUCCESS_GREEN, ColorScheme.NEUTRAL_GRAY, ColorScheme.WARNING_ORANGE]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        hole=0.4
    )])
    
    fig.update_layout(
        title="Current Billing Status Distribution",
        height=400
    )
    
    return fig

def create_provider_performance_chart(df):
    """Create provider billing performance chart"""
    if df.empty:
        return None
    
    # Group by provider and calculate billing rates
    provider_stats = df.groupby('provider_name').agg({
        'is_billed': 'sum',
        'provider_task_id': 'count'
    }).reset_index()
    
    provider_stats['billing_rate'] = (provider_stats['is_billed'] / provider_stats['provider_task_id'] * 100).round(1)
    provider_stats = provider_stats.sort_values('billing_rate', ascending=True)
    
    fig = px.bar(
        provider_stats,
        x='billing_rate',
        y='provider_name',
        orientation='h',
        title="Provider Billing Performance",
        labels={'billing_rate': 'Billing Rate (%)', 'provider_name': 'Provider'},
        color='billing_rate',
        color_continuous_scale='RdYlGn'
    )
    
    fig.update_layout(height=max(400, len(provider_stats) * 30))
    
    return fig

def display_tasks_requiring_attention(df):
    """Display tasks that require attention"""
    attention_tasks = df[df['billing_status'] == 'Requires Attention']
    
    if attention_tasks.empty:
        st.success(f"{TextStyle.SUCCESS_INDICATOR} No tasks currently require attention")
        return
    
    st.warning(f"{TextStyle.ALERT_INDICATOR} {len(attention_tasks)} tasks require attention")
    
    # Display attention tasks
    display_df = attention_tasks[[
        'provider_name', 'patient_name', 'task_date', 'billing_code', 
        'minutes_of_service', 'task_description'
    ]].copy()
    
    display_df.columns = [
        'Provider', 'Patient', 'Task Date', 'Billing Code', 
        'Minutes', 'Description'
    ]
    
    st.dataframe(display_df, use_container_width=True)

def display_carryover_tasks(df):
    """Display carryover tasks from previous weeks"""
    carryover_tasks = df[df['is_carried_over'] == 1]
    
    if carryover_tasks.empty:
        st.info(f"{TextStyle.INFO_INDICATOR} No carryover tasks from previous weeks")
        return
    
    st.info(f"{TextStyle.INFO_INDICATOR} {len(carryover_tasks)} tasks carried over from previous weeks")
    
    # Display carryover tasks
    display_df = carryover_tasks[[
        'provider_name', 'patient_name', 'task_date', 'billing_code', 
        'original_billing_week', 'minutes_of_service'
    ]].copy()
    
    display_df.columns = [
        'Provider', 'Patient', 'Task Date', 'Billing Code', 
        'Original Week', 'Minutes'
    ]
    
    st.dataframe(display_df, use_container_width=True)

def display_billing_dashboard():
    """Main function to display the weekly billing dashboard"""
    apply_custom_css()
    
    st.title(get_section_title("Weekly Billing System Dashboard"))
    st.markdown("### Healthcare Provider Billing Management")
    
    # Load data
    with st.spinner("Loading weekly billing data..."):
        weekly_summary_df = get_weekly_billing_summary()
        provider_billing_df = get_provider_billing_status()
        current_week_stats = get_current_week_summary()
    
    # Current week summary metrics
    st.subheader(get_section_title("Current Week Summary"))
    
    if current_week_stats:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Tasks", current_week_stats[0] or 0)
        
        with col2:
            billed = current_week_stats[1] or 0
            st.metric("Billed Tasks", billed)
        
        with col3:
            not_billable = current_week_stats[2] or 0
            st.metric("Not Billable", not_billable)
        
        with col4:
            attention = current_week_stats[3] or 0
            st.metric("Require Attention", attention, delta_color="inverse")
        
        with col5:
            carryover = current_week_stats[4] or 0
            st.metric("Carryover Tasks", carryover)
    
    # Weekly trends
    st.subheader(get_section_title("Weekly Billing Trends"))
    
    if not weekly_summary_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            trend_chart = create_weekly_trend_chart(weekly_summary_df)
            if trend_chart:
                st.plotly_chart(trend_chart, use_container_width=True)
        
        with col2:
            if not provider_billing_df.empty:
                status_chart = create_billing_status_distribution(provider_billing_df)
                if status_chart:
                    st.plotly_chart(status_chart, use_container_width=True)
    
    # Provider performance
    st.subheader(get_section_title("Provider Billing Performance"))
    
    if not provider_billing_df.empty:
        performance_chart = create_provider_performance_chart(provider_billing_df)
        if performance_chart:
            st.plotly_chart(performance_chart, use_container_width=True)
    
    # Tasks requiring attention
    st.subheader(get_section_title("Tasks Requiring Attention"))
    display_tasks_requiring_attention(provider_billing_df)
    
    # Carryover tasks
    st.subheader(get_section_title("Carryover Tasks"))
    display_carryover_tasks(provider_billing_df)
    
    # Weekly summary table
    st.subheader(get_section_title("Weekly Summary History"))
    
    if not weekly_summary_df.empty:
        display_summary = weekly_summary_df[[
            'billing_week', 'week_start_date', 'week_end_date', 
            'total_tasks', 'total_billed_tasks', 'billing_percentage'
        ]].copy()
        
        display_summary.columns = [
            'Week', 'Start Date', 'End Date', 
            'Total Tasks', 'Billed Tasks', 'Billing %'
        ]
        
        # Format percentage
        display_summary['Billing %'] = display_summary['Billing %'].round(1).astype(str) + '%'
        
        st.dataframe(display_summary, use_container_width=True)
    else:
        st.info(f"{TextStyle.INFO_INDICATOR} No weekly billing data available")

if __name__ == "__main__":
    display_billing_dashboard()