"""
Daily Patient Export System
Exports active patient data to CSV and syncs with Google Sheets
"""

import sqlite3
import csv
import os
from datetime import datetime
from pathlib import Path
import logging
from typing import List, Dict, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_patient_export.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PatientExporter:
    """Handles daily export of patient data to CSV"""
    
    def __init__(self, db_path: str = 'production.db', export_dir: str = 'exports'):
        """
        Initialize the exporter
        
        Args:
            db_path: Path to the SQLite database
            export_dir: Directory to store exported CSV files
        """
        self.db_path = db_path
        self.export_dir = export_dir
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create export directory if it doesn't exist
        Path(self.export_dir).mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(exist_ok=True)
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_active_patients(self) -> List[Dict]:
        """
        Retrieve all active patients with their related data
        
        Returns:
            List of dictionaries containing patient data
        """
        conn = self.get_db_connection()
        try:
            query = """
            SELECT DISTINCT
                p.patient_id,
                p.status as 'Pt Status',
                p.last_visit_date as 'Last Visit',
                'TV' as 'Last Visit Type',  -- Placeholder for visit type
                p.last_first_dob as 'LAST FIRST DOB',
                p.last_name as 'Last',
                p.first_name as 'First',
                COALESCE(p.phone_primary, p.phone_secondary, p.email, '') as 'Contact',
                (p.first_name || ' ' || p.last_name) as 'Name',
                p.address_city as 'City',
                p.facility as 'Fac',
                '' as 'Initial TV',  -- Placeholder
                pr.first_name || ' ' || pr.last_name as 'Prov',
                p.insurance_primary as 'Insurance Eligibility',
                pa.assignment_date as 'Assigned',
                pr.first_name || ' ' || pr.last_name as 'Reg Prov',
                COALESCE(cc.first_name || ' ' || cc.last_name, 'Unassigned') as 'Care Coordinator',
                '' as 'Prescreen Call',  -- Placeholder
                p.notes as 'Notes',
                '' as 'Initial TV_Date',  -- Placeholder
                '' as 'Initial TV_Notes',  -- Placeholder
                '' as 'Initial HV_Date',  -- Placeholder
                '' as 'Labs',  -- Placeholder
                '' as 'Imaging',  -- Placeholder
                p.notes as 'General Notes',
                p.status as 'status',
                '' as 'goc',
                '' as 'code',
                p.subjective_risk_level as 'risk',
                (p.first_name || ' ' || p.last_name) as 'pt_name',
                '' as 'MED_poc',
                '' as 'Appt_POC'
            FROM patients p
            LEFT JOIN patient_assignments pa ON p.patient_id = pa.patient_id
            LEFT JOIN users pr ON pa.provider_id = pr.user_id
            LEFT JOIN users cc ON p.assigned_coordinator_id = cc.user_id
            WHERE p.status = 'active' OR p.status = 'Active'
            ORDER BY p.last_name, p.first_name
            """
            
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Convert rows to list of dictionaries
            patients = []
            for row in cursor.fetchall():
                patients.append(dict(row))
            
            logger.info(f"Retrieved {len(patients)} active patients")
            return patients
            
        except Exception as e:
            logger.error(f"Error retrieving patients: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_visit_data(self, patient_id: str) -> Optional[Dict]:
        """
        Get the most recent visit data for a patient
        
        Args:
            patient_id: Patient ID
            
        Returns:
            Dictionary with visit information or None
        """
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT *
                FROM patient_visits
                WHERE patient_id = ?
                ORDER BY visit_date DESC
                LIMIT 1
            """, (patient_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            logger.warning(f"Could not retrieve visit data for patient {patient_id}: {str(e)}")
            return None
        finally:
            conn.close()
    
    def enrich_patient_data(self, patients: List[Dict]) -> List[Dict]:
        """
        Enrich patient data with additional information
        
        Args:
            patients: List of patient dictionaries
            
        Returns:
            Enriched patient data
        """
        enriched = []
        
        for patient in patients:
            # Get visit data
            visit = self.get_visit_data(patient.get('patient_id'))
            
            if visit:
                patient['Last Visit'] = visit.get('visit_date', patient.get('Last Visit'))
                patient['Last Visit Type'] = visit.get('visit_type', 'TV')
                if 'Initial TV_Date' in patient and not patient['Initial TV_Date']:
                    patient['Initial TV_Date'] = visit.get('visit_date', '')
                if 'Initial TV_Notes' in patient and not patient['Initial TV_Notes']:
                    patient['Initial TV_Notes'] = visit.get('notes', '')
            
            enriched.append(patient)
        
        return enriched
    
    def export_to_csv(self, patients: List[Dict], filename: Optional[str] = None) -> str:
        """
        Export patient data to CSV file
        
        Args:
            patients: List of patient dictionaries
            filename: Optional custom filename (defaults to timestamp-based)
            
        Returns:
            Path to the created CSV file
        """
        if not filename:
            filename = f"patient_export_{self.timestamp}.csv"
        
        filepath = os.path.join(self.export_dir, filename)
        
        if not patients:
            logger.warning("No patients to export")
            return filepath
        
        try:
            # Define column order based on your requirements
            fieldnames = [
                'Pt Status', 'Last Visit', 'Last Visit Type', 'LAST FIRST DOB',
                'Last', 'First', 'Contact', 'Name', 'City', 'Fac',
                'Initial TV', 'Prov', 'Insurance Eligibility', 'Assigned',
                'Reg Prov', 'Care Coordinator', 'Prescreen Call', 'Notes',
                'Initial TV_Date', 'Initial TV_Notes', 'Initial HV_Date',
                'Labs', 'Imaging', 'General Notes',
                'status', 'goc', 'code', 'risk', 'pt_name', 'MED_poc', 'Appt_POC'
            ]
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for patient in patients:
                    # Ensure all fields exist, fill with empty string if missing
                    row = {field: patient.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            logger.info(f"Successfully exported {len(patients)} patients to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise
    
    def get_daily_export_path(self) -> str:
        """Get the standard daily export filename"""
        today = datetime.now().strftime('%Y%m%d')
        return os.path.join(self.export_dir, f"patient_export_{today}.csv")
    
    def run_daily_export(self) -> str:
        """
        Execute the complete daily export process
        
        Returns:
            Path to the exported CSV file
        """
        try:
            logger.info("Starting daily patient export...")
            
            # Get active patients
            patients = self.get_active_patients()
            
            if not patients:
                logger.warning("No active patients found for export")
                return self.get_daily_export_path()
            
            # Enrich with additional data
            enriched_patients = self.enrich_patient_data(patients)
            
            # Export to CSV with daily filename (overwrites if exists)
            daily_filename = f"patient_export_{datetime.now().strftime('%Y%m%d')}.csv"
            export_path = self.export_to_csv(enriched_patients, daily_filename)
            
            logger.info(f"Daily export completed successfully: {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Daily export failed: {str(e)}")
            raise


class GoogleSheetsSync:
    """Handles synchronization with Google Sheets"""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Sheets synchronizer
        
        Args:
            credentials_path: Path to Google service account credentials JSON
        """
        self.credentials_path = credentials_path or 'config/google_credentials.json'
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Sheets API service"""
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            
            if not os.path.exists(self.credentials_path):
                logger.warning(f"Google credentials not found at {self.credentials_path}")
                logger.info("Please follow the setup instructions to enable Google Sheets sync")
                return
            
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("Google Sheets API initialized successfully")
            
        except ImportError:
            logger.warning("Google API client not installed. Install with: pip install google-api-python-client google-auth-oauthlib")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {str(e)}")
    
    def sync_csv_to_sheet(self, csv_path: str, spreadsheet_id: str, sheet_name: str = 'Active Patients') -> bool:
        """
        Sync CSV data to a Google Sheet
        
        Args:
            csv_path: Path to the CSV file
            spreadsheet_id: Google Sheet ID
            sheet_name: Name of the sheet to update
            
        Returns:
            True if successful, False otherwise
        """
        if