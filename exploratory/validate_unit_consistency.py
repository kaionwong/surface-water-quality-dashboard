"""
Script 6: validate_unit_consistency.py
Purpose: Ensure Rule S1 (VmvCode -> Unit consistency) across all records
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from config import ALBERTA_DATA_FILE, DATA_RAW_PATH, OUTPUT_EDA_PATH

# Load data
print("[OK] Loading data...")
data_file = os.path.join(DATA_RAW_PATH, ALBERTA_DATA_FILE)
df = pd.read_csv(data_file)
print(f"[OK] Loaded {len(df):,} rows × {len(df.columns)} columns")

output_dir = Path(OUTPUT_EDA_PATH)
output_dir.mkdir(parents=True, exist_ok=True)

# =============================================================================
# UNIT CONSISTENCY VALIDATION
# =============================================================================

print("\n=== UNIT CONSISTENCY VALIDATION ===\n")

# Build mapping of VmvCode -> all observed UnitCodes
print("[OK] Analyzing VmvCode-Unit relationships...")
vmv_unit_mapping = df.groupby('VmvCode')['UnitCode'].unique().reset_index()
vmv_unit_mapping['UnitCount'] = vmv_unit_mapping['UnitCode'].apply(len)
vmv_unit_mapping['IsConsistent'] = vmv_unit_mapping['UnitCount'] == 1
vmv_unit_mapping['Units'] = vmv_unit_mapping['UnitCode'].apply(
    lambda x: '; '.join(sorted(set([str(u) for u in x if pd.notna(u)])))
)

# Get additional info for each VmvCode
vmv_info = df.groupby('VmvCode').agg({
    'VariableCode': 'first',
    'VariableName': 'first',
    'MethodCode': 'first',
    'MeasurementValue': 'count'
}).reset_index()
vmv_info.columns = ['VmvCode', 'VariableCode', 'VariableName', 'MethodCode', 'RecordCount']

# Merge
unit_consistency_report = vmv_unit_mapping.merge(vmv_info, on='VmvCode', how='left')
unit_consistency_report = unit_consistency_report.sort_values('RecordCount', ascending=False)

# Output full report
report_output = unit_consistency_report[['VmvCode', 'VariableName', 
                                          'Units', 'UnitCount', 'RecordCount', 'IsConsistent']].copy()
report_output = report_output.rename(columns={
    'UnitCode': 'UnitCodes',
    'UnitCount': 'UniqueUnitCount',
    'RecordCount': 'TotalRecords'
})
report_output.to_csv(output_dir / "unit_consistency_report.csv", index=False)
print(f"[OK] unit_consistency_report.csv ({len(report_output)} VmvCodes)")

# =============================================================================
# IDENTIFY VIOLATIONS
# =============================================================================

print("\n[OK] Identifying unit consistency violations...")
violations = unit_consistency_report[~unit_consistency_report['IsConsistent']].copy()

if len(violations) > 0:
    # Detailed violation report
    violation_details = []
    
    for idx, row in violations.iterrows():
        vmv = row['VmvCode']
        vmv_data = df[df['VmvCode'] == vmv]
        
        for unit in row['UnitCode']:
            unit_count = len(vmv_data[vmv_data['UnitCode'] == unit])
            violation_details.append({
                'VmvCode': vmv,
                'VariableName': row['VariableName'],
                'UnitCode': unit,
                'RecordsWithThisUnit': unit_count,
                'StationCount': vmv_data[vmv_data['UnitCode'] == unit]['StationNumber'].nunique(),
                'ProjectCount': vmv_data[vmv_data['UnitCode'] == unit]['ProjectNumber'].nunique()
            })
    
    violation_df = pd.DataFrame(violation_details)
    violation_df = violation_df.sort_values(['VmvCode', 'RecordsWithThisUnit'], ascending=[True, False])
    violation_df.to_csv(output_dir / "unit_violations.csv", index=False)
    print(f"[OK] unit_violations.csv ({len(violations)} VmvCodes with violations)")
    
    print("\nUnit Consistency Violations:")
    for vmv in violations['VmvCode'].unique():
        vmv_violations = violation_df[violation_df['VmvCode'] == vmv]
        print(f"\n  {vmv}:")
        units_found = vmv_violations['UnitCode'].unique()
        print(f"    Found {len(units_found)} different units: {', '.join(units_found)}")
        for idx, vrow in vmv_violations.iterrows():
            print(f"      {vrow['UnitCode']}: {vrow['RecordsWithThisUnit']:,} records " +
                  f"({vrow['StationCount']} stations, {vrow['ProjectCount']} projects)")
else:
    pd.DataFrame().to_csv(output_dir / "unit_violations.csv", index=False)
    print(f"[OK] unit_violations.csv (NO VIOLATIONS - all VmvCodes have consistent units)")

# =============================================================================
# UNIT CONVERSION GUIDE (if applicable)
# =============================================================================

print("\n[OK] Generating unit conversion guidance...")

# Find common unit discrepancies that might need conversion
conversion_candidates = []

# Example: If pH measurements found in both "pH units" and "unitless"
pH_records = df[df['VariableName'].str.contains('pH', case=False, na=False)]
if len(pH_records) > 0:
    pH_units = pH_records['UnitCode'].unique()
    if len(pH_units) > 1:
        conversion_candidates.append({
            'Variable': 'pH',
            'UnitsFound': '; '.join(pH_units),
            'ConversionNeeded': 'Harmonize to canonical unit',
            'Recommendation': 'Use pH units as canonical'
        })

# Temperature conversions
temp_records = df[df['VariableName'].str.contains('Temperature', case=False, na=False)]
if len(temp_records) > 0:
    temp_units = temp_records['UnitCode'].unique()
    if 'C' in temp_units and 'F' in temp_units:
        conversion_candidates.append({
            'Variable': 'Temperature',
            'UnitsFound': 'Celsius; Fahrenheit',
            'ConversionNeeded': 'Celsius-Fahrenheit conversion',
            'Recommendation': 'Convert all to Celsius; F = C * 9/5 + 32'
        })

if conversion_candidates:
    conversion_guide = pd.DataFrame(conversion_candidates)
    conversion_guide.to_csv(output_dir / "unit_conversion_guide.csv", index=False)
    print(f"[OK] unit_conversion_guide.csv ({len(conversion_guide)} conversion opportunities)")
else:
    pd.DataFrame().to_csv(output_dir / "unit_conversion_guide.csv", index=False)
    print(f"[OK] unit_conversion_guide.csv (No multi-unit variables detected)")

# =============================================================================
# SUMMARY STATISTICS
# =============================================================================

print("\n=== UNIT CONSISTENCY SUMMARY ===")
print(f"Total unique VmvCodes: {len(unit_consistency_report)}")
print(f"VmvCodes with consistent units: {unit_consistency_report['IsConsistent'].sum()}")
print(f"VmvCodes with inconsistent units: {(~unit_consistency_report['IsConsistent']).sum()}")

if len(violations) > 0:
    affected_records = df[df['VmvCode'].isin(violations['VmvCode'])].shape[0]
    affected_pct = 100 * affected_records / len(df)
    print(f"Records affected by unit inconsistency: {affected_records:,} ({affected_pct:.2f}%)")

print(f"\n[OK] Unit consistency validation complete. Reports saved to {output_dir}\n")
