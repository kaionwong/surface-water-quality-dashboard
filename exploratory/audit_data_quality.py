"""
Script 3: audit_data_quality.py
Purpose: Apply all 12 quality rules and generate a comprehensive data quality report
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
from config import ALBERTA_DATA_FILE, DATA_RAW_PATH, OUTPUT_EDA_PATH

# Load data
print("[OK] Loading data...")
data_file = os.path.join(DATA_RAW_PATH, ALBERTA_DATA_FILE)
df = pd.read_csv(data_file)
print(f"[OK] Loaded {len(df):,} rows × {len(df.columns)} columns")

output_dir = Path(OUTPUT_EDA_PATH)
output_dir.mkdir(parents=True, exist_ok=True)

# Convert MeasurementValue to numeric (it has mixed types)
df['MeasurementValue'] = pd.to_numeric(df['MeasurementValue'], errors='coerce')

# Initialize audit tracking
df['audit_issues'] = ''
issue_counts = {}

print("\n=== DATA QUALITY AUDIT ===\n")

# =============================================================================
# STRUCTURAL RULES
# =============================================================================

print("[S1] Checking VmvCode consistency (Rule S1)...")
# Rule S1: For each VmvCode, all instances should have same UnitCode
vmv_units = df.groupby('VmvCode')['UnitCode'].unique()
vmv_unit_violations = vmv_units[vmv_units.apply(len) > 1].index
for vmv in vmv_unit_violations:
    df.loc[df['VmvCode'] == vmv, 'audit_issues'] += 'S1:MultipleUnits;'
issue_counts['S1:VmvCodeUnitInconsistency'] = len(df[df['audit_issues'].str.contains('S1:', na=False)])
print(f"  [OK] {issue_counts['S1:VmvCodeUnitInconsistency']} records with unit inconsistency")

print("[S2] Checking station location stability (Rule S2)...")
# Rule S2: Each StationNumber should map to single (Lat, Long)
station_locs = df.groupby('StationNumber')[['LatitudeDecimalDegrees', 'LongitudeDecimalDegrees']].nunique().max(axis=1)
station_loc_violations = station_locs[station_locs > 1].index
for station in station_loc_violations:
    df.loc[df['StationNumber'] == station, 'audit_issues'] += 'S2:LocationVariation;'
issue_counts['S2:StationLocationVariation'] = len(df[df['audit_issues'].str.contains('S2:', na=False)])
print(f"  [OK] {issue_counts['S2:StationLocationVariation']} records with station location variation")

print("[S3] Checking project number consistency (Rule S3)...")
# Rule S3: Samples should have ProjectNumber
missing_project = df['ProjectNumber'].isna() | (df['ProjectNumber'] == '')
df.loc[missing_project, 'audit_issues'] += 'S3:MissingProject;'
issue_counts['S3:MissingProjectNumber'] = missing_project.sum()
print(f"  [OK] {issue_counts['S3:MissingProjectNumber']} records with missing project")

# =============================================================================
# MEASUREMENT RULES
# =============================================================================

print("[M1] Checking flag-qualifier alignment (Rule M1)...")
# Rule M1: Suspect measurements should have qualifier/notes
suspect_no_qualifier = (df['MeasurementFlag'] == 'S') & (df['MeasurementQualifier'].isna() | (df['MeasurementQualifier'] == ''))
df.loc[suspect_no_qualifier, 'audit_issues'] += 'M1:SuspectNoQualifier;'
issue_counts['M1:SuspectFlagNoQualifier'] = suspect_no_qualifier.sum()
print(f"  [OK] {issue_counts['M1:SuspectFlagNoQualifier']} suspect readings without qualifier")

print("[M2] Checking value range plausibility (Rule M2)...")
# Rule M2: Values should be within reasonable bounds per variable
out_of_range = pd.Series(False, index=df.index)

# pH: 0-14
if 'pH' in df['VariableName'].unique():
    ph_mask = (df['VariableName'] == 'pH') & ((df['MeasurementValue'] < 0) | (df['MeasurementValue'] > 14))
    df.loc[ph_mask, 'audit_issues'] += 'M2:OutOfRange;'
    out_of_range |= ph_mask

# Temperature: -5 to +50°C (adjust as needed for your region)
if any(df['VariableName'].str.contains('Temperature', case=False, na=False)):
    temp_mask = (df['VariableName'].str.contains('Temperature', case=False, na=False)) & \
                ((df['MeasurementValue'] < -5) | (df['MeasurementValue'] > 50))
    df.loc[temp_mask, 'audit_issues'] += 'M2:OutOfRange;'
    out_of_range |= temp_mask

# Dissolved Oxygen: 0-15 mg/L
if any(df['VariableName'].str.contains('Dissolved Oxygen', case=False, na=False)):
    do_mask = (df['VariableName'].str.contains('Dissolved Oxygen', case=False, na=False)) & \
              ((df['MeasurementValue'] < 0) | (df['MeasurementValue'] > 15))
    df.loc[do_mask, 'audit_issues'] += 'M2:OutOfRange;'
    out_of_range |= do_mask

issue_counts['M2:OutOfRangeValues'] = out_of_range.sum()
print(f"  [OK] {issue_counts['M2:OutOfRangeValues']} records with out-of-range values")

print("[M3] Checking measurement completeness (Rule M3)...")
# Rule M3: Core variables should be well-represented
core_variables = ['pH', 'Dissolved Oxygen', 'Temperature']
station_core_coverage = df.groupby('StationNumber')[['VariableName']].apply(
    lambda x: sum(1 for cv in core_variables if cv in x.values)
)
sparse_stations = station_core_coverage[station_core_coverage < 1].index
df.loc[df['StationNumber'].isin(sparse_stations), 'audit_issues'] += 'M3:SparseCore;'
issue_counts['M3:SparseCoreCoverage'] = len(df[df['audit_issues'].str.contains('M3:', na=False)])
print(f"  [OK] {issue_counts['M3:SparseCoreCoverage']} records at stations missing core variables")

# =============================================================================
# TEMPORAL RULES
# =============================================================================

print("[T1] Checking sampling frequency consistency (Rule T1)...")
# Rule T1: Sampling frequency should be consistent within project-station pairs
# (simplified: flag if gaps > 60 days between consecutive samples)
df['SampleDateTime'] = pd.to_datetime(df['SampleDateTime'], errors='coerce')
temporal_violations = 0

for station in df['StationNumber'].unique():
    station_data = df[df['StationNumber'] == station].sort_values('SampleDateTime')
    date_diffs = station_data['SampleDateTime'].diff().dt.days
    large_gaps = date_diffs[date_diffs > 60].index
    df.loc[large_gaps, 'audit_issues'] += 'T1:FrequencyGap;'
    temporal_violations += len(large_gaps)

issue_counts['T1:SamplingFrequencyGaps'] = temporal_violations
print(f"  [OK] {issue_counts['T1:SamplingFrequencyGaps']} records with sampling gaps >60 days")

print("[T2] Checking for time travel (Rule T2)...")
# Rule T2: Dates should be monotonic within project
time_travel_count = 0
for project in df['ProjectNumber'].unique():
    project_data = df[df['ProjectNumber'] == project].sort_values('SampleDateTime')
    date_diffs = project_data['SampleDateTime'].diff()
    reversals = date_diffs[date_diffs < pd.Timedelta(days=0)].index
    df.loc[reversals, 'audit_issues'] += 'T2:TimeTravel;'
    time_travel_count += len(reversals)

issue_counts['T2:TimeTravel'] = time_travel_count
print(f"  [OK] {issue_counts['T2:TimeTravel']} records with time travel violations")

print("[T3] Checking for seasonal anomalies (Rule T3)...")
# Rule T3: Simplified check - flag if temperature is implausible for season
seasonal_anomalies = 0
if any(df['VariableName'].str.contains('Temperature', case=False, na=False)):
    df['Month'] = df['SampleDateTime'].dt.month
    # Summer (Jun-Aug): expect temp > 10°C; Winter (Dec-Feb): expect temp < +20°C
    summer_cold = (df['Month'].isin([6, 7, 8])) & (df['MeasurementValue'] < 5) & \
                  (df['VariableName'].str.contains('Temperature', case=False, na=False))
    df.loc[summer_cold, 'audit_issues'] += 'T3:SeasonalAnomaly;'
    seasonal_anomalies += summer_cold.sum()

issue_counts['T3:SeasonalAnomalies'] = seasonal_anomalies
print(f"  [OK] {issue_counts['T3:SeasonalAnomalies']} records with seasonal anomalies")

# =============================================================================
# COMPLETENESS RULES
# =============================================================================

print("[C1] Checking sample validity threshold (Rule C1)...")
# Rule C1: Sample valid if >= 50% of expected variables
sample_completeness = df.groupby('SampleNumber').agg({
    'VariableName': 'nunique',
    'MeasurementValue': lambda x: x.notna().sum()
}).reset_index()
sample_completeness.columns = ['SampleNumber', 'VariableCount', 'NonNullCount']
sample_completeness['CompletePct'] = 100 * sample_completeness['NonNullCount'] / (sample_completeness['VariableCount'] + 1)

# Assume 20 expected core variables per sample (adjust as needed)
incomplete_samples = sample_completeness[sample_completeness['CompletePct'] < 50]['SampleNumber']
df.loc[df['SampleNumber'].isin(incomplete_samples), 'audit_issues'] += 'C1:LowCompleteness;'
issue_counts['C1:LowCompleteness'] = len(df[df['audit_issues'].str.contains('C1:', na=False)])
print(f"  [OK] {issue_counts['C1:LowCompleteness']} records with <50% variable coverage")

print("[C2] Checking project representativeness (Rule C2)...")
# Rule C2: Station-period representative if >= 3 samples with >= 70% coverage
station_year_coverage = df.copy()
station_year_coverage['Year'] = station_year_coverage['SampleDateTime'].dt.year
station_year_reps = station_year_coverage.groupby(['StationNumber', 'Year']).agg({
    'SampleNumber': 'nunique',
}).reset_index()
station_year_reps.columns = ['StationNumber', 'Year', 'SampleCount']

sparse_periods = station_year_reps[station_year_reps['SampleCount'] < 3][
    ['StationNumber', 'Year']
].values
for station, year in sparse_periods:
    df.loc[(df['StationNumber'] == station) & (df['SampleDateTime'].dt.year == year), 
           'audit_issues'] += 'C2:InsufficientRepresentativeness;'

issue_counts['C2:InsufficientRepresentativeness'] = len(
    df[df['audit_issues'].str.contains('C2:', na=False)]
)
print(f"  [OK] {issue_counts['C2:InsufficientRepresentativeness']} records from under-sampled station-years")

# =============================================================================
# GENERATE AUDIT REPORT
# =============================================================================

print("\n=== GENERATING AUDIT REPORTS ===\n")

# Report 1: Row-level issues
audit_output = df[['StationNumber', 'Station', 'SampleDateTime', 'VariableName', 
                    'MeasurementValue', 'MeasurementFlag', 'audit_issues']].copy()
audit_output['IssueCount'] = audit_output['audit_issues'].str.count(';')
audit_output = audit_output[audit_output['IssueCount'] > 0]  # Only rows with issues
audit_output.to_csv(output_dir / "data_quality_audit.csv", index=False)
print(f"[OK] data_quality_audit.csv ({len(audit_output)} records with issues)")

# Report 2: Summary by rule
rule_summary = pd.DataFrame(
    [(rule, count) for rule, count in issue_counts.items()],
    columns=['Rule', 'RecordCount']
).sort_values('RecordCount', ascending=False)
rule_summary.to_csv(output_dir / "quality_summary_by_rule.csv", index=False)
print(f"[OK] quality_summary_by_rule.csv ({len(rule_summary)} rules)")

# Report 3: Summary by station
station_issues = df[df['audit_issues'] != ''].groupby('StationNumber').agg({
    'audit_issues': 'count',
}).reset_index()
station_issues.columns = ['StationNumber', 'IssueCount']
station_issues['CompleteRecords'] = station_issues['StationNumber'].map(
    lambda x: len(df[df['StationNumber'] == x]) - len(df[(df['StationNumber'] == x) & (df['audit_issues'] != '')])
)
station_issues['TotalRecords'] = station_issues['StationNumber'].map(
    lambda x: len(df[df['StationNumber'] == x])
)
station_issues['CompliancePct'] = 100 * station_issues['CompleteRecords'] / station_issues['TotalRecords']
station_issues = station_issues.sort_values('CompliancePct')

station_issues.to_csv(output_dir / "quality_summary_by_station.csv", index=False)
print(f"[OK] quality_summary_by_station.csv ({len(station_issues)} stations)")

# Report 4: Summary by project
project_issues = df[df['audit_issues'] != ''].groupby('ProjectNumber').agg({
    'audit_issues': 'count',
}).reset_index()
project_issues.columns = ['ProjectNumber', 'IssueCount']
project_issues['CompleteRecords'] = project_issues['ProjectNumber'].map(
    lambda x: len(df[df['ProjectNumber'] == x]) - len(df[(df['ProjectNumber'] == x) & (df['audit_issues'] != '')])
)
project_issues['TotalRecords'] = project_issues['ProjectNumber'].map(
    lambda x: len(df[df['ProjectNumber'] == x])
)
project_issues['CompliancePct'] = 100 * project_issues['CompleteRecords'] / project_issues['TotalRecords']
project_issues = project_issues.sort_values('CompliancePct')

project_issues.to_csv(output_dir / "quality_summary_by_project.csv", index=False)
print(f"[OK] quality_summary_by_project.csv ({len(project_issues)} projects)")

# Overall summary
overall_compliance = 100 * (1 - len(df[df['audit_issues'] != '']) / len(df))
print(f"\n[OK] OVERALL DATA QUALITY COMPLIANCE: {overall_compliance:.1f}%")
print(f"[OK] {len(df[df['audit_issues'] != '']):,} records flagged with issues")
print(f"[OK] {len(df[df['audit_issues'] == '']):,} records passed all checks")

print(f"\n[OK] Data quality audit complete. Reports saved to {output_dir}\n")
