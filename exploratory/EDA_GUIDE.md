# Exploratory Data Analysis Setup Guide

## ⚡ Quick Start - Run with Python

### Complete EDA Synthesis (All 5 Modules)

**Option 1: Using PowerShell/Bash** (Recommended)

Activate the correct virtual environment first:
```bash
C:\Users\kai.wong\Dev\virtual_env\venv_etl_for_ecol_analytics\Scripts\activate.bat
```

Then run:
```bash
cd "C:\Users\kai.wong\OneDrive - Government of Alberta\_work\project\etl_for_testing\surface-water-quality-dashboard"
python -m exploratory
```

**Option 2: Using Batch Script**
```bash
# From project root
.\run_eda_quickstart.bat
```

**Option 3: Python Direct**
```bash
python run_eda.py
```

**Option 4: Direct Module**
```bash
python exploratory/eda_notebook.py
```

---

## Run Individual Modules

```bash
# First activate venv (if not already active)
C:\Users\kai.wong\Dev\virtual_env\venv_etl_for_ecol_analytics\Scripts\activate.bat

python -m exploratory profiling    # Data profiling
python -m exploratory missing      # Missing data analysis
python -m exploratory stats        # Statistical tests
python -m exploratory quality      # Quality issues detection
```

---

## Virtual Environment

**Location**: `C:\Users\kai.wong\Dev\virtual_env\venv_etl_for_ecol_analytics`
**Python**: 3.13.13 (✅ Has all pre-built wheels)
**Status**: ✅ Ready (pandas, numpy, scipy, plotly, all dependencies installed)

**Why this venv?**
- Python 3.15.0 alpha has no pre-built wheels (requires C compiler)
- Python 3.13.13 has pre-built wheels for all packages → fast, reliable installs
- All dependencies already installed and tested ✓

**Activate manually if needed:**
```bash
C:\Users\kai.wong\Dev\virtual_env\venv_etl_for_ecol_analytics\Scripts\activate.bat
```

---

## 5 Core Analysis Modules

| # | Module | Command | Purpose |
|---|--------|---------|---------|
| 1 | **Data Profiling** | `python -m exploratory profiling` | Dataset shape, types, memory, completeness |
| 2 | **Missing Data Analysis** | `python -m exploratory missing` | Missing patterns, coverage, spatial gaps |
| 3 | **Statistical Tests** | `python -m exploratory stats` | Normality tests, distributions, trends |
| 4 | **Quality Issues Detection** | `python -m exploratory quality` | Validity violations, outliers, anomalies |
| 5 | **EDA Executive Synthesis** | `python -m exploratory` | All findings combined + recommendations |

---

## Interactive Jupyter Notebook

For interactive exploration and visualization:

```bash
# Ensure jupyter is installed
pip install jupyter

# Launch notebook
jupyter notebook notebooks/eda/eda_interactive.ipynb
```

**In notebook**, run these cells to execute analyses:

```python
# Cell 1: Setup imports
import sys
sys.path.insert(0, r'C:\Users\kai.wong\OneDrive - Government of Alberta\_work\project\etl_for_testing\surface-water-quality-dashboard')

from exploratory import (
    data_profiling,
    missing_data_analysis, 
    statistical_tests,
    quality_issues,
    eda_notebook
)

# Cell 2: Run data profiling
profiling_results = data_profiling.main(nrows=10000)

# Cell 3: Run missing data analysis  
missing_results = missing_data_analysis.main(nrows=10000)

# Cell 4: Run statistical tests
stats_results = statistical_tests.main(nrows=10000)

# Cell 5: Run quality issues
quality_results = quality_issues.main(nrows=10000)

# Cell 6: Run complete synthesis
complete_results = eda_notebook.main(nrows=10000)

print("✓ All analyses complete!")
```

---

## Advanced: Run Specific Module in Python

```python
# In your own Python script
import sys
sys.path.insert(0, r'C:\path\to\surface-water-quality-dashboard')

from exploratory import data_profiling

# Run with custom row limit
results = data_profiling.main(nrows=50000)

# Results dict contains:
# - results['dataset_profile']  — Dataset overview
# - results['column_analysis']  — Column-by-column stats
# - results['numeric_summaries'] — Statistical summaries
# - results['dataframe']        — Loaded DataFrame
```

---

## Output Files

All results saved to: **`output/eda_outputs/`**

### Key Deliverables

| File | Type | Purpose |
|------|------|---------|
| `executive_summary.txt` | Text | Complete findings, quality assessment, recommendations |
| `synthesis.json` | JSON | Structured results for downstream processing |
| `data_profiling_*.csv` | CSV | Column analysis, numeric summaries |
| `missing_data_%.csv` | CSV | Missing value statistics by column |
| `statistical_tests_*.csv` | CSV | Normality tests, trend analysis results |
| `quality_issues_*.csv` | CSV | Validity violations, outlier counts |
| `quality_issues_*.json` | JSON | Duplicates and suspicious patterns |

Execute and review:
```bash
python -m exploratory
# Results now in: output/eda_outputs/

# View executive summary
type output/eda_outputs/executive_summary.txt
```

---

## Data Quality Dimensions Analyzed

The EDA covers all 10 quality dimensions:

✅ **Completeness** — Missing values per column/station  
✅ **Validity** — Physically impossible values (pH > 14, negative concentrations, etc.)  
✅ **Detection Limits** — Proportion of values below detection limit  
✅ **Temporal Consistency** — Unrealistic jumps, sampling frequency regularity  
✅ **Unit Consistency** — Same parameter reported in different units  
✅ **Method Consistency** — Parameter method code consistency  
✅ **Outliers & Anomalies** — Z-score, IQR-based detection  
✅ **QA/QC Flags** — Lab reliability, flagged results patterns  
✅ **Spatial Consistency** — Geographic patterns, station clustering  
✅ **Sampling Coverage** — Temporal coverage, gaps, frequency  

---

## Project Structure

```
surface-water-quality-dashboard/
├── run_eda.py                         # ⭐ Standalone runner (Option 2)
├── README.md                          # Project documentation
├── requirements.txt                   # Python dependencies
│
├── exploratory/                       # ⭐ Main EDA package
│   ├── __init__.py
│   ├── __main__.py                    # Entry point for: python -m exploratory
│   ├── config.py                      # Domain constraints, thresholds
│   ├── utils.py                       # Shared utility functions
│   ├── data_profiling.py              # Module 1: Dataset overview
│   ├── missing_data_analysis.py       # Module 2: Coverage & gaps
│   ├── statistical_tests.py           # Module 3: Distributions & trends
│   ├── quality_issues.py              # Module 4: Validity & anomalies
│   └── eda_notebook.py                # Module 5: Executive synthesis
│
├── notebooks/
│   └── eda/                           # Jupyter notebooks (interactive)
│       └── eda_interactive.ipynb      # (Create as needed)
│
├── data/
│   └── raw/
│       └── alberta_surface_water_quality_data.csv  (50MB+)
│
└── output/
    └── eda_outputs/                   # CSV, JSON, HTML results
```

**Run using (choose one):**
1. `python -m exploratory` — Python module (recommended)
2. `python run_eda.py` — Standalone script
3. `jupyter notebook notebooks/eda/eda_interactive.ipynb` — Interactive notebook

---

## Configuration

### Customizable Parameters

File: `src/exploratory/config.py`

- **Parameter Constraints**: pH (0-14), Temperature (-5 to 40°C), etc.
- **Completeness Targets**: What % missing = Excellent/Good/Poor
- **Outlier Thresholds**: Z-score (3.0), IQR multiplier (1.5)
- **Detection Limit Alerts**: Critical (>90% below DL), High (70-90%), etc.
- **Sampling Frequency**: Good (12+/yr), Moderate (4+/yr), Poor (<4/yr)

Modify these values if Alberta water quality standards differ from defaults.

---

## Next Steps After EDA

1. **Review** `output/eda_outputs/executive_summary.txt`
2. **Parse** `output/eda_outputs/synthesis.json` for structured data
3. **Visualize** CSV results in analysis tool of choice
4. **Feed into quality assessment phase** to weight stations in dashboard
5. **Build interactive dashboard** with Streamlit or similar

---

## Troubleshooting

### ImportError: No module named 'exploratory'

Ensure you run from project root:
```bash
cd "C:\Users\kai.wong\OneDrive - Government of Alberta\_work\project\etl_for_testing\surface-water-quality-dashboard"
python -m exploratory
```

### ModuleNotFoundError: No module named 'pandas', 'numpy', etc.

Install dependencies:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install pandas numpy scipy plotly matplotlib seaborn statsmodels
```

### Memory issues with large dataset

Use the `nrows` parameter to limit rows:
```python
from exploratory import data_profiling
data_profiling.main(nrows=50000)  # Load only 50k rows
```

Or modify `CHUNK_SIZE` in `exploratory/config.py` (default: 50,000).

### "ModuleNotFoundError: MATLAB engine..." or other scipy/statsmodels issues

These are optional. Core analyses work without them.
- Try running individual module that's failing
- Check Python version compatibility: `python --version`
- Reinstall scipy: `pip install --upgrade scipy`

### CSV file not found

Verify data location:
```bash
ls "data/raw/alberta_surface_water_quality_data.csv"
```

If not found, update `ALBERTA_DATA_FILE` in `exploratory/config.py`

---

## Architecture Highlights

✅ **Memory-Efficient**: Chunked loading for 50MB+ CSV  
✅ **Adaptive**: Auto-detects column names; customizable via config  
✅ **Comprehensive**: All 10 quality dimensions in one run  
✅ **Modular**: Run individually or as synthesis pipeline  
✅ **Reproducible**: Configs and thresholds documented and adjustable  
✅ **Actionable**: Top concerns ranked for prioritization  

---

*For more details, see README.md and individual module docstrings.*
