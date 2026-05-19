#!/usr/bin/env python
import pandas as pd
import os

print("=" * 80)
print("SURFACE WATER QUALITY DATA SCHEMA EXPLORATION")
print("=" * 80)

csv_path = 'data/raw/alberta_surface_water_quality_data.csv'

if os.path.exists(csv_path):
    # Load just the first few rows to understand structure
    df = pd.read_csv(csv_path, nrows=1000)
    
    print("\n1. ALL COLUMNS:")
    print("-" * 80)
    for i, col in enumerate(df.columns, 1):
        print(f"{i:2d}. {col}")
    
    print(f"\nTotal columns: {len(df.columns)}")
    
    print("\n2. DATA SHAPE:")
    print("-" * 80)
    total_rows = len(pd.read_csv(csv_path, usecols=[df.columns[0]]))
    print(f"Total rows: {total_rows:,}")
    print(f"Total columns: {len(df.columns)}")
    
    print("\n3. SAMPLE COMMENT FIELD:")
    print("-" * 80)
    if 'SampleComment' in df.columns:
        print("✓ SampleComment field EXISTS")
        print(f"  Non-null values: {df['SampleComment'].notna().sum()}")
        print(f"  Sample values:")
        print(df[df['SampleComment'].notna()]['SampleComment'].head(3).to_string())
    else:
        print("✗ SampleComment field NOT FOUND")
        similar = [col for col in df.columns if 'comment' in col.lower() or 'sample' in col.lower()]
        if similar:
            print(f"  Similar fields: {similar}")
    
    print("\n4. VMV CODE AND DESCRIPTION:")
    print("-" * 80)
    vmv_cols = [col for col in df.columns if 'vmv' in col.lower()]
    print(f"VMV-related columns found: {vmv_cols}")
    if vmv_cols:
        for col in vmv_cols:
            print(f"\n{col}:")
            print(f"  Unique values: {df[col].nunique()}")
            print(f"  Sample values: {df[col].unique()[:5].tolist()}")
    
    print("\n5. MEASUREMENT QUALIFIER:")
    print("-" * 80)
    mq_cols = [col for col in df.columns if 'qualifier' in col.lower() or 'quality' in col.lower()]
    print(f"Qualifier-related columns: {mq_cols}")
    
    if 'MeasurementQualifier' in df.columns:
        mq = df['MeasurementQualifier']
        print(f"\nMeasurementQualifier:")
        print(f"  Unique values: {mq.nunique()}")
        print(f"  All values: {mq.unique().tolist()}")
        print(f"\n  Examples with HT:")
        ht_rows = df[df['MeasurementQualifier'] == 'HT']
        if len(ht_rows) > 0:
            print(ht_rows.head(1).to_string())
        
        print(f"\n  Examples with SUS:")
        sus_rows = df[df['MeasurementQualifier'] == 'SUS']
        if len(sus_rows) > 0:
            print(sus_rows.head(1).to_string())
    
    print("\n6. FIRST 3 ROWS:")
    print("-" * 80)
    print(df.head(3).to_string())
    
    print("\n7. DATA TYPES:")
    print("-" * 80)
    print(df.dtypes.to_string())
    
else:
    print(f"ERROR: File not found: {csv_path}")

print("\n" + "=" * 80)
