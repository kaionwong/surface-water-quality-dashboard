# Alberta Surface Water Quality Dashboard

Interactive Streamlit dashboard for exploring 247,121+ water quality measurements (2020-2023) across 174 monitoring stations.

## Project Structure

```
streamlit_app/
├── app.py                          # Main entry point (multi-page routing)
├── requirements.txt                # Python dependencies
├── .streamlit/
│   └── config.toml                # Streamlit configuration
├── data/
│   ├── data_loader.py             # CSV loading & caching
│   └── data_processor.py           # Filtering, aggregation, quality classification
├── modules/
│   ├── visualizations.py          # Plotly & Folium chart builders
│   ├── filters.py                 # Sidebar controls & filter application
│   └── utils.py                   # Helper functions (TBD)
└── pages/
    ├── 1_dataset_overview.py      # Page 1 (integrated into app.py for MVP)
    ├── 2_data_quality_analysis.py # Page 2 (integrated into app.py for MVP)
    ├── 3_unit_of_analysis.py      # Page 3 (integrated into app.py for MVP)
    ├── 4_geospatial_analysis.py   # Page 4 (integrated into app.py for MVP)
    └── 5_advanced_analytics.py    # Page 5 (integrated into app.py for MVP)
```

## Quick Start

### 1. Install Dependencies

```bash
cd streamlit_app
pip install -r requirements.txt
```

### 2. Run the App

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

### 3. Data Source

The dashboard loads CSV files from `../output/`:
- `dataset_version_a_strict.csv` (246,052 records) - High quality, excludes SUS codes
- `dataset_version_b_balanced.csv` (246,052 records) - Balanced, excludes SUS-combined
- `dataset_version_c_full.csv` (247,121 records) - Full data with quality indicators

**🔄 Update data**: Re-run notebooks in `../notebooks/` to refresh CSVs; dashboard auto-reloads from cache

## Features (MVP v0.1)

### Page 1: Surface water quality analytics and trends ✅
- **Statistical Summary**: Count, Mean, Median, Std dev, Min, Max, % removed by filters, Number of stations
  - Real-time updates reflect selected data quality filter and station/date selections
  - Metrics formatted to 3 decimal places for precision
- **Quantile Map**: Equal-count binning visualization
  - 5 color-coded quantile classes (blue = lowest, red = highest)
  - Drag time slider to visualize historical changes across aggregation periods (Weekly/Monthly/Quarterly/Yearly/Seasonal)
  - Optional heat map view with spatial density visualization
  - Playback feature with adjustable speed
- **Threshold Map**: Binary value threshold detection
  - Interactive slider control with minimum, median (default), and maximum values
  - Station markers highlighted for values meeting/exceeding threshold
  - Direction toggle (above/below threshold)
  - Both point map and heat map options
  - Configurable time range and aggregation period
- **Trend Analysis**: Time-series percentile trend chart
  - Mean, median, and IQR (P25-P75) visualization
  - Temporal trends overlay
- **Map Settings**: Flexible controls for all visualizations
  - Time range presets (Last year, Last 5 years, All data, Custom)
  - Aggregation period selection
  - Map type selection (Station points or Heat map)
- **Data Quality Filtering**: Multi-level quality gate
  - Exclude unreliable data (confirmed quality issues: SUS, RER|SUS, HT|RER|SUS, HT|SUS, DR|SUS)
  - Exclude unreliable and potentially unreliable data (adds HT, HT|RER, FSE|HT, DR|HT, DR, DR|FSE, DR|SPNF, SPNF)
  - All data (no filtering)
- **Unit Integration**: Active units displayed in metrics and legends for all visualizations

### Page 2: Data Quality Analysis ⭐
- **Qualifier Distribution**: All 16+ qualifier codes with counts & percentages
- **Version Comparison**: Record counts for A/B/C versions
- **Station × Qualifier Heatmap**: Identify problematic station-code combinations
- **Parameter Quality Ranking**: Which parameters have most flags
- **Quality Trends**: Monthly % clean data over time
- **Missing/Null Analysis**: Column-by-column null value analysis

### Page 3: Unit of Analysis
- **By Station**: Station-level summary, parameters, sampling frequency, quality
- **By Parameter**: Parameter details, measuring stations, statistics, quality profile
- **By Time Period**: Year/month-level analysis, active stations, top parameters
- **Summary Statistics**: Aggregated tables by station/parameter/year

### Page 4: Geospatial Analysis
- **Interactive Folium Map**: 174 station markers color-coded by quality
  - Green: ≥95% clean | Orange: 90-95% clean | Red: <90% clean
  - Marker size: Proportional to record count
- **Station Quality Ranking**: Top 10 best / worst stations
- **Quality Threshold Control**: Adjust "good" quality threshold slider

### Page 5: Advanced Analytics (Placeholder)
- Trend analysis (Phase 2)
- Correlation matrices (Phase 2)
- Anomaly detection (Phase 2)

## Global Filters (Sidebar)

Applied to Page 1 (Surface water quality analytics and trends):
- **Variable Selection**: Choose water quality parameter (displayed as VariableName (VmvCode-VariableCode))
- **Data Quality Filter**: Multi-level quality gate with 3 options
  - Exclude unreliable data (confirmed issues)
  - Exclude unreliable and potentially unreliable data (broader)
  - All data (no filtering)
- **Station Selection**: All stations or custom multiselect by StationNumber (Station)
- **Date Range**: Global date range preset (Last year, Last 5 years, All data, Custom)

Filters dynamically update statistics, maps, and trend visualization in real-time.

## Data Processing Pipeline

```
Raw CSV (Version C, 247K records)
        ↓
    Filters (date, station, parameter applied)
        ↓
    Quality Classification (Clean/Suspect/Acceptable/Other)
        ↓
    Visualizations (Plotly, Folium)
        ↓
    Dashboard Display
```

### Key Data Functions

**data_loader.py**:
- `load_version_a()`: Strict filtering (excludes SUS)
- `load_version_b()`: Balanced filtering
- `load_version_c()`: Full data with quality indicators
- `get_data_info()`: Summary statistics

**data_processor.py**:
- `classify_qualifier()`: Categorize quality codes
- `filter_by_*()`: Date, station, parameter filtering
- `get_quality_metrics()`: Calculate % clean, flagged, etc.
- `quality_by_station()`: Station-level aggregation
- `quality_by_year()`: Temporal aggregation
- `get_qualifier_distribution()`: Code frequency analysis
- `station_qualifier_matrix()`: Crosstab for heatmap

**visualizations.py**:
- `qualifier_distribution_chart()`: Bar chart of codes
- `quality_timeline_chart()`: Monthly trend line
- `station_quality_heatmap()`: Station × Qualifier heatmap
- `parameter_quality_chart()`: Parameter flagging ranking
- `create_geospatial_map()`: Folium map with stations
- `completeness_matrix()`: Station-parameter coverage

**filters.py**:
- `global_sidebar_filters()`: Build all sidebar controls
- `apply_global_filters()`: Apply filters to dataframe
- `dataframe_summary_sidebar()`: Display filtered data summary

## Caching Strategy

All data loads use `@st.cache_data` for performance:
- First load: ~2-3 seconds (imports + CSV read for 247K records)
- Subsequent loads: <100ms (cached)
- Cache invalidated when notebook regenerates CSVs (manual refresh)

**Performance Notes**:
- Heatmaps limited to top 30 stations for readability & responsiveness
- Filters applied client-side (no database required)
- Streamlit Cloud free tier: supports ~5 concurrent users

## Roadmap

### Phase 2 (Advanced Analytics)
- [ ] Trend line fitting (polynomial, linear) with R² and p-values
- [ ] Anomaly detection (IQR, z-score, isolation forest)
- [ ] Cross-parameter correlation heatmaps
- [ ] Station multi-factor ranking (quality + activity + completeness)
- [ ] Export to CSV/PDF
- [ ] Monitoring program comparisons (if data available)

### Phase 3 (Scaling)
- [ ] SQLite backend for >1M records
- [ ] Real-time refresh scheduling
- [ ] User authentication (Streamlit Cloud secrets)
- [ ] Custom alerts & parametrized thresholds
- [ ] Long-running computation workers

## Deployment

### Local Development
```bash
cd streamlit_app
streamlit run app.py
```

### Streamlit Cloud
1. Push code to GitHub
2. Connect repo to Streamlit Cloud
3. Deploy with: `streamlit run streamlit_app/app.py`

**Required environment variables** (none in MVP; add in auth Phase):
- (Future: API keys, secrets.toml)

## Troubleshooting

### "ModuleNotFoundError" on import
```bash
# Ensure you're in streamlit_app directory
cd streamlit_app
pip install -r requirements.txt
```

### Map not loading
- Check that `LatitudeDecimalDegrees` and `LongitudeDecimalDegrees` columns exist in CSV
- Verify Folium installation: `pip install folium streamlit-folium`

### Dashboard very slow
- Check if date range filter is too large
- Reduce # of stations/parameters selected
- Consider SQLite backend (Phase 3)

### Data not updated
- Verify notebooks have run and saved CSVs to `../output/`
- Restart Streamlit: `Ctrl+C` and rerun `streamlit run app.py`
- Or clear cache: `Delete .streamlit/cache` folder

## Configuration

Edit `.streamlit/config.toml` to customize:
- **Theme colors**: Primary, background, text
- **Layout**: Wide mode (default), centered
- **Font**: Sans serif (default)

## Dependencies

- **streamlit**: Web app framework
- **pandas**: Data manipulation
- **plotly**: Interactive charts
- **folium**: Geospatial maps
- **numpy, matplotlib, seaborn, scipy, scikit-learn**: Analytics & visualization

See `requirements.txt` for versions.

## Data Quality Notes

**Version A (Strict)**:
- Excludes: SUS, RER|SUS, HT|RER|SUS, HT|SUS
- Use for: Trend analysis, regulatory reporting
- 246,052 records (99.6%)

**Version B (Balanced)**:
- Excludes: SUS-combined codes only
- Includes: HT, DR, SPNF, OBS, FSE, RER, EST (flagged but acceptable)
- Use for: Exploratory analysis, cross-study comparisons
- 246,052 records (99.6%)

**Version C (Full)**:
- Includes: All 247,121 records with quality indicators
- Use for: Quality landscape, sensitivity testing, outlier analysis
- 247,121 records (100%)

## Dashboard Metrics

- **Total Records**: 247,121
- **Time Period**: 2020-01-06 to 2023-12-19 (4 years)
- **Stations**: 174 unique monitoring locations
- **Parameters**: 91 water quality variables
- **Qualifier Codes**: 16 unique quality indicators
- **Baseline Quality**: 96.5% clean (no flags)

## Support & Documentation

- **Reference Docs**: See `../data_quality_analysis.md`, `../unit_of_analysis.md`, `../TECHNICAL_IMPLEMENTATION_GUIDE.md`
- **Notebook Specs**: See `../notebooks/01_data_description_and_quality.ipynb`, `02_temporal_trends.ipynb`
- **Dashboard Plan**: See `/memories/session/streamlit_dashboard_plan.md`

---

**Status**: MVP v0.2 (2026-05-18) | Phase 1: Project Foundation ✅ | Phase 1.5: Surface Water Analytics Complete ✅ | Phase 2: Advanced Features (TBD)
