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
    get_qualifier_matrix,
    get_station_aggregated_values,
    get_station_quality_map_data,
    get_station_quality_stats,
    get_statistical_summary,
    get_variable_quality_stats,
)
from modules.visualizations import (
    percentile_time_series,
    qualifier_heatmap_matrix,
    quality_ranking_chart,
    quality_station_map,
    quantile_map,
    threshold_map,
)


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

_nav_options = [
    "Surface water quality analytics and trends",
    "Data quality analysis for surface water quality data",
]
_active_page = st.radio(
    "",
    _nav_options,
    horizontal=True,
    key="main_nav",
    label_visibility="collapsed",
)
st.markdown("---")

if _active_page == _nav_options[0]:
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

elif _active_page == _nav_options[1]:
    st.subheader("Data quality analysis for surface water quality data")

    # ── Sidebar controls ───────────────────────────────────────────────────
    st.sidebar.header("🔎 Filters")

    t2_focus = st.sidebar.radio(
        "Focus of analysis",
        ["By variable", "By station"],
        key="t2_focus",
    )

    t2_flag_scope = st.sidebar.radio(
        "Flag type to analyze",
        ["Unreliable data only", "Unreliable and potentially unreliable data"],
        key="t2_flag_scope",
        help=(
            "Unreliable data only — records with confirmed quality issues: "
            "SUS, RER|SUS, HT|RER|SUS, HT|SUS, DR|SUS.\n\n"
            "Unreliable and potentially unreliable data — additionally includes: "
            "HT, HT|RER, FSE|HT, DR|HT, DR, DR|FSE, DR|SPNF, SPNF."
        ),
    )
    t2_include_potential = t2_flag_scope == "Unreliable and potentially unreliable data"

    st.sidebar.markdown("---")
    t2_date_preset = st.sidebar.selectbox(
        "Date range",
        ["Last year", "Last 5 years", "All data", "Custom"],
        index=2,
        key="t2_date_preset",
    )
    _t2_min_date = df_full["SampleDateTime"].min().date()
    _t2_max_date = df_full["SampleDateTime"].max().date()
    if t2_date_preset == "Custom":
        t2_start_date = st.sidebar.date_input(
            "Start date", value=_t2_min_date,
            min_value=_t2_min_date, max_value=_t2_max_date,
            key="t2_custom_start",
        )
        t2_end_date = st.sidebar.date_input(
            "End date", value=_t2_max_date,
            min_value=_t2_min_date, max_value=_t2_max_date,
            key="t2_custom_end",
        )
    else:
        t2_start_date, t2_end_date = apply_date_preset(df_full, t2_date_preset)

    # ── Apply date filter ─────────────────────────────────────────────────
    df_t2 = filter_by_date(df_full, t2_start_date, t2_end_date)

    # ── Pre-compute stats ─────────────────────────────────────────────────
    t2_var_stats_unreliable = get_variable_quality_stats(df_t2, include_potentially_unreliable=False)
    t2_var_stats_broad = get_variable_quality_stats(df_t2, include_potentially_unreliable=True)
    t2_var_stats = get_variable_quality_stats(df_t2, include_potentially_unreliable=t2_include_potential)
    t2_stn_stats = get_station_quality_stats(df_t2, include_potentially_unreliable=t2_include_potential)

    total_records_t2 = len(df_t2)
    unreliable_count_t2 = int(t2_var_stats_unreliable["flagged_count"].sum())
    broad_count_t2 = int(t2_var_stats_broad["flagged_count"].sum())
    potentially_count_t2 = broad_count_t2 - unreliable_count_t2
    stations_affected_t2 = int((t2_stn_stats["flagged_count"] > 0).sum())
    variables_affected_t2 = int((t2_var_stats["flagged_count"] > 0).sum())

    scope_label = (
        "unreliable and potentially unreliable"
        if t2_include_potential
        else "unreliable"
    )
    scope_title = (
        "unreliable and potentially unreliable records"
        if t2_include_potential
        else "unreliable records"
    )

    # ── A. KPI Summary Row ────────────────────────────────────────────────
    st.markdown(
        '<h4 style="margin-bottom:4px;color:#1d3557;font-size:16px;">'
        f"Dataset quality overview — {scope_title}"
        "</h4>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Scope is controlled by 'Flag type to analyze' in the sidebar. "
        "Percentages remain relative to all records in the selected date range."
    )

    kpi_data = [
        (
            "Unreliable and potentially unreliable records",
            f"{broad_count_t2:,}",
            f"{broad_count_t2 / total_records_t2 * 100:.2f}% of all records",
        )
        if t2_include_potential
        else (
            "Unreliable records",
            f"{unreliable_count_t2:,}",
            f"{unreliable_count_t2 / total_records_t2 * 100:.2f}% of all records",
        ),
        (
            "Stations with flags",
            f"{stations_affected_t2}",
            f"of {len(t2_stn_stats)} total",
        ),
        (
            "Variables with flags",
            f"{variables_affected_t2}",
            f"of {t2_var_stats['VmvCode'].nunique()} total",
        ),
    ]
    kpi_cols = st.columns(len(kpi_data))
    for col, (label, value, context) in zip(kpi_cols, kpi_data):
        with col:
            st.markdown(
                f'<div style="font-size:12px;">'
                f'<p style="font-size:14px;color:gray;">{label}</p>'
                f'<p style="font-size:22px;font-weight:bold;">{value}</p>'
                f'<p style="font-size:11px;color:#888;">{context}</p>'
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── D. GIS Maps (always visible, both modes) ──────────────────────────
    with st.container():
        st.markdown(
            '<h2 style="margin-bottom:0;color:#1d3557;font-weight:700;">'
            "Geospatial distribution of data quality issues"
            "</h2>",
            unsafe_allow_html=True,
        )

        # ── Inline variable + station filters ────────────────────────────
        _gis_var_key_map = build_variable_key_mapping(df_t2)
        _gis_all_vmvcodes = sorted(df_t2["VmvCode"].unique().tolist())
        _gis_label_to_code = {_gis_var_key_map.get(c, str(c)): c for c in _gis_all_vmvcodes}
        _gis_var_labels = sorted(_gis_label_to_code.keys())

        _gis_stn_ref = (
            df_t2[["StationNumber", "Station"]]
            .drop_duplicates("StationNumber")
            .sort_values("StationNumber")
        )
        _gis_stn_options = ["All stations"] + [
            f"{r['StationNumber']} ({r['Station']})" for _, r in _gis_stn_ref.iterrows()
        ]
        _gis_stn_label_to_num = {
            f"{r['StationNumber']} ({r['Station']})": r["StationNumber"]
            for _, r in _gis_stn_ref.iterrows()
        }

        gis_filter_col1, gis_filter_col2, gis_filter_col3 = st.columns([2, 2, 1])
        with gis_filter_col1:
            _gis_sel_var = st.selectbox(
                "Variable",
                options=["All variables"] + _gis_var_labels,
                index=0,
                key="t2_gis_variable",
            )
        with gis_filter_col2:
            _gis_sel_stn = st.selectbox(
                "Station",
                options=_gis_stn_options,
                index=0,
                key="t2_gis_station",
            )
        with gis_filter_col3:
            t2_map_type = st.radio(
                "Map type",
                ["Station points", "Heat map"],
                horizontal=False,
                key="t2_map_type",
            )

        # Resolve filter values
        _gis_variable_filter = (
            None if _gis_sel_var == "All variables"
            else [_gis_label_to_code[_gis_sel_var]]
        )
        _gis_station_filter = (
            None if _gis_sel_stn == "All stations"
            else [_gis_stn_label_to_num[_gis_sel_stn]]
        )

        _gis_var_note = _gis_sel_var
        _gis_stn_note = _gis_sel_stn
        st.markdown(
            f"Station-level flag rate — **{scope_label}** flags · "
            f"**{_gis_var_note}** · **{_gis_stn_note}**"
        )

        # Apply station filter on top of date-filtered data
        _df_gis = (
            df_t2 if _gis_station_filter is None
            else df_t2[df_t2["StationNumber"].isin(_gis_station_filter)].copy()
        )

        map_station_data = get_station_quality_map_data(
            _df_gis,
            include_potentially_unreliable=t2_include_potential,
            variable_filter=_gis_variable_filter,
        )

        t2_map_result = quality_station_map(
            map_station_data,
            map_type="heatmap" if t2_map_type == "Heat map" else "points",
        )

        if t2_map_result is None:
            st.info("No station data available for the current filter.")
        else:
            t2_folium_map, t2_legend_html = t2_map_result
            stf.folium_static(t2_folium_map, width=1400, height=560)
            _assumption_note = (
                "<b>Assumption:</b> Data quality flags are derived from the <code>MeasurementQualifier</code> "
                "field. Records with no entry in this field, or with qualifier codes not associated with "
                "quality issues, are assumed to be clean (no data quality concerns flagged)."
            )
            if t2_map_type == "Heat map":
                method_html_t2 = (
                    "<b>Methodology (Heat map):</b> Each station contributes a point weighted "
                    "by its % flagged records. A Gaussian kernel heat map visualises spatial "
                    "clusters of data quality issues. Higher intensity = higher proportion of "
                    "flagged records in that area.<br><br>"
                    + _assumption_note
                )
            else:
                method_html_t2 = (
                    "<b>Methodology (Station points):</b> Each marker represents one monitoring "
                    "station, coloured by its proportion of flagged records. Hover over a marker "
                    "for exact counts. Colour scale: 0% (green, no quality issues), "
                    "&gt;0%–5% (amber), 5–10% (orange), &gt;10% (red).<br><br>"
                    + _assumption_note
                )
            st.markdown(
                f"<div style='display:flex;gap:16px;align-items:flex-start;'>"
                f"<div style='flex-shrink:0;'>{t2_legend_html}</div>"
                f"<div style='flex:1;font-size:14px;padding-top:8px;'>{method_html_t2}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── B. By Variable mode ───────────────────────────────────────────────
    if t2_focus == "By variable":

        # B1 – Variable ranking, all stations
        with st.container():
            st.markdown(
                '<h2 style="margin-bottom:0;color:#1d3557;font-weight:700;">'
                "Variable ranking — all stations"
                "</h2>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"Variables ranked by % **{scope_label}** records across all stations."
            )
            _var_shown = t2_var_stats[t2_var_stats["flagged_pct"] > 0]
            _var_hidden = t2_var_stats[t2_var_stats["flagged_pct"] == 0]
            if _var_shown.empty:
                st.info("No flagged records found for the selected flag type.")
            else:
                fig_var_all = quality_ranking_chart(
                    _var_shown,
                    label_col="variable_label",
                    pct_col="flagged_pct",
                    title=f"Variable flag rate — all stations ({scope_label})",
                    color="#E76F51",
                )
                st.plotly_chart(fig_var_all, use_container_width=True)
            if len(_var_hidden) > 0:
                with st.expander(f"Show {len(_var_hidden)} variable(s) with 0% flag rate"):
                    st.dataframe(
                        _var_hidden[["variable_label", "total_records"]].rename(
                            columns={"variable_label": "Variable", "total_records": "Total records"}
                        ),
                        use_container_width=True,
                    )

        st.markdown("---")

        # B2 – Variable ranking, top-N problematic stations
        with st.container():
            st.markdown(
                '<h2 style="margin-bottom:0;color:#1d3557;font-weight:700;">'
                "Variable ranking — top N most-flagged stations"
                "</h2>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "Select how many of the most-flagged stations to include. "
                "Variables are re-ranked within that subset."
            )

            b2_max_n = len(t2_stn_stats)
            top_n_stations = st.slider(
                "Top N stations by flag rate",
                min_value=5,
                max_value=min(50, b2_max_n),
                value=min(10, b2_max_n),
                step=5,
                key="t2_topn_slider",
            )

            top_n_station_ids = t2_stn_stats.head(top_n_stations)["StationNumber"].tolist()
            df_topn = df_t2[df_t2["StationNumber"].isin(top_n_station_ids)].copy()
            t2_var_stats_topn = get_variable_quality_stats(
                df_topn, include_potentially_unreliable=t2_include_potential
            )

            _topn_shown = t2_var_stats_topn[t2_var_stats_topn["flagged_pct"] > 0]
            _topn_hidden = t2_var_stats_topn[t2_var_stats_topn["flagged_pct"] == 0]
            if _topn_shown.empty:
                st.info("No flagged records found in the selected top-N stations.")
            else:
                fig_var_topn = quality_ranking_chart(
                    _topn_shown,
                    label_col="variable_label",
                    pct_col="flagged_pct",
                    title=f"Variable flag rate — top {top_n_stations} most-flagged stations ({scope_label})",
                    color="#F4A261",
                )
                st.plotly_chart(fig_var_topn, use_container_width=True)
                shown = top_n_station_ids[:10]
                extra = len(top_n_station_ids) - len(shown)
                st.caption(
                    "Stations included: "
                    + ", ".join(str(s) for s in shown)
                    + (f" … and {extra} more" if extra > 0 else "")
                )
            if len(_topn_hidden) > 0:
                with st.expander(f"Show {len(_topn_hidden)} variable(s) with 0% flag rate"):
                    st.dataframe(
                        _topn_hidden[["variable_label", "total_records"]].rename(
                            columns={"variable_label": "Variable", "total_records": "Total records"}
                        ),
                        use_container_width=True,
                    )

        st.markdown("---")

        # B3 – Qualifier flag distribution by variable
        with st.container():
            st.markdown(
                '<h2 style="margin-bottom:0;color:#1d3557;font-weight:700;">'
                "Qualifier flag distribution by variable"
                "</h2>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "How each qualifier code is distributed across variables. "
                "Only unreliable / potentially unreliable codes are shown."
            )
            matrix_var = get_qualifier_matrix(df_t2, group_by="variable")
            if matrix_var.empty:
                st.info("No flagged records found.")
            else:
                fig_matrix_var = qualifier_heatmap_matrix(
                    matrix_var,
                    title="Qualifier code × variable — record count",
                )
                st.plotly_chart(fig_matrix_var, use_container_width=True)
                with st.expander("View as table (download-ready)"):
                    st.dataframe(matrix_var, use_container_width=True)

    # ── C. By Station mode ────────────────────────────────────────────────
    else:

        # C1 – Station ranking
        with st.container():
            st.markdown(
                '<h2 style="margin-bottom:0;color:#1d3557;font-weight:700;">'
                "Station ranking by data quality issues"
                "</h2>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"All {len(t2_stn_stats)} stations ranked by % **{scope_label}** "
                "records (all variables combined)."
            )
            _stn_shown = t2_stn_stats[t2_stn_stats["flagged_pct"] > 0]
            _stn_hidden = t2_stn_stats[t2_stn_stats["flagged_pct"] == 0]
            if _stn_shown.empty:
                st.info("No flagged records found for the selected flag type.")
            else:
                fig_stn = quality_ranking_chart(
                    _stn_shown,
                    label_col="station_label",
                    pct_col="flagged_pct",
                    title=f"Station flag rate ({scope_label})",
                    color="#2E8BC0",
                )
                st.plotly_chart(fig_stn, use_container_width=True)
            if len(_stn_hidden) > 0:
                with st.expander(f"Show {len(_stn_hidden)} station(s) with 0% flag rate"):
                    st.dataframe(
                        _stn_hidden[["station_label", "total_records"]].rename(
                            columns={"station_label": "Station", "total_records": "Total records"}
                        ),
                        use_container_width=True,
                    )

        st.markdown("---")

        # C2 – Qualifier flag distribution by station
        with st.container():
            st.markdown(
                '<h2 style="margin-bottom:0;color:#1d3557;font-weight:700;">'
                "Qualifier flag distribution by station"
                "</h2>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "How each qualifier code is distributed across stations. "
                "Only unreliable / potentially unreliable codes are shown."
            )
            matrix_stn = get_qualifier_matrix(df_t2, group_by="station")
            if matrix_stn.empty:
                st.info("No flagged records found.")
            else:
                fig_matrix_stn = qualifier_heatmap_matrix(
                    matrix_stn,
                    title="Qualifier code × station — record count",
                )
                st.plotly_chart(fig_matrix_stn, use_container_width=True)
                with st.expander("View as table (download-ready)"):
                    st.dataframe(matrix_stn, use_container_width=True)

st.markdown("---")
st.caption("Dashboard status: Active | Updated: 2026-05-18")
