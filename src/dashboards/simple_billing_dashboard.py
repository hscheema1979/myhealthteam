"""
Simple Billing Dashboard
Shows provider/coordinator billing data with export functionality
Patient ID, Provider ID, Service Type, Minutes, Billing Code, Billing Status
"""

import calendar
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st


# Database connection
def get_db_connection():
    return sqlite3.connect("production.db")


def get_available_months():
    """Get list of available months from provider_tasks_YYYY_MM tables"""
    conn = get_db_connection()
    try:
        query = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'provider_tasks_20%'
        ORDER BY name DESC
        """
        tables = conn.execute(query).fetchall()

        months = []
        for table in tables:
            table_name = table[0]
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


def get_provider_billing_data(year, month):
    """Get provider billing data with all required columns"""
    conn = get_db_connection()
    try:
        table_name = f"provider_tasks_{year}_{month:02d}"

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

        query = f"""
        SELECT
            provider_id,
            provider_name,
            patient_id,
            patient_name,
            task_date,
            task_description as service_type,
            minutes_of_service as minutes,
            billing_code,
            CASE WHEN billing_code IS NULL OR billing_code = '' THEN 'Pending'
                 ELSE 'Assigned' END as billing_status,
            notes
        FROM {table_name}
        WHERE provider_name IS NOT NULL
        ORDER BY provider_name, task_date DESC
        """

        df = pd.read_sql_query(query, conn)
        return df

    except Exception as e:
        st.error(f"Error getting provider billing data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_provider_summary(year, month):
    """Get summary statistics for the month"""
    conn = get_db_connection()
    try:
        table_name = f"provider_tasks_{year}_{month:02d}"

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name = ?
        """,
            (table_name,),
        )

        if not cursor.fetchone():
            return None

        query = f"""
        SELECT
            COUNT(DISTINCT provider_id) as total_providers,
            COUNT(DISTINCT patient_id) as total_patients,
            COUNT(*) as total_tasks,
            SUM(minutes_of_service) as total_minutes,
            COUNT(CASE WHEN billing_code IS NOT NULL AND billing_code != '' THEN 1 END) as tasks_with_billing_code,
            COUNT(CASE WHEN billing_code IS NULL OR billing_code = '' THEN 1 END) as tasks_without_billing_code
        FROM {table_name}
        """

        result = conn.execute(query).fetchone()
        return {
            "total_providers": result[0],
            "total_patients": result[1],
            "total_tasks": result[2],
            "total_minutes": result[3],
            "tasks_with_billing_code": result[4],
            "tasks_without_billing_code": result[5],
        }
    finally:
        conn.close()


def export_to_csv(df, filename):
    """Export dataframe to CSV"""
    return df.to_csv(index=False).encode("utf-8")


def display_simple_billing_dashboard():
    """Main billing dashboard"""
    st.title("Provider Billing Dashboard")
    st.markdown(
        "Track provider billing with patient, service type, minutes, and billing code information"
    )

    # Get available months
    months = get_available_months()

    if not months:
        st.warning("No provider billing data available")
        return

    # Month selector
    col1, col2 = st.columns(2)

    with col1:
        selected_month = st.selectbox(
            "Select Month", options=months, format_func=lambda x: x["display"]
        )

    if selected_month:
        year = selected_month["year"]
        month = selected_month["month"]

        with col2:
            st.metric("Selected Period", f"{calendar.month_name[month]} {year}")

        # Get summary data
        summary = get_provider_summary(year, month)

        if summary:
            # Display summary metrics
            st.subheader("Monthly Summary")
            col1, col2, col3, col4, col5, col6 = st.columns(6)

            with col1:
                st.metric("Providers", summary["total_providers"])
            with col2:
                st.metric("Patients", summary["total_patients"])
            with col3:
                st.metric("Total Tasks", summary["total_tasks"])
            with col4:
                st.metric("Total Minutes", f"{summary['total_minutes']:,.0f}")
            with col5:
                st.metric("Coded Tasks", summary["tasks_with_billing_code"])
            with col6:
                st.metric("Pending Code", summary["tasks_without_billing_code"])

        # Get detailed data
        billing_df = get_provider_billing_data(year, month)

        if not billing_df.empty:
            st.subheader("Billing Data")

            # Filters
            col1, col2, col3 = st.columns(3)

            with col1:
                providers = ["All"] + sorted(
                    billing_df["provider_name"].unique().tolist()
                )
                selected_provider = st.selectbox("Filter by Provider", providers)

            with col2:
                statuses = ["All"] + sorted(
                    billing_df["billing_status"].unique().tolist()
                )
                selected_status = st.selectbox("Filter by Status", statuses)

            with col3:
                show_only_pending = st.checkbox("Show Only Pending Codes", value=False)

            # Apply filters
            filtered_df = billing_df.copy()

            if selected_provider != "All":
                filtered_df = filtered_df[
                    filtered_df["provider_name"] == selected_provider
                ]

            if selected_status != "All":
                filtered_df = filtered_df[
                    filtered_df["billing_status"] == selected_status
                ]

            if show_only_pending:
                filtered_df = filtered_df[
                    (filtered_df["billing_code"].isna())
                    | (filtered_df["billing_code"] == "")
                ]

            # Display table
            st.dataframe(
                filtered_df[
                    [
                        "provider_id",
                        "provider_name",
                        "patient_id",
                        "patient_name",
                        "task_date",
                        "service_type",
                        "minutes",
                        "billing_code",
                        "billing_status",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

            # Export buttons
            st.subheader("Export Options")
            col1, col2, col3 = st.columns(3)

            with col1:
                # Export filtered data to CSV
                csv_data = export_to_csv(
                    filtered_df, f"provider_billing_{year}_{month:02d}"
                )
                st.download_button(
                    label="Download Filtered Data (CSV)",
                    data=csv_data,
                    file_name=f"provider_billing_{year}_{month:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )

            with col2:
                # Export all data for month to CSV
                csv_all = export_to_csv(
                    billing_df, f"provider_billing_all_{year}_{month:02d}"
                )
                st.download_button(
                    label="Download All Data (CSV)",
                    data=csv_all,
                    file_name=f"provider_billing_all_{year}_{month:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )

            with col3:
                # Export only pending codes
                pending_df = billing_df[
                    (billing_df["billing_code"].isna())
                    | (billing_df["billing_code"] == "")
                ]
                csv_pending = export_to_csv(
                    pending_df, f"provider_billing_pending_{year}_{month:02d}"
                )
                st.download_button(
                    label="Download Pending Codes (CSV)",
                    data=csv_pending,
                    file_name=f"provider_billing_pending_{year}_{month:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
        else:
            st.info("No billing data available for selected period")


if __name__ == "__main__":
    display_simple_billing_dashboard()
