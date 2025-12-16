#!/usr/bin/env python3
"""Temporary script to fix the duplicate code issue"""

# Read the file
with open('src/dashboards/admin_dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the duplicate section starting at line 3259 (index 3258)
# Look for the second occurrence of "Add selection column"
duplicate_start = None
add_selection_count = 0

for i, line in enumerate(lines):
    if 'Add selection column' in line:
        add_selection_count += 1
        if add_selection_count == 2:
            duplicate_start = i
            break

if duplicate_start:
    print(f"Found duplicate section starting at line {duplicate_start + 1}")
    
    # Find the end of the duplicate section (look for the next major section break)
    # We'll look for the next occurrence of a major indentation change or section
    duplicate_end = None
    for i in range(duplicate_start + 1, len(lines)):
        line = lines[i]
        # Look for the next major section break (like a new tab or major function)
        if i > duplicate_start + 50:  # Minimum lines to avoid small blocks
            # Look for patterns that indicate end of this section
            if line.strip() == '' or line.startswith('    elif ') or line.startswith('    if ') or line.startswith('def '):
                # Go back to find the last meaningful line
                for j in range(i-1, duplicate_start, -1):
                    if lines[j].strip() and not lines[j].startswith('#'):
                        duplicate_end = j + 1
                        break
                break
    
    if duplicate_end:
        print(f"Duplicate section ends at line {duplicate_end}")
        print(f"Removing lines {duplicate_start + 1} to {duplicate_end}")
        
        # Keep everything up to the duplicate start, then add a simple else clause
        new_lines = lines[:duplicate_start]
        
        # Add simplified else clause
        new_lines.append('                else:\n')
        new_lines.append('                    if filtered_workflows_df.empty:\n')
        new_lines.append('                        st.warning("No workflows match your current filters")\n')
        new_lines.append('                    else:\n')
        new_lines.append('                        st.warning("No coordinators available for reassignment")\n')
        
        # Add the rest of the file from the original ending
        new_lines.extend(lines[duplicate_end:])
        
        # Write back to file
        with open('src/dashboards/admin_dashboard.py', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print("Successfully removed duplicate code!")
    else:
        print("Could not find end of duplicate section")
else:
    print("Could not find duplicate section")