#!/usr/bin/env python3
"""
Standalone runner for Surface Water Quality Dashboard Exploratory Data Analysis.

This script runs the complete EDA synthesis with all 5 analysis modules.

Usage:
    python run_eda.py              Run complete synthesis
    python -m exploratory          Same (from project root)
    
For Jupyter notebook:
    jupyter notebook notebooks/eda/eda_interactive.ipynb
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from exploratory import eda_notebook


def main():
    """Run complete EDA synthesis."""
    print("\n" + "="*70)
    print("SURFACE WATER QUALITY DASHBOARD")
    print("Exploratory Data Analysis")
    print("="*70)
    print(f"\nProject Root: {project_root}")
    print(f"Data Location: {project_root / 'data' / 'raw'}")
    print(f"Output Location: {project_root / 'output' / 'eda_outputs'}\n")
    
    eda_notebook.main()
    
    print("\n" + "="*70)
    print("[OK] EDA Complete!")
    print("="*70)
    print(f"\nResults saved to: {project_root / 'output' / 'eda_outputs'}")
    print("\nKey files:")
    print("  - executive_summary.txt")
    print("  - synthesis.json")
    print("  - Various CSV and HTML outputs")
    print()


if __name__ == '__main__':
    main()
