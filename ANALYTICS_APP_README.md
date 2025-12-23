# Analytics & Metrics Dashboard

Standalone Streamlit application for flexible metrics exploration and visualization.

## Running the Analytics App

The analytics dashboard runs as a **separate Streamlit instance** from the main application.

### Start the analytics app on port 8505:

```bash
streamlit run analytics_app.py --server.port 8505
```

Or use any other port you prefer (8506, 8507, etc.):

```bash
streamlit run analytics_app.py --server.port 8506
```

### Access the app:

Once running, navigate to:
```
http://localhost:8505
```

## Features

### User-Controllable Metrics Dashboard

**Four main tabs:**

1. **Coordinators** - Analyze coordinator performance
   - Filter by coordinator, facility, date range
   - Metrics: minutes/month, tasks/month, avg duration, minutes/patient
   - Interactive visualizations with multiple chart types

2. **Providers** - Analyze provider visits and billing
   - Filter by provider, facility, date range
   - Metrics: visits/month, visit types, minutes, avg duration, patients served
   - Interactive visualizations with multiple chart types

3. **Facilities** - Aggregated facility-level data
   - Filter by facility, date range
   - Metrics: total minutes, visits, patient count, billable tasks
   - Breakdown by coordinator vs provider
   - Data transfer tracking (CM LOG, PSI, ZMO, PROVIDER ONBOARDING)

4. **Comparison** - Side-by-side analysis
   - Compare multiple coordinators, providers, or facilities
   - Interactive comparative visualizations

### Interactive Visualization with Plotly & Streamlit

Users can:
- Select from multiple chart types (bar, line, scatter, box)
- Choose X and Y axes dynamically
- Hover over data points for detailed information
- Download charts as PNG
- View raw data in table format

## Requirements

```bash
pip install streamlit plotly pandas streamlit-elements
```

## Authentication

- Requires admin role (role_id = 34) to access
- Uses existing application authentication system
- Login via sidebar form

## Database

Uses the same SQLite database as the main application (production.db or prototype.db based on USE_PROTOTYPE_MODE flag).

Data sources:
- `coordinator_tasks_YYYY_MM` tables
- `provider_tasks_YYYY_MM` tables
- `coordinators`, `providers`, `facilities` master tables
- `patient_assignments` for patient counts
