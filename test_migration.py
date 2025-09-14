#!/usr/bin/env python3
"""
Test script to verify the database migration fixes
"""
import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append('.')

from database.db_manager import DatabaseManager
from database.services import FleetDatabaseService

def main():
    print("🧪 Testing database migration with user's CSV file...")
    print(f"Timestamp: {datetime.now()}")
    
    # Test file path
    csv_file = 'attached_assets/relatorio_historico_de_posicoes-tfe-6d41_05-09-2025_06_47_1757817200636.csv'
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print(f"📁 Found CSV file: {csv_file}")
    
    # Check file size
    file_size = os.path.getsize(csv_file)
    print(f"📏 File size: {file_size:,} bytes")
    
    # Run migration
    print("\n🚀 Starting migration...")
    result = DatabaseManager.migrate_csv_to_database(csv_file)
    
    print(f"\n📊 Migration Result:")
    print(f"Success: {result.get('success', False)}")
    if result.get('success'):
        print(f"Records processed: {result.get('records_processed', 0):,}")
        print(f"Unique vehicles: {result.get('unique_vehicles', 0):,}")
        print(f"Unique clients: {result.get('unique_clients', 0):,}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Verify database state
    print("\n🔍 Verifying database state...")
    try:
        with FleetDatabaseService() as db:
            summary = db.get_fleet_summary()
            print(f"Total clients: {summary['total_clients']:,}")
            print(f"Total vehicles: {summary['total_vehicles']:,}")
            print(f"Total telematics records: {summary['total_records']:,}")
            print(f"Date range: {summary['start_date']} to {summary['end_date']}")
            print(f"Average speed: {summary['avg_speed']} km/h")
            print(f"GPS coverage: {summary['gps_coverage']}%")
    except Exception as e:
        print(f"❌ Error getting database summary: {str(e)}")
    
    print("\n✅ Migration test complete!")

if __name__ == "__main__":
    main()