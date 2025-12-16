"""
Weekly Provider Payroll Dashboard
Tracks provider payroll by week/month with task counts by visit type and payment status
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


def get_provider_payroll_summary(year, month, week_key=None):
    """Get provider payroll summary with task counts by visit type"""
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

        # Query the provider tasks table grouped by provider
        query = f"""
        SELECT
            provider_name,
            COUNT(*) as total_tasks,
            SUM(minutes_of_service) as total_minutes,
            COUNT(DISTINCT task_description) as visit_types
        FROM {table_name}
        {where_clause}
        AND provider_name IS NOT NULL
        GROUP BY provider_name
        ORDER BY provider_name
        """

        df = pd.read_sql_query(query, conn, params=params)
        return df

    except Exception as e:
        st.error(f"Error getting payroll summary: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_provider_tasks_by_visit_type(year, month, provider_name, week_key=None):
    """Get task counts by visit type for a specific provider"""
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
            task_description,
            COUNT(*) as task_count,
            SUM(minutes_of_service) as total_minutes,
            COUNT(DISTINCT task_date) as days_worked,
            ROUND(AVG(minutes_of_service), 1) as avg_minutes_per_task
        FROM {table_name}
        {where_clause}
        GROUP BY task_description
        ORDER BY task_count DESC
        """

        df = pd.read_sql_query(query, conn, params=params)
        return df

    except Exception as e:
        st.error(f"Error getting visit type details: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_provider_payment_status(provider_name, year, month, week_key=None):
    """Get payment status for a provider from provider_weekly_summary_with_billing table"""
    conn = get_db_connection()
    try:
        # Build WHERE clause
        where_clause = """
        WHERE provider_name = ?
        AND year = ?
        AND month = ?
        """
        params = [provider_name, year, month]

        if week_key:
            where_clause += " AND week_number = ?"
            # Extract week number from week_key (format: YYYY-WW)
            week_num = int(week_key.split("-")[1])
            params.append(week_num)

        query = f"""
        SELECT
            summary_id,
            provider_id,
            provider_name,
            week_start_date,
            week_end_date,
            total_tasks_completed,
            total_time_spent_minutes,
            paid
        FROM provider_weekly_summary_with_billing
        {where_clause}
        ORDER BY week_number DESC
        LIMIT 1
        """

        result = conn.execute(query, params).fetchone()
        conn.close()

        if result:
            return {
                "summary_id": result[0],
                "provider_id": result[1],
                "provider_name": result[2],
                "week_start": result[3],
                "week_end": result[4],
                "total_tasks": result[5],
                "total_minutes": result[6],
                "paid": bool(result[7]),
            }
        return None

    except Exception as e:
        st.error(f"Error getting payment status: {e}")
        return None
    finally:
        conn.close()


def update_provider_paid_status(summary_id, paid_status):
    """Update provider paid status in provider_weekly_summary_with_billing table"""
    conn = get_db_connection()
    try:
        query = """
        UPDATE provider_weekly_summary_with_billing
        SET paid = ?,
            updated_date = CURRENT_TIMESTAMP
        WHERE summary_id = ?
        """

        conn.execute(query, (1 if paid_status else 0, summary_id))
        conn.commit()
        conn.close()

        return True, "Payment status updated successfully"

    except Exception as e:
        conn.close()
        return False, f"Error updating payment status: {str(e)}"


def create_visit_type_chart(df, provider_name):
    """Create chart showing tasks by visit type"""
    if df.empty:
        return None

    fig = px.bar(
        df,
        x="task_description",
        y="task_count",
        title=f"Tasks by Visit Type - {provider_name}",
        labels={"task_description": "Visit Type", "task_count": "Number of Tasks"},
        color="task_count",
        color_continuous_scale="Viridis",
    )

    fig.update_layout(height=400, title_x=0.5, xaxis_tickangle=-45)

    return fig


def create_minutes_chart(df, provider_name):
    """Create chart showing minutes by visit type"""
    if df.empty:
        return None

    fig = px.bar(
        df,
        x="task_description",
        y="total_minutes",
        title=f"Minutes by Visit Type - {provider_name}",
        labels={"task_description": "Visit Type", "total_minutes": "Total Minutes"},
        color="total_minutes",
        color_continuous_scale="Blues",
    )

    fig.update_layout(height=400, title_x=0.5, xaxis_tickangle=-45)

    return fig


def display_weekly_provider_payroll_dashboard():
    """Main function to display the weekly provider payroll dashboard"""
    st.title("Weekly Provider Payroll Dashboard")
    st.markdown("Track provider tasks by visit type and manage payment status")

    # Get available months
    months = get_available_months()

    if not months:
        st.warning("No provider data available")
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
            f"Payroll for {selected_month['display']}"
            + (f" - {selected_week['display']}" if week_key else "")
        )

        # Get summary data
        summary_df = get_provider_payroll_summary(year, month, week_key)

        if summary_df.empty:
            st.info(f"No data available for selected period")
            return

        # Display summary metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Providers", len(summary_df))

        with col2:
            total_minutes = summary_df["total_minutes"].sum()
            st.metric("Total Minutes", f"{total_minutes:,}")

        with col3:
            total_tasks = summary_df["total_tasks"].sum()
            st.metric("Total Tasks", total_tasks)

        # Create tabs for different views
        tab1, tab2 = st.tabs(["Provider Payroll", "Provider Details"])

        with tab1:
            st.subheader("Provider Payroll Summary")

            # Display payroll table with payment checkboxes
            payroll_data = []

            for idx, row in summary_df.iterrows():
                provider_name = row["provider_name"]

                # Get payment status
                payment_info = get_provider_payment_status(
                    provider_name, year, month, week_key
                )

                payroll_data.append(
                    {
                        "Provider": provider_name,
                        "Tasks": row["total_tasks"],
                        "Minutes": f"{row['total_minutes']:,}",
                        "Visit Types": row["visit_types"],
                        "Payment Status": "Paid"
                        if (payment_info and payment_info["paid"])
                        else "Unpaid",
                        "summary_id": payment_info["summary_id"]
                        if payment_info
                        else None,
                        "paid": payment_info["paid"] if payment_info else False,
                    }
                )

            payroll_df = pd.DataFrame(payroll_data)

            # Display table
            st.dataframe(
                payroll_df[
                    ["Provider", "Tasks", "Minutes", "Visit Types", "Payment Status"]
                ],
                use_container_width=True,
                hide_index=True,
            )

            # Payment processing section
            st.subheader("Mark Providers as Paid")

            # Multi-select providers to mark as paid
            providers_to_pay = st.multiselect(
                "Select providers to mark as paid:",
                options=summary_df["provider_name"].tolist(),
            )

            if providers_to_pay:
                if st.button("Submit Payment for Selected Providers", type="primary"):
                    success_count = 0
                    error_count = 0

                    for provider_name in providers_to_pay:
                        payment_info = get_provider_payment_status(
                            provider_name, year, month, week_key
                        )

                        if payment_info:
                            success, message = update_provider_paid_status(
                                payment_info["summary_id"], True
                            )
                            if success:
                                success_count += 1
                            else:
                                error_count += 1

                    if success_count > 0:
                        st.success(
                            f"Successfully marked {success_count} provider(s) as paid"
                        )
                    if error_count > 0:
                        st.error(f"Failed to update {error_count} provider(s)")

                    st.rerun()

        with tab2:
            st.subheader("Provider Details - Tasks by Visit Type")

            # Provider selector
            provider_names = summary_df["provider_name"].tolist()
            selected_provider = st.selectbox("Select Provider", options=provider_names)

            if selected_provider:
                # Get visit type details
                visit_types_df = get_provider_tasks_by_visit_type(
                    year, month, selected_provider, week_key
                )

                if not visit_types_df.empty:
                    st.subheader(f"Tasks by Visit Type - {selected_provider}")

                    # Display summary metrics
                    col1, col2, col3 = st.columns(3)

                    total_tasks = visit_types_df["task_count"].sum()
                    total_minutes = visit_types_df["total_minutes"].sum()

                    with col1:
                        st.metric("Total Tasks", total_tasks)

                    with col2:
                        st.metric("Total Minutes", f"{total_minutes:,}")

                    with col3:
                        avg_min_per_task = (
                            total_minutes / total_tasks if total_tasks > 0 else 0
                        )
                        st.metric("Avg Minutes/Task", f"{avg_min_per_task:.1f}")

                    # Display visit type table
                    st.dataframe(
                        visit_types_df.style.format(
                            {"total_minutes": "{:,}", "avg_minutes_per_task": "{:.1f}"}
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )

                    # Charts
                    col1, col2 = st.columns(2)

                    with col1:
                        visit_chart = create_visit_type_chart(
                            visit_types_df, selected_provider
                        )
                        if visit_chart:
                            st.plotly_chart(visit_chart, use_container_width=True)

                    with col2:
                        minutes_chart = create_minutes_chart(
                            visit_types_df, selected_provider
                        )
                        if minutes_chart:
                            st.plotly_chart(minutes_chart, use_container_width=True)

                    # Payment status for this provider
                    payment_info = get_provider_payment_status(
                        selected_provider, year, month, week_key
                    )

                    if payment_info:
                        st.subheader(f"Payment Status - {selected_provider}")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "Week",
                                f"{payment_info['week_start']} to {payment_info['week_end']}",
                            )

                        with col2:
                            status = "Paid" if payment_info["paid"] else "Unpaid"
                            st.metric("Payment Status", status)

                        with col3:
                            paid_text = (
                                "Paid" if payment_info["paid"] else "Mark as Paid"
                            )
                            if st.button(
                                paid_text,
                                key=f"pay_{selected_provider}",
                                type="primary"
                                if not payment_info["paid"]
                                else "secondary",
                            ):
                                success, message = update_provider_paid_status(
                                    payment_info["summary_id"], True
                                )
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.info(f"No visit type data found for {selected_provider}")


# Main execution
if __name__ == "__main__":
    display_weekly_provider_payroll_dashboard()
