@echo off
REM Run complete EDA synthesis with all 5 modules
REM This script uses the venv_surface_water_quality_dashboard environment

setlocal enabledelayedexpansion

set PYTHON_EXE=C:\Users\kai.wong\Dev\virtual_env\venv_surface_water_quality_dashboard\Scripts\python.exe
set PROJECT_ROOT=%~dp0

echo.
echo ================================================================
echo Surface Water Quality Dashboard - Exploratory Data Analysis
echo ================================================================
echo.

if not exist "!PYTHON_EXE!" (
    echo ERROR: Python executable not found at:
    echo !PYTHON_EXE!
    exit /b 1
)

echo Using Python: !PYTHON_EXE!
echo Project Root: !PROJECT_ROOT!
echo.

cd /d "!PROJECT_ROOT!"

echo Running complete EDA synthesis...
echo This will execute all 5 analysis modules in sequence.
echo.

"!PYTHON_EXE!" -m exploratory.eda_notebook

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================
    echo EDA COMPLETE
    echo ================================================================
    echo.
    echo Results saved to: output/eda_outputs/
    echo.
    echo Key files:
    echo   - EDA_Executive_Summary.md
    echo   - eda_concern_ranking.csv
    echo   - missing_data_summary.csv
    echo   - heatmap_missing_station_parameter.html
    echo.
) else (
    echo.
    echo ERROR: EDA synthesis failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

pause
