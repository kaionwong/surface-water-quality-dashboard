"""
Alberta Surface Water Quality Dashboard
Three-page interface focused on analytics and trends.
"""

import os
import sys
import time
from datetime import timedelta

import pandas as pd
import streamlit as st
import streamlit_folium as stf

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.data_loader import load_data
from data.data_processor import (
    apply_quality_filter,
    build_variable_key_mapping,
    compute_time_series_percentiles,
    get_statistical_summary,
    get_station_aggregated_values,
)
from modules.visualizations import percentile_time_series, quantile_map, threshold_map


st.set_page_config(
    page_title="Water Quality Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1d3557;
        margin-bottom: 8px;
    }
    .subtle {
        color: #5f6b7a;
    }
    .metric-value-small [data-testid="metricDeltaContainer-up"],
    .metric-value-small [data-testid="metricDeltaContainer-down"],
    .metric-value-small [class*="metric"] {
        font-size: 0.75rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_full_data():
    """Load full dataset (Version C)."""
    df = load_data("C")
    if "SampleDateTime" in df.columns:
        df["SampleDateTime"] = pd.to_datetime(df["SampleDateTime"], errors="coerce")
    return df


def apply_date_preset(df, preset):
    """Return start/end dates based on quick preset."""
    min_date = df["SampleDateTime"].min().date()
    max_date = df["SampleDateTime"].max().date()

    if preset == "Last year":
        start = max(min_date, max_date - timedelta(days=365))
        end = max_date
    elif preset == "Last 5 years":
        start = max(min_date, max_date - timedelta(days=365 * 5))
        end = max_date
    elif preset == "All data":
        start = min_date
        end = max_date
    else:
        start = min_date
        end = max_date
    return start, end


def seasonal_label(ts):
    """Return year-season label for a timestamp."""
    month = ts.month
    if month in [12, 1, 2]:
        season = "Winter"
    elif month in [3, 4, 5]:
        season = "Spring"
    elif month in [6, 7, 8]:
        season = "Summer"
    else:
        season = "Fall"
    return f"{ts.year} {season}"


def add_period_label(df, aggregation):
    """Add period label for map slider filtering."""
    out = df.copy()
    if aggregation == "Weekly":
        out["PeriodLabel"] = out["SampleDateTime"].dt.to_period("W").astype(str)
    elif aggregation == "Monthly":
        out["PeriodLabel"] = out["SampleDateTime"].dt.to_period("M").astype(str)
    elif aggregation == "Quarterly":
        out["PeriodLabel"] = out["SampleDateTime"].dt.to_period("Q").astype(str)
    elif aggregation == "Yearly":
        out["PeriodLabel"] = out["SampleDateTime"].dt.to_period("Y").astype(str)
    else:
        out["PeriodLabel"] = out["SampleDateTime"].apply(seasonal_label)
    return out


def filter_by_date(df, start_date, end_date):
    mask = (df["SampleDateTime"].dt.date >= start_date) & (df["SampleDateTime"].dt.date <= end_date)
    return df[mask].copy()


def format_metric(value, decimals=2):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.{decimals}f}"


st.markdown('<h2 class="main-header">Alberta Surface Water Quality Dashboard</h2>', unsafe_allow_html=True)
st.markdown(
    """
Interactive analytics for Alberta surface water data with variable-level filtering,
quality-aware summaries, geospatial mapping, and trend analysis.
"""
)
st.markdown("---")


df_full = get_full_data()

if len(df_full) == 0:
    st.warning("No data loaded.")
    st.stop()

main_tab_1, main_tab_2, main_tab_3 = st.tabs(
    [
        "Surface water quality analytics and trends",
        "Data quality analysis for surface water quality data",
        "Statistical and sensitivity analyses",
    ]
)

with main_tab_1:
    st.subheader("Surface water quality analytics and trends")

    st.sidebar.header("🔍 Filters")

    variable_key_map = build_variable_key_mapping(df_full)
    # sort by VariableName (the new label format puts VariableName first)
    all_vmvcodes = df_full["VmvCode"].unique().tolist()
    label_to_code = {variable_key_map.get(code, str(code)): code for code in all_vmvcodes}
    variable_labels = sorted(label_to_code.keys())

    selected_variable_label = st.sidebar.selectbox(
        "Select variable: VariableName (VmvCode-VariableCode)",
        options=variable_labels,
        index=0,
        key="sidebar_variable",
    )
    selected_vmvcode = label_to_code[selected_variable_label]

    df_variable = df_full[df_full["VmvCode"] == selected_vmvcode].copy()

    quality_option = st.sidebar.radio(
        "Data quality filter",
        options=[
            "Exclude unreliable data",
            "Exclude unreliable and potentially unreliable data",
            "All data",
        ],
        horizontal=False,
        index=0,
        key="sidebar_quality",
        help=(
            "Exclude unreliable data — removes records flagged with qualifier codes "
            "SUS, RER|SUS, HT|RER|SUS, HT|SUS, DR|SUS "
            "(confirmed data quality issues such as suspected errors or repeated errors with suspect flags).\n\n"
            "Exclude unreliable and potentially unreliable data — additionally removes "
            "HT, HT|RER, FSE|HT, DR|HT, DR, DR|FSE, DR|SPNF, SPNF "
            "(potential quality concerns including high turbidity, drift, sensor malfunction, or spike noise flags).\n\n"
            "All data — no records are removed based on qualifier codes."
        ),
    )

    quality_map = {
        "Exclude unreliable data": "definite",
        "Exclude unreliable and potentially unreliable data": "broader",
        "All data": "all",
    }

    df_after_quality = apply_quality_filter(df_variable, quality_map[quality_option])

    station_ref = df_after_quality[["StationNumber", "Station"]].drop_duplicates("StationNumber").copy()
    station_ref["station_label"] = station_ref.apply(
        lambda r: f"{r['StationNumber']} ({r['Station']})", axis=1
    )
    all_station_labels = sorted(station_ref["station_label"].tolist())
    label_to_station = {
        label: station
        for label, station in zip(station_ref["station_label"], station_ref["StationNumber"])
    }

    st.sidebar.markdown("Select stations")
    all_stations_selected = st.sidebar.checkbox(
        "All stations",
        value=True,
        key="sidebar_all_stations",
        help="Use 'All stations' to include every station, or uncheck it to choose specific stations from the list below.",
    )
    if all_stations_selected:
        selected_stations = station_ref["StationNumber"].tolist()
    else:
        selected_station_labels = st.sidebar.multiselect(
            "StationNumber (Station)",
            options=all_station_labels,
            default=all_station_labels[: min(10, len(all_station_labels))],
            key="sidebar_stations",
        )
        selected_stations = [label_to_station[lbl] for lbl in selected_station_labels]

    st.sidebar.markdown("---")
    sidebar_preset = st.sidebar.selectbox(
        "Global date range preset",
        ["Last year", "Last 5 years", "All data", "Custom"],
        index=2,
        key="sidebar_date_preset",
    )

    var_min_date = df_after_quality["SampleDateTime"].min().date()
    var_max_date = df_after_quality["SampleDateTime"].max().date()
    if sidebar_preset == "Custom":
        sidebar_start = st.sidebar.date_input(
            "Global start date",
            value=var_min_date,
            min_value=var_min_date,
            max_value=var_max_date,
            key="sidebar_start",
        )
        sidebar_end = st.sidebar.date_input(
            "Global end date",
            value=var_max_date,
            min_value=var_min_date,
            max_value=var_max_date,
            key="sidebar_end",
        )
    else:
        sidebar_start, sidebar_end = apply_date_preset(df_after_quality, sidebar_preset)

    if sidebar_start > sidebar_end:
        sidebar_start, sidebar_end = sidebar_end, sidebar_start

    df_filtered = df_after_quality[df_after_quality["StationNumber"].isin(selected_stations)].copy()
    df_filtered = filter_by_date(df_filtered, sidebar_start, sidebar_end)

    if len(df_filtered) == 0:
        st.warning("No rows remain after applying filters.")
        st.stop()

    unit_mode = df_filtered["UnitCode"].mode(dropna=True)
    active_unit = unit_mode.iloc[0] if len(unit_mode) > 0 else ""

    summary = get_statistical_summary(df_filtered, df_variable)

    st.markdown(
        f'<h4 style="margin-bottom:0;color:#1d3557;font-size:16px;">Selected variable: <span style="font-weight:700;">{selected_variable_label}</span></h4>',
        unsafe_allow_html=True,
    )

    stat_cols = st.columns(8)
    with stat_cols[0]:
        st.markdown(f'<div style="font-size:12px;"><p style="font-size:14px;color:gray;">Count</p><p style="font-size:22px;font-weight:bold;">{summary["count"]:,}</p></div>', unsafe_allow_html=True)
    with stat_cols[1]:
        st.markdown(f'<div style="font-size:12px;"><p style="font-size:14px;color:gray;">Mean</p><p style="font-size:22px;font-weight:bold;">{format_metric(summary["mean"], 3)}</p></div>', unsafe_allow_html=True)
    with stat_cols[2]:
        st.markdown(f'<div style="font-size:12px;"><p style="font-size:14px;color:gray;">Median</p><p style="font-size:22px;font-weight:bold;">{format_metric(summary["median"], 3)}</p></div>', unsafe_allow_html=True)
    with stat_cols[3]:
        st.markdown(f'<div style="font-size:12px;"><p style="font-size:14px;color:gray;">Std dev</p><p style="font-size:22px;font-weight:bold;">{format_metric(summary["std"], 3)}</p></div>', unsafe_allow_html=True)
    with stat_cols[4]:
        st.markdown(f'<div style="font-size:12px;"><p style="font-size:14px;color:gray;">Min</p><p style="font-size:22px;font-weight:bold;">{format_metric(summary["min"], 3)}</p></div>', unsafe_allow_html=True)
    with stat_cols[5]:
        st.markdown(f'<div style="font-size:12px;"><p style="font-size:14px;color:gray;">Max</p><p style="font-size:22px;font-weight:bold;">{format_metric(summary["max"], 3)}</p></div>', unsafe_allow_html=True)
    with stat_cols[6]:
        st.markdown(f'<div style="font-size:12px;"><p style="font-size:14px;color:gray;">% removed by filters</p><p style="font-size:22px;font-weight:bold;">{summary["pct_removed"]:.2f}%</p></div>', unsafe_allow_html=True)
    with stat_cols[7]:
        st.markdown(f'<div style="font-size:12px;"><p style="font-size:14px;color:gray;">Number of stations</p><p style="font-size:22px;font-weight:bold;">{summary["stations"]:,}</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    with st.container():
        st.markdown(
            '<h2 style="margin-bottom:0;color:#1d3557;font-weight:700;">Quantile map</h2>',
            unsafe_allow_html=True,
        )
        st.markdown("**Select map settings**")
        m1_col1, m1_col2, m1_col3 = st.columns(3)
        with m1_col1:
            map1_preset = st.selectbox(
                "Time range preset",
                ["Last year", "Last 5 years", "All data", "Custom"],
                index=2,
                key="map1_preset",
            )
        with m1_col2:
            map1_agg = st.selectbox(
                "Aggregation period",
                ["Weekly", "Monthly", "Quarterly", "Yearly", "Seasonal"],
                index=1,
                key="map1_agg",
            )
        with m1_col3:
            map1_type = st.radio(
                "Map type",
                ["Station points", "Heat map"],
                horizontal=False,
                key="map1_type",
            )

        min_date = df_filtered["SampleDateTime"].min().date()
        max_date = df_filtered["SampleDateTime"].max().date()

        if map1_preset == "Custom":
            dcol1, dcol2 = st.columns(2)
            with dcol1:
                map1_start = st.date_input("Start date", value=min_date, min_value=min_date, max_value=max_date, key="map1_start")
            with dcol2:
                map1_end = st.date_input("End date", value=max_date, min_value=min_date, max_value=max_date, key="map1_end")
        else:
            map1_start, map1_end = apply_date_preset(df_filtered, map1_preset)
            st.caption(f"Date window: {map1_start} to {map1_end}")

        if map1_start > map1_end:
            map1_start, map1_end = map1_end, map1_start

        df_map1 = filter_by_date(df_filtered, map1_start, map1_end)
        df_map1 = add_period_label(df_map1, map1_agg)
        map1_periods = sorted(df_map1["PeriodLabel"].dropna().unique().tolist())

        if not map1_periods:
            st.info("No map data available for this date range.")
        else:
            selected_map1_period = st.select_slider(
                "Play historical change (drag time)",
                options=map1_periods,
                value=map1_periods[-1],
                key="map1_period_slider",
            )

            p1_col1, p1_col2 = st.columns([1, 1])
            with p1_col1:
                autoplay_map1 = st.button("Play as video", key="map1_play")
            with p1_col2:
                autoplay_speed_map1 = st.selectbox("Playback speed (sec/frame)", [0.25, 0.5, 0.75, 1.0], index=1, key="map1_speed")

            map_placeholder_1 = st.empty()
            legend_placeholder_1 = st.empty()
            status_placeholder_1 = st.empty()

            def render_map1_for_period(period_label):
                df_map1_period = df_map1[df_map1["PeriodLabel"] == period_label].copy()
                station_map1 = get_station_aggregated_values(df_map1_period)
                result_1 = quantile_map(
                    station_map1,
                    map_type="heatmap" if map1_type == "Heat map" else "points",
                    unit_code=active_unit,
                )
                if result_1 is None:
                    with map_placeholder_1.container():
                        st.info("No station values available in the selected period.")
                    legend_placeholder_1.empty()
                else:
                    folium_map_1, legend_html_1 = result_1
                    with map_placeholder_1.container():
                        stf.folium_static(folium_map_1, width=1400, height=560)
                    with legend_placeholder_1.container():
                        if map1_type == "Heat map":
                            method_html = (
                                "<b>Methodology (Heat map):</b> Mean measurement value is computed per station "
                                "across all records in the selected period. The heat map uses a Gaussian kernel "
                                "to visualize spatial density of concentrations. Intensity reflects relative value "
                                "magnitude, not counts."
                            )
                        else:
                            method_html = (
                                "<b>Methodology (Station points):</b> Mean measurement value is computed per station "
                                "across all records in the selected period. Each station is then assigned to one of "
                                "up to 5 quantile classes using equal-count (quantile) binning (qcut). Marker color "
                                "progresses from blue (lowest quantile) to red (highest quantile)."
                            )
                        st.markdown(
                            f"<div style='display:flex;gap:16px;align-items:flex-start;'>"
                            f"<div style='flex-shrink:0;'>{legend_html_1}</div>"
                            f"<div style='flex:1;font-size:14px;padding-top:8px;'>{method_html}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

            if autoplay_map1:
                for period_label in map1_periods:
                    status_placeholder_1.caption(f"Playing frame: {period_label}")
                    render_map1_for_period(period_label)
                    time.sleep(autoplay_speed_map1)
                status_placeholder_1.caption("Playback complete")
            else:
                render_map1_for_period(selected_map1_period)

    st.markdown("---")
    with st.container():
        st.markdown(
            '<h2 style="margin-bottom:0;color:#1d3557;font-weight:700;">Threshold map</h2>',
            unsafe_allow_html=True,
        )
        st.markdown("**Select map settings**")
        m2_col1, m2_col2, m2_col3 = st.columns(3)
        with m2_col1:
            map2_preset = st.selectbox(
                "Time range preset",
                ["Last year", "Last 5 years", "All data", "Custom"],
                index=2,
                key="map2_preset",
            )
        with m2_col2:
            map2_agg = st.selectbox(
                "Aggregation period",
                ["Weekly", "Monthly", "Quarterly", "Yearly", "Seasonal"],
                index=1,
                key="map2_agg",
            )
        with m2_col3:
            map2_type = st.radio(
                "Map type",
                ["Station points", "Heat map"],
                horizontal=False,
                key="map2_type",
            )

        min_date = df_filtered["SampleDateTime"].min().date()
        max_date = df_filtered["SampleDateTime"].max().date()

        if map2_preset == "Custom":
            dcol1, dcol2 = st.columns(2)
            with dcol1:
                map2_start = st.date_input("Start date", value=min_date, min_value=min_date, max_value=max_date, key="map2_start")
            with dcol2:
                map2_end = st.date_input("End date", value=max_date, min_value=min_date, max_value=max_date, key="map2_end")
        else:
            map2_start, map2_end = apply_date_preset(df_filtered, map2_preset)
            st.caption(f"Date window: {map2_start} to {map2_end}")

        if map2_start > map2_end:
            map2_start, map2_end = map2_end, map2_start

        df_map2 = filter_by_date(df_filtered, map2_start, map2_end)
        df_map2 = add_period_label(df_map2, map2_agg)
        map2_periods = sorted(df_map2["PeriodLabel"].dropna().unique().tolist())

        if not map2_periods:
            st.info("No map data available for this date range.")
        else:
            selected_map2_period = st.select_slider(
                "Play historical change (drag time)",
                options=map2_periods,
                value=map2_periods[-1],
                key="map2_period_slider",
            )
            df_map2_period = df_map2[df_map2["PeriodLabel"] == selected_map2_period].copy()
            station_map2 = get_station_aggregated_values(df_map2_period)

            threshold_data = pd.to_numeric(df_filtered["MeasurementValue"], errors="coerce").dropna() if "MeasurementValue" in df_filtered.columns else pd.Series(dtype=float)
            if len(threshold_data) > 0:
                threshold_min = float(threshold_data.min())
                threshold_max = float(threshold_data.max())
                threshold_p50 = float(threshold_data.quantile(0.50))
                if threshold_min == threshold_max:
                    threshold_max = threshold_min + 1.0
                threshold_step = max((threshold_max - threshold_min) / 1000, 0.0001)
            else:
                threshold_min = 0.0
                threshold_max = 1.0
                threshold_p50 = 0.5
                threshold_step = 0.001
            tcol1, tcol2 = st.columns(2)
            with tcol1:
                threshold_value = st.slider(
                    "Threshold value",
                    min_value=threshold_min,
                    max_value=threshold_max,
                    value=threshold_p50,
                    step=threshold_step,
                    format="%.3f",
                    key="threshold_slider",
                )
            with tcol2:
                threshold_direction = st.radio(
                    "Condition",
                    ["Over threshold", "Under threshold"],
                    horizontal=False,
                    key="threshold_direction",
                )

            p2_col1, p2_col2 = st.columns([1, 1])
            with p2_col1:
                autoplay_map2 = st.button("Play as video", key="map2_play")
            with p2_col2:
                autoplay_speed_map2 = st.selectbox("Playback speed (sec/frame)", [0.25, 0.5, 0.75, 1.0], index=1, key="map2_speed")

            map_placeholder_2 = st.empty()
            legend_placeholder_2 = st.empty()
            status_placeholder_2 = st.empty()

            def render_map2_for_period(period_label):
                df_map2_period_local = df_map2[df_map2["PeriodLabel"] == period_label].copy()
                station_map2_local = get_station_aggregated_values(df_map2_period_local)
                result_2 = threshold_map(
                    station_map2_local,
                    threshold=threshold_value,
                    direction="above" if threshold_direction == "Over threshold" else "below",
                    map_type="heatmap" if map2_type == "Heat map" else "points",
                    show_only_matching=True,
                    unit_code=active_unit,
                )
                if result_2 is None:
                    with map_placeholder_2.container():
                        st.info("No stations satisfy the selected threshold condition.")
                    legend_placeholder_2.empty()
                else:
                    folium_map_2, legend_html_2 = result_2
                    with map_placeholder_2.container():
                        stf.folium_static(folium_map_2, width=1400, height=560)
                    with legend_placeholder_2.container():
                        if map2_type == "Heat map":
                            method_html_2 = (
                                "<b>Methodology (Heat map):</b> Mean measurement value is computed per station "
                                "across all records in the selected period. Only stations meeting the threshold "
                                "condition are included. The heat map uses a Gaussian kernel to visualize spatial "
                                "density of those values."
                            )
                        else:
                            method_html_2 = (
                                "<b>Methodology (Station points):</b> Mean measurement value is computed per station "
                                "across all records in the selected period. Stations meeting the threshold condition "
                                "are highlighted on the map."
                            )
                        st.markdown(
                            f"<div style='display:flex;gap:16px;align-items:flex-start;'>"
                            f"<div style='flex-shrink:0;'>{legend_html_2}</div>"
                            f"<div style='flex:1;font-size:14px;padding-top:8px;'>{method_html_2}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

            if autoplay_map2:
                for period_label in map2_periods:
                    status_placeholder_2.caption(f"Playing frame: {period_label}")
                    render_map2_for_period(period_label)
                    time.sleep(autoplay_speed_map2)
                status_placeholder_2.caption("Playback complete")
            else:
                render_map2_for_period(selected_map2_period)

    st.markdown("---")
    st.subheader("Time-series summary")

    ts_col1, ts_col2 = st.columns(2)
    with ts_col1:
        ts_agg = st.radio(
            "Aggregation period",
            ["Weekly", "Monthly", "Quarterly", "Yearly", "Seasonal"],
            horizontal=True,
            index=1,
            key="ts_agg",
        )
    with ts_col2:
        ts_preset = st.selectbox(
            "Time range preset",
            ["Last year", "Last 5 years", "All data", "Custom"],
            index=2,
            key="ts_preset",
        )

    ts_min_date = df_filtered["SampleDateTime"].min().date()
    ts_max_date = df_filtered["SampleDateTime"].max().date()

    if ts_preset == "Custom":
        c1, c2 = st.columns(2)
        with c1:
            ts_start = st.date_input("Start date", value=ts_min_date, min_value=ts_min_date, max_value=ts_max_date, key="ts_start")
        with c2:
            ts_end = st.date_input("End date", value=ts_max_date, min_value=ts_min_date, max_value=ts_max_date, key="ts_end")
    else:
        ts_start, ts_end = apply_date_preset(df_filtered, ts_preset)
        st.caption(f"Date window: {ts_start} to {ts_end}")

    if ts_start > ts_end:
        ts_start, ts_end = ts_end, ts_start

    df_ts = filter_by_date(df_filtered, ts_start, ts_end)

    period_map = {
        "Weekly": "W",
        "Monthly": "M",
        "Quarterly": "Q",
        "Yearly": "Y",
        "Seasonal": "seasonal",
    }
    ts_summary = compute_time_series_percentiles(df_ts, period_map[ts_agg])

    if len(ts_summary) > 0:
        period_options = ts_summary["period_label"].tolist()
        selected_ts_period = st.select_slider(
            "Play historical time-series (drag time)",
            options=period_options,
            value=period_options[-1],
            key="ts_period_slider",
        )

        ts_controls_1, ts_controls_2 = st.columns([1, 1])
        with ts_controls_1:
            autoplay_ts = st.button("Play time-series as video", key="ts_play")
        with ts_controls_2:
            autoplay_speed_ts = st.selectbox("Playback speed (sec/frame)", [0.25, 0.5, 0.75, 1.0], index=1, key="ts_speed")

        ts_chart_placeholder = st.empty()
        ts_status_placeholder = st.empty()

        def render_ts_until(period_label):
            idx = period_options.index(period_label)
            ts_view = ts_summary.iloc[: idx + 1].copy()
            ts_fig = percentile_time_series(ts_view, selected_variable_label, active_unit)
            with ts_chart_placeholder.container():
                st.plotly_chart(ts_fig, width="stretch")

        if autoplay_ts:
            for period_label in period_options:
                ts_status_placeholder.caption(f"Playing frame: {period_label}")
                render_ts_until(period_label)
                time.sleep(autoplay_speed_ts)
            ts_status_placeholder.caption("Playback complete")
        else:
            render_ts_until(selected_ts_period)
    else:
        ts_fig = percentile_time_series(ts_summary, selected_variable_label, active_unit)
        st.plotly_chart(ts_fig, width="stretch")

with main_tab_2:
    st.subheader("Data quality analysis for surface water quality data")
    st.info("Placeholder: additional data quality diagnostics will be added here.")

with main_tab_3:
    st.subheader("Statistical and sensitivity analyses")
    st.info("Placeholder: statistical and sensitivity workflows will be added here.")

st.markdown("---")
st.caption("Dashboard status: Active | Updated: 2026-05-18")
