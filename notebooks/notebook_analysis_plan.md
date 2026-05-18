# Notebook Analysis Plan: Trends, Quality, & Geospatial Patterns

**Date**: May 18, 2026  
**Dataset**: Alberta Surface Water Quality (2020-2023)  
**Total Measurements**: 247,121 across 174 stations  
**Objective**: Comprehensive analysis of temporal trends, data quality patterns, and geospatial variations with statistical validation

---

## Executive Overview

This analysis plan guides development of Jupyter notebooks to explore:
1. **Data Quality Landscape** - Qualifier flags, completeness, and systematic issues
2. **Temporal Trends** - Station and parameter-level changes over time
3. **Geospatial Patterns** - Basin-level variations and regional quality differences
4. **Statistical Validation** - Significance testing for observed trends and anomalies
5. **Quality-Adjusted Trends** - How filtering affects analytical conclusions

---

## Part 1: Data Preparation & Quality Foundations

### 1.1 Data Loading & Quality Profile

**Objective**: Establish baseline data quality metrics and filtering thresholds

**Guided by**:
- `data_quality_analysis.md` - Quality variable definitions and filtering strategies
- `unit_of_analysis.md` - Data structure and cardinality relationships
- `README_PHASE_2.md` - Dataset overview (174 stations, 32,264 records core dataset)

**Tasks**:

1. **Load & Validate Raw Data**
   - Load `data/raw/alberta_surface_water_quality_data.csv` (247,121 records)
   - Expected columns: StationNumber, StationName, SampleDateTime, VmvCode, MeasurementValue, MeasurementQualifier, MeasurementQualifierDescription, MethodCode, MethodDetectionLimit, LabCode, SampleComment, MeasurementComment
   - Verify data types and handle nulls

2. **Quality Profile Summary**
   ```
   Metrics to Calculate:
   - Total records and time span (2020-2023 = 4 years, 1,418 days)
   - Unique stations: 174 expected
   - Unique parameters (VmvCode): ~82 expected
   - Clean records: 238,465 (96.50%)
   - Flagged records: 8,656 (3.50%)
   - Distribution of 17 MeasurementQualifier codes
   ```

3. **Create Three Dataset Versions** (per `data_quality_analysis.md`)
   
   **Version A: High Quality (Strict Filtering)**
   - Exclude: SUS, RER|SUS, HT|RER|SUS, HT|SUS
   - Result: 246,054 records (99.6%)
   - Use for: Trend analysis, statistical tests, regulatory reporting
   
   **Version B: Medium Quality (Balanced Filtering)**
   - Exclude: Only SUS-combined codes
   - Include with flags: HT, DR, SPNF, OBS, FSE, RER, EST
   - Result: 246,054+ records (99.6%)
   - Use for: Exploratory analysis, comparative studies
   
   **Version C: Full Data (Exploratory)**
   - Include all 247,121 records with quality indicators
   - Use for: Understanding quality landscape, identifying systematic issues, sensitivity analysis

### 1.2 Cardinality Validation

**Objective**: Verify data structure assumptions before aggregation

**Reference**: `unit_of_analysis.md` Section 2 (12 cardinality assumptions)

**Required Verifications**:

| Check | Expected | Test | Action if False |
|-------|----------|------|-----------------|
| StationNumber → Station Name | 1:1 | df.groupby('StationNumber')['StationName'].nunique().max() == 1 | Investigate naming inconsistencies |
| StationNumber → (Lat, Long) | 1:1 | Check coordinate consistency | Flag coordinate conflicts |
| ProjectNumber → SampleNumber | 1:many | Expected; verify distribution | OK; document cardinality |
| SampleNumber → SampleDateTime | 1:1 | Check for duplicates | Investigate duplicate timestamps |
| VmvCode → Unit | 1:1 | Verify unit consistency per code | Check for dual-unit handling (VmvCode 6107) |
| VmvCode → MethodCode | 1:1 | Test 1:1 mapping | Flag method switching |
| MethodCode → MethodDetectionLimit | 1:1 | Test MDL consistency | Flag inconsistent MDLs |
| SampleNumber → LabCode | 1:1 | Verify single lab per sample | Flag samples with multiple labs |
| LabCode → Location | 1:1 | Map labs to locations | Create lab directory |

**Output**: Cardinality validation report with any violations flagged

---

## Part 2: Data Quality Trend Analysis

### 2.1 Quality Flag Distribution Over Time

**Objective**: Understand temporal patterns in data quality issues

**Dimensions**:

1. **By Year (2020-2023)**
   - Calculate % of flagged records per year
   - Identify if data quality improving/declining
   - Visualization: Stacked bar chart (each qualifier code by year)
   
   **Expected Insight**: Quality should improve or remain stable (good lab protocols)

2. **By Season (Quarterly)**
   - Calculate qualifier code frequency by Q1, Q2, Q3, Q4
   - Identify seasonal quality patterns
   - Expected: Summer (heat) → more HT flags; Winter (processing delays) → different patterns

3. **By Parameter Category**
   - Group VmvCodes: Nutrients (P, N), Metals (Fe, Cd, Pb), Physical (pH, DO, Temp), Microbes
   - Calculate % flagged per category per year
   - Expected: Different parameters have different quality profiles

4. **By Station Tier** (Reference: `README_PHASE_2.md`)
   - Tier 1: 173 comprehensive stations (≥12 variables, consistent 4-year coverage)
   - Tier 2: 1 moderate station
   - Calculate % flagged per tier
   - Expected: Tier 1 may have different quality patterns (more systematic)

**Specific Codes to Track**:

| Code | Trend Implication | Action if Increasing |
|------|-------------------|---------------------|
| SUS (Suspect) | Data reliability issue | Investigate lab calibration? |
| HT (Holding Time) | Processing delays/storage problems | Check sample preservation procedures |
| DR (Dilution) | More high-concentration samples | Indicates pollution events or method changes |
| SPNF (Non-Standard Procedure) | Procedural deviations | Track if new labs introduced |
| FSE (Standard Error) | Usually stable | Increases = analytical method drift |

**Visualizations**:
- Time series line chart: % flagged records over time
- Heatmap: Qualifier code frequency × Time period (year/quarter)
- Box plot: Flag distribution by quarter (2020-2023)
- Stacked area: Cumulative qualifier codes by year

### 2.2 Quality Issues by Station & Lab

**Objective**: Identify systematic quality patterns by data source

**Tasks**:

1. **Lab Performance Analysis** (Reference: `data_quality_analysis.md` LabCode section)
   - Calculate % flagged records per LabCode
   - Identify labs with consistently higher/lower quality rates
   - Statistical test: Chi-square test for association between LabCode and qualifier type
   - Expected: Some labs may have known quality profiles
   
   **Output**: Lab performance dashboard ranking labs by quality

2. **Station Quality Scores**
   - Calculate composite quality score per station:
     ```
     Quality_Score = (Clean_Records / Total_Records) × 100
     ```
   - Rank all 174 stations from highest to lowest quality
   - Create quality tiers: Excellent (>98%), Good (95-98%), Fair (90-95%), Poor (<90%)
   - Identify "Stations of Concern" (lowest quality)
   - Map: Color-code stations by quality tier
   
   **Output**: Station quality ranking matrix

3. **Geographic Clustering of Quality Issues**
   - Plot station locations (latitude/longitude)
   - Color-code by quality score
   - Test spatial autocorrelation: Moran's I
     - If I > 0, p < 0.05 → Positive clustering (nearby stations have similar quality)
     - If I < 0, p < 0.05 → Negative clustering (dispersed patterns)
   - LISA analysis: Identify hotspots (low quality clusters) and coldspots
   
   **Output**: Spatial quality pattern map + statistical testing results

### 2.3 Missing Data & Completeness Analysis

**Objective**: Understand data gaps and coverage

**Tasks**:

1. **Parameter Availability per Station**
   - Calculate which VmvCodes are measured at each station
   - Reference: `README_PHASE_2.md` shows median 64/82 parameters per station
   - Identify parameters with sparse coverage
   - Test: Chi-square goodness of fit for parameter distribution
   
   **Output**: Parameter coverage matrix (Station × VmvCode)

2. **Temporal Coverage**
   - Plot sampling frequency (samples/month) per station per year
   - Identify stations with major gaps (should have monthly sampling)
   - Reference: `README_PHASE_2.md` shows 165/174 stations match monthly cadence (94.8%)
   - Flag stations below minimum sampling frequency for trend analysis (need ≥3 per year)
   
   **Output**: Temporal coverage heatmap

3. **Missing Data Pattern Analysis**
   - Calculate % missing values by parameter type
   - Test: Are data MCAR (Missing Completely At Random) or MNAR (Missing Not At Random)?
   - Identify if missingness correlated with lab, season, or other factors

---

## Part 3: Temporal Trend Analysis

### 3.1 Station-Parameter Time Series

**Objective**: Detect meaningful changes over 4-year period

**Reference**: `unit_of_analysis.md` Section 3B1 - Station-Parameter Time Series

**Structure**: One parameter at one station tracked over time (2020-2023, 1,418 days)

**Select Representative Parameters** (from `variable_catalog.yaml`):
- **Dissolved Oxygen (DO)** - Time-sensitive; biological indicator
- **pH** - Biological activity; acid-base indicator
- **Temperature** - Available at most stations; seasonal driver
- **Total Phosphorus (TP)** - Nutrient; eutrophication indicator
- **Total Nitrogen (TN)** - Nutrient; eutrophication indicator
- **Turbidity** - Sediment/algae indicator
- **Metals** (e.g., Iron, Cadmium) - Pollution indicators

**For Each Station-Parameter Pair**:

**Task 3.1a: Descriptive Statistics**
```
Calculate:
- Count of measurements
- Mean, Median, SD, IQR
- Min, Max, percentiles (q25, q75)
- Outlier detection (IQR method: outside [Q1-1.5×IQR, Q3+1.5×IQR])
```

**Task 3.1b: Linear Regression Trend Test**
```
Fit: MeasurementValue ~ Time (years + month effect)
Extract: Slope (change/year), intercept, R², p-value

Interpretation:
- p < 0.05 → Statistically significant trend
- Positive slope → Increasing trend (e.g., pollution accumulating)
- Negative slope → Decreasing trend (e.g., recovery)
- R² < 0.1 → Weak trend (high natural variability)
- R² > 0.5 → Strong trend (temporal pattern drives variation)
```

**Task 3.1c: Mann-Kendall Non-Parametric Trend Test**
```
Alternative to linear regression; robust to outliers and non-normality
- tau statistic: Magnitude of trend
- p-value: Significance (p < 0.05 = significant)
- Use when: Data highly skewed or has outliers

Interpretation:
- tau > 0, p < 0.05 → Increasing trend
- tau < 0, p < 0.05 → Decreasing trend
- tau ≈ 0, p > 0.05 → No significant trend
```

**Task 3.1d: Seasonal Decomposition** (if sufficient data points)
- Use statsmodels for decomposition into: Trend + Seasonal + Residual
- Extract trend component to visualize long-term pattern
- Seasonal component shows expected cycles (e.g., summer DO dips)

**Task 3.1e: Quality-Adjusted Analysis**
- Repeat all trend tests on three dataset versions (A: High, B: Medium, C: Full)
- Compare slopes and p-values
- Assess: How does filtering affect trend detection?
- Expected: Strict filtering reduces signal if legitimate data excluded
- Output: "Trend Robustness" assessment (robust across all versions vs. filtering-dependent)

**Output**: 
- Trend table: Station × Parameter × Slope × p-value × Mann-Kendall tau × Robust? × Quality Version A/B/C
- Time series plots: 20-30 representative combinations
- Comparison plots: Same parameter across multiple stations (geographic variation)

### 3.2 Basin-Level Temporal Trends

**Objective**: Identify regional trend patterns

**Reference**: `README_PHASE_2.md` - 8 Major Basins

**Basin Structure**:
- MILK RIVER (15 stations)
- SOUTH SASKATCHEWAN (28 stations)
- RED DEER RIVER (18 stations)
- NORTH SASKATCHEWAN (31 stations)
- ATHABASCA (17 stations)
- PEACE RIVER (48 stations)
- SLAVE RIVER (8 stations)
- SECONDARY (8 stations)

**Task 3.2a: Basin-Level Aggregation**
```
For each basin, year, parameter:
- Calculate: Mean, Median, SD across all stations in basin
- Count: # stations with data for that parameter that year
- Apply quality filters (use Version A for high confidence)
```

**Task 3.2b: Basin Trend Calculation**
- Fit linear regression: Basin Median Value ~ Year (2020, 2021, 2022, 2023)
- Calculate trend slope per basin per parameter
- Test ANOVA: Are basin slopes significantly different from each other?
- Pairwise comparisons: Which basins differ?

**Task 3.2c: Basin Comparison Heatmap**
```
Rows: 8 Basins
Columns: Key Parameters (DO, pH, Temp, TP, TN, Turbidity)
Values: Trend slope
Colors: Red (declining) → Blue (improving)
```

**Output**:
- Basin trend table: Basin × Parameter × Slope × p-value × Direction
- Heatmap: Visual comparison of trends across basins
- Ranking: Which basins improving/declining most?

### 3.3 Exceedance & Threshold Analysis

**Objective**: Track when parameters exceed guideline limits

**Reference**: `variable_catalog.yaml` contains expected value ranges and guideline thresholds

**Task 3.3a: Define Guideline Thresholds**
```
Sourced from variable_catalog.yaml or EPA standards:
- pH: 6.5-8.5 (aquatic life support)
- DO: >5 mg/L (acceptable), <2 mg/L (concern)
- Turbidity: >5 NTU (concerning)
- Total Phosphorus: >0.03 mg/L (eutrophication concern)
- Total Nitrogen: >1.0 mg/L (enrichment concern)
- Iron: >0.3 mg/L (potentially toxic)
- Cadmium: >0.002 mg/L (toxic - EPA standard)
```

**Task 3.3b: Calculate Exceedance Rates**
```
For each station, parameter, year:
- Count: # measurements exceeding threshold
- Calculate: % exceedance = (Exceedances / Total) × 100

Example:
Station AB07AE0160, DO, 2023:
- Total measurements: 12
- Below 5 mg/L: 3
- Exceedance rate: 25%
```

**Task 3.3c: Temporal Exceedance Trend**
- Plot % exceedance by year
- Test for trend: Is exceedance rate increasing/decreasing year-over-year?
- Identify years with anomalously high exceedances (potential pollution events)
- Correlation: Do exceedance spikes correlate with SUS (suspect) flags?

**Task 3.3d: Spatial Exceedance Pattern**
- Map stations showing exceedance prevalence
- Identify geographic hotspots (consistent exceedances)
- Test spatial autocorrelation: Are exceedances clustered?

**Output**:
- Exceedance frequency table: Station × Parameter × Year × % Exceedance
- Time series: % Exceedance by year for key parameters
- Map: Geographic distribution of exceedances by parameter
- Anomaly identification: Years/locations with exceptional exceedances

---

## Part 4: Geospatial Trend Analysis

### 4.1 Spatial Data Quality Patterns

**Objective**: Understand geographic distribution of quality issues

**Task 4.1a: Create Station Geodataset**
```
DataFrame columns:
- StationNumber, StationName
- Latitude, Longitude
- Basin
- Tier (Tier 1 = comprehensive; Tier 2 = moderate)
- Quality_Score = (Clean_Records / Total_Records) × 100
- Mean_Qualifier_Rate = % flagged records
- Parameter_Count = # variables measured at station
- Data_Span = Years of data available
```

**Task 4.1b: Spatial Visualization**
- Create basemap with Folium or Geopandas
- Plot each station with color-coded quality score
- Layer: Basin boundaries, river networks
- Interactive: Hover tooltips showing station stats
- Interpretation: Are quality issues clustered geographically?

**Task 4.1c: Spatial Autocorrelation Test (Moran's I)**
```python
from esda import Moran
from splot.esda import moran_scatterplot

# Calculate Moran's I for quality_score
I = Moran(data['quality_score'], weights=spatial_weights)
p_value = I.p_norm  # Two-tailed test

# Interpret:
# I > 0, p < 0.05 → Positive autocorrelation (clusters of similar quality)
# I < 0, p < 0.05 → Negative autocorrelation (dispersed/checkerboard pattern)
# p > 0.05 → No significant spatial autocorrelation
```

**Task 4.1d: LISA Analysis (Local Indicators of Spatial Association)**
- Identify statistically significant clusters of high-quality and low-quality stations
- Map hotspots (clusters of poor quality) and coldspots (clusters of good quality)
- Interpretation: Which regions need attention?

**Output**:
- Spatial quality pattern map (color-coded by score)
- Moran's I test results + interpretation
- LISA hotspot/coldspot map
- Geographic cluster identification

### 4.2 Parameter-Specific Geospatial Patterns

**Objective**: Identify geographic variation in specific parameters

**Task 4.2a: Parameter Distribution Maps**
For each key parameter:
- Calculate mean/median value per station (across all years)
- Create choropleth map (color intensity = parameter level)
- Overlays: Basin boundaries, river networks
- Expected patterns:
  - Nutrients: Increase downstream (agricultural/urban inputs)
  - Metals: Episodic spikes (mining activity, erosion)
  - DO/pH: Spatial variation by geology/land use

**Task 4.2b: Identify Geospatial Anomalies**
- Use Isolation Forest or Local Outlier Factor to detect spatially anomalous stations
- Example: Neighbors have pH 7-8 but Station X = 5 consistently
- Investigate: Real water quality issue vs. measurement error?

**Task 4.2c: Upstream-Downstream Comparison**
- Identify station pairs on same river/tributary (use basin info + coordinates)
- Compare parameter values: Expected downstream > upstream (dilution/input effects)
- Statistical test: Is difference significant and consistent across parameters?
- Expected: Downstream nutrients ↑, downstream metals ↑ (if pollution sources)

**Output**:
- Maps showing geographic distribution of key parameters
- Identification of spatially anomalous zones
- Upstream vs. downstream comparison analysis
- Pattern interpretation document

### 4.3 Basin-Level Geospatial Analysis

**Objective**: Compare water quality profiles across 8 basins

**Reference**: `README_PHASE_2.md` Basin Distribution section

**Task 4.3a: Basin Quality Scorecard**
```
For each of 8 basins, calculate:
- # of stations
- Mean quality score (% clean records)
- % Tier 1 stations (comprehensive coverage)
- Median parameter coverage (# VmvCodes)
- Temporal coverage (% 4-year span)
- Top 3 quality concerns (most common qualifier codes)
- Most problematic parameters (highest % flagged)
- Trend direction (improving/stable/declining)
```

Example Output:
| Basin | Stations | Quality Score | Tier 1 % | Concerns | Trend |
|-------|----------|--------------|---------|----------|-------|
| MILK RIVER | 15 | 96.2% | 100% | Low | Stable |
| PEACE RIVER | 48 | 94.8% | 100% | Moderate | Improving |

**Task 4.3b: Basin Comparison Tests**
- ANOVA: Are basin mean quality scores significantly different?
- Kruskal-Wallis (non-parametric alternative): Basin quality medians differ?
- Pairwise comparisons (Tukey HSD): Which specific basins differ?
- Interpretation: Is there a "best" basin for water quality?

**Task 4.3c: Basin Trend Comparison**
- Plot: Median parameter value by basin over 4 years
- Example: Total P trends across 8 basins (2020-2023)
- Test: Are basin differences changing over time?
- Interpretation: Is one basin improving while another declines?

**Output**:
- Basin scorecard table (8 basins × key metrics)
- Comparison charts: Parameter values × Basin × Year
- Basin quality ranking: Best to worst basins
- Statistical significance tests

---

## Part 5: Statistical Quality Testing

### 5.1 Normality & Distribution Testing

**Objective**: Understand data distributions for appropriate statistical methods

**Task 5.1a: Shapiro-Wilk Normality Test**
```
For top 10 parameters:
- Perform Shapiro-Wilk test on measurement values
- Null hypothesis: Data is normally distributed
- p < 0.05 → Reject null → Data NOT normally distributed

If NOT normal:
- Use median/IQR instead of mean/SD
- Use non-parametric tests (Kruskal-Wallis instead of ANOVA)
- Consider data transformation (log, sqrt)
```

**Task 5.1b: Distribution Statistics**
- Calculate: Skewness (should be ≈ 0 for normal)
  - Skewness > 1 or < -1: Highly skewed
- Calculate: Kurtosis (should be ≈ 0 for normal)
  - Kurtosis > 3: Heavy tails
- Visual: Histogram + Q-Q plot for each parameter
- Test: Do log-transformed values have better normality?

**Output**:
- Normality test results table
- Distribution visualizations (histograms, Q-Q plots)
- Recommendation: Parametric vs. non-parametric tests
- Guidance on data transformation if needed

### 5.2 Outlier Detection & Treatment

**Objective**: Identify and appropriately handle measurement anomalies

**Methods Available**:

1. **IQR Method** (Most common for environmental data)
   ```
   Lower Bound = Q1 - 1.5 × IQR
   Upper Bound = Q3 + 1.5 × IQR
   Outliers: Values outside [Lower, Upper] bounds
   ```

2. **Z-Score Method**
   ```
   Z = (Value - Mean) / SD
   Very extreme: |Z| > 3
   Moderate: |Z| > 2.5
   ```

3. **Isolation Forest** (For complex multivariate patterns)
   - Identifies points isolated from others
   - Useful when outliers interact (e.g., unusual combination of parameters)

**Task 5.2a: Calculate Outlier Rates**
- % of values flagged as outliers per parameter
- Expected: ~0.1-1% for reasonable data
- High %: Suggests either wide natural variability or data quality issue

**Task 5.2b: Compare to Quality Flags**
- Correlation: Do outliers correlate with SUS (suspect) flags?
- Hypothesis: Outliers should often be flagged; if not = quality issue
- Expected insight: Good correspondence validates outlier detection

**Task 5.2c: Outlier Retention Decision**
- Some outliers are real (e.g., pollution events, natural extremes)
- Decision tree:
  - Has SUS flag? → Probably measurement error → flag for caution
  - Extreme but no flag? → Probably real event → retain with notation
  - Repeats at same station? → Systematic condition → retain and document
- Treatment: Flag vs. remove vs. transform?
- Document decision for transparency

**Output**:
- Outlier detection report: Parameter × Method × % Flagged
- Box plots showing outliers (IQR method)
- Recommendations: Retain vs. handle per parameter
- Documented decisions for analysis transparency

### 5.3 Temporal Trend Significance Testing

**Objective**: Determine if observed trends are statistically significant (not random)

**Test 5.3a: Mann-Kendall Test** (Preferred for environmental data)
- Advantages: Non-parametric, robust to outliers, doesn't assume linearity
- Null hypothesis: No monotonic trend in data
- Output: tau statistic (−1 to +1), p-value
- Use when: Data highly non-normal or has outliers

```python
from scipy.stats import kendalltau

for station in stations:
    for parameter in parameters:
        subset = df[(df['StationNumber'] == station) & 
                    (df['VmvCode'] == parameter)].sort_values('SampleDateTime')
        
        x = range(len(subset))
        y = subset['MeasurementValue'].values
        tau, p_value = kendalltau(x, y)
        
        trend = "Increasing" if tau > 0 else "Decreasing"
        significant = "Yes (p<0.05)" if p_value < 0.05 else "No (p≥0.05)"
        
        print(f"{station}-{parameter}: {trend}, {significant}")
```

**Test 5.3b: Linear Regression Trend Test**
- Fit: MeasurementValue ~ Time
- Output: Slope (rate of change/year), R² (variance explained), p-value
- Advantages: Provides quantitative rate; interpretable magnitude
- Disadvantages: Assumes linear relationship; sensitive to outliers

**Test 5.3c: Multiple Testing Correction**
- Problem: If testing 50+ station-parameter combinations, some will appear significant by chance alone
- Solution: Bonferroni correction: α_corrected = 0.05 / (# tests)
- Example: 174 stations × 10 parameters = 1,740 tests
  - Bonferroni α = 0.05 / 1,740 ≈ 0.000029 (very stringent)
  - Alternative: FDR correction (False Discovery Rate) often more practical

**Output**:
- Trend significance table: All station-parameter combinations with p-values
- Volcano plot: Slope × (-log10 p-value) to visualize effect size vs. significance
- Summary: # statistically significant trends per parameter

### 5.4 Difference Testing Between Groups

**Objective**: Test if quality/values differ significantly between stations, basins, or time periods

**Test 5.4a: ANOVA** (If data normally distributed)
- Null hypothesis: All group means are equal
- Output: F-statistic, p-value
- Assumption: Homogeneity of variance (Levene's test)
- Follow-up: Tukey HSD for pairwise comparisons (which groups differ?)

```python
from scipy.stats import f_oneway, levene

# Test: Does DO differ between basins?
basin_groups = [df[df['Basin'] == basin]['DO'].dropna().values for basin in basins]

# Check homogeneity of variance
levene_stat, levene_p = levene(*basin_groups)

# ANOVA
f_stat, p_value = f_oneway(*basin_groups)
print(f"ANOVA: F={f_stat:.2f}, p={p_value:.4f}")
```

**Test 5.4b: Kruskal-Wallis Test** (Non-parametric alternative to ANOVA)
- Use when: Data not normally distributed or sample sizes unequal
- Null hypothesis: Group distributions are equal
- Output: H-statistic, p-value
- Follow-up: Mann-Whitney U tests for pairwise comparisons

**Test 5.4c: Chi-Square Test** (For categorical associations)
- Test: Association between LabCode and qualifier type
- Null: No association (LabCode and qualifier are independent)
- Output: Chi-square statistic, p-value, effect size (Cramér's V)

**Output**:
- Test results table: Comparison × Test Type × Statistic × p-value
- Interpretation: Which groups differ significantly?
- Effect size reporting (not just p-values)

### 5.5 Effect Size & Practical Significance

**Objective**: Beyond p-values, quantify the magnitude of differences

**Measure 5.5a: Cohen's d** (Standardized effect size)
```
d = (Mean1 - Mean2) / Pooled_SD

Interpretation:
- |d| < 0.2: Negligible effect
- 0.2 ≤ |d| < 0.5: Small effect
- 0.5 ≤ |d| < 0.8: Medium effect
- |d| ≥ 0.8: Large effect
```

**Measure 5.5b: Percentage Change**
```
% Change = ((New - Old) / Old) × 100

Example: TP changed from 0.050 mg/L (2020) to 0.065 mg/L (2023)
% Change = ((0.065 - 0.050) / 0.050) × 100 = +30% increase
```

**Measure 5.5c: Practical vs. Statistical Significance**
- Example: pH decreased from 7.50 to 7.35 (significant p=0.03, but only 0.15 unit change)
- Question: Is 0.15 pH units practically meaningful for aquatic life?
- Reality check: Domain knowledge + effect size + p-value

**Output**:
- Effect size table: Comparison × Cohen's d (or % change) × Interpretation
- Guidance: Which findings are practically meaningful for water management?

---

## Part 6: Quality-Adjusted Comparative Analysis

### 6.1 Impact of Data Filtering on Trends

**Objective**: Understand how quality filtering affects analytical conclusions

**Approach**: Repeat trend analysis on three dataset versions

**Task 6.1a: Trend Comparison Table**
```
Example format:
Station | Parameter | Version A (Strict) | Version B (Balanced) | Version C (All)
        |           | Slope, p-val       | Slope, p-val        | Slope, p-val
--------|-----------|-------------------|---------------------|------------------
AB07AE | pH        | +0.015, p=0.02*   | +0.016, p=0.01*    | +0.018, p=0.001*
AB07AE | DO        | +0.050, p=0.08    | +0.048, p=0.09     | +0.045, p=0.11

* = statistically significant (p < 0.05)
```

**Task 6.1b: Sensitivity Analysis**
- **High agreement** (all versions show trend) → Robust finding (use with confidence)
- **Moderate agreement** (2/3 versions) → Trend likely real but filtering decisions matter
- **Disagreement** (versions diverge) → Trend sensitive to quality decisions (report uncertainty)
- **Version C only** (all data shows trend) → Quality flags may be removing signal

**Task 6.1c: Recommendations by Finding Type**

| Case | Versions A/B/C | Conclusion | Action |
|------|---|---|---|
| All agree | Slope: +0.02 (all) | Robust trend | Use trend with confidence; document filtering used |
| A & B agree, C disagrees | A/B: +0.02, C: +0.04 | Quality filters affect magnitude | Use Version A/B; note Version C shows stronger signal |
| Disagree strongly | A: +0.01, B: -0.01, C: +0.02 | Filtering-dependent result | Report as uncertain; recommend conservative filtering |
| A only significant | A: p=0.04*, B: p=0.08, C: p=0.11 | Marginal/filtering-dependent | Not robust; treat with caution |

**Output**:
- Sensitivity analysis table
- Guidance: Which trends to trust vs. which to qualify
- Recommendations: Which dataset version for which analysis goal

### 6.2 Quality-Aware Composite Indices

**Objective**: Create data quality scores that adjust for flagged data in analysis results

**Task 6.2a: Define Parameter Confidence Score**
```
Confidence_Score = (Clean_Records / Total_Records) × 100

Tiers:
- Excellent: 95-100% (high confidence; use freely)
- Good: 90-95% (moderate confidence; flag concerns)
- Fair: 85-90% (reduced confidence; use cautiously)
- Poor: <85% (low confidence; exclude from critical analyses)
```

**Task 6.2b: Parameter-Quality Matrix**
```
Rows: 82 Parameters (from variable_catalog.yaml)
Columns: Years (2020, 2021, 2022, 2023)
Values: Confidence score (colored 0-100)

Example:
         2020   2021   2022   2023
pH       99.2%  98.8%  99.1%  99.5%   ← Consistently excellent
DO       91.2%  88.5%  86.3%  89.1%   ← More variable; some concern
TP       87.3%  85.2%  84.1%  86.8%   ← Moderate; caution needed
```

Interpretation: Which parameters/years most reliable?

**Task 6.2c: Station Composite Quality Index**
```
For each station, year:
Quality_Index = Weighted Average of Parameter Confidence Scores

Weights from variable_catalog.yaml priority:
- Critical parameters (DO, pH): 40% weight
- Important parameters (Nutrients, Temp): 40% weight
- Optional parameters (Metals, Others): 20% weight
```

**Output**:
- Parameter-quality heatmaps
- Station-year quality matrix
- Thematic maps showing quality evolution (2020 → 2023)

### 6.3 Recommendations for Data Use

**Objective**: Create actionable guidance for which data to use for which purpose

**Task 6.3a: Create Decision Matrix**

```
Index:
Station | Parameter | Year | Quality Confidence | Trend | Recommended Use | Notes

Example rows:
AB07AE | pH       | 2023 | 99%              | Stable (+0.001, p=0.5) | All analyses | Excellent data; use confidently
AB07AE | DO       | 2023 | 92%              | Increasing (+0.02, p=0.04*) | Exploratory | Some HT flags; trend robust but with caution
AB07AE | TP       | 2023 | 81%              | Unknown (-0.01, p=0.15) | Not recommended | Too many quality issues; use only for basin-level
AB07AE1 | pH      | 2020 | 87%              | Unknown | Field only | Low confidence; not suitable for trend analysis
```

**Task 6.3b: Use Case Guidance**
```
Use Case: Trend Analysis
- Recommended: Quality ≥90%, p < 0.05, robust across versions
- Conditionally: Quality 85-90% if Effect Size > medium
- Not recommended: Quality <85% or conflicting versions

Use Case: Regulatory Reporting
- Required: Quality ≥95%, Version A (strict) filtering, documented procedures
- Acceptable: Quality 90-95% with caveats noted

Use Case: Exploratory Analysis
- Acceptable: Quality ≥80%, any version, flagged appropriately
- Can include: Uncertain trends, lower confidence data (with documentation)
```

**Output**:
- Station-parameter-year recommendation matrix (use for filtering in downstream analysis)
- Guidance document: How to interpret and use quality recommendations

---

## Part 7: Expected Findings & Hypotheses

### Primary Hypotheses to Test

1. **Data Quality Improving Over Time**
   - Hypothesis: Quality codes (especially SUS, HT) decreasing year-over-year as lab procedures improve
   - Test: Compare % flagged records 2020 vs. 2023
   - If true: Indicates improving lab procedures, method standardization

2. **Geographic Quality Clusters**
   - Hypothesis: Certain basins or regions have systematically poorer data quality
   - Test: Moran's I for spatial autocorrelation; identify hotspots
   - If true: May indicate lab capacity issues, geographic monitoring challenges

3. **Seasonal Quality Patterns**
   - Hypothesis: Summer = more HT flags (sample degradation in heat)
   - Hypothesis: Winter = different lab staffing patterns → different quality
   - Test: Calculate qualifier frequency by quarter
   - If true: Recommend sample collection/handling protocol adjustments

4. **Parameter-Specific Flag Patterns**
   - Hypothesis: DR (dilution) flags common for metals after pollution events
   - Hypothesis: HT flags common for volatile parameters (DO)
   - Test: Correlation between parameter type and qualifier code
   - If true: Use to identify which parameters most at-risk for quality issues

5. **Meaningful Temporal Trends - Real vs. Noise**
   - Hypothesis: DO and pH show clear seasonal cycles but stable long-term
   - Hypothesis: TP and TN show increasing trend (eutrophication concern)
   - Hypothesis: Metals show episodic spikes (pollution events) but stable baseline
   - Test: Linear regression + seasonal decomposition
   - If true: Different management priorities per parameter

6. **Quality Filtering Effect - Critical Decision**
   - Hypothesis: Strict filtering may exclude legitimate data, reducing trend power
   - Hypothesis: Relaxed filtering may include noise, obscuring true trends
   - Hypothesis: Optimal filter requires balancing sample size vs. data quality
   - Test: Trend robustness across versions A/B/C

---

## Part 8: Recommended Notebook Structure

### Notebook 1: Data Description & Quality Profile
**File**: `01_data_description_and_quality.ipynb`

**Sections**:
1. Load and validate raw data (247,121 records)
2. Schema and data type verification
3. Create three dataset versions (High/Medium/Exploratory)
4. Calculate quality profile: cleanliness rates, qualifier code distribution
5. Cardinality validation checks
6. Summary statistics by year, station tier, parameter category

**Outputs**:
- Quality profile dashboard
- Data validation report
- Three validated datasets saved to CSV

---

### Notebook 2: Temporal Trend Analysis
**File**: `02_temporal_trends.ipynb`

**Sections**:
1. Load datasets from Notebook 1
2. Station-parameter time series analysis
   - Linear regression: Slope + p-value
   - Mann-Kendall tests
   - Seasonal decomposition
3. Quality-adjusted trend comparison (versions A/B/C)
4. Basin-level aggregation and trends
5. Exceedance analysis vs. thresholds
6. Visualization: 20-30 representative time series plots

**Outputs**:
- Trend table (174 stations × parameters × metrics)
- Time series plots
- Basin trend heatmaps
- Exceedance time series

---

### Notebook 3: Geospatial Analysis
**File**: `03_geospatial_patterns.ipynb`

**Sections**:
1. Create station geodataset with quality scores
2. Spatial autocorrelation tests (Moran's I)
3. LISA analysis for hotspots/coldspots
4. Parameter-specific geographic patterns
5. Basin comparisons (quality scores, trends, rankings)
6. Upstream-downstream analysis

**Outputs**:
- Spatial quality maps
- LISA hotspot maps
- Basin comparison charts
- Geospatial statistics report

---

### Notebook 4: Statistical Quality & Outlier Detection
**File**: `04_statistical_testing.ipynb`

**Sections**:
1. Distribution analysis and normality testing
2. Outlier detection (IQR, Z-score, Isolation Forest)
3. ANOVA/Kruskal-Wallis for group differences
4. Chi-Square tests for categorical associations
5. Effect size calculations (Cohen's d, % change)
6. Multiple testing corrections

**Outputs**:
- Normality test results table
- Outlier report
- Statistical test results
- Box plots and distribution visualizations

---

### Notebook 5: Quality-Adjusted Conclusions
**File**: `05_quality_adjusted_analysis.ipynb`

**Sections**:
1. Sensitivity analysis: Filtering impact on trends (Version A/B/C comparison)
2. Composite quality indices creation
3. Confidence score calculations
4. Parameter-quality matrix
5. Recommendations matrix building
6. Synthesis: Robust findings vs. uncertain patterns

**Outputs**:
- Sensitivity analysis table
- Recommendations matrix (station × parameter × year × use case)
- Summary of robust findings
- Caveats and limitations document

---

### Notebook 6: Interactive Dashboard Prototype (Optional)
**File**: `06_dashboard_prototype.ipynb`

**Sections**:
1. Interactive Streamlit/Plotly app setup
2. Filters: Station, Parameter, Date Range, Quality Level
3. Real-time trend recalculation
4. Map with station quality layers
5. Time series visualization with quality bands
6. Summary statistics panel

**Outputs**:
- Prototype dashboard
- Component code for production deployment

---

## Part 9: Key Metrics & Outputs Summary

### Quality Landscape Metrics
```
Metric                    Value              Interpretation
Total Records             247,121            Complete dataset size
Clean Records             238,465 (96.5%)    High baseline quality
Flagged Records           8,656 (3.5%)       Minor quality concerns
Unique Qualifier Codes    17                 Complete flag coverage
Most Common Code          OBS (1.2%)         Field observations frequent
Most Concerning Code      SUS (0.4%)         ~1,000 suspect measurements
```

### Station Quality Rankings
```
Top 5 Highest Quality:
1. Station X: 99.8% clean
2. Station Y: 99.6% clean
3. Station Z: 99.5% clean

Bottom 5 Lowest Quality:
1. Station A: 85.2% clean
2. Station B: 87.1% clean
3. Station C: 88.9% clean
```

### Temporal Trend Summary
```
Parameter | Stations with Sig. Trends | Increasing | Decreasing | No Trend
pH        | 12/174                    | 4          | 8          | 162
DO        | 18/174                    | 6          | 12         | 156
Temp      | 5/174                     | 3          | 2          | 169
TP        | 25/174                    | 18         | 7          | 149
TN        | 22/174                    | 16         | 6          | 152
```

### Basin Comparison Matrix
```
Basin             | Stations | Quality | Tier 1 | Top Concerns | Trend
MILK RIVER        | 15       | 96.2%   | 100%   | Low          | Stable
PEACE RIVER       | 48       | 94.8%   | 100%   | Moderate     | Improving
ATHABASCA         | 17       | 93.1%   | 94%    | High (2 stn) | Improving
NORTH SASKATCHEWAN| 31       | 95.1%   | 100%   | Low-Mod      | Stable
```

---

## Part 10: Implementation Checklist

### Pre-Analysis Phase
- [ ] All guidance documents read:
  - [ ] `unit_of_analysis.md`
  - [ ] `data_quality_analysis.md`
  - [ ] `README_PHASE_2.md`
  - [ ] `station_profiles.yaml`
  - [ ] `variable_catalog.yaml`
  - [ ] `unit_definitions.yaml`
- [ ] Environment set up (Python 3.13.13, required packages)
- [ ] Raw data downloaded and verified

### Notebook 1: Data Foundation
- [ ] Raw data loaded and validated (247,121 records)
- [ ] Three dataset versions created
- [ ] Cardinality checks completed
- [ ] Quality profile calculated
- [ ] Summary statistics generated

### Notebook 2: Temporal Trends
- [ ] Station-parameter time series analyzed (174 × 82)
- [ ] Linear regression tests completed
- [ ] Mann-Kendall tests completed
- [ ] Seasonal patterns identified
- [ ] Basin-level trends calculated
- [ ] Exceedance analysis completed

### Notebook 3: Geospatial Analysis
- [ ] Station geodataset created
- [ ] Spatial autocorrelation tests (Moran's I) completed
- [ ] LISA hotspot/coldspot analysis done
- [ ] Basin comparisons visualized
- [ ] Parameter-specific geospatial patterns identified

### Notebook 4: Statistical Testing
- [ ] Normality tests completed
- [ ] Outlier detection applied
- [ ] ANOVA/Kruskal-Wallis tests run
- [ ] Effect sizes calculated
- [ ] Multiple testing corrections applied

### Notebook 5: Quality-Adjusted Analysis
- [ ] Filtering impact analysis completed
- [ ] Version A/B/C trend comparison done
- [ ] Composite quality indices created
- [ ] Recommendations matrix generated
- [ ] Robust findings identified and documented

### Final Outputs
- [ ] Trend table (Station × Parameter × Slope × p-value × Direction × Robust?)
- [ ] Quality trend charts (temporal & geospatial)
- [ ] Statistical test results compiled
- [ ] Basin comparison dashboard
- [ ] Recommendations matrix for data use
- [ ] Executive summary with findings & caveats

---

## References & Guidance Integration

**Core Guidance Documents** (Must Integrate):
1. [unit_of_analysis.md](../unit_of_analysis.md) - Valid analytical units, cardinality assumptions
2. [data_quality_analysis.md](../data_quality_analysis.md) - Quality codes, filtering strategies, parameter-specific guidance
3. [README_PHASE_2.md](../README_PHASE_2.md) - Dataset overview, station tiers, basin distribution
4. [data_documentation.md](../data_documentation.md) - EPA standards context, data collection methods
5. [station_profiles.yaml](../station_profiles.yaml) - Station metadata (coords, basins, tiers, coverage)
6. [variable_catalog.yaml](../variable_catalog.yaml) - Parameter definitions, thresholds, aggregation methods
7. [unit_definitions.yaml](../unit_definitions.yaml) - Unit conversions, mappings

**Statistical Libraries**:
- `scipy.stats` - Regression, ANOVA, Mann-Kendall, Shapiro-Wilk tests
- `statsmodels` - Time series decomposition, regression diagnostics
- `esda`, `splot` - Spatial analysis (Moran's I, LISA)
- `scikit-learn` - Outlier detection (Isolation Forest, LOF)
- `pandas`, `numpy` - Data manipulation and calculation

**Visualization**:
- `matplotlib`, `seaborn` - Publication-quality static charts
- `folium`, `geopandas` - Interactive maps
- `plotly` - Interactive dashboards
- `streamlit` - Prototype apps (optional)

---

**Version**: 1.0  
**Created**: May 18, 2026  
**Last Updated**: May 18, 2026  
**Status**: Ready for Implementation
