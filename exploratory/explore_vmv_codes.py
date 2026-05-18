"""
Script 2: explore_vmv_codes.py
Purpose: Document all Variable-Method-Unit code combinations and validate consistency
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
# VMV CODE ANALYSIS
# =============================================================================

print("\n=== VMV CODE ANALYSIS ===\n")

# Build VMV registry
print("[OK] Building Variable-Method-Unit registry...")
vmv_registry = df.groupby('VmvCode').agg({
    'VariableCode': 'first',
    'VariableName': 'first',
    'MethodCode': 'first',
    'UnitCode': lambda x: list(x.unique()),  # All unique units for this VmvCode
    'MethodDetectionLimit': lambda x: list(x.unique()),  # All unique MDLs
    'MeasurementValue': 'count'
}).reset_index()

vmv_registry.columns = ['VmvCode', 'VariableCode', 'VariableName', 'MethodCode', 
                         'UniquUnits', 'UniqueMDLs', 'RecordCount']

# Count consistency issues
vmv_registry['UnitCount'] = vmv_registry['UniquUnits'].apply(len)
vmv_registry['MDLCount'] = vmv_registry['UniqueMDLs'].apply(len)
vmv_registry['IsConsistent'] = (vmv_registry['UnitCount'] == 1) & (vmv_registry['MDLCount'] == 1)

print(f"[OK] Found {len(vmv_registry)} unique VmvCodes")
print(f"[OK] {vmv_registry['IsConsistent'].sum()} VmvCodes with consistent units and MDLs")
print(f"[OK] {(~vmv_registry['IsConsistent']).sum()} VmvCodes with inconsistencies")

# Simplify for output
vmv_registry_output = vmv_registry.copy()
vmv_registry_output['UniquUnits'] = vmv_registry_output['UniquUnits'].apply(
    lambda x: '; '.join([str(u) for u in x])
)
vmv_registry_output['UniqueMDLs'] = vmv_registry_output['UniqueMDLs'].apply(
    lambda x: '; '.join([str(m) for m in x])
)

vmv_registry_output.to_csv(output_dir / "vmv_code_registry.csv", index=False)
print(f"[OK] vmv_code_registry.csv saved ({len(vmv_registry_output)} codes)")

# Identify violations
vmv_violations = vmv_registry[~vmv_registry['IsConsistent']].copy()
if len(vmv_violations) > 0:
    vmv_violations_output = vmv_violations[['VmvCode', 'VariableName', 
                                             'UnitCount', 'MDLCount', 'RecordCount', 
                                             'UniquUnits', 'UniqueMDLs']].copy()
    vmv_violations_output['UniquUnits'] = vmv_violations_output['UniquUnits'].apply(
        lambda x: '; '.join([str(u) for u in x])
    )
    vmv_violations_output['UniqueMDLs'] = vmv_violations_output['UniqueMDLs'].apply(
        lambda x: '; '.join([str(m) for m in x])
    )
    vmv_violations_output.to_csv(output_dir / "vmv_violations.csv", index=False)
    print(f"[OK] vmv_violations.csv ({len(vmv_violations)} violations)")
else:
    pd.DataFrame().to_csv(output_dir / "vmv_violations.csv", index=False)
    print(f"[OK] vmv_violations.csv (NO violations found)")

# =============================================================================
# STATION-PARAMETER COVERAGE
# =============================================================================

print("\n[OK] Building station-parameter coverage matrix...")

# Pivot table: rows=stations, cols=variables
station_var_coverage = df.groupby(['StationNumber', 'VariableName']).size().reset_index(name='MeasurementCount')
station_var_pivot = station_var_coverage.pivot(index='StationNumber', 
                                                columns='VariableName', 
                                                values='MeasurementCount').fillna(0).astype(int)

station_var_pivot.to_csv(output_dir / "variable_station_coverage.csv")
print(f"[OK] variable_station_coverage.csv ({station_var_pivot.shape[0]} stations × {station_var_pivot.shape[1]} variables)")

# Summary statistics per station
station_summary = pd.DataFrame({
    'StationNumber': df['StationNumber'].unique(),
})
station_summary['StationName'] = station_summary['StationNumber'].map(
    lambda x: df[df['StationNumber'] == x]['Station'].iloc[0]
)
station_summary['MeasurementCount'] = station_summary['StationNumber'].map(
    lambda x: len(df[df['StationNumber'] == x])
)
station_summary['UniqueVariables'] = station_summary['StationNumber'].map(
    lambda x: df[df['StationNumber'] == x]['VariableName'].nunique()
)
station_summary['DateRangeStart'] = station_summary['StationNumber'].map(
    lambda x: df[df['StationNumber'] == x]['SampleDateTime'].min()
)
station_summary['DateRangeEnd'] = station_summary['StationNumber'].map(
    lambda x: df[df['StationNumber'] == x]['SampleDateTime'].max()
)

station_summary.to_csv(output_dir / "station_parameter_summary.csv", index=False)
print(f"[OK] station_parameter_summary.csv ({len(station_summary)} stations)")

# Variable popularity
variable_popularity = df.groupby('VariableName').agg({
    'MeasurementValue': 'count',
    'StationNumber': 'nunique'
}).reset_index()
variable_popularity.columns = ['VariableName', 'TotalMeasurements', 'StationCount']
variable_popularity = variable_popularity.sort_values('TotalMeasurements', ascending=False)

variable_popularity.to_csv(output_dir / "variable_popularity.csv", index=False)
print(f"[OK] variable_popularity.csv ({len(variable_popularity)} variables)")

print(f"\n[OK] VMV analysis complete. Reports saved to {output_dir}\n")
