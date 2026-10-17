"""Dataset summaries that leave inputs untouched."""

import numpy as np
import pandas as pd


def numeric_columns(frame: pd.DataFrame) -> list[str]:
    """Real numerical columns, excluding boolean indicators."""
    return [
        c for c in frame.select_dtypes(include="number") if not pd.api.types.is_bool_dtype(frame[c])
    ]


def column_profile(frame: pd.DataFrame) -> pd.DataFrame:
    """Return missingness, cardinality, dtype, and numeric/categorical roles."""
    numeric = numeric_columns(frame)
    return pd.DataFrame(
        [
            {
                "column": str(c),
                "dtype": str(frame[c].dtype),
                "role": "numeric" if c in numeric else "categorical / datetime",
                "missing_count": int(frame[c].isna().sum()),
                "missing_pct": float(frame[c].isna().mean() * 100) if len(frame) else 0.0,
                "unique_count": int(frame[c].nunique(dropna=True)),
            }
            for c in frame
        ],
        columns=["column", "dtype", "role", "missing_count", "missing_pct", "unique_count"],
    )


def profile(frame: pd.DataFrame) -> dict:
    """High-level counts, with duplicates defined as repeats after the first row."""
    return {
        "rows": len(frame),
        "columns": len(frame.columns),
        "missing_cells": int(frame.isna().sum().sum()),
        "duplicate_rows": int(frame.duplicated().sum()) if len(frame.columns) else 0,
        "numeric_columns": numeric_columns(frame),
        "categorical_columns": [c for c in frame if c not in numeric_columns(frame)],
        "memory_bytes": int(frame.memory_usage(deep=True).sum()),
    }


def iqr_mask(series: pd.Series, multiplier: float = 1.5) -> pd.Series:
    """Flag potential outliers; zero IQR produces no flags, not invented bounds."""
    values = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)
    q1, q3 = values.quantile([0.25, 0.75])
    width = q3 - q1
    if not np.isfinite(width) or width <= 0:
        return pd.Series(False, index=series.index)
    return ((values < q1 - multiplier * width) | (values > q3 + multiplier * width)).fillna(False)
