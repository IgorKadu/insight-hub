#!/usr/bin/env python3
"""
Debug script to analyze the CSV file and column mapping issues
"""
import pandas as pd
import sys
sys.path.append('.')

def main():
    print("🔍 Debugging CSV column mapping and data issues...")
    
    csv_file = 'attached_assets/relatorio_historico_de_posicoes-tfe-6d41_05-09-2025_06_47_1757817200636.csv'
    
    # Read the CSV with different separators
    print("\n📄 Testing CSV reading with different separators...")
    
    separators = [',', ';']
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'windows-1252', 'cp1252']
    
    df = None
    used_sep = None
    used_enc = None
    
    for sep in separators:
        for enc in encodings:
            try:
                df = pd.read_csv(csv_file, sep=sep, encoding=enc)
                used_sep = sep
                used_enc = enc
                print(f"✅ Successfully read with separator='{sep}' and encoding='{enc}'")
                break
            except Exception as e:
                print(f"❌ Failed with separator='{sep}' and encoding='{enc}': {str(e)[:100]}")
                continue
        if df is not None:
            break
    
    if df is None:
        print("❌ Could not read CSV file with any combination")
        return
    
    print(f"\n📊 File info:")
    print(f"Shape: {df.shape}")
    print(f"Used separator: '{used_sep}'")
    print(f"Used encoding: '{used_enc}'")
    
    print(f"\n📋 Original columns:")
    for i, col in enumerate(df.columns):
        print(f"{i:2d}: '{col}' (len={len(col)})")
    
    # Test normalization
    print(f"\n🔧 Testing column normalization:")
    normalized_cols = [' '.join(col.strip().split()) for col in df.columns]
    for i, (orig, norm) in enumerate(zip(df.columns, normalized_cols)):
        if orig != norm:
            print(f"{i:2d}: '{orig}' -> '{norm}'")
    
    # Test first few rows of key columns
    print(f"\n📝 Sample data (first 3 rows):")
    key_cols = ['Cliente', 'Placa', 'Data']
    for col in key_cols:
        if col in df.columns:
            print(f"{col}: {df[col].head(3).tolist()}")
        else:
            print(f"❌ Column '{col}' not found")
    
    # Check unique values in key columns
    print(f"\n🔢 Unique value counts:")
    if 'Cliente' in df.columns:
        print(f"Unique clients: {df['Cliente'].nunique()}")
        print(f"Client values: {df['Cliente'].unique()[:5]}")
    
    if 'Placa' in df.columns:
        print(f"Unique plates: {df['Placa'].nunique()}")
        print(f"Plate values: {df['Placa'].unique()[:5]}")
    
    # Test date parsing
    print(f"\n📅 Testing date parsing:")
    if 'Data' in df.columns:
        date_sample = df['Data'].head(3)
        print(f"Original dates: {date_sample.tolist()}")
        
        # Test without dayfirst
        parsed_normal = pd.to_datetime(date_sample, errors='coerce')
        print(f"Parsed (normal): {parsed_normal.tolist()}")
        
        # Test with dayfirst
        parsed_dayfirst = pd.to_datetime(date_sample, errors='coerce', dayfirst=True)
        print(f"Parsed (dayfirst): {parsed_dayfirst.tolist()}")
        
        # Check for NaT values
        nat_count = parsed_dayfirst.isna().sum()
        print(f"NaT values with dayfirst=True: {nat_count}")

if __name__ == "__main__":
    main()