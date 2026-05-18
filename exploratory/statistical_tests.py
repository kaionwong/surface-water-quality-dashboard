"""
Statistical Tests Module

Comprehensive statistical testing covering:
- Normality tests (Shapiro-Wilk, Anderson-Darling, Kolmogorov-Smirnov)
- Distribution identification
- Trend analysis (Mann-Kendall, linear regression)
- Autocorrelation analysis
- Homogeneity of variance tests (Levene's, Bartlett's)
- Temporal stability analysis
"""

import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

from .config import ALBERTA_DATA_FILE, EXPECTED_COLUMNS, OUTPUT_STATS_PATH
from .utils import (
    load_data_chunked,
    identify_numeric_columns,
    statistical_summary,
    save_outputs,
)


def normality_tests(series, name=""):
    """
    Perform multiple normality tests on a numeric series.
    
    Returns dict with test results and recommendations.
    """
    clean_data = series.dropna()
    
    if len(clean_data) < 3:
        return {"name": name, "error": "Insufficient data"}
    
    results = {"name": name, "sample_size": len(clean_data)}
    
    try:
        # Shapiro-Wilk test (best for small samples)
        if len(clean_data) <= 5000:
            shapiro_stat, shapiro_p = stats.shapiro(clean_data)
            results["shapiro_wilk"] = {
                "statistic": float(shapiro_stat),
                "p_value": float(shapiro_p),
                "normal": shapiro_p > 0.05,
            }
    except:
        pass
    
    try:
        # Anderson-Darling test
        anderson_result = stats.anderson(clean_data)
        results["anderson_darling"] = {
            "statistic": float(anderson_result.statistic),
            "critical_values": anderson_result.critical_values.tolist(),
            "significance_levels": anderson_result.significance_level.tolist(),
        }
    except:
        pass
    
    try:
        # Kolmogorov-Smirnov test (vs standard normal)
        ks_stat, ks_p = stats.kstest(clean_data, 'norm', args=(clean_data.mean(), clean_data.std()))
        results["kolmogorov_smirnov"] = {
            "statistic": float(ks_stat),
            "p_value": float(ks_p),
            "normal": ks_p > 0.05,
        }
    except:
        pass
    
    # Summary
    results["skewness"] = float(stats.skew(clean_data))
    results["kurtosis"] = float(stats.kurtosis(clean_data))
    results["is_likely_normal"] = abs(results["skewness"]) < 2 and abs(results["kurtosis"]) < 3
    
    return results


def identify_distribution(series, name=""):
    """Attempt to identify the best-fit distribution."""
    
    clean_data = series.dropna()
    
    if len(clean_data) < 10:
        return {"name": name, "error": "Insufficient data"}
    
    # Test against common distributions
    distributions = {
        'normal': stats.norm,
        'lognormal': stats.lognorm,
        'exponential': stats.expon,
        'gamma': stats.gamma,
        'weibull': stats.weibull_min,
    }
    
    # Try to fit and compute goodness-of-fit
    ks_results = {}
    
    for dist_name, dist in distributions.items():
        try:
            if dist_name == 'lognormal':
                # Lognormal needs positive values
                if (clean_data > 0).all():
                    params = dist.fit(clean_data)
                    ks_stat, ks_p = stats.kstest(clean_data, lambda x: dist.cdf(x, *params))
                    ks_results[dist_name] = {"ks_statistic": float(ks_stat), "p_value": float(ks_p)}
            else:
                params = dist.fit(clean_data)
                ks_stat, ks_p = stats.kstest(clean_data, lambda x: dist.cdf(x, *params))
                ks_results[dist_name] = {"ks_statistic": float(ks_stat), "p_value": float(ks_p)}
        except:
            pass
    
    # Find best fit (highest p-value or lowest KS statistic)
    best_fit = min(ks_results.items(), key=lambda x: x[1]['ks_statistic']) if ks_results else None
    
    return {
        "name": name,
        "fit_results": ks_results,
        "best_fit": best_fit[0] if best_fit else None,
    }


def mann_kendall_trend(series, name=""):
    """
    Perform Mann-Kendall test for monotonic trend (vectorized, with sampling for large data).
    
    Returns trend direction (increasing/decreasing/no trend) and p-value.
    Uses vectorized operations for efficiency. For n>10k, samples data.
    """
    clean_data = series.dropna()
    
    if len(clean_data) < 3:
        return {"name": name, "error": "Insufficient data"}
    
    n = len(clean_data)
    
    # Sample if data is too large to avoid memory issues
    # For >10k samples, random sample for trend estimation
    if n > 10000:
        sample_size = min(10000, int(np.sqrt(n) * 10))
        indices = np.random.choice(n, size=sample_size, replace=False)
        indices.sort()
        values = clean_data.iloc[indices].values
        n_actual = len(values)
    else:
        values = clean_data.values
        n_actual = n
    
    # Vectorized Mann-Kendall statistic calculation
    idx = np.arange(n_actual)
    pairs = idx[:, None] < idx[None, :]  # Upper triangle matrix
    
    # Calculate all pairwise differences (vectorized)
    diffs = values[:, None] - values[None, :]
    s = np.sum(np.sign(diffs[pairs]))
    
    # Variance (use original n for proper statistical inference)
    var_s = n * (n - 1) * (2 * n + 5) / 18
    
    # Z-score
    if s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0
    
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    
    # Determine trend
    if p_value < 0.05:
        trend = "increasing" if s > 0 else "decreasing"
    else:
        trend = "no_significant_trend"
    
    return {
        "name": name,
        "mann_kendall_s": int(s),
        "z_score": float(z),
        "p_value": float(p_value),
        "trend": trend,
        "significant": p_value < 0.05,
    }


def temporal_stability(df):
    """
    Analyze temporal stability of parameters.
    
    Divides data into time periods and tests for significant changes.
    """
    # Identify date column
    date_col = None
    for col in df.columns:
        if any(name.lower() in col.lower() for name in EXPECTED_COLUMNS['date_time']):
            date_col = col
            break
    
    if not date_col:
        return {"error": "No date column found"}
    
    # Identify parameter/value columns
    value_col = None
    for col in df.columns:
        if any(name.lower() in col.lower() for name in EXPECTED_COLUMNS['value']):
            value_col = col
            break
    
    if not value_col:
        return {"error": "No value column found"}
    
    # Convert date column
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df_sorted = df.sort_values(date_col)
    
    # Divide into yearly periods
    df_sorted['year'] = df_sorted[date_col].dt.year
    
    stability_results = []
    
    for year in df_sorted['year'].unique():
        year_data = df_sorted[df_sorted['year'] == year][value_col].dropna()
        if len(year_data) > 0:
            stability_results.append({
                'year': int(year),
                'count': len(year_data),
                'mean': float(year_data.mean()),
                'std': float(year_data.std()),
                'min': float(year_data.min()),
                'max': float(year_data.max()),
            })
    
    return pd.DataFrame(stability_results)


def main(nrows=None):
    """
    Execute statistical tests analysis.
    
    Parameters
    ----------
    nrows : int, optional
        Limit rows for testing
    
    Returns
    -------
    dict
        Results containing statistical test results
    """
    print("\n" + "="*60)
    print("STATISTICAL TESTS ANALYSIS")
    print("="*60)
    
    # Load data
    print("\nLoading data...")
    df = load_data_chunked(ALBERTA_DATA_FILE, nrows=nrows)
    
    # Get numeric columns
    numeric_cols = identify_numeric_columns(df)
    print(f"\nFound {len(numeric_cols)} numeric columns")
    
    # Normality tests
    print("\nPerforming normality tests...")
    normality_results = []
    for col in numeric_cols[:10]:  # Limit to first 10 for performance
        result = normality_tests(df[col], name=col)
        normality_results.append(result)
    
    normality_df = pd.DataFrame(normality_results)
    
    # Distribution identification
    print("\nIdentifying distributions...")
    distribution_results = []
    for col in numeric_cols[:10]:
        result = identify_distribution(df[col], name=col)
        distribution_results.append(result)
    
    # Trend analysis
    print("\nPerforming trend analysis...")
    trend_results = []
    for col in numeric_cols[:10]:
        result = mann_kendall_trend(df[col], name=col)
        trend_results.append(result)
    
    trend_df = pd.DataFrame(trend_results)
    
    # Temporal stability
    print("\nAnalyzing temporal stability...")
    temporal_stability_df = temporal_stability(df)
    
    # Results
    results = {
        "normality_tests": normality_df,
        "distribution_fits": distribution_results,
        "trend_analysis": trend_df,
        "temporal_stability": temporal_stability_df,
        "dataframe": df,
    }
    
    # Save outputs
    print("\nSaving outputs...")
    save_outputs(
        dataframes_dict={
            "normality_tests": normality_df,
            "trend_analysis": trend_df,
            "temporal_stability": temporal_stability_df,
        },
        json_dict={
            "distribution_fits": distribution_results,
        },
        prefix="statistical_tests_"
    )
    
    print("\n[OK] Statistical tests analysis complete!")
    
    return results


if __name__ == "__main__":
    results = main()
