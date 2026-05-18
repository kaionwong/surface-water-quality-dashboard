# Run complete EDA pipeline
python run_eda.py

# Run individual modules
python -m exploratory profiling
python -m exploratory missing
python -m exploratory stats
python -m exploratory quality

# Or launch Streamlit dashboard (when ready)
streamlit run app.py