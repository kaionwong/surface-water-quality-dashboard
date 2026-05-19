"""
Filters Module
Sidebar controls and global filter application.
"""

import streamlit as st
import pandas as pd
from data.data_processor import build_vmvcode_mapping, format_vmvcode_display


def global_sidebar_filters(df):
    """
    Create and manage global sidebar filters.
    
    Args:
        df (pd.DataFrame): Full dataset for filter options
        
    Returns:
        tuple: (date_range, selected_stations, selected_parameters)
    """
    st.sidebar.header("🔍 Global Filters")
    
    # Date range filter
    st.sidebar.subheader("Date Range")
    min_date = df['SampleDateTime'].min().date()
    max_date = df['SampleDateTime'].max().date()
    
    date_range = st.sidebar.date_input(
        "Select date range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date,
        key='global_date_filter'
    )
    
    # Ensure date_range is a tuple with 2 elements
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        date_range = tuple(date_range)
    else:
        date_range = (min_date, max_date)
    
    # Station filter
    st.sidebar.subheader("Stations")
    all_stations = sorted(df['StationNumber'].unique())
    
    select_all_stations = st.sidebar.checkbox("Select all stations", value=True, key='all_stations')
    
    if select_all_stations:
        selected_stations = all_stations
    else:
        selected_stations = st.sidebar.multiselect(
            "Choose stations",
            options=all_stations,
            default=all_stations[:10],
            key='station_filter'
        )
    
    # VmvCode (Water Quality Parameter) filter
    st.sidebar.subheader("VmvCode (Water Quality Parameters)")
    
    # Build VmvCode → VariableName mapping
    vmvcode_mapping = build_vmvcode_mapping(df)
    all_vmvcodes = sorted(df['VmvCode'].unique())
    top_vmvcodes = df['VmvCode'].value_counts().head(20).index.tolist()
    
    # Create a stable display->code lookup so we preserve original dtype (int/str)
    all_display_to_code = {format_vmvcode_display(code, vmvcode_mapping): code for code in all_vmvcodes}
    top_display_to_code = {format_vmvcode_display(code, vmvcode_mapping): code for code in top_vmvcodes}

    all_vmvcode_displays = list(all_display_to_code.keys())
    top_vmvcode_displays = list(top_display_to_code.keys())
    
    vmvcode_mode = st.sidebar.radio(
        "VmvCode selection mode",
        ["Top 20 (default)", "All VmvCodes", "Custom selection"],
        key='vmvcode_mode'
    )
    
    if vmvcode_mode == "Top 20 (default)":
        selected_vmvcode_displays = top_vmvcode_displays
    elif vmvcode_mode == "All VmvCodes":
        selected_vmvcode_displays = all_vmvcode_displays
    else:  # Custom selection
        selected_vmvcode_displays = st.sidebar.multiselect(
            "Choose VmvCodes",
            options=all_vmvcode_displays,
            default=top_vmvcode_displays,
            key='vmvcode_filter'
        )
    
    # Map selected display labels back to original VmvCode values
    selected_vmvcodes = [all_display_to_code.get(display) for display in selected_vmvcode_displays]
    selected_vmvcodes = [code for code in selected_vmvcodes if code is not None]
    
    # Data version selector (for quality page usage)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Data Quality")
    data_version = st.sidebar.radio(
        "Dataset version",
        ["Version A (Strict)", "Version B (Balanced)", "Version C (Full Data)"],
        key='version_selector'
    )
    
    return date_range, selected_stations, selected_vmvcodes, data_version


def apply_global_filters(df, date_range, stations, parameters):
    """
    Apply all global filters to a dataframe.
    
    Args:
        df (pd.DataFrame): Input dataframe
        date_range (tuple): (start_date, end_date)
        stations (list): List of station numbers
        parameters (list): List of parameter codes
        
    Returns:
        pd.DataFrame: Filtered dataframe
    """
    # Apply date filter
    if date_range and len(date_range) == 2:
        df = df[(df['SampleDateTime'].dt.date >= date_range[0]) & 
                (df['SampleDateTime'].dt.date <= date_range[1])]
    
    # Apply station filter
    if stations and len(stations) > 0:
        df = df[df['StationNumber'].isin(stations)]
    
    # Apply parameter filter
    if parameters and len(parameters) > 0:
        df = df[df['VmvCode'].isin(parameters)]
    
    return df


def dataframe_summary_sidebar(df):
    """
    Display dataframe summary in sidebar.
    
    Args:
        df (pd.DataFrame): Filtered dataframe
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Current Data Summary")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        st.metric("Records", f"{len(df):,}")
        st.metric("Stations", df['StationNumber'].nunique())
    
    with col2:
        clean_pct = (df['MeasurementQualifier'].isna().sum() / len(df) * 100) if len(df) > 0 else 0
        st.metric("Clean %", f"{clean_pct:.1f}%")
        st.metric("Parameters", df['VmvCode'].nunique())
    
    # Date range info
    if len(df) > 0:
        st.sidebar.info(
            f"📅 **Date Range**\n"
            f"{df['SampleDateTime'].min().date()} to {df['SampleDateTime'].max().date()}"
        )


def page_header(title, description):
    """
    Display consistent page header.
    
    Args:
        title (str): Page title
        description (str): Page description
    """
    st.header(title)
    st.markdown(description)
    st.markdown("---")
