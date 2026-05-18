"""
Missing Data Analysis Module

Analyzes patterns of missing data across:
- Overall missingness by column
- Missingness by station and parameter
- Time-series gaps
- Correlation between missing values
- Missing data mechanisms (MCAR, MAR, MNAR inference)
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from .config import ALBERTA_DATA_FILE, EXPECTED_COLUMNS
from .utils import (
    load_data_chunked,
    plot_missing_heatmap,
    save_outputs,
)


def analyze_missing_overall(df):
    """Analyze overall missing data by column."""
    
    missing_analysis = pd.DataFrame({
        'column': df.columns,
        'missing_count': df.isnull().sum().values,
        'missing_percent': (df.isnull().sum() / len(df) * 100).values,
        'data_type': df.dtypes.astype(str).values,
    }).sort_values('missing_percent', ascending=False)
    
    return missing_analysis


def analyze_missing_by_station(df):
    """Analyze missing data patterns by station."""
    
    # Identify station column
    station_col = None
    for col in df.columns:
        if any(name.lower() in col.lower() for name in EXPECTED_COLUMNS['station_id']):
            station_col = col
            break
    
    if not station_col:
        return None
    
    station_missing = df.groupby(station_col).apply(
        lambda x: (x.isnull().sum() / len(x) * 100)
    ).mean(axis=0).sort_values(ascending=False)
    
    return station_missing


def analyze_missing_patterns(df):
    """Identify patterns in missing data (correlations between nulls)."""
    
    # Create boolean matrix of missing values
    missing_mask = df.isnull().astype(int)
    
    # Compute correlation of missingness
    missing_corr = missing_mask.corr()
    
    return missing_corr


def plot_missing_distribution(df):
    """Create visualization of missing data distribution."""
    
    missing_pct = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
    
    fig = px.bar(
        x=missing_pct.values,
        y=missing_pct.index,
        title="Missing Data by Column (%)",
        labels={"x": "Missing Percentage (%)", "y": "Column"},
        orientation="h",
    )
    
    fig.update_layout(
        height=max(400, len(df.columns) * 20),
        showlegend=False,
    )
    
    return fig


def infer_missing_mechanism(df):
    """
    Attempt to infer missing data mechanism (MCAR, MAR, MNAR).
    
    Returns inference matrix and summary.
    """
    
    mechanism_summary = {
        "MCAR_candidates": [],  # Columns with random missingness
        "MAR_candidates": [],   # Missingness dependent on other columns
        "MNAR_candidates": [],  # Missingness dependent on own values
    }
    
    for col in df.columns:
        missing_rate = df[col].isnull().sum() / len(df)
        
        if missing_rate == 0:
            continue
        
        # Check correlation with other missing columns
        other_corr = []
        for other_col in df.columns:
            if col != other_col and df[other_col].isnull().sum() > 0:
                corr = df[col].isnull().astype(int).corr(df[other_col].isnull().astype(int))
                if abs(corr) > 0.1:
                    other_corr.append((other_col, corr))
        
        if other_corr:
            mechanism_summary["MAR_candidates"].append({
                "column": col,
                "missing_rate": missing_rate,
                "correlated_with": other_corr,
            })
        else:
            mechanism_summary["MCAR_candidates"].append({
                "column": col,
                "missing_rate": missing_rate,
            })
    
    return mechanism_summary


def main(nrows=None):
    """
    Execute missing data analysis.
    
    Parameters
    ----------
    nrows : int, optional
        Limit rows for testing
    
    Returns
    -------
    dict
        Results containing missing data analysis
    """
    print("\n" + "="*60)
    print("MISSING DATA ANALYSIS")
    print("="*60)
    
    # Load data
    print("\nLoading data...")
    df = load_data_chunked(ALBERTA_DATA_FILE, nrows=nrows)
    
    # Overall missing analysis
    print("\nAnalyzing overall missingness...")
    missing_overall = analyze_missing_overall(df)
    print(missing_overall.head(10))
    
    # By station analysis
    print("\nAnalyzing missingness by station...")
    missing_by_station = analyze_missing_by_station(df)
    
    if missing_by_station is not None:
        print(missing_by_station.head(10))
    
    # Missing patterns
    print("\nAnalyzing missing data patterns...")
    missing_patterns = analyze_missing_patterns(df)
    
    # Infer mechanism
    print("\nInferring missing data mechanism...")
    mechanism = infer_missing_mechanism(df)
    
    # Create visualizations
    print("\nGenerating visualizations...")
    fig_missing_dist = plot_missing_distribution(df)
    
    # Results
    results = {
        "missing_overall": missing_overall,
        "missing_by_station": missing_by_station,
        "missing_patterns": missing_patterns,
        "mechanism_inference": mechanism,
        "dataframe": df,
    }
    
    # Save outputs
    print("\nSaving outputs...")
    save_outputs(
        dataframes_dict={
            "missing_overall": missing_overall,
        },
        figures_dict={
            "missing_distribution": fig_missing_dist,
        },
        json_dict={
            "mechanism_inference": mechanism,
        },
        prefix="missing_data_"
    )
    
    print("\n[OK] Missing data analysis complete!")
    
    return results


if __name__ == "__main__":
    results = main()
