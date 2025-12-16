# Healthcare Dashboard - Unified Import System

## Overview

The **Unified Import System** consolidates all CSV import, transformation, and staging operations into a single, maintainable Python script with comprehensive error handling, logging, and automation features.

## 🎯 Key Features

### ✅ **Complete Automation**
- Single script handles entire import pipeline
- Automatic backup creation and recovery
- Comprehensive logging and error handling
- Date-based incremental imports with watermarks

### ✅ **Centralized Management**
- Staff code mapping via `staff_codes` table
- Patient ID normalization and validation
- Coordinated handling of coordinator and provider tasks
- Production-safe staging operations

### ✅ **Production Ready**
- Backward compatibility with existing PowerShell scripts
- Comprehensive testing framework
- Automated scheduling and monitoring
- Detailed audit trails and validation

## 📁 File Structure

```
scripts/
├── unified_import.py              # Main unified import script
├── run_unified_import.bat         # Windows batch wrapper (user-friendly)
├── schedule_daily_import.ps1      # PowerShell scheduler setup
├── staff_utils.py                 # Staff code management utilities
├── 3_import_to_database.ps1       # Legacy PowerShell import script
├── 4a-transform.ps1               # Legacy PowerShell transformation
├── 4b-transform.ps1               # Legacy PowerShell transformation
├── 4c-transform.ps1               # Legacy PowerShell transformation
└── logs/                          # Import execution logs
    └── unified_import_*.log       # Timestamped log files
```

## 🚀 Quick Start

### **Option 1: Interactive Wizard**
```batch
# Double-click or run from command line
scripts\run_unified_import.bat
```

### **Option 2: Direct Script Execution**
```bash
# Basic incremental import (using watermark)
python scripts\unified_import.py

# Import from specific date
python scripts\unified_import.py --start-date 2025-11-01

# Skip backup for testing
python scripts\unified_import.py --no-backup --start-date 2025-11-01

# Custom database paths
python scripts\unified_import.py --production-db custom.db --staging-db staging.db
```

### **Option 3: Automated Daily Import**
```powershell
# Setup automated daily import at 2:00 AM
powershell -ExecutionPolicy Bypass -File scripts\schedule_daily_import.ps1

# Test the setup
powershell -ExecutionPolicy Bypass -File scripts\schedule_daily_import.ps1 -TestRun

# Remove scheduled task
powershell -ExecutionPolicy Bypass -File scripts\schedule_daily_import.ps1 -Remove
```

## 📊 Import Process Flow

### **Phase 1: Pre-Import Setup**
1. **Backup Creation**: Automatic backup of production database
2. **Watermark Check**: Retrieve last successful import date
3. **File Validation**: Verify required CSV files exist
4. **Staff Mapping**: Load staff codes from `staff_codes` table

### **Phase 2: CSV Import to Staging**
1. **Coordinator Tasks**: Import `downloads/cmlog.csv` with date filtering
2. **Provider Tasks**: Combine `downloads/psl.csv` and `downloads/rvz.csv`
3. **Patient Data**: Import `downloads/patients/ZMO_Main.csv`
4. **Date Filtering**: Apply start date filter to all imported data

### **Phase 3: Data Transformation**
1. **Legacy Scripts**: Execute existing PowerShell transformation scripts
2. **Patient Normalization**: Create `staging_patients`, `staging_patient_assignments`
3. **Task Processing**: Transform coordinator and provider tasks
4. **Summary Generation**: Build visit summaries and metrics

### **Phase 4: Post-Import**
1. **Watermark Update**: Record latest imported date
2. **Validation**: Verify table counts and data integrity
3. **Log Generation**: Create detailed execution logs
4. **Error Handling**: Capture and report any issues

## ⚙️ Configuration Options

### **Command Line Parameters**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--start-date` | Import data from this date (YYYY-MM-DD) | Uses watermark |
| `--no-backup` | Skip database backup creation | False |
| `--production-db` | Path to production database | production.db |
| `--staging-db` | Path to staging database | sheets_data.db |

### **CSV File Requirements**
| File | Purpose | Format |
|------|---------|--------|
| `downloads/cmlog.csv` | Coordinator tasks | MM/DD/YYYY dates, CM ID |
| `downloads/psl.csv` | Provider tasks (PSL) | DOS dates, provider names |
| `downloads/rvz.csv` | Provider tasks (RVZ) | DOS dates, provider names |
| `downloads/patients/ZMO_Main.csv` | Patient master data | LAST FIRST DOB format |

### **Database Tables**
| Table | Purpose | Status |
|-------|---------|--------|
| `staff_codes` | Staff mapping reference | Required |
| `etl_watermarks` | Import tracking | Auto-created |
| `staging_*` tables | Import staging area | Auto-generated |

## 🔧 Advanced Features

### **Incremental Import with Watermarks**
The system automatically tracks the last successful import date and only processes new data:

```python
# Automatic watermark-based import
manager = UnifiedImportManager()
manager.run_import()  # Uses stored watermark

# Manual date-based import
manager.run_import(start_date="2025-11-01")
```

### **Staff Code Integration**
Leverages the centralized `staff_codes` table for consistent staff identification:

```python
# Load staff mappings
mapping = manager._load_staff_mapping()
# Returns: {'Ethel Antonio': {'coordinator_code': 'ANTET000', 'provider_code': 'Antonio, Ethel'}}
```

### **Comprehensive Logging**
All operations are logged with timestamps and error details:

```bash
# View latest import log
type logs\unified_import_20251203_162800.log

# Monitor real-time logs
Get-Content logs\unified_import_*.log -Tail 20 -Wait
```

## 🧪 Testing & Validation

### **Test the Unified Import**
```bash
# Test with backup copy
python scripts\unified_import.py --production-db production_backup_test.db --no-backup --start-date 2025-11-01

# Test incremental update
python scripts\unified_import.py --start-date 2025-11-15
```

### **Validate Results**
```sql
-- Check staging table counts
SELECT COUNT(*) FROM staging_coordinator_tasks;
SELECT COUNT(*) FROM staging_provider_tasks;

-- Verify data quality
SELECT patient_id, COUNT(*) FROM staging_patients GROUP BY patient_id HAVING COUNT(*) > 1;
```

### **Test Automated Scheduling**
```powershell
# Test scheduled task setup
powershell -ExecutionPolicy Bypass -File scripts\schedule_daily_import.ps1 -TestRun

# Manual task execution
schtasks /run /tn "HealthcareDashboard_DailyImport"
```

## 📈 Monitoring & Maintenance

### **Log File Monitoring**
```bash
# List recent import logs
dir logs\unified_import_*.log | Sort-Object LastWriteTime -Descending

# Check for errors
Select-String -Path logs\unified_import_*.log -Pattern "ERROR|Failed"
```

### **Database Health Checks**
```sql
-- Check watermark status
SELECT * FROM etl_watermarks;

-- Verify staging tables
SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'staging_%';

-- Check recent activity
SELECT MAX(activity_date) FROM staging_provider_tasks;
SELECT MAX(activity_date) FROM staging_coordinator_tasks;
```

### **Backup Management**
```bash
# List backups
dir backups\unified_import_backup_*.db

# Clean old backups (older than 30 days)
Get-ChildItem backups\unified_import_backup_*.db | Where-Object LastWriteTime -lt (Get-Date).AddDays(-30) | Remove-Item
```

## 🛠️ Troubleshooting

### **Common Issues**

#### **CSV Files Not Found**
```
ERROR: Required CSV files not found
```
**Solution**: Ensure CSV files exist in `downloads/` directory:
- `cmlog.csv` (coordinator tasks)
- `psl.csv` (provider tasks - PSL)
- `rvz.csv` (provider tasks - RVZ)
- `patients/ZMO_Main.csv` (patient data)

#### **Date Parsing Errors**
```
ERROR: Coordinator tasks import failed
```
**Solution**: Check date format in CSV files - should be MM/DD/YYYY or MM/DD/YY

#### **Staff Code Mapping Issues**
```
WARNING: Could not load staff mapping
```
**Solution**: Verify `staff_codes` table exists and contains valid staff records

#### **Permission Errors**
```
ERROR: Failed to create backup
```
**Solution**: Ensure write permissions to `backups/` directory and database files

### **Recovery Procedures**

#### **Restore from Backup**
```bash
# Replace production database with backup
copy backups\unified_import_backup_20251203_162800.db production.db

# Verify restoration
sqlite3 production.db "SELECT COUNT(*) FROM patients;"
```

#### **Manual Watermark Reset**
```sql
-- Reset watermark to allow full reimport
UPDATE etl_watermarks SET last_import_date = '2025-09-26' 
WHERE source_name IN ('provider_tasks', 'coordinator_tasks', 'patients');
```

## 🔄 Migration from Legacy Scripts

The unified import system is **backward compatible** with existing workflows:

### **Before (Multiple Scripts)**
```powershell
# Old workflow
powershell -File scripts\3_import_to_database.ps1 -StartDate "2025-11-01"
powershell -File scripts\4a-transform.ps1
powershell -File scripts\4b-transform.ps1
powershell -File scripts\4c-transform.ps1
python scripts\verify_normalization_linkage.py --quick
```

### **After (Single Command)**
```bash
# New unified workflow
python scripts\unified_import.py --start-date 2025-11-01
```

## 🎯 Next Steps

### **Immediate Actions**
1. **Test the unified import** with a copy of production data
2. **Review logs** to ensure all operations complete successfully
3. **Validate staging tables** contain expected data
4. **Schedule daily automation** if testing is successful

### **Production Deployment**
1. **Run during maintenance window** for first production deployment
2. **Monitor logs** closely during initial automated runs
3. **Establish alerting** for failed imports (optional)
4. **Document any custom requirements** or exceptions

### **Future Enhancements**
- **Email notifications** for import status
- **Web dashboard** for monitoring import status
- **Data validation rules** and quality checks
- **Integration with external data sources**

## 📞 Support

For issues or questions about the unified import system:

1. **Check logs first**: `logs/unified_import_*.log`
2. **Review this documentation** for common solutions
3. **Test with `--no-backup`** for debugging
4. **Verify CSV file formats** and date ranges
5. **Check staff code mappings** in `staff_codes` table

---

## 🎉 Success Criteria

The unified import system is considered **production-ready** when:

- ✅ **All imports complete successfully** without errors
- ✅ **Data counts match expectations** (staging vs. expected volumes)
- ✅ **Logs are clean** (no ERROR or WARNING messages)
- ✅ **Staff code mappings work** correctly
- ✅ **Watermark tracking** functions properly
- ✅ **Automated scheduling** runs reliably
- ✅ **Backup/recovery** procedures tested

**Congratulations!** You now have a robust, maintainable, and automated import system for the Healthcare Dashboard.
