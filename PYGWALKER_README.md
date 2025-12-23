# PyGWalker Data Visualization

Load all unified views into PyGWalker for interactive data exploration.

## 🚀 Quick Start

### Option 1: Batch File (Windows)
Double-click: `run_pygwalker.bat`

### Option 2: PowerShell
Run: `.\run_pygwalker.ps1`

### Option 3: Manual Command
```bash
# Using conda (recommended)
conda run -n base python simple_pygwalker.py

# Using system Python
python simple_pygwalker.py
```

## 📊 What This Does

Loads all 7 unified views into **ONE PyGWalker instance**:
1. `unified_tasks` - All coordinator and provider tasks combined
2. `unified_tasks_with_facilities` - Tasks with facility information
3. `minutes_per_staff_per_month_per_facility` - Minutes per coordinator/provider per month per facility ⭐
4. `tasks_per_month_per_facility` - Tasks per month per facility ⭐
5. `staff_performance_summary` - Staff performance metrics
6. `facility_summary` - Facility-level summaries ⭐
7. `monthly_trends` - Monthly trends for all tasks

Each row has a `_view_name` column to filter by dataset.

## 🎯 Your Requested Metrics (Ready to Use)

### Minutes per Coordinator per Month, per Facility
In PyGWalker:
1. Filter by `_view_name = 'minutes_per_staff_per_month_per_facility'`
2. Filter by `task_type = 'coordinator'`
3. Drag columns to create charts

### Tasks per Provider per Month, per Facility
In PyGWalker:
1. Filter by `_view_name = 'minutes_per_staff_per_month_per_facility'`
2. Filter by `task_type = 'provider'`
3. Create visualizations

### General Minutes per Month per Facility
In PyGWalker:
1. Filter by `_view_name = 'tasks_per_month_per_facility'`
2. Use `facility_name`, `month`, `total_minutes` columns
3. Create charts

## 🎮 How to Use PyGWalker

### Basic Workflow:
1. **Run the script** (`run_pygwalker.bat`)
2. **Browser opens** with PyGWalker interface
3. **Filter data** using the right panel
4. **Drag columns** to X/Y axes for charts
5. **Export results** using PyGWalker tools

### Filtering:
- Use `_view_name` to select specific views
- Filter by `facility_name`, `staff_name`, `month`, etc.
- Apply date ranges and value filters

### Creating Charts:
1. **Drag** a column (e.g., `total_minutes`) to Y-axis
2. **Drag** another column (e.g., `facility_name`) to X-axis
3. **Choose chart type** from toolbar
4. **Add color** by dragging a third column

## 📋 Example Analyses

### Coordinator Performance
1. Filter: `_view_name = 'minutes_per_staff_per_month_per_facility'`
2. Filter: `task_type = 'coordinator'`
3. X-axis: `staff_name`
4. Y-axis: `total_minutes`
5. Chart: Bar chart

### Facility Comparison
1. Filter: `_view_name = 'facility_summary'`
2. X-axis: `facility_name`
3. Y-axis: `total_minutes`
4. Color: `coordinator_minutes` vs `provider_minutes`

### Monthly Trends
1. Filter: `_view_name = 'monthly_trends'`
2. X-axis: `month`
3. Y-axis: `total_minutes`
4. Color: `task_type`
5. Chart: Line chart

## 🚨 Troubleshooting

### PyGWalker Not Found
```bash
# Using conda (recommended)
conda install -c conda-forge pygwalker pandas

# Using pip
pip install pygwalker pandas
```

### Browser Won't Open
- Check if port 8050 is in use
- Try: `python simple_pygwalker.py` and manually go to `http://localhost:8050`

### Data Too Large
- Script limits to 5000 rows per view for performance
- Modify `LIMIT 5000` in `simple_pygwalker.py` if needed

### No Data Loaded
- Verify `production.db` exists
- Check that views were created (`create_unified_view.sql`)

## 📁 File Structure

```
Dev/
├── simple_pygwalker.py        # Main PyGWalker script
├── run_pygwalker.bat          # Windows launcher
├── run_pygwalker.ps1          # PowerShell launcher
├── PYGWALKER_README.md        # This file
├── production.db              # Your database
├── create_unified_view.sql    # SQL to create views
└── (other files...)
```

## 💡 Tips

1. **Start with filters** - Use `_view_name` to focus on one dataset
2. **Save configurations** - PyGWalker saves your layout automatically
3. **Export charts** - Use the export button in PyGWalker
4. **Combine views** - Use `_view_name` as a grouping column
5. **Date filtering** - Filter by `month` column for time ranges

## 🆕 Getting Started

1. **Double-click** `run_pygwalker.bat`
2. **Wait** for browser to open
3. **Filter** by `_view_name = 'minutes_per_staff_per_month_per_facility'`
4. **Create** your first chart
5. **Explore** all 7 views

## 📞 Need Help?

- Check PyGWalker documentation: https://docs.kanaries.net/pygwalker
- Use the **filter panel** on the right
- Start with **simple bar charts**
- Combine **multiple filters** for detailed analysis

---
**Last Updated**: 2025-12-17
**Views Loaded**: 7 unified views
**Default Port**: 8050 (PyGWalker default)