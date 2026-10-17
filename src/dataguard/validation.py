"""Configurable validation with a documented, project-specific score."""

import math
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from dataguard.profiling import iqr_mask, numeric_columns


@dataclass(frozen=True)
class ColumnRule:
    dtype: str | None = None
    required: bool = True
    minimum: float | None = None
    maximum: float | None = None
    allowed: list[Any] | None = None
    date_format: str = "ISO8601"

    def __post_init__(self) -> None:
        if self.dtype not in {None, "numeric", "integer", "string", "date"}:
            raise ValueError("dtype must be numeric, integer, string, date, or null.")
        if type(self.required) is not bool:
            raise ValueError("required must be true or false.")
        for value in (self.minimum, self.maximum):
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError("Bounds must be finite numbers.")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("minimum cannot exceed maximum.")
        if self.allowed is not None and not isinstance(self.allowed, list):
            raise ValueError("allowed must be a JSON list.")
        if not isinstance(self.date_format, str):
            raise ValueError("date_format must be a string.")


@dataclass
class QualityReport:
    rows: int
    columns: int
    score: float | None
    indicators: dict
    findings: list[dict] = field(default_factory=list)
    rules: dict = field(default_factory=dict)
    methodology: str = (
        "Project score: weighted mean of completeness (0.4), uniqueness (0.2), "
        "validity (0.4). Completeness=1-missing cells/all cells; uniqueness=1-duplicate "
        "rows after first/all rows; validity=1-failed/evaluated rule opportunities. "
        "Validity checks exclude missing cells; absent required columns fail one schema "
        "opportunity. Unavailable categories are omitted and weights renormalized. "
        "IQR and retail context flags are excluded. Not an industry standard or a guarantee."
    )

    def to_dict(self) -> dict:
        return asdict(self)

    def findings_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            self.findings,
            columns=[
                "category",
                "rule",
                "column",
                "severity",
                "count",
                "row_positions",
                "recommendation",
            ],
        )


def parse_rules(payload: dict) -> dict[str, ColumnRule]:
    """Accept a JSON mapping of column names to explicit rule definitions."""
    if not isinstance(payload, dict) or not all(
        isinstance(c, str) and isinstance(v, dict) for c, v in payload.items()
    ):
        raise ValueError("Rules must map column names to objects.")
    try:
        return {c: ColumnRule(**v) for c, v in payload.items()}
    except TypeError as exc:
        raise ValueError(f"Unsupported rule property: {exc}") from exc


def retail_rules() -> dict[str, ColumnRule]:
    """Negative quantities are allowed: returns/cancellations need context."""
    return {
        "InvoiceNo": ColumnRule("string"),
        "StockCode": ColumnRule("string"),
        "Description": ColumnRule("string"),
        "Quantity": ColumnRule("integer"),
        "InvoiceDate": ColumnRule("date"),
        "UnitPrice": ColumnRule("numeric", minimum=0),
        "CustomerID": ColumnRule("string"),
        "Country": ColumnRule("string"),
    }


def validate(
    frame: pd.DataFrame,
    rules: dict[str, ColumnRule] | None = None,
    *,
    include_outliers: bool = True,
    retail_context: bool = False,
) -> QualityReport:
    """Evaluate independent rule opportunities; retain only 20 example positions per finding."""
    rules = rules or {}
    n, p = frame.shape
    findings: list[dict] = []
    evaluated = 0
    failed = 0

    def add(
        category: str, rule: str, column: str, mask: pd.Series, severity: str, action: str
    ) -> None:
        flags = mask.fillna(False).to_numpy(dtype=bool)
        count = int(flags.sum())
        if count:
            findings.append(
                {
                    "category": category,
                    "rule": rule,
                    "column": column,
                    "severity": severity,
                    "count": count,
                    "row_positions": np.flatnonzero(flags)[:20].tolist(),
                    "recommendation": action,
                }
            )

    def check(rule: str, column: str, mask: pd.Series, eligible: pd.Series, action: str) -> None:
        nonlocal evaluated, failed
        evaluated += int(eligible.sum())
        failed += int((mask & eligible).sum())
        add("validity", rule, column, mask & eligible, "warning", action)

    for c in frame:
        add(
            "completeness",
            "missing",
            c,
            frame[c].isna(),
            "warning",
            "Check source availability; impute only with a justified policy.",
        )
    if p:
        add(
            "uniqueness",
            "exact_duplicate",
            "*",
            frame.duplicated(),
            "warning",
            "Review repeated rows before removing copies; identical transactions can be legitimate.",
        )
    for c, rule in rules.items():
        if c not in frame:
            if rule.required:
                evaluated += 1
                failed += 1
                findings.append(
                    {
                        "category": "validity",
                        "rule": "missing_column",
                        "column": c,
                        "severity": "error",
                        "count": 1,
                        "row_positions": [],
                        "recommendation": "Supply the required column or change the schema rule.",
                    }
                )
            continue
        values = frame[c]
        present = values.notna()
        numbers = pd.to_numeric(values, errors="coerce")
        finite = present & numbers.notna() & np.isfinite(numbers.fillna(np.nan).astype(float))
        if rule.dtype in {"numeric", "integer"}:
            invalid = present & numbers.isna()
            if rule.dtype == "integer":
                invalid |= finite & numbers.mod(1).ne(0)
            check(
                "invalid_" + rule.dtype,
                c,
                invalid,
                present,
                "Review values incompatible with the configured numeric type.",
            )
        if rule.dtype == "string":
            check(
                "invalid_string",
                c,
                present & ~values.map(lambda v: isinstance(v, str)),
                present,
                "Convert confirmed identifiers/text explicitly; preserve leading zeros.",
            )
        if rule.dtype == "date":
            dates = pd.to_datetime(values, errors="coerce", format=rule.date_format)
            check(
                "invalid_date",
                c,
                present & dates.isna(),
                present,
                "Check the expected date format before coercing invalid values to missing.",
            )
        if rule.minimum is not None:
            check(
                "below_minimum",
                c,
                numbers.lt(rule.minimum),
                finite,
                f"Review values below configured minimum {rule.minimum}.",
            )
        if rule.maximum is not None:
            check(
                "above_maximum",
                c,
                numbers.gt(rule.maximum),
                finite,
                f"Review values above configured maximum {rule.maximum}.",
            )
        if rule.allowed is not None:
            check(
                "unexpected_category",
                c,
                present & ~values.isin(rule.allowed),
                present,
                "Review against the configured allowed categories; do not infer validity from frequency.",
            )

    for c in dict.fromkeys(
        numeric_columns(frame)
        + [
            c
            for c, r in rules.items()
            if c in frame
            and (
                r.dtype in {"numeric", "integer"} or r.minimum is not None or r.maximum is not None
            )
        ]
    ):
        values = pd.to_numeric(frame[c], errors="coerce")
        check(
            "infinite",
            c,
            values.isin([np.inf, -np.inf]),
            values.notna(),
            "Investigate infinite values; replace only with an explicit policy.",
        )
        if include_outliers:
            add(
                "potential_outliers",
                "iqr_1.5",
                c,
                iqr_mask(values),
                "info",
                "Statistical tail observation; investigate context. Not a confirmed error.",
            )
    if retail_context:
        context = [
            (
                "InvoiceNo",
                "cancellation",
                lambda s: s.astype("string").str.upper().str.startswith("C"),
                "Cancellation marker; retain for return/cancellation analysis.",
            ),
            (
                "Quantity",
                "negative_quantity",
                lambda s: pd.to_numeric(s, errors="coerce").lt(0),
                "May represent returns, cancellations, or stock adjustments; not automatically invalid.",
            ),
            (
                "Quantity",
                "zero_quantity",
                lambda s: pd.to_numeric(s, errors="coerce").eq(0),
                "Review zero quantity using transaction context.",
            ),
            (
                "UnitPrice",
                "zero_price",
                lambda s: pd.to_numeric(s, errors="coerce").eq(0),
                "May be a promotion or adjustment; inspect source context.",
            ),
        ]
        for c, name, predicate, action in context:
            if c in frame:
                add("business_context", name, c, predicate(frame[c]), "info", action)
    completeness = 1 - float(frame.isna().sum().sum()) / (n * p) if n and p else None
    uniqueness = 1 - float(frame.duplicated().sum()) / n if n and p else None
    validity = 1 - failed / evaluated if evaluated else None
    indicators = {
        "completeness": completeness,
        "uniqueness": uniqueness,
        "validity": validity,
        "validity_evaluated": evaluated,
        "validity_failed": failed,
    }
    weights = {"completeness": 0.4, "uniqueness": 0.2, "validity": 0.4}
    available = {k: w for k, w in weights.items() if indicators[k] is not None}
    score = (
        round(
            100 * sum(indicators[k] * w for k, w in available.items()) / sum(available.values()), 2
        )
        if available and n and p
        else None
    )
    return QualityReport(
        n, p, score, indicators, findings, {c: asdict(r) for c, r in rules.items()}
    )
