#!/usr/bin/env python3
"""
Test if metrics are now updating correctly after data transfer
"""

import sys
sys.path.append('src')

from src.database import (
    get_coordinator_performance_metrics,
    get_provider_performance_metrics,
    get_coordinator_monthly_minutes_live
)

def test_coordinator_metrics():
    """Test coordinator performance metrics"""
    print("📊 TESTING COORDINATOR METRICS")
    print("=" * 50)
    
    try:
        # Test current month coordinator metrics
        metrics = get_coordinator_performance_metrics()
        print(f"Coordinator performance metrics: {len(metrics)} records")
        
        if metrics:
            for i, metric in enumerate(metrics[:5]):  # Show first 5
                print(f"  {i+1}. {metric}")
        else:
            print("  ⚠️  No coordinator metrics found")
        
        # Test live coordinator minutes
        live_minutes = get_coordinator_monthly_minutes_live()
        print(f"Live coordinator minutes: {len(live_minutes)} records")
        
        if live_minutes:
            for i, coord in enumerate(live_minutes[:5]):  # Show first 5
                print(f"  {i+1}. {coord}")
        else:
            print("  ⚠️  No live coordinator minutes found")
            
    except Exception as e:
        print(f"  ❌ Error testing coordinator metrics: {e}")
        import traceback
        traceback.print_exc()

def test_provider_metrics():
    """Test provider performance metrics"""
    print("\n👩‍⚕️ TESTING PROVIDER METRICS")
    print("=" * 50)
    
    try:
        # Test provider performance metrics
        metrics = get_provider_performance_metrics()
        print(f"Provider performance metrics: {len(metrics)} records")
        
        if metrics:
            for i, metric in enumerate(metrics[:5]):  # Show first 5
                print(f"  {i+1}. {metric}")
        else:
            print("  ⚠️  No provider metrics found")
            
    except Exception as e:
        print(f"  ❌ Error testing provider metrics: {e}")
        import traceback
        traceback.print_exc()

def test_database_directly():
    """Test database queries directly"""
    print("\n🔍 TESTING DATABASE DIRECTLY")
    print("=" * 50)
    
    import sqlite3
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Test coordinator tasks counts by month
    months = ['2025_09', '2025_10', '2025_11']
    
    for month in months:
        table_name = f'coordinator_tasks_{month}'
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} records")
        except Exception as e:
            print(f"  {table_name}: Error - {e}")
    
    # Test provider tasks counts by month
    for month in months:
        table_name = f'provider_tasks_{month}'
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} records")
        except Exception as e:
            print(f"  {table_name}: Error - {e}")
    
    conn.close()

def main():
    print("🚀 TESTING METRICS AFTER DATA TRANSFER")
    print("=" * 60)
    
    test_database_directly()
    test_coordinator_metrics()
    test_provider_metrics()
    
    print(f"\n✅ METRICS TEST COMPLETE")

if __name__ == "__main__":
    main()