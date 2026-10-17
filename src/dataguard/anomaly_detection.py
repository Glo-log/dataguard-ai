"""Reproducible, in-sample Isolation Forest screening, never automatic correction."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from dataguard.profiling import numeric_columns

MIN_ROWS = 10
MAX_MODEL_ROWS = 50_000


@dataclass
class AnomalyResult:
    rows: pd.DataFrame
    features: list[str]
    excluded: dict[str, str]
    parameters: dict
    pipeline: Pipeline


def detect_anomalies(
    frame: pd.DataFrame,
    features: list[str],
    *,
    contamination: float = 0.05,
    random_state: int = 42,
) -> AnomalyResult:
    """Median-impute finite numerical features and fit a deterministic forest.

    Higher anomaly_score means more unusual (-score_samples). decision_function
    below zero is flagged. Scores are relative, not probabilities or accuracy.
    Returned positional row references preserve alignment even for duplicate indices.
    """
    if not MIN_ROWS <= len(frame) <= MAX_MODEL_ROWS:
        raise ValueError(f"Anomaly screening requires {MIN_ROWS}–{MAX_MODEL_ROWS:,} rows.")
    if (
        isinstance(contamination, bool)
        or not isinstance(contamination, (int, float))
        or not 0 < contamination <= 0.5
    ):
        raise ValueError("contamination must be a number in (0, 0.5].")
    if type(random_state) is not int or not 0 <= random_state < 2**32:
        raise ValueError("random_state must be an integer between 0 and 2**32-1.")
    if not features or len(features) != len(set(features)):
        raise ValueError("Select at least one distinct numerical feature.")
    if set(features) - set(frame.columns):
        raise ValueError("Selected feature columns are missing from the dataset.")
    selected = []
    excluded = {}
    numeric = numeric_columns(frame)
    for c in features:
        if c not in numeric:
            excluded[c] = "Unsupported non-numerical feature"
            continue
        values = frame[c].replace([np.inf, -np.inf], np.nan)
        if values.notna().sum() == 0:
            excluded[c] = "No finite observations"
        elif values.nunique(dropna=True) < 2:
            excluded[c] = "Constant feature"
        else:
            selected.append(c)
    if not selected:
        raise ValueError("No variable finite numerical features remain after exclusions.")
    matrix = frame[selected].replace([np.inf, -np.inf], np.nan).astype(float)
    pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "forest",
                IsolationForest(
                    n_estimators=200,
                    contamination=float(contamination),
                    random_state=random_state,
                    n_jobs=1,
                ),
            ),
        ]
    )
    pipeline.fit(matrix)
    rows = pd.DataFrame(
        {
            "row_position": np.arange(len(frame)),
            "anomaly_label": pipeline.predict(matrix),
            "anomaly_score": -pipeline.score_samples(matrix),
            "decision_function": pipeline.decision_function(matrix),
            "imputed_feature_count": matrix.isna().sum(axis=1).to_numpy(),
        }
    )
    rows["is_anomaly"] = rows["anomaly_label"].eq(-1)
    return AnomalyResult(
        rows,
        selected,
        excluded,
        {
            "contamination": float(contamination),
            "random_state": random_state,
            "n_estimators": 200,
            "imputation": "median",
            "scoring": "in-sample",
            "infinite_values": "treated as missing for modeling only",
        },
        pipeline,
    )
