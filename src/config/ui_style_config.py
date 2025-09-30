# UI Style Configuration for Healthcare Management System
# This file contains consistent styling rules and conventions

# =============================================================================
# CONTENT STYLE RULES
# =============================================================================

# Emoji Usage Policy
USE_EMOJIS = False  # Set to False for professional healthcare environment
"""
Healthcare applications should maintain a professional appearance.
Emojis can be distracting in clinical and administrative contexts.
"""

# Text Formatting Rules
class TextStyle:
    # Header styles (consistent across all dashboards)
    H1_PREFIX = ""  # No emojis in main headers
    H2_PREFIX = ""  # No emojis in subheaders
    H3_PREFIX = ""  # No emojis in section headers
    
    # Professional alternatives to common emojis
    ALERT_INDICATOR = "ALERT"  # Instead of ⚠️
    SUCCESS_INDICATOR = "SUCCESS"  # Instead of ✅
    ERROR_INDICATOR = "ERROR"  # Instead of ❌
    INFO_INDICATOR = "INFO"  # Instead of ℹ️
    
    # Priority indicators
    HIGH_PRIORITY = "[HIGH]"  # Instead of 🔥
    MEDIUM_PRIORITY = "[MEDIUM]"  # Instead of 📊
    LOW_PRIORITY = "[LOW]"  # Instead of 📋

# =============================================================================
# DASHBOARD SECTION NAMING CONVENTIONS
# =============================================================================

class SectionTitles:
    # Performance sections
    COORDINATOR_PERFORMANCE = "Coordinator Performance"
    PROVIDER_PERFORMANCE = "Provider Performance" 
    PATIENT_SERVICE_ANALYSIS = "Patient Service Analysis"
    
    # Data sections
    CURRENT_MONTH = "Current Month Performance"
    HISTORICAL_DATA = "Historical Performance Data"
    DETAILED_RECORDS = "Detailed Patient Service Records"
    SERVICE_BREAKDOWN = "Patient Service Breakdown by Month"
    SERVICE_CHARTS = "Service Analysis Charts"
    SERVICE_DISTRIBUTION = "Service Type Distribution"
    
    # Administrative sections
    ONBOARDING_QUEUE = "Onboarding Queue"
    TASK_MANAGEMENT = "Task Management"
    PATIENT_ASSIGNMENTS = "Patient Assignments"

# =============================================================================
# METRIC DISPLAY RULES
# =============================================================================

class MetricStyle:
    # Current month metrics should be highlighted but professionally
    CURRENT_MONTH_PREFIX = "Current Month"  # Instead of 🔥
    
    # Standard metric labels
    TASKS_COMPLETED = "Tasks Completed"
    TOTAL_MINUTES = "Total Minutes"
    PATIENTS_SERVED = "Patients Served"
    UTILIZATION_RATE = "Utilization Rate"
    AVG_MINUTES_PER_PATIENT = "Avg Minutes/Patient"
    TOTAL_PATIENTS_SERVED = "Total Patients Served"

# =============================================================================
# COLOR AND VISUAL INDICATORS
# =============================================================================

class ColorScheme:
    # Professional color palette for healthcare
    PRIMARY_BLUE = "#1f77b4"
    SUCCESS_GREEN = "#2ca02c"
    WARNING_ORANGE = "#ff7f0e"
    ERROR_RED = "#d62728"
    NEUTRAL_GRAY = "#7f7f7f"
    
    # Status indicators using colors instead of emojis
    CURRENT_MONTH_COLOR = "#1f77b4"  # Blue for current period
    HISTORICAL_COLOR = "#7f7f7f"     # Gray for historical data
    HIGH_PRIORITY_COLOR = "#d62728"   # Red for high priority
    MEDIUM_PRIORITY_COLOR = "#ff7f0e" # Orange for medium priority
    LOW_PRIORITY_COLOR = "#2ca02c"    # Green for low priority

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_section_title(base_title: str, add_emoji: bool = None) -> str:
    """
    Get section title with or without emoji based on configuration
    
    Args:
        base_title: The base title text
        add_emoji: Override the global USE_EMOJIS setting if provided
    
    Returns:
        Formatted title string
    """
    use_emoji = add_emoji if add_emoji is not None else USE_EMOJIS
    if use_emoji:
        # Legacy emoji mapping (disabled by default)
        emoji_map = {
            "Coordinator Performance": "📊 Coordinator Performance",
            "Provider Performance": "🏥 Provider Performance",
            "Patient Service Analysis": "🔍 Patient Service Analysis",
            "Current Month Performance": "🔥 Current Month Performance",
        }
        return emoji_map.get(base_title, base_title)
    else:
        return base_title

def get_metric_label(metric_type: str, is_current_month: bool = False) -> str:
    """
    Get professional metric label without emojis
    
    Args:
        metric_type: Type of metric (tasks, minutes, patients, etc.)
        is_current_month: Whether this is current month data
    
    Returns:
        Professional metric label
    """
    prefix = MetricStyle.CURRENT_MONTH_PREFIX + " " if is_current_month else ""
    
    metric_labels = {
        "tasks": MetricStyle.TASKS_COMPLETED,
        "minutes": MetricStyle.TOTAL_MINUTES,
        "patients": MetricStyle.PATIENTS_SERVED,
        "utilization": MetricStyle.UTILIZATION_RATE
    }
    
    return prefix + metric_labels.get(metric_type, metric_type.title())

# =============================================================================
# USAGE EXAMPLES AND DOCUMENTATION
# =============================================================================

"""
USAGE EXAMPLES:

1. Section Headers:
   st.header(get_section_title("Coordinator Performance"))  # No emojis
   
2. Metric Labels:
   col1.metric(get_metric_label("tasks", True), value)  # "Current Month Tasks Completed"
   
3. Professional Indicators:
   st.info(f"{TextStyle.INFO_INDICATOR}: Data updated successfully")
   
4. Priority Levels:
   st.markdown(f"{TextStyle.HIGH_PRIORITY} Urgent patient requires attention")

CUSTOMIZATION:
- Set USE_EMOJIS = True to re-enable emojis globally
- Modify TextStyle class for different professional indicators
- Update ColorScheme for different visual themes
- Add new section titles to SectionTitles class

CONSISTENCY RULES:
1. All dashboard headers should use get_section_title()
2. All metrics should use get_metric_label()  
3. Status indicators should use TextStyle constants
4. Colors should reference ColorScheme constants
5. No hardcoded emojis in any component
"""