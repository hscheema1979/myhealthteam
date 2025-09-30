# Provider Dashboard Patient Panel Column Order Redesign

## Objective

Reorder and augment the provider dashboard patient panel columns to match the client’s required order and ensure all columns are present, even if null.

## Required Column Order

1. status/goc (show column even if null)
2. code (show column even if null)
3. pt name
4. facility
5. cc name
6. last visit date
7. service type
8. phone number

## Steps

1. Locate the provider dashboard patient panel code.
2. Identify the DataFrame or data structure used for the patient panel.
3. Add missing columns (status/goc, code) if not present, ensuring they display even if all values are null.
4. Reorder columns to match the required order.
5. Test with patients missing these fields to confirm columns still appear.
6. Validate with the client for sign-off.

## Tracking

- [x] Code located and reviewed
- [x] Columns added and reordered
- [x] Null data tested
- [ ] Client validation

---

**Owner:** GitHub Copilot
**Start Date:** 2025-09-24
**Status:** Not Started
