"""
Data Processor Module
Handles filtering, aggregation, and quality classification.
"""

import pandas as pd
import numpy as np
import streamlit as st


# Qualifier categorization (from data_quality_analysis.md)
QUALIFIER_CATEGORIES = {
    'Clean': [None, '', 'nan'],
    'Suspect': ['SUS', 'RER|SUS', 'HT|RER|SUS', 'HT|SUS'],
    'Acceptable': ['HT', 'DR', 'SPNF', 'OBS', 'FSE', 'RER', 'EST']
}

# Codes to always exclude (suspect data)
ALWAYS_EXCLUDE = ['SUS', 'RER|SUS', 'HT|RER|SUS', 'HT|SUS']

# Codes to include but flag (acceptable with caveats)
ACCEPTABLE_FLAGS = ['HT', 'DR', 'SPNF', 'OBS', 'FSE', 'RER', 'EST']

# Quality filter tiers for dashboard controls
DEFINITELY_UNRELIABLE_CODES = {'SUS', 'RER|SUS', 'HT|RER|SUS', 'HT|SUS', 'DR|SUS'}
SOMEWHAT_UNRELIABLE_CODES = {'HT', 'HT|RER', 'FSE|HT', 'DR|HT', 'DR', 'DR|FSE', 'DR|SPNF', 'SPNF'}


@st.cache_data
def build_vmvcode_mapping(df):
    """
    Build a mapping of VmvCode → VariableName for human-readable display.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        dict: {VmvCode: VariableName}
    """
    if 'VariableName' in df.columns:
        mapping = df.drop_duplicates('VmvCode')[['VmvCode', 'VariableName']].set_index('VmvCode')['VariableName'].to_dict()
        return mapping
    else:
        # Fallback: if VariableName not available, return VmvCode as-is
        return {code: str(code) for code in df['VmvCode'].unique()}


def format_vmvcode_display(vmvcode, vmvcode_mapping=None):
    """
    Format VmvCode for display with VariableName.
    
    Args:
        vmvcode: VmvCode value
        vmvcode_mapping (dict): Mapping of VmvCode to VariableName
        
    Returns:
        str: Formatted string "VmvCode - VariableName" or just VmvCode
    """
    if vmvcode_mapping and vmvcode in vmvcode_mapping:
        return f"{vmvcode} - {vmvcode_mapping[vmvcode]}"
    return str(vmvcode)


def get_vmvcode_list_with_descriptions(df, vmvcode_list=None):
    """
    Get list of VmvCodes with descriptions for dropdown/multiselect display.
    
    Args:
        df (pd.DataFrame): Input dataframe
        vmvcode_list (list): List of VmvCodes to format (default: all unique)
        
    Returns:
        list: List of formatted "VmvCode - VariableName" strings
    """
    mapping = build_vmvcode_mapping(df)
    
    if vmvcode_list is None:
        vmvcode_list = sorted(df['VmvCode'].unique())
    
    return [format_vmvcode_display(code, mapping) for code in vmvcode_list]


def extract_vmvcode_from_display(display_string):
    """
    Extract VmvCode from display string "VmvCode - VariableName".
    
    Args:
        display_string (str): Formatted string like "2004 - RESIDUE FILTERABLE"
        
    Returns:
        str: VmvCode value (e.g., "2004")
    """
    if ' - ' in str(display_string):
        return str(display_string).split(' - ')[0].strip()
    return str(display_string)


def classify_qualifier(qual):
    """
    Classify measurement quality based on qualifier code.
    
    Args:
        qual: Qualifier code (string or NaN)
        
    Returns:
        str: Quality class ('Clean', 'Suspect', 'Acceptable', 'Other')
    """
    if pd.isna(qual) or qual == '' or qual == 'nan':
        return 'Clean'
    if qual in ALWAYS_EXCLUDE:
        return 'Suspect'
    if qual in ACCEPTABLE_FLAGS:
        return 'Acceptable'
    return 'Other'


def filter_by_date_range(df, start_date, end_date):
    """
    Filter dataframe by date range.
    
    Args:
        df (pd.DataFrame): Input dataframe
        start_date: Start date (datetime or date object)
        end_date: End date (datetime or date object)
        
    Returns:
        pd.DataFrame: Filtered dataframe
    """
    return df[(df['SampleDateTime'].dt.date >= start_date) & 
              (df['SampleDateTime'].dt.date <= end_date)]


def filter_by_stations(df, stations):
    """
    Filter dataframe by station numbers.
    
    Args:
        df (pd.DataFrame): Input dataframe
        stations (list): List of station numbers to include
        
    Returns:
        pd.DataFrame: Filtered dataframe
    """
    if not stations or len(stations) == 0:
        return df
    return df[df['StationNumber'].isin(stations)]


def filter_by_parameters(df, parameters):
    """
    Filter dataframe by VmvCode (parameter codes).
    
    Args:
        df (pd.DataFrame): Input dataframe
        parameters (list): List of parameter codes to include
        
    Returns:
        pd.DataFrame: Filtered dataframe
    """
    if not parameters or len(parameters) == 0:
        return df
    return df[df['VmvCode'].isin(parameters)]


def get_quality_metrics(df):
    """
    Calculate key quality metrics for dataset.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        dict: Quality metrics
    """
    total = len(df)
    if total == 0:
        return {
            'total_records': 0,
            'clean_records': 0,
            'pct_clean': 0,
            'flagged_records': 0,
            'pct_flagged': 0
        }
    
    clean = (df['MeasurementQualifier'].isna() | (df['MeasurementQualifier'] == '')).sum()
    flagged = total - clean
    
    return {
        'total_records': total,
        'clean_records': clean,
        'pct_clean': (clean / total * 100) if total > 0 else 0,
        'flagged_records': flagged,
        'pct_flagged': (flagged / total * 100) if total > 0 else 0
    }


def get_top_stations(df, n=15):
    """
    Get top N stations by record count.
    
    Args:
        df (pd.DataFrame): Input dataframe
        n (int): Number of top stations to return
        
    Returns:
        pd.DataFrame: Top stations with counts
    """
    return df['StationNumber'].value_counts().head(n)


def get_top_parameters(df, n=15):
    """
    Get top N parameters by measurement count.
    
    Args:
        df (pd.DataFrame): Input dataframe
        n (int): Number of top parameters to return
        
    Returns:
        pd.Series: Top parameters with counts
    """
    return df['VmvCode'].value_counts().head(n)


def get_qualifier_distribution(df):
    """
    Get distribution of all qualifier codes.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Qualifier distribution with counts and percentages
    """
    dist = df['MeasurementQualifier'].value_counts(dropna=False).reset_index()
    dist.columns = ['Qualifier', 'Count']
    dist['Percentage'] = (dist['Count'] / len(df) * 100).round(3)
    dist['Cumulative %'] = dist['Percentage'].cumsum().round(3)
    
    # Replace NaN with descriptive label
    dist['Qualifier'] = dist['Qualifier'].fillna('(Clean/No Flag)')
    
    return dist


def quality_by_station(df):
    """
    Calculate quality metrics by station.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Quality metrics indexed by StationNumber
    """
    def calc_quality(x):
        total = len(x)
        clean = (x['MeasurementQualifier'].isna() | (x['MeasurementQualifier'] == '')).sum()
        return {
            'total': total,
            'clean': clean,
            'pct_clean': (clean / total * 100) if total > 0 else 0,
            'flagged': total - clean,
            'pct_flagged': ((total - clean) / total * 100) if total > 0 else 0
        }
    
    grouped = df.groupby('StationNumber').apply(calc_quality).apply(pd.Series)
    return grouped.sort_values('pct_clean')


def quality_by_year(df):
    """
    Calculate quality metrics by year.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Quality metrics indexed by Year
    """
    df_temp = df.copy()
    df_temp['Year'] = df_temp['SampleDateTime'].dt.year
    
    def calc_quality(x):
        total = len(x)
        clean = (x['MeasurementQualifier'].isna() | (x['MeasurementQualifier'] == '')).sum()
        return {
            'total': total,
            'clean': clean,
            'pct_clean': (clean / total * 100) if total > 0 else 0,
            'flagged': total - clean,
            'pct_flagged': ((total - clean) / total * 100) if total > 0 else 0
        }
    
    grouped = df_temp.groupby('Year').apply(calc_quality).apply(pd.Series)
    return grouped


def station_qualifier_matrix(df):
    """
    Create heatmap-ready matrix: Station × Qualifier.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Crosstab of stations vs qualifiers
    """
    return pd.crosstab(df['StationNumber'], df['MeasurementQualifier'], margins=False)


def quality_by_parameter(df):
    """
    Calculate quality metrics by parameter (VmvCode).
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Quality metrics by parameter
    """
    def calc_quality(x):
        total = len(x)
        clean = (x['MeasurementQualifier'].isna() | (x['MeasurementQualifier'] == '')).sum()
        return {
            'total': total,
            'clean': clean,
            'pct_clean': (clean / total * 100) if total > 0 else 0,
            'flagged': total - clean,
            'pct_flagged': ((total - clean) / total * 100) if total > 0 else 0
        }
    
    grouped = df.groupby('VmvCode').apply(calc_quality).apply(pd.Series)
    return grouped.sort_values('pct_flagged', ascending=False)


def get_suspicious_records(df):
    """
    Extract records with suspect qualifiers (SUS variants).
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Records with suspect qualifiers
    """
    return df[df['MeasurementQualifier'].isin(ALWAYS_EXCLUDE)]


def add_temporal_features(df):
    """
    Add temporal feature columns to dataframe.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Dataframe with temporal features
    """
    df = df.copy()
    df['Year'] = df['SampleDateTime'].dt.year
    df['Month'] = df['SampleDateTime'].dt.month
    df['YearMonth'] = df['SampleDateTime'].dt.to_period('M')
    df['Quarter'] = df['SampleDateTime'].dt.quarter
    df['DayOfYear'] = df['SampleDateTime'].dt.dayofyear
    return df


@st.cache_data
def build_variable_key_mapping(df):
    """
    Build a mapping of VmvCode -> "VariableName (VmvCode-VariableCode)".

    Falls back safely when VariableCode or VariableName is missing.
    """
    required_cols = ['VmvCode']
    if not all(col in df.columns for col in required_cols):
        return {}

    unique_rows = df.drop_duplicates('VmvCode').copy()
    mapping = {}

    for _, row in unique_rows.iterrows():
        vmv = row['VmvCode']
        var_code = row['VariableCode'] if 'VariableCode' in unique_rows.columns else None
        var_name = row['VariableName'] if 'VariableName' in unique_rows.columns else None

        if pd.notna(var_code) and pd.notna(var_name):
            mapping[vmv] = f"{var_name} ({vmv}-{var_code})"
        elif pd.notna(var_name):
            mapping[vmv] = f"{var_name} ({vmv})"
        else:
            mapping[vmv] = str(vmv)

    return mapping


def apply_quality_filter(df, option):
    """
    Apply dashboard quality filtering option.

    option values:
    - 'all': include all rows
    - 'definite': exclude codes that clearly indicate unreliable values
    - 'broader': exclude definite + somewhat unreliable values
    """
    if option == 'all':
        return df.copy()

    qualifier = df['MeasurementQualifier']
    if option == 'definite':
        exclude_codes = DEFINITELY_UNRELIABLE_CODES
    elif option == 'broader':
        exclude_codes = DEFINITELY_UNRELIABLE_CODES.union(SOMEWHAT_UNRELIABLE_CODES)
    else:
        return df.copy()

    mask_keep = qualifier.isna() | (~qualifier.isin(exclude_codes))
    return df[mask_keep].copy()


def get_station_aggregated_values(df):
    """
    Aggregate filtered rows to one numeric value per station for mapping.
    """
    if len(df) == 0:
        return pd.DataFrame(columns=['StationNumber', 'Station', 'LatitudeDecimalDegrees', 'LongitudeDecimalDegrees', 'MeasurementValueNum', 'RecordCount', 'UnitCode'])

    work = df.copy()
    work['MeasurementValueNum'] = pd.to_numeric(work['MeasurementValue'], errors='coerce')
    work = work.dropna(subset=['MeasurementValueNum', 'LatitudeDecimalDegrees', 'LongitudeDecimalDegrees'])

    if len(work) == 0:
        return pd.DataFrame(columns=['StationNumber', 'Station', 'LatitudeDecimalDegrees', 'LongitudeDecimalDegrees', 'MeasurementValueNum', 'RecordCount', 'UnitCode'])

    grouped = work.groupby('StationNumber', as_index=False).agg(
        Station=('Station', 'first'),
        LatitudeDecimalDegrees=('LatitudeDecimalDegrees', 'first'),
        LongitudeDecimalDegrees=('LongitudeDecimalDegrees', 'first'),
        MeasurementValueNum=('MeasurementValueNum', 'mean'),
        RecordCount=('MeasurementValueNum', 'size'),
        UnitCode=('UnitCode', 'first')
    )
    return grouped


def compute_time_series_percentiles(df, period):
    """
    Compute mean, median, 25th, and 75th percentile over time.

    period values: 'W' (weekly), 'M' (monthly), 'Q' (quarterly), 'Y' (yearly), 'seasonal'
    """
    if len(df) == 0:
        return pd.DataFrame(columns=['period_label', 'mean', 'p25', 'p50', 'p75'])

    work = df.copy()
    work['MeasurementValueNum'] = pd.to_numeric(work['MeasurementValue'], errors='coerce')
    work = work.dropna(subset=['MeasurementValueNum'])
    if len(work) == 0:
        return pd.DataFrame(columns=['period_label', 'mean', 'p25', 'p50', 'p75'])

    if period == 'seasonal':
        month = work['SampleDateTime'].dt.month
        work['season'] = np.select(
            [month.isin([12, 1, 2]), month.isin([3, 4, 5]), month.isin([6, 7, 8]), month.isin([9, 10, 11])],
            ['Winter', 'Spring', 'Summer', 'Fall'],
            default='Unknown'
        )
        work['year'] = work['SampleDateTime'].dt.year
        agg = work.groupby(['year', 'season'])['MeasurementValueNum'].agg(
            mean='mean',
            p25=lambda s: s.quantile(0.25),
            p50='median',
            p75=lambda s: s.quantile(0.75)
        ).reset_index()
        season_order = {'Winter': 0, 'Spring': 1, 'Summer': 2, 'Fall': 3}
        agg['season_order'] = agg['season'].map(season_order).fillna(9)
        agg = agg.sort_values(['year', 'season_order'])
        agg['period_label'] = agg['year'].astype(str) + ' ' + agg['season']
        return agg[['period_label', 'mean', 'p25', 'p50', 'p75']]

    period_map = {'W': 'W', 'M': 'M', 'Q': 'Q', 'Y': 'Y'}
    freq = period_map.get(period, 'M')
    work['period'] = work['SampleDateTime'].dt.to_period(freq)

    agg = work.groupby('period')['MeasurementValueNum'].agg(
        mean='mean',
        p25=lambda s: s.quantile(0.25),
        p50='median',
        p75=lambda s: s.quantile(0.75)
    ).reset_index()
    agg['period_label'] = agg['period'].astype(str)
    return agg[['period_label', 'mean', 'p25', 'p50', 'p75']]


def get_statistical_summary(df_filtered, df_pre_filter):
    """
    Compute compact statistical summary for selected variable and filters.
    """
    values = pd.to_numeric(df_filtered['MeasurementValue'], errors='coerce') if 'MeasurementValue' in df_filtered.columns else pd.Series(dtype=float)
    values = values.dropna()

    pre_count = len(df_pre_filter)
    post_count = len(df_filtered)
    pct_removed = ((pre_count - post_count) / pre_count * 100) if pre_count > 0 else 0.0

    if len(values) == 0:
        return {
            'count': 0,
            'mean': None,
            'median': None,
            'std': None,
            'min': None,
            'max': None,
            'pct_removed': pct_removed,
            'stations': df_filtered['StationNumber'].nunique() if 'StationNumber' in df_filtered.columns else 0,
        }

    return {
        'count': int(values.count()),
        'mean': float(values.mean()),
        'median': float(values.median()),
        'std': float(values.std()) if values.count() > 1 else 0.0,
        'min': float(values.min()),
        'max': float(values.max()),
        'pct_removed': pct_removed,
        'stations': df_filtered['StationNumber'].nunique() if 'StationNumber' in df_filtered.columns else 0,
    }
