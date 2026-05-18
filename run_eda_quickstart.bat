@echo off
REM ==============================================================================
REM Quick Start: Surface Water Quality Dashboard - EDA
REM ==============================================================================
REM This script activates the correct Python virtual environment and runs the EDA
REM ==============================================================================

set VENV_PATH=C:\Users\kai.wong\Dev\virtual_env\venv_etl_for_ecol_analytics\Scripts

if not exist "%VENV_PATH%\python.exe" (
    echo ERROR: Virtual environment not found at:
    echo %VENV_PATH%
    echo.
    echo Please ensure venv_etl_for_ecol_analytics is installed
    pause
    exit /b 1
)

cd /d "%~dp0"

echo.
echo ==============================================================================
echo SURFACE WATER QUALITY DASHBOARD - EXPLORATORY DATA ANALYSIS
echo ==============================================================================
echo.
echo Python: %VENV_PATH%\python.exe
echo Working Directory: %cd%
echo.

REM Run the EDA synthesis
"%VENV_PATH%\python.exe" -m exploratory

pause
