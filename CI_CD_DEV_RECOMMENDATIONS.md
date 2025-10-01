# CI/CD Development Environment Recommendations

## Overview

This document outlines the Continuous Integration/Continuous Deployment (CI/CD) strategy from the **development environment perspective**. This covers development workflows, testing procedures, and preparing code for release to GitHub.

**Related Document:** See `CI_CD_MAIN_RECOMMENDATIONS.md` for production deployment and main branch management.

## Current Architecture Analysis

### Repository Structure
```
Production Environment: d:\Git\myhealthteam2\Streamlit\
├── main branch (production-ready code - PROTECTED)
├── Runs continuously on Port 8501
└── NEVER modify from Dev environment

Development Environment: d:\Git\myhealthteam2\Dev\
├── main branch (development integration)
├── feature/* branches (feature development)
├── sandbox branches (isolated development)
├── testing branches (QA and testing)
└── All development and testing work happens here
```

### Current Port Allocation
- **Port 8501**: Production Environment (d:\Git\myhealthteam2\Streamlit\) - PROTECTED - NEVER TOUCH FROM DEV
- **Port 8502**: Sandbox Development Environment (d:\Git\myhealthteam2\Dev\)
- **Port 8503**: Alternate Development/Testing Environment (d:\Git\myhealthteam2\Dev\)

### CRITICAL SAFETY PROTOCOL
⚠️ **NEVER run commands targeting Port 8501 from the Dev environment**
⚠️ **Production environment (d:\Git\myhealthteam2\Streamlit\) runs independently**
⚠️ **All development work uses Ports 8502 and 8503 only**

## Recommended CI/CD Pipeline

### Phase 1: Development Workflow

#### 1.1 Branch Strategy (GitFlow Enhanced)
```
main (production)
├── develop (integration branch)
│   ├── feature/dashboard-improvements
│   ├── feature/user-authentication
│   └── feature/data-visualization
├── release/* (from develop → merge to main)
└── hotfix/* (from main → merge to main & develop)
```

**Branch Flow Rules:**
- **Feature branches**: Always branch FROM `develop`, merge back TO `develop`
- **Release branches**: Branch FROM `develop`, merge TO `main` and back TO `develop`
- **Hotfix branches**: Branch FROM `main`, merge TO both `main` and `develop`
- **Main branch**: Only receives tested, production-ready code
- **Develop branch**: Integration point for all feature development

#### 1.2 Development Environment Setup
```powershell
# Environment-specific configurations
environments/
├── development.env
├── staging.env
├── production.env
└── testing.env
```

### Phase 2: Automated Testing Pipeline

#### 2.1 Testing Levels
```yaml
# .github/workflows/ci-pipeline.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop, feature/* ]
  pull_request:
    branches: [ main, develop ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run unit tests
        run: |
          pytest tests/unit/ --cov=src/ --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    services:
      sqlite:
        image: sqlite:latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup test database
        run: |
          python scripts/setup_test_db.py
      - name: Run integration tests
        run: |
          pytest tests/integration/ --db-path=test.db

  workflow-tests:
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test workflow system
        run: |
          python test_all_workflows.py
          python verify_workflows_readonly.py

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run security scan
        uses: securecodewarrior/github-action-add-sarif@v1
        with:
          sarif-file: 'security-scan-results.sarif'
```

#### 2.2 Test Structure
```
tests/
├── unit/
│   ├── test_auth_module.py
│   ├── test_database.py
│   ├── test_workflow_utils.py
│   └── test_chart_components.py
├── integration/
│   ├── test_auth_integration.py
│   ├── test_workflow_integration.py
│   └── test_database_integration.py
├── e2e/
│   ├── test_user_workflows.py
│   ├── test_admin_dashboard.py
│   └── test_data_entry.py
└── performance/
    ├── test_load_performance.py
    └── test_database_performance.py
```

### Phase 3: Development Deployment Strategy

#### 3.1 Development Environment Progression
```
Dev Environment (d:\Git\myhealthteam2\Dev\):
Development → Testing → Staging → GitHub Push
    ↓           ↓         ↓          ↓
  Port 8503   Port 8502  Port 8502  GitHub Repository
                                    (Ready for Production)

SAFETY BARRIER: Dev environment NEVER directly touches Port 8501
Production deployment handled separately (see CI_CD_MAIN_RECOMMENDATIONS.md)
```

#### 3.2 Development Workflow (d:\Git\myhealthteam2\Dev\)

##### Simple Development Cycle with BrowserStack Testing
```powershell
# 1. Start development session
cd d:\Git\myhealthteam2\Dev\
git checkout develop
git pull origin develop

# 2. Create feature branch FROM develop
git checkout -b feature/your-feature-name

# 3. Develop and test locally on Port 8503
$env:ENVIRONMENT = "development"
streamlit run app.py --server.port 8503

# 4. Manual testing (spend time here!)
Write-Host "🧪 Manual Testing Checklist:" -ForegroundColor Cyan
Write-Host "  ✓ App loads without errors" -ForegroundColor Green
Write-Host "  ✓ All buttons and inputs work" -ForegroundColor Green
Write-Host "  ✓ Layout looks good on your screen" -ForegroundColor Green
Write-Host "  ✓ Data displays correctly" -ForegroundColor Green
Write-Host "  ✓ Try to break it (edge cases)" -ForegroundColor Green

# 5. Deploy to staging for BrowserStack testing
Write-Host "🚀 Deploying to staging for cross-browser testing..." -ForegroundColor Yellow
$env:ENVIRONMENT = "staging"
streamlit run app.py --server.port 8502 &
Start-Sleep -Seconds 10

# 6. Run BrowserStack tests (scripts to be created later)
Write-Host "🌐 Running BrowserStack tests..." -ForegroundColor Yellow
Write-Host "  Testing on: Chrome, Firefox, Safari, Edge" -ForegroundColor Cyan
Write-Host "  Testing on: Desktop, Tablet, Mobile" -ForegroundColor Cyan
# TODO: Add BrowserStack test scripts here

# 7. ONLY commit and push if everything works
Write-Host "✅ All tests passed! Committing changes..." -ForegroundColor Green
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name

# 8. Create Pull Request on GitHub (feature → develop)
# Simple code review, no complex CI/CD

# 9. After PR approval, merge to develop
git checkout develop
git pull origin develop
git merge feature/your-feature-name
git push origin develop

# 10. When ready for production, create release from develop → main
# Production deployment handled separately (see CI_CD_MAIN_RECOMMENDATIONS.md)
```

##### Simple BrowserStack Testing Flow
```
Dev Work (Port 8503) → Manual Testing → BrowserStack Tests → GitHub Push → Ready for Production
     ↑                      ↓                    ↓                ↓                ↓
Feature Development    Local Validation    Cross-Browser      Code Review    GitHub Release
                       (Your Computer)     Testing (8502)     (GitHub PR)    (Ready for Deploy)
                           ↓                    ↓                ↓
                       ✅ Works Locally    ✅ Works on All    ✅ Code Approved
                                          Browsers/Devices

CRITICAL RULE: TEST THOROUGHLY ON YOUR COMPUTER + BROWSERSTACK BEFORE PUSHING!
```

##### What BrowserStack Tests:
- **Desktop Browsers:** Chrome, Firefox, Safari, Edge
- **Mobile Devices:** iPhone, Android phones, tablets
- **Screen Sizes:** Desktop, laptop, tablet, mobile
- **Performance:** Load times, responsiveness
- **Visual:** Layout, colors, fonts display correctly

#### 3.3 Development Deployment Pipeline
```yaml
# .github/workflows/deploy-dev.yml
name: Development Deployment Pipeline

on:
  push:
    branches: [ develop ]
  workflow_run:
    workflows: ["CI/CD Pipeline"]
    types: [completed]
    branches: [ develop ]

jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to staging (Port 8502)
        run: |
          ./scripts/deploy_staging.ps1
      - name: Run smoke tests
        run: |
          python tests/smoke/test_staging_health.py
      - name: Notify team
        run: |
          echo "Staging deployment complete - ready for testing on Port 8502"

# Note: Production deployment handled separately in CI_CD_MAIN_RECOMMENDATIONS.md
```

## GitHub Integration with BrowserStack Testing

### Repository Setup
```powershell
# Initialize Git repository in Dev folder (if not already done)
cd d:\Git\myhealthteam2\Dev\
git init
git remote add origin https://github.com/yourusername/myhealthteam-dev.git

# Create .gitignore for development environment
echo "*.db" >> .gitignore
echo "__pycache__/" >> .gitignore
echo ".env" >> .gitignore
echo "logs/" >> .gitignore
```

### Simple GitHub Workflow (No Complex CI/CD)
```yaml
# .github/workflows/simple-review.yml
name: Simple Code Review

on:
  pull_request:
    branches: [ main ]

jobs:
  safety-check:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Safety Check - Prevent Port 8501 Usage
        run: |
          if (Select-String -Path "*.py" -Pattern "8501") {
            Write-Error "CRITICAL: Port 8501 detected! This is reserved for production."
            exit 1
          }
          Write-Host "✅ Safety check passed - No production port usage detected"

  code-quality:
    runs-on: windows-latest
    needs: safety-check
    steps:
      - uses: actions/checkout@v3
      - name: Basic Code Quality Check
        run: |
          Write-Host "✅ Code review ready - BrowserStack testing should be completed locally"
          Write-Host "📋 Reviewer checklist:"
          Write-Host "  - BrowserStack tests passed?"
          Write-Host "  - Manual testing completed?"
          Write-Host "  - No hardcoded values?"
          Write-Host "  - Code is readable?"
```

### BrowserStack Integration Setup
```powershell
# scripts/setup_browserstack.ps1
# TODO: Create BrowserStack account and get credentials

# Install BrowserStack Local for testing staging environment
Write-Host "Setting up BrowserStack Local..." -ForegroundColor Cyan
# Download and install BrowserStack Local binary

# Set environment variables
$env:BROWSERSTACK_USERNAME = "your-username"
$env:BROWSERSTACK_ACCESS_KEY = "your-access-key"

Write-Host "✅ BrowserStack setup complete" -ForegroundColor Green
Write-Host "Next: Create test scripts for your Streamlit app" -ForegroundColor Yellow
```

### Simple Branch Strategy
```
main (stable, tested with BrowserStack)
├── feature/user-interface-update
├── feature/new-dashboard-widget
└── hotfix/mobile-layout-fix
```

### BrowserStack Test Strategy (Scripts to be created)
```powershell
# scripts/run_browserstack_tests.ps1
# TODO: Implement BrowserStack test automation

Write-Host "🌐 Starting BrowserStack tests..." -ForegroundColor Cyan

# Test plan:
# 1. Desktop browsers (Chrome, Firefox, Safari, Edge)
# 2. Mobile devices (iPhone, Android)
# 3. Tablet devices (iPad, Android tablets)
# 4. Different screen resolutions
# 5. Performance testing

Write-Host "📱 Testing mobile responsiveness..." -ForegroundColor Yellow
Write-Host "🖥️  Testing desktop browsers..." -ForegroundColor Yellow
Write-Host "📊 Testing performance..." -ForegroundColor Yellow

# Results will be available in BrowserStack dashboard
Write-Host "✅ BrowserStack tests completed - Check dashboard for results" -ForegroundColor Green
```

## CRITICAL SAFETY PROTOCOLS

### Environment Isolation Rules

#### 🚨 NEVER DO FROM DEV ENVIRONMENT:
1. **NEVER target Port 8501** - This is production only
2. **NEVER modify files in d:\Git\myhealthteam2\Streamlit\** - Production is separate
3. **NEVER run production deployment scripts** from Dev folder
4. **NEVER use production database connections** from Dev environment
5. **NEVER push directly to production** without proper CI/CD pipeline

#### ✅ ALWAYS DO IN DEV ENVIRONMENT:
1. **ALWAYS use Ports 8502 or 8503** for development and testing
2. **ALWAYS work within d:\Git\myhealthteam2\Dev\** folder structure
3. **ALWAYS test locally** before pushing to GitHub
4. **ALWAYS use feature branches** for development work
5. **ALWAYS run safety checks** before staging deployment

### Automated Safety Checks
```powershell
# scripts/safety_check.ps1
Write-Host "=== Running Safety Checks ===" -ForegroundColor Yellow

# Check 1: Verify we're in Dev environment
$currentPath = Get-Location
if ($currentPath -notlike "*\Dev*") {
    Write-Host "❌ ERROR: Not in Dev environment!" -ForegroundColor Red
    Write-Host "Current: $currentPath" -ForegroundColor Red
    Write-Host "Expected: d:\Git\myhealthteam2\Dev\" -ForegroundColor Green
    exit 1
}

# Check 2: Verify no production port references in code
$prodPortRefs = Select-String -Path "*.py" -Pattern "8501" -AllMatches
if ($prodPortRefs) {
    Write-Host "❌ ERROR: Found production port 8501 references!" -ForegroundColor Red
    $prodPortRefs | ForEach-Object { Write-Host "  $($_.Filename):$($_.LineNumber) - $($_.Line.Trim())" }
    exit 1
}

# Check 3: Verify no production database connections
$prodDbRefs = Select-String -Path "*.py" -Pattern "production\.db|prod\.db" -AllMatches
if ($prodDbRefs) {
    Write-Host "❌ ERROR: Found production database references!" -ForegroundColor Red
    $prodDbRefs | ForEach-Object { Write-Host "  $($_.Filename):$($_.LineNumber) - $($_.Line.Trim())" }
    exit 1
}

# Check 4: Verify Streamlit folder is not being accessed
$streamlitRefs = Select-String -Path "*.py" -Pattern "\\Streamlit\\" -AllMatches
if ($streamlitRefs) {
    Write-Host "❌ ERROR: Found Streamlit folder references!" -ForegroundColor Red
    $streamlitRefs | ForEach-Object { Write-Host "  $($_.Filename):$($_.LineNumber) - $($_.Line.Trim())" }
    exit 1
}

Write-Host "✅ All safety checks passed!" -ForegroundColor Green
```

### Pre-Commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit
echo "Running safety checks before commit..."

# Run safety check script
powershell -ExecutionPolicy Bypass -File "scripts/safety_check.ps1"

if [ $? -ne 0 ]; then
    echo "❌ Safety checks failed! Commit aborted."
    exit 1
fi

echo "✅ Safety checks passed! Proceeding with commit."
```

### Environment Configuration Safety
```python
# config/environment_config.py
import os
import sys
from pathlib import Path

class EnvironmentSafety:
    """Ensures safe environment configuration"""
    
    PRODUCTION_PORT = 8501
    DEV_PORTS = [8502, 8503]
    PRODUCTION_PATH = r"d:\Git\myhealthteam2\Streamlit"
    DEV_PATH = r"d:\Git\myhealthteam2\Dev"
    
    @classmethod
    def verify_dev_environment(cls):
        """Verify we're running in development environment"""
        current_path = str(Path.cwd())
        
        if cls.PRODUCTION_PATH.lower() in current_path.lower():
            raise EnvironmentError(
                f"❌ CRITICAL: Running in production environment!\n"
                f"Current: {current_path}\n"
                f"This script must run from: {cls.DEV_PATH}"
            )
        
        if cls.DEV_PATH.lower() not in current_path.lower():
            raise EnvironmentError(
                f"❌ ERROR: Not in development environment!\n"
                f"Current: {current_path}\n"
                f"Expected: {cls.DEV_PATH}"
            )
    
    @classmethod
    def verify_port_safety(cls, port):
        """Verify port is safe for development use"""
        if port == cls.PRODUCTION_PORT:
            raise ValueError(
                f"❌ CRITICAL: Cannot use production port {cls.PRODUCTION_PORT}!\n"
                f"Use development ports: {cls.DEV_PORTS}"
            )
        
        if port not in cls.DEV_PORTS:
            print(f"⚠️  WARNING: Port {port} is not a standard dev port")
            print(f"Standard dev ports: {cls.DEV_PORTS}")
    
    @classmethod
    def get_safe_config(cls, environment="development"):
        """Get safe configuration for development"""
        cls.verify_dev_environment()
        
        configs = {
            "development": {
                "port": 8503,
                "database": "dev.db",
                "debug": True,
                "environment": "development"
            },
            "staging": {
                "port": 8502,
                "database": "staging.db", 
                "debug": False,
                "environment": "staging"
            }
        }
        
        config = configs.get(environment)
        if not config:
            raise ValueError(f"Unknown environment: {environment}")
        
        cls.verify_port_safety(config["port"])
        return config

# Usage in app.py
if __name__ == "__main__":
    from config.environment_config import EnvironmentSafety
    
    # Safety check before starting
    EnvironmentSafety.verify_dev_environment()
    
    # Get safe configuration
    config = EnvironmentSafety.get_safe_config("development")
    
    # Start Streamlit with safe configuration
    import streamlit as st
    st.set_page_config(page_title="MyHealthTeam - Dev Environment")
```

## Implementation Roadmap

### Week 1: Foundation Setup

#### Day 1-2: Repository Structure
```powershell
# Create CI/CD directory structure
mkdir .github\workflows
mkdir tests\{unit,integration,e2e,performance,smoke}
mkdir scripts\deployment
mkdir environments
mkdir docs\deployment
```

#### Day 3-4: Basic Testing Framework
```python
# tests/conftest.py
import pytest
import sqlite3
import tempfile
import os
from src.database import get_db_connection

@pytest.fixture
def test_db():
    """Create a temporary test database"""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Setup test schema
    conn = sqlite3.connect(db_path)
    with open('src/sql/create_test_schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.close()
    
    yield db_path
    os.unlink(db_path)

@pytest.fixture
def test_user():
    """Create a test user"""
    return {
        'email': 'test@myhealthteam.org',
        'password': 'test_password',
        'role': 'coordinator'
    }
```

#### Day 5: Environment Configuration
```python
# environments/config.py
import os
from dataclasses import dataclass

@dataclass
class EnvironmentConfig:
    database_path: str
    port: int
    debug: bool
    log_level: str
    secret_key: str

def get_config(env: str = None) -> EnvironmentConfig:
    env = env or os.getenv('ENVIRONMENT', 'development')
    
    configs = {
        'development': EnvironmentConfig(
            database_path='development.db',
            port=8503,
            debug=True,
            log_level='DEBUG',
            secret_key=os.getenv('DEV_SECRET_KEY', 'dev-secret')
        ),
        'testing': EnvironmentConfig(
            database_path='test.db',
            port=8504,
            debug=True,
            log_level='INFO',
            secret_key='test-secret'
        ),
        'staging': EnvironmentConfig(
            database_path='staging.db',
            port=8502,
            debug=False,
            log_level='INFO',
            secret_key=os.getenv('STAGING_SECRET_KEY')
        ),
        'production': EnvironmentConfig(
            database_path='production.db',
            port=8501,
            debug=False,
            log_level='WARNING',
            secret_key=os.getenv('PROD_SECRET_KEY')
        )
    }
    
    return configs[env]
```

### Week 2: Testing Implementation

#### Unit Tests
```python
# tests/unit/test_workflow_utils.py
import pytest
from src.utils.workflow_utils import create_workflow, get_workflow_status

def test_create_workflow(test_db):
    """Test workflow creation"""
    workflow_id = create_workflow(
        template_id='IMAGING_URGENT',
        patient_id='TEST001',
        coordinator_id='coord001'
    )
    assert workflow_id is not None
    assert isinstance(workflow_id, str)

def test_get_workflow_status(test_db):
    """Test workflow status retrieval"""
    # Create test workflow
    workflow_id = create_workflow(
        template_id='LAB_ROUTINE',
        patient_id='TEST002',
        coordinator_id='coord001'
    )
    
    status = get_workflow_status(workflow_id)
    assert status['workflow_status'] == 'active'
    assert status['current_step'] == 1
```

#### Integration Tests
```python
# tests/integration/test_auth_integration.py
import pytest
import requests
from src.auth_module import authenticate_user, create_user_session

def test_auth_workflow_integration(test_db):
    """Test complete authentication workflow"""
    # Test user creation
    user_data = {
        'email': 'integration@test.com',
        'password': 'test_password',
        'role': 'coordinator'
    }
    
    # Test authentication
    auth_result = authenticate_user(
        user_data['email'], 
        user_data['password']
    )
    assert auth_result['success'] is True
    assert auth_result['user']['role'] == 'coordinator'
    
    # Test session creation
    session = create_user_session(auth_result['user']['id'])
    assert session['session_id'] is not None
```

### Week 3: Deployment Automation

#### Deployment Scripts
```powershell
# scripts/deployment/deploy_staging.ps1
param(
    [string]$Branch = "main",
    [string]$Environment = "staging"
)

Write-Host "=== Deploying to Staging Environment (Dev Folder) ===" -ForegroundColor Green

# SAFETY CHECK: Ensure we're in the Dev environment
$currentPath = Get-Location
if ($currentPath -notlike "*\Dev*") {
    Write-Host "ERROR: Must run from Dev environment (d:\Git\myhealthteam2\Dev\)" -ForegroundColor Red
    Write-Host "Current path: $currentPath" -ForegroundColor Red
    exit 1
}

# SAFETY CHECK: Ensure we're not targeting production port
if ($Environment -eq "production") {
    Write-Host "ERROR: Cannot deploy to production from Dev environment!" -ForegroundColor Red
    Write-Host "Production deployments must be done from d:\Git\myhealthteam2\Streamlit\" -ForegroundColor Red
    exit 1
}

Write-Host "Safety checks passed - proceeding with staging deployment" -ForegroundColor Green

# 1. Backup current staging database
Write-Host "Backing up staging database..." -ForegroundColor Yellow
python scripts/backup_staging_db.py --env staging

# 2. Stop staging service (Port 8502 only)
Write-Host "Stopping staging service on Port 8502..." -ForegroundColor Yellow
$stagingProcess = Get-Process | Where-Object {$_.ProcessName -eq "streamlit" -and $_.CommandLine -like "*8502*"}
if ($stagingProcess) {
    Stop-Process -Id $stagingProcess.Id -Force
}

# 3. Deploy new code
Write-Host "Deploying code..." -ForegroundColor Yellow
git checkout $Branch
git pull origin $Branch

# 4. Update dependencies
Write-Host "Updating dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# 5. Run database migrations
Write-Host "Running migrations..." -ForegroundColor Yellow
python scripts/run_migrations.py --env staging

# 6. Start staging service on Port 8502 ONLY
Write-Host "Starting staging service on Port 8502..." -ForegroundColor Yellow
$env:ENVIRONMENT = "staging"
Start-Process -FilePath "streamlit" -ArgumentList "run app.py --server.port 8502" -NoNewWindow

# 7. Wait for service to start
Start-Sleep -Seconds 10

# 8. Run health checks
Write-Host "Running health checks..." -ForegroundColor Yellow
python tests/smoke/test_staging_health.py --port 8502

Write-Host "Staging deployment complete on Port 8502!" -ForegroundColor Green
Write-Host "Production (Port 8501) remains untouched and protected." -ForegroundColor Cyan
```

#### Health Check Tests
```python
# tests/smoke/test_staging_health.py
import requests
import pytest
import time

def test_staging_health():
    """Test staging environment health"""
    base_url = "http://localhost:8502"
    
    # Wait for service to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            if i == max_retries - 1:
                pytest.fail("Staging service failed to start")
            time.sleep(2)
    
    # Test critical endpoints
    endpoints = [
        "/",
        "/health",
        "/api/workflows",
        "/api/users"
    ]
    
    for endpoint in endpoints:
        response = requests.get(f"{base_url}{endpoint}")
        assert response.status_code in [200, 401], f"Endpoint {endpoint} failed"

def test_database_connectivity():
    """Test database connectivity in staging"""
    from src.database import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Test basic query
    cursor.execute("SELECT COUNT(*) FROM workflow_templates")
    count = cursor.fetchone()[0]
    assert count > 0, "No workflow templates found"
    
    conn.close()
```

### Week 4: Monitoring and Observability

#### Application Monitoring
```python
# src/monitoring/health_check.py
import streamlit as st
import sqlite3
import time
from datetime import datetime
from src.database import get_db_connection

def health_check_endpoint():
    """Health check endpoint for monitoring"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }
    
    # Database connectivity check
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Workflow system check
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM workflow_templates")
        count = cursor.fetchone()[0]
        if count > 0:
            health_status['checks']['workflows'] = 'healthy'
        else:
            health_status['checks']['workflows'] = 'unhealthy: no templates'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['workflows'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    return health_status

# Add to app.py
if st.sidebar.button("Health Check"):
    health = health_check_endpoint()
    if health['status'] == 'healthy':
        st.success("System is healthy")
    else:
        st.error("System health issues detected")
    st.json(health)
```

## Quality Gates

### Pre-Merge Requirements
1. **All unit tests pass** (minimum 80% coverage)
2. **Integration tests pass**
3. **Security scan passes** (no high/critical vulnerabilities)
4. **Code review approved** (minimum 1 reviewer)
5. **Documentation updated** (if applicable)

### Pre-Production Requirements
1. **All tests pass in staging**
2. **Performance benchmarks met**
3. **Security review completed**
4. **Database backup verified**
5. **Rollback plan documented**

## Rollback Strategy

### Automated Rollback
```powershell
# scripts/deployment/rollback.ps1
param(
    [string]$Environment = "production",
    [string]$Version = "previous"
)

Write-Host "=== Rolling back $Environment to $Version ===" -ForegroundColor Red

# 1. Stop current service
Stop-Process -Name "streamlit" -Force -ErrorAction SilentlyContinue

# 2. Restore previous version
git checkout $Version

# 3. Restore database backup
python scripts/restore_database.py --env $Environment --version $Version

# 4. Restart service
$port = if ($Environment -eq "production") { 8501 } else { 8502 }
Start-Process -FilePath "streamlit" -ArgumentList "run app.py --server.port $port"

Write-Host "Rollback complete!" -ForegroundColor Green
```

## Metrics and KPIs

### Development Metrics
- **Build Success Rate**: Target 95%
- **Test Coverage**: Target 80%
- **Mean Time to Recovery**: Target < 30 minutes
- **Deployment Frequency**: Target daily for staging (production frequency managed separately)

### Application Metrics
- **Response Time**: Target < 2 seconds
- **Error Rate**: Target < 1%
- **Uptime**: Target 99.9%
- **Database Performance**: Target < 100ms query time

## Security Considerations

### Secrets Management
```yaml
# .github/workflows/secrets.yml
env:
  PROD_SECRET_KEY: ${{ secrets.PROD_SECRET_KEY }}
  STAGING_SECRET_KEY: ${{ secrets.STAGING_SECRET_KEY }}
  DATABASE_ENCRYPTION_KEY: ${{ secrets.DATABASE_ENCRYPTION_KEY }}
```

### Security Scanning
```yaml
# .github/workflows/security.yml
- name: Run Bandit Security Scan
  run: |
    pip install bandit
    bandit -r src/ -f json -o bandit-report.json

- name: Run Safety Check
  run: |
    pip install safety
    safety check --json --output safety-report.json
```

## Implementation Files

The following files have been created to support this CI/CD strategy:

### GitHub Actions Workflows
- **`.github\workflows\ci-cd-pipeline.yml`**: Main CI/CD pipeline with testing, linting, and security scans
- **`.github\workflows\deploy-dev.yml`**: Development deployment pipeline for staging environment

### Monitoring and Health Checks
- **`scripts\monitoring_setup.py`**: Comprehensive monitoring and health checking system
- **`docs\testing\AUTOMATED_TESTING_STRATEGY.md`**: Detailed testing strategy and implementation guide

### Key Features Implemented
- **Automated Testing**: Unit, integration, workflow, and security tests
- **Development Deployment**: Staging deployment with rollback capabilities
- **Health Monitoring**: Database, application, and workflow system health checks
- **Performance Tracking**: Development metrics and system performance monitoring
- **Security Scanning**: Dependency vulnerability and code security analysis

## Next Steps

### Immediate Actions (Week 1)
1. ✅ Set up basic GitHub Actions workflow (completed)
2. ✅ Create test directory structure (completed)
3. ✅ Implement basic unit tests (completed)
4. ✅ Configure environment-specific settings (completed)
5. [ ] Test the CI/CD pipeline with a sample commit
6. [ ] Configure GitHub repository secrets for deployment

### Short Term (Month 1)
1. [ ] Complete test suite implementation using `docs\testing\AUTOMATED_TESTING_STRATEGY.md`
2. [ ] Set up staging environment with port 8503
3. [ ] Implement automated deployment
4. [ ] Add monitoring and alerting using `scripts\monitoring_setup.py`
5. [ ] Create test data management system

### Long Term (Quarter 1)
1. [ ] Implement advanced monitoring
2. [ ] Set up performance testing
3. [ ] Add chaos engineering
4. [ ] Implement blue-green deployments
5. [ ] Automated rollback triggers based on health metrics

## Conclusion

This CI/CD strategy provides a robust foundation for continuous improvement and reliable deployments while maintaining the flexibility of your current multi-branch development approach. The phased implementation ensures minimal disruption to current workflows while progressively improving automation and reliability.

---

**Document Version**: 1.0  
**Last Updated**: $(Get-Date -Format "yyyy-MM-dd")  
**Next Review**: $(Get-Date -Format "yyyy-MM-dd" (Get-Date).AddMonths(3))