"""
Entry point for running exploratory analysis as a Python module.

Run complete synthesis:
    python -m exploratory
    
Run individual modules:
    python -m exploratory profiling
    python -m exploratory missing
    python -m exploratory stats
    python -m exploratory quality
"""

import sys
import argparse
from . import (
    data_profiling,
    missing_data_analysis,
    statistical_tests,
    quality_issues,
    eda_notebook,
)


def run_module(module_name: str):
    """Run individual analysis module by name."""
    modules = {
        'profiling': ('Data Profiling', data_profiling.main),
        'missing': ('Missing Data Analysis', missing_data_analysis.main),
        'stats': ('Statistical Tests', statistical_tests.main),
        'quality': ('Quality Issues Detection', quality_issues.main),
    }
    
    if module_name not in modules:
        print(f"\n[ERROR] Unknown module: {module_name}")
        print(f"Available modules: {', '.join(modules.keys())}")
        sys.exit(1)
    
    display_name, func = modules[module_name]
    print(f"\n{'='*70}")
    print(f"Running: {display_name}")
    print(f"{'='*70}\n")
    func()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="python -m exploratory",
        description="Surface Water Quality Dashboard - Exploratory Data Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m exploratory              Run complete EDA synthesis
  python -m exploratory profiling    Run data profiling only
  python -m exploratory missing      Run missing data analysis only
  python -m exploratory stats        Run statistical tests only
  python -m exploratory quality      Run quality issues only
        """
    )
    
    parser.add_argument(
        'module',
        nargs='?',
        default='all',
        choices=['all', 'profiling', 'missing', 'stats', 'quality'],
        help='Which module to run (default: all for complete synthesis)'
    )
    
    args = parser.parse_args()
    
    if args.module == 'all':
        eda_notebook.main()
    else:
        run_module(args.module)


if __name__ == '__main__':
    main()
