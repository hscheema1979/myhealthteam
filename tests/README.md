# MyHealthTeam Comprehensive Test Suite

Complete test coverage for all dashboards, scripts, and database operations using Streamlit AppTest framework.

## Test Structure

```
tests/
├── test_runner.py                          # Master test runner
├── test_admin_dashboard_comprehensive.py   # Admin dashboard tests
├── test_database_comprehensive.py          # Database module tests
├── test_scripts_comprehensive.py           # Script validation tests
├── test_admin_facility_apptest.py         # Facility management tests
└── test_reports/                          # Test report output directory
```

## Quick Start

### Run All Tests
```bash
python tests/test_runner.py
```

### Run Specific Test Suites
```bash
# Admin dashboard only
python tests/test_runner.py --suite admin

# Database tests only
python tests/test_runner.py --suite database

# Scripts only
python tests/test_runner.py --suite scripts
```

### Run Individual Test Files
```bash
# Admin dashboard comprehensive tests
python tests/test_admin_dashboard_comprehensive.py

# Database comprehensive tests
python tests/test_database_comprehensive.py

# Scripts comprehensive tests
python tests/test_scripts_comprehensive.py

# Facility management tests
python tests/test_admin_facility_apptest.py
```

## Test Categories

### 1. Admin Dashboard Tests (`test_admin_dashboard_comprehensive.py`)

**Patient Info Tab**
- Patient data loads correctly
- Editable columns exist (labs_notes, imaging_notes, general_notes)
- Patient panel view works
- Data persistence

**User Roles Tab**
- User list loads
- Role list loads
- Results Reviewer (RR) role exists
- User role assignments work
- Role management functions

**Facility Management Tab**
- Facilities table exists
- Facility columns correct
- User facility assignments table exists
- Facility CRUD operations
- User-facility assignment operations

**Staff Onboarding Tab**
- Users table structure correct
- User roles table exists
- User creation workflow

**System Metrics**
- Patient count metric
- User count metric
- Facility count metric

### 2. Database Tests (`test_database_comprehensive.py`)

**Database Connection**
- Connection opens/closes correctly
- Query execution works
- Database file exists and is accessible

**Patient Operations**
- Get all patients
- Get patient panel
- Get patient by ID
- Patient tables exist

**User Operations**
- Get all users
- Get all roles
- Get user by ID
- Get user roles by user ID
- Get users by role

**Coordinator Operations**
- Get coordinators
- Coordinator tasks table exists (monthly)

**Provider Operations**
- Get providers
- Provider tasks table exists (monthly)

**Workflow Operations**
- Workflow templates table exists
- Workflow instances table exists
- Query workflow templates

**Billing Operations**
- Task billing codes table exists
- Provider task billing status table exists

**Facility Operations**
- Get all facilities
- User facility assignments table exists

### 3. Scripts Tests (`test_scripts_comprehensive.py`)

**ETL Scripts**
- ETL script exists (`transform_production_data_v3_fixed.py`)
- ETL script is valid Python
- CSV cleaning utility exists

**Refresh Scripts**
- Refresh script exists (`refresh_production_data.ps1`)
- Download script exists (`scripts/1_download_files_complete.ps1`)
- Consolidation script exists (`scripts/2_consolidate_files.ps1`)
- Post-import SQL exists (`src/sql/post_import_processing.sql`)

**Sync Scripts**
- CSV billing sync script exists
- Sync config exists
- VPS2 setup scripts exist

**Backup Scripts**
- Backup script exists
- VPS2 backup deploy script exists
- Setup daily backup task script exists
- Test backup script exists

**Deployment Scripts**
- Deploy to test script exists
- Deploy to production script exists
- Promote test to production script exists

**Workflow Scripts**
- Capture workflows script exists
- Direct capture workflows script exists

**Daily Scripts**
- Daily pull from VPS2 script exists

### 4. Feature-Specific Tests (`test_admin_facility_apptest.py`)

**Facility Management**
- RR role exists in database
- RR workflow assignments correct
- Facilities table exists
- User facility assignments table exists
- Facility columns correct
- Facility management sub-tabs exist

## Test Reports

All tests generate JSON reports in the `test_reports/` directory:

```bash
test_report_admin_comprehensive_YYYYMMDD_HHMMSS.json
test_report_database_comprehensive_YYYYMMDD_HHMMSS.json
test_report_scripts_comprehensive_YYYYMMDD_HHMMSS.json
test_report_admin_facility_YYYYMMDD_HHMMSS.json
test_report_comprehensive_YYYYMMDD_HHMMSS.json
```

### Report Format

```json
{
  "timestamp": "2026-02-18T00:30:00",
  "duration": 5.23,
  "summary": {
    "total": 45,
    "passed": 42,
    "failed": 3
  },
  "results": [
    {
      "name": "Test Name",
      "status": "PASS",
      "details": "Test details",
      "timestamp": "2026-02-18T00:30:01"
    }
  ]
}
```

## Integration with CI/CD

### Pre-Commit Testing
```bash
# Run quick tests before committing
python tests/test_database_comprehensive.py
```

### Pre-Deployment Testing
```bash
# Run comprehensive tests before deploying to test/production
python tests/test_runner.py --report
```

### Continuous Testing
```bash
# Add to Git hooks or CI/CD pipeline
python tests/test_runner.py --suite all --report
```

## Adding New Tests

### Create a New Test File

1. Create test file in `tests/` directory
2. Import test infrastructure

```python
import sys
from pathlib import Path
from datetime import datetime
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import database  # or other modules
```

3. Create test class

```python
class MyFeatureTest:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def test_something(self):
        tests = []
        try:
            # Test logic here
            tests.append({
                "name": "Test Name",
                "status": "PASS",
                "details": "Test passed"
            })
        except Exception as e:
            tests.append({
                "name": "Test Name",
                "status": "FAIL",
                "error": str(e)
            })
        return tests

    def run_all_tests(self):
        # Run all test methods
        pass

    def print_summary(self):
        # Print and save summary
        pass
```

4. Add to test runner (`test_runner.py`)

```python
"myfeature": {
    "name": "My Feature Tests",
    "tests": [
        "test_myfeature_apptest.py",
    ]
}
```

## Test Coverage Matrix

| Component | Test File | Coverage |
|-----------|-----------|----------|
| Admin Dashboard | `test_admin_dashboard_comprehensive.py` | All tabs, UI components, DB operations |
| Database Module | `test_database_comprehensive.py` | All CRUD operations, connections, tables |
| Scripts | `test_scripts_comprehensive.py` | ETL, sync, backup, deployment scripts |
| Facility Management | `test_admin_facility_apptest.py` | Facility CRUD, user assignments |
| Coordinator Dashboard | *(pending)* | Coordinator tasks, patient assignment |
| Provider Dashboard | *(pending)* | Provider tasks, patient management |
| Onboarding Dashboard | *(pending)* | Patient onboarding, phone review |
| Workflow System | *(pending)* | Workflow templates, instances |
| ZMO Module | *(pending)* | ZMO editing, cascade updates |

## Best Practices

1. **Run tests locally before committing**
   ```bash
   python tests/test_runner.py --suite database
   ```

2. **Run full suite before major deployments**
   ```bash
   python tests/test_runner.py --report
   ```

3. **Review test reports after each run**
   - Check for failed tests
   - Review error messages
   - Fix issues before deploying

4. **Keep tests updated**
   - Add tests for new features
   - Update tests when modifying existing features
   - Remove tests for deprecated features

5. **Test data isolation**
   - Use read-only operations when possible
   - Don't modify production data during tests
   - Use test database when available

## Troubleshooting

### Tests Fail to Run

**Issue**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Make sure you're running from project root directory
```bash
cd D:\Git\myhealthteam2\Dev
python tests/test_runner.py
```

### Database Connection Errors

**Issue**: `sqlite3.OperationalError: unable to open database file`

**Solution**: Ensure database exists and you have permissions
```bash
ls production.db  # Check if database exists
```

### Import Errors

**Issue**: `ImportError` for dashboard modules

**Solution**: Install required dependencies
```bash
pip install streamlit pandas numpy
```

## Future Enhancements

- [ ] Streamlit AppTest framework integration (UI testing)
- [ ] Automated testing in CI/CD pipeline
- [ ] Performance benchmarks
- [ ] Load testing for critical operations
- [ ] Visual regression testing for dashboards
- [ ] API endpoint testing
- [ ] Security testing
- [ ] Data integrity testing

## Support

For issues or questions:
1. Check test reports for detailed error messages
2. Review code in test files for examples
3. Check existing test patterns in `test_*.py` files
4. Refer to database schema in `src/database.py`
