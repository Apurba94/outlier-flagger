"""Flag outliers with IQR, z-score and modified z-score methods."""
from .core import iqr_outliers, zscore_outliers, mad_outliers, grubbs_test, flag_columns

__version__ = "0.1.0"
__all__ = ["iqr_outliers", "zscore_outliers", "mad_outliers", "grubbs_test", "flag_columns"]
