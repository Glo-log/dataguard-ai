import numpy as np
import pandas as pd
import pytest

from dataguard.cleaning import CleaningPlan, clean


def test_preview_does_not_mutate_source_and_logs_true_counts():
    frame = pd.DataFrame({"x": [1.0, None, 1.0], "category": [" A ", None, " A "]})
    original = frame.copy(deep=True)
    result = clean(
        frame,
        CleaningPlan(
            drop_duplicates=True,
            numeric_imputation={"x": "median"},
            categorical_imputation={"category": "constant"},
            standardize=["category"],
        ),
    )
    pd.testing.assert_frame_equal(frame, original)
    assert result.frame.x.isna().sum() == 0
    assert len(result.frame) == 2
    log = {v["operation"]: v for v in result.log}
    assert log["impute_numeric"]["affected_records"] == 1
    assert log["standardize_text"]["affected_records"] == 2
    assert log["drop_exact_duplicates"]["affected_records"] == 1
    assert log["impute_numeric"]["parameters"]["value"] == 1


def test_type_and_invalid_date_conversion_explicit():
    frame = pd.DataFrame({"x": ["1", "bad"], "date": ["31/12/2025", "invalid"]})
    result = clean(
        frame, CleaningPlan(conversions={"x": "numeric"}, date_formats={"date": "%d/%m/%Y"})
    )
    assert result.frame.x.iloc[0] == 1
    assert pd.isna(result.frame.x.iloc[1])
    assert pd.isna(result.frame.date.iloc[1])
    assert result.log[1]["parameters"]["new_missing"] == 1


@pytest.mark.parametrize(
    "plan",
    [
        CleaningPlan(numeric_imputation={"x": "mean"}),
        CleaningPlan(categorical_imputation={"x": "mode"}),
        CleaningPlan(conversions={"missing": "numeric"}),
        CleaningPlan(conversions={"x": "arbitrary"}),
    ],
)
def test_undefined_or_invalid_cleaning_rejected(plan):
    with pytest.raises(ValueError):
        clean(pd.DataFrame({"x": [np.nan, np.nan]}), plan)


def test_infinite_not_silently_replaced_and_mean_uses_finite_values():
    result = clean(
        pd.DataFrame({"x": [1.0, 3.0, None, np.inf]}),
        CleaningPlan(numeric_imputation={"x": "mean"}),
    )
    assert result.frame.x.iloc[2] == 2
    assert np.isinf(result.frame.x.iloc[3])


def test_mode_and_empty_single_row_cleaning():
    result = clean(
        pd.DataFrame({"x": ["b", "b", None]}), CleaningPlan(categorical_imputation={"x": "mode"})
    )
    assert result.frame.x.tolist() == ["b", "b", "b"]
    assert len(clean(pd.DataFrame({"x": [1]}), CleaningPlan(drop_duplicates=True)).frame) == 1
    assert clean(pd.DataFrame({"x": []}), CleaningPlan()).frame.empty
