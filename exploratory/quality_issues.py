"""
Quality Issues Detection Module

Identifies and flags data quality issues including:
- Invalid values (outside parameter constraints)
- Outliers (statistical anomalies)
- Consistency violations (duplicates, contradictions)
- Range violations
- Suspicious patterns
"""

import pandas as pd
import numpy as np
import plotly.express as px
from .config import ALBERTA_DATA_FILE, PARAMETER_CONSTRAINTS, EXPECTED_COLUMNS
from .utils import (
    load_data_chunked,
    flag_outliers,
    identify_numeric_columns,
    save_outputs,
)


def check_validity_constraints(df):
    """
    Check values against known parameter constraints.
    
    Returns list of validity issues.
    """
    validity_issues = []
    
    # Identify parameter and value columns
    param_col = None
    value_col = None
    
    for col in df.columns:
        if any(name.lower() in col.lower() for name in EXPECTED_COLUMNS['parameter']):
            param_col = col
        if any(name.lower() in col.lower() for name in EXPECTED_COLUMNS['value']):
            value_col = col
    
    if not param_col or not value_col:
        return validity_issues
    
    # Check each parameter's constraints
    for param, constraints in PARAMETER_CONSTRAINTS.items():
        param_data = df[df[param_col].str.lower().str.contains(param.lower(), na=False)]
        
        if len(param_data) == 0:
            continue
        
        # Convert values to numeric (coerce errors to NaN)
        values = pd.to_numeric(param_data[value_col], errors='coerce')
        
        # Skip if all values are NaN or not numeric
        if values.isna().all():
            continue
        
        # Check min constraint
        try:
            below_min = values < constraints['min']
            if below_min.sum() > 0:
                validity_issues.append({
                    'parameter': param,
                    'issue_type': 'below_minimum',
                    'constraint': f"Min: {constraints['min']}",
                    'count': int(below_min.sum()),
                    'percent': float(below_min.sum() / len(param_data) * 100),
                })
        except (TypeError, KeyError):
            pass
        
        # Check max constraint
        try:
            above_max = values > constraints['max']
            if above_max.sum() > 0:
                validity_issues.append({
                    'parameter': param,
                    'issue_type': 'above_maximum',
                    'constraint': f"Max: {constraints['max']}",
                    'count': int(above_max.sum()),
                    'percent': float(above_max.sum() / len(param_data) * 100),
                })
        except (TypeError, KeyError):
            pass
        
        # Check recommended range
        try:
            if 'recommended_min' in constraints:
                below_rec = (values < constraints['recommended_min']) & (values >= constraints['min'])
                if below_rec.sum() > 0:
                    validity_issues.append({
                        'parameter': param,
                        'issue_type': 'below_recommended',
                        'constraint': f"Recommended Min: {constraints['recommended_min']}",
                        'count': int(below_rec.sum()),
                        'percent': float(below_rec.sum() / len(param_data) * 100),
                    })
        except (TypeError, KeyError):
            pass
    
    return validity_issues


def detect_outliers_all(df):
    """
    Detect outliers across all numeric columns using multiple methods.
    """
    numeric_cols = identify_numeric_columns(df)
    
    outlier_summary = []
    
    for col in numeric_cols:
        # Skip if too many nulls
        if df[col].isnull().sum() / len(df) > 0.5:
            continue
        
        methods = ['zscore', 'iqr']
        for method in methods:
            outliers = flag_outliers(df[col], method=method)
            outlier_count = outliers.sum()
            
            if outlier_count > 0:
                outlier_summary.append({
                    'column': col,
                    'method': method,
                    'outlier_count': int(outlier_count),
                    'outlier_percent': float(outlier_count / len(df[col].dropna()) * 100),
                })
    
    return pd.DataFrame(outlier_summary) if outlier_summary else pd.DataFrame()


def check_duplicate_records(df):
    """
    Identify duplicate or near-duplicate records.
    
    Returns duplicate detection summary.
    """
    # Exact duplicates
    exact_duplicates = len(df[df.duplicated(keep=False)])
    
    # Partial duplicates (by key columns)
    station_col = None
    date_col = None
    param_col = None
    
    for col in df.columns:
        if any(name.lower() in col.lower() for name in EXPECTED_COLUMNS['station_id']):
            station_col = col
        if any(name.lower() in col.lower() for name in EXPECTED_COLUMNS['date_time']):
            date_col = col
        if any(name.lower() in col.lower() for name in EXPECTED_COLUMNS['parameter']):
            param_col = col
    
    duplicate_summary = {
        'exact_duplicates': int(exact_duplicates),
    }
    
    # Check for duplicate station-date-parameter combinations
    if station_col and date_col and param_col:
        key_cols = [station_col, date_col, param_col]
        key_duplicates = df.duplicated(subset=key_cols, keep=False)
        duplicate_summary['key_column_duplicates'] = int(key_duplicates.sum())
    
    return duplicate_summary


def check_suspicion_patterns(df):
    """
    Detect suspicious patterns that might indicate data quality issues.
    """
    suspicious = []
    
    # Check for repeated values (all same value)
    for col in df.select_dtypes(include=[np.number]).columns:
        unique_values = df[col].nunique()
        total_values = len(df[col].dropna())
        
        if unique_values == 0:
            suspicious.append({
                'column': col,
                'pattern': 'all_missing',
            })
        elif unique_values == 1 and total_values > 10:
            suspicious.append({
                'column': col,
                'pattern': 'all_identical_value',
                'value': float(df[col].dropna().iloc[0]),
                'count': int(total_values),
            })
    
    # Check for suspiciously round numbers (potential defaults/placeholders)
    for col in df.select_dtypes(include=[np.number]).columns:
        values = df[col].dropna()
        if len(values) > 0:
            round_values = (values % 1 == 0).sum()
            if len(values) > 100:
                pct_round = round_values / len(values) * 100
                if pct_round > 80:
                    suspicious.append({
                        'column': col,
                        'pattern': 'suspiciously_round',
                        'percent_round': float(pct_round),
                    })
    
    return suspicious


def main(nrows=None):
    """
    Execute quality issues detection.
    
    Parameters
    ----------
    nrows : int, optional
        Limit rows for testing
    
    Returns
    -------
    dict
        Results containing quality issue detections
    """
    print("\n" + "="*60)
    print("DATA QUALITY ISSUES DETECTION")
    print("="*60)
    
    # Load data
    print("\nLoading data...")
    df = load_data_chunked(ALBERTA_DATA_FILE, nrows=nrows)
    
    # Validity constraints
    print("\nChecking validity constraints...")
    validity_issues = check_validity_constraints(df)
    validity_df = pd.DataFrame(validity_issues) if validity_issues else pd.DataFrame()
    
    if not validity_df.empty:
        print(f"Found {len(validity_df)} validity constraint violations")
    else:
        print("No constraint violations detected")
    
    # Outlier detection
    print("\nDetecting outliers...")
    outlier_df = detect_outliers_all(df)
    
    if not outlier_df.empty:
        print(f"Found {len(outlier_df)} outlier detection results")
        print(outlier_df[['column', 'method', 'outlier_count']])
    
    # Duplicate detection
    print("\nChecking for duplicates...")
    duplicates = check_duplicate_records(df)
    print(f"Exact duplicates: {duplicates['exact_duplicates']}")
    if 'key_column_duplicates' in duplicates:
        print(f"Key column duplicates: {duplicates['key_column_duplicates']}")
    
    # Suspicious patterns
    print("\nAnalyzing suspicious patterns...")
    suspicious = check_suspicion_patterns(df)
    
    if suspicious:
        print(f"Found {len(suspicious)} suspicious patterns")
    
    # Results
    results = {
        "validity_issues": validity_df,
        "outlier_detections": outlier_df,
        "duplicates": duplicates,
        "suspicious_patterns": suspicious,
        "dataframe": df,
    }
    
    # Save outputs
    print("\nSaving outputs...")
    save_outputs(
        dataframes_dict={
            "validity_issues": validity_df,
            "outlier_detections": outlier_df,
        },
        json_dict={
            "duplicates": duplicates,
            "suspicious_patterns": suspicious,
        },
        prefix="quality_issues_"
    )
    
    print("\n[OK] Quality issues detection complete!")
    
    return results


if __name__ == "__main__":
    results = main()
