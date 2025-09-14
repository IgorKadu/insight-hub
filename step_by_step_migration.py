#!/usr/bin/env python3
"""
Step-by-step migration test to verify each component works
"""
import pandas as pd
import sys
sys.path.append('.')

from database.db_manager import DatabaseManager

def test_step_by_step():
    print("🔧 Step-by-step migration test...")
    
    csv_file = 'attached_assets/relatorio_historico_de_posicoes-tfe-6d41_05-09-2025_06_47_1757817200636.csv'
    
    # Step 1: Test CSV reading
    print("\n📁 Step 1: Testing CSV reading...")
    try:
        df = None
        separators = [',', ';']
        encodings = ['latin-1', 'utf-8', 'iso-8859-1', 'windows-1252', 'cp1252']
        
        for sep in separators:
            for enc in encodings:
                try:
                    test_df = pd.read_csv(csv_file, sep=sep, encoding=enc)
                    if test_df.shape[1] > 1:  # Multiple columns
                        df = test_df
                        print(f"✅ CSV read successfully: sep='{sep}', enc='{enc}', shape={df.shape}")
                        break
                except:
                    continue
            if df is not None:
                break
        
        if df is None:
            print("❌ Could not read CSV")
            return
            
    except Exception as e:
        print(f"❌ CSV reading failed: {str(e)}")
        return
    
    # Step 2: Test column normalization
    print(f"\n🔧 Step 2: Testing column normalization...")
    try:
        print(f"Original columns: {list(df.columns[:5])}")
        df.columns = [' '.join(col.strip().split()) for col in df.columns]
        print(f"Normalized columns: {list(df.columns[:5])}")
        print(f"✅ Column normalization successful")
    except Exception as e:
        print(f"❌ Column normalization failed: {str(e)}")
        return
    
    # Step 3: Test small sample migration
    print(f"\n🧪 Step 3: Testing small sample migration (first 5 rows)...")
    try:
        small_df = df.head(5).copy()
        result = DatabaseManager.migrate_csv_to_database_from_df(small_df, "test_sample.csv")
        print(f"Sample migration result: {result}")
        
        if result.get('success'):
            print(f"✅ Sample migration successful: {result.get('records_processed', 0)} records processed")
        else:
            print(f"❌ Sample migration failed: {result.get('error', 'Unknown error')}")
            return
    except Exception as e:
        print(f"❌ Sample migration failed: {str(e)}")
        return
    
    # Step 4: Test full migration if sample worked
    print(f"\n🚀 Step 4: Testing full migration ({df.shape[0]} rows)...")
    try:
        result = DatabaseManager.migrate_csv_to_database_from_df(df, "full_migration.csv")
        print(f"Full migration result: {result}")
        
        if result.get('success'):
            print(f"✅ Full migration successful!")
            print(f"   Records processed: {result.get('records_processed', 0):,}")
            print(f"   Unique vehicles: {result.get('unique_vehicles', 0):,}")
            print(f"   Unique clients: {result.get('unique_clients', 0):,}")
        else:
            print(f"❌ Full migration failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Full migration failed: {str(e)}")

if __name__ == "__main__":
    test_step_by_step()