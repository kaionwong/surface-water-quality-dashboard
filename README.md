# Surface Water Quality Dashboard

An interactive Python dashboard for assessing data quality and integrity of incoming surface water quality monitoring data across Alberta. This project enables scientists, data stewards, and field staff to easily review data, identify issues, and make informed decisions about data trustworthiness.

## Assignment Overview

### Objective
Develop an interactive dashboard to assess and visualize 3 years (2020-2023) of water quality data from monitoring stations across Alberta with unknown data quality, enabling stakeholders to identify data issues and assess station reliability.

### Core Components

#### 1. Data Visualization & Exploration
- **Interactive filtering**: Date ranges, regions of interest, water quality parameters
- **Guideline reference limits**: Built-in exceedance visualization plus custom limit capabilities
- **Time series analysis**: Temporal trends and patterns for selected stations/parameters
- **Multi-parameter support**: Simultaneous analysis of multiple water quality variables

#### 2. Data Quality Assessment & Trend Analysis
Comprehensive data quality scoring across 10 dimensions:

- **Completeness**: Missing values, incomplete records, unusable rows (target: <5% missing)
- **Validity**: Chemical plausibility (pH 0-14, temperature ranges, non-negative concentrations)
- **Detection Limit Quality**: Censoring patterns and method detection limit consistency
- **Temporal Consistency**: Unrealistic jumps, sampling frequency regularity
- **Consistency (Units/Methods)**: Unit code and method code consistency across records
- **Outlier Detection**: Z-score, IQR-based, and rolling window anomaly detection
- **QA/QC Flags**: Analysis of flagged results and lab reliability patterns
- **Spatial Consistency**: Duplicate coordinates, basin mismatches, geographic clustering
- **Sampling Coverage**: Temporal coverage, gaps in data, sampling frequency
- **Parameter Coverage**: Parameter availability per station

**Composite Data Quality Score**:
```
Quality Score = 100 - sum(weighted penalties)
- Completeness: 25%
- Validity: 20%
- Outliers: 20%
- QA/QC Flags: 15%
- Temporal Consistency: 10%
- Method Stability: 10%

Classification:
🟢 Good (80-100)
🟡 Moderate (50-79)
🔴 Poor (<50)
```

**Top Stations of Concern Ranking**:
Identifies priority stations for investigation based on concern score incorporating missing data rate, outlier frequency, QC flags, and temporal irregularities.

#### 3. Spatial Risk Map
- **Station markers** with color-coded data quality assessment
- **Interactive tooltips**: Quality score breakdown, parameter counts, recent issues
- **Basin/Region filtering**: Geographic context for trend analysis
- **Risk visualization**: Spatial patterns of data quality across Alberta

### Optional Enhancements
- Data quality trend over time (yearly evolution)
- Lab/Method performance comparison
- Parameter-specific quality scorecards
- Seasonal decomposition analysis
- Statistical anomaly detection (Isolation Forest, Local Outlier Factor)

## Prerequisites

- Python 3.8+
- Virtual Environment (configured at `C:\Users\kai.wong\Dev\virtual_env\venv_surface_water_quality_dashboard`)

## Setup Instructions

### 1. Activate the Virtual Environment

```bash
C:\Users\kai.wong\Dev\virtual_env\venv_surface_water_quality_dashboard\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## Project Structure

```
surface-water-quality-dashboard/
├── README.md
├── .gitignore
├── requirements.txt
├── data/
│   ├── raw/                           # Raw input data (2020-2023)
│   └── processed/                     # Cleaned/validated data
├── src/
│   ├── etl/
│   │   ├── data_loader.py            # Data ingestion
│   │   ├── data_cleaner.py           # Validation & cleaning
│   │   └── data_validator.py         # Completeness, validity checks
│   ├── quality_assessment/
│   │   ├── quality_scorer.py         # Composite quality scoring
│   │   ├── outlier_detection.py      # Anomaly detection
│   │   ├── consistency_checks.py     # Temporal, unit, method consistency
│   │   └── concern_ranking.py        # Top stations identification
│   ├── visualization/
│   │   ├── exploratory_plots.py      # Time series, distributions
│   │   ├── spatial_map.py            # Geographic visualization
│   │   └── quality_dashboard.py      # Quality assessment charts
│   └── dashboard/
│       └── app.py                     # Main Streamlit application
├── output/
│   ├── quality_reports/              # Station quality assessments
│   ├── findings_summary.md           # Key findings & recommendations
│   └── visualizations/               # Exported charts/maps
└── tests/
    ├── test_data_loader.py
    ├── test_quality_scorer.py
    └── test_validation.py
```

## Running the Dashboard

```bash
# From project root with venv activated
streamlit run src/dashboard/app.py
```

The dashboard will start at `http://localhost:8501`

## Development Workflow

### 1. Data Exploration Phase
- Load raw water quality data (2020-2023)
- Identify key variables: Station, SampleDateTime, VariableName, MeasurementValue, etc.
- Profile dataset completeness and outliers
- Document data schema and assumptions

### 2. ETL & Validation Phase
- Implement completeness checks (missing fields, null values)
- Implement validity checks (domain constraints per parameter)
- Handle censored values and detection limits
- Standardize units and variable naming
- Flag QA/QC issues with audit trail

### 3. Quality Assessment Phase
- Build 10-dimension quality scoring framework
- Implement composite scoring algorithm
- Calculate per-station quality metrics
- Rank stations by concern priority
- Generate quality assessment reports

### 4. Visualization Phase
- Create time series plotting with guideline overlays
- Build interactive parameter/date/region filters
- Develop spatial map with color-coded quality markers
- Create summary statistics and trend visualizations
- Link visualizations to underlying quality assessments

### 5. Dashboard Integration Phase
- Structure Streamlit multi-page application
- Add interactive filtering and drill-down capabilities
- Optimize performance for large datasets
- Add user guidance and documentation tabs

## Key Deliverables

### 1. Interactive Dashboard
- **Requirements**: Functional Streamlit application
- **Features**: All 3 core components + optional enhancements
- **Accessibility**: Clear UI, intuitive navigation, help documentation
- **Files needed**: Source code + requirements.txt + instructions

### 2. Written Summary (1-page maximum)
- **Contents**: Key findings from data quality assessment
- **Analysis**: Interpretation of dashboard insights
- **Recommendations**: Actionable improvements for surface water data quality
- **AI disclosure**: Reference any AI tools used in development

## Data Quality Dimensions Explained

### Completeness
- Percentage of missing `MeasurementValue`, `SampleDateTime`, `Station`, coordinates, `VariableName`
- Percentage of unusable rows (missing critical fields)
- **Target**: < 5% missing for reliable stations

### Validity
- Chemical plausibility checks: pH 0-14, temperature -5 to 40°C, concentrations ≥ 0
- Flag absurd spikes (e.g., TDS > 500,000 mg/L)
- Domain-specific constraints per parameter

### Detection Limits
- Proportion of values below detection limit per parameter/station
- Method detection limit consistency over time
- Censoring pattern impact on analysis

### Consistency
- **Temporal**: Unrealistic jumps in time series (z-score flagging)
- **Units**: Same variable reported in different units
- **Methods**: Parameter method code consistency and stability

### Outlier & Anomaly Detection
- Z-score based (values > 3σ from mean)
- IQR-based (values outside 1.5 × IQR)
- Rolling window spike detection
- Seasonal decomposition (optional advanced)

### QA/QC & Lab Reliability
- Analysis of built-in flags: `QCSampleFlag`, `MeasurementFlag`, `MeasurementQualifier`
- Lab and method code performance comparison
- Flagged result patterns and trends

### Spatial Consistency
- Duplicate station coordinates
- Geographic basin mismatches
- Isolated outlier station clusters

### Sampling Coverage
- Samples per year per station
- Sampling gaps and frequency
- Stations with minimal data (low reliability)

### Parameter Coverage
- Parameter diversity per station
- Missing key analytes (nutrients, major ions, etc.)
- Station suitability for comprehensive assessment

## Technologies Used

- **Data Processing**: `pandas`, `numpy`, `scipy`
- **Visualization**: `streamlit`, `plotly`, `matplotlib`, `seaborn`, `altair`
- **Time Series**: `statsmodels`, `pmdarima`
- **Database**: `pyodbc`, `oracledb` (for Oracle DB connectivity)
- **Environment**: `python-dotenv`

## Testing

```bash
# Run unit tests for data quality scoring
pytest tests/test_quality_scorer.py

# Run validation tests
pytest tests/test_validation.py

# Run data loader tests
pytest tests/test_data_loader.py
```


## Notes

- Data source: 3-year (2020-2023) water quality dataset from Alberta monitoring stations
- Data quality is composite: completeness + validity + consistency + reliability + usability
- Focus on decision-making value: recommendations should be actionable
- Consider AI tool usage and document accordingly

## Environment Configuration

Create a `.env` file for database credentials and configuration:
```
DATABASE_HOST=your_oracle_host
DATABASE_PORT=1521
DATABASE_SID=your_sid
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password
```

## Contributing

When adding features:
1. Follow PEP 8 style guide
2. Add comprehensive docstrings
3. Update relevant tests
4. Document changes in commit messages

## License

[Add license information here]
