"""
Script 1: explore_cardinality.py
Purpose: Verify 8 cardinality assumptions and diagnose relationship violations
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
# CARDINALITY CHECKS
# =============================================================================

print("\n=== CARDINALITY ANALYSIS ===\n")

# Check 1: StationNumber -> Station Name (1:1)
print("[1/8] StationNumber -> Station Name mapping...")
station_name_mapping = df.groupby('StationNumber')['Station'].nunique()
violations_1 = station_name_mapping[station_name_mapping > 1]
print(f"  [OK] {len(station_name_mapping)} unique stations")
print(f"  [OK] {len(violations_1)} stations with multiple names (violations)")

# Check 2: StationNumber -> (Lat, Long) (1:1)
print("[2/8] StationNumber -> (Latitude, Longitude) mapping...")
station_loc_mapping = df.groupby('StationNumber')[['LatitudeDecimalDegrees', 'LongitudeDecimalDegrees']].nunique().max(axis=1)
violations_2 = station_loc_mapping[station_loc_mapping > 1]
print(f"  [OK] {(station_loc_mapping == 1).sum()} stations with consistent coordinates")
print(f"  [OK] {len(violations_2)} stations with multiple locations (violations)")

# Check 3: StationNumber -> ProjectNumber (1:many)
print("[3/8] StationNumber -> ProjectNumber relationship...")
station_project_mapping = df.groupby('StationNumber')['ProjectNumber'].nunique()
print(f"  [OK] Avg {station_project_mapping.mean():.1f} projects per station")
print(f"  [OK] Range: {station_project_mapping.min()}-{station_project_mapping.max()} projects")

# Check 4: ProjectNumber -> SampleNumber (1:many)
print("[4/8] ProjectNumber -> SampleNumber relationship...")
project_sample_mapping = df.groupby('ProjectNumber')['SampleNumber'].nunique()
print(f"  [OK] Avg {project_sample_mapping.mean():.1f} samples per project")
print(f"  [OK] Range: {project_sample_mapping.min()}-{project_sample_mapping.max()} samples")

# Check 5: SampleNumber -> SampleDateTime (1:1)
print("[5/8] SampleNumber -> SampleDateTime mapping...")
sample_datetime_mapping = df.groupby('SampleNumber')['SampleDateTime'].nunique()
violations_5 = sample_datetime_mapping[sample_datetime_mapping > 1]
print(f"  [OK] {(sample_datetime_mapping == 1).sum()} samples with consistent datetime")
print(f"  [OK] {len(violations_5)} samples with multiple datetimes (violations)")

# Check 6: SampleNumber -> VmvCode (1:many)
print("[6/8] SampleNumber -> VmvCode relationship...")
sample_vmv_mapping = df.groupby('SampleNumber')['VmvCode'].nunique()
print(f"  [OK] Avg {sample_vmv_mapping.mean():.1f} variables per sample")
print(f"  [OK] Range: {sample_vmv_mapping.min()}-{sample_vmv_mapping.max()} variables")

# Check 7: VmvCode -> UnitCode (1:1)
print("[7/8] VmvCode -> UnitCode mapping...")
vmv_unit_mapping = df.groupby('VmvCode')['UnitCode'].nunique()
violations_7 = vmv_unit_mapping[vmv_unit_mapping > 1]
print(f"  [OK] {(vmv_unit_mapping == 1).sum()} VmvCodes with consistent units")
print(f"  [OK] {len(violations_7)} VmvCodes with multiple units (violations)")

# Check 8: VmvCode -> MethodDetectionLimit (1:1)
print("[8/8] VmvCode -> MethodDetectionLimit mapping...")
vmv_mdl_mapping = df.groupby('VmvCode')['MethodDetectionLimit'].nunique()
violations_8 = vmv_mdl_mapping[vmv_mdl_mapping > 1]
print(f"  [OK] {(vmv_mdl_mapping == 1).sum()} VmvCodes with consistent MDL")
print(f"  [OK] {len(violations_8)} VmvCodes with multiple MDLs (violations)")

# =============================================================================
# GENERATE REPORTS
# =============================================================================

print("\n=== GENERATING REPORTS ===\n")

# Report 1: Detailed cardinality mapping
cardinality_report = pd.DataFrame({
    'StationNumber': df['StationNumber'].unique(),
})
cardinality_report['UniqueNames'] = cardinality_report['StationNumber'].map(
    lambda x: df[df['StationNumber'] == x]['Station'].nunique()
)
cardinality_report['UniqueLocations'] = cardinality_report['StationNumber'].map(
    lambda x: df[df['StationNumber'] == x][['LatitudeDecimalDegrees', 'LongitudeDecimalDegrees']].drop_duplicates().shape[0]
)
cardinality_report['ProjectCount'] = cardinality_report['StationNumber'].map(
    lambda x: df[df['StationNumber'] == x]['ProjectNumber'].nunique()
)
cardinality_report['SampleCount'] = cardinality_report['StationNumber'].map(
    lambda x: df[df['StationNumber'] == x]['SampleNumber'].nunique()
)
cardinality_report['RecordCount'] = cardinality_report['StationNumber'].map(
    lambda x: len(df[df['StationNumber'] == x])
)

cardinality_report.to_csv(output_dir / "cardinality_report.csv", index=False)
print(f"[OK] cardinality_report.csv ({len(cardinality_report)} stations)")

# Report 2: Cardinality violations
violations_list = []
for station in violations_2.index:
    locations = df[df['StationNumber'] == station][['LatitudeDecimalDegrees', 'LongitudeDecimalDegrees']].drop_duplicates()
    for idx, row in locations.iterrows():
        violations_list.append({
            'StationNumber': station,
            'LatitudeDecimalDegrees': row['LatitudeDecimalDegrees'],
            'LongitudeDecimalDegrees': row['LongitudeDecimalDegrees'],
            'RecordCount': len(df[(df['StationNumber'] == station) & 
                                  (df['LatitudeDecimalDegrees'] == row['LatitudeDecimalDegrees']) & 
                                  (df['LongitudeDecimalDegrees'] == row['LongitudeDecimalDegrees'])])
        })

if violations_list:
    violations_df = pd.DataFrame(violations_list)
    violations_df.to_csv(output_dir / "cardinality_violations.csv", index=False)
    print(f"[OK] cardinality_violations.csv ({len(violations_df)} location violations)")
else:
    pd.DataFrame().to_csv(output_dir / "cardinality_violations.csv", index=False)
    print(f"[OK] cardinality_violations.csv (NO violations found)")

# Report 3: Station-Project matrix
station_project_matrix = pd.crosstab(
    df['StationNumber'], df['ProjectNumber'], margins=False
)
station_project_matrix.to_csv(output_dir / "station_project_matrix.csv")
print(f"[OK] station_project_matrix.csv ({station_project_matrix.shape[0]} stations × {station_project_matrix.shape[1]} projects)")

print(f"\n[OK] Cardinality analysis complete. Reports saved to {output_dir}\n")
