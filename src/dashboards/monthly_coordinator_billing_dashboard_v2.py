"""
Monthly Coordinator Billing Dashboard - Updated
Handles both CSV summaries (pre-2026) and live operational data (2026+)
"""

import calendar
import sqlite3
from datetime import datetime
import zipfile
import io

import pandas as pd
import streamlit as st


def get_db_connection():
    return sqlite3.connect("production.db")


def get_available_months():
    """Get list of available months from CSV summaries and operational tables"""
    conn = get_db_connection()
    try:
        months = []

        # Get months from CSV monthly billing summaries
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'csv_monthly_billing_summary_%'
            ORDER BY name DESC
        """)
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            parts = table_name.split("_")
            if len(parts) >= 5:
                try:
                    year = int(parts[4])
                    month = int(parts[5])
                    month_name = calendar.month_name[month]

                    # For January 2026, show as CSV Import
                    if year == 2026 and month == 1:
                        display_name = f"{month_name} {year} (CSV Import)"
                        data_type = "CSV_IMPORT"
                        view_name = "coordinator_monthly_2026_01_import"
                    elif year >= 2026:
                        display_name = f"{month_name} {year} (CSV)"
                        data_type = "CSV"
                        view_name = f"csv_monthly_billing_summary_{year}_{month:02d}"
                    else:
                        display_name = f"{month_name} {year}"
                        data_type = "CSV"
                        view_name = f"csv_monthly_billing_summary_{year}_{month:02d}"

                    months.append({
                        "year": year,
                        "month": month,
                        "display": display_name,
                        "data_type": data_type,
                        "view": view_name
                    })
                except (ValueError, IndexError):
                    continue

        # Check for 2026 live operational data
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name = 'coordinator_tasks_2026_01'
        """)
        if cursor.fetchone():
            # Count records to see if there's live data
            count = conn.execute("SELECT COUNT(*) FROM coordinator_tasks_2026_01 WHERE coordinator_id IS NOT NULL").fetchone()[0]
            if count > 0:
                months.append({
                    "year": 2026,
                    "month": 1,
                    "display": "January 2026 (Live)",
                    "data_type": "LIVE",
                    "view": "coordinator_monthly_2026_01"
                })
                # Combined option
                months.append({
                    "year": 2026,
                    "month": 1,
                    "display": "January 2026 (Combined)",
                    "data_type": "COMBINED",
                    "view": "coordinator_monthly_2026_01_combined"
                })

        return sorted(months, key=lambda x: (x["year"], x["month"]), reverse=True)
    except Exception as e:
        st.error(f"Error getting available months: {e}")
        return []
    finally:
        conn.close()


def get_coordinator_billing_data(selected_month):
    """Get coordinator billing data based on selected month"""
    conn = get_db_connection()
    try:
        data_type = selected_month.get("data_type", "")
        view_name = selected_month.get("view", "")
        year = selected_month["year"]
        month = selected_month["month"]

        if data_type == "CSV" or data_type == "CSV_IMPORT":
            # Query CSV monthly billing summary
            table_name = f"csv_monthly_billing_summary_{year}_{month:02d}"

            query = f"""
                SELECT
                    staff_id as coordinator_id,
                    staff_name as coordinator_name,
                    task_type,
                    SUM(total_tasks) as total_tasks,
                    SUM(total_minutes) as total_minutes,
                    ROUND(SUM(total_minutes) / 60.0, 2) as total_hours,
                    SUM(unique_patients) as unique_patients
                FROM {table_name}
                WHERE staff_type = 'coordinator'
                GROUP BY staff_id, staff_name, task_type
                ORDER BY total_minutes DESC
            """
            df = pd.read_sql_query(query, conn)

        elif data_type == "LIVE":
            # Query live operational table
            query = """
                SELECT
                    c.coordinator_id,
                    u.full_name as coordinator_name,
                    c.task_type,
                    COUNT(*) as total_tasks,
                    SUM(c.duration_minutes) as total_minutes,
                    ROUND(SUM(c.duration_minutes) / 60.0, 2) as total_hours,
                    COUNT(DISTINCT c.patient_id) as unique_patients
                FROM coordinator_tasks_2026_01 c
                LEFT JOIN users u ON CAST(c.coordinator_id AS TEXT) = CAST(u.user_id AS TEXT)
                WHERE c.coordinator_id IS NOT NULL
                GROUP BY c.coordinator_id, u.full_name, c.task_type
                ORDER BY total_minutes DESC
            """
            df = pd.read_sql_query(query, conn)

        elif data_type == "COMBINED":
            # Query the combined view
            query = """
                SELECT
                    coordinator_id,
                    coordinator_name,
                    task_type,
                    SUM(total_tasks) as total_tasks,
                    SUM(total_minutes) as total_minutes,
                    ROUND(SUM(total_minutes) / 60.0, 2) as total_hours,
                    SUM(unique_patients) as unique_patients,
                    data_source
                FROM coordinator_monthly_2026_01_combined
                GROUP BY coordinator_id, coordinator_name, task_type, data_source
                ORDER BY total_minutes DESC
            """
            df = pd.read_sql_query(query, conn)

        else:
            return pd.DataFrame()

        return df

    except Exception as e:
        st.error(f"Error getting coordinator billing data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_coordinator_summary(selected_month):
    """Get summary statistics for selected month"""
    conn = get_db_connection()
    try:
        data_type = selected_month.get("data_type", "")
        year = selected_month["year"]
        month = selected_month["month"]

        if data_type == "CSV" or data_type == "CSV_IMPORT":
            table_name = f"csv_monthly_billing_summary_{year}_{month:02d}"
            query = f"""
                SELECT
                    SUM(total_tasks) as total_tasks,
                    SUM(total_minutes) as total_minutes,
                    SUM(unique_patients) as total_patients
                FROM {table_name}
                WHERE staff_type = 'coordinator'
            """

        elif data_type == "LIVE":
            query = """
                SELECT
                    COUNT(*) as total_tasks,
                    SUM(duration_minutes) as total_minutes,
                    COUNT(DISTINCT patient_id) as total_patients
                FROM coordinator_tasks_2026_01
                WHERE coordinator_id IS NOT NULL
            """

        elif data_type == "COMBINED":
            query = """
                SELECT
                    SUM(total_tasks) as total_tasks,
                    SUM(total_minutes) as total_minutes,
                    SUM(unique_patients) as total_patients
                FROM coordinator_monthly_2026_01_combined
            """

        result = conn.execute(query).fetchone()
        if result and result[0]:
            return {
                "total_tasks": result[0] or 0,
                "total_minutes": result[1] or 0,
                "total_patients": result[2] or 0,
            }
        return None

    except Exception as e:
        st.error(f"Error getting summary: {e}")
        return None
    finally:
        conn.close()


def export_to_csv(df, filename):
    """Export dataframe to CSV"""
    return df.to_csv(index=False).encode("utf-8")


def display_monthly_coordinator_billing_dashboard():
    """Main billing dashboard v2 - handles CSV summaries and live data"""
    months = get_available_months()

    if not months:
        st.warning("No coordinator billing data available")
        return

    tab1, tab2 = st.tabs(["Single Month View", "Bulk Download"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            selected_month = st.selectbox(
                "Select Month", options=months, format_func=lambda x: x["display"], key="csv_month_select"
            )

        if selected_month:
            year = selected_month["year"]
            month = selected_month["month"]
            data_type = selected_month.get("data_type", "")

            with col2:
                st.metric("Selected Period", selected_month["display"])
                if data_type:
                    st.caption(f"Data Source: {data_type}")

            # Get summary data
            summary = get_coordinator_summary(selected_month)

            if summary:
                st.subheader("Monthly Summary")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Tasks", summary["total_tasks"])
                with col2:
                    st.metric("Total Minutes", f"{summary['total_minutes']:,}")
                with col3:
                    st.metric("Total Patients", summary["total_patients"])

            # Get detailed billing data
            df = get_coordinator_billing_data(selected_month)

            if not df.empty:
                st.subheader("Coordinator Billing Breakdown")

                if data_type == "COMBINED":
                    # Add data source filter for combined view
                    sources = df["data_source"].unique().tolist()
                    if len(sources) > 1:
                        selected_sources = st.multiselect(
                            "Filter by Data Source",
                            options=sources,
                            default=sources,
                            key="combined_source_filter"
                        )
                        if selected_sources:
                            df = df[df["data_source"].isin(selected_sources)]

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                # Export option
                csv_data = export_to_csv(df, f"coordinator_billing_{year}_{month:02d}.csv")
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"coordinator_billing_{year}_{month:02d}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No data available for selected period")

    with tab2:
        st.subheader("Bulk Download")
        st.info("Select months to download and export as a single ZIP file")

        # Multi-select for months
        selected_months = st.multiselect(
            "Select Months to Download",
            options=months,
            format_func=lambda x: x["display"],
            key="bulk_month_select"
        )

        if selected_months and st.button("Generate ZIP", key="generate_zip"):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for month in selected_months:
                    df = get_coordinator_billing_data(month)
                    if not df.empty:
                        filename = f"coordinator_billing_{month['year']}_{month['month']:02d}.csv"
                        zip_file.writestr(filename, df.to_csv(index=False).encode('utf-8'))

            zip_buffer.seek(0)
            st.download_button(
                label="Download ZIP Archive",
                data=zip_buffer.getvalue(),
                file_name=f"coordinator_billing_bulk_{datetime.now().strftime('%Y%m%d')}.zip",
                mime="application/zip"
            )


if __name__ == "__main__":
    display_monthly_coordinator_billing_dashboard()
