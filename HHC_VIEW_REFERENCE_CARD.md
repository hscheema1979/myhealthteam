# HHC View Template - Quick Reference Card

## Access
- **Tab Name**: HHC View Template
- **Location**: Admin Dashboard (after Billing Report)
- **Users**: Justin (12), Harpreet (18)
- **Role Required**: Admin (34)

## What's Displayed
A table of all active patients with:
- Patient demographics (name, DOB, contact)
- Location & facility info
- Visit history
- Provider & coordinator assignments
- Insurance & risk assessment
- Clinical notes

## Quick Actions

| Action | How | Result |
|--------|-----|--------|
| Sort | Click column header | Data sorts by that column |
| Filter | Use search box | Shows only matching rows |
| Scroll | Use arrow keys or mouse | See hidden columns |
| Download | Click "📥 Download as CSV" | File: `hhc_patients_YYYYMMDD.csv` |
| Refresh | Click "🔄 Refresh Data" | Updates from database |

## Summary Metrics
- **Total Active Patients**: Count of all active
- **Assigned to Coordinator**: Count with coordinator
- **With Provider**: Count with provider
- **Unassigned**: Count without coordinator

## Key Columns
1. Pt Status
2. Name
3. LAST FIRST DOB
4. Last Visit
5. Contact (Phone)
6. City
7. Facility
8. Provider
9. Care Coordinator
10. Insurance
11. Risk Level
12. Notes

## Common Tasks

### Find Unassigned Patients
1. Click "Assigned" column header
2. Scroll to see all "No" values

### Export Today's Data
1. Click "📥 Download as CSV"
2. File saves to Downloads folder
3. Upload to Google Sheets

### See High-Risk Patients
1. Scroll right to "Risk" column
2. Click "Risk" header to sort
3. High-risk patients grouped at top

### Filter by City
1. Click "City" column header
2. All cities group together

### View Coordinator Assignments
1. Scroll to "Care Coordinator" column
2. Click header to sort
3. See who has how many patients

## Data Sources
- **Database**: production.db
- **Tables**: patients, provider_tasks, users
- **Updated**: Real-time (on demand via Refresh)
- **Status Filter**: active only

## Column Count
26 total columns across:
- Demographics (6)
- Location (2)
- Visits (5)
- Assignments (5)
- Insurance/Status (2)
- Clinical (1)
- Documentation (5)

## Export Format
- **Type**: CSV (Comma-Separated Values)
- **Encoding**: UTF-8
- **Headers**: Yes (first row)
- **Filename**: hhc_patients_YYYYMMDD.csv
- **Compatible**: Google Sheets, Excel, all spreadsheet apps

## Performance
- Query: <1 second
- Display: <500ms
- Total load: <2 seconds
- Works with 656+ patients

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tab not visible | Check user ID (must be 12 or 18) |
| No data | Click Refresh Data button |
| CSV won't download | Check browser pop-up settings |
| Slow performance | Wait for refresh, check connection |
| Missing columns | Scroll right, columns may be hidden |

## Database Query
```sql
SELECT p.patient_id, p.status, p.first_name, p.last_name,
       p.phone_primary, p.address_city, p.facility,
       p.last_visit_date, p.insurance_primary,
       pr.first_name || ' ' || pr.last_name as provider,
       c.first_name || ' ' || c.last_name as coordinator,
       p.subjective_risk_level, p.notes
FROM patients p
LEFT JOIN provider_tasks pt ON p.patient_id = pt.patient_id
LEFT JOIN users pr ON pt.provider_id = pr.user_id
LEFT JOIN users c ON p.assigned_coordinator_id = c.user_id
WHERE LOWER(p.status) = 'active'
ORDER BY p.last_name, p.first_name
```

## Code Location
- **File**: Dev/src/dashboards/admin_dashboard.py
- **Tab Content**: Lines 2952-3097
- **Tab Registration**: Lines 335-336
- **Tab Assignment**: Line 402

## Related Documentation
- **User Guide**: HHC_VIEW_QUICK_START.md
- **Technical Specs**: HHC_VIEW_TECHNICAL_SPEC.md
- **Implementation**: HHC_VIEW_IMPLEMENTATION.md
- **Roadmap**: HHC_VIEW_DAILY_EXPORT_ROADMAP.md

## Future Features (Planned)
- [ ] Scheduled daily exports
- [ ] Auto-sync to Google Sheets
- [ ] Email notifications
- [ ] Advanced filtering
- [ ] Bulk operations
- [ ] Export history log

## Keyboard Shortcuts (Streamlit)
- `/` - Open search/filter
- `Ctrl+F` - Browser find
- `Arrow Keys` - Navigate table
- `Escape` - Close dialogs

## Tips
- ✓ Download CSV daily for backup
- ✓ Use search to find specific patients
- ✓ Sort by Risk to prioritize high-acuity
- ✓ Check Assigned column for unassigned patients
- ✓ Refresh before major decisions
- ✓ CSV file includes all columns (even hidden ones)

## Support Contacts
- **Questions**: See HHC_VIEW_QUICK_START.md
- **Technical Issues**: Check error message in dashboard
- **Feature Requests**: Contact development team
- **Admin Access**: Contact system administrator

---

**Version**: 1.0 | **Updated**: January 2025 | **Status**: Active