"""
Script 5: explore_temporal_patterns.py
Purpose: Identify seasonal patterns, sampling gaps, and temporal consistency
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
df['SampleDateTime'] = pd.to_datetime(df['SampleDateTime'], errors='coerce')
print(f"[OK] Loaded {len(df):,} rows × {len(df.columns)} columns")

output_dir = Path(OUTPUT_EDA_PATH)
output_dir.mkdir(parents=True, exist_ok=True)

# =============================================================================
# TEMPORAL PATTERN ANALYSIS
# =============================================================================

print("\n=== TEMPORAL PATTERN ANALYSIS ===\n")

# Add temporal features
df['Year'] = df['SampleDateTime'].dt.year
df['Month'] = df['SampleDateTime'].dt.month
df['Quarter'] = df['SampleDateTime'].dt.quarter
df['DayOfYear'] = df['SampleDateTime'].dt.dayofyear

# =============================================================================
# 1. SAMPLING FREQUENCY AND GAPS
# =============================================================================

print("[OK] Analyzing sampling frequency and gaps...")
temporal_coverage = []

for station in df['StationNumber'].unique():
    station_data = df[df['StationNumber'] == station].sort_values('SampleDateTime')
    
    if len(station_data) < 2:
        continue
    
    sample_dates = station_data['SampleDateTime'].unique()
    sample_dates = pd.to_datetime(sample_dates[~pd.isna(sample_dates)])
    sample_dates = sorted(sample_dates)
    
    # Calculate gaps between consecutive samples
    if len(sample_dates) > 1:
        gaps = pd.Series(sample_dates[1:]).diff().dt.days.values
        gaps = gaps[~np.isnan(gaps)]
        
        avg_gap = gaps.mean() if len(gaps) > 0 else np.nan
        max_gap = gaps.max() if len(gaps) > 0 else np.nan
        gap_count_large = (gaps > 60).sum()  # Flag gaps >60 days
    else:
        avg_gap = max_gap = gap_count_large = np.nan
    
    # Estimate sampling frequency
    if avg_gap < 10:
        freq = "Weekly or more"
    elif avg_gap < 35:
        freq = "Monthly"
    elif avg_gap < 100:
        freq = "Quarterly"
    else:
        freq = "Annual or less"
    
    temporal_coverage.append({
        'StationNumber': station,
        'Station': station_data['Station'].iloc[0],
        'SampleCount': len(station_data['SampleNumber'].unique()),
        'DateRangeStart': sample_dates[0],
        'DateRangeEnd': sample_dates[-1],
        'YearsSpanned': (sample_dates[-1] - sample_dates[0]).days / 365.25,
        'EstimatedFrequency': freq,
        'AvgGapDays': avg_gap,
        'MaxGapDays': max_gap,
        'GapsOver60Days': gap_count_large
    })

temporal_df = pd.DataFrame(temporal_coverage)
temporal_df = temporal_df.sort_values('SampleCount', ascending=False)
temporal_df.to_csv(output_dir / "temporal_coverage_by_station.csv", index=False)
print(f"[OK] temporal_coverage_by_station.csv ({len(temporal_df)} stations)")

# =============================================================================
# 2. SEASONAL SAMPLING PATTERNS
# =============================================================================

print("[OK] Analyzing seasonal sampling patterns...")
seasonal_pattern = df.groupby(['Quarter']).size().reset_index(name='SampleCount')
seasonal_pattern['QuarterName'] = seasonal_pattern['Quarter'].map({
    1: 'Q1 (Jan-Mar)',
    2: 'Q2 (Apr-Jun)',
    3: 'Q3 (Jul-Sep)',
    4: 'Q4 (Oct-Dec)'
})
seasonal_pattern['SamplePct'] = 100 * seasonal_pattern['SampleCount'] / seasonal_pattern['SampleCount'].sum()

seasonal_pattern.to_csv(output_dir / "seasonal_sampling_pattern.csv", index=False)
print(f"[OK] seasonal_sampling_pattern.csv")
print("\nSeasonal Distribution:")
for idx, row in seasonal_pattern.iterrows():
    print(f"  {row['QuarterName']}: {row['SampleCount']:,} samples ({row['SamplePct']:.1f}%)")

# Monthly distribution
print("\n[OK] Analyzing monthly distribution...")
monthly_data = df.groupby('Month').agg({
    'SampleNumber': 'nunique',
    'MeasurementValue': 'count'
}).reset_index()
monthly_data.columns = ['Month', 'UniqueSamples', 'TotalMeasurements']
monthly_data['MonthName'] = monthly_data['Month'].map({
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
})

print("Monthly Sampling Distribution:")
for idx, row in monthly_data.iterrows():
    pct = 100 * row['TotalMeasurements'] / df.shape[0]
    print(f"  {row['MonthName']}: {row['UniqueSamples']} samples, {row['TotalMeasurements']:,} measurements ({pct:.1f}%)")

# =============================================================================
# 3. TEMPORAL CONSISTENCY CHECK
# =============================================================================

print("\n[OK] Checking for temporal inconsistencies...")
violations = []

for station in df['StationNumber'].unique():
    station_data = df[df['StationNumber'] == station].sort_values('SampleDateTime')
    
    # Check for time travel (dates should be monotonic)
    date_diffs = station_data['SampleDateTime'].diff()
    time_travel = date_diffs[date_diffs < pd.Timedelta(days=0)]
    
    if len(time_travel) > 0:
        violations.append({
            'StationNumber': station,
            'ViolationType': 'TimeTravel',
            'Count': len(time_travel),
            'Description': f"Found {len(time_travel)} instances where sampling date reversed"
        })

violations_df = pd.DataFrame(violations)
violations_df.to_csv(output_dir / "temporal_violations.csv", index=False)

if len(violations_df) > 0:
    print(f"[OK] temporal_violations.csv ({len(violations_df)} violations found)")
    for idx, row in violations_df.iterrows():
        print(f"  {row['ViolationType']}: {row['Count']} instances")
else:
    print(f"[OK] temporal_violations.csv (NO temporal violations detected)")

# =============================================================================
# 4. TEMPORAL COVERAGE BY YEAR AND STATION
# =============================================================================

print("\n[OK] Analyzing coverage by year...")
yearly_coverage = df.groupby(['Year', 'StationNumber']).agg({
    'SampleNumber': 'nunique',
    'MeasurementValue': 'count'
}).reset_index()
yearly_coverage.columns = ['Year', 'StationNumber', 'UniqueSamples', 'MeasurementCount']

# Pivot to see coverage matrix
yearly_pivot = yearly_coverage.pivot_table(
    index='StationNumber',
    columns='Year',
    values='MeasurementCount',
    fill_value=0
).astype(int)

yearly_pivot.to_csv(output_dir / "temporal_coverage_by_year.csv")
print(f"[OK] temporal_coverage_by_year.csv ({yearly_pivot.shape[0]} stations × {yearly_pivot.shape[1]} years)")

# Overall temporal summary
print("\n=== TEMPORAL SUMMARY ===")
print(f"Data spans: {df['SampleDateTime'].min().date()} to {df['SampleDateTime'].max().date()}")
print(f"Total years covered: {len(df['Year'].unique())}")
print(f"Years covered:")
for year in sorted(df['Year'].unique()):
    year_count = len(df[df['Year'] == year])
    print(f"  {int(year)}: {year_count:,} measurements")

print(f"\n[OK] Temporal pattern analysis complete. Reports saved to {output_dir}\n")
