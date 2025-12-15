#!/usr/bin/env python3
"""
Database Schema Validation Script
Phase 1: Schema Analysis - Extract all tables and compare against dashboard requirements

This script:
1. Extracts all tables from production.db
2. Parses dashboard SQL queries to identify required tables/columns
3. Identifies missing tables and columns
4. Generates a comprehensive validation report
"""

import sqlite3
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

class DatabaseSchemaValidator:
    def __init__(self, db_path: str = "production.db"):
        self.db_path = db_path
        self.existing_tables: Dict[str, List[Dict[str, Any]]] = {}
        self.dashboard_requirements: Dict[str, Dict[str, Any]] = {}
        self.missing_tables: List[str] = []
        self.missing_columns: Dict[str, List[str]] = {}
        self.validation_report: Dict[str, Any] = {}
        
    def get_db_connection(self):
        """Get SQLite database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
        
    def extract_existing_tables(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extract all tables and their columns from production.db"""
        print("🔍 Extracting existing tables from production.db...")
        
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Get all tables (excluding sqlite_sequence)
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            
            tables = cursor.fetchall()
            print(f"Found {len(tables)} tables in production.db")
            
            for table_row in tables:
                table_name = table_row['name']
                # Get column information for this table
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                column_info = []
                for col in columns:
                    column_info.append({
                        'name': col[1],
                        'type': col[2],
                        'nullable': not col[3],  # not null = 1 means nullable = False
                        'default': col[4],
                        'primary_key': col[5] == 1
                    })
                
                self.existing_tables[table_name] = column_info
                print(f"  - {table_name}: {len(column_info)} columns")
                
        finally:
            conn.close()
            
        return self.existing_tables
        
    def parse_dashboard_sql_queries(self, dashboard_path: str = "src/dashboards") -> Dict[str, Set[str]]:
        """Parse dashboard Python files to extract SQL table references"""
        print(f"\n📊 Parsing dashboard SQL queries from {dashboard_path}...")
        
        dashboard_tables: Dict[str, Set[str]] = {}
        
        if not os.path.exists(dashboard_path):
            print(f"Warning: Dashboard path {dashboard_path} does not exist")
            return dashboard_tables
            
        # Find all Python dashboard files
        dashboard_files = list(Path(dashboard_path).glob("*.py"))
        print(f"Found {len(dashboard_files)} dashboard files")
        
        for dashboard_file in dashboard_files:
            dashboard_name = dashboard_file.stem
            dashboard_tables[dashboard_name] = set()
            
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract SQL queries (basic pattern matching)
            # Look for execute() calls with SQL
            sql_patterns = [
                r'execute\(["\']([^"\']*?)["\']',  # execute("SELECT ...")
                r'execute\(\s*["\']([^"\']*?)["\']',  # execute( "SELECT ...")
                r'conn\.execute\(["\']([^"\']*?)["\']',  # conn.execute("SELECT ...")
                r'cursor\.execute\(["\']([^"\']*?)["\']',  # cursor.execute("SELECT ...")
            ]
            
            all_queries = []
            for pattern in sql_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                all_queries.extend(matches)
            
            # Extract table names from SQL queries
            for query in all_queries:
                # Clean up the query (remove newlines, extra spaces)
                query = ' '.join(query.split())
                
                # Look for table names in FROM and JOIN clauses
                table_pattern = r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
                tables = re.findall(table_pattern, query, re.IGNORECASE)
                
                for table in tables:
                    # Skip common SQL keywords that might be captured
                    if table.upper() not in ['SELECT', 'WHERE', 'GROUP', 'ORDER', 'LIMIT']:
                        dashboard_tables[dashboard_name].add(table)
        
        # Print findings
        for dashboard, tables in dashboard_tables.items():
            print(f"  - {dashboard}: {len(tables)} tables referenced")
            for table in sorted(tables):
                print(f"    * {table}")
                
        return dashboard_tables
        
    def parse_database_functions(self, db_module_path: str = "src/database.py") -> Dict[str, Set[str]]:
        """Parse database.py to extract table references in functions"""
        print(f"\n🔧 Parsing database functions from {db_module_path}...")
        
        function_tables: Dict[str, Set[str]] = {}
        
        if not os.path.exists(db_module_path):
            print(f"Warning: Database module {db_module_path} does not exist")
            return function_tables
            
        with open(db_module_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract function names and their SQL queries
        function_pattern = r'def (\w+)\([^)]*\):.*?(?=def |\Z)'
        functions = re.findall(function_pattern, content, re.DOTALL)
        
        for func_match in functions:
            # This is a simplified extraction - in practice we'd need more sophisticated parsing
            func_name = func_match.split('(')[0].strip()
            if func_name.startswith('_'):
                continue  # Skip private functions
                
            function_tables[func_name] = set()
            
            # Look for table names in the function body
            # Pattern for table names in SQL queries
            table_patterns = [
                r'([a-zA-Z_][a-zA-Z0-9_]*_tasks_\d{4}_\d{2})',  # Monthly task tables
                r'([a-zA-Z_][a-zA-Z0-9_]*_tasks_\d{4}_\d{1})',   # Single digit month
                r'\b(patients|users|roles|user_roles|facilities|task_billing_codes|patient_panel|patient_assignments|onboarding_patients)\b',
                r'\b(provider_tasks|coordinator_tasks)_\d{4}_\d{1,2}\b',
            ]
            
            for pattern in table_patterns:
                matches = re.findall(pattern, func_match)
                for match in matches:
                    if isinstance(match, tuple):
                        for item in match:
                            if item:
                                function_tables[func_name].add(item)
                    else:
                        function_tables[func_name].add(match)
        
        # Print findings
        for func, tables in function_tables.items():
            if tables:
                print(f"  - {func}(): {len(tables)} tables referenced")
                for table in sorted(tables):
                    print(f"    * {table}")
                    
        return function_tables
        
    def identify_missing_tables(self) -> List[str]:
        """Identify tables referenced in dashboards but missing from database"""
        print("\n❌ Identifying missing tables...")
        
        # Combine all required tables from dashboards and database functions
        all_required_tables: Set[str] = set()
        
        # Add dashboard requirements
        dashboard_tables = self.parse_dashboard_sql_queries()
        for tables in dashboard_tables.values():
            all_required_tables.update(tables)
            
        # Add database function requirements
        function_tables = self.parse_database_functions()
        for tables in function_tables.values():
            all_required_tables.update(tables)
            
        # Check for dynamic monthly tables (provider_tasks_YYYY_MM, coordinator_tasks_YYYY_MM)
        monthly_patterns = [
            (r'provider_tasks_\d{4}_\d{1,2}', 'provider_tasks_YYYY_MM'),
            (r'coordinator_tasks_\d{4}_\d{1,2}', 'coordinator_tasks_YYYY_MM'),
        ]
        
        # Add pattern placeholders
        all_required_tables.add('provider_tasks_YYYY_MM')
        all_required_tables.add('coordinator_tasks_YYYY_MM')
        
        # Check which tables exist
        existing_table_names = set(self.existing_tables.keys())
        
        # Identify missing tables
        self.missing_tables = []
        for required_table in all_required_tables:
            # Check if it's a monthly pattern
            is_pattern = False
            for pattern, placeholder in monthly_patterns:
                if required_table == placeholder:
                    # Check if any tables match this pattern
                    pattern_exists = any(re.match(pattern, table) for table in existing_table_names)
                    if not pattern_exists:
                        self.missing_tables.append(f"{placeholder} (pattern: no tables found)")
                    is_pattern = True
                    break
            
            if not is_pattern and required_table not in existing_table_names:
                self.missing_tables.append(required_table)
        
        if self.missing_tables:
            print(f"Found {len(self.missing_tables)} missing tables:")
            for table in self.missing_tables:
                print(f"  - {table}")
        else:
            print("✅ No missing tables found!")
            
        return self.missing_tables
        
    def identify_missing_columns(self) -> Dict[str, List[str]]:
        """Identify missing columns in existing tables based on dashboard requirements"""
        print("\n❌ Identifying missing columns...")
        
        # This would require parsing the actual column requirements from dashboards
        # For now, we'll check for common required columns that should exist
        
        critical_columns = {
            'patients': ['patient_id', 'first_name', 'last_name', 'date_of_birth'],
            'users': ['user_id', 'username', 'full_name', 'email'],
            'user_roles': ['user_id', 'role_id'],
            'provider_tasks_YYYY_MM': ['provider_id', 'patient_id', 'task_date', 'minutes_of_service'],
            'coordinator_tasks_YYYY_MM': ['coordinator_id', 'patient_id', 'task_date', 'duration_minutes'],
        }
        
        self.missing_columns = {}
        
        for table_pattern, required_cols in critical_columns.items():
            # Find tables matching the pattern
            matching_tables = []
            
            if 'YYYY_MM' in table_pattern:
                # Pattern for monthly tables
                base_pattern = table_pattern.replace('_YYYY_MM', '')
                pattern = re.compile(rf'{base_pattern}_\d{{4}}_\d{{1,2}}')
                matching_tables = [t for t in self.existing_tables.keys() if pattern.match(t)]
            else:
                # Exact table name
                if table_pattern in self.existing_tables:
                    matching_tables = [table_pattern]
            
            for table in matching_tables:
                existing_cols = [col['name'] for col in self.existing_tables[table]]
                missing = [col for col in required_cols if col not in existing_cols]
                
                if missing:
                    if table not in self.missing_columns:
                        self.missing_columns[table] = []
                    self.missing_columns[table].extend(missing)
        
        if self.missing_columns:
            print(f"Found missing columns in {len(self.missing_columns)} tables:")
            for table, columns in self.missing_columns.items():
                print(f"  - {table}: {', '.join(columns)}")
        else:
            print("✅ No missing columns found!")
            
        return self.missing_columns
        
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        print("\n📋 Generating validation report...")
        
        self.validation_report = {
            'timestamp': '2025-12-11T19:00:00Z',
            'database_path': self.db_path,
            'summary': {
                'total_tables_in_db': len(self.existing_tables),
                'missing_tables_count': len(self.missing_tables),
                'missing_columns_count': sum(len(cols) for cols in self.missing_columns.values()),
            },
            'existing_tables': list(self.existing_tables.keys()),
            'missing_tables': self.missing_tables,
            'missing_columns': self.missing_columns,
            'table_details': self.existing_tables,
        }
        
        # Save report to JSON file
        report_path = 'database_validation_report.json'
        with open(report_path, 'w') as f:
            json.dump(self.validation_report, f, indent=2)
            
        print(f"Validation report saved to: {report_path}")
        
        return self.validation_report
        
    def print_summary(self):
        """Print a summary of the validation results"""
        print("\n" + "="*60)
        print("DATABASE SCHEMA VALIDATION SUMMARY")
        print("="*60)
        print(f"Database: {self.db_path}")
        print(f"Total tables found: {len(self.existing_tables)}")
        print(f"Missing tables: {len(self.missing_tables)}")
        print(f"Missing columns: {sum(len(cols) for cols in self.missing_columns.values())}")
        print("="*60)
        
        if self.missing_tables:
            print("\n🔴 MISSING TABLES:")
            for table in self.missing_tables:
                print(f"  - {table}")
                
        if self.missing_columns:
            print("\n🔴 MISSING COLUMNS:")
            for table, columns in self.missing_columns.items():
                print(f"  - {table}: {', '.join(columns)}")
                
        if not self.missing_tables and not self.missing_columns:
            print("\n✅ ALL TABLES AND COLUMNS PRESENT - NO GAPS FOUND!")
            
        print("\n" + "="*60)


def main():
    """Main execution function"""
    print("🚀 Starting Database Schema Validation...")
    print("="*60)
    
    validator = DatabaseSchemaValidator()
    
    # Phase 1: Extract existing tables
    validator.extract_existing_tables()
    
    # Phase 2: Identify missing tables
    validator.identify_missing_tables()
    
    # Phase 3: Identify missing columns
    validator.identify_missing_columns()
    
    # Phase 4: Generate validation report
    validator.generate_validation_report()
    
    # Phase 5: Print summary
    validator.print_summary()
    
    print("\n✅ Schema validation complete!")
    print("📄 Report saved to: database_validation_report.json")


if __name__ == "__main__":
    main()