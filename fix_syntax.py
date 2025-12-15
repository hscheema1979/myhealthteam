#!/usr/bin/env python3
"""Fix syntax errors in admin dashboard"""

def fix_admin_dashboard():
    # Read the file
    with open('src/dashboards/admin_dashboard.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the line with the duplicate "else:" that starts the problematic section
    # This should be around line 3258 (index 3257)
    problem_start = None
    for i in range(3250, len(lines)):
        if lines[i].strip() == 'else:' and i > 3255:
            problem_start = i
            break
    
    if problem_start:
        print(f"Found problematic section starting at line {problem_start + 1}")
        
        # Keep everything up to the problem start, then add proper ending
        new_lines = lines[:problem_start]
        
        # Add the proper else clause ending
        new_lines.append('                else:\n')
        new_lines.append('                    if filtered_workflows_df.empty:\n')
        new_lines.append('                        st.warning("No workflows match your current filters")\n')
        new_lines.append('                    else:\n')
        new_lines.append('                        st.warning("No coordinators available for reassignment")\n')
        
        # Find where the next major section starts (look for except, def, or major indentation)
        resume_start = None
        for i in range(problem_start + 1, len(lines)):
            line = lines[i]
            # Look for patterns that indicate a new major section
            if (line.strip().startswith('except') or 
                line.strip().startswith('def ') or 
                line.strip().startswith('class ') or
                line.strip().startswith('if __name__') or
                (line.strip() and not line.startswith(' '))):  # Non-indented line
                resume_start = i
                break
        
        if resume_start:
            print(f"Resuming from line {resume_start + 1}")
            new_lines.extend(lines[resume_start:])
        else:
            print("Could not find resume point, adding basic ending")
            new_lines.append('\n        except Exception as e:\n')
            new_lines.append('            st.error(f"Error in workflow reassignment: {e}")\n')
        
        # Write back to file
        with open('src/dashboards/admin_dashboard.py', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print("Successfully fixed syntax errors!")
        return True
    else:
        print("Could not find problematic section")
        return False

if __name__ == '__main__':
    fix_admin_dashboard()