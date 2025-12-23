# Datasette Database Browser

A modern web interface for browsing and analyzing your SQLite database.

## 🚀 Quick Start

### Option 1: Batch File (Windows)
Double-click: `run_datasette.bat`

### Option 2: PowerShell
Run: `.\run_datasette.ps1`

### Option 3: Manual Command
```bash
datasette production.db --port 8001
```

Then visit: **http://localhost:8001**

## 📊 What is Datasette?

Datasette is a **web-based SQLite database browser** that provides:
- **Full SQL query interface** in your browser
- **Built-in charting** with Vega visualization
- **Data exploration** without writing code
- **Export options** (CSV, JSON, etc.)
- **Shareable links** to queries and charts

## 🎯 Features for Your Use Case

### 1. **Browse All Tables & Views**
- See all 50+ tables in your database
- View the 7 unified views we created
- Sort, filter, and search data

### 2. **Run SQL Queries**
```sql
-- Minutes per coordinator per month, per facility
SELECT * FROM minutes_per_staff_per_month_per_facility 
WHERE task_type = 'coordinator'
ORDER BY facility_name, staff_name, month DESC;

-- Tasks per provider per month, per facility
SELECT * FROM minutes_per_staff_per_month_per_facility
WHERE task_type = 'provider'
ORDER BY facility_name, staff_name, month DESC;

-- General facility metrics
SELECT * FROM facility_summary;
```

### 3. **Create Charts & Visualizations**
- Bar charts, line charts, scatter plots
- Pie charts for distributions
- Heatmaps for time series
- Export charts as PNG/SVG

### 4. **Export Data**
- Download any query result as CSV
- Export as JSON for APIs
- Copy data to clipboard

## 🗂️ Available Views (Pre-built)

We've created 7 unified views for easy analysis:

### 1. `unified_tasks`
All coordinator and provider tasks combined with standardized columns.

### 2. `unified_tasks_with_facilities`
Tasks with facility information joined.

### 3. `minutes_per_staff_per_month_per_facility` ⭐
**Your requested metric:** Minutes per coordinator/provider per month per facility.
- `facility_name`
- `staff_name` (coordinator or provider)
- `task_type` ('coordinator' or 'provider')
- `month` (YYYY-MM)
- `total_minutes`
- `task_count`
- `unique_patients`
- `avg_minutes_per_task`

### 4. `tasks_per_month_per_facility` ⭐
**Your requested metric:** Tasks per month per facility.
- `facility_name`
- `month`
- `task_type`
- `task_count`
- `total_minutes`
- `unique_staff`
- `unique_patients`

### 5. `staff_performance_summary`
Performance metrics for all staff (coordinators and providers).

### 6. `facility_summary` ⭐
**Your requested metric:** General minutes and tasks per facility.
- `facility_name`
- `total_tasks`
- `total_minutes`
- `avg_minutes_per_task`
- `unique_patients`
- `coordinator_count`
- `provider_count`

### 7. `monthly_trends`
Monthly trends for both coordinator and provider tasks.

## 🎮 How to Use

### Browse Data
1. Go to **http://localhost:8001**
2. Click on any table/view name
3. Use the filter/search boxes
4. Click column headers to sort

### Run SQL Queries
1. Click "View and edit SQL" on any table
2. Write your SQL query
3. Click "Run SQL"
4. Save queries as bookmarks

### Create Charts
1. Run a SQL query
2. Click the "Visualize" button
3. Choose chart type (bar, line, scatter, etc.)
4. Configure X/Y axes
5. Save or export the chart

### Export Data
1. Run a query or view a table
2. Click "Export" button
3. Choose format (CSV, JSON, etc.)
4. Download the file

## 📋 Example Queries

### Minutes per Coordinator per Month, per Facility
```sql
SELECT 
  facility_name,
  staff_name as coordinator_name,
  month,
  total_minutes,
  task_count,
  unique_patients
FROM minutes_per_staff_per_month_per_facility
WHERE task_type = 'coordinator'
ORDER BY total_minutes DESC;
```

### Tasks per Provider per Month, per Facility
```sql
SELECT 
  facility_name,
  staff_name as provider_name,
  month,
  task_count,
  total_minutes,
  unique_patients
FROM minutes_per_staff_per_month_per_facility
WHERE task_type = 'provider'
ORDER BY task_count DESC;
```

### Facility Comparison
```sql
SELECT 
  facility_name,
  total_minutes,
  total_tasks,
  coordinator_count,
  provider_count,
  ROUND(100.0 * coordinator_minutes / total_minutes, 2) as coordinator_pct,
  ROUND(100.0 * provider_minutes / total_minutes, 2) as provider_pct
FROM facility_summary
ORDER BY total_minutes DESC;
```

## 🔧 Advanced Usage

### Save Queries as Bookmarks
1. Run a SQL query
2. Click "Save this query"
3. Give it a name (e.g., "Coordinator Monthly Report")
4. Access it anytime from the homepage

### Create Dashboards
1. Create multiple charts
2. Save each chart query
3. Bookmark the queries
4. Share the bookmark links as a dashboard

### API Access
Datasette provides a JSON API:
- `http://localhost:8001/production.json` - Database metadata
- `http://localhost:8001/production/facility_summary.json` - Table data
- `http://localhost:8001/production.json?sql=SELECT+*+FROM+facility_summary` - Custom query

## 🚨 Troubleshooting

### Port Already in Use
If port 8001 is busy, the script automatically tries 8002. Or manually specify:
```bash
datasette production.db --port 8003
```

### Datasette Not Found
```bash
pip install datasette datasette-vega datasette-copyable datasette-json-html
```

### Slow Queries
- Add indexes on frequently filtered columns
- Use `LIMIT` for exploration
- Filter by date ranges

### Database Locked
Make sure no other process is using `production.db` (like the Streamlit app).

## 📁 File Structure

```
Dev/
├── production.db                    # Your SQLite database
├── create_unified_view.sql          # SQL to create the 7 views
├── run_datasette.bat               # Windows launcher
├── run_datasette.ps1               # PowerShell launcher
├── DATASETTE_README.md             # This file
└── (other existing files...)
```

## 💡 Tips & Tricks

1. **Start with the views** - Use `minutes_per_staff_per_month_per_facility` for your specific needs
2. **Use filters** - Click column values to filter data
3. **Save common queries** - Bookmark frequently used SQL
4. **Export to Excel** - Use CSV export for further analysis
5. **Share insights** - Copy the URL to share specific views

## 🆕 Getting Started

1. **Double-click** `run_datasette.bat`
2. **Open browser** to `http://localhost:8001`
3. **Click on** `minutes_per_staff_per_month_per_facility`
4. **Filter by** `task_type = 'coordinator'`
5. **Visualize** with the chart button

## 📞 Need Help?

- Check the **Datasette documentation**: https://docs.datasette.io
- View **table schemas** by clicking table names
- Use **SQLite syntax** for queries
- Start with **simple queries**, then add complexity

---

**Last Updated**: 2025-12-17  
**Database**: `production.db`  
**Created Views**: 7 unified views for analytics  
**Default Port**: 8001 (falls back to 8002, 8003, etc.)