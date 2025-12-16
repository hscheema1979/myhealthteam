"""
Monthly Coordinator Billing Dashboard
Aggregates coordinator minutes by patient with billing code assignment
"""

import calendar
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st


def get_db_connection():
    return sqlite3.connect("production.db")


def get_available_months():
    """Get list of available months from coordinator_tasks_YYYY_MM tables"""
    conn = get_db_connection()
    try:
        query = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'coordinator_tasks_20%'
        ORDER BY name DESC
        """
        tables = conn.execute(query).fetchall()

        months = []
        for table in tables:
            table_name = table[0]
            parts = table_name.split("_")
            if len(parts) >= 4:
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


def get_billing_codes_for_minutes(minutes):
    """Determine billing code based on minutes of service"""
    if minutes is None or minutes == 0:
        return "PENDING", "Pending Billing Code Assignment"
    elif minutes <= 15:
        return "99211", "Office visit - established patient, minimal"
    elif minutes <= 30:
        return "99212", "Office visit - established patient, low"
    elif minutes <= 45:
        return "99213", "Office visit - established patient, moderate"
    elif minutes <= 60:
        return "99214", "Office visit - established patient, moderate-high"
    else:
        return "99215", "Office visit - established patient, high"


def get_coordinator_billing_data(year, month):
    """Get coordinator billing data aggregated by patient only"""
    conn = get_db_connection()
    try:
        table_name = f"coordinator_tasks_{year}_{month:02d}"

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
            patient_id,
            COUNT(*) as task_count,
            SUM(duration_minutes) as total_minutes
        FROM {table_name}
        WHERE patient_id IS NOT NULL
        GROUP BY patient_id
        ORDER BY total_minutes DESC
        """

        df = pd.read_sql_query(query, conn)

        # Apply billing codes based on minutes
        df["billing_code"] = df["total_minutes"].apply(
            lambda x: get_billing_codes_for_minutes(x)[0]
        )
        df["billing_description"] = df["total_minutes"].apply(
            lambda x: get_billing_codes_for_minutes(x)[1]
        )
        df["billing_status"] = "Pending"

        return df

    except Exception as e:
        st.error(f"Error getting coordinator billing data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_coordinator_summary(year, month):
    """Get summary statistics"""
    conn = get_db_connection()
    try:
        table_name = f"coordinator_tasks_{year}_{month:02d}"

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
            COUNT(DISTINCT patient_id) as total_patients,
            COUNT(*) as total_tasks,
            SUM(duration_minutes) as total_minutes
        FROM {table_name}
        WHERE patient_id IS NOT NULL
        """

        result = conn.execute(query).fetchone()
        if result:
            return {
                "total_patients": result[0],
                "total_tasks": result[1],
                "total_minutes": result[2] or 0,
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
    """Main billing dashboard"""
    # Get available months
    months = get_available_months()

    if not months:
        st.warning("No coordinator billing data available")
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
        summary = get_coordinator_summary(year, month)

        if summary:
            st.subheader("Monthly Summary")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Patients", summary["total_patients"])
            with col2:
                st.metric("Total Tasks", summary["total_tasks"])
            with col3:
                st.metric("Total Minutes", f"{summary['total_minutes']:,.0f}")

        # Get detailed data
        billing_df = get_coordinator_billing_data(year, month)

        if not billing_df.empty:
            st.subheader("Billing Data by Patient")

            # Filters
            col1, col2 = st.columns(2)

            with col1:
                billing_codes = ["All"] + sorted(
                    billing_df["billing_code"].unique().tolist()
                )
                selected_code = st.selectbox("Filter by Billing Code", billing_codes)

            with col2:
                show_pending = st.checkbox("Show Only Pending Codes", value=False)

            # Apply filters
            filtered_df = billing_df.copy()

            if selected_code != "All":
                filtered_df = filtered_df[filtered_df["billing_code"] == selected_code]

            if show_pending:
                filtered_df = filtered_df[filtered_df["billing_code"] == "PENDING"]

            # Display table
            st.dataframe(
                filtered_df[
                    [
                        "patient_id",
                        "task_count",
                        "total_minutes",
                        "billing_code",
                        "billing_description",
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
                csv_data = export_to_csv(filtered_df, "coordinator_billing")
                st.download_button(
                    label="Download Filtered Data (CSV)",
                    data=csv_data,
                    file_name=f"coordinator_billing_{year}_{month:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )

            with col2:
                csv_all = export_to_csv(billing_df, "coordinator_billing_all")
                st.download_button(
                    label="Download All Data (CSV)",
                    data=csv_all,
                    file_name=f"coordinator_billing_all_{year}_{month:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )

            with col3:
                pending_df = billing_df[billing_df["billing_code"] == "PENDING"]
                if not pending_df.empty:
                    csv_pending = export_to_csv(
                        pending_df, "coordinator_billing_pending"
                    )
                    st.download_button(
                        label="Download Pending Codes (CSV)",
                        data=csv_pending,
                        file_name=f"coordinator_billing_pending_{year}_{month:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )

        else:
            st.info("No billing data available for selected period")


if __name__ == "__main__":
    display_monthly_coordinator_billing_dashboard()
