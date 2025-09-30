# core_utils.py
"""
Core utility functions for user roles and other shared logic.
"""
import sqlite3
import pandas as pd
from typing import List, Dict, Any

DB_PATH = 'production.db'  # Adjust path as needed

def get_user_role_ids(user_id: int, db_path: str = DB_PATH) -> List[int]:
    """
    Returns a list of role_ids for the given user_id from the user_roles table.
    """
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT role_id FROM user_roles WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()


# Facility mapping utility

def get_facility_id_to_name_map(db=None):
    """
    Returns a dict mapping facility_id (as str) to facility_name using db.get_all_facilities().
    db: database module (must have get_all_facilities())
    """
    if db is None or not hasattr(db, 'get_all_facilities'):
        raise ValueError("db must be provided and have get_all_facilities()")
    facilities = db.get_all_facilities()
    return {str(f['facility_id']): f['facility_name'] for f in facilities if f.get('facility_id') is not None}

def map_facility_id_to_name(facility_id, facility_id_to_name):
    """
    Robustly map a facility_id (int or str) to a facility_name using the provided mapping dict.
    Returns None if not found.
    """
    if facility_id is None:
        return None
    # Always use string key for lookup
    return facility_id_to_name.get(str(facility_id))


# Patient data aggregation utilities

def aggregate_patient_data_by_patient_id(summary_df: pd.DataFrame, 
                                       patient_id_col: str = 'patient_id', 
                                       minutes_col: str = 'total_minutes') -> pd.DataFrame:
    """
    Aggregate patient data by patient_id to avoid coordinator-patient duplicates.
    
    This function is useful when working with coordinator monthly summary tables that contain
    one record per coordinator-patient combination, but you need to show unique patients
    with their total minutes across all coordinators.
    
    Args:
        summary_df: DataFrame containing patient data with potential duplicates
        patient_id_col: Name of the patient ID column (default: 'patient_id')
        minutes_col: Name of the minutes column to aggregate (default: 'total_minutes')
    
    Returns:
        DataFrame with unique patients and aggregated minutes
    """
    if summary_df.empty:
        return summary_df
    
    # Ensure required columns exist
    if patient_id_col not in summary_df.columns or minutes_col not in summary_df.columns:
        raise ValueError(f"Required columns '{patient_id_col}' and '{minutes_col}' must exist in DataFrame")
    
    # Prepare data for aggregation
    agg_df = summary_df[[patient_id_col, minutes_col]].copy()
    agg_df[minutes_col] = pd.to_numeric(agg_df[minutes_col], errors='coerce').fillna(0)
    
    # Group by patient_id and sum minutes across all coordinators
    aggregated = agg_df.groupby(patient_id_col).agg({minutes_col: 'sum'}).reset_index()
    
    return aggregated


def prepare_patient_summary_with_facility_mapping(aggregated_df: pd.DataFrame, 
                                                 db, 
                                                 patient_id_col: str = 'patient_id',
                                                 minutes_col: str = 'total_minutes') -> pd.DataFrame:
    """
    Prepare a patient summary DataFrame with patient names and facility mapping.
    
    Args:
        aggregated_df: DataFrame with aggregated patient data (from aggregate_patient_data_by_patient_id)
        db: Database module with get_all_patients() method
        patient_id_col: Name of the patient ID column (default: 'patient_id')
        minutes_col: Name of the minutes column (default: 'total_minutes')
    
    Returns:
        DataFrame with Patient, Facility, and Sum of Minutes columns
    """
    if aggregated_df.empty:
        return pd.DataFrame(columns=['Patient', 'Facility', 'Sum of Minutes'])
    
    # Create patient ID to name mapping
    id_to_name = {}
    id_to_facility_id = {}
    patients = db.get_all_patients() if hasattr(db, 'get_all_patients') else []
    for p in patients:
        pid = p.get('patient_id')
        if pid is None:
            continue
        id_to_name[str(pid)] = f"{p.get('first_name','') or ''} {p.get('last_name','') or ''}".strip()
        id_to_facility_id[str(pid)] = p.get('current_facility_id') or p.get('facility')

    # Get facility mapping
    facility_id_to_name = get_facility_id_to_name_map(db)
    
    # Prepare summary DataFrame
    summary_df = aggregated_df.rename(columns={patient_id_col: 'Patient ID', minutes_col: 'Sum of Minutes'})
    summary_df['Patient'] = summary_df['Patient ID'].astype(str).map(id_to_name).fillna(summary_df['Patient ID'])
    summary_df['Facility ID'] = summary_df['Patient ID'].astype(str).map(id_to_facility_id)
    summary_df['Facility'] = summary_df['Facility ID'].astype(str).map(lambda fid: facility_id_to_name.get(str(fid), str(fid) if fid else 'Unknown'))
    summary_df = summary_df[['Patient', 'Facility', 'Sum of Minutes']]
    summary_df = summary_df.sort_values('Sum of Minutes', ascending=True)
    
    return summary_df
