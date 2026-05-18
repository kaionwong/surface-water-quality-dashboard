"""Utility functions for exploratory data analysis."""

import os
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Lazy import scipy to avoid import issues
def _import_scipy_stats():
    try:
        from scipy import stats
        return stats
    except ImportError:
        print("Warning: scipy not available, some features disabled")
        return None

# Try to import sklearn, but make it optional
try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from .config import (
    DATA_RAW_PATH,
    OUTPUT_EDA_PATH,
    OUTPUT_STATS_PATH,
    CHUNK_SIZE,
    OUTLIER_DETECTION,
)


def load_data_chunked(filename, chunk_size=CHUNK_SIZE, nrows=None):
    """
    Load large CSV file in chunks to manage memory efficiently.
    
    Parameters
    ----------
    filename : str
        Name of the CSV file in data/raw/
    chunk_size : int
        Number of rows per chunk (default: 50000)
    nrows : int, optional
        Total rows to read (for testing)
    
    Returns
    -------
    pd.DataFrame
        Complete dataframe loaded from chunks
    """
    filepath = os.path.join(DATA_RAW_PATH, filename)
    
    if nrows:
        return pd.read_csv(filepath, nrows=nrows)
    
    chunks = []
    for chunk in pd.read_csv(filepath, chunksize=chunk_size):
        chunks.append(chunk)
    
    df = pd.concat(chunks, ignore_index=True)
    print(f"Loaded {len(df):,} rows from {filename}")
    return df


def plot_missing_heatmap(df, dimension="columns", title="Missing Data Overview"):
    """
    Create interactive heatmap of missing data.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe
    dimension : str
        'columns' for column-wise, 'station-parameter' for 2D heatmap
    title : str
        Plot title
    
    Returns
    -------
    plotly.graph_objects.Figure
        Interactive heatmap
    """
    if dimension == "columns":
        missing_pct = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
        fig = px.bar(x=missing_pct.values, y=missing_pct.index, 
                     title=title,
                     labels={"x": "Missing %", "y": "Column"},
                     orientation="h")
    
    return fig


def statistical_summary(series, name=""):
    """
    Compute statistical summary for a numeric column.
    
    Parameters
    ----------
    series : pd.Series
        Numeric series
    name : str
        Series name for reporting
    
    Returns
    -------
    dict
        Summary statistics
    """
    stats = _import_scipy_stats()
    clean_data = series.dropna()
    
    if len(clean_data) == 0:
        return {"name": name, "error": "No valid data"}
    
    summary = {
        "name": name,
        "count": len(clean_data),
        "missing": series.isnull().sum(),
        "missing_pct": series.isnull().sum() / len(series) * 100,
        "mean": clean_data.mean(),
        "median": clean_data.median(),
        "std": clean_data.std(),
        "min": clean_data.min(),
        "25%": clean_data.quantile(0.25),
        "75%": clean_data.quantile(0.75),
        "max": clean_data.max(),
        "skewness": stats.skew(clean_data) if stats else None,
        "kurtosis": stats.kurtosis(clean_data) if stats else None,
    }
    
    return summary


def flag_outliers(series, method="zscore"):
    """
    Detect outliers in a numeric series using multiple methods.
    
    Parameters
    ----------
    series : pd.Series
        Numeric series
    method : str
        'zscore', 'iqr', or 'isolation_forest'
    
    Returns
    -------
    pd.Series
        Boolean series with True for outliers
    """
    stats = _import_scipy_stats()
    clean_data = series.dropna()
    
    if len(clean_data) < 3:
        return pd.Series(False, index=series.index)
    
    outliers = pd.Series(False, index=series.index)
    
    if method == "zscore":
        if not stats:
            return outliers  # Can't compute without scipy
        z_scores = np.abs(stats.zscore(clean_data))
        outlier_indices = clean_data[z_scores > OUTLIER_DETECTION["z_score_threshold"]].index
        outliers[outlier_indices] = True
        
    elif method == "iqr":
        Q1 = clean_data.quantile(0.25)
        Q3 = clean_data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - OUTLIER_DETECTION["iqr_multiplier"] * IQR
        upper_bound = Q3 + OUTLIER_DETECTION["iqr_multiplier"] * IQR
        outlier_indices = clean_data[(clean_data < lower_bound) | (clean_data > upper_bound)].index
        outliers[outlier_indices] = True
        
    elif method == "isolation_forest":
        if SKLEARN_AVAILABLE and len(clean_data) > 10:
            iso_forest = IsolationForest(
                contamination=OUTLIER_DETECTION["isolation_forest_contamination"],
                random_state=42
            )
            predictions = iso_forest.fit_predict(clean_data.values.reshape(-1, 1))
            outlier_indices = clean_data[predictions == -1].index
            outliers[outlier_indices] = True
        else:
            # Fallback to IQR if sklearn not available
            return flag_outliers(series, method="iqr")
    
    return outliers


def save_outputs(dataframes_dict, figures_dict=None, json_dict=None, prefix=""):
    """
    Save analysis outputs to CSV, HTML, and JSON files.
    
    Parameters
    ----------
    dataframes_dict : dict
        {filename: dataframe} pairs for CSV export
    figures_dict : dict, optional
        {filename: plotly.Figure} pairs for HTML export
    json_dict : dict, optional
        {filename: dict} pairs for JSON export
    prefix : str, optional
        Prefix for output files
    """
    # Save DataFrames to CSV
    if dataframes_dict:
        for name, df in dataframes_dict.items():
            if isinstance(df, pd.DataFrame):
                filepath = os.path.join(OUTPUT_EDA_PATH, f"{prefix}{name}.csv")
                df.to_csv(filepath, index=False)
                print(f"Saved: {filepath}")
    
    # Save Figures to HTML
    if figures_dict:
        for name, fig in figures_dict.items():
            if hasattr(fig, 'write_html'):
                filepath = os.path.join(OUTPUT_EDA_PATH, f"{prefix}{name}.html")
                fig.write_html(filepath)
                print(f"Saved: {filepath}")
    
    # Save JSON
    if json_dict:
        for name, data in json_dict.items():
            filepath = os.path.join(OUTPUT_EDA_PATH, f"{prefix}{name}.json")
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"Saved: {filepath}")


def standardize_column_names(df, name_map_dict):
    """
    Standardize column names using a mapping dictionary.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe
    name_map_dict : dict
        {standard_name: [possible_names]} mapping
    
    Returns
    -------
    pd.DataFrame
        Dataframe with standardized columns
    """
    rename_dict = {}
    
    for standard_name, possible_names in name_map_dict.items():
        for col in df.columns:
            if col.lower() in [n.lower() for n in possible_names]:
                rename_dict[col] = standard_name
                break
    
    return df.rename(columns=rename_dict)


def identify_numeric_columns(df):
    """Identify numeric columns in dataframe."""
    return df.select_dtypes(include=[np.number]).columns.tolist()


def identify_categorical_columns(df):
    """Identify categorical columns in dataframe."""
    return df.select_dtypes(include=['object']).columns.tolist()
