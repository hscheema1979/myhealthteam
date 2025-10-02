This is a much cleaner and more structured way to present your request. I've organized it into clear sections with specific, actionable requirements.
Project Request: Weekly Billing Report (P00)
Goal
Create a new automated weekly billing report system to track and manage the status of all provider tasks from creation through final payment.
Data Source
The core data source for the report will be the weekly files: provider_tasks_YYYY_WW.
Weekly Billing Cycle & Logic
 * Report Generation: The report will be generated weekly, covering tasks up to the designated billing cutoff date.
 * Billing Status Assignment: On the Saturday of the billing week, all tasks included in that week's report will be permanently tagged as "Billed" in the master log (provider_tasks_YYYY_MM). The report must clearly show the original Task Creation Date for all tasks.
 * Late Task Handling (Carryover):
   * If a provider's tasks are not entered into the system by the weekly Saturday cutoff, they will be marked "Not Billed" for that cycle.
   * The subsequent weekly billing report must automatically identify all tasks currently marked "Not Billed" (from previous weeks) and include them in the new cycle, assigning them the "Billed" tag once processed.
Required Billing Status Tracking
The system must track and display the following billing states. Integration with the existing master log and external data sources is required.
| Billing Status | Data Source/Dependency |
|---|---|
| Not Billed | Internal System Tracking |
| Billed | Assigned by Weekly Report Logic |
| Invoiced | Internal System Tracking |
| Claim Submitted | External: Requires data integration from Nathan's Sheets |
| Insurance Processed | External: Requires data integration from Nathan's Sheets |
| Approve to Pay | External: Requires data integration from Nathan's Sheets |
| Paid | External: Requires data integration from Nathan's Sheets |
Action Item: Identifying Missing Data
 * Problem: We currently have no reliable way to track or flag when providers are late or missing task logs altogether.
 * Next Step: Schedule a discussion with Andrew and Justin to define a reliable process and corresponding metrics for tracking and alerting on missing provider task entries. This tracking mechanism must be integrated into the final solution.
Does this capture all the necessary requirements, and what's the planned delivery date for this project?
