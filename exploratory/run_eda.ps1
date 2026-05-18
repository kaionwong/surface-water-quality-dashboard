#!/usr/bin/env powershell
# Surface Water Quality Dashboard - Run EDA Synthesis
# This script uses the venv_surface_water_quality_dashboard environment

$PythonExe = "C:\Users\kai.wong\Dev\virtual_env\venv_surface_water_quality_dashboard\Scripts\python.exe"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Surface Water Quality Dashboard - Exploratory Data Analysis" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: Python executable not found at:" -ForegroundColor Red
    Write-Host $PythonExe -ForegroundColor Red
    exit 1
}

Write-Host "Using Python: $PythonExe" -ForegroundColor Green
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Green
Write-Host ""

Set-Location -Path $ProjectRoot

Write-Host "Running complete EDA synthesis..." -ForegroundColor Yellow
Write-Host "This will execute all 5 analysis modules in sequence." -ForegroundColor Yellow
Write-Host ""

& $PythonExe -m exploratory.eda_notebook

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "EDA COMPLETE" -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Results saved to: output/eda_outputs/" -ForegroundColor Green
    Write-Host ""
    Write-Host "Key files:" -ForegroundColor Cyan
    Write-Host "  - EDA_Executive_Summary.md" -ForegroundColor White
    Write-Host "  - eda_concern_ranking.csv" -ForegroundColor White
    Write-Host "  - missing_data_summary.csv" -ForegroundColor White
    Write-Host "  - heatmap_missing_station_parameter.html" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "ERROR: EDA synthesis failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
