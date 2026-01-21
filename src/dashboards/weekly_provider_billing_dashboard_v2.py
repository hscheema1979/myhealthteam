"""
Weekly Provider Billing Dashboard - Updated
Handles both CSV summaries (pre-2026) and live operational data (2026+)
For CSV data: Read-only viewing from csv_weekly_billing_summary tables
For Live data: Full workflow status tracking from provider_task_billing_status
"""

import calendar
from datetime import datetime
import zipfile
import io

import pandas as pd
import streamlit as st

from src import database
from src.config.ui_style_config import (
    get_metric_label,
    get_section_title,
)


def get_db_connection():
    from src.database import get_db_connection
    return get_db_connection()


def get_available_periods():
    """Get list of available billing periods from CSV summaries and operational tables"""
    conn = get_db_connection()
    try:
        periods = []

        # Get periods from CSV weekly billing summaries
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'csv_weekly_billing_summary_%'
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
                        view_name = "provider_weekly_2026_01_import"
                    elif year >= 2026:
                        display_name = f"{month_name} {year} (CSV)"
                        data_type = "CSV"
                        view_name = f"csv_weekly_billing_summary_{year}_{month:02d}"
                    else:
                        display_name = f"{month_name} {year}"
                        data_type = "CSV"
                        view_name = f"csv_weekly_billing_summary_{year}_{month:02d}"

                    periods.append({
                        "year": year,
                        "month": month,
                        "display": display_name,
                        "data_type": data_type,
                        "view": view_name,
                        "table": table_name
                    })
                except (ValueError, IndexError):
                    continue

        # Check for 2026 live operational data
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name = 'provider_tasks_2026_01'
        """)
        if cursor.fetchone():
            # Count records to see if there's live data
            count = conn.execute("SELECT COUNT(*) FROM provider_tasks_2026_01 WHERE provider_id IS NOT NULL").fetchone()[0]
            if count > 0:
                periods.append({
                    "year": 2026,
                    "month": 1,
                    "display": "January 2026 (Live)",
                    "data_type": "LIVE",
                    "view": "provider_weekly_2026_01"
                })
                # Combined option
                periods.append({
                    "year": 2026,
                    "month": 1,
                    "display": "January 2026 (Combined)",
                    "data_type": "COMBINED",
                    "view": "provider_weekly_2026_01_combined"
                })

        return sorted(periods, key=lambda x: (x["year"], x["month"]), reverse=True)
    except Exception as e:
        st.error(f"Error getting available periods: {e}")
        return []
    finally:
        conn.close()


def get_weeks_for_period(selected_period):
    """Get available weeks for selected period"""
    conn = get_db_connection()
    try:
        data_type = selected_period.get("data_type", "")
        year = selected_period["year"]
        month = selected_period["month"]

        if data_type == "CSV" or data_type == "CSV_IMPORT":
            table_name = f"csv_weekly_billing_summary_{year}_{month:02d}"
            query = f"""
                SELECT DISTINCT
                    week_number,
                    week_start_date,
                    week_end_date,
                    billing_week
                FROM {table_name}
                ORDER BY week_number ASC
            """
            rows = conn.execute(query).fetchall()
            weeks = []
            for row in rows:
                weeks.append({
                    "week_number": row[0],
                    "week_start_date": row[1],
                    "week_end_date": row[2],
                    "billing_week": row[3],
                    "display": f"Week {row[0]} - {row[1]}"
                })
            return weeks

        elif data_type == "LIVE":
            # For live data, use provider_task_billing_status
            query = """
                SELECT DISTINCT
                    CAST(STRFTIME('%W', week_start_date) AS INTEGER) as week_number,
                    week_start_date,
                    week_end_date,
                    billing_week
                FROM provider_task_billing_status
                WHERE STRFTIME('%Y', week_start_date) = ?
                    AND STRFTIME('%m', week_start_date) = ?
                ORDER BY week_number ASC
            """
            rows = conn.execute(query, (str(year), f"{month:02d}")).fetchall()
            weeks = []
            for row in rows:
                weeks.append({
                    "week_number": row[0],
                    "week_start_date": row[1],
                    "week_end_date": row[2],
                    "billing_week": row[3],
                    "display": f"Week {row[0]} - {row[1]}"
                })
            return weeks

        elif data_type == "COMBINED":
            # For combined, use the combined view
            query = """
                SELECT DISTINCT
                    week_number,
                    MIN(week_start_date) as week_start_date,
                    MIN(week_end_date) as week_end_date,
                    billing_week
                FROM provider_weekly_2026_01_combined
                GROUP BY week_number, billing_week
                ORDER BY week_number ASC
            """
            rows = conn.execute(query).fetchall()
            weeks = []
            for row in rows:
                weeks.append({
                    "week_number": row[0],
                    "week_start_date": row[1],
                    "week_end_date": row[2],
                    "billing_week": row[3],
                    "display": f"Week {row[0]} - {row[1]}"
                })
            return weeks

        return []
    except Exception as e:
        st.error(f"Error getting weeks for period: {e}")
        return []
    finally:
        conn.close()


def get_providers_for_period_and_week(selected_period, week_number):
    """Get available providers for selected period and week"""
    conn = get_db_connection()
    try:
        data_type = selected_period.get("data_type", "")
        year = selected_period["year"]
        month = selected_period["month"]

        providers = []
        providers.append({"provider_id": None, "provider_name": "All Providers"})

        if data_type == "CSV" or data_type == "CSV_IMPORT":
            table_name = f"csv_weekly_billing_summary_{year}_{month:02d}"
            query = f"""
                SELECT DISTINCT
                    provider_id,
                    provider_name
                FROM {table_name}
                WHERE week_number = ?
                ORDER BY provider_name
            """
            rows = conn.execute(query, (week_number,)).fetchall()
            for row in rows:
                providers.append({
                    "provider_id": row[0],
                    "provider_name": row[1]
                })

        elif data_type == "LIVE":
            query = """
                SELECT DISTINCT
                    provider_id,
                    provider_name
                FROM provider_task_billing_status
                WHERE STRFTIME('%Y', week_start_date) = ?
                    AND STRFTIME('%m', week_start_date) = ?
                    AND CAST(STRFTIME('%W', week_start_date) AS INTEGER) = ?
                ORDER BY provider_name
            """
            rows = conn.execute(query, (str(year), f"{month:02d}", week_number)).fetchall()
            for row in rows:
                providers.append({
                    "provider_id": row[0],
                    "provider_name": row[1]
                })

        elif data_type == "COMBINED":
            query = """
                SELECT DISTINCT
                    provider_id,
                    provider_name
                FROM provider_weekly_2026_01_combined
                WHERE week_number = ?
                ORDER BY provider_name
            """
            rows = conn.execute(query, (week_number,)).fetchall()
            for row in rows:
                providers.append({
                    "provider_id": row[0],
                    "provider_name": row[1]
                })

        return providers
    except Exception as e:
        st.error(f"Error getting providers: {e}")
        return [{"provider_id": None, "provider_name": "All Providers"}]
    finally:
        conn.close()


def get_provider_billing_data(selected_period, week_number, provider_filter=None):
    """Get provider billing data based on selected period and week"""
    conn = get_db_connection()
    try:
        data_type = selected_period.get("data_type", "")
        year = selected_period["year"]
        month = selected_period["month"]

        if data_type == "CSV" or data_type == "CSV_IMPORT":
            table_name = f"csv_weekly_billing_summary_{year}_{month:02d}"

            query = f"""
                SELECT
                    provider_id,
                    provider_name,
                    week_start_date,
                    week_end_date,
                    year,
                    week_number,
                    billing_code,
                    billing_code_description,
                    task_type,
                    total_tasks,
                    total_minutes,
                    total_hours,
                    unique_patients,
                    '{data_type}' as data_source
                FROM {table_name}
                WHERE week_number = ?
            """
            params = [week_number]

            if provider_filter and provider_filter != "All Providers":
                query += " AND provider_name = ?"
                params.append(provider_filter)

            query += " ORDER BY provider_name, billing_code"

        elif data_type == "LIVE":
            # For live data, get from provider_task_billing_status
            # with additional provider_weekly_summary_with_billing details
            query = """
                SELECT
                    ptbs.provider_id,
                    ptbs.provider_name,
                    ptbs.week_start_date,
                    ptbs.week_end_date,
                    STRFTIME('%Y', ptbs.week_start_date) as year,
                    CAST(STRFTIME('%W', ptbs.week_start_date) AS INTEGER) as week_number,
                    ptbs.billing_code,
                    ptbs.billing_code_description,
                    ptbs.task_description as task_type,
                    COUNT(*) as total_tasks,
                    SUM(ptbs.minutes_of_service) as total_minutes,
                    ROUND(SUM(ptbs.minutes_of_service) / 60.0, 2) as total_hours,
                    COUNT(DISTINCT ptbs.patient_name) as unique_patients,
                    'LIVE' as data_source
                FROM provider_task_billing_status ptbs
                WHERE STRFTIME('%Y', ptbs.week_start_date) = ?
                    AND STRFTIME('%m', ptbs.week_start_date) = ?
                    AND CAST(STRFTIME('%W', ptbs.week_start_date) AS INTEGER) = ?
            """
            params = [str(year), f"{month:02d}", week_number]

            if provider_filter and provider_filter != "All Providers":
                query += " AND ptbs.provider_name = ?"
                params.append(provider_filter)

            query += " GROUP BY ptbs.provider_id, ptbs.provider_name, ptbs.billing_code, ptbs.task_description"
            query += " ORDER BY ptbs.provider_name, ptbs.billing_code"

        elif data_type == "COMBINED":
            query = """
                SELECT
                    provider_id,
                    provider_name,
                    week_start_date,
                    week_end_date,
                    year,
                    week_number,
                    billing_code,
                    billing_code_description,
                    task_type,
                    SUM(total_tasks) as total_tasks,
                    SUM(total_minutes) as total_minutes,
                    ROUND(SUM(total_minutes) / 60.0, 2) as total_hours,
                    SUM(unique_patients) as unique_patients,
                    data_source
                FROM provider_weekly_2026_01_combined
                WHERE week_number = ?
            """
            params = [week_number]

            if provider_filter and provider_filter != "All Providers":
                query += " AND provider_name = ?"
                params.append(provider_filter)

            query += " GROUP BY provider_id, provider_name, billing_code, task_type, data_source"
            query += " ORDER BY provider_name, data_source, billing_code"

        else:
            return pd.DataFrame()

        df = pd.read_sql_query(query, conn, params=params)
        return df

    except Exception as e:
        st.error(f"Error getting provider billing data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_billing_summary(selected_period, week_number, provider_filter=None):
    """Get summary statistics for selected period and week"""
    conn = get_db_connection()
    try:
        data_type = selected_period.get("data_type", "")
        year = selected_period["year"]
        month = selected_period["month"]

        if data_type == "CSV" or data_type == "CSV_IMPORT":
            table_name = f"csv_weekly_billing_summary_{year}_{month:02d}"
            query = f"""
                SELECT
                    SUM(total_tasks) as total_tasks,
                    SUM(total_minutes) as total_minutes,
                    COUNT(DISTINCT provider_id) as unique_providers,
                    SUM(unique_patients) as total_patients
                FROM {table_name}
                WHERE week_number = ?
            """
            params = [week_number]

            if provider_filter and provider_filter != "All Providers":
                query += " AND provider_name = ?"
                params.append(provider_filter)

        elif data_type == "LIVE":
            query = """
                SELECT
                    COUNT(*) as total_tasks,
                    SUM(minutes_of_service) as total_minutes,
                    COUNT(DISTINCT provider_id) as unique_providers,
                    COUNT(DISTINCT patient_name) as total_patients
                FROM provider_task_billing_status
                WHERE STRFTIME('%Y', week_start_date) = ?
                    AND STRFTIME('%m', week_start_date) = ?
                    AND CAST(STRFTIME('%W', week_start_date) AS INTEGER) = ?
            """
            params = [str(year), f"{month:02d}", week_number]

            if provider_filter and provider_filter != "All Providers":
                query += " AND provider_name = ?"
                params.append(provider_filter)

        elif data_type == "COMBINED":
            query = """
                SELECT
                    SUM(total_tasks) as total_tasks,
                    SUM(total_minutes) as total_minutes,
                    COUNT(DISTINCT provider_id) as unique_providers,
                    SUM(unique_patients) as total_patients
                FROM provider_weekly_2026_01_combined
                WHERE week_number = ?
            """
            params = [week_number]

            if provider_filter and provider_filter != "All Providers":
                query += " AND provider_name = ?"
                params.append(provider_filter)

        result = conn.execute(query, params).fetchone()
        if result and result[0]:
            return {
                "total_tasks": result[0] or 0,
                "total_minutes": result[1] or 0,
                "unique_providers": result[2] or 0,
                "total_patients": result[3] or 0,
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


def display_weekly_provider_billing_dashboard(user_id=None, user_role_ids=None):
    """Main billing dashboard v2 - handles CSV summaries and live data"""

    # For live data, check if we need to process weekly billing
    try:
        from src.billing.weekly_billing_processor import WeeklyBillingProcessor
        processor = WeeklyBillingProcessor()
        processor.process_weekly_billing()
    except Exception as e:
        # Log but don't break the dashboard
        import logging
        logging.getLogger(__name__).warning(f"Weekly billing processing failed: {e}")

    periods = get_available_periods()

    if not periods:
        st.warning("No provider billing data available")
        return

    tab1, tab2 = st.tabs(["Single Week View", "Bulk Download"])

    with tab1:
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_period = st.selectbox(
                "Select Period", options=periods, format_func=lambda x: x["display"], key="period_select"
            )

        if selected_period:
            data_type = selected_period.get("data_type", "")
            year = selected_period["year"]
            month = selected_period["month"]

            with col2:
                # Get weeks for selected period
                weeks = get_weeks_for_period(selected_period)
                if weeks:
                    selected_week = st.selectbox(
                        "Select Week", options=weeks, format_func=lambda x: x["display"], key="week_select"
                    )
                    week_number = selected_week["week_number"] if selected_week else None
                else:
                    st.info("No weeks available")
                    week_number = None

            with col3:
                if week_number:
                    providers = get_providers_for_period_and_week(selected_period, week_number)
                    selected_provider = st.selectbox(
                        "Select Provider", options=providers, format_func=lambda x: x["provider_name"], key="provider_select"
                    )
                    provider_filter = selected_provider["provider_name"] if selected_provider else None
                else:
                    provider_filter = None

            st.metric("Selected Period", selected_period["display"])
            if data_type:
                st.caption(f"Data Source: {data_type}")

            # Show note about CSV data being read-only
            if data_type in ["CSV", "CSV_IMPORT"]:
                st.info(get_metric_label("info") + ": Historical CSV data is read-only. For billing workflow actions, use live data.")

            # Get summary data
            if week_number:
                summary = get_billing_summary(selected_period, week_number, provider_filter)

                if summary:
                    st.subheader("Weekly Summary")
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(get_metric_label("Total Tasks"), summary["total_tasks"])
                    with col2:
                        st.metric(get_metric_label("Total Minutes"), f"{summary['total_minutes']:,}")
                    with col3:
                        st.metric(get_metric_label("Unique Providers"), summary["unique_providers"])
                    with col4:
                        st.metric(get_metric_label("Total Patients"), summary["total_patients"])

                # Get detailed billing data
                df = get_provider_billing_data(selected_period, week_number, provider_filter)

                if not df.empty:
                    st.subheader("Provider Billing Breakdown")

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
                    csv_data = export_to_csv(df, f"provider_billing_{year}_{month:02d}_w{week_number}.csv")
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"provider_billing_{year}_{month:02d}_w{week_number}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No data available for selected period and week")
            else:
                st.info("Please select a week")

    with tab2:
        st.subheader("Bulk Download")
        st.info("Select periods to download and export as a single ZIP file")

        # Multi-select for periods
        selected_periods = st.multiselect(
            "Select Periods to Download",
            options=periods,
            format_func=lambda x: x["display"],
            key="bulk_period_select"
        )

        if selected_periods and st.button("Generate ZIP", key="generate_zip"):
            zip_buffer = io.BytesIO()
            total_files = 0

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for period in selected_periods:
                    # Get all weeks for this period
                    weeks = get_weeks_for_period(period)
                    for week in weeks:
                        df = get_provider_billing_data(period, week["week_number"])
                        if not df.empty:
                            filename = f"provider_billing_{period['year']}_{period['month']:02d}_w{week['week_number']}.csv"
                            zip_file.writestr(filename, df.to_csv(index=False).encode('utf-8'))
                            total_files += 1

            zip_buffer.seek(0)
            st.download_button(
                label=f"Download ZIP Archive ({total_files} files)",
                data=zip_buffer.getvalue(),
                file_name=f"provider_billing_bulk_{datetime.now().strftime('%Y%m%d')}.zip",
                mime="application/zip"
            )


if __name__ == "__main__":
    display_weekly_provider_billing_dashboard(
        user_id=1,
        user_role_ids=[34],  # Admin for testing
    )
