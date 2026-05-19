# Alberta Surface Water Quality Dashboard

Interactive Streamlit dashboard for analyzing 247,121 water quality measurements across 174 Alberta monitoring stations (2020-2023).

## Live App

**Deployed on Streamlit Cloud**: https://surface-water-quality-dashboard-8kkvmcckcfq5rarcsrgxy4.streamlit.app/

## Quick Start

### Run the Dashboard
```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```
Then open your browser to `http://localhost:8501`

## What's in This Repository

**Main Goal**: Provide an interactive, multi-page dashboard to explore water quality trends, identify data quality issues, and analyze patterns across Alberta's monitoring stations.

### Dashboard Pages
- **Page 1**: Surface Water Quality Analytics & Trends (completed)
  - Real-time statistical summaries, quantile visualizations, temporal trends
  - Interactive threshold maps and quality filtering
- **Page 2**: Data Quality Analysis 
  - Qualifier code distribution, station/variable ranking by quality issues
  - Geospatial quality heatmaps
- **Page 3+**: Additional analysis pages (in development)

### Core Components
- `streamlit_app/app.py` — Main dashboard application
- `streamlit_app/data/` — Data loading and processing logic
- `streamlit_app/modules/` — Visualization builders (Folium, Plotly)
- `exploratory/` — Standalone EDA scripts (data profiling, quality analysis)
- Configuration files:
  - `unit_definitions.yaml` — Unit conversions for all parameters
  - `station_profiles.yaml` — Metadata for all 174 stations
  - `data_quality_analysis.md` — Qualifier codes and filtering guidance

### Dataset Overview
| Metric | Value |
|--------|-------|
| Total Records | 247,121 measurements |
| Stations | 174 monitoring locations |
| Parameters | 91 water quality variables |
| Time Period | Jan 2020 – Dec 2023 (4 years) |
| Data Quality | 96.5% clean (no flags) |
| Flagged Records | 3.5% (17 unique qualifier codes) |

## Setup & Requirements

- Python 3.12+
- See `streamlit_app/requirements.txt` for dependencies

### Installation
```bash
python -m venv venv
source venv/Scripts/activate  # or: venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Run EDA Scripts
```bash
python exploratory/data_profiling.py
python exploratory/quality_issues.py
# ... other scripts in exploratory/
```

## Key Files

- **Data Quality**: `data_quality_analysis.md` — All 17 qualifier codes explained
- **Data Guide**: `data_documentation.md` — Data source and collection methods
- **Dashboard Help**: `streamlit_app/README.md` — Detailed dashboard documentation

---

**Last Updated**: May 19, 2026 | **Data**: 247,121 records, 174 stations, 2020-2023
