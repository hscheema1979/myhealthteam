#!/usr/bin/env python3
"""
Compare provider_tasks table with PSL CSV files in downloads folder
- Analyze data consistency between database and source files
- Identify missing records, discrepancies, and data quality issues
- Generate detailed comparison reports
"""

import pandas as pd
import sqlite3
import glob
import os
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProviderTasksPSLComparator:
    def __init__(self, downloads_dir="./downloads", db_path="./production.db"):
        self.downloads_dir = downloads_dir
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
    def load_psl_files(self):
        """Load and combine all PSL CSV files from downloads folder, filtering for Sept 26th onward"""
        psl_files = glob.glob(os.path.join(self.downloads_dir, "PSL_ZEN-*.csv"))
        
        if not psl_files:
            logger.error(f"No PSL files found in {self.downloads_dir}")
            return None
            
        logger.info(f"Found {len(psl_files)} PSL files")
        
        all_psl_data = []
        file_stats = {}
        
        for file in psl_files:
            try:
                df = pd.read_csv(file)
                
                # Skip placeholder rows
                original_count = len(df)
                df = df[~df['Patient Last, First DOB'].str.contains('Aaa, Aaa', na=False)]
                df = df[~df['Notes'].str.contains('Place holder', na=False)]
                
                # Remove empty rows
                df = df.dropna(subset=['Prov', 'Patient Last, First DOB', 'DOS'])
                
                # Filter for September 26th onward (2024 and 2025)
                df['dos_parsed'] = pd.to_datetime(df['DOS'], errors='coerce')
                sept_26_2024 = pd.to_datetime('2024-09-26')
                df = df[df['dos_parsed'] >= sept_26_2024]
                
                provider_code = os.path.basename(file).replace('PSL_', '').replace('.csv', '')
                df['source_file'] = provider_code
                
                file_stats[provider_code] = {
                    'original_rows': original_count,
                    'filtered_rows': len(df),
                    'provider_code': df['Prov'].iloc[0] if len(df) > 0 else 'Unknown',
                    'date_range': f"{df['dos_parsed'].min()} to {df['dos_parsed'].max()}" if len(df) > 0 else "No data"
                }
                
                all_psl_data.append(df)
                logger.info(f"Loaded {len(df)} records from {os.path.basename(file)} (filtered from {original_count}, Sept 26+ only)")
                
            except Exception as e:
                logger.error(f"Error reading {file}: {e}")
                
        if not all_psl_data:
            return None, {}
            
        combined_psl = pd.concat(all_psl_data, ignore_index=True)
        logger.info(f"Combined PSL data: {len(combined_psl)} total records (Sept 26th onward)")
        
        return combined_psl, file_stats
    
    def load_provider_tasks(self):
        """Load provider_tasks data from database, filtering for September 26th onward"""
        query = """
        SELECT 
            provider_task_id,
            provider_id,
            provider_name,
            patient_name,
            patient_id,
            task_date,
            minutes_of_service,
            billing_code,
            billing_code_description,
            task_description,
            status,
            notes,
            month,
            year
        FROM provider_tasks
        WHERE provider_id IS NOT NULL
        AND task_date >= '2024-09-26'
        """
        
        try:
            db_tasks = pd.read_sql_query(query, self.conn)
            logger.info(f"Loaded {len(db_tasks)} records from provider_tasks table (Sept 26th onward)")
            return db_tasks
        except Exception as e:
            logger.error(f"Error loading provider_tasks: {e}")
            return None
    
    def compare_record_counts(self, psl_data, db_tasks, file_stats):
        """Compare record counts between PSL files and database"""
        logger.info("=== RECORD COUNT COMPARISON ===")
        
        # Group by provider
        psl_by_provider = psl_data.groupby('Prov').size().reset_index(name='psl_count')
        db_by_provider = db_tasks.groupby('provider_id').size().reset_index(name='db_count')
        
        # Convert provider_id to string for comparison
        db_by_provider['provider_id'] = db_by_provider['provider_id'].astype(str)
        
        # Merge for comparison
        comparison = pd.merge(psl_by_provider, db_by_provider, 
                            left_on='Prov', right_on='provider_id', how='outer')
        comparison['psl_count'] = comparison['psl_count'].fillna(0)
        comparison['db_count'] = comparison['db_count'].fillna(0)
        comparison['difference'] = comparison['psl_count'] - comparison['db_count']
        
        print("\nProvider Record Count Comparison:")
        print("Provider | PSL Count | DB Count | Difference")
        print("-" * 45)
        
        for _, row in comparison.iterrows():
            provider = row['Prov'] if pd.notna(row['Prov']) else row['provider_id']
            print(f"{provider:8} | {int(row['psl_count']):9} | {int(row['db_count']):8} | {int(row['difference']):10}")
        
        return comparison
    
    def compare_data_quality(self, psl_data, db_tasks):
        """Compare data quality between PSL and database"""
        logger.info("=== DATA QUALITY COMPARISON ===")
        
        quality_report = {}
        
        # Date format analysis
        psl_data['dos_valid'] = pd.to_datetime(psl_data['DOS'], errors='coerce').notna()
        db_tasks['task_date_valid'] = pd.to_datetime(db_tasks['task_date'], errors='coerce').notna()
        
        quality_report['date_quality'] = {
            'psl_valid_dates': psl_data['dos_valid'].sum(),
            'psl_invalid_dates': (~psl_data['dos_valid']).sum(),
            'db_valid_dates': db_tasks['task_date_valid'].sum(),
            'db_invalid_dates': (~db_tasks['task_date_valid']).sum()
        }
        
        # Minutes analysis
        psl_data['minutes_numeric'] = pd.to_numeric(psl_data['Minutes'], errors='coerce')
        db_tasks['minutes_numeric'] = pd.to_numeric(db_tasks['minutes_of_service'], errors='coerce')
        
        quality_report['minutes_quality'] = {
            'psl_valid_minutes': psl_data['minutes_numeric'].notna().sum(),
            'psl_invalid_minutes': psl_data['minutes_numeric'].isna().sum(),
            'db_valid_minutes': db_tasks['minutes_numeric'].notna().sum(),
            'db_invalid_minutes': db_tasks['minutes_numeric'].isna().sum()
        }
        
        # Patient name analysis
        quality_report['patient_names'] = {
            'psl_unique_patients': psl_data['Patient Last, First DOB'].nunique(),
            'db_unique_patients': db_tasks['patient_name'].nunique(),
            'psl_empty_names': psl_data['Patient Last, First DOB'].isna().sum(),
            'db_empty_names': db_tasks['patient_name'].isna().sum()
        }
        
        print("\nData Quality Report:")
        print("=" * 50)
        
        for category, metrics in quality_report.items():
            print(f"\n{category.upper()}:")
            for metric, value in metrics.items():
                print(f"  {metric}: {value}")
        
        return quality_report
    
    def find_missing_records(self, psl_data, db_tasks):
        """Find records that exist in PSL but not in database"""
        logger.info("=== MISSING RECORDS ANALYSIS ===")
        
        # Create comparison keys
        psl_data['comparison_key'] = (
            psl_data['Prov'].astype(str).str.strip() + '|' +
            psl_data['Patient Last, First DOB'].astype(str).str.strip() + '|' +
            psl_data['DOS'].astype(str).str.strip()
        )
        
        db_tasks['comparison_key'] = (
            db_tasks['provider_id'].astype(str).str.strip() + '|' +
            db_tasks['patient_name'].astype(str).str.strip() + '|' +
            db_tasks['task_date'].astype(str).str.strip()
        )
        
        # Find missing records
        missing_in_db = psl_data[~psl_data['comparison_key'].isin(db_tasks['comparison_key'])]
        missing_in_psl = db_tasks[~db_tasks['comparison_key'].isin(psl_data['comparison_key'])]
        
        print(f"\nRecords in PSL but missing from database: {len(missing_in_db)}")
        print(f"Records in database but missing from PSL: {len(missing_in_psl)}")
        
        if len(missing_in_db) > 0:
            print("\nSample missing records (first 10):")
            print("Provider | Patient | Date | Service")
            print("-" * 60)
            for _, row in missing_in_db.head(10).iterrows():
                print(f"{row['Prov']:8} | {row['Patient Last, First DOB'][:20]:20} | {row['DOS']:8} | {row['Service'][:15]:15}")
        
        return missing_in_db, missing_in_psl
    
    def analyze_billing_codes(self, psl_data, db_tasks):
        """Analyze billing code consistency"""
        logger.info("=== BILLING CODE ANALYSIS ===")
        
        # PSL billing codes
        psl_codes = psl_data['Coding'].value_counts()
        db_codes = db_tasks['billing_code'].value_counts()
        
        print(f"\nUnique billing codes in PSL: {len(psl_codes)}")
        print(f"Unique billing codes in DB: {len(db_codes)}")
        
        print("\nTop 10 PSL billing codes:")
        for code, count in psl_codes.head(10).items():
            print(f"  {code}: {count}")
        
        print("\nTop 10 DB billing codes:")
        for code, count in db_codes.head(10).items():
            print(f"  {code}: {count}")
        
        # Find codes in PSL but not in DB
        psl_only_codes = set(psl_codes.index) - set(db_codes.index)
        db_only_codes = set(db_codes.index) - set(psl_codes.index)
        
        print(f"\nBilling codes only in PSL: {len(psl_only_codes)}")
        if psl_only_codes:
            print("  " + ", ".join(list(psl_only_codes)[:10]))
        
        print(f"Billing codes only in DB: {len(db_only_codes)}")
        if db_only_codes:
            print("  " + ", ".join(list(db_only_codes)[:10]))
        
        return psl_codes, db_codes
    
    def generate_summary_report(self, psl_data, db_tasks, file_stats, comparison_data):
        """Generate comprehensive summary report"""
        logger.info("=== GENERATING SUMMARY REPORT ===")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'file_analysis': {
                'psl_files_processed': len(file_stats),
                'total_psl_records': len(psl_data),
                'total_db_records': len(db_tasks),
                'file_details': file_stats
            },
            'provider_comparison': comparison_data.to_dict('records'),
            'data_coverage': {
                'date_range_psl': {
                    'min_date': psl_data['DOS'].min(),
                    'max_date': psl_data['DOS'].max()
                },
                'date_range_db': {
                    'min_date': db_tasks['task_date'].min(),
                    'max_date': db_tasks['task_date'].max()
                }
            }
        }
        
        # Save detailed report
        report_file = f"provider_tasks_psl_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w') as f:
            f.write("PROVIDER TASKS vs PSL FILES COMPARISON REPORT\n")
            f.write("(September 26th, 2024 onward)\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {report['timestamp']}\n\n")
            
            f.write("FILE ANALYSIS:\n")
            f.write(f"PSL files processed: {report['file_analysis']['psl_files_processed']}\n")
            f.write(f"Total PSL records: {report['file_analysis']['total_psl_records']}\n")
            f.write(f"Total DB records: {report['file_analysis']['total_db_records']}\n\n")
            
            f.write("PROVIDER COMPARISON:\n")
            for provider_data in report['provider_comparison']:
                f.write(f"Provider {provider_data.get('Prov', provider_data.get('provider_id'))}: ")
                f.write(f"PSL={int(provider_data['psl_count'])}, ")
                f.write(f"DB={int(provider_data['db_count'])}, ")
                f.write(f"Diff={int(provider_data['difference'])}\n")
        
        logger.info(f"Detailed report saved to: {report_file}")
        return report
    
    def run_comparison(self):
        """Run complete comparison analysis for September 26th onward"""
        logger.info("Starting provider_tasks vs PSL comparison (September 26th onward)...")
        
        # Load data
        psl_data, file_stats = self.load_psl_files()
        if psl_data is None:
            logger.error("Failed to load PSL data")
            return None
            
        db_tasks = self.load_provider_tasks()
        if db_tasks is None:
            logger.error("Failed to load database tasks")
            return None
        
        # Run comparisons
        comparison_data = self.compare_record_counts(psl_data, db_tasks, file_stats)
        quality_report = self.compare_data_quality(psl_data, db_tasks)
        missing_in_db, missing_in_psl = self.find_missing_records(psl_data, db_tasks)
        psl_codes, db_codes = self.analyze_billing_codes(psl_data, db_tasks)
        
        # Generate summary
        summary_report = self.generate_summary_report(psl_data, db_tasks, file_stats, comparison_data)
        
        logger.info("Comparison analysis complete!")
        return {
            'psl_data': psl_data,
            'db_tasks': db_tasks,
            'comparison_data': comparison_data,
            'quality_report': quality_report,
            'missing_in_db': missing_in_db,
            'missing_in_psl': missing_in_psl,
            'summary_report': summary_report
        }
    
    def close(self):
        """Close database connection"""
        self.conn.close()

if __name__ == "__main__":
    comparator = ProviderTasksPSLComparator()
    try:
        results = comparator.run_comparison()
        if results:
            print("\n" + "="*60)
            print("COMPARISON COMPLETE!")
            print("="*60)
            print(f"PSL Records: {len(results['psl_data'])}")
            print(f"DB Records: {len(results['db_tasks'])}")
            print(f"Missing in DB: {len(results['missing_in_db'])}")
            print(f"Missing in PSL: {len(results['missing_in_psl'])}")
            print("\nCheck the generated report file for detailed analysis.")
    finally:
        comparator.close()