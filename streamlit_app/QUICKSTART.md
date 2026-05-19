# 🚀 Quick Start Guide

## Step 1: Python Setup (If needed)

Check your Python version:
```bash
python --version
```

✅ **Required**: Python 3.12 or 3.13  
❌ **Not supported**: Python 3.15 alpha (lacks pre-built wheels)

If you have Python 3.15, download Python 3.12 from [python.org](https://www.python.org/downloads/)

---

## Step 2: Install Dependencies (One-time)

Open PowerShell or terminal in the `streamlit_app` folder:

```bash
cd "c:\Users\kai.wong\OneDrive - Government of Alberta\_work\project\etl_for_testing\surface-water-quality-dashboard\streamlit_app"

pip install -r requirements.txt
```

⏱️ Takes ~2-3 minutes the first time

---

## Step 3: Run the Dashboard

```bash
streamlit run app.py
```

✅ Browser opens automatically to `http://localhost:8501`

---

## Step 4: Explore

### Page 1: Surface water quality analytics and trends ✅ (Complete)
Fully interactive data exploration interface:
- **Statistical Metrics**: Real-time summary statistics (Count, Mean, Median, Std dev, Min, Max, % removed by filters, Number of stations)
- **Quantile Map**: Explore data distribution across stations with time-series visualization
  - Drag the time slider to see how measurements change over time
  - Switch between station points (color-coded by quantile) and heat map views
  - Adjust aggregation period (Weekly/Monthly/Quarterly/Yearly/Seasonal)
- **Threshold Map**: Find stations exceeding or meeting a target value
  - Use the slider to set your threshold (min, median [default], max)
  - Toggle between "above" and "below" conditions
  - Visualize time-varying data with the period slider
- **Trend Chart**: See temporal patterns
  - Mean, median, and inter-quartile range (IQR) over time
- **Sidebar Filters**:
  - Select variable (parameter to analyze)
  - Choose data quality filter (Exclude unreliable | Exclude unreliable + potentially unreliable | All data)
  - Select stations (All or custom multiselect)
  - Set global date range

**Page 2**: Data Quality Analysis (KPIs, qualifier distribution, heatmaps, trends) ⭐
**Page 3**: Unit of Analysis (drill-down by station/parameter/time)
**Page 4**: Geospatial Analysis (interactive map)
**Page 5**: Advanced Analytics (placeholder)

---

## Stop the Dashboard

Press `Ctrl+C` in the terminal

---

## Update Data

1. Run notebooks in `../notebooks/` folder
2. This generates new CSVs in `../output/`
3. Restart dashboard (dashboard auto-reloads cache)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` in streamlit_app folder |
| Map not showing | Verify CSVs exist: `../output/dataset_version_*.csv` |
| Very slow loading | Try narrower date range or fewer stations (sidebar filters) |
| Python version error | Switch to Python 3.12: `python --version` → download if needed |
| Data not updated | Re-run notebooks, then restart dashboard |

---

## Next Steps

- 📚 Read full docs: `README.md`
- 🎯 View design plan: `/memories/session/streamlit_dashboard_plan.md`
- 📊 Explore data specs: `../data_quality_analysis.md`

---

**Questions?** Check `README.md` for comprehensive documentation.
