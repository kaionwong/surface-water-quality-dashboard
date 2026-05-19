"""
Data Loader Module
Handles loading and caching CSV files with proper datetime parsing.
"""

import streamlit as st
import pandas as pd
from pathlib import Path


_THIS_DIR = Path(__file__).resolve().parent
_STREAMLIT_APP_DIR = _THIS_DIR.parent
_REPO_ROOT = _STREAMLIT_APP_DIR.parent


def _resolve_existing_path(relative_candidates):
    """Return the first existing path from repo-root-relative candidates."""
    checked = []
    for rel_path in relative_candidates:
        candidate = _REPO_ROOT / rel_path
        checked.append(str(candidate))
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not find expected dataset file. Checked paths:\n"
        + "\n".join(checked)
        + "\n\nIf deploying to Streamlit Cloud, ensure the CSV is committed to the repo."
    )


@st.cache_data
def load_version_a():
    """
    Load Version A (Strict) - excludes SUS and SUS-combined codes.
    246,052 records with highest data quality.
    """
    path = _resolve_existing_path([
        "output/dataset_version_a_strict.csv",
        "streamlit_app/output/dataset_version_a_strict.csv",
    ])
    df = pd.read_csv(path)
    df['SampleDateTime'] = pd.to_datetime(df['SampleDateTime'])
    return df


@st.cache_data
def load_version_b():
    """
    Load Version B (Balanced) - excludes SUS-combined codes, includes other acceptable flags.
    246,052 records with balanced quality filtering.
    """
    path = _resolve_existing_path([
        "output/dataset_version_b_balanced.csv",
        "streamlit_app/output/dataset_version_b_balanced.csv",
    ])
    df = pd.read_csv(path)
    df['SampleDateTime'] = pd.to_datetime(df['SampleDateTime'])
    return df


@st.cache_data
def load_version_c():
    """
    Load Version C (Full) - all records with quality indicators.
    247,121 records suitable for exploratory analysis.
    """
    path = _resolve_existing_path([
        "output/dataset_version_c_full.csv",
        "streamlit_app/output/dataset_version_c_full.csv",
        "data/raw/alberta_surface_water_quality_data.csv",
    ])
    df = pd.read_csv(path)
    df['SampleDateTime'] = pd.to_datetime(df['SampleDateTime'])
    return df


def load_data(version='C'):
    """
    Load data by version selection.
    
    Args:
        version (str): 'A' (Strict), 'B' (Balanced), or 'C' (Full)
        
    Returns:
        pd.DataFrame: Loaded and preprocessed dataframe
    """
    version = version.upper()
    if version == 'A':
        return load_version_a()
    elif version == 'B':
        return load_version_b()
    elif version == 'C':
        return load_version_c()
    else:
        raise ValueError(f"Invalid version '{version}'. Must be 'A', 'B', or 'C'")


def get_data_info(df):
    """
    Get basic info about loaded dataset.
    
    Args:
        df (pd.DataFrame): Dataframe to analyze
        
    Returns:
        dict: Summary statistics
    """
    return {
        'shape': df.shape,
        'records': len(df),
        'date_min': df['SampleDateTime'].min(),
        'date_max': df['SampleDateTime'].max(),
        'stations': df['StationNumber'].nunique(),
        'parameters': df['VmvCode'].nunique(),
        'qualifiers': df['MeasurementQualifier'].nunique(),
        'memory_mb': df.memory_usage(deep=True).sum() / 1024 ** 2
    }
