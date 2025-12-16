"""
Weekly Provider Billing Dashboard
Tracks provider billing by week, similar to the Monthly Coordinator Billing Dashboard
"""

import calendar
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# Database connection
def get_db_connection():
    return sqlite3.connect("production.db")


def get_available_months():
    """Get list of available months from provider_tasks_YYYY_MM tables"""
    conn = get_db_connection()
    try:
        # Get list of all provider_tasks tables
        query = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'provider_tasks_20%'
        ORDER BY name DESC
        """
        tables = conn.execute(query).fetchall()

        months = []
        for table in tables:
            table_name = table[0]
            # Extract year and month from table name (provider_tasks_YYYY_MM)
            parts = table_name.split("_")
            if len(parts) >= 3:
                try:
                    year = int(parts[2])
                    month = int(parts[3])
                    month_name = calendar.month_name[month]
                    months.append(
                        {
                            "year": year,
                            "month": month,
                            "display": f"{month_name} {year}",
                        }
                    )
                except (ValueError, IndexError):
                    continue

        return sorted(months, key=lambda x: (x["year"], x["month"]), reverse=True)
    except Exception as e:
        st.error(f"Error getting available months: {e}")
        return []
    finally:
        conn.close()


def get_weeks_for_month(year, month):
    """Get available weeks for a specific month"""
    conn = get_db_connection()
    try:
        table_name = f"provider_tasks_{year}_{month:02d}"

        # Check if table exists
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name = ?
        """,
            (table_name,),
        )

        if not cursor.fetchone():
            return []

        # Get distinct weeks in this month
        query = f"""
        SELECT DISTINCT
            strftime('%Y-%W', task_date) as week_key,
            MIN(task_date) as week_start,
            MAX(task_date) as week_end
        FROM {table_name}
        WHERE strftime('%Y', task_date) = ?
            AND strftime('%m', task_date) = ?
            AND task_date IS NOT NULL
        GROUP BY strftime('%Y-%W', task_date)
        ORDER BY week_key DESC
        """

        weeks = []
        results = conn.execute(query, (str(year), f"{month:02d}")).fetchall()
        for week_key, week_start, week_end in results:
            weeks.append(
                {
                    "week_key": week_key,
                    "week_start": week_start,
                    "week_end": week_end,
                    "display": f"Week of {week_start} to {week_end}",
                }
            )

        return weeks

    except Exception as e:
        st.error(f"Error getting weeks: {e}")
        return []
    finally:
        conn.close()


def get_provider_weekly_summary(year, month, week_key=None):
    """Get provider weekly summary data"""
    conn = get_db_connection()
    try:
        table_name = f"provider_tasks_{year}_{month:02d}"

        # Check if table exists
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name = ?
        """,
            (table_name,),
        )

        if not cursor.fetchone():
            return pd.DataFrame()

        # Build WHERE clause based on whether a specific week is selected
        where_clause = (
            f"WHERE strftime('%Y', task_date) = ? AND strftime('%m', task_date) = ?"
        )
        params = [str(year), f"{month:02d}"]

        if week_key:
            where_clause += " AND strftime('%Y-%W', task_date) = ?"
            params.append(week_key)

        # Query the provider tasks table
        query = f"""
        SELECT
            provider_name,
            COUNT(*) as total_tasks,
            SUM(minutes_of_service) as total_minutes,
            COUNT(DISTINCT patient_id) as unique_patients
        FROM {table_name}
        {where_clause}
        AND provider_name IS NOT NULL
        GROUP BY provider_name
        ORDER BY total_minutes DESC
        """

        df = pd.read_sql_query(query, conn, params=params)
        return df

    except Exception as e:
        st.error(f"Error getting provider summary: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_provider_task_details(year, month, provider_name, week_key=None):
    """Get detailed task information for a specific provider"""
    conn = get_db_connection()
    try:
        table_name = f"provider_tasks_{year}_{month:02d}"

        # Check if table exists
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name = ?
        """,
            (table_name,),
        )

        if not cursor.fetchone():
            return pd.DataFrame()

        # Build WHERE clause
        where_clause = "WHERE provider_name = ? AND strftime('%Y', task_date) = ? AND strftime('%m', task_date) = ?"
        params = [provider_name, str(year), f"{month:02d}"]

        if week_key:
            where_clause += " AND strftime('%Y-%W', task_date) = ?"
            params.append(week_key)

        query = f"""
        SELECT
            task_date,
            patient_name,
            patient_id,
            task_description,
            minutes_of_service,
            billing_code,
            billing_code_description,
            status,
            notes
        FROM {table_name}
        {where_clause}
        ORDER BY task_date DESC
        """

        df = pd.read_sql_query(query, conn, params=params)
        return df

    except Exception as e:
        st.error(f"Error getting provider details: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def create_provider_minutes_chart(df):
    """Create minutes by provider chart"""
    if df.empty:
        return None

    fig = px.bar(
        df.head(10),
        x="provider_name",
        y="total_minutes",
        title="Top 10 Providers by Minutes",
        labels={"provider_name": "Provider", "total_minutes": "Total Minutes"},
        color="total_minutes",
        color_continuous_scale="Blues",
    )

    fig.update_layout(height=500, title_x=0.5, xaxis_tickangle=-45)

    return fig


def create_provider_tasks_chart(df):
    """Create task counts by provider chart"""
    if df.empty:
        return None

    fig = px.bar(
        df.head(10),
        x="provider_name",
        y="total_tasks",
        title="Top 10 Providers by Task Count",
        labels={"provider_name": "Provider", "total_tasks": "Total Tasks"},
        color="total_tasks",
        color_continuous_scale="Greens",
    )

    fig.update_layout(height=500, title_x=0.5, xaxis_tickangle=-45)

    return fig


def display_weekly_provider_billing_dashboard():
    """Main function to display the weekly provider billing dashboard"""
    st.title("Weekly Provider Billing Dashboard")

    # Get available months
    months = get_available_months()

    if not months:
        st.warning("No provider billing data available")
        return

    # Month selector
    selected_month = st.selectbox(
        "Select Month", options=months, format_func=lambda x: x["display"]
    )

    if selected_month:
        year = selected_month["year"]
        month = selected_month["month"]

        # Get available weeks for this month
        weeks = get_weeks_for_month(year, month)

        if not weeks:
            st.info(f"No data available for {selected_month['display']}")
            return

        # Week selector
        week_options = [{"week_key": None, "display": "All Weeks"}] + weeks
        selected_week = st.selectbox(
            "Select Week", options=week_options, format_func=lambda x: x["display"]
        )

        week_key = selected_week["week_key"] if selected_week else None

        st.subheader(
            f"Billing Summary for {selected_month['display']}"
            + (f" - {selected_week['display']}" if week_key else "")
        )

        # Get summary data
        summary_df = get_provider_weekly_summary(year, month, week_key)

        if summary_df.empty:
            st.info(f"No data available for selected period")
            return

        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Providers", len(summary_df))

        with col2:
            total_minutes = summary_df["total_minutes"].sum()
            st.metric("Total Minutes", f"{total_minutes:,}")

        with col3:
            total_tasks = summary_df["total_tasks"].sum()
            st.metric("Total Tasks", total_tasks)

        with col4:
            avg_minutes_per_task = (
                (total_minutes / total_tasks) if total_tasks > 0 else 0
            )
            st.metric("Avg Minutes/Task", f"{avg_minutes_per_task:.1f}")

        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Summary", "Charts", "Details"])

        with tab1:
            st.subheader("Provider Summary")
            st.dataframe(
                summary_df.style.format(
                    {
                        "total_minutes": "{:,}",
                        "total_tasks": "{:,}",
                        "unique_patients": "{:,}",
                    }
                ),
                use_container_width=True,
            )

        with tab2:
            col1, col2 = st.columns(2)

            with col1:
                minutes_chart = create_provider_minutes_chart(summary_df)
                if minutes_chart:
                    st.plotly_chart(minutes_chart, use_container_width=True)

            with col2:
                tasks_chart = create_provider_tasks_chart(summary_df)
                if tasks_chart:
                    st.plotly_chart(tasks_chart, use_container_width=True)

        with tab3:
            st.subheader("Provider Details")

            # Provider selector
            provider_names = summary_df["provider_name"].tolist()
            selected_provider = st.selectbox("Select Provider", options=provider_names)

            if selected_provider:
                details_df = get_provider_task_details(
                    year, month, selected_provider, week_key
                )

                if not details_df.empty:
                    st.subheader(f"Tasks for {selected_provider}")
                    st.dataframe(details_df, use_container_width=True, hide_index=True)

                    # Display metrics for selected provider
                    prov_summary = summary_df[
                        summary_df["provider_name"] == selected_provider
                    ].iloc[0]

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Tasks", prov_summary["total_tasks"])
                    with col2:
                        st.metric("Total Minutes", f"{prov_summary['total_minutes']:,}")
                    with col3:
                        st.metric("Unique Patients", prov_summary["unique_patients"])
                    with col4:
                        avg_min = (
                            prov_summary["total_minutes"] / prov_summary["total_tasks"]
                            if prov_summary["total_tasks"] > 0
                            else 0
                        )
                        st.metric("Avg Min/Task", f"{avg_min:.1f}")
                else:
                    st.info(f"No detailed tasks found for {selected_provider}")


# Main execution
if __name__ == "__main__":
    display_weekly_provider_billing_dashboard()
