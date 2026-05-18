"""
EDA Notebook Synthesis Module

Synthesizes results from all exploratory analyses into:
- Executive summary
- Key findings
- Recommendations for data cleaning
- Quality assessment framework application
- Data readiness for dashboard
"""

import pandas as pd
import json
from . import (
    data_profiling,
    missing_data_analysis,
    statistical_tests,
    quality_issues,
)
from .config import OUTPUT_EDA_PATH
from .utils import save_outputs


def synthesize_findings(results_dict):
    """
    Synthesize findings from all modules into executive summary.
    """
    
    synthesis = {
        "overview": {
            "total_rows": None,
            "total_columns": None,
            "total_cells": None,
            "completeness_percent": None,
        },
        "key_findings": [],
        "quality_dimensions": {},
        "recommendations": [],
        "data_readiness": {
            "raw_data_quality": None,
            "estimated_cleaning_effort": None,
            "recommended_next_steps": [],
        }
    }
    
    # Extract overview from profiling
    if 'profiling' in results_dict and 'dataset_profile' in results_dict['profiling']:
        profile = results_dict['profiling']['dataset_profile']
        synthesis["overview"]["total_rows"] = profile['dataset_shape']['rows']
        synthesis["overview"]["total_columns"] = profile['dataset_shape']['columns']
        synthesis["overview"]["total_cells"] = profile['total_cells']
    
    # Calculate completeness
    if 'missing' in results_dict and isinstance(results_dict['missing']['missing_overall'], pd.DataFrame):
        missing_df = results_dict['missing']['missing_overall']
        total_missing_pct = missing_df['missing_percent'].sum() / len(missing_df)
        synthesis["overview"]["completeness_percent"] = 100 - total_missing_pct
    
    # Extract quality issues
    if 'quality' in results_dict:
        quality = results_dict['quality']
        
        if not quality['validity_issues'].empty:
            synthesis["key_findings"].append(
                f"Found {len(quality['validity_issues'])} validity constraint violations"
            )
        
        if not quality['outlier_detections'].empty:
            outlier_count = quality['outlier_detections']['outlier_count'].sum()
            synthesis["key_findings"].append(
                f"Detected {outlier_count} potential outliers"
            )
        
        if quality['duplicates']['exact_duplicates'] > 0:
            synthesis["key_findings"].append(
                f"Found {quality['duplicates']['exact_duplicates']} exact duplicate records"
            )
    
    # Quality dimensions assessment
    if 'profiling' in results_dict:
        profile = results_dict['profiling']
        synthesis["quality_dimensions"]["completeness"] = {
            "assessment": synthesis["overview"]["completeness_percent"],
            "status": "good" if synthesis["overview"]["completeness_percent"] > 95 else "needs_attention",
        }
    
    if 'stats' in results_dict and isinstance(results_dict['stats']['normality_tests'], pd.DataFrame):
        normal_count = results_dict['stats']['normality_tests']['is_likely_normal'].sum()
        total_count = len(results_dict['stats']['normality_tests'])
        synthesis["quality_dimensions"]["validity"] = {
            "normally_distributed_percent": float(normal_count / total_count * 100) if total_count > 0 else 0,
            "status": "good",
        }
    
    # Recommendations
    if synthesis["overview"]["completeness_percent"] is not None:
        if synthesis["overview"]["completeness_percent"] < 90:
            synthesis["recommendations"].append(
                "High missingness detected - implement imputation strategy or investigate data collection gaps"
            )
    
    if 'quality' in results_dict and not results_dict['quality']['validity_issues'].empty:
        synthesis["recommendations"].append(
            "Apply constraint-based validation to flag and handle out-of-range values"
        )
    
    if 'quality' in results_dict and not results_dict['quality']['outlier_detections'].empty:
        synthesis["recommendations"].append(
            "Implement outlier detection in data pipeline or flag for manual review"
        )
    
    # Data readiness
    if synthesis["overview"]["completeness_percent"] is not None:
        if synthesis["overview"]["completeness_percent"] > 95:
            synthesis["data_readiness"]["raw_data_quality"] = "high"
        elif synthesis["overview"]["completeness_percent"] > 80:
            synthesis["data_readiness"]["raw_data_quality"] = "moderate"
        else:
            synthesis["data_readiness"]["raw_data_quality"] = "low"
    
    synthesis["data_readiness"]["recommended_next_steps"] = [
        "Apply identified constraint-based cleaning rules",
        "Implement outlier handling strategy (flag vs remove)",
        "Create standardized parameter mappings",
        "Build temporal aggregation pipeline",
        "Implement dashboard-ready views",
    ]
    
    return synthesis


def create_executive_summary(synthesis):
    """Create human-readable executive summary."""
    
    summary = "="*70 + "\n"
    summary += "EXPLORATORY DATA ANALYSIS - EXECUTIVE SUMMARY\n"
    summary += "="*70 + "\n\n"
    
    # Overview
    summary += "DATASET OVERVIEW\n"
    summary += "-" * 70 + "\n"
    if synthesis["overview"]["total_rows"]:
        summary += f"  Total Records:        {synthesis['overview']['total_rows']:,}\n"
    if synthesis["overview"]["total_columns"]:
        summary += f"  Total Columns:        {synthesis['overview']['total_columns']}\n"
    if synthesis["overview"]["completeness_percent"]:
        summary += f"  Data Completeness:    {synthesis['overview']['completeness_percent']:.1f}%\n"
    
    summary += "\n"
    
    # Key Findings
    if synthesis["key_findings"]:
        summary += "KEY FINDINGS\n"
        summary += "-" * 70 + "\n"
        for i, finding in enumerate(synthesis["key_findings"], 1):
            summary += f"  {i}. {finding}\n"
        summary += "\n"
    
    # Quality Assessment
    summary += "QUALITY ASSESSMENT\n"
    summary += "-" * 70 + "\n"
    for dimension, assessment in synthesis["quality_dimensions"].items():
        status = assessment.get("status", "unknown").upper()
        summary += f"  {dimension.upper()}: {status}\n"
    summary += "\n"
    
    # Recommendations
    if synthesis["recommendations"]:
        summary += "RECOMMENDATIONS\n"
        summary += "-" * 70 + "\n"
        for i, rec in enumerate(synthesis["recommendations"], 1):
            summary += f"  {i}. {rec}\n"
        summary += "\n"
    
    # Data Readiness
    summary += "DATA READINESS\n"
    summary += "-" * 70 + "\n"
    if synthesis["data_readiness"]["raw_data_quality"]:
        summary += f"  Raw Data Quality:     {synthesis['data_readiness']['raw_data_quality'].upper()}\n"
    summary += "  Next Steps:\n"
    for i, step in enumerate(synthesis["data_readiness"]["recommended_next_steps"], 1):
        summary += f"    {i}. {step}\n"
    
    summary += "\n" + "="*70 + "\n"
    
    return summary


def main(nrows=None):
    """
    Run all exploratory analyses and synthesize findings.
    
    Parameters
    ----------
    nrows : int, optional
        Limit rows for testing
    
    Returns
    -------
    dict
        Synthesis results and summary report
    """
    print("\n" + "="*70)
    print("RUNNING COMPLETE EXPLORATORY DATA ANALYSIS")
    print("="*70)
    
    results = {}
    
    # 1. Data Profiling
    print("\n[1/5] Data Profiling...")
    try:
        results['profiling'] = data_profiling.main(nrows=nrows)
        print("[OK] Data profiling complete")
    except Exception as e:
        print(f"[ERROR] Data profiling failed: {e}")
    
    # 2. Missing Data Analysis
    print("\n[2/5] Missing Data Analysis...")
    try:
        results['missing'] = missing_data_analysis.main(nrows=nrows)
        print("[OK] Missing data analysis complete")
    except Exception as e:
        print(f"[ERROR] Missing data analysis failed: {e}")
    
    # 3. Statistical Tests
    print("\n[3/5] Statistical Tests...")
    try:
        results['stats'] = statistical_tests.main(nrows=nrows)
        print("[OK] Statistical tests complete")
    except Exception as e:
        print(f"[ERROR] Statistical tests failed: {e}")
    
    # 4. Quality Issues
    print("\n[4/5] Quality Issues Detection...")
    try:
        results['quality'] = quality_issues.main(nrows=nrows)
        print("[OK] Quality issues detection complete")
    except Exception as e:
        print(f"[ERROR] Quality issues detection failed: {e}")
    
    # 5. Synthesis
    print("\n[5/5] Synthesizing Findings...")
    try:
        synthesis = synthesize_findings(results)
        executive_summary = create_executive_summary(synthesis)
        
        print(executive_summary)
        
        # Save synthesis
        with open(f"{OUTPUT_EDA_PATH}/executive_summary.txt", 'w') as f:
            f.write(executive_summary)
        
        with open(f"{OUTPUT_EDA_PATH}/synthesis.json", 'w') as f:
            json.dump(synthesis, f, indent=2, default=str)
        
        print("\n[OK] Synthesis complete")
        print(f"[OK] Results saved to: {OUTPUT_EDA_PATH}")
    
    except Exception as e:
        print(f"[ERROR] Synthesis failed: {e}")
    
    print("\n" + "="*70)
    print("EDA COMPLETE - Ready for next phase (Data Cleaning & Quality Assessment)")
    print("="*70 + "\n")
    
    return {
        "individual_results": results,
        "synthesis": synthesis if 'synthesis' in locals() else None,
    }


if __name__ == "__main__":
    results = main()
