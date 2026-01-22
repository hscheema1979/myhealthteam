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

        # Get months from CSV coordinator task tables (for per-patient billing)
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'csv_coordinator_tasks_20%'
            ORDER BY name DESC
        """)
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            parts = table_name.split("_")
            if len(parts) >= 4:
                try:
                    year = int(parts[3])
                    month = int(parts[4])
                    month_name = calendar.month_name[month]

                    months.append({
                        "year": year,
                        "month": month,
                        "display": f"{month_name} {year} (CSV Import)",
                        "data_type": "CSV_IMPORT",
                        "view": f"coordinator_billing_{year}_{month:02d}"
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
                    "view": "coordinator_tasks_2026_01"
                })

        return sorted(months, key=lambda x: (x["year"], x["month"]), reverse=True)
    except Exception as e:
        st.error(f"Error getting available months: {e}")
        return []
    finally:
        conn.close()


def get_coordinator_billing_data(selected_month):
    """Get per-patient billing data (billing is by patient, not coordinator)"""
    conn = get_db_connection()
    try:
        data_type = selected_month.get("data_type", "")
        view_name = selected_month.get("view", "")
        year = selected_month["year"]
        month = selected_month["month"]

        if data_type == "CSV_IMPORT":
            # Query per-patient billing view from CSV data
            query = f"""
                SELECT
                    cb.patient_id,
                    (p.first_name || ' ' || p.last_name) as patient_name,
                    p.facility,
                    cb.total_minutes
                FROM {view_name} cb
                LEFT JOIN patients p ON cb.patient_id = p.patient_id
                ORDER BY cb.total_minutes DESC
            """
            df = pd.read_sql_query(query, conn)

        elif data_type == "LIVE":
            # Query live operational table - per-patient aggregation
            query = """
                SELECT
                    ct.patient_id,
                    (p.first_name || ' ' || p.last_name) as patient_name,
                    p.facility,
                    SUM(ct.duration_minutes) as total_minutes
                FROM coordinator_tasks_2026_01 ct
                LEFT JOIN patients p ON ct.patient_id = p.patient_id
                WHERE ct.duration_minutes IS NOT NULL
                GROUP BY ct.patient_id, p.first_name, p.last_name, p.facility
                ORDER BY total_minutes DESC
            """
            df = pd.read_sql_query(query, conn)
        else:
            df = pd.DataFrame()

        conn.close()
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
        view_name = selected_month.get("view", "")
        year = selected_month["year"]
        month = selected_month["month"]

        if data_type == "CSV_IMPORT":
            query = f"""
                SELECT
                    COUNT(*) as total_patients,
                    SUM(total_minutes) as total_minutes
                FROM {view_name}
            """

        elif data_type == "LIVE":
            query = """
                SELECT
                    COUNT(DISTINCT patient_id) as total_patients,
                    SUM(duration_minutes) as total_minutes
                FROM coordinator_tasks_2026_01
                WHERE coordinator_id IS NOT NULL
            """

        else:
            return None

        result = conn.execute(query).fetchone()
        if result and result[0]:
            return {
                "total_patients": result[0] or 0,
                "total_minutes": result[1] or 0,
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
                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Total Minutes", f"{summary['total_minutes']:,}")
                with col2:
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
