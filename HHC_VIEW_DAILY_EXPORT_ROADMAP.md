# HHC View Template - Daily Export Roadmap

## Overview
This document outlines the path to implement automated daily exports of the HHC View Template data directly to Google Sheets without manual intervention.

## Current State (Phase 1)
- ✅ HHC View Template tab displays all active patients
- ✅ Manual CSV export available via download button
- ✅ Data queries from production.db in real-time
- ⏳ No automated scheduling

## Target State (Phase 2)
- Automated daily export at specified time (e.g., 6:00 AM)
- Automatic sync to Google Sheet: https://docs.google.com/spreadsheets/d/14WJOBqHvxCEQ1i3WynUB6Kwe-4Be78jPrTMWuGUX5oE/edit?gid=0#gid=0
- Email notification on completion
- Audit log of all exports
- Fallback notifications if export fails

## Implementation Steps

### Step 1: Google Sheets API Setup (Prerequisites)
**Time Estimate**: 30 minutes
**Complexity**: Medium

#### 1.1 Enable Google Sheets API
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing one
3. Search for "Google Sheets API" and enable it
4. Search for "Google Drive API" and enable it

#### 1.2 Create Service Account
1. Go to "Service Accounts" in Cloud Console
2. Click "Create Service Account"
3. Name it: `zen-medical-export`
4. Grant role: Editor
5. Create a JSON key file
6. Download and save as `google_credentials.json` in project root

#### 1.3 Share Google Sheet with Service Account
1. Open the Google Sheet you want to sync to
2. Get the service account email from the JSON key file
3. Share the sheet with that email address (Editor access)

### Step 2: Install Required Dependencies
**Time Estimate**: 5 minutes
**Complexity**: Low

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client schedule
```

Required packages:
- `google-auth-oauthlib`: Google OAuth authentication
- `google-auth-httplib2`: HTTP adapter for Google Auth
- `google-api-python-client`: Google Sheets API client
- `schedule`: Job scheduling library

### Step 3: Create Export Service Module
**Time Estimate**: 2-3 hours
**Complexity**: Medium-High

Create new file: `src/exporters/hhc_daily_export_service.py`

Key components:
```python
class HHCExportService:
    """Service for exporting HHC View data to Google Sheets"""
    
    def __init__(self, sheet_id, credentials_path):
        """Initialize with Google Sheets ID and credentials"""
        
    def get_active_patients(self):
        """Query database for active patients"""
        
    def format_for_sheets(self, df):
        """Format DataFrame for Google Sheets compatibility"""
        
    def sync_to_sheets(self, df):
        """Upload data to Google Sheets"""
        
    def send_notification(self, status, error=None):
        """Send email notification on completion/failure"""
```

### Step 4: Create Scheduler
**Time Estimate**: 1-2 hours
**Complexity**: Medium

Create new file: `src/exporters/scheduler.py`

Key features:
- Schedule exports at specified time (default: 6:00 AM)
- Retry logic for failed exports
- Maintain execution log
- Graceful error handling

```python
class ExportScheduler:
    """Schedules and manages daily HHC exports"""
    
    def __init__(self, hour=6, minute=0):
        """Initialize scheduler for specified time"""
        
    def schedule_daily_export(self):
        """Schedule export to run daily at specified time"""
        
    def run_scheduler(self):
        """Run scheduler loop (blocks - run as background service)"""
        
    def export_now(self):
        """Trigger export immediately"""
        
    def get_export_history(self):
        """Retrieve log of recent exports"""
```

### Step 5: Add Scheduling to Admin Dashboard
**Time Estimate**: 1-2 hours
**Complexity**: Medium

Modify: `src/dashboards/admin_dashboard.py`

Add new control section:
```python
# In HHC View Template tab
with st.expander("⚙️ Export Settings", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        enable_auto_export = st.checkbox("Enable Automated Daily Export")
        
    with col2:
        export_time = st.time_input("Export Time", value=datetime.time(6, 0))
    
    if st.button("Start Scheduler"):
        # Start background scheduler
        pass
    
    # Show export history
    st.subheader("Export History")
    # Display table of recent exports with timestamps, status, row counts
```

### Step 6: Create CLI Tool for Manual Scheduling
**Time Estimate**: 1 hour
**Complexity**: Low-Medium

Create new file: `src/exporters/cli.py`

Usage examples:
```bash
# Run export immediately
python -m src.exporters.cli --export-now

# Start daily scheduler (background service)
python -m src.exporters.cli --schedule --time 6:00

# View export history
python -m src.exporters.cli --history

# Check scheduler status
python -m src.exporters.cli --status
```

### Step 7: Email Notification System
**Time Estimate**: 1-2 hours
**Complexity**: Low-Medium

Integrate email notifications:
- Success emails with export summary (row count, timestamp)
- Failure alerts with error details
- Weekly summary of all exports
- Recipients: Justin, Harpreet, Admin email list

Requirements:
- SMTP server configuration (Gmail, Office 365, etc.)
- Email template design
- Recipient management

### Step 8: Logging and Audit Trail
**Time Estimate**: 1 hour
**Complexity**: Low

Create logging system:
- Log all export attempts (success/failure)
- Store in database table: `export_audit_log`
- Track: timestamp, status, row count, errors, user_id
- Dashboard view of export history

### Step 9: Error Handling and Retry Logic
**Time Estimate**: 1-2 hours
**Complexity**: Medium

Implement resilience:
- Automatic retry on network failures (3 attempts)
- Graceful degradation if Google Sheets unavailable
- Fallback to local CSV backup
- Alert on persistent failures

### Step 10: Testing and Validation
**Time Estimate**: 2-3 hours
**Complexity**: Medium

Test scenarios:
- [ ] Export with 0 patients
- [ ] Export with 100+ patients
- [ ] Google Sheets API unavailable
- [ ] Network timeout during upload
- [ ] Missing credentials file
- [ ] Sheet permissions incorrect
- [ ] Scheduler runs at specified time
- [ ] Email notifications sent
- [ ] Audit log records all attempts

## Implementation Timeline

### Week 1
- Days 1-2: Google Sheets API setup
- Days 3-4: Install dependencies, create export service
- Days 5: Create scheduler module

### Week 2
- Days 1-2: Dashboard integration
- Days 3: CLI tool development
- Days 4-5: Email notifications

### Week 3
- Days 1: Logging system
- Days 2-3: Error handling and retry logic
- Days 4-5: Testing and validation

**Total Estimated Effort**: 3-4 weeks

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│           Admin Dashboard                       │
│  ┌─────────────────────────────────────────┐   │
│  │  HHC View Template Tab                  │   │
│  │  - Display Active Patients              │   │
│  │  - Manual CSV Export                    │   │
│  │  - Auto Export Settings (NEW)           │   │
│  │  - Export History (NEW)                 │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│      HHC Export Service                         │
│  ┌─────────────────────────────────────────┐   │
│  │  - Query Database                       │   │
│  │  - Format Data                          │   │
│  │  - Validate Data                        │   │
│  │  - Sync to Google Sheets                │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
         ↙            ↓            ↘
    ┌────────┐  ┌────────────┐  ┌─────────┐
    │Database│  │Google Sheets API  │Email
    │(SQLite)│  │                  │Service
    └────────┘  └────────────┘  └─────────┘
                      ↓
                ┌────────────┐
                │Google Sheet│
                │(14WJOBq...)│
                └────────────┘
```

## File Structure After Implementation

```
Dev/
├── src/
│   ├── exporters/                    # NEW DIRECTORY
│   │   ├── __init__.py
│   │   ├── hhc_daily_export_service.py
│   │   ├── scheduler.py
│   │   ├── cli.py
│   │   ├── email_notifications.py
│   │   └── audit_logger.py
│   └── dashboards/
│       └── admin_dashboard.py        # MODIFIED
├── google_credentials.json            # NEW (from Google Cloud)
├── logs/
│   └── export_audit.log               # NEW (auto-generated)
└── HHC_VIEW_*                         # Documentation files
```

## Database Schema Changes

### New Table: `export_audit_log`

```sql
CREATE TABLE export_audit_log (
    export_id INTEGER PRIMARY KEY AUTOINCREMENT,
    export_timestamp TEXT NOT NULL,
    export_type TEXT NOT NULL,  -- 'DAILY', 'MANUAL', 'ON_DEMAND'
    status TEXT NOT NULL,  -- 'SUCCESS', 'FAILED', 'PARTIAL'
    row_count INTEGER,
    error_message TEXT,
    execution_time_seconds REAL,
    user_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_export_timestamp ON export_audit_log(export_timestamp);
CREATE INDEX idx_export_status ON export_audit_log(status);
```

## Configuration Requirements

### Environment Variables or Config File
```
HHC_EXPORT_ENABLED=true
HHC_EXPORT_TIME=06:00
HHC_EXPORT_TIMEZONE=America/New_York
HHC_GOOGLE_SHEET_ID=14WJOBqHvxCEQ1i3WynUB6Kwe-4Be78jPrTMWuGUX5oE
HHC_GOOGLE_CREDENTIALS_PATH=google_credentials.json
HHC_EMAIL_ENABLED=true
HHC_EMAIL_RECIPIENTS=justin@example.com,harpreet@example.com
HHC_RETRY_ATTEMPTS=3
HHC_RETRY_DELAY_SECONDS=300
```

## Success Metrics

### Functional Success
- ✅ Daily exports occur at scheduled time
- ✅ 100% of active patient records exported
- ✅ Data accuracy matches source database
- ✅ Zero data loss between exports
- ✅ Google Sheet updates within 5 minutes

### Operational Success
- ✅ Notification emails sent on completion
- ✅ Audit log records all exports
- ✅ Retry logic recovers from transient failures
- ✅ Monitoring alerts on persistent failures
- ✅ Admin dashboard shows export history

### User Success
- ✅ No manual exports needed
- ✅ Data always current in Google Sheets
- ✅ Email confirmations received
- ✅ Dashboard shows last export time
- ✅ Easy to pause/resume exports

## Risk Mitigation

### Data Loss Prevention
- Keep local CSV backup of last export
- Maintain 30-day export history
- Version control for Google Sheets data
- Database transaction logs

### API Failures
- Automatic retry with exponential backoff
- Fallback to local storage
- Manual export option always available
- Alert on consecutive failures

### Unauthorized Access
- Encrypt credentials file
- Use service account (not personal account)
- Limit sheet access to service account
- Audit all API calls

### Scheduling Issues
- Independent scheduler process
- Health checks via monitoring
- Graceful shutdown/startup
- Recovery on application restart

## Rollback Plan

If issues occur post-implementation:

1. **Immediate**: Disable auto-export via dashboard toggle
2. **Short-term**: Revert to manual exports
3. **Medium-term**: Investigate root cause
4. **Long-term**: Fix and re-enable with monitoring

## Future Enhancements (Phase 3)

1. **Smart Scheduling**
   - Export on data changes (event-driven)
   - Conditional exports (only export if data changed)
   - Multiple export schedules per day

2. **Enhanced Filtering**
   - Export only specific patient cohorts
   - Export only changed records (delta sync)
   - Custom export templates

3. **Alternative Destinations**
   - Export to multiple Google Sheets
   - Export to cloud storage (AWS S3, Azure Blob)
   - Export to data warehouse (BigQuery, Snowflake)

4. **Advanced Analytics**
   - Track export metrics over time
   - Alert on data anomalies
   - Trend analysis of patient metrics

5. **Integration Expansion**
   - Slack notifications
   - Microsoft Teams integration
   - Webhooks for external systems

## Support and Maintenance

### Troubleshooting Guide
- Common errors and solutions
- Credential troubleshooting
- Permission issues
- API quota limits

### Monitoring
- Daily health checks
- Export completion verification
- Data quality validation
- Performance metrics

### Maintenance Tasks
- Monthly credential rotation review
- Quarterly API quota review
- Annual system audit
- Documentation updates

## Conclusion

The roadmap provides a clear path to automate the HHC View daily exports, reducing manual effort and ensuring timely data availability. Implementation can proceed incrementally with Phase 1 (current state) providing immediate value while Phases 2 and 3 add automation and advanced features.

---

**Document Version**: 1.0
**Created**: January 2025
**Status**: Planning Phase
**Next Review**: Before Phase 2 Implementation