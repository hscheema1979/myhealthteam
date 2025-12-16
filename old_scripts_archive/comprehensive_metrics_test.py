#!/usr/bin/env python3
"""
Comprehensive verification that metrics are now working correctly
"""

import sys
sys.path.append('src')

import sqlite3
from src.database import get_coordinator_monthly_minutes_live, get_provider_performance_metrics

def verify_coordinator_metrics():
    """Verify coordinator metrics are working"""
    print("📊 COORDINATOR METRICS VERIFICATION")
    print("=" * 50)
    
    try:
        # Test live coordinator minutes
        live_minutes = get_coordinator_monthly_minutes_live()
        print(f"✅ get_coordinator_monthly_minutes_live(): {len(live_minutes)} records returned")
        
        if live_minutes:
            print("   Sample data:")
            for i, coord in enumerate(live_minutes[:3]):
                print(f"     {i+1}. {coord}")
        else:
            print("   ⚠️  No live coordinator minutes returned (may be expected if no current month data)")
        
        # Test direct database query for November 2025
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT coordinator_id, COUNT(*) as task_count, SUM(duration_minutes) as total_minutes
            FROM coordinator_tasks_2025_11 
            WHERE duration_minutes > 0
            GROUP BY coordinator_id 
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        print(f"   Direct DB query for Nov 2025: {len(results)} coordinators with tasks")
        
        for row in results:
            print(f"     - {row[0]}: {row[1]} tasks, {row[2]} minutes")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

def verify_provider_metrics():
    """Verify provider metrics are working"""
    print("\n👩‍⚕️ PROVIDER METRICS VERIFICATION")
    print("=" * 50)
    
    try:
        # Test provider performance metrics
        metrics = get_provider_performance_metrics()
        print(f"✅ get_provider_performance_metrics(): {len(metrics)} records returned")
        
        if metrics:
            print("   Sample data:")
            for i, metric in enumerate(metrics[:3]):
                print(f"     {i+1}. {metric}")
        
        # Test direct database query for November 2025 provider tasks
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT provider_name, COUNT(*) as task_count, SUM(minutes_of_service) as total_minutes
            FROM provider_tasks_2025_11 
            WHERE minutes_of_service > 0
            GROUP BY provider_name
        """)
        
        results = cursor.fetchall()
        print(f"   Direct DB query for Nov 2025: {len(results)} providers with tasks")
        
        for row in results:
            print(f"     - {row[0]}: {row[1]} tasks, {row[2]} minutes")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

def verify_billing_data():
    """Verify billing-related data is available"""
    print("\n💰 BILLING DATA VERIFICATION")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        # Check for billing codes in provider tasks
        cursor.execute("""
            SELECT billing_code, billing_code_description, COUNT(*) as count
            FROM provider_tasks_2025_10 
            WHERE billing_code IS NOT NULL AND billing_code != ''
            GROUP BY billing_code, billing_code_description
            LIMIT 10
        """)
        
        billing_codes = cursor.fetchall()
        print(f"✅ Found {len(billing_codes)} billing codes in provider_tasks_2025_10")
        
        for row in billing_codes:
            print(f"   - {row[0]}: {row[1] if row[1] else 'No description'} ({row[2]} tasks)")
        
        # Check coordinator task types
        cursor.execute("""
            SELECT task_type, COUNT(*) as count
            FROM coordinator_tasks_2025_10 
            WHERE task_type IS NOT NULL
            GROUP BY task_type
            ORDER BY count DESC
            LIMIT 10
        """)
        
        task_types = cursor.fetchall()
        print(f"\n✅ Found {len(task_types)} task types in coordinator_tasks_2025_10")
        
        for row in task_types:
            print(f"   - {row[0]}: {row[1]} tasks")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🚀 COMPREHENSIVE METRICS VERIFICATION")
    print("=" * 60)
    print("Testing if coordinator, provider, and billing metrics are working correctly...")
    
    verify_coordinator_metrics()
    verify_provider_metrics()
    verify_billing_data()
    
    print(f"\n✅ VERIFICATION COMPLETE")
    print("If all sections show ✅, then the metrics issue has been resolved!")

if __name__ == "__main__":
    main()