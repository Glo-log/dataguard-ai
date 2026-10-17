"""Portable, strict JSON and CSV exports."""

import json
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd


def _portable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _portable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [_portable(v) for v in value]
    if isinstance(value, (np.integer, np.bool_)):
        return value.item()
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.isoformat()
    return value


def json_bytes(payload: dict | list) -> bytes:
    """Reject nonportable JSON numbers; explicit null replaces nonfinite statistics."""
    return (
        json.dumps(_portable(payload), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")


def csv_bytes(frame: pd.DataFrame, *, spreadsheet_safe: bool = False) -> bytes:
    """UTF-8 CSV; optional formula protection changes dangerous text explicitly.

    Raw exports preserve values. The UI explains the formula-protection option.
    Negative numeric values remain numeric in either mode.
    """
    export = frame.copy(deep=True)
    if spreadsheet_safe:
        for c in export.select_dtypes(include=["object", "string"]):
            export[c] = export[c].map(
                lambda v: (
                    "'" + v
                    if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@"))
                    else v
                )
            )
    return export.to_csv(index=False, lineterminator="\n").encode("utf-8-sig")


def anomaly_export(frame: pd.DataFrame, rows: pd.DataFrame) -> pd.DataFrame:
    """Use positional references, with reserved output names checked explicitly."""
    if len(frame) != len(rows) or not np.array_equal(rows["row_position"], np.arange(len(frame))):
        raise ValueError("Anomaly results do not align with this dataset revision.")
    if set(frame.columns) & set(rows.columns):
        raise ValueError("Source columns collide with reserved anomaly result column names.")
    return pd.concat([rows.reset_index(drop=True), frame.reset_index(drop=True)], axis=1)
