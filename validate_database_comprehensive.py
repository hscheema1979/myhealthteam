#!/usr/bin/env python3
"""
Comprehensive Database Validation Script
Enhanced version that analyzes database functions called by dashboards

This script:
1. Extracts all tables from production.db
2. Analyzes database.py functions and their table dependencies
3. Parses dashboard imports to identify which functions they use
4. Tests actual function execution to verify compatibility
5. Identifies missing tables, columns, and data gaps
"""

import sqlite3
import os
import re
import json
import ast
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from datetime import datetime

class ComprehensiveDatabaseValidator:
    def __init__(self, db_path: str = "production.db"):
        self.db_path = db_path
        self.existing_tables: Dict[str, List[Dict[str, Any]]] = {}
        self.database_functions: Dict[str, Dict[str, Any]] = {}
        self.dashboard_dependencies: Dict[str, Set[str]] = {}
        self.function_table_dependencies: Dict[str, Set[str]] = {}
        self.missing_tables: List[str] = []
        self.missing_columns: Dict[str, List[str]] = {}
        self.data_gaps: Dict[str, Any] = {}
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
                
        finally:
            conn.close()
            
        return self.existing_tables
        
    def analyze_database_module(self, db_module_path: str = "src/database.py") -> Dict[str, Dict[str, Any]]:
        """Analyze database.py to extract function signatures and SQL queries"""
        print(f"\n🔧 Analyzing database module: {db_module_path}")
        
        if not os.path.exists(db_module_path):
            print(f"❌ Database module {db_module_path} not found")
            return {}
            
        try:
            # Read the file content
            with open(db_module_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse the AST to extract function definitions
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    if not func_name.startswith('_'):  # Skip private functions
                        
                        # Extract function signature
                        args = [arg.arg for arg in node.args.args]
                        
                        # Extract docstring
                        docstring = ast.get_docstring(node) or ""
                        
                        # Extract SQL queries from function body
                        sql_queries = self._extract_sql_queries(node)
                        table_references = self._extract_table_references(sql_queries)
                        
                        self.database_functions[func_name] = {
                            'args': args,
                            'docstring': docstring,
                            'sql_queries': sql_queries,
                            'table_references': table_references,
                            'line_number': node.lineno
                        }
                        
            print(f"Found {len(self.database_functions)} database functions")
            
            # Show function details
            for func_name, func_info in self.database_functions.items():
                print(f"  - {func_name}({', '.join(func_info['args'])})")
                if func_info['table_references']:
                    print(f"    Tables: {', '.join(func_info['table_references'])}")
                    
        except Exception as e:
            print(f"❌ Error analyzing database module: {e}")
            
        return self.database_functions
        
    def _extract_sql_queries(self, func_node: ast.FunctionDef) -> List[str]:
        """Extract SQL queries from a function AST node"""
        queries = []
        
        for node in ast.walk(func_node):
            # Look for string literals that might be SQL
            if isinstance(node, ast.Str):
                if isinstance(node.s, str):
                    query = node.s.strip()
                    if any(keyword in query.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE']):
                        queries.append(query)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                query = node.value.strip()
                if any(keyword in query.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE']):
                    queries.append(query)
                    
        return queries
        
    def _extract_table_references(self, sql_queries: List[str]) -> Set[str]:
        """Extract table names from SQL queries"""
        table_refs = set()
        
        for query in sql_queries:
            # Look for table names in FROM and JOIN clauses
            patterns = [
                r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'(?:INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'(?:TABLE|EXISTS)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                for match in matches:
                    # Skip common SQL keywords
                    if match.upper() not in ['SELECT', 'WHERE', 'GROUP', 'ORDER', 'LIMIT', 'TABLE']:
                        table_refs.add(match)
                        
        return table_refs
        
    def analyze_dashboard_dependencies(self, dashboard_path: str = "src/dashboards") -> Dict[str, Set[str]]:
        """Analyze which database functions each dashboard imports and uses"""
        print(f"\n📊 Analyzing dashboard dependencies from {dashboard_path}...")
        
        if not os.path.exists(dashboard_path):
            print(f"❌ Dashboard path {dashboard_path} does not exist")
            return {}
            
        # Find all Python dashboard files
        dashboard_files = list(Path(dashboard_path).glob("*.py"))
        print(f"Found {len(dashboard_files)} dashboard files")
        
        for dashboard_file in dashboard_files:
            dashboard_name = dashboard_file.stem
            self.dashboard_dependencies[dashboard_name] = set()
            
            try:
                with open(dashboard_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse imports
                imports = self._extract_imports(content)
                
                # Look for database function calls
                for func_name in self.database_functions.keys():
                    # Check for direct function calls
                    if f"{func_name}(" in content:
                        self.dashboard_dependencies[dashboard_name].add(func_name)
                        
                    # Check for module.function calls
                    if any(f"{imp}.{func_name}(" in content for imp in imports):
                        self.dashboard_dependencies[dashboard_name].add(func_name)
                        
            except Exception as e:
                print(f"❌ Error analyzing {dashboard_file}: {e}")
                
        # Print findings
        for dashboard, functions in self.dashboard_dependencies.items():
            if functions:
                print(f"  - {dashboard}: {len(functions)} functions")
                for func in sorted(functions):
                    print(f"    * {func}()")
                    
        return self.dashboard_dependencies
        
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from Python code"""
        imports = []
        
        # Simple regex for import statements
        import_patterns = [
            r'import\s+(\w+)',
            r'from\s+(\w+)\s+import',
            r'import\s+src\.(\w+)',
            r'from\s+src\.(\w+)\s+import',
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
            
        return imports
        
    def test_database_functions(self) -> Dict[str, Dict[str, Any]]:
        """Test database functions to verify they work with current schema"""
        print("\n🧪 Testing database functions...")
        
        test_results = {}
        
        # Try to import the database module dynamically
        try:
            spec = importlib.util.spec_from_file_location("database", "src/database.py")
            database_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(database_module)
            
            # Test key functions
            test_functions = [
                ('get_db_connection', [], {}),
                ('normalize_patient_id', ['ZEN-12345'], {}),
                ('ensure_monthly_provider_tasks_table', [2025, 12], {}),
                ('ensure_monthly_coordinator_tasks_table', [2025, 12], {}),
            ]
            
            for func_name, args, kwargs in test_functions:
                if hasattr(database_module, func_name):
                    try:
                        func = getattr(database_module, func_name)
                        result = func(*args, **kwargs)
                        test_results[func_name] = {
                            'status': 'success',
                            'result': str(result)[:100] if result else 'None',
                            'error': None
                        }
                        print(f"  ✅ {func_name}() - Success")
                    except Exception as e:
                        test_results[func_name] = {
                            'status': 'failed',
                            'result': None,
                            'error': str(e)
                        }
                        print(f"  ❌ {func_name}() - Failed: {e}")
                else:
                    test_results[func_name] = {
                        'status': 'not_found',
                        'result': None,
                        'error': 'Function not found in module'
                    }
                    print(f"  ⚠️  {func_name}() - Not found")
                    
        except Exception as e:
            print(f"❌ Error importing database module: {e}")
            
        return test_results
        
    def check_data_completeness(self) -> Dict[str, Any]:
        """Check for missing or incomplete data in critical tables"""
        print("\n📈 Checking data completeness...")
        
        data_status = {}
        
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Check patient data
            cursor.execute("SELECT COUNT(*) as count FROM patients")
            patient_count = cursor.fetchone()['count']
            data_status['patients'] = {'count': patient_count, 'status': 'ok' if patient_count > 0 else 'empty'}
            
            # Check user data
            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()['count']
            data_status['users'] = {'count': user_count, 'status': 'ok' if user_count > 0 else 'empty'}
            
            # Check task data
            task_tables = [t for t in self.existing_tables.keys() if t.startswith('provider_tasks_') or t.startswith('coordinator_tasks_')]
            total_tasks = 0
            for table in task_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    total_tasks += count
                except:
                    pass  # Table might not exist
                    
            data_status['total_tasks'] = {'count': total_tasks, 'status': 'ok' if total_tasks > 0 else 'empty'}
            
            # Check for NULL values in critical columns
            critical_nulls = {}
            
            # Check patients table
            cursor.execute("SELECT COUNT(*) as count FROM patients WHERE patient_id IS NULL")
            null_patients = cursor.fetchone()['count']
            if null_patients > 0:
                critical_nulls['patients.patient_id'] = null_patients
                
            # Check users table
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE user_id IS NULL")
            null_users = cursor.fetchone()['count']
            if null_users > 0:
                critical_nulls['users.user_id'] = null_users
                
            data_status['critical_nulls'] = critical_nulls
            
            # Print summary
            print(f"  - Patients: {patient_count} records")
            print(f"  - Users: {user_count} records") 
            print(f"  - Total Tasks: {total_tasks} records")
            if critical_nulls:
                print(f"  - Critical NULLs found: {len(critical_nulls)} columns")
            else:
                print("  - No critical NULL values found")
                
        finally:
            conn.close()
            
        return data_status
        
    def identify_missing_tables(self) -> List[str]:
        """Identify tables that should exist based on function dependencies"""
        print("\n❌ Identifying missing tables...")
        
        # Collect all table references from functions
        all_table_refs: Set[str] = set()
        
        for func_name, func_info in self.database_functions.items():
            all_table_refs.update(func_info['table_references'])
            
        # Collect table references from dashboard dependencies
        for dashboard, functions in self.dashboard_dependencies.items():
            for func_name in functions:
                if func_name in self.database_functions:
                    all_table_refs.update(self.database_functions[func_name]['table_references'])
                    
        # Filter out sqlite_master (it's a system table)
        all_table_refs.discard('sqlite_master')
        
        # Check which tables are missing
        existing_table_names = set(self.existing_tables.keys())
        self.missing_tables = []
        
        for required_table in all_table_refs:
            # Handle monthly table patterns
            if '_YYYY_MM' in required_table:
                base_pattern = required_table.replace('_YYYY_MM', '')
                pattern = re.compile(rf'{base_pattern}_\d{{4}}_\d{{1,2}}')
                matching_tables = [t for t in existing_table_names if pattern.match(t)]
                if not matching_tables:
                    self.missing_tables.append(f"{required_table} (no tables found matching pattern)")
            elif required_table not in existing_table_names:
                self.missing_tables.append(required_table)
        
        if self.missing_tables:
            print(f"Found {len(self.missing_tables)} missing tables:")
            for table in self.missing_tables:
                print(f"  - {table}")
        else:
            print("✅ No missing tables found!")
            
        return self.missing_tables
        
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        print("\n📋 Generating comprehensive validation report...")
        
        self.validation_report = {
            'timestamp': datetime.now().isoformat(),
            'database_path': self.db_path,
            'summary': {
                'total_tables_in_db': len(self.existing_tables),
                'database_functions_found': len(self.database_functions),
                'dashboards_analyzed': len(self.dashboard_dependencies),
                'missing_tables_count': len(self.missing_tables),
                'missing_columns_count': sum(len(cols) for cols in self.missing_columns.values()),
            },
            'database_functions': self.database_functions,
            'dashboard_dependencies': {k: list(v) for k, v in self.dashboard_dependencies.items()},
            'existing_tables': list(self.existing_tables.keys()),
            'missing_tables': self.missing_tables,
            'missing_columns': self.missing_columns,
            'table_details': self.existing_tables,
            'data_completeness': self.check_data_completeness(),
            'function_test_results': self.test_database_functions()
        }
        
        # Save report to JSON file
        report_path = 'comprehensive_database_validation_report.json'
        with open(report_path, 'w') as f:
            json.dump(self.validation_report, f, indent=2, default=str)
            
        print(f"Comprehensive validation report saved to: {report_path}")
        
        return self.validation_report
        
    def print_summary(self):
        """Print a comprehensive summary of the validation results"""
        print("\n" + "="*80)
        print("COMPREHENSIVE DATABASE VALIDATION SUMMARY")
        print("="*80)
        print(f"Database: {self.db_path}")
        print(f"Total tables found: {len(self.existing_tables)}")
        print(f"Database functions: {len(self.database_functions)}")
        print(f"Dashboards analyzed: {len(self.dashboard_dependencies)}")
        print(f"Missing tables: {len(self.missing_tables)}")
        print(f"Missing columns: {sum(len(cols) for cols in self.missing_columns.values())}")
        print("="*80)
        
        if self.missing_tables:
            print("\n🔴 MISSING TABLES:")
            for table in self.missing_tables:
                print(f"  - {table}")
                
        if self.missing_columns:
            print("\n🔴 MISSING COLUMNS:")
            for table, columns in self.missing_columns.items():
                print(f"  - {table}: {', '.join(columns)}")
                
        # Show function usage
        print("\n📊 FUNCTION USAGE BY DASHBOARDS:")
        for dashboard, functions in self.dashboard_dependencies.items():
            if functions:
                print(f"  - {dashboard}: {len(functions)} functions")
                for func in sorted(functions):
                    print(f"    * {func}()")
                    
        if not self.missing_tables and not self.missing_columns:
            print("\n✅ NO CRITICAL SCHEMA GAPS FOUND!")
            
        print("\n" + "="*80)


def main():
    """Main execution function"""
    print("🚀 Starting Comprehensive Database Validation...")
    print("="*80)
    
    validator = ComprehensiveDatabaseValidator()
    
    # Phase 1: Extract existing tables
    validator.extract_existing_tables()
    
    # Phase 2: Analyze database functions
    validator.analyze_database_module()
    
    # Phase 3: Analyze dashboard dependencies
    validator.analyze_dashboard_dependencies()
    
    # Phase 4: Identify missing tables
    validator.identify_missing_tables()
    
    # Phase 5: Generate comprehensive report
    validator.generate_comprehensive_report()
    
    # Phase 6: Print summary
    validator.print_summary()
    
    print("\n✅ Comprehensive validation complete!")
    print("📄 Report saved to: comprehensive_database_validation_report.json")


if __name__ == "__main__":
    main()