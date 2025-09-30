import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src import database as db

def display_provider_weekly_summary_chart(provider_id=None, show_all=False, title="Provider Weekly Performance Chart"):
    """Display provider weekly performance as interactive chart with filtering options"""
    st.subheader(title)
    
    # Date range filters
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        start_date = st.date_input(
            "Start Date", 
            value=datetime.now() - timedelta(days=90),
            key=f"chart_start_{provider_id}_{show_all}"
        )
    
    with col2:
        end_date = st.date_input(
            "End Date", 
            value=datetime.now(),
            key=f"chart_end_{provider_id}_{show_all}"
        )
    
    with col3:
        chart_type = st.selectbox(
            "Chart Type",
            [
                "Line Chart - Time Trends",
                "Bar Chart - Weekly Comparison", 
                "Scatter Plot - Tasks vs Time",
                "Area Chart - Cumulative View",
                "Multi-metric Dashboard",
                "Heatmap - Weekly Activity"
            ],
            key=f"chart_type_{provider_id}_{show_all}"
        )
    
    # Get data
    conn = db.get_db_connection()
    try:
        if show_all:
            # Admin/CPM view - show all providers
            query = """
                SELECT 
                    pws.provider_id,
                    pws.provider_name,
                    pws.year,
                    pws.week_number,
                    pws.week_start_date,
                    pws.week_end_date,
                    pws.total_tasks_completed,
                    pws.total_time_spent_minutes,
                    pws.average_daily_minutes,
                    pws.days_active,
                    pws.paid,
                    pws.created_date
                FROM provider_weekly_summary pws
                WHERE DATE(pws.week_start_date) >= ? AND DATE(pws.week_end_date) <= ?
                ORDER BY pws.year DESC, pws.week_number DESC, pws.provider_name
                LIMIT 500
            """
            data = conn.execute(query, (start_date, end_date)).fetchall()
        else:
            # Individual provider view
            query = """
                SELECT 
                    pws.provider_id,
                    pws.provider_name,
                    pws.year,
                    pws.week_number,
                    pws.week_start_date,
                    pws.week_end_date,
                    pws.total_tasks_completed,
                    pws.total_time_spent_minutes,
                    pws.average_daily_minutes,
                    pws.days_active,
                    pws.paid,
                    pws.created_date
                FROM provider_weekly_summary pws
                WHERE pws.provider_id = ? 
                AND DATE(pws.week_start_date) >= ? AND DATE(pws.week_end_date) <= ?
                ORDER BY pws.year DESC, pws.week_number DESC
            """
            data = conn.execute(query, (provider_id, start_date, end_date)).fetchall()
        
        if not data:
            st.info("No data found for the selected date range. Try expanding the date range.")
            return
            
        df = pd.DataFrame([dict(row) for row in data])
        
        # Data preprocessing
        df['week_period'] = df['year'].astype(str) + '-W' + df['week_number'].astype(str).str.zfill(2)
        df['week_start_date'] = pd.to_datetime(df['week_start_date'])
        df['week_end_date'] = pd.to_datetime(df['week_end_date'])
        df['hours_spent'] = df['total_time_spent_minutes'] / 60
        df['payment_status'] = df['paid'].apply(lambda x: 'Paid' if x else 'Pending')
        
        # Sort by date for proper time series display
        df = df.sort_values('week_start_date')
        
        # Create charts based on selection
        if chart_type == "Line Chart - Time Trends":
            create_line_chart(df, show_all)
        elif chart_type == "Bar Chart - Weekly Comparison":
            create_bar_chart(df, show_all)
        elif chart_type == "Scatter Plot - Tasks vs Time":
            create_scatter_chart(df, show_all)
        elif chart_type == "Area Chart - Cumulative View":
            create_area_chart(df, show_all)
        elif chart_type == "Multi-metric Dashboard":
            create_multi_metric_dashboard(df, show_all)
        elif chart_type == "Heatmap - Weekly Activity":
            create_heatmap_chart(df, show_all)
            
        # Display summary metrics
        display_summary_metrics(df, show_all)
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
    finally:
        conn.close()

def create_line_chart(df, show_all):
    """Create line chart showing trends over time"""
    st.markdown("### 📈 Time Trends")
    
    # Metric selection
    metrics = st.multiselect(
        "Select metrics to display:",
        ["Total Tasks", "Total Hours", "Days Active", "Avg Daily Minutes"],
        default=["Total Tasks", "Total Hours"],
        key="line_metrics"
    )
    
    if not metrics:
        st.warning("Please select at least one metric to display.")
        return
    
    fig = go.Figure()
    
    if show_all:
        # Multiple providers - use different colors for each
        for provider in df['provider_name'].unique():
            provider_data = df[df['provider_name'] == provider]
            
            if "Total Tasks" in metrics:
                fig.add_trace(go.Scatter(
                    x=provider_data['week_start_date'],
                    y=provider_data['total_tasks_completed'],
                    mode='lines+markers',
                    name=f'{provider} - Tasks',
                    line=dict(width=2),
                    hovertemplate='<b>%{fullData.name}</b><br>Week: %{x}<br>Tasks: %{y}<extra></extra>'
                ))
            
            if "Total Hours" in metrics:
                fig.add_trace(go.Scatter(
                    x=provider_data['week_start_date'],
                    y=provider_data['hours_spent'],
                    mode='lines+markers',
                    name=f'{provider} - Hours',
                    yaxis='y2',
                    line=dict(width=2, dash='dash'),
                    hovertemplate='<b>%{fullData.name}</b><br>Week: %{x}<br>Hours: %{y:.1f}<extra></extra>'
                ))
    else:
        # Single provider - different metrics as separate lines
        if "Total Tasks" in metrics:
            fig.add_trace(go.Scatter(
                x=df['week_start_date'],
                y=df['total_tasks_completed'],
                mode='lines+markers',
                name='Tasks Completed',
                line=dict(color='#1f77b4', width=3),
                hovertemplate='Week: %{x}<br>Tasks: %{y}<extra></extra>'
            ))
        
        if "Total Hours" in metrics:
            fig.add_trace(go.Scatter(
                x=df['week_start_date'],
                y=df['hours_spent'],
                mode='lines+markers',
                name='Hours Spent',
                yaxis='y2',
                line=dict(color='#ff7f0e', width=3),
                hovertemplate='Week: %{x}<br>Hours: %{y:.1f}<extra></extra>'
            ))
        
        if "Days Active" in metrics:
            fig.add_trace(go.Scatter(
                x=df['week_start_date'],
                y=df['days_active'],
                mode='lines+markers',
                name='Days Active',
                line=dict(color='#2ca02c', width=3),
                hovertemplate='Week: %{x}<br>Days: %{y}<extra></extra>'
            ))
    
    # Update layout
    fig.update_layout(
        title="Weekly Performance Trends",
        xaxis_title="Week",
        yaxis_title="Tasks / Days",
        yaxis2=dict(
            title="Hours",
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        height=500,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_bar_chart(df, show_all):
    """Create bar chart for weekly comparisons"""
    st.markdown("### 📊 Weekly Comparison")
    
    metric = st.selectbox(
        "Select metric:",
        ["total_tasks_completed", "hours_spent", "days_active", "average_daily_minutes"],
        format_func=lambda x: {
            "total_tasks_completed": "Total Tasks",
            "hours_spent": "Hours Spent", 
            "days_active": "Days Active",
            "average_daily_minutes": "Avg Daily Minutes"
        }[x],
        key="bar_metric"
    )
    
    if show_all:
        # Group by provider
        fig = px.bar(
            df,
            x='week_period',
            y=metric,
            color='provider_name',
            title=f"Weekly {metric.replace('_', ' ').title()}",
            labels={'week_period': 'Week', metric: metric.replace('_', ' ').title()},
            hover_data=['provider_name', 'payment_status']
        )
    else:
        # Single provider
        fig = px.bar(
            df,
            x='week_period',
            y=metric,
            title=f"Weekly {metric.replace('_', ' ').title()}",
            labels={'week_period': 'Week', metric: metric.replace('_', ' ').title()},
            color=metric,
            color_continuous_scale='viridis'
        )
    
    fig.update_layout(height=500, showlegend=show_all)
    st.plotly_chart(fig, use_container_width=True)

def create_scatter_chart(df, show_all):
    """Create scatter plot showing relationship between tasks and time"""
    st.markdown("### 🔍 Tasks vs Time Analysis")
    
    if show_all:
        fig = px.scatter(
            df,
            x='total_tasks_completed',
            y='hours_spent',
            color='provider_name',
            size='days_active',
            hover_data=['week_period', 'payment_status'],
            title="Tasks vs Hours (bubble size = days active)",
            labels={'total_tasks_completed': 'Tasks Completed', 'hours_spent': 'Hours Spent'}
        )
    else:
        fig = px.scatter(
            df,
            x='total_tasks_completed',
            y='hours_spent',
            color='week_period',
            size='days_active',
            title="Tasks vs Hours Over Time",
            labels={'total_tasks_completed': 'Tasks Completed', 'hours_spent': 'Hours Spent'}
        )
    
    # Add trendline
    fig.add_trace(go.Scatter(
        x=df['total_tasks_completed'],
        y=df['hours_spent'],
        mode='lines',
        name='Trend',
        line=dict(dash='dash', color='red')
    ))
    
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

def create_area_chart(df, show_all):
    """Create area chart showing cumulative performance"""
    st.markdown("### 📈 Cumulative Performance")
    
    # Calculate cumulative metrics
    if show_all:
        df_cum = df.groupby(['provider_name', 'week_start_date']).agg({
            'total_tasks_completed': 'sum',
            'hours_spent': 'sum'
        }).groupby('provider_name').cumsum().reset_index()
        df_cum = df_cum.merge(df[['provider_name', 'week_start_date']], on=['provider_name', 'week_start_date'])
        
        fig = px.area(
            df_cum,
            x='week_start_date',
            y='total_tasks_completed',
            color='provider_name',
            title="Cumulative Tasks Completed",
            labels={'week_start_date': 'Week', 'total_tasks_completed': 'Cumulative Tasks'}
        )
    else:
        df['cumulative_tasks'] = df['total_tasks_completed'].cumsum()
        df['cumulative_hours'] = df['hours_spent'].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['week_start_date'],
            y=df['cumulative_tasks'],
            fill='tonexty',
            name='Cumulative Tasks',
            line_color='rgba(31, 119, 180, 0.8)'
        ))
        
        fig.update_layout(
            title="Cumulative Performance",
            xaxis_title="Week",
            yaxis_title="Cumulative Tasks",
            height=500
        )
    
    st.plotly_chart(fig, use_container_width=True)

def create_multi_metric_dashboard(df, show_all):
    """Create dashboard with multiple small charts"""
    st.markdown("### 📊 Multi-Metric Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Tasks over time
        fig_tasks = px.line(
            df,
            x='week_start_date',
            y='total_tasks_completed',
            color='provider_name' if show_all else None,
            title="Tasks Completed"
        )
        fig_tasks.update_layout(height=300)
        st.plotly_chart(fig_tasks, use_container_width=True)
        
        # Days active distribution
        fig_days = px.histogram(
            df,
            x='days_active',
            color='provider_name' if show_all else None,
            title="Days Active Distribution",
            nbins=7
        )
        fig_days.update_layout(height=300)
        st.plotly_chart(fig_days, use_container_width=True)
    
    with col2:
        # Hours over time
        fig_hours = px.line(
            df,
            x='week_start_date',
            y='hours_spent',
            color='provider_name' if show_all else None,
            title="Hours Spent"
        )
        fig_hours.update_layout(height=300)
        st.plotly_chart(fig_hours, use_container_width=True)
        
        # Payment status
        payment_summary = df.groupby('payment_status').size().reset_index(name='count')
        fig_payment = px.pie(
            payment_summary,
            values='count',
            names='payment_status',
            title="Payment Status"
        )
        fig_payment.update_layout(height=300)
        st.plotly_chart(fig_payment, use_container_width=True)

def create_heatmap_chart(df, show_all):
    """Create heatmap showing weekly activity patterns"""
    st.markdown("### 🔥 Weekly Activity Heatmap")
    
    if show_all:
        # Pivot data for heatmap
        heatmap_data = df.pivot_table(
            values='total_tasks_completed',
            index='provider_name',
            columns='week_period',
            fill_value=0
        )
        
        fig = px.imshow(
            heatmap_data,
            title="Tasks Completed by Provider and Week",
            labels={'x': 'Week', 'y': 'Provider', 'color': 'Tasks'},
            aspect='auto'
        )
    else:
        # For single provider, show days active vs week
        heatmap_data = df.pivot_table(
            values='days_active',
            index=['week_period'],
            columns=['payment_status'],
            fill_value=0
        )
        
        fig = px.imshow(
            heatmap_data.T,
            title="Days Active by Week and Payment Status",
            labels={'x': 'Week', 'y': 'Payment Status', 'color': 'Days Active'},
            aspect='auto'
        )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

def display_summary_metrics(df, show_all):
    """Display summary metrics below charts"""
    st.markdown("### 📋 Summary Metrics")
    
    if show_all:
        # Multi-provider summary
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Providers", df['provider_name'].nunique())
        col2.metric("Total Tasks", f"{df['total_tasks_completed'].sum():.0f}")
        col3.metric("Total Hours", f"{df['hours_spent'].sum():.1f}")
        col4.metric("Avg Tasks/Week", f"{df['total_tasks_completed'].mean():.1f}")
        
        # Provider breakdown
        st.markdown("#### Provider Breakdown")
        provider_summary = df.groupby('provider_name').agg({
            'total_tasks_completed': 'sum',
            'hours_spent': 'sum',
            'days_active': 'mean',
            'week_period': 'count'
        }).round(1)
        provider_summary.columns = ['Total Tasks', 'Total Hours', 'Avg Days Active', 'Weeks Recorded']
        st.dataframe(provider_summary, use_container_width=True)
    else:
        # Single provider summary
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Tasks", f"{df['total_tasks_completed'].sum():.0f}")
        col2.metric("Total Hours", f"{df['hours_spent'].sum():.1f}")
        col3.metric("Avg Tasks/Week", f"{df['total_tasks_completed'].mean():.1f}")
        col4.metric("Avg Hours/Week", f"{df['hours_spent'].mean():.1f}")
        
        # Weekly trend
        if len(df) > 1:
            latest_tasks = df.iloc[-1]['total_tasks_completed']
            previous_tasks = df.iloc[-2]['total_tasks_completed']
            task_change = ((latest_tasks - previous_tasks) / previous_tasks * 100) if previous_tasks > 0 else 0
            
            st.metric(
                "Week-over-Week Task Change",
                f"{task_change:+.1f}%",
                delta=f"{latest_tasks - previous_tasks:+.0f} tasks"
            )