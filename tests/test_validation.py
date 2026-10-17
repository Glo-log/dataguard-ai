import numpy as np
import pandas as pd
import pytest

from dataguard.validation import ColumnRule, parse_rules, retail_rules, validate


def test_type_date_range_category_infinity_and_missing_rules():
    frame = pd.DataFrame(
        {
            "number": ["1", "wrong", "inf", None],
            "date": ["2025-01-01", "bad", "2025-02-01", None],
            "status": ["paid", "other", "paid", None],
        }
    )
    report = validate(
        frame,
        {
            "number": ColumnRule("numeric", minimum=0, maximum=2),
            "date": ColumnRule("date"),
            "status": ColumnRule(allowed=["paid"]),
        },
    )
    rules = {(r["column"], r["rule"]): r["count"] for r in report.findings}
    assert rules[("number", "invalid_numeric")] == 1
    assert rules[("number", "infinite")] == 1
    assert rules[("date", "invalid_date")] == 1
    assert rules[("status", "unexpected_category")] == 1
    assert rules[("number", "missing")] == 1


def test_score_formula_is_explicit_and_outliers_excluded():
    # Four cells: one missing; one repeat after first; no validity opportunities.
    frame = pd.DataFrame({"category": ["a", "a", None, "b"]})
    report = validate(frame)
    assert report.indicators["completeness"] == 0.75
    assert report.indicators["uniqueness"] == 0.75
    assert report.indicators["validity"] is None
    assert report.score == 75
    assert validate(pd.DataFrame({"x": [0, 1, 2, 3, 4, 100]})).score == 100


def test_rule_opportunity_score_denominator():
    report = validate(pd.DataFrame({"x": [-1, 2]}), {"x": ColumnRule("numeric", minimum=0)})
    # Type, range, finite checks: six opportunities; one range violation.
    assert report.indicators["validity_evaluated"] == 6
    assert report.indicators["validity_failed"] == 1
    assert report.score == pytest.approx(93.33)


def test_required_optional_columns_and_empty_dataset():
    report = validate(
        pd.DataFrame({"x": [1]}), {"missing": ColumnRule(), "optional": ColumnRule(required=False)}
    )
    assert [f["column"] for f in report.findings if f["rule"] == "missing_column"] == ["missing"]
    assert report.indicators["validity"] == 0.5  # one schema failure and one finite check
    assert validate(pd.DataFrame({"x": []})).score is None


def test_mixed_integer_type_and_date_format():
    report = validate(
        pd.DataFrame({"x": [1, 1.5, "bad"], "date": ["31/12/2025", "no", "01/01/2025"]}),
        {"x": ColumnRule("integer"), "date": ColumnRule("date", date_format="%d/%m/%Y")},
    )
    assert next(f for f in report.findings if f["rule"] == "invalid_integer")["count"] == 2
    assert next(f for f in report.findings if f["rule"] == "invalid_date")["count"] == 1


def test_retail_returns_are_context_not_negative_quantity_errors(synthetic_retail):
    before = synthetic_retail.copy(deep=True)
    report = validate(synthetic_retail, retail_rules(), retail_context=True)
    negative = next(f for f in report.findings if f["rule"] == "negative_quantity")
    assert negative["category"] == "business_context" and negative["count"] == 1
    assert not any(
        f["rule"] == "below_minimum" and f["column"] == "Quantity" for f in report.findings
    )
    assert any(f["rule"] == "below_minimum" and f["column"] == "UnitPrice" for f in report.findings)
    pd.testing.assert_frame_equal(synthetic_retail, before)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"x": []},
        {"x": {"dtype": "imaginary"}},
        {"x": {"minimum": 5, "maximum": 0}},
        {"x": {"allowed": "a"}},
        {"x": {"required": "yes"}},
        {"x": {"minimum": float("inf")}},
        {"x": {"unknown": True}},
    ],
)
def test_invalid_rules_rejected(payload):
    with pytest.raises(ValueError):
        parse_rules(payload)


def test_all_null_finite_values_and_position_examples():
    report = validate(
        pd.DataFrame({"x": [np.nan] * 30}, index=[100] * 30), {"x": ColumnRule("numeric")}
    )
    assert report.indicators["validity_evaluated"] == 0
    finding = next(f for f in report.findings if f["rule"] == "missing")
    assert finding["count"] == 30
    assert finding["row_positions"] == list(range(20))
