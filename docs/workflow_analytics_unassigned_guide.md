# Workflow Analytics & Unassigned Patient Management - User Guide

## Overview

This new tab provides two powerful features for managing workflows and patient assignments across three dashboards:
- **Admin Dashboard**
- **Care Coordinator Dashboard** (for users with management roles: Lead Coordinator or Coordinator Manager)
- **Coordinator Manager Dashboard**

## Feature 1: Workflow Analytics & Monitoring

### What It Does

Provides comprehensive monitoring of workflow performance with:

#### 1.1 Step-Level Metrics (FR-2.1)
- **Completion Time**: Average days to complete each workflow step
- **Throughput**: Number of instances processed through each step
- **Expected vs Actual**: Compare expected cycle time to actual performance
- **Per-Step Breakdown**: View performance for each individual step in every workflow template

**Use Case**: Identify bottlenecks in your workflow process by seeing which steps take longer than expected.

#### 1.2 Delay Tracking (FR-2.2)
- **Delayed Workflows**: Flagged when exceeding 150% of expected cycle time (internal benchmark)
- **Late Workflows**: Flagged when exceeding 200% of expected cycle time (hard deadline)
- **Real-time Monitoring**: Automatic calculation of days in workflow vs. expected time

**Use Case**: Proactively manage at-risk workflows before they become critical issues.

#### 1.3 Stagnation Alerts (FR-2.3)
- **Configurable Threshold**: Default 48 hours (adjustable from 24-120 hours)
- **No Activity Detection**: Identifies workflows with no status changes or updates
- **Prioritized List**: Shows most stagnant workflows first (longest time since update)

**Use Case**: Ensure workflows keep moving and don't get stuck due to inactivity.

### How to Use

1. **Navigate to the Tab**: Click "Analytics & Unassigned" tab in your dashboard
2. **View Summary Metrics**: Top section shows:
   - Total Active Workflows
   - Completed This Week
   - Average Completion Time
   - Delayed/Late counts

3. **Drill Down**:
   - **Step-Level Metrics**: See performance per step
   - **Delay Tracking**: View delayed and late workflows with details
   - **Stagnation Alerts**: Adjust threshold slider and see stagnant workflows

### Interpreting the Data

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Avg Completion Time | < Expected | 1.5x Expected | > 2x Expected |
| Delayed Count | 0 | < 5 | > 10 |
| Late Count | 0 | 0 | > 0 |
| Stagnant Workflows | 0 | < 3 | > 5 |

## Feature 2: Unassigned Patient Management

### What It Does

Manages patients who are missing critical assignments (coordinator or provider) with two custom views:

#### 2.1 Andrew's View (FR-3.1)
- **Focus**: Patients without **coordinator** assignment
- **Sorting**: By facility, then by last name
- **Priority Indicators**:
  - `[HIGH]` - No visit on record OR > 60 days since last visit
  - `[MEDIUM]` - 30-60 days since last visit
  - `[LOW]` - < 30 days since last visit

**Use Case**: Andrew needs to quickly identify and assign coordinators to unassigned patients, prioritizing those who haven't been seen recently.

#### 2.2 Jan's View (FR-3.1)
- **Focus**: Patients without **provider** assignment
- **Sorting**: By last visit date (oldest first - most urgent)
- **Urgency Indicators**:
  - `NEVER VISITED` - No visit on record
  - `URGENT (X days)` - > 90 days since last visit
  - `HIGH (X days)` - 60-90 days since last visit
  - `MEDIUM (X days)` - 30-60 days since last visit
  - `LOW (X days)` - < 30 days since last visit

**Use Case**: Jan needs to see patients by urgency of care (time since last visit) to assign providers.

#### 2.3 Unassigned Logic (FR-3.2)
- **Filters**: Only shows patients with `status = 'Active'`
- **Unassigned Criteria**:
  - `coordinator_id IS NULL` OR `coordinator_id = 0`
  - OR `provider_id IS NULL` OR `provider_id = 0`
- **Excludes**: Patients with any status other than 'Active'

### How to Use

1. **Navigate to the Tab**: Click "Analytics & Unassigned" tab
2. **Switch to "Unassigned Patients" sub-tab**
3. **Select a View**:
   - Click "Andrew's View" for coordinator assignment
   - Click "Jan's View" for provider assignment

4. **Assign Patients**:
   - Check the "Select" checkbox for patients to assign
   - Click "Assign Selected Patients" button
   - Choose the appropriate coordinator or provider
   - Add optional notes
   - Confirm assignment

### Workflow Assignment Process

For Andrew's View (Coordinator Assignment):
1. Review priority indicators - focus on `[HIGH]` priority patients first
2. Consider facility grouping - assign coordinators who already cover that facility
3. Check patient notes for context
4. Select patients and assign

For Jan's View (Provider Assignment):
1. Review urgency indicators - focus on `NEVER VISITED` and `URGENT` patients first
2. Consider provider workload and specialties
3. Check patient notes for context
4. Select patients and assign

## Dashboard-Specific Access

### Admin Dashboard
- **Access**: Users with Admin role (role_id = 34) or Coordinator Manager role (role_id = 40)
- **Full Access**: All features, including billing (for specific users)
- **Tab Location**: "Workflow Analytics & Unassigned" (after ZMO)

### Care Coordinator Dashboard
- **Access**: Users with management roles:
  - Lead Coordinator (role_id = 37)
  - Coordinator Manager (role_id = 40)
- **Limited Access**: Workflow analytics and unassigned patients for their teams
- **Tab Location**: "Analytics & Unassigned" (appears when user has management role)

### Coordinator Manager Dashboard
- **Access**: Users with Coordinator Manager role (role_id = 40)
- **Full Access**: All features for managing coordinator team
- **Tab Location**: "Analytics & Unassigned" (dedicated tab)

## Best Practices

### Workflow Analytics

1. **Check Daily**: Review stagnation alerts to ensure workflows keep moving
2. **Weekly Review**: Analyze step-level metrics to identify process bottlenecks
3. **Proactive Management**: Address delayed workflows before they become late
4. **Trend Analysis**: Monitor average completion time over weeks to spot trends

### Unassigned Patients

1. **Daily Assignment**: Assign new unassigned patients within 24 hours
2. **Priority-Based**: Always address HIGH priority or URGENT patients first
3. **Load Balancing**: Consider current workload when assigning coordinators/providers
4. **Facility Alignment**: Assign staff who already work at the patient's facility

### Data Quality

1. **Verify Accuracy**: Check that coordinator_id and provider_id are correctly set
2. **Update Status**: Ensure patient status is 'Active' for patients in active care
3. **Document Notes**: Use notes field to explain assignment decisions
4. **Audit Trail**: All assignments are logged in the audit_log table

## Troubleshooting

### Issue: No data showing in Workflow Analytics
**Cause**: No active workflows in system
**Solution**: Create workflow instances for patients using the Workflow Assignment tab

### Issue: Stagnation alerts show many workflows
**Cause**: Threshold too low OR workflows actually stuck
**Solution**: Adjust threshold slider OR investigate specific workflows for blockers

### Issue: Unassigned patients list is empty
**Cause**: All active patients have both coordinator and provider assigned
**Solution**: This is good! No action needed unless you need to reassign

### Issue: Can't see the tab in my dashboard
**Cause**: Missing required role
**Solution**:
- Admin Dashboard: Need Admin (34) or Coordinator Manager (40) role
- Care Coordinator Dashboard: Need Lead Coordinator (37) or Coordinator Manager (40) role
- Coordinator Manager Dashboard: Need Coordinator Manager (40) role

### Issue: Assignment fails
**Cause**: Missing required fields OR database connection error
**Solution**:
- Verify patient_id is valid
- Check coordinator/provider ID is valid
- Ensure database connection is active
- Check error message for specific details

## Technical Details

### Database Tables Used

- `workflow_instances`: Active workflow tracking
- `workflow_templates`: Workflow template definitions
- `workflow_steps`: Individual step definitions
- `patients`: Patient master data
- `patient_assignments`: Coordinator and provider assignments
- `users`: User information for coordinators and providers
- `audit_log`: Assignment history and changes

### Performance

- **Caching**: Workflow analytics data cached for 5 minutes (300 seconds)
- **Query Optimization**: Uses indexed columns for fast filtering
- **Refresh**: Automatic refresh when switching tabs or clicking rerun

### Security

- **Role-Based Access**: Tab only visible to authorized roles
- **Audit Logging**: All assignments logged with user_id and timestamp
- **Data Isolation**: Coordinators only see their team's data (not all-coordinator view)

## Future Enhancements

Potential future improvements:
1. **Bulk Assignment**: Assign multiple patients to same coordinator/provider at once
2. **Assignment Recommendations**: AI-powered suggestions based on workload and geography
3. **Email Notifications**: Alerts for delayed or stagnant workflows
4. **Export Functionality**: Download workflow analytics as CSV/Excel
5. **Historical Trends**: Track workflow performance over time with charts
6. **Mobile View**: Optimized layout for mobile devices

## Support

For questions or issues:
1. Check this guide first
2. Review error messages carefully
3. Check browser console for technical errors
4. Contact system administrator with:
   - Screenshot of error
   - Steps to reproduce
   - Browser and version
   - User role and ID

## Version History

- **v1.0** (2026-03-05): Initial release with Workflow Analytics and Unassigned Patient Management
  - FR-2.1: Step-level metrics
  - FR-2.2: Delay and late tracking
  - FR-2.3: Stagnation alerts
  - FR-3.1: Andrew's View and Jan's View
  - FR-3.2: Unassigned patient logic

---

**Document Version**: 1.0
**Last Updated**: March 5, 2026
**Author**: AI Agent (Claude)
