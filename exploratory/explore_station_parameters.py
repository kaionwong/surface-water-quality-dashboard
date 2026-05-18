"""
Script 4: explore_station_parameters.py
Purpose: Map which parameters are measured at each station (coverage matrix)
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
# STATION-PARAMETER COVERAGE ANALYSIS
# =============================================================================

print("\n=== STATION-PARAMETER COVERAGE ANALYSIS ===\n")

# Create station-parameter matrix
print("[OK] Building station-parameter coverage matrix...")
coverage_data = df.groupby(['StationNumber', 'Station', 'VariableName']).agg({
    'MeasurementValue': 'count',
    'SampleDateTime': ['min', 'max']
}).reset_index()

coverage_data.columns = ['StationNumber', 'Station', 'VariableName', 
                        'MeasurementCount', 'DateMin', 'DateMax']

# Pivot: rows=stations, cols=variables
station_param_matrix = coverage_data.pivot_table(
    index='StationNumber',
    columns='VariableName',
    values='MeasurementCount',
    fill_value=0
).astype(int)

station_param_matrix.to_csv(output_dir / "station_parameter_matrix.csv")
print(f"[OK] station_parameter_matrix.csv ({station_param_matrix.shape[0]} stations × {station_param_matrix.shape[1]} parameters)")

# Station profiles with summary statistics
print("[OK] Building station profiles...")
station_profiles = []

for station in df['StationNumber'].unique():
    station_data = df[df['StationNumber'] == station]
    
    station_profiles.append({
        'StationNumber': station,
        'Station': station_data['Station'].iloc[0],
        'Latitude': station_data['LatitudeDecimalDegrees'].iloc[0],
        'Longitude': station_data['LongitudeDecimalDegrees'].iloc[0],
        'TotalMeasurements': len(station_data),
        'UniqueVariables': station_data['VariableName'].nunique(),
        'UniqueSamples': station_data['SampleNumber'].nunique(),
        'UniqueProjects': station_data['ProjectNumber'].nunique(),
        'DateRangeStart': station_data['SampleDateTime'].min(),
        'DateRangeEnd': station_data['SampleDateTime'].max(),
        'YearsOfData': len(pd.to_datetime(station_data['SampleDateTime'], errors='coerce').dt.year.unique()),
        'VariableList': ', '.join(sorted(station_data['VariableName'].unique()))
    })

station_profiles_df = pd.DataFrame(station_profiles)
station_profiles_df = station_profiles_df.sort_values('TotalMeasurements', ascending=False)
station_profiles_df.to_csv(output_dir / "station_profiles.csv", index=False)
print(f"[OK] station_profiles.csv ({len(station_profiles_df)} stations)")

# Classify stations by coverage level
print("\n[OK] Classifying stations by coverage...")
station_profiles_df['CoverageLevel'] = pd.cut(
    station_profiles_df['UniqueVariables'],
    bins=[0, 3, 7, 12, 100],
    labels=['Minimal (<3 vars)', 'Basic (3-7 vars)', 'Moderate (7-12 vars)', 'Comprehensive (12+ vars)']
)

coverage_summary = station_profiles_df['CoverageLevel'].value_counts().sort_index()
print("\nStation Coverage Classification:")
for level, count in coverage_summary.items():
    print(f"  {level}: {count} stations")

# Parameter popularity (which variables are measured most)
print("\n[OK] Analyzing parameter popularity...")
param_popularity = df.groupby('VariableName').agg({
    'MeasurementValue': 'count',
    'StationNumber': 'nunique',
    'SampleDateTime': ['min', 'max']
}).reset_index()

param_popularity.columns = ['VariableName', 'TotalMeasurements', 'StationCount', 
                            'DateMin', 'DateMax']
param_popularity['StationCoverage'] = 100 * param_popularity['StationCount'] / len(df['StationNumber'].unique())
param_popularity = param_popularity.sort_values('TotalMeasurements', ascending=False)

param_popularity.to_csv(output_dir / "parameter_popularity.csv", index=False)
print(f"[OK] parameter_popularity.csv ({len(param_popularity)} parameters)")

print("\nTop 10 Most Measured Parameters:")
for idx, row in param_popularity.head(10).iterrows():
    print(f"  {row['VariableName']}: {row['TotalMeasurements']:,} measurements at {row['StationCount']} stations ({row['StationCoverage']:.1f}%)")

# Identify "complete" and "sparse" stations
print("\n[OK] Identifying station characteristics...")
complete_stations = station_profiles_df[station_profiles_df['UniqueVariables'] >= 7]
sparse_stations = station_profiles_df[station_profiles_df['UniqueVariables'] < 3]

print(f"\nComplete Stations (>=7 variables): {len(complete_stations)}")
if len(complete_stations) > 0:
    print("  Examples:")
    for _, row in complete_stations.head(3).iterrows():
        print(f"    {row['Station']} ({row['UniqueVariables']} variables, {row['TotalMeasurements']:,} measurements)")

print(f"\nSparse Stations (<3 variables): {len(sparse_stations)}")
if len(sparse_stations) > 0:
    print("  Examples:")
    for _, row in sparse_stations.head(3).iterrows():
        print(f"    {row['Station']} ({row['UniqueVariables']} variables, {row['TotalMeasurements']:,} measurements)")

# Variable diversification by station
print("\n[OK] Computing variable diversity index...")
station_diversity = station_param_matrix.apply(
    lambda row: (row > 0).sum() / len(row) * 100,
    axis=1
).reset_index()
station_diversity.columns = ['StationNumber', 'VariableDiversityPct']

station_profiles_df = station_profiles_df.merge(station_diversity, on='StationNumber', how='left')
station_profiles_df.to_csv(output_dir / "station_profiles.csv", index=False)

print(f"\n[OK] Station-parameter analysis complete. Reports saved to {output_dir}\n")
