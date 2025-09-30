import re

def extract_system_prefix(name):
    """Returns 'ZEN' if the patient name starts with 'ZEN-', else None."""
    if not isinstance(name, str):
        return None
    m = re.match(r'^(ZEN)-', name)
    return m.group(1) if m else None

def extract_last_name(name):
    """Extracts the full last name (including hyphens) from PSL patient name format, after removing 'ZEN-' if present."""
    if not isinstance(name, str):
        return None
    # Remove 'ZEN-' prefix if present
    name = re.sub(r'^ZEN-', '', name)
    # Extract last name before comma
    m = re.match(r'^([\w-]+),', name)
    return m.group(1) if m else None

# Example usage:
# name = 'ZEN-Barajas-Mejia, Maria 01/01/1980'
# print(extract_system_prefix(name))  # Output: 'ZEN'
# print(extract_last_name(name))      # Output: 'Barajas-Mejia'
