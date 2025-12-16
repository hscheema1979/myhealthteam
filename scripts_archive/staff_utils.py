#!/usr/bin/env python3
"""
Staff Code Utility Functions
Centralized staff code lookup for import/export scripts.
"""

import sqlite3
import os
from typing import Optional, Dict, List, Tuple

class StaffCodeManager:
    """Manages staff code lookups from the staff_codes table"""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize with database path"""
        if db_path is None:
            # Default to production.db in parent directory
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'production.db')
        self.db_path = db_path
        self._staff_cache = None

    def _connect(self):
        """Create database connection"""
        return sqlite3.connect(self.db_path)

    def _load_staff_cache(self):
        """Load all staff data into cache"""
        if self._staff_cache is None:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT full_name, email, coordinator_code, provider_code, alt_provider_code
                FROM staff_codes ORDER BY full_name
            """)
            self._staff_cache = {}
            for row in cursor.fetchall():
                full_name, email, coord_code, provider_code, alt_provider = row
                self._staff_cache[full_name] = {
                    'email': email,
                    'coordinator_code': coord_code,
                    'provider_code': provider_code,
                    'alt_provider_code': alt_provider
                }
            conn.close()

    def get_coordinator_code(self, full_name: str) -> Optional[str]:
        """Get coordinator code for staff member"""
        self._load_staff_cache()
        return self._staff_cache.get(full_name, {}).get('coordinator_code')

    def get_provider_code(self, full_name: str) -> Optional[str]:
        """Get provider code for staff member"""
        self._load_staff_cache()
        return self._staff_cache.get(full_name, {}).get('provider_code')

    def get_alt_provider_code(self, full_name: str) -> Optional[str]:
        """Get alternate provider code for staff member"""
        self._load_staff_cache()
        return self._staff_cache.get(full_name, {}).get('alt_provider_code')

    def get_staff_by_coordinator_code(self, coord_code: str) -> Optional[Dict]:
        """Get staff member by coordinator code"""
        self._load_staff_cache()
        for full_name, data in self._staff_cache.items():
            if data['coordinator_code'] == coord_code:
                return {'full_name': full_name, **data}
        return None

    def get_staff_by_provider_code(self, provider_code: str) -> Optional[Dict]:
        """Get staff member by provider code"""
        self._load_staff_cache()
        for full_name, data in self._staff_cache.items():
            if data['provider_code'] == provider_code or data['alt_provider_code'] == provider_code:
                return {'full_name': full_name, **data}
        return None

    def get_all_staff(self) -> List[Dict]:
        """Get all staff as list of dictionaries"""
        self._load_staff_cache()
        return [{'full_name': name, **data} for name, data in self._staff_cache.items()]

    def add_staff_member(self, full_name: str, email: str, coordinator_code: str,
                        provider_code: str, alt_provider_code: str) -> bool:
        """Add new staff member to the table"""
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO staff_codes (full_name, email, coordinator_code, provider_code, alt_provider_code)
                VALUES (?, ?, ?, ?, ?)
            """, (full_name, email, coordinator_code, provider_code, alt_provider_code))
            conn.commit()
            # Clear cache to reload on next query
            self._staff_cache = None
            return True
        except sqlite3.Error as e:
            print(f"Error adding staff member: {e}")
            return False
        finally:
            conn.close()

    def remove_staff_member(self, full_name: str) -> bool:
        """Remove staff member from the table"""
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM staff_codes WHERE full_name = ?", (full_name,))
            conn.commit()
            # Clear cache to reload on next query
            self._staff_cache = None
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error removing staff member: {e}")
            return False
        finally:
            conn.close()

    def validate_coordinator_code(self, coord_code: str) -> bool:
        """Validate if coordinator code exists"""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM staff_codes WHERE coordinator_code = ?", (coord_code,))
        result = cursor.fetchone()[0] > 0
        conn.close()
        return result

    def validate_provider_code(self, provider_code: str) -> bool:
        """Validate if provider code exists"""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM staff_codes
            WHERE provider_code = ? OR alt_provider_code = ?
        """, (provider_code, provider_code))
        result = cursor.fetchone()[0] > 0
        conn.close()
        return result

# Convenience functions for easy importing
staff_manager = StaffCodeManager()

def get_coordinator_code(full_name: str) -> Optional[str]:
    """Get coordinator code for staff member"""
    return staff_manager.get_coordinator_code(full_name)

def get_provider_code(full_name: str) -> Optional[str]:
    """Get provider code for staff member"""
    return staff_manager.get_provider_code(full_name)

def get_all_staff() -> List[Dict]:
    """Get all staff members"""
    return staff_manager.get_all_staff()

def validate_codes(coord_code: str, provider_code: str) -> Tuple[bool, bool]:
    """Validate both coordinator and provider codes"""
    return (
        staff_manager.validate_coordinator_code(coord_code),
        staff_manager.validate_provider_code(provider_code)
    )

if __name__ == "__main__":
    # Test the utility
    print("🧪 Testing Staff Code Utility")
    print("=" * 40)

    # Test basic lookups
    print("\n📋 All Staff Members:")
    all_staff = get_all_staff()
    for staff in all_staff[:3]:  # Show first 3
        print(f"   {staff['full_name']}: {staff['coordinator_code']} | {staff['provider_code']}")
    print(f"   ... and {len(all_staff) - 3} more")

    # Test individual lookups
    print(f"\n🔍 Lookups:")
    coord_code = get_coordinator_code("Ethel Antonio")
    provider_code = get_provider_code("Laura Sumpay CC")
    print(f"   Ethel Antonio coordinator code: {coord_code}")
    print(f"   Laura Sumpay provider code: {provider_code}")

    # Test validation
    print(f"\n✅ Validation:")
    valid_coord, valid_provider = validate_codes("ANTET000", "Sumpay, Laura")
    print(f"   ANTET000 is valid coordinator: {valid_coord}")
    print(f"   Sumpay, Laura is valid provider: {valid_provider}")

    print(f"\n🎯 Utility ready for use in import/export scripts!")