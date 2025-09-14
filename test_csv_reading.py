#!/usr/bin/env python3
"""
Test CSV reading with proper separator detection
"""
import pandas as pd

def test_csv_reading():
    csv_file = 'attached_assets/relatorio_historico_de_posicoes-tfe-6d41_05-09-2025_06_47_1757817200636.csv'
    
    print("🧪 Testing CSV reading with proper separator detection...")
    
    separators = [',', ';']
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'windows-1252', 'cp1252']
    
    for sep in separators:
        for enc in encodings:
            try:
                df = pd.read_csv(csv_file, sep=sep, encoding=enc)
                print(f"\n✅ Separator='{sep}', Encoding='{enc}':")
                print(f"   Shape: {df.shape}")
                print(f"   Columns: {len(df.columns)}")
                if df.shape[1] > 1:
                    print(f"   First 3 column names: {list(df.columns[:3])}")
                    print(f"   Sample row 0: {dict(list(df.iloc[0].items())[:3])}")
                    return df, sep, enc
                else:
                    print(f"   ⚠️  Only {df.shape[1]} column - wrong separator")
            except Exception as e:
                print(f"❌ Separator='{sep}', Encoding='{enc}': {str(e)[:80]}")
    
    return None, None, None

if __name__ == "__main__":
    df, sep, enc = test_csv_reading()
    if df is not None:
        print(f"\n🎉 Successfully found correct separator: '{sep}' with encoding: '{enc}'")
    else:
        print(f"\n❌ No valid combination found")