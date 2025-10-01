# CI/CD Pipeline Quick Start Guide

## Overview

This guide helps developers quickly get started with the MyHealthTeam CI/CD pipeline for continuous integration, testing, and deployment.

## Prerequisites

- Git repository access
- GitHub Actions enabled
- Python 3.9+ installed locally
- Access to development environment (port 8502)

## Pipeline Overview

Our CI/CD pipeline consists of two main workflows:

1. **CI/CD Pipeline** (`.github\workflows\ci-cd-pipeline.yml`)
   - Triggered on: Push, Pull Request
   - Runs: Linting, Testing, Security Scans, Build

2. **Deployment Pipeline** (`.github\workflows\deploy.yml`)
   - Triggered on: Push to main, CI/CD completion
   - Runs: Staging deployment, Production deployment, Rollback

## Quick Start Steps

### 1. Local Development Setup

```powershell
# Clone and setup
git clone <repository-url>
cd myhealthteam2\Streamlit

# Install dependencies
pip install -r requirements.txt

# Run local tests
python -m pytest tests/ -v

# Check code quality
flake8 src/
black --check src/
isort --check-only src/
```

### 2. Development Workflow

```powershell
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Run local tests before committing
python scripts/test_all_workflows.py
python scripts/verify_workflows_readonly.py

# Commit changes
git add .
git commit -m "feat: add your feature description"

# Push to trigger CI pipeline
git push origin feature/your-feature-name
```

### 3. Monitor Pipeline Execution

1. **Go to GitHub Actions tab** in your repository
2. **Find your workflow run** (named after your commit message)
3. **Monitor each job**:
   - ✅ **Lint and Format**: Code quality checks
   - ✅ **Unit Tests**: Fast unit test execution
   - ✅ **Integration Tests**: Component interaction tests
   - ✅ **Workflow Tests**: Workflow system validation
   - ✅ **Security Scan**: Vulnerability detection
   - ✅ **Build and Test**: Final build verification

### 4. Pull Request Process

```powershell
# Create pull request
# - GitHub will automatically run CI pipeline
# - All checks must pass before merge
# - Code review required

# After approval and merge to main:
# - Deployment pipeline automatically triggers
# - Staging deployment runs first
# - Production deployment follows if staging succeeds
```

## Environment-Specific Testing

### Development Environment (Port 8502)
```powershell
# Test in development environment
cd sandbox\auth_integration_branch
streamlit run app.py --server.port 8502

# Run development tests
python scripts/test_all_workflows.py --env development
```

### Staging Environment (Port 8503)
```powershell
# Test staging deployment
cd sandbox\production_branch
streamlit run app.py --server.port 8503

# Run staging health checks
python scripts/monitoring_setup.py --action health-check --environment staging
```

### Production Environment (Port 8501)
```powershell
# Production is managed by CI/CD pipeline
# Manual access for emergency only
streamlit run app.py --server.port 8501

# Check production health
python scripts/monitoring_setup.py --action monitor --environment production
```

## Common Commands

### Testing Commands
```powershell
# Run all tests
python -m pytest tests/ -v --cov=src

# Run specific test categories
python -m pytest tests/unit/ -v          # Unit tests only
python -m pytest tests/integration/ -v   # Integration tests only

# Run workflow tests
python scripts/test_all_workflows.py

# Verify system health
python scripts/verify_workflows_readonly.py
```

### Code Quality Commands
```powershell
# Check code formatting
black --check src/
isort --check-only src/
flake8 src/

# Fix code formatting
black src/
isort src/
```

### Monitoring Commands
```powershell
# Run health check
python scripts/monitoring_setup.py --action health-check

# Full monitoring cycle
python scripts/monitoring_setup.py --action monitor

# Setup monitoring environment
python scripts/monitoring_setup.py --action setup
```

## Pipeline Status Indicators

### ✅ Success Indicators
- All tests pass
- Code quality checks pass
- Security scans show no critical issues
- Deployment completes successfully

### ⚠️ Warning Indicators
- Some non-critical tests fail
- Code coverage below target
- Minor security issues found
- Performance degradation detected

### ❌ Failure Indicators
- Critical tests fail
- Code quality standards not met
- Critical security vulnerabilities
- Deployment fails

## Troubleshooting

### Common Issues

#### 1. Test Failures
```powershell
# Check test output
python -m pytest tests/ -v -s

# Run specific failing test
python -m pytest tests/test_specific.py::test_function -v -s

# Check database connectivity
python scripts/verify_workflows_readonly.py
```

#### 2. Code Quality Issues
```powershell
# Fix formatting issues
black src/
isort src/

# Check specific linting errors
flake8 src/ --show-source
```

#### 3. Database Issues
```powershell
# Verify database structure
python scripts/check_db_tables.py

# Reset development database
cp backups/production_backup_latest.db production.db
```

#### 4. Pipeline Failures
1. **Check GitHub Actions logs** for detailed error messages
2. **Run tests locally** to reproduce issues
3. **Check environment variables** and secrets configuration
4. **Verify file paths** and dependencies

### Getting Help

1. **Check pipeline logs** in GitHub Actions
2. **Run local diagnostics**:
   ```powershell
   python scripts/monitoring_setup.py --action health-check
   ```
3. **Review documentation**:
   - `docs\CI_CD_RECOMMENDATIONS.md` - Full CI/CD strategy
   - `docs\testing\AUTOMATED_TESTING_STRATEGY.md` - Testing details
   - `docs\workflow\IDE_BRANCH_WORKFLOW.md` - Branch management

## Best Practices

### Development
- **Write tests first** for new features
- **Run tests locally** before pushing
- **Keep commits small** and focused
- **Use descriptive commit messages**

### Testing
- **Maintain test coverage** above 80%
- **Test edge cases** and error conditions
- **Use realistic test data**
- **Keep tests fast** and independent

### Deployment
- **Test in staging** before production
- **Monitor deployment** health checks
- **Have rollback plan** ready
- **Document changes** in commit messages

### Security
- **Never commit secrets** or credentials
- **Use environment variables** for configuration
- **Keep dependencies updated**
- **Review security scan results**

## Quick Reference

### Port Allocation
- **8501**: Production (protected)
- **8502**: Development/Sandbox
- **8503**: Staging/Testing

### Key Files
- **`app.py`**: Main application entry point
- **`src/database.py`**: Database operations
- **`src/auth_module.py`**: Authentication system
- **`src/workflow_engine.py`**: Workflow management
- **`production.db`**: Production database

### Important Directories
- **`src/`**: Source code
- **`tests/`**: Test files
- **`scripts/`**: Utility scripts
- **`docs/`**: Documentation
- **`backups/`**: Database backups
- **`.github/workflows/`**: CI/CD pipelines

---

**Last Updated**: 2024-12-19  
**Document Owner**: Development Team  
**Next Review**: 2025-01-19