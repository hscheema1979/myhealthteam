#!/usr/bin/env python3

import sys
import os

# Add src to path
sys.path.append('src')

def test_weekly_billing_functionality():
    """Test weekly billing dashboard functionality"""
    print("TESTING WEEKLY BILLING DASHBOARD FUNCTIONALITY")
    print("=" * 70)
    
    try:
        # Test imports
        print("1. Testing imports...")
        from src.dashboards.weekly_billing_dashboard import get_billing_weeks_list, get_available_months
        from src.dashboards.provider_payment_dashboard import get_provider_payment_summary, get_provider_monthly_summary
        print("   ✅ All imports successful")
        
        # Test billing weeks list
        print("\n2. Testing billing weeks list...")
        weeks_df = get_billing_weeks_list()
        print(f"   ✅ Found {len(weeks_df)} billing weeks")
        if len(weeks_df) > 0:
            print("   Recent weeks:")
            for i, row in weeks_df.head(3).iterrows():
                print(f"     - {row['billing_week']}: {row['week_start_date']} to {row['week_end_date']}")
        
        # Test available months
        print("\n3. Testing available months...")
        months = get_available_months()
        print(f"   ✅ Found {len(months)} available months")
        if months:
            print("   Recent months:")
            for month in months[:3]:
                print(f"     - {month['display']}")
        
        # Test provider payment summary
        print("\n4. Testing provider payment summary...")
        payment_summary = get_provider_payment_summary()
        print(f"   ✅ Payment summary: {len(payment_summary)} records")
        
        if len(payment_summary) > 0:
            print("   Sample providers:")
            for i, row in payment_summary.head(3).iterrows():
                print(f"     - {row['provider_name']}: {row['total_tasks']} tasks, {row['total_minutes']} minutes")
        
        # Test monthly summary
        print("\n5. Testing monthly summary...")
        monthly_summary = get_provider_monthly_summary()
        print(f"   ✅ Monthly summary: {len(monthly_summary)} records")
        
        if len(monthly_summary) > 0:
            print("   Recent months:")
            for i, row in monthly_summary.head(3).iterrows():
                print(f"     - {row['provider_name']}: {row['total_tasks']} tasks, {row['total_minutes']} minutes")
        
        # Test billing status data
        print("\n6. Testing billing status data...")
        import sqlite3
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                billing_status,
                COUNT(*) as task_count,
                SUM(minutes_of_service) as total_minutes,
                AVG(minutes_of_service) as avg_minutes
            FROM provider_task_billing_status
            GROUP BY billing_status
            ORDER BY task_count DESC
        """)
        
        status_summary = cursor.fetchall()
        print("   Billing status breakdown:")
        for status, count, total_min, avg_min in status_summary:
            print(f"     - {status}: {count} tasks, {total_min} total min, {avg_min:.1f} avg min")
        
        # Test provider breakdown
        cursor.execute("""
            SELECT 
                provider_name,
                billing_status,
                COUNT(*) as task_count
            FROM provider_task_billing_status
            GROUP BY provider_name, billing_status
            ORDER BY task_count DESC
            LIMIT 5
        """)
        
        provider_status = cursor.fetchall()
        print("   Top providers by task count:")
        for provider, status, count in provider_status:
            print(f"     - {provider} ({status}): {count} tasks")
        
        conn.close()
        
        print("\n✅ ALL WEEKLY BILLING TESTS PASSED!")
        print("\n🎯 SUMMARY:")
        print(f"   - Billing weeks available: {len(weeks_df)}")
        print(f"   - Months with data: {len(months)}")
        print(f"   - Provider payment records: {len(payment_summary)}")
        print(f"   - Monthly summary records: {len(monthly_summary)}")
        print(f"   - Billing status records: {sum([count for _, count, _, _ in status_summary])}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing weekly billing functionality: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_weekly_billing_functionality()