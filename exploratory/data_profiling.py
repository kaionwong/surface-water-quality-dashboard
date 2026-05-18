"""
Data Profiling Module

Comprehensive dataset profiling covering:
- Row/column counts
- Data types
- Memory usage
- Duplicate records
- Basic statistical summaries
- Column-level completeness
"""

import pandas as pd
from .config import ALBERTA_DATA_FILE
from .utils import (
    load_data_chunked,
    statistical_summary,
    identify_numeric_columns,
    identify_categorical_columns,
    save_outputs,
)


def profile_dataset(df):
    """Generate comprehensive dataset profile."""
    
    profile = {
        "dataset_shape": {"rows": len(df), "columns": len(df.columns)},
        "total_cells": len(df) * len(df.columns),
        "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024**2,
        "duplicate_rows": len(df[df.duplicated(keep=False)]),
        "dtypes": df.dtypes.astype(str).to_dict(),
    }
    
    return profile


def analyze_columns(df):
    """Analyze all columns for completeness and type."""
    
    column_analysis = []
    
    for col in df.columns:
        col_info = {
            "column": col,
            "dtype": str(df[col].dtype),
            "non_null_count": df[col].notna().sum(),
            "null_count": df[col].isnull().sum(),
            "null_percent": df[col].isnull().sum() / len(df) * 100,
            "unique_values": df[col].nunique(),
            "duplicate_values": len(df) - df[col].nunique(),
        }
        
        # Add numeric-specific stats
        if df[col].dtype in ['int64', 'float64']:
            col_info.update({
                "min": df[col].min(),
                "max": df[col].max(),
                "mean": df[col].mean(),
                "median": df[col].median(),
                "std": df[col].std(),
            })
        
        # Add categorical-specific info
        if df[col].dtype == 'object':
            top_values = df[col].value_counts().head(5)
            col_info["top_5_values"] = top_values.to_dict()
        
        column_analysis.append(col_info)
    
    return pd.DataFrame(column_analysis)


def main(nrows=None):
    """
    Execute data profiling analysis.
    
    Parameters
    ----------
    nrows : int, optional
        Limit rows for testing
    
    Returns
    -------
    dict
        Results containing profiles and summaries
    """
    print("\n" + "="*60)
    print("DATA PROFILING ANALYSIS")
    print("="*60)
    
    # Load data
    print("\nLoading data...")
    df = load_data_chunked(ALBERTA_DATA_FILE, nrows=nrows)
    
    # Overall dataset profile
    print("\nGenerating dataset profile...")
    dataset_profile = profile_dataset(df)
    
    print(f"\nDataset Overview:")
    print(f"  Shape: {dataset_profile['dataset_shape']['rows']:,} rows × {dataset_profile['dataset_shape']['columns']} columns")
    print(f"  Memory: {dataset_profile['memory_usage_mb']:.2f} MB")
    print(f"  Duplicates: {dataset_profile['duplicate_rows']}")
    
    # Column analysis
    print("\nAnalyzing columns...")
    column_stats = analyze_columns(df)
    
    # Numeric and categorical summaries
    numeric_cols = identify_numeric_columns(df)
    categorical_cols = identify_categorical_columns(df)
    
    print(f"  Numeric columns: {len(numeric_cols)}")
    print(f"  Categorical columns: {len(categorical_cols)}")
    
    # Detailed statistics for numeric columns
    print("\nComputing numeric column statistics...")
    numeric_summaries = []
    for col in numeric_cols:
        summary = statistical_summary(df[col], name=col)
        numeric_summaries.append(summary)
    
    numeric_summary_df = pd.DataFrame(numeric_summaries)
    
    # Results dictionary
    results = {
        "dataset_profile": dataset_profile,
        "column_analysis": column_stats,
        "numeric_summaries": numeric_summary_df,
        "dataframe": df,
    }
    
    # Save outputs
    print("\nSaving outputs...")
    save_outputs(
        dataframes_dict={
            "column_analysis": column_stats,
            "numeric_summaries": numeric_summary_df,
        },
        prefix="data_profiling_"
    )
    
    print("\n[OK] Data profiling analysis complete!")
    
    return results


if __name__ == "__main__":
    results = main()
