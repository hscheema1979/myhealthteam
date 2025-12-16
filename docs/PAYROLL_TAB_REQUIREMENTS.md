# Task 4: Weekly Provider Payroll Tab - Requirements Needed

## Current Status
Found the Weekly Billing Dashboard (`weekly_billing_dashboard.py`). It tracks:
- Billing weeks and months
- Provider task data (patient visits, minutes of service)
- Billing codes and status tracking
- Payment pipeline (billed → invoiced → paid)

## What I Need to Know

### 1. Payroll Data to Display
**Options:**
- A) Total hours worked per provider per week
- B) Calculated pay (hours × rate)
- C) Task breakdown by type (billable vs non-billable)
- D) All of the above

### 2. Pay Rate Storage
**Do you have provider pay rates?**
- Stored in database? (which table/column?)
- Manually configured?
- Fixed rate for all providers or varies by provider?
- Different rates for different task types?

### 3. Time Period View
- Weekly (match billing dashboard)?
- Monthly?
- Both with tabs?

### 4. Key Metrics
What's most important to track:
- [ ] Total minutes worked
- [ ] Total hours worked (minutes/60)
- [ ] Gross pay amount
- [ ] Task count by type
- [ ] Patient count
- [ ] Efficiency metrics (tasks per hour?)

### 5. Data Source
- Use `provider_tasks` table (same as billing)?
- Filter out `billing_code = "Not_Billable"` tasks?
- Or include all tasks regardless of billing status?

## Next Steps
Once requirements clarified, I can:
1. Create the payroll calculation queries
2. Add tab next to Weekly Billing in admin dashboard
3. Design similar UI to billing dashboard
4. Test with real provider data

## Question for User
**What should the Weekly Provider Payroll tab show, and where are pay rates stored?**
