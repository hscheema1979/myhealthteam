# Coordinator Dashboard Patient Panel Column Order Redesign

## Objective

Reorder and augment the coordinator dashboard patient panel columns to match the client’s required order and ensure all columns are present, even if null.

## Required Column Order

1. status
2. patient name
3. facility
4. provider name
5. provider’s last visit date of service or task date
6. service type
7. phone number

## Steps

1. Locate the coordinator dashboard patient panel code.
2. Identify the DataFrame or data structure used for the patient panel.
3. Add missing columns if not present, ensuring they display even if all values are null.
4. Reorder columns to match the required order.
5. Test with patients missing these fields to confirm columns still appear.
6. Validate with the client for sign-off.

## Tracking

- [ ] Code located and reviewed
- [ ] Columns added and reordered
- [ ] Null data tested
- [ ] Client validation

---

**Owner:** GitHub Copilot
**Start Date:** 2025-09-24
**Status:** Not Started
