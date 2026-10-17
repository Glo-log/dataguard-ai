"""Explicit cleaning on a copy, suitable for preview before adoption."""

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class CleaningPlan:
    drop_duplicates: bool = False
    numeric_imputation: dict[str, str] = field(default_factory=dict)
    categorical_imputation: dict[str, str] = field(default_factory=dict)
    constant: str = "Unknown"
    conversions: dict[str, str] = field(default_factory=dict)
    standardize: list[str] = field(default_factory=list)
    date_formats: dict[str, str] = field(default_factory=dict)


@dataclass
class CleaningResult:
    frame: pd.DataFrame
    log: list[dict]
    plan: dict


def clean(frame: pd.DataFrame, plan: CleaningPlan) -> CleaningResult:
    """Apply conversion, text normalization, imputation, then exact deduplication.

    Logs count changed records per operation (counts can overlap). Invalid dates
    and numeric conversions become missing only when the conversion was selected.
    Infinite values require review and cannot be used to compute an imputation value.
    """
    output = frame.copy(deep=True)
    log: list[dict] = []
    selected = (
        set(plan.numeric_imputation)
        | set(plan.categorical_imputation)
        | set(plan.conversions)
        | set(plan.standardize)
        | set(plan.date_formats)
    )
    if selected - set(frame.columns):
        raise ValueError(f"Missing columns: {sorted(selected - set(frame.columns))}")

    def record(operation: str, column: str, before: pd.Series, params: dict[str, Any]) -> None:
        after = output[column]
        same = before.eq(after).fillna(False) | (before.isna() & after.isna())
        log.append(
            {
                "operation": operation,
                "columns": [column],
                "affected_records": int((~same).sum()),
                "parameters": params,
            }
        )

    for c, dtype in plan.conversions.items():
        before = output[c].copy()
        if dtype == "numeric":
            output[c] = pd.to_numeric(output[c], errors="coerce")
        elif dtype == "string":
            output[c] = output[c].astype("string")
        else:
            raise ValueError("Conversion must be numeric or string. Dates use date_formats.")
        record(
            "convert_type",
            c,
            before,
            {
                "dtype": dtype,
                "errors": "coerce" if dtype == "numeric" else "raise",
                "before_dtype": str(before.dtype),
                "after_dtype": str(output[c].dtype),
            },
        )
    for c, fmt in plan.date_formats.items():
        before = output[c].copy()
        output[c] = pd.to_datetime(output[c], errors="coerce", format=fmt)
        record(
            "parse_date",
            c,
            before,
            {
                "format": fmt,
                "errors": "coerce",
                "new_missing": int((before.notna() & output[c].isna()).sum()),
            },
        )
    for c in plan.standardize:
        if pd.api.types.is_numeric_dtype(output[c]):
            raise ValueError(f"{c} is numeric; text standardization requires a text column.")
        before = output[c].copy()
        output[c] = output[c].astype("string").str.strip().str.casefold()
        record("standardize_text", c, before, {"strip": True, "case": "casefold"})
    for c, strategy in plan.numeric_imputation.items():
        if (
            strategy not in {"mean", "median"}
            or not pd.api.types.is_numeric_dtype(output[c])
            or pd.api.types.is_bool_dtype(output[c])
        ):
            raise ValueError(f"Choose mean/median for a numerical column: {c}.")
        before = output[c].copy()
        finite = pd.to_numeric(before, errors="coerce").replace([np.inf, -np.inf], np.nan)
        value = finite.mean() if strategy == "mean" else finite.median()
        if pd.isna(value):
            raise ValueError(f"{c} has no finite values; an imputation statistic is undefined.")
        output[c] = output[c].astype(float).fillna(float(value))
        record("impute_numeric", c, before, {"strategy": strategy, "value": float(value)})
    for c, strategy in plan.categorical_imputation.items():
        if strategy not in {"mode", "constant"}:
            raise ValueError("Categorical imputation must use mode or constant.")
        before = output[c].copy()
        modes = before.mode(dropna=True)
        if strategy == "mode" and modes.empty:
            raise ValueError(f"{c} is all missing; mode is undefined. Choose a constant.")
        value = modes.iloc[0] if strategy == "mode" else plan.constant
        output[c] = output[c].astype(object).where(output[c].notna(), value)
        record("impute_categorical", c, before, {"strategy": strategy, "value": str(value)})
    if plan.drop_duplicates:
        count = int(output.duplicated().sum())
        output = output.drop_duplicates(keep="first")
        log.append(
            {
                "operation": "drop_exact_duplicates",
                "columns": list(output.columns),
                "affected_records": count,
                "parameters": {"keep": "first"},
            }
        )
    return CleaningResult(output, log, asdict(plan))
