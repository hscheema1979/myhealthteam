#!/usr/bin/env python3
"""
Monitoring and Alerting Setup for MyHealthTeam CI/CD Pipeline

This script sets up monitoring, health checks, and alerting for the application
to support continuous deployment and reliability monitoring.
"""

import sqlite3
import json
import time
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import subprocess
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HealthChecker:
    """Comprehensive health checking for the MyHealthTeam application"""
    
    def __init__(self, db_path: str = "production.db"):
        self.db_path = db_path
        self.health_status = {}
        
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and integrity"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Basic connectivity test
            cursor.execute("SELECT 1")
            
            # Check critical tables
            critical_tables = [
                'workflow_templates', 'users', 'patients', 
                'workflow_instances', 'workflow_steps'
            ]
            
            table_status = {}
            for table in critical_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_status[table] = {
                        'status': 'healthy',
                        'record_count': count
                    }
                except sqlite3.OperationalError as e:
                    table_status[table] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            conn.close()
            
            return {
                'status': 'healthy',
                'database_path': self.db_path,
                'tables': table_status,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def check_application_files(self) -> Dict[str, Any]:
        """Check critical application files exist and are readable"""
        critical_files = [
            'app.py',
            'src/database.py',
            'src/auth_module.py',
            'src/workflow_engine.py',
            'requirements.txt'
        ]
        
        file_status = {}
        for file_path in critical_files:
            try:
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    file_status[file_path] = {
                        'status': 'exists',
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                else:
                    file_status[file_path] = {
                        'status': 'missing'
                    }
            except Exception as e:
                file_status[file_path] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        all_healthy = all(
            status['status'] == 'exists' 
            for status in file_status.values()
        )
        
        return {
            'status': 'healthy' if all_healthy else 'unhealthy',
            'files': file_status,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def check_workflow_system(self) -> Dict[str, Any]:
        """Check workflow system functionality"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check workflow templates
            cursor.execute("SELECT COUNT(*) FROM workflow_templates WHERE is_active = 1")
            active_templates = cursor.fetchone()[0]
            
            # Check recent workflow instances
            cursor.execute("""
                SELECT COUNT(*) FROM workflow_instances 
                WHERE created_at > datetime('now', '-24 hours')
            """)
            recent_instances = cursor.fetchone()[0]
            
            # Check for stuck workflows (running for more than 24 hours)
            cursor.execute("""
                SELECT COUNT(*) FROM workflow_instances 
                WHERE status = 'running' 
                AND created_at < datetime('now', '-24 hours')
            """)
            stuck_workflows = cursor.fetchone()[0]
            
            conn.close()
            
            status = 'healthy'
            issues = []
            
            if active_templates == 0:
                issues.append("No active workflow templates found")
                status = 'warning'
            
            if stuck_workflows > 0:
                issues.append(f"{stuck_workflows} workflows stuck for >24 hours")
                status = 'unhealthy'
            
            return {
                'status': status,
                'active_templates': active_templates,
                'recent_instances_24h': recent_instances,
                'stuck_workflows': stuck_workflows,
                'issues': issues,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status"""
        logger.info("Starting comprehensive health check...")
        
        health_report = {
            'overall_status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        # Run individual checks
        checks = {
            'database': self.check_database_health,
            'application_files': self.check_application_files,
            'workflow_system': self.check_workflow_system
        }
        
        unhealthy_checks = []
        warning_checks = []
        
        for check_name, check_func in checks.items():
            try:
                result = check_func()
                health_report['checks'][check_name] = result
                
                if result['status'] == 'unhealthy':
                    unhealthy_checks.append(check_name)
                elif result['status'] == 'warning':
                    warning_checks.append(check_name)
                    
            except Exception as e:
                logger.error(f"Health check {check_name} failed: {e}")
                health_report['checks'][check_name] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
                unhealthy_checks.append(check_name)
        
        # Determine overall status
        if unhealthy_checks:
            health_report['overall_status'] = 'unhealthy'
            health_report['unhealthy_checks'] = unhealthy_checks
        elif warning_checks:
            health_report['overall_status'] = 'warning'
            health_report['warning_checks'] = warning_checks
        
        logger.info(f"Health check completed. Overall status: {health_report['overall_status']}")
        return health_report

class DeploymentMonitor:
    """Monitor deployments and track metrics"""
    
    def __init__(self, db_path: str = "production.db"):
        self.db_path = db_path
        self.setup_monitoring_tables()
    
    def setup_monitoring_tables(self):
        """Create monitoring tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Deployment tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deployments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deployment_id TEXT UNIQUE NOT NULL,
                    commit_sha TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    status TEXT NOT NULL,
                    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deployed_by TEXT,
                    rollback_deployment_id TEXT,
                    metadata TEXT
                )
            """)
            
            # Health check history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    overall_status TEXT NOT NULL,
                    check_results TEXT NOT NULL,
                    environment TEXT DEFAULT 'production'
                )
            """)
            
            # Performance metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    environment TEXT DEFAULT 'production',
                    metadata TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Monitoring tables created/verified successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup monitoring tables: {e}")
    
    def record_deployment(self, deployment_id: str, commit_sha: str, 
                         environment: str, status: str, deployed_by: str = None,
                         metadata: Dict = None):
        """Record a deployment event"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO deployments 
                (deployment_id, commit_sha, environment, status, deployed_by, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                deployment_id, commit_sha, environment, status, 
                deployed_by, json.dumps(metadata) if metadata else None
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Recorded deployment: {deployment_id} ({status})")
            
        except Exception as e:
            logger.error(f"Failed to record deployment: {e}")
    
    def record_health_check(self, health_report: Dict[str, Any], environment: str = 'production'):
        """Record health check results"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO health_checks 
                (overall_status, check_results, environment)
                VALUES (?, ?, ?)
            """, (
                health_report['overall_status'],
                json.dumps(health_report),
                environment
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Recorded health check: {health_report['overall_status']}")
            
        except Exception as e:
            logger.error(f"Failed to record health check: {e}")
    
    def get_deployment_history(self, environment: str = 'production', limit: int = 10) -> List[Dict]:
        """Get recent deployment history"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM deployments 
                WHERE environment = ?
                ORDER BY deployed_at DESC
                LIMIT ?
            """, (environment, limit))
            
            deployments = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return deployments
            
        except Exception as e:
            logger.error(f"Failed to get deployment history: {e}")
            return []

def setup_monitoring_environment():
    """Setup monitoring environment and directories"""
    directories = ['logs', 'backups', 'deployments', 'monitoring']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created/verified directory: {directory}")

def run_monitoring_cycle():
    """Run a complete monitoring cycle"""
    logger.info("Starting monitoring cycle...")
    
    # Setup environment
    setup_monitoring_environment()
    
    # Initialize components
    health_checker = HealthChecker()
    deployment_monitor = DeploymentMonitor()
    
    # Run health check
    health_report = health_checker.run_comprehensive_health_check()
    
    # Record health check
    deployment_monitor.record_health_check(health_report)
    
    # Save health report to file
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    health_file = f"monitoring/health_report_{timestamp}.json"
    
    with open(health_file, 'w') as f:
        json.dump(health_report, f, indent=2)
    
    logger.info(f"Health report saved to: {health_file}")
    
    # Print summary
    print("\n" + "="*50)
    print("MYHEALTHTEAM MONITORING SUMMARY")
    print("="*50)
    print(f"Overall Status: {health_report['overall_status'].upper()}")
    print(f"Timestamp: {health_report['timestamp']}")
    
    for check_name, check_result in health_report['checks'].items():
        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'unhealthy': '❌',
            'error': '💥'
        }.get(check_result['status'], '❓')
        
        print(f"{status_emoji} {check_name.replace('_', ' ').title()}: {check_result['status']}")
    
    print("="*50)
    
    return health_report

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='MyHealthTeam Monitoring Setup')
    parser.add_argument('--action', choices=['setup', 'health-check', 'monitor'], 
                       default='monitor', help='Action to perform')
    parser.add_argument('--db-path', default='production.db', 
                       help='Database path')
    parser.add_argument('--environment', default='production',
                       help='Environment name')
    
    args = parser.parse_args()
    
    if args.action == 'setup':
        setup_monitoring_environment()
        print("✅ Monitoring environment setup complete")
        
    elif args.action == 'health-check':
        health_checker = HealthChecker(args.db_path)
        health_report = health_checker.run_comprehensive_health_check()
        print(json.dumps(health_report, indent=2))
        
    elif args.action == 'monitor':
        health_report = run_monitoring_cycle()
        
        # Exit with appropriate code
        if health_report['overall_status'] == 'unhealthy':
            sys.exit(1)
        elif health_report['overall_status'] == 'warning':
            sys.exit(2)
        else:
            sys.exit(0)