"""Configuration and domain constraints for water quality data analysis."""

import os

# File paths - exploratory is at project root level
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_PATH = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED_PATH = os.path.join(PROJECT_ROOT, "data", "processed")
OUTPUT_EDA_PATH = os.path.join(PROJECT_ROOT, "output", "eda_outputs")
OUTPUT_STATS_PATH = os.path.join(PROJECT_ROOT, "output", "statistical_tests")

# Ensure output directories exist
for path in [OUTPUT_EDA_PATH, OUTPUT_STATS_PATH]:
    os.makedirs(path, exist_ok=True)

# Data settings
CSV_FILE = "alberta_surface_water_quality_data.csv"
ALBERTA_DATA_FILE = "alberta_surface_water_quality_data.csv"  # Alias for consistency
CHUNK_SIZE = 50000  # Rows to load at a time for large files

# Completeness targets (%)
COMPLETENESS_TARGETS = {
    "excellent": 95,  # < 5% missing
    "good": 85,       # 5-15% missing
    "poor": 0,        # > 15% missing
}

# Water quality parameter constraints (Alberta/EPA standards)
PARAMETER_CONSTRAINTS = {
    "pH": {
        "min": 0,
        "max": 14,
        "units": "pH",
        "description": "Acidity/Alkalinity",
    },
    "Temperature": {
        "min": -5,
        "max": 40,
        "units": ["°C", "Celsius"],
        "description": "Water temperature",
    },
    "Conductivity": {
        "min": 0,
        "max": 100000,
        "units": ["µS/cm", "mS/cm"],
        "description": "Electrical conductivity",
    },
    "Turbidity": {
        "min": 0,
        "max": 5000,
        "units": ["NTU", "FNU"],
        "description": "Water clarity",
    },
    "Dissolved Oxygen": {
        "min": 0,
        "max": 20,
        "units": ["mg/L", "ppm"],
        "description": "Dissolved oxygen content",
    },
    "Total Suspended Solids": {
        "min": 0,
        "max": 50000,
        "units": ["mg/L", "g/L"],
        "description": "Suspended particles",
    },
    "Nitrogen": {
        "min": 0,
        "max": 1000,
        "units": ["mg/L", "µg/L"],
        "description": "Total nitrogen",
    },
    "Phosphorus": {
        "min": 0,
        "max": 100,
        "units": ["mg/L", "µg/L"],
        "description": "Total phosphorus",
    },
}

# Outlier detection thresholds
OUTLIER_DETECTION = {
    "z_score_threshold": 3.0,      # Standard deviations from mean
    "iqr_multiplier": 1.5,         # IQR multiplier for whisker method
    "isolation_forest_contamination": 0.05,  # Expected proportion of outliers
}

# Statistical test significance level
SIGNIFICANCE_LEVEL = 0.05

# Missing data thresholds for concern ranking
MISSING_DATA_ALERT = {
    "critical": 50,  # > 50% missing → critical
    "high": 30,      # 30-50% missing → high
    "moderate": 15,  # 15-30% missing → moderate
    "low": 5,        # < 5% missing → good
}

# Sampling frequency thresholds (samples per year)
SAMPLING_FREQUENCY = {
    "good": 12,      # Monthly or better
    "moderate": 4,   # Quarterly or better
    "poor": 1,       # Less than quarterly
}

# Detection limit analysis
DETECTION_LIMIT_ALERT = {
    "critical": 90,  # > 90% < DL → critical
    "high": 70,      # 70-90% < DL → high
    "moderate": 50,  # 50-70% < DL → moderate
}

# Column name patterns to look for (adaptive to actual data structure)
EXPECTED_COLUMNS = {
    "station_id": ["Station", "StationID", "Station_ID", "SiteID", "Location"],
    "date_time": ["SampleDateTime", "Date", "DateTime", "SampleDate", "Datetime"],
    "parameter": ["VariableName", "Parameter", "Analyte", "Parameter_Name"],
    "value": ["MeasurementValue", "Value", "Result", "Concentration"],
    "unit": ["UnitCode", "Unit", "Units"],
    "latitude": ["Latitude", "Lat", "Y"],
    "longitude": ["Longitude", "Lon", "Long", "X"],
    "method": ["MethodCode", "Method", "Analysis_Method"],
    "lab": ["LabCode", "Lab", "Laboratory"],
    "flag": ["MeasurementFlag", "Flag", "QA_Flag", "QC_Flag"],
    "detection_limit": ["SampleDetectLimit", "DetectionLimit", "DL", "MDL"],
}
