#!/usr/bin/env powershell
# Run individual EDA modules

param(
    [ValidateSet("profiling", "missing", "stats", "quality", "all")]
    [string]$Module = "all"
)

$Python = "C:\Users\kai.wong\Dev\virtual_env\venv_surface_water_quality_dashboard\Scripts\python.exe"

function Run-Module {
    param([string]$ModuleFile, [string]$ModuleName)
    
    Write-Host ""
    Write-Host "Running: $ModuleName" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    & $Python -m "exploratory.$ModuleFile"
}

Write-Host ""
Write-Host "Surface Water Quality Dashboard - EDA Modules" -ForegroundColor Green
Write-Host ""

switch ($Module) {
    "profiling" { Run-Module "data_profiling" "Data Profiling" }
    "missing"   { Run-Module "missing_data_analysis" "Missing Data Analysis" }
    "stats"     { Run-Module "statistical_tests" "Statistical Tests" }
    "quality"   { Run-Module "quality_issues" "Quality Issues" }
    "all"       {
        Run-Module "data_profiling" "Data Profiling"
        Run-Module "missing_data_analysis" "Missing Data Analysis"
        Run-Module "statistical_tests" "Statistical Tests"
        Run-Module "quality_issues" "Quality Issues"
        
        Write-Host ""
        Write-Host "Running Executive Summary..." -ForegroundColor Cyan
        Write-Host "=" * 60 -ForegroundColor Cyan
        & $Python -m exploratory.eda_notebook
    }
}

Write-Host ""
Write-Host "Results saved to: output/eda_outputs/" -ForegroundColor Green
