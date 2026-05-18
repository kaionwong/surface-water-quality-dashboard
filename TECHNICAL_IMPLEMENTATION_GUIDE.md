# Technical Implementation Guide: Surface Water Quality Data Processing

**Version**: 1.0  
**Date**: May 18, 2024  
**Status**: Complete - Ready for Phase 3 Implementation  

---

## Overview

This guide provides technical specifications for implementing data processing pipelines, analytical workflows, and reporting systems for the Alberta Surface Water Quality Monitoring dataset. All recommendations are based on Phase 1-2 exploratory and confirmatory analysis.

---

## Section 1: Data Pipeline Architecture

### 1.1 Source Data Ingestion

#### Source System
```
Source: Alberta Environment & Protected Areas (EPA) Database
Format: CSV export (RDBMS dump)
Update Frequency: Quarterly (recommend)
Retention Period: All historical data (current: 2020-2023)
```

#### Ingestion Workflow

```python
"""
Recommended Python pseudocode for ETL ingestion
"""
import pandas as pd
from datetime import datetime

# Step 1: Read raw CSV
raw_data = pd.read_csv('raw_swq_monitoring_data.csv')
# Expected shape: ~32,264 rows × ~15 columns

# Step 2: Initial schema validation
required_columns = [
    'STATION_CODE', 'STATION_NAME', 'SAMPLE_DATE',
    'PARAMETER_CODE', 'PARAMETER_NAME', 'RESULT_VALUE',
    'RESULT_UNIT_CODE', 'LATITUDE', 'LONGITUDE', 'BASIN_NAME'
]
missing_cols = set(required_columns) - set(raw_data.columns)
assert not missing_cols, f"Missing required columns: {missing_cols}"

# Step 3: Type conversion
raw_data['SAMPLE_DATE'] = pd.to_datetime(raw_data['SAMPLE_DATE'])
raw_data['RESULT_VALUE'] = pd.to_numeric(raw_data['RESULT_VALUE'], errors='coerce')
raw_data['LATITUDE'] = pd.to_numeric(raw_data['LATITUDE'])
raw_data['LONGITUDE'] = pd.to_numeric(raw_data['LONGITUDE'])

# Step 4: Geocoding validation
assert raw_data['LATITUDE'].between(51, 61).all(), "Invalid latitude range"
assert raw_data['LONGITUDE'].between(-128, -110).all(), "Invalid longitude range"

# Step 5: Deduplication
print(f"Rows before dedup: {len(raw_data)}")
raw_data = raw_data.drop_duplicates()
print(f"Rows after dedup: {len(raw_data)}")

# Step 6: Store in analytics database
# (See Section 2: Database Schema for table design)
raw_data.to_sql('raw_swq_observations', engine, if_exists='replace')

print("✓ Ingestion complete")
print(f"  - {len(raw_data)} records loaded")
print(f"  - {raw_data['STATION_CODE'].nunique()} unique stations")
print(f"  - Date range: {raw_data['SAMPLE_DATE'].min()} to {raw_data['SAMPLE_DATE'].max()}")
```

#### Validation Rules (Stage 1)

| Rule | Implementation | Action on Fail |
|------|---|---|
| Schema Validation | All required columns present | Reject batch; alert admin |
| Type Check | Numeric columns parse; dates valid | Coerce nulls; tag for review |
| Geocoding | Lat 51-61°N; Lon 110-128°W | Flag record; manual review |
| Deduplication | Drop exact row duplicates | Warn if >5% duplicates |

---

### 1.2 Data Cleaning & Standardization

#### Unit Standardization (Critical)

```python
"""
Handle VmvCode 6107: Dual-unit inconsistency
Specifications from unit_definitions.yaml
"""
import pandas as pd

# Define unit conversions
UNIT_CONVERSIONS = {
    # Example: mg/L to ug/L (×1000)
    ('6071', '6102'): lambda x: x * 1000,  # mg/L → ug/L
    
    # Define reverse conversions as needed
    ('6102', '6071'): lambda x: x / 1000,  # ug/L → mg/L
}

def standardize_units(df, target_unit='6071'):  # Default: mg/L
    """
    Standardize all measurements to target unit.
    
    Args:
        df: DataFrame with RESULT_VALUE and RESULT_UNIT_CODE
        target_unit: Target VmvCode (default 6071 = mg/L)
    
    Returns:
        DataFrame with standardized values and units
    """
    df['RESULT_VALUE_STANDARDIZED'] = df['RESULT_VALUE']
    df['UNIT_STANDARDIZED'] = df['RESULT_UNIT_CODE']
    
    # Identify records needing conversion
    needs_conversion = df['RESULT_UNIT_CODE'] != target_unit
    
    for unit_pair, converter in UNIT_CONVERSIONS.items():
        source_unit, dest_unit = unit_pair
        if dest_unit == target_unit:
            mask = (df['RESULT_UNIT_CODE'] == source_unit) & needs_conversion
            df.loc[mask, 'RESULT_VALUE_STANDARDIZED'] = \
                df.loc[mask, 'RESULT_VALUE'].apply(converter)
            df.loc[mask, 'UNIT_STANDARDIZED'] = target_unit
            df.loc[mask, 'UNIT_CONVERSION_APPLIED'] = True
    
    return df

# Apply standardization
data_cleaned = standardize_units(raw_data, target_unit='mg/L code')
print(f"Standardized {data_cleaned['UNIT_CONVERSION_APPLIED'].sum()} records")
```

#### Quality Flags (S1, M2, C2)

```python
"""
Implement quality checks as defined in Phase 2
"""
def apply_quality_flags(df):
    """
    Apply S1 (unit consistency), M2 (value range), C2 (field name) flags.
    """
    
    # S1: Unit Consistency
    df['QA_S1_UNIT_ISSUE'] = False
    df.loc[df['RESULT_UNIT_CODE'].isin(['6107']), 'QA_S1_UNIT_ISSUE'] = True
    
    # M2: Value Range Check (load ranges from variable_catalog.yaml)
    value_ranges = {
        'pH': (6.5, 8.5),
        'DISSOLVED_OXYGEN': (0, 15),
        'TEMPERATURE': (-0.5, 30),
        'TURBIDITY': (0, 100),
        # ... extend for all parameters
    }
    
    for param, (min_val, max_val) in value_ranges.items():
        mask = (df['PARAMETER_NAME'] == param)
        out_of_range = (df.loc[mask, 'RESULT_VALUE'] < min_val) | \
                       (df.loc[mask, 'RESULT_VALUE'] > max_val)
        df.loc[mask & out_of_range, 'QA_M2_OUT_OF_RANGE'] = True
    
    # C2: Field Name Consistency
    required_fields = ['STATION_CODE', 'SAMPLE_DATE', 'PARAMETER_NAME']
    df['QA_C2_MISSING_FIELD'] = df[required_fields].isnull().any(axis=1)
    
    # Summary
    print("Quality Flag Summary:")
    print(f"  S1 Issues: {df['QA_S1_UNIT_ISSUE'].sum()} records")
    print(f"  M2 Issues: {df['QA_M2_OUT_OF_RANGE'].sum()} records")
    print(f"  C2 Issues: {df['QA_C2_MISSING_FIELD'].sum()} records")
    
    return df

data_quality = apply_quality_flags(data_cleaned)
```

---

### 1.3 Temporal Aggregation

#### Sample Date Clustering

```python
"""
Aggregate records taken on same date at same station
(Handle lab delays, split submissions, etc.)
"""

def consolidate_samples(df, date_tolerance_days=1):
    """
    Group measurements taken within N days of each other
    at the same station to create unified "samples."
    
    Args:
        df: Raw observations DataFrame
        date_tolerance_days: Window for clustering (default: 1)
    
    Returns:
        DataFrame with SAMPLE_ID and SAMPLE_DATE cluster
    """
    
    # Sort by station and date
    df = df.sort_values(['STATION_CODE', 'SAMPLE_DATE'])
    
    # Create sample ID based on date clustering
    df['SAMPLE_DATE_CLUSTER'] = (
        (df.groupby('STATION_CODE')['SAMPLE_DATE'].diff() > 
         pd.Timedelta(days=date_tolerance_days))
        .cumsum()
        .astype(str)
    )
    
    df['SAMPLE_ID'] = (
        df['STATION_CODE'] + '_' + 
        df['SAMPLE_DATE_CLUSTER'] + '_' + 
        df['SAMPLE_DATE'].dt.strftime('%Y%m%d')
    )
    
    return df

samples_consolidated = consolidate_samples(data_quality)
print(f"Unique samples (observations): {samples_consolidated['SAMPLE_ID'].nunique()}")
# Expected: ~3,150 samples across 174 stations over 4 years
```

#### Temporal Window Definitions

```python
"""
Define standard aggregation windows for reporting
"""
TEMPORAL_WINDOWS = {
    'event': {
        'description': 'Single sampling event (raw data)',
        'aggregation': None,
        'use_case': 'Exploratory analysis, outlier detection'
    },
    'daily': {
        'description': 'Daily mean across all parameters',
        'aggregation': 'mean',
        'use_case': 'Rare; use only if high-frequency sampling'
    },
    'weekly': {
        'description': 'Weekly average',
        'aggregation': 'mean',
        'use_case': 'Suitable for monitoring compliance'
    },
    'monthly': {
        'description': 'Monthly average',
        'aggregation': 'mean',
        'use_case': 'Standard for trend analysis; matches sampling frequency'
    },
    'quarterly': {
        'description': 'Quarterly average (3-month)',
        'aggregation': 'mean',
        'use_case': 'Seasonal analysis'
    },
    'annual': {
        'description': 'Yearly average',
        'aggregation': 'mean',
        'use_case': 'Long-term trends, inter-year comparisons'
    },
    'multi_year': {
        'description': 'Multi-year rolling average',
        'aggregation': 'mean',
        'use_case': 'Environmental baselines, climate signals'
    }
}

def aggregate_to_window(df, window='monthly'):
    """Aggregate raw data to specified temporal window."""
    spec = TEMPORAL_WINDOWS[window]
    
    if spec['aggregation'] == 'mean':
        if window == 'monthly':
            df['PERIOD'] = df['SAMPLE_DATE'].dt.to_period('M')
        elif window == 'annual':
            df['PERIOD'] = df['SAMPLE_DATE'].dt.to_period('Y')
        # ... extend for other windows
        
        result = df.groupby(['STATION_CODE', 'PARAMETER_NAME', 'PERIOD']).agg({
            'RESULT_VALUE_STANDARDIZED': ['mean', 'std', 'count', 'min', 'max'],
            'SAMPLE_ID': 'count'
        }).reset_index()
        
        return result
    else:
        return df  # Return raw data for 'event'

monthly_agg = aggregate_to_window(samples_consolidated, window='monthly')
print(f"Monthly aggregated: {len(monthly_agg)} records")
```

---

## Section 2: Database Schema Design

### 2.1 Normalized Schema (PostgreSQL)

```sql
-- Schema: surface_water_quality
-- Purpose: Store ~32K observations across 174 stations with 82+ parameters

-- Table 1: Stations (Reference Data)
CREATE TABLE stations (
    station_id SERIAL PRIMARY KEY,
    station_code VARCHAR(20) UNIQUE NOT NULL,  -- e.g., 'AB07AE0160'
    station_name VARCHAR(255) NOT NULL,
    latitude DECIMAL(9, 6) NOT NULL,           -- WGS 84
    longitude DECIMAL(10, 6) NOT NULL,         -- WGS 84
    basin_code VARCHAR(50),
    basin_name VARCHAR(255),
    tier INT,                                   -- 1 (comprehensive) or 2 (moderate)
    num_variables INT,                          -- # of parameters measured
    first_sample_date DATE,
    last_sample_date DATE,
    sample_count INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stations_code ON stations(station_code);
CREATE INDEX idx_stations_basin ON stations(basin_code);
CREATE INDEX idx_stations_tier ON stations(tier);

-- Table 2: Parameters (Reference Data)
CREATE TABLE parameters (
    parameter_id SERIAL PRIMARY KEY,
    parameter_code VARCHAR(20) UNIQUE NOT NULL,
    parameter_name VARCHAR(255) NOT NULL,
    description TEXT,
    unit_code VARCHAR(10),
    unit_symbol VARCHAR(20),
    category VARCHAR(50),  -- pH, nutrients, cations/anions, etc.
    expected_min DECIMAL(10, 4),
    expected_max DECIMAL(10, 4),
    preferred_aggregation VARCHAR(20),  -- 'mean', 'median', 'sum'
    detection_limit DECIMAL(10, 4),
    is_core BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_param_code ON parameters(parameter_code);
CREATE INDEX idx_param_category ON parameters(category);

-- Table 3: Unit Code Mappings (Reference Data - from unit_definitions.yaml)
CREATE TABLE unit_codes (
    vmvcode VARCHAR(10) PRIMARY KEY,
    unit_symbol VARCHAR(20) NOT NULL,
    unit_name VARCHAR(100) NOT NULL,
    decimal_places INT,
    conversion_to_si VARCHAR(50),
    notes TEXT
);

-- Table 4: Observations (Fact Table - ~32K rows)
CREATE TABLE observations (
    observation_id SERIAL PRIMARY KEY,
    station_id INT NOT NULL REFERENCES stations(station_id),
    parameter_id INT NOT NULL REFERENCES parameters(parameter_id),
    sample_date DATE NOT NULL,
    result_value DECIMAL(12, 4),
    unit_code VARCHAR(10) NOT NULL REFERENCES unit_codes(vmvcode),
    result_value_standardized DECIMAL(12, 4),  -- Post-conversion
    unit_code_standardized VARCHAR(10),
    qa_s1_unit_issue BOOLEAN DEFAULT FALSE,
    qa_m2_out_of_range BOOLEAN DEFAULT FALSE,
    qa_c2_missing_field BOOLEAN DEFAULT FALSE,
    quality_flag VARCHAR(20),  -- 'OK', 'WARNING', 'ERROR'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_obs_station ON observations(station_id);
CREATE INDEX idx_obs_parameter ON observations(parameter_id);
CREATE INDEX idx_obs_date ON observations(sample_date);
CREATE INDEX idx_obs_station_date ON observations(station_id, sample_date);
CREATE INDEX idx_obs_quality ON observations(qa_s1_unit_issue, qa_m2_out_of_range);

-- Table 5: Aggregated Data (Monthly)
CREATE TABLE monthly_aggregations (
    aggregation_id SERIAL PRIMARY KEY,
    station_id INT NOT NULL REFERENCES stations(station_id),
    parameter_id INT NOT NULL REFERENCES parameters(parameter_id),
    period_year INT NOT NULL,
    period_month INT NOT NULL,
    value_mean DECIMAL(12, 4),
    value_std DECIMAL(12, 4),
    value_min DECIMAL(12, 4),
    value_max DECIMAL(12, 4),
    sample_count INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(station_id, parameter_id, period_year, period_month)
);

CREATE INDEX idx_monthly_station ON monthly_aggregations(station_id);
CREATE INDEX idx_monthly_period ON monthly_aggregations(period_year, period_month);

-- Table 6: Audit Log (Governance)
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    action_type VARCHAR(50),  -- 'INSERT', 'UPDATE', 'DELETE', 'QUALITY_FLAG'
    table_name VARCHAR(50),
    record_id INT,
    user_id VARCHAR(50),
    change_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Materialized View: Station Summary (Fast Dashboard Queries)
CREATE MATERIALIZED VIEW v_station_summary AS
SELECT
    s.station_code,
    s.station_name,
    s.basin_name,
    s.tier,
    COUNT(DISTINCT o.parameter_id) as num_parameters,
    COUNT(DISTINCT DATE(o.sample_date)) as num_samples,
    MIN(o.sample_date) as first_sample,
    MAX(o.sample_date) as last_sample,
    SUM(CASE WHEN o.qa_s1_unit_issue THEN 1 ELSE 0 END) as s1_violations,
    SUM(CASE WHEN o.qa_m2_out_of_range THEN 1 ELSE 0 END) as m2_violations,
    ROUND(100.0 * (COUNT(*) - COALESCE(SUM(CASE 
        WHEN o.qa_s1_unit_issue OR o.qa_m2_out_of_range OR o.qa_c2_missing_field 
        THEN 1 ELSE 0 END), 0)) / COUNT(*), 2) as compliance_pct
FROM
    stations s
LEFT JOIN observations o ON s.station_id = o.station_id
GROUP BY s.station_id, s.station_code, s.station_name, s.basin_name, s.tier;

CREATE INDEX idx_v_station_code ON v_station_summary(station_code);
```

### 2.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Separate Fact & Reference** | Stations, parameters, units are slowly-changing; separate for normalization |
| **Standardized Value Column** | Store original + converted; enables auditing, unit traceability |
| **Quality Flags as Booleans** | S1, M2, C2 easily filterable; can sum for compliance metrics |
| **Aggregated Table** | Pre-compute monthly summaries for fast dashboard queries (vs. real-time aggregation) |
| **Audit Log** | Track all changes for governance, reproducibility, regulatory compliance |
| **Materialized View** | Expensive GROUP BY pre computed; refresh nightly |

---

## Section 3: Python Analysis Workflows

### 3.1 Standard Import & Setup

```python
"""
Standard imports and configuration for all analyses
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configuration
CONFIG = {
    'data_dir': './data/processed/',
    'output_dir': './output/results/',
    'figures_dir': './output/figures/',
    'default_test_alpha': 0.05,
    'temporal_window': 'monthly',  # Default aggregation
    'exclude_quality_issues': False,  # If True, filter Q1, M2, C2 violations
}

# Color palette (for consistency across reports)
PALETTE = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'warning': '#d62728',
    'neutral': '#7f7f7f'
}

# Load core data
stations_df = pd.read_csv(f"{CONFIG['data_dir']}/stations.csv")
parameters_df = pd.read_csv(f"{CONFIG['data_dir']}/parameters.csv")
obs_df = pd.read_csv(f"{CONFIG['data_dir']}/observations.csv", 
                      parse_dates=['sample_date'],
                      low_memory=False)

print(f"Loaded {len(obs_df)} observations across {obs_df['station_id'].nunique()} stations")
print(f"Date range: {obs_df['sample_date'].min()} to {obs_df['sample_date'].max()}")
```

### 3.2 Single-Station Trend Analysis

```python
"""
Template for analyzing water quality trends at a specific station
Example: Phosphorus Total (TP) trend at Milk River station
"""

def analyze_station_trend(station_code, parameter_name, window='monthly'):
    """
    Analyze temporal trend for a parameter at single station.
    
    Args:
        station_code: e.g., 'AB07AE0160'
        parameter_name: e.g., 'Phosphorus Total'
        window: 'monthly' or 'annual'
    
    Returns:
        dict with trend, significance, visualization data
    """
    from scipy.stats import linregress
    import matplotlib.pyplot as plt
    
    # 1. Filter data
    station_id = stations_df[stations_df['station_code'] == station_code]['station_id'].iloc[0]
    param_id = parameters_df[parameters_df['parameter_name'] == parameter_name]['parameter_id'].iloc[0]
    
    data = obs_df[
        (obs_df['station_id'] == station_id) &
        (obs_df['parameter_id'] == param_id) &
        (~obs_df['qa_m2_out_of_range'])  # Exclude outliers
    ].copy()
    
    if len(data) < 10:
        raise ValueError(f"Insufficient data ({len(data)} records)")
    
    # 2. Aggregate to temporal window
    if window == 'monthly':
        data['period'] = data['sample_date'].dt.to_period('M')
    elif window == 'annual':
        data['period'] = data['sample_date'].dt.to_period('Y')
    
    ts = data.groupby('period')['result_value_standardized'].agg(['mean', 'std', 'count'])
    ts['date'] = ts.index.to_timestamp()
    
    # 3. Linear regression
    x = np.arange(len(ts))
    y = ts['mean'].values
    valid_idx = ~np.isnan(y)
    x_valid = x[valid_idx]
    y_valid = y[valid_idx]
    
    slope, intercept, r_value, p_value, std_err = linregress(x_valid, y_valid)
    
    # 4. Interpretation
    trend_interpretation = "increasing" if slope > 0 else "decreasing"
    significant = "YES" if p_value < 0.05 else "NO"
    
    # 5. Visualization
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.errorbar(ts['date'], ts['mean'], yerr=ts['std'], fmt='o-', label='Mean ± SD')
    ax.plot(ts['date'], slope * x + intercept, 'r--', label=f'Trend (p={p_value:.4f})')
    ax.set_xlabel('Time')
    ax.set_ylabel(f'{parameter_name} ({data["unit_code"].iloc[0]})')
    ax.set_title(f'{station_code}: {parameter_name} Trend')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    return {
        'station_code': station_code,
        'parameter_name': parameter_name,
        'trend': trend_interpretation,
        'slope': slope,
        'p_value': p_value,
        'significant': significant,
        'r_squared': r_value ** 2,
        'n_observations': len(y_valid),
        'time_series': ts,
        'figure': fig
    }

# Example usage
result = analyze_station_trend('AB07AE0160', 'Phosphorus Total', window='monthly')
print(f"Phosphorus Total trend at {result['station_code']}: {result['trend']} (p={result['p_value']:.4f})")
if result['significant'] == 'YES':
    print(f"  → Statistically significant change of {result['slope']:.6f} units/month")
```

### 3.3 Multi-Station Comparative Analysis

```python
"""
Compare water quality across stations in a basin
"""

def compare_basin_stations(basin_name, parameter_name, year=2023):
    """
    Generate comparative statistics across stations in a basin.
    
    Args:
        basin_name: e.g., 'PEACE RIVER'
        parameter_name: e.g., 'Phosphorus Total'
        year: Filter to specific year (optional)
    
    Returns:
        DataFrame with station-level statistics
    """
    
    # 1. Identify stations in basin
    basin_stations = stations_df[stations_df['basin_name'] == basin_name]
    param_id = parameters_df[parameters_df['parameter_name'] == parameter_name]['parameter_id'].iloc[0]
    
    # 2. Filter observations
    data = obs_df[
        (obs_df['station_id'].isin(basin_stations['station_id'])) &
        (obs_df['parameter_id'] == param_id) &
        (~obs_df['qa_m2_out_of_range'])
    ]
    
    if not data.empty:
        data = data[data['sample_date'].dt.year == year]
    
    if len(data) < 10:
        raise ValueError(f"Insufficient data for {basin_name} in {year}")
    
    # 3. Calculate statistics per station
    comparision = data.groupby('station_id').agg({
        'result_value_standardized': ['mean', 'std', 'count', 'min', 'max']
    }).round(3)
    
    # 4. Add station metadata
    comparison.columns = ['Mean', 'StdDev', 'Count', 'Min', 'Max']
    comparison['station_code'] = comparison.index.map(
        lambda x: stations_df[stations_df['station_id'] == x]['station_code'].iloc[0]
    )
    comparison['station_name'] = comparison.index.map(
        lambda x: stations_df[stations_df['station_id'] == x]['station_name'].iloc[0]
    )
    
    # 5. Sort by mean value
    comparison = comparison.sort_values('Mean', ascending=False)
    
    return comparison

# Example usage
basin_comp = compare_basin_stations('PEACE RIVER', 'Phosphorus Total', year=2023)
print(basin_comp[['station_code', 'station_name', 'Mean', 'Count']])
```

---

## Section 4: Quality Assurance & Validation

### 4.1 Pre-Analysis Checklist

```python
"""
Run before starting any analysis to ensure data integrity
"""

def pre_analysis_check(station_codes=None, parameter_names=None, 
                        year_range=(2020, 2023)):
    """
    Comprehensive data quality validation.
    
    Returns:
        dict with pass/fail status and warnings
    """
    
    checks = {}
    
    # 1. Data Availability
    checks['data_loaded'] = len(obs_df) > 0
    checks['n_stations'] = obs_df['station_id'].nunique()
    checks['n_parameters'] = obs_df['parameter_id'].nunique()
    checks['n_observations'] = len(obs_df)
    
    # 2. Station Availability
    if station_codes:
        invalid_stations = [s for s in station_codes 
                           if s not in stations_df['station_code'].values]
        checks['stations_valid'] = len(invalid_stations) == 0
        if invalid_stations:
            checks['invalid_stations_warning'] = invalid_stations
    
    # 3. Parameter Availability
    if parameter_names:
        invalid_params = [p for p in parameter_names 
                         if p not in parameters_df['parameter_name'].values]
        checks['parameters_valid'] = len(invalid_params) == 0
        if invalid_params:
            checks['invalid_params_warning'] = invalid_params
    
    # 4. Temporal Coverage
    checks['date_min'] = obs_df['sample_date'].min()
    checks['date_max'] = obs_df['sample_date'].max()
    checks['span_years'] = (checks['date_max'] - checks['date_min']).days / 365.25
    
    # 5. Quality Flags
    checks['s1_violations'] = obs_df['qa_s1_unit_issue'].sum()
    checks['m2_violations'] = obs_df['qa_m2_out_of_range'].sum()
    checks['c2_violations'] = obs_df['qa_c2_missing_field'].sum()
    checks['total_violations'] = (checks['s1_violations'] + 
                                 checks['m2_violations'] + 
                                 checks['c2_violations'])
    checks['compliance_pct'] = 100 * (1 - checks['total_violations'] / len(obs_df))
    
    # Print summary
    print("=" * 60)
    print("PRE-ANALYSIS DATA QUALITY CHECK")
    print("=" * 60)
    print(f"✓ Data loaded: {checks['n_observations']:,} observations")
    print(f"✓ Stations: {checks['n_stations']}")
    print(f"✓ Parameters: {checks['n_parameters']}")
    print(f"✓ Temporal span: {checks['span_years']:.1f} years")
    print(f"✓ Compliance: {checks['compliance_pct']:.2f}%")
    print(f"  - S1 violations (unit inconsistency): {checks['s1_violations']}")
    print(f"  - M2 violations (out-of-range): {checks['m2_violations']}")
    print(f"  - C2 violations (missing fields): {checks['c2_violations']}")
    
    if checks['stations_valid'] and checks['parameters_valid']:
        print("\n✓ Requested stations and parameters available")
    else:
        print("\n⚠ WARNING: Some requested data unavailable")
    
    print("=" * 60)
    
    return checks

# Run check
pre_check = pre_analysis_check(
    station_codes=['AB07AE0160'],
    parameter_names=['Phosphorus Total', 'Nitrogen Total Kjeldahl (TKN)']
)
```

### 4.2 Statistical Test Best Practices

| Test | Use Case | Assumptions | Cautions |
|------|----------|-------------|----------|
| **Paired t-test** | Compare same station, different years | Normality; paired samples | Sensitive to outliers |
| **ANOVA** | Compare ≥3 stations, same parameter | Normality; equal variance | Violations don't invalidate; use Kruskal-Wallis alternative |
| **Mann-Whitney U** | Compare 2 stations (non-parametric) | —None— | Rank-based; less power than t-test |
| **Kruskal-Wallis** | Compare ≥3 stations (non-parametric) | —None— | Preferred if not normal |
| **Linear Regression** | Trend analysis | Linearity; independence; normality of residuals | Check residual plots |
| **Spearman Correlation** | Correlation between parameters | —None— | Rank-based; robust to outliers |

---

## Section 5: Reporting Standards

### 5.1 Report Template

```markdown
# Water Quality Analysis Report: [TITLE]

## Executive Summary
[1 paragraph: key finding, implication, recommendation]

## Methodology
- **Data Source**: Alberta Surface Water Quality Monitoring Network
- **Temporal Scope**: [date range]
- **Geographic Scope**: [basin/station(s)]
- **Parameters Analyzed**: [list]
- **Quality Flags Considered**: [S1/M2/C2 handling]

## Data Preparation
- Raw observations pooled: **X** records
- Quality-controlled observations: **Y** records (Z% compliance)
- Temporal aggregation window: **[monthly/annual]**
- Unit standardization: **[applied/not applicable]**

## Results
[Findings, tables, figures]

## Limitations
- [Data limitation 1]
- [Data limitation 2]
- [Statistical limitation]

## Conclusions
[What does this mean for basin management/decision-making?]

## Appendix A: Data Quality Summary
[Reference to Phase 2 documentation]

## Appendix B: Station & Parameter Metadata
[Details from station_profiles.yaml and variable_catalog.yaml]

---
**Data Citation**: Alberta Surface Water Quality Monitoring Dataset - Phase 2 Documentation (2024)  
**Report Date**: [date]  
**Analyst**: [name]  
**Confidence Level**: [High/Medium/Low]
```

---

## Section 6: Deployment & Ops

### 6.1 Docker Deployment

```dockerfile
# Dockerfile for analytics pipeline
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY src/ ./src/

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    OUTPUT_DIR=/output

# Run pipeline
CMD ["python", "src/main.py"]
```

### 6.2 Scheduling & Monitoring

```python
"""
Example: Apache Airflow DAG for ETL pipeline
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'retries': 2,
    'retry_delay': timedelta(hours=1),
    'on_failure_callback': slack_notify  # Custom function
}

dag = DAG(
    'swq_etl_pipeline',
    default_args=default_args,
    description='Surface Water Quality data refresh',
    schedule_interval='0 2 * * MON',  # Every Monday at 2 AM
    start_date=datetime(2024, 1, 1),
    catchup=False
)

# Task 1: Ingest
ingest_task = PythonOperator(
    task_id='ingest_from_source',
    python_callable=ingest_data,
    op_kwargs={'source_db': 'epa_prod'},
    dag=dag
)

# Task 2: Clean
clean_task = PythonOperator(
    task_id='clean_and_validate',
    python_callable=clean_data,
    upstream=[ingest_task],
    dag=dag
)

# Task 3: Load
load_task = PythonOperator(
    task_id='load_to_analytics_db',
    python_callable=load_data,
    upstream=[clean_task],
    dag=dag
)

# Task 4: Aggregate
aggregate_task = PythonOperator(
    task_id='compute_aggregations',
    python_callable=compute_monthly_aggregations,
    upstream=[load_task],
    dag=dag
)

# Task 5: Report
report_task = PythonOperator(
    task_id='generate_monthly_report',
    python_callable=generate_quality_report,
    upstream=[aggregate_task],
    dag=dag
)

# Define dependencies
ingest_task >> clean_task >> load_task >> aggregate_task >> report_task
```

---

## Section 7: Troubleshooting & FAQ

### Q: Data looks different than expected. What could be wrong?

**A**: Check in order:
1. **Date range**: Did you filter by correct dates in `station_profiles.yaml`?
2. **Quality flags**: Are M2 violations excluded? See `apply_quality_flags()` in Section 1.2
3. **Unit conversion**: Was VmvCode 6107 converted? See Section 1.2
4. **Aggregation method**: Did you use correct aggregation window? See `TEMPORAL_WINDOWS`

### Q: Can I compare stations from different basins?

**A**: **Yes**, but:
- ✓ OK for exploratory analysis
- ✓ OK for sensitivity analysis
- ⚠ Caution: Different geology, land use, flow regimes
- ✗ NOT recommended for direct comparison without contextualizing differences

### Q: How do I handle missing data?

**A**: Depends on use case:
- **Trend analysis**: Exclude months with no data; flag in report
- **Spatial comparison**: Report sample sizes; avoid over-interpreting small-n differences
- **Aggregation**: Require ≥1 measurement per aggregation window (or per policy)

### Q: What's the best way to visualize multi-station comparison?

**A**:
- **Box plots** if ≤10 stations (easy to see outliers)
- **Time series** if comparing temporal trends
- **Heatmaps** if comparing ≥10 stations × ≥5 parameters
- **Interactive dashboard** for exploratory analysis

---

## Appendix A: Python Package Dependencies

```
# requirements.txt
pandas==2.0.0
numpy==1.24.0
scipy==1.10.0
matplotlib==3.7.0
seaborn==0.12.0
sqlalchemy==2.0.0
psycopg2-binary==2.9.0
openpyxl==3.10.0
click==8.1.0
pytest==7.3.0
```

---

## Appendix B: References

1. **Phase 2 Documentation**: See `station_profiles.yaml`, `variable_catalog.yaml`, `unit_definitions.yaml`
2. **EPA Database**: Internal source; contact EPA for raw data access
3. **Statistical Methods**: Standard references apply (t-tests, ANOVA, regression); consult statistician for complex analyses
4. **Reporting Standards**: WHO Guidelines for Water Quality Monitoring (reference)

---

**Document Prepared For**: Developers, Data Engineers, Analysts  
**Classification**: Internal / Restricted  
**Date**: May 18, 2024  
**Version**: 1.0
