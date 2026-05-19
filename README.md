# Alberta Surface Water Quality Dashboard

Interactive Streamlit dashboard with exploratory data analysis for 247,121 water quality measurements (2020-2023) across 174 Alberta monitoring stations.

**Status**: Phase 1.5 Complete ✅ — Surface water quality analytics section fully functional and deployed.

## Quick Start

### Run the Dashboard
```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```
See [streamlit_app/QUICKSTART.md](streamlit_app/QUICKSTART.md) for detailed setup. Full dashboard docs: [streamlit_app/README.md](streamlit_app/README.md).

### Run Exploratory Analysis
```bash
# From project root with Python 3.12+
python exploratory/data_profiling.py
python exploratory/missing_data_analysis.py
python exploratory/quality_issues.py
```

## Project Overview

### Dataset
- **Records**: 247,121 measurements
- **Stations**: 174 monitoring locations
- **Parameters**: 91 water quality variables
- **Period**: January 6, 2020 – December 19, 2023 (4 years)
- **Basins**: 8 major river basins across Alberta
- **Quality**: 96.5% clean (no flags) | 3.5% flagged records

### What's Included

#### 1. Interactive Dashboard (Streamlit) ✅
**Page 1: Surface Water Quality Analytics & Trends** (Completed)
- Real-time statistical summaries (Count, Mean, Median, Std dev, Min, Max, % removed by filters)
- Quantile-based station visualizations with time-series exploration
- Binary threshold maps with interactive slider controls
- Temporal trend analysis with percentile bands
- Multi-level data quality filtering (3 options)
- Unit integration across all displays

**Pages 2-5**: Data Quality Analysis, Unit of Analysis, Geospatial Analysis, Advanced Analytics (In Development)

#### 2. Exploratory Data Analysis (Python)
Standalone modules in `exploratory/`:
- **data_profiling.py**: Shape, types, ranges, summary statistics
- **missing_data_analysis.py**: Missing value patterns, temporal/spatial gaps
- **quality_issues.py**: Anomalies, validity issues, outlier detection
- **statistical_tests.py**: Distribution analysis, trend testing
- **temporal_analysis.py**: Seasonality, autocorrelation, time-series patterns

#### 3. Data Documentation
Configuration files explaining the dataset:
- **unit_definitions.yaml**: Unit mappings and conversions for all 91 VmvCodes
- **station_profiles.yaml**: Metadata for all 174 stations (tiers, coverage, basin)
- **variable_catalog.yaml**: Parameter definitions, aggregation methods, expected ranges

Reference guides:
- **data_quality_analysis.md**: All 17 qualifier codes + filtering recommendations
- **data_documentation.md**: Data source, collection methods, portal info
- **unit_of_analysis.md**: Data relationships and cardinality assumptions

## Project Structure

```
surface-water-quality-dashboard/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── streamlit_app/                     # Dashboard (Phase 1.5 ✅)
│   ├── app.py                         # Main Streamlit application
│   ├── README.md                      # Dashboard documentation
│   ├── QUICKSTART.md                  # Quick start guide
│   ├── modules/
│   │   ├── visualizations.py          # Folium & Plotly builders
│   │   └── filters.py                 # Sidebar controls
│   └── data/
│       ├── data_loader.py             # CSV loading & caching
│       └── data_processor.py           # Filtering, aggregation, quality classification
├── exploratory/                       # EDA modules (Python scripts)
│   ├── data_profiling.py
│   ├── missing_data_analysis.py
│   ├── quality_issues.py
│   ├── statistical_tests.py
│   └── temporal_analysis.py
├── notebooks/                         # Jupyter analysis notebooks
├── data/                              # Data directory
│   └── raw/                           # CSV files (Version A/B/C)
├── output/                            # Analysis outputs
│   ├── eda_outputs/                   # EDA results & visualizations
│   └── statistical_tests/             # Statistical analysis results
├── unit_definitions.yaml              # Unit reference & conversions
├── station_profiles.yaml              # Station metadata & tiers
├── variable_catalog.yaml              # Parameter definitions
├── data_quality_analysis.md           # Qualifier code mappings & filtering
├── data_documentation.md              # Data source & collection info
├── unit_of_analysis.md                # Data structure & cardinality
└── README_PHASE_2.md                  # Detailed reference tables & guidance
```

## Key Statistics

| Metric | Value | Interpretation |
|--------|-------|-----------------|
| **Data Completeness** | 98.18% | Only ~600 rule violations across 247K records |
| **Tier 1 Stations** | 173 (99.4%) | Comprehensive 12+ variable coverage |
| **Monthly+ Frequency** | 165 stations (94.8%) | Regular, consistent sampling |
| **Basin Coverage** | 8 basins | 15-48 stations per basin |
| **Parameter Coverage** | Median 64/91 | Most stations measure majority of variables |
| **Clean Data (No Flags)** | 238K (96.5%) | Excellent baseline quality |
| **Flagged Records** | 8,656 (3.5%) | 17 unique qualifier codes documented |

## How to Use Documentation

### I want to analyze water quality trends at a specific station
1. Check station viability & metadata: `station_profiles.yaml`
2. Understand the parameters: `variable_catalog.yaml`
3. Verify units & conversions: `unit_definitions.yaml`
4. Review data quality guidelines: `data_quality_analysis.md`

### I want to compare multiple stations
1. Select comparable stations (same basin, similar frequency): `station_profiles.yaml`
2. Standardize measurements (same units): `unit_definitions.yaml`
3. Review parameter definitions: `variable_catalog.yaml`

### I need to filter or handle flagged data
1. Understand the 17 qualifier codes: `data_quality_analysis.md`
2. Choose filtering strategy (high-quality, exploratory, all-data)
3. Apply parameter-specific rules as needed

### I want to understand data structure
1. Review data relationships & cardinality: `unit_of_analysis.md`
2. Check station/basin distribution: `station_profiles.yaml`
3. See full reference tables: `README_PHASE_2.md`

## Technologies

- **Dashboard**: Streamlit, Folium (maps), Plotly (charts)
- **Data**: Pandas, NumPy, SciPy
- **EDA**: Matplotlib, Seaborn, StatsModels
- **Caching**: Streamlit's built-in caching for performance

## Setup & Installation

### Prerequisites
- Python 3.12+
- Git

### Installation
```bash
# Clone/navigate to project root
cd surface-water-quality-dashboard

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/Scripts/activate  # Windows
# or: source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Run Dashboard
```bash
cd streamlit_app
streamlit run app.py
```
Open browser to `http://localhost:8501` (or use default port)

### Run EDA
```bash
# From project root
python exploratory/data_profiling.py
python exploratory/missing_data_analysis.py
# ... etc
```

## Data Quality Highlights

### What's Good ✅
- 98.18% compliance with quality rules
- Consistent station coordinates & names
- Standardized field naming conventions
- 4-year continuous monitoring (173 of 174 stations)
- Comprehensive parameter coverage

### Known Issues ⚠️
- **S1 (Unit Inconsistency)**: 4 stations with dual units (fixable via conversion per `unit_definitions.yaml`)
- **M2 (Out-of-Range Values)**: 596 records with physiologically impossible values (recommend exclusion for trend analysis)
- **Recommended Action**: Document quality choices in methodology; use `data_quality_analysis.md` for filtering guidance

## Next Steps (Phase 2+)

- [ ] Pages 2-5 dashboard sections (Data Quality, Unit Analysis, Geospatial, Advanced)
- [ ] Automated quality alerting and monitoring
- [ ] Real-time or scheduled data updates
- [ ] Statistical anomaly detection (Isolation Forest, LOF)
- [ ] Parameter-specific quality scorecards
- [ ] Lab/method performance comparison
- [ ] Export to PNG/PDF/CSV capabilities

## Support & References

- **Dashboard Help**: [streamlit_app/README.md](streamlit_app/README.md)
- **Quick Start**: [streamlit_app/QUICKSTART.md](streamlit_app/QUICKSTART.md)
- **Data Guide**: [README_PHASE_2.md](README_PHASE_2.md) (full reference tables)
- **Quality Details**: [data_quality_analysis.md](data_quality_analysis.md)
- **Data Origin**: [data_documentation.md](data_documentation.md)

---

**Last Updated**: May 18, 2026 | **Version**: 0.2 MVP | **Data**: 247,121 records, 174 stations, 2020-2023
