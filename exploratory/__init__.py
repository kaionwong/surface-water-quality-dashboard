"""Exploratory Data Analysis module for surface water quality dataset."""

__version__ = "1.0.0"
__author__ = "Data Science Team"

from .utils import (
    load_data_chunked,
    plot_missing_heatmap,
    statistical_summary,
    flag_outliers,
    save_outputs,
)

__all__ = [
    "load_data_chunked",
    "plot_missing_heatmap",
    "statistical_summary",
    "flag_outliers",
    "save_outputs",
]
