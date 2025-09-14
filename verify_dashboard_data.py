#!/usr/bin/env python3
"""
Verify dashboard components work with migrated data
"""
import sys
sys.path.append('.')

from database.db_manager import DatabaseManager
from database.services import FleetDatabaseService
from utils.data_analyzer import DataAnalyzer

def verify_dashboard_data():
    print("🔍 Verifying dashboard data components...")
    
    # Test 1: Check DatabaseManager.get_dashboard_data()
    print("\n📊 Test 1: DatabaseManager.get_dashboard_data()")
    try:
        df = DatabaseManager.get_dashboard_data()
        print(f"✅ Dashboard data loaded: {df.shape[0]:,} rows, {df.shape[1]} columns")
        
        if df.shape[0] > 0:
            print(f"   Date range: {df['data'].min()} to {df['data'].max()}")
            print(f"   Unique clients: {df['cliente'].nunique()}")
            print(f"   Unique vehicles: {df['placa'].nunique()}")
            print(f"   Sample data: {df[['cliente', 'placa', 'velocidade_km']].head(2).to_dict('records')}")
        
    except Exception as e:
        print(f"❌ Dashboard data loading failed: {str(e)}")
        return False
    
    # Test 2: Check if DataAnalyzer can load from database
    print("\n🧮 Test 2: DataAnalyzer.from_database()")
    try:
        analyzer = DataAnalyzer.from_database()
        if analyzer.data is not None and not analyzer.data.empty:
            print(f"✅ DataAnalyzer loaded: {analyzer.data.shape[0]:,} rows")
            
            # Test KPIs calculation
            kpis = analyzer.get_kpis()
            print(f"   KPIs: {kpis['total_veiculos']} vehicles, {kpis['velocidade_media']:.1f} avg speed")
        else:
            print(f"❌ DataAnalyzer data is empty")
            return False
            
    except Exception as e:
        print(f"❌ DataAnalyzer loading failed: {str(e)}")
        return False
    
    # Test 3: Check FleetDatabaseService summary
    print("\n📈 Test 3: FleetDatabaseService.get_fleet_summary()")
    try:
        with FleetDatabaseService() as db:
            summary = db.get_fleet_summary()
            print(f"✅ Fleet summary: {summary['total_records']:,} records")
            print(f"   Vehicles: {summary['total_vehicles']}, Clients: {summary['total_clients']}")
            print(f"   Speed stats: {summary['avg_speed']} avg, {summary['max_speed']} max")
            print(f"   GPS coverage: {summary['gps_coverage']}%")
            
    except Exception as e:
        print(f"❌ Fleet summary failed: {str(e)}")
        return False
    
    # Test 4: Test data filtering
    print("\n🔍 Test 4: Data filtering functionality")
    try:
        # Test with client filter
        filtered_df = DatabaseManager.get_dashboard_data(client_filter="JANDAIA")
        print(f"✅ Client filter works: {filtered_df.shape[0]:,} records for JANDAIA")
        
        # Test with vehicle filter
        filtered_df = DatabaseManager.get_dashboard_data(vehicle_filter="TFE-6D41")
        print(f"✅ Vehicle filter works: {filtered_df.shape[0]:,} records for TFE-6D41")
        
    except Exception as e:
        print(f"❌ Data filtering failed: {str(e)}")
        return False
    
    print("\n🎉 Dashboard verification complete - All components working correctly!")
    return True

if __name__ == "__main__":
    success = verify_dashboard_data()
    if success:
        print("\n✅ DASHBOARD READY: All migrated data is accessible and dashboard components work correctly")
    else:
        print("\n❌ DASHBOARD ISSUES: Some components need attention")