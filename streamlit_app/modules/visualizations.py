"""
Visualizations Module
Reusable chart and map builders using Plotly and Folium.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import HeatMap
import pandas as pd
import numpy as np
from data.data_processor import build_vmvcode_mapping, format_vmvcode_display


def metric_card(label, value, unit='', context_text='', col_width=None):
    """
    Display a KPI metric card.
    
    Args:
        label (str): Metric label
        value (float/int): Metric value
        unit (str): Unit of measurement
        context_text (str): Additional context
        col_width: Column width specification (optional)
    """
    formatted_value = f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)
    
    if col_width:
        st.metric(label=label, value=formatted_value + (f" {unit}" if unit else ""), 
                 help=context_text)
    else:
        st.markdown(f"<div style='text-align: center'><p style='font-size: 14px; color: gray'>{label}</p>"
                   f"<p style='font-size: 24px; font-weight: bold'>{formatted_value} {unit}</p></div>", 
                   unsafe_allow_html=True)


def qualifier_distribution_chart(df, title='Measurement Qualifier Distribution', top_n=15):
    """
    Create horizontal bar chart of qualifier codes.
    
    Args:
        df (pd.DataFrame): Input dataframe
        title (str): Chart title
        top_n (int): Number of top qualifiers to show
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure
    """
    qual_dist = df['MeasurementQualifier'].value_counts(dropna=False).head(top_n).reset_index()
    qual_dist.columns = ['Qualifier', 'Count']
    qual_dist['Percentage'] = (qual_dist['Count'] / len(df) * 100).round(2)
    
    # Replace NaN with label
    qual_dist['Qualifier'] = qual_dist['Qualifier'].fillna('(Clean/No Flag)')
    
    # Color-code by category
    def get_color(qual):
        if '(Clean' in str(qual):
            return '#2ecc71'  # Green
        elif qual in ['SUS', 'RER|SUS', 'HT|RER|SUS', 'HT|SUS']:
            return '#e74c3c'  # Red
        else:
            return '#f39c12'  # Orange
    
    colors = [get_color(q) for q in qual_dist['Qualifier']]
    
    fig = px.bar(qual_dist, y='Qualifier', x='Count', orientation='h',
                 labels={'Count': 'Number of Records', 'Qualifier': 'Qualifier Code'},
                 title=title)
    
    fig.update_traces(marker_color=colors)
    fig.update_layout(height=400, showlegend=False)
    
    return fig


def quality_timeline_chart(df, title='Data Quality Trend Over Time'):
    """
    Create line chart showing % clean data over time (monthly).
    
    Args:
        df (pd.DataFrame): Input dataframe
        title (str): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure
    """
    df_temp = df.copy()
    df_temp['YearMonth'] = df_temp['SampleDateTime'].dt.to_period('M')
    
    monthly = df_temp.groupby('YearMonth').apply(
        lambda x: (x['MeasurementQualifier'].isna().sum() / len(x) * 100)
    ).reset_index(name='Pct_Clean')
    monthly['YearMonth'] = monthly['YearMonth'].astype(str)
    
    fig = px.line(monthly, x='YearMonth', y='Pct_Clean',
                  title=title,
                  labels={'Pct_Clean': 'Clean Data (%)', 'YearMonth': 'Month'},
                  markers=True)
    fig.update_layout(height=350)
    
    return fig


def station_quality_heatmap(df, title='Station × Qualifier Code Heatmap', height=500):
    """
    Create heatmap: Stations × Qualifier codes.
    
    Args:
        df (pd.DataFrame): Input dataframe
        title (str): Chart title
        height (int): Chart height
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure
    """
    station_qual = pd.crosstab(df['StationNumber'], df['MeasurementQualifier'])
    
    fig = px.imshow(station_qual, 
                    labels=dict(x='Qualifier Code', y='Station', color='Count'),
                    title=title,
                    color_continuous_scale='YlOrRd',
                    aspect='auto')
    fig.update_layout(height=height)
    
    return fig


def top_stations_chart(df, n=15, title='Top Stations by Record Count'):
    """
    Create bar chart of top stations by record count.
    
    Args:
        df (pd.DataFrame): Input dataframe
        n (int): Number of top stations
        title (str): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure
    """
    top_stations = df['StationNumber'].value_counts().head(n).reset_index()
    top_stations.columns = ['Station', 'Count']
    
    fig = px.bar(top_stations, x='Count', y='Station', orientation='h',
                 title=title,
                 labels={'Count': 'Number of Records', 'Station': 'Station ID'})
    fig.update_layout(height=400, showlegend=False)
    
    return fig


def top_parameters_chart(df, n=15, title='Top Parameters by Measurement Count'):
    """
    Create bar chart of top parameters by count.
    
    Args:
        df (pd.DataFrame): Input dataframe
        n (int): Number of top parameters
        title (str): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure
    """
    # Build VmvCode mapping
    vmvcode_mapping = build_vmvcode_mapping(df)
    
    # Get top parameters
    top_params = df['VmvCode'].value_counts().head(n).reset_index()
    top_params.columns = ['VmvCode', 'Count']
    
    # Add mapped display names
    top_params['Display'] = top_params['VmvCode'].apply(
        lambda x: format_vmvcode_display(x, vmvcode_mapping)
    )
    
    fig = px.bar(top_params, x='Count', y='Display', orientation='h',
                 title=title,
                 labels={'Count': 'Number of Measurements', 'Display': 'VmvCode - Parameter Name'})
    fig.update_layout(height=400, showlegend=False)
    
    return fig


def parameter_quality_chart(quality_by_param, df, n=20, title='Parameter Quality Profile'):
    """
    Create bar chart showing % flagged by parameter.
    
    Args:
        quality_by_param (pd.DataFrame): Quality metrics by parameter
        df (pd.DataFrame): Original dataframe for VmvCode mapping
        n (int): Number of parameters to show
        title (str): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure
    """
    # Build VmvCode mapping
    vmvcode_mapping = build_vmvcode_mapping(df)
    
    data = quality_by_param.head(n).reset_index()
    data.columns = ['VmvCode', 'Total', 'Clean', 'Pct_Clean', 'Flagged', 'Pct_Flagged']
    
    # Add mapped display names
    data['Display'] = data['VmvCode'].apply(
        lambda x: format_vmvcode_display(x, vmvcode_mapping)
    )
    
    fig = px.bar(data, x='Pct_Flagged', y='Display', orientation='h',
                 title=title,
                 labels={'Pct_Flagged': '% Flagged', 'Display': 'VmvCode - Parameter Name'},
                 color='Pct_Flagged',
                 color_continuous_scale='YlOrRd')
    fig.update_layout(height=400, showlegend=False)
    
    return fig


def create_geospatial_map(df, quality_threshold=90, title_suffix=''):
    """
    Create Folium map with station markers colored by quality.
    
    Args:
        df (pd.DataFrame): Input dataframe
        quality_threshold (int): Quality % threshold for coloring
        title_suffix (str): Additional title info
        
    Returns:
        folium.Map: Folium map object
    """
    # Calculate center of map
    if 'LatitudeDecimalDegrees' in df.columns and 'LongitudeDecimalDegrees' in df.columns:
        lat_col = 'LatitudeDecimalDegrees'
        lon_col = 'LongitudeDecimalDegrees'
    elif 'Latitude' in df.columns and 'Longitude' in df.columns:
        lat_col = 'Latitude'
        lon_col = 'Longitude'
    else:
        st.error("Latitude/Longitude columns not found in data")
        return None
    
    center_lat = df[lat_col].mean()
    center_lon = df[lon_col].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    
    # Add station markers
    for station in df['StationNumber'].unique():
        station_data = df[df['StationNumber'] == station]
        
        try:
            lat = station_data[lat_col].iloc[0]
            lon = station_data[lon_col].iloc[0]
            quality = (station_data['MeasurementQualifier'].isna().sum() / len(station_data)) * 100
            record_count = len(station_data)
            
            # Color-code by quality
            if quality >= 95:
                color = 'green'
                category = 'Excellent'
            elif quality >= quality_threshold:
                color = '#2E8BC0'
                category = 'Good'
            else:
                color = 'red'
                category = 'Poor'
            
            # Size proportional to record count (min 4, max 15)
            radius = min(4 + record_count / 200, 15)
            
            popup_text = f"""
            <b>{station}</b><br>
            Quality: {quality:.1f}%<br>
            Records: {record_count:,}<br>
            Category: {category}
            """
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                popup=folium.Popup(popup_text, max_width=250),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)
        except (ValueError, KeyError):
            continue
    
    return m


def quality_by_year_stacked(quality_by_year_df, title='Quality Distribution by Year'):
    """
    Create stacked bar chart of quality by year.
    
    Args:
        quality_by_year_df (pd.DataFrame): Quality metrics by year
        title (str): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure
    """
    data = quality_by_year_df[['pct_clean', 'pct_flagged']].reset_index()
    data.columns = ['Year', 'Clean %', 'Flagged %']
    
    fig = go.Figure(data=[
        go.Bar(name='Clean', x=data['Year'], y=data['Clean %'], marker_color='#2ecc71'),
        go.Bar(name='Flagged', x=data['Year'], y=data['Flagged %'], marker_color='#e74c3c')
    ])
    
    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis_title='Year',
        yaxis_title='Percentage (%)',
        height=350
    )
    
    return fig


def completeness_matrix(df, title='Data Completeness: Stations × Parameters'):
    """
    Create heatmap showing % completeness of station-parameter combinations.
    
    Args:
        df (pd.DataFrame): Input dataframe
        title (str): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure
    """
    # Build VmvCode mapping
    vmvcode_mapping = build_vmvcode_mapping(df)
    
    completeness = df.groupby(['StationNumber', 'VmvCode']).size().unstack(fill_value=0)
    
    # Convert to percentage of max records per parameter
    for col in completeness.columns:
        max_val = completeness[col].max()
        if max_val > 0:
            completeness[col] = (completeness[col] / max_val) * 100
    
    # Rename columns to include mapped parameter names
    completeness.columns = [format_vmvcode_display(col, vmvcode_mapping) for col in completeness.columns]
    
    fig = px.imshow(completeness.head(30),  # Limit to top 30 stations for readability
                    labels=dict(x='VmvCode - Parameter Name', y='Station', color='Coverage %'),
                    title=title,
                    color_continuous_scale='Blues',
                    aspect='auto')
    fig.update_layout(height=500)
    
    return fig


def _build_legend_html(title, items):
    """
    Build a styled HTML legend string to be rendered via st.markdown() outside the map iframe.

    items: list of (color_hex_or_None, label_text) tuples.
           If color is None, the row is rendered as a text-only note.
    """
    rows_html = ""
    for color, label in items:
        if color:
            rows_html += (
                f"<div style='display:flex;align-items:center;gap:6px;margin:3px 0;'>"
                f"<span style='flex-shrink:0;width:16px;height:16px;background:{color};"
                f"border:1px solid #555;border-radius:2px;'></span>"
                f"<span>{label}</span>"
                f"</div>"
            )
        else:
            rows_html += f"<div style='margin:3px 0;color:#555;'>{label}</div>"

    return (
        f"<div style='display:inline-block;background:#f8f9fa;border:1px solid #ced4da;"
        f"border-radius:6px;padding:10px 14px;font-size:12px;line-height:1.4;"
        f"margin-top:4px;max-width:420px;'>"
        f"<div style='font-weight:700;margin-bottom:6px;color:#1d3557;'>{title}</div>"
        f"{rows_html}"
        f"</div>"
    )


def quantile_map(station_df, n_quantiles=5, map_type='points', unit_code=''):
    """
    Build a station map where marker color represents value quantile class.

    Returns:
        (folium.Map, legend_html_str) or None if no data.
    """
    if station_df is None or len(station_df) == 0:
        return None

    work = station_df.dropna(subset=['LatitudeDecimalDegrees', 'LongitudeDecimalDegrees', 'MeasurementValueNum']).copy()
    if len(work) == 0:
        return None

    center_lat = work['LatitudeDecimalDegrees'].mean()
    center_lon = work['LongitudeDecimalDegrees'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)

    unit_suffix = f" {unit_code}" if unit_code else ""

    if map_type == 'heatmap':
        heat_points = work[['LatitudeDecimalDegrees', 'LongitudeDecimalDegrees', 'MeasurementValueNum']].values.tolist()
        HeatMap(heat_points, radius=18, blur=12, min_opacity=0.3).add_to(m)
        min_val = work['MeasurementValueNum'].min()
        max_val = work['MeasurementValueNum'].max()
        gradient_colors = ['#0000ff', '#00ffff', '#00ff00', '#ffff00', '#ff0000']
        gradient_labels = ['Low', 'Low-mid', 'Mid', 'Mid-high', 'High']
        n_steps = len(gradient_colors)
        step = (max_val - min_val) / (n_steps - 1) if max_val > min_val else 0
        items = [("", f"Value range: {min_val:.3f}{unit_suffix} \u2013 {max_val:.3f}{unit_suffix}")]
        for i, (gc, gl) in enumerate(zip(gradient_colors, gradient_labels)):
            v = min_val + i * step
            items.append((gc, f"{gl}: {v:.3f}{unit_suffix}"))
        legend_html = _build_legend_html("Heat map colour scale", items)
        return m, legend_html

    unique_vals = work['MeasurementValueNum'].nunique()
    q = min(n_quantiles, unique_vals) if unique_vals > 0 else 1
    if q <= 1:
        work['quantile'] = 0
        bins = np.array([work['MeasurementValueNum'].min(), work['MeasurementValueNum'].max()])
    else:
        quant_codes, bins = pd.qcut(
            work['MeasurementValueNum'],
            q=q,
            labels=False,
            retbins=True,
            duplicates='drop',
        )
        work['quantile'] = quant_codes

    palette = ['#0B5FA5', '#2E8BC0', '#A8DADC', '#F4A261', '#E76F51']
    max_idx = max(int(work['quantile'].max()), 0)

    for _, row in work.iterrows():
        # quantile index and color
        q_idx = int(row['quantile']) if 'quantile' in row.index else 0
        color = palette[min(q_idx, len(palette) - 1)] if q_idx >= 0 else palette[0]
        popup_text = (
            f"<b>{row['StationNumber']}</b><br>"
            f"Value: {row['MeasurementValueNum']:.3f} {row.get('UnitCode', '')}<br>"
            f"Quantile class: {q_idx + 1} / {max_idx + 1}<br>"
            f"Records: {int(row.get('RecordCount', 0))}"
        )
        folium.CircleMarker(
            location=[row['LatitudeDecimalDegrees'], row['LongitudeDecimalDegrees']],
            radius=7,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.85,
            weight=1,
            popup=folium.Popup(popup_text, max_width=350),
        ).add_to(m)

    n_classes = max(1, len(bins) - 1)
    items = [("", f"Equal-count (quantile) bins — {n_classes} class{'es' if n_classes != 1 else ''}")]
    for i in range(n_classes):
        color = palette[min(i, len(palette) - 1)]
        low = bins[i]
        high = bins[i + 1]
        items.append((color, f"Q{i + 1}: {low:.3f}{unit_suffix} \u2013 {high:.3f}{unit_suffix}"))
    legend_html = _build_legend_html("Quantile legend (value range)", items)

    return m, legend_html


def threshold_map(station_df, threshold, direction='above', map_type='points', show_only_matching=True, unit_code=''):
    """
    Build a binary threshold map (above/below threshold) for station values.

    Returns:
        (folium.Map, legend_html_str) or None if no data.
    """
    if station_df is None or len(station_df) == 0:
        return None

    work = station_df.dropna(subset=['LatitudeDecimalDegrees', 'LongitudeDecimalDegrees', 'MeasurementValueNum']).copy()
    if len(work) == 0:
        return None

    unit_suffix = f" {unit_code}" if unit_code else ""

    if direction == 'above':
        work['match'] = work['MeasurementValueNum'] >= threshold
    else:
        work['match'] = work['MeasurementValueNum'] <= threshold

    if show_only_matching:
        work = work[work['match']].copy()
        if len(work) == 0:
            return None

    center_lat = work['LatitudeDecimalDegrees'].mean()
    center_lon = work['LongitudeDecimalDegrees'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)

    if map_type == 'heatmap':
        heat_points = work[['LatitudeDecimalDegrees', 'LongitudeDecimalDegrees', 'MeasurementValueNum']].values.tolist()
        HeatMap(heat_points, radius=18, blur=12, min_opacity=0.3).add_to(m)
        min_val = work['MeasurementValueNum'].min()
        max_val = work['MeasurementValueNum'].max()
        gradient_colors = ['#0000ff', '#00ffff', '#00ff00', '#ffff00', '#ff0000']
        gradient_labels = ['Low', 'Low-mid', 'Mid', 'Mid-high', 'High']
        n_steps = len(gradient_colors)
        step = (max_val - min_val) / (n_steps - 1) if max_val > min_val else 0
        direction_sym = ">=" if direction == 'above' else "<="
        items = [
            ("", f"Condition: value {direction_sym} {threshold:.3f}{unit_suffix}"),
            ("", f"Displayed range: {min_val:.3f}{unit_suffix} \u2013 {max_val:.3f}{unit_suffix}"),
        ]
        for i, (gc, gl) in enumerate(zip(gradient_colors, gradient_labels)):
            v = min_val + i * step
            items.append((gc, f"{gl}: {v:.3f}{unit_suffix}"))
        legend_html = _build_legend_html("Heat map colour scale (threshold)", items)
        return m, legend_html

    for _, row in work.iterrows():
        is_match = bool(row['match'])
        color = '#2A9D8F' if is_match else '#E63946'
        state = 'Matches condition' if is_match else 'Does not match'
        popup_text = (
            f"<b>{row['StationNumber']}</b><br>"
            f"Value: {row['MeasurementValueNum']:.3f} {row.get('UnitCode', '')}<br>"
            f"Threshold: {threshold:.3f}<br>"
            f"Status: {state}"
        )
        folium.CircleMarker(
            location=[row['LatitudeDecimalDegrees'], row['LongitudeDecimalDegrees']],
            radius=7,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.85,
            weight=1,
            popup=folium.Popup(popup_text, max_width=350),
        ).add_to(m)

    direction_sym = ">=" if direction == 'above' else "<="
    # Only include the threshold marker for stations that meet the condition.
    items = [
        ("", f"Threshold: {threshold:.3f}{unit_suffix} ({direction_sym} condition)"),
        ('#2A9D8F', 'Meets condition'),
    ]
    legend_html = _build_legend_html("Threshold legend", items)

    return m, legend_html


def percentile_time_series(ts_df, variable_label, unit_code):
    """
    Create time-series figure with mean, median, and IQR (p25-p75).
    """
    fig = go.Figure()
    if ts_df is None or len(ts_df) == 0:
        fig.update_layout(
            title=f"No data available for {variable_label}",
            xaxis_title='Time',
            yaxis_title=f"Measurement ({unit_code})" if unit_code else 'Measurement',
            height=430,
        )
        return fig

    x = ts_df['period_label']
    fig.add_trace(go.Scatter(x=x, y=ts_df['p75'], mode='lines', line=dict(width=0), showlegend=False, name='P75'))
    fig.add_trace(go.Scatter(
        x=x,
        y=ts_df['p25'],
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(42, 157, 143, 0.20)',
        line=dict(width=0),
        name='P25-P75',
    ))
    fig.add_trace(go.Scatter(x=x, y=ts_df['mean'], mode='lines+markers', name='Mean', line=dict(color='#1D3557', width=2)))
    fig.add_trace(go.Scatter(x=x, y=ts_df['p50'], mode='lines+markers', name='Median', line=dict(color='#E76F51', width=2, dash='dash')))

    fig.update_layout(
        title=f"Trend summary for {variable_label}",
        xaxis_title='Time',
        yaxis_title=f"Measurement ({unit_code})" if unit_code else 'Measurement',
        legend_title='Statistics',
        height=430,
    )
    return fig


# ---------------------------------------------------------------------------
# Tab 2 — Data Quality Analysis visualizations
# ---------------------------------------------------------------------------

def quality_ranking_chart(stats_df, label_col, pct_col, title, color='#E76F51'):
    """
    Horizontal bar chart ranking variables or stations by % flagged records.

    Args:
        stats_df (pd.DataFrame): Data with label and percentage columns
        label_col (str): Column name for y-axis (category label)
        pct_col (str): Column name for x-axis (% flagged)
        title (str): Chart title
        color (str): Bar fill colour (hex)

    Returns:
        plotly.graph_objects.Figure
    """
    if stats_df is None or len(stats_df) == 0:
        return go.Figure().update_layout(title='No data available', height=300)

    # Sort ascending so highest value appears at top of horizontal bar
    plot_df = stats_df.sort_values(pct_col, ascending=True).copy()

    fig = go.Figure(go.Bar(
        x=plot_df[pct_col],
        y=plot_df[label_col],
        orientation='h',
        marker_color=color,
        customdata=plot_df[['flagged_count', 'total_records']].values,
        hovertemplate=(
            '<b>%{y}</b><br>'
            'Flagged: %{customdata[0]:,} / %{customdata[1]:,}<br>'
            'Rate: %{x:.2f}%<extra></extra>'
        ),
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Flagged records (%)',
        yaxis_title='',
        height=max(350, 25 * len(plot_df) + 100),
        margin=dict(l=10, r=20, t=50, b=40),
        showlegend=False,
    )
    return fig


def qualifier_heatmap_matrix(matrix_df, title):
    """
    Cross-tab heatmap: rows = variable/station labels, columns = qualifier codes.

    Args:
        matrix_df (pd.DataFrame): pd.crosstab output (rows × qualifier codes)
        title (str): Chart title

    Returns:
        plotly.graph_objects.Figure
    """
    if matrix_df is None or matrix_df.empty:
        return go.Figure().update_layout(title='No flagged data available', height=400)

    fig = px.imshow(
        matrix_df,
        labels=dict(x='Qualifier Code', y='', color='Record Count'),
        title=title,
        color_continuous_scale='Blues',
        aspect='auto',
        text_auto=True,
    )
    fig.update_layout(
        height=max(400, 28 * len(matrix_df) + 150),
        xaxis_title='Qualifier Code',
        yaxis_title='',
        coloraxis_colorbar=dict(title='Count'),
    )
    fig.update_xaxes(side='bottom')
    return fig


def quality_station_map(station_df, map_type='points'):
    """
    Folium map with stations coloured by % flagged records.

    Colour classes:
        0%      → green  (#22C55E)  — no flagged records
        >0–5%  → amber  (#FBBF24)
        5–10%  → orange (#F97316)
        >10%   → red    (#DC2626)

    Args:
        station_df (pd.DataFrame): Output of get_station_quality_map_data()
        map_type (str): 'points' or 'heatmap'

    Returns:
        (folium.Map, legend_html_str) or None if no data.
    """
    if station_df is None or len(station_df) == 0:
        return None

    work = station_df.dropna(
        subset=['LatitudeDecimalDegrees', 'LongitudeDecimalDegrees']
    ).copy()
    if len(work) == 0:
        return None

    color_classes = [
        ('#22C55E', 0,    0,           '0% (no issues)'),
        ('#FBBF24', 0,    5,           '>0–5%'),
        ('#F97316', 5,    10,          '5–10%'),
        ('#DC2626', 10,   float('inf'), '> 10%'),
    ]

    def _get_color(pct):
        if pct == 0:
            return color_classes[0][0]  # green: exactly 0%
        for clr, lo, hi, _ in color_classes[1:]:
            if lo < pct <= hi:
                return clr
        return color_classes[-1][0]  # > 10%

    center_lat = work['LatitudeDecimalDegrees'].mean()
    center_lon = work['LongitudeDecimalDegrees'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)

    if map_type == 'heatmap':
        # Exclude stations with 0% flag rate from heat map
        heat_work = work[work['flagged_pct'] > 0].copy()
        if len(heat_work) == 0:
            return None
        heat_work['heat_weight'] = heat_work['flagged_pct'].clip(lower=0.01)
        heat_points = heat_work[
            ['LatitudeDecimalDegrees', 'LongitudeDecimalDegrees', 'heat_weight']
        ].values.tolist()
        HeatMap(heat_points, radius=18, blur=12, min_opacity=0.3).add_to(m)
        items = [
            ("", "Intensity ∝ % flagged records per station"),
            ("", "(Stations with 0% flag rate are excluded)"),
        ]
        legend_html = _build_legend_html("Data quality heat map", items)
        return m, legend_html

    for _, row in work.iterrows():
        pct = float(row['flagged_pct'])
        color = _get_color(pct)
        popup_text = (
            f"<b>{row['StationNumber']}</b><br>"
            f"Station: {row['Station']}<br>"
            f"Flagged: {int(row['flagged_count']):,} / {int(row['total_records']):,}<br>"
            f"Flag rate: {pct:.2f}%"
        )
        folium.CircleMarker(
            location=[row['LatitudeDecimalDegrees'], row['LongitudeDecimalDegrees']],
            radius=7,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.85,
            weight=1,
            popup=folium.Popup(popup_text, max_width=300),
        ).add_to(m)

    items = [("", "Colour = % flagged records per station")]
    for clr, _, _, label in color_classes:
        items.append((clr, label))
    legend_html = _build_legend_html("Station flag rate", items)
    return m, legend_html
