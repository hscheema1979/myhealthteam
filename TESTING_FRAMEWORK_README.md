# MyHealthTeam Comprehensive Integration Testing Framework

## Overview

This comprehensive testing framework provides end-to-end validation of the MyHealthTeam system, including workflow templates, provider functionality, database integrity, and data synchronization. The framework is designed to rigorously test all functional components and ensure alignment with intended system behavior.

## Framework Architecture

### Core Components

1. **Comprehensive Integration Test Suite** (`comprehensive_integration_test_suite.py`)
   - Tests all 14 workflow templates with multiple iterations
   - Validates provider functionality (visit tasks, phone reviews)
   - Performs data consistency checks
   - Includes authentication and database connection management

2. **Integration Test Runner** (`run_integration_tests.py`)
   - Orchestrates test execution with progress tracking
   - Generates detailed reports in multiple formats (JSON, CSV, HTML, Text)
   - Provides real-time monitoring and status updates
   - Supports command-line configuration

3. **Database Verification Suite** (`database_verification_suite.py`)
   - Uses direct sqlite3 commands for database validation
   - Verifies schema integrity and table structure
   - Checks data consistency and foreign key relationships
   - Validates synchronization between main and monthly tables
   - Collects performance metrics

4. **Master Test Execution** (`master_test_execution.py`)
   - Coordinates all testing components
   - Provides comprehensive reporting across all test phases
   - Handles error recovery and continuation strategies
   - Generates executive summaries and recommendations

5. **Simple Test Runner** (`run_tests.py`)
   - Easy-to-use interface for running tests
   - Provides quick test options and selective test execution
   - Simplified command-line interface

## Testing Scope

### 1. Workflow Testing
- **All 14 Workflow Templates**: LAB ROUTINE, IMAGING ROUTINE, DME REFERRAL, POT_PATIENT_ONBOARDING, etc.
- **5 Iterations per Template**: Each workflow is tested multiple times to ensure consistency
- **Step Validation**: Every workflow step is validated for proper execution
- **Progress Tracking**: Detailed documentation of each iteration with notes and status

### 2. Provider Testing
- **Visit Tasks**: Testing with default 15-minute duration
- **Phone Reviews**: Comprehensive phone review functionality testing
- **Data Validation**: Ensures patient info changes are properly written to:
  - `patients` table
  - `patient_panel` table
  - `provider_tasks_YYYY_MM` tables
  - `provider_tasks` table
  - Task notes and documentation

### 3. Data Validation
- **Coordinator Tasks**: Validates data is written to both:
  - `coordinator_tasks` table
  - `coordinator_tasks_YYYY_MM` tables
- **Provider Tasks**: Validates data is written to both:
  - `provider_tasks` table
  - `provider_tasks_YYYY_MM` tables
- **Synchronization**: Ensures all tables remain in sync with consistent data

### 4. Database Verification
- **Schema Validation**: Verifies all required tables and columns exist
- **Data Consistency**: Checks foreign key relationships and referential integrity
- **Monthly Table Sync**: Validates synchronization between main and partitioned tables
- **Performance Metrics**: Collects database size, counts, and performance data
- **SQLite3 Verification**: Direct database queries to verify data correctness

## Installation and Setup

### Prerequisites
- Python 3.7+
- SQLite3
- Access to `production.db`
- Required Python modules (automatically imported)

### File Structure
```
Dev/
├── comprehensive_integration_test_suite.py
├── run_integration_tests.py
├── database_verification_suite.py
├── master_test_execution.py
├── run_tests.py
├── TESTING_FRAMEWORK_README.md
├── production.db
└── test_results/
    ├── JSON reports
    ├── HTML reports
    ├── CSV summaries
    └── Text reports
```

## Usage Instructions

### Quick Start

#### 1. Run Complete Test Suite
```bash
python run_tests.py
```
This runs all tests with default settings (5 iterations per test).

#### 2. Quick Test Mode
```bash
python run_tests.py --quick
```
Runs all tests with 2 iterations for faster execution.

#### 3. Selective Testing
```bash
# Database verification only
python run_tests.py --db-only

# Workflow tests only
python run_tests.py --workflows-only

# Provider tests only
python run_tests.py --providers-only
```

### Advanced Usage

#### 1. Master Test Execution
```bash
python master_test_execution.py --iterations 5 --verbose --continue-on-failure
```

**Parameters:**
- `--iterations`: Number of iterations per test (default: 5)
- `--username`: Test username (default: test_user)
- `--password`: Test password (default: test_password)
- `--database`: Database file path (default: production.db)
- `--output`: Output directory (default: test_results)
- `--verbose`: Enable verbose output
- `--continue-on-failure`: Continue testing even if a phase fails
- `--quick`: Run quick test mode (fewer iterations)

#### 2. Integration Test Runner
```bash
python run_integration_tests.py --iterations 3 --output custom_results --verbose
```

#### 3. Database Verification Only
```bash
python database_verification_suite.py --database production.db --output db_results
```

## Test Results and Reports

### Output Directory Structure
```
test_results/
├── master_test_results_YYYYMMDD_HHMMSS.json
├── master_test_report_YYYYMMDD_HHMMSS.txt
├── master_test_summary_YYYYMMDD_HHMMSS.csv
├── integration_test_results_YYYYMMDD_HHMMSS.json
├── integration_test_report_YYYYMMDD_HHMMSS.html
├── database_verification_YYYYMMDD_HHMMSS.json
└── database_verification_report_YYYYMMDD_HHMMSS.txt
```

### Report Types

#### 1. Master Test Report
- Executive summary with overall success rates
- Phase-by-phase breakdown
- Recommendations and next steps
- Duration and performance metrics

#### 2. Integration Test Report
- Detailed workflow test results
- Provider test outcomes
- Individual iteration tracking
- Error logs and debugging information

#### 3. Database Verification Report
- Schema validation results
- Data consistency checks
- Synchronization status
- Performance metrics
- Integrity check results

#### 4. HTML Dashboard Report
- Interactive web-based report
- Visual charts and graphs
- Drill-down capabilities
- Export functionality

## Test Configuration

### Default Test Users
- **Username**: `test_user`
- **Password**: `test_password`
- **Role**: Configured for testing access

### Database Configuration
- **Primary Database**: `production.db`
- **Test Tables**: All workflow and task tables
- **Monthly Tables**: Current month partitioned tables

### Test Parameters
- **Default Iterations**: 5 per test
- **Quick Mode Iterations**: 2 per test
- **Provider Task Duration**: 15 minutes (default)
- **Timeout Settings**: Configurable per test type

## Workflow Templates Tested

The framework tests all 14 workflow templates:

1. LAB ROUTINE
2. IMAGING ROUTINE
3. DME REFERRAL
4. POT_PATIENT_ONBOARDING
5. SPECIALIST REFERRAL
6. MEDICATION REVIEW
7. CARE PLAN UPDATE
8. INSURANCE VERIFICATION
9. APPOINTMENT SCHEDULING
10. FOLLOW-UP COORDINATION
11. DISCHARGE PLANNING
12. EMERGENCY RESPONSE
13. QUALITY ASSURANCE
14. BILLING COORDINATION

Each template is tested through complete workflow execution with step-by-step validation.

## Error Handling and Recovery

### Automatic Recovery
- Connection retry mechanisms
- Transaction rollback on failures
- Graceful degradation for non-critical errors

### Error Reporting
- Detailed error logs with stack traces
- Context information for debugging
- Categorized error types (database, authentication, workflow, etc.)

### Continuation Strategies
- `--continue-on-failure` option to proceed despite errors
- Phase-level error isolation
- Partial result preservation

## Performance Monitoring

### Metrics Collected
- Test execution duration
- Database query performance
- Memory usage patterns
- Success/failure rates
- Throughput measurements

### Performance Thresholds
- Database response time limits
- Workflow completion timeouts
- Resource usage monitoring
- Scalability indicators

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```
Error: database is locked
```
**Solution**: Ensure no other processes are accessing the database.

#### 2. Authentication Failures
```
Error: Invalid credentials
```
**Solution**: Verify test user credentials in the system.

#### 3. Missing Tables
```
Error: no such table: workflow_templates
```
**Solution**: Ensure database schema is up to date.

#### 4. Import Errors
```
ImportError: No module named 'comprehensive_integration_test_suite'
```
**Solution**: Ensure all test files are in the same directory.

### Debug Mode
Enable verbose logging for detailed troubleshooting:
```bash
python run_tests.py --verbose
```

### Log Analysis
Check test result files for detailed error information:
- JSON files contain structured error data
- Text reports include human-readable summaries
- CSV files provide tabular analysis data

## Best Practices

### 1. Pre-Test Preparation
- Backup database before testing
- Ensure test environment is isolated
- Verify all dependencies are available
- Check disk space for result files

### 2. Test Execution
- Run tests during low-usage periods
- Monitor system resources during execution
- Use quick mode for initial validation
- Run full tests for comprehensive validation

### 3. Result Analysis
- Review all failed tests immediately
- Compare results across test runs
- Track performance trends over time
- Document any system changes

### 4. Maintenance
- Update test credentials as needed
- Refresh test data periodically
- Review and update test parameters
- Archive old test results

## Integration with CI/CD

### GitHub Actions Integration
The framework can be integrated with GitHub Actions for automated testing:

```yaml
name: Comprehensive Testing
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Run Tests
        run: python run_tests.py --quick
```

### Scheduled Testing
Set up automated testing schedules:
- Daily quick tests
- Weekly comprehensive tests
- Monthly full validation

## Support and Maintenance

### Framework Updates
- Regular updates to test scenarios
- New workflow template support
- Enhanced reporting capabilities
- Performance optimizations

### Documentation Updates
- Keep usage instructions current
- Update troubleshooting guides
- Maintain example configurations
- Document new features

## Conclusion

This comprehensive testing framework provides robust validation of the MyHealthTeam system, ensuring all components function correctly and data remains consistent across all tables and workflows. The framework's modular design allows for flexible testing strategies while maintaining comprehensive coverage of all system functionality.

For questions or issues, refer to the troubleshooting section or review the detailed test reports generated by the framework.