# Admin Dashboard: Facility Home Health View Reports Tab

## Objective

Add a new tab to the admin dashboard for Facility Home Health View Reports, with a facility-based patient table containing all required columns in the specified order.

## Required Columns (in order)

- status
- patient status
- last task date
- last visit type
- patient name (LAST FIRST DOB)
- contact
- name
- city
- facility
- initial TV provider assigned
- insurance eligibility
- assigned provider
- care coordinator
- prescreen call notes
- initial TV date
- initial TV notes
- initial HV date
- labs notes (from latest LAB workflow)
- imaging notes (from latest IMAGING workflow)
- general notes (from provider/coordinator)

## Steps

1. Add a new tab to the admin dashboard: "Facility Home Health View Reports".
2. Build a facility-based patient table with all required columns, in the specified order.
3. Ensure all columns are present, even if some data is missing.
4. For labs/imaging/general notes, pull the latest relevant workflow notes.
5. Test with various facilities and patients.
6. Validate with the client for sign-off.

## Tracking

- [ ] Tab added
- [ ] Table built with all columns
- [ ] Null/missing data tested
- [ ] Client validation

---

**Owner:** GitHub Copilot
**Start Date:** 2025-09-24
**Status:** Not Started
