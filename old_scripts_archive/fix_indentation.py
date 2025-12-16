#!/usr/bin/env python3
"""
Fix indentation issues in the transform file
"""

def fix_indentation():
    print("Fixing indentation issues...")
    
    # Read the file
    with open('transform_production_data_v3_fixed copy.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Fix the specific indentation issue around line 127
    # The issue is that line 127 has extra indentation
    
    fixed_lines = []
    for i, line in enumerate(lines):
        line_num = i + 1
        
        if line_num == 127:  # The problematic line
            # This line should have the same indentation as the previous line
            if i > 0:
                # Get the indentation from the previous line
                prev_line = lines[i-1]
                indent = len(prev_line) - len(prev_line.lstrip())
                fixed_line = ' ' * indent + line.lstrip()
                fixed_lines.append(fixed_line)
                print(f"Fixed line {line_num}: {repr(fixed_line)}")
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Write the fixed content back
    with open('transform_production_data_v3_fixed.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("Indentation fixed!")

if __name__ == "__main__":
    fix_indentation()