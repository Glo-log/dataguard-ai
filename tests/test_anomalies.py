import numpy as np
import pandas as pd
import pytest

from dataguard.anomaly_detection import detect_anomalies


def test_extreme_synthetic_measurement_flagged_and_reproducible(synthetic_measurements):
    frame = synthetic_measurements
    before = frame.copy(deep=True)
    first = detect_anomalies(frame, list(frame), contamination=0.05, random_state=42)
    second = detect_anomalies(frame, list(frame), contamination=0.05, random_state=42)
    assert first.rows.is_anomaly.iloc[-1]
    assert first.rows.anomaly_score.iloc[-1] == first.rows.anomaly_score.max()
    assert np.isfinite(first.rows.anomaly_score).all()
    pd.testing.assert_frame_equal(first.rows, second.rows)
    pd.testing.assert_frame_equal(frame, before)
    assert np.array_equal(first.rows.is_anomaly, first.rows.decision_function.lt(0))


def test_missing_infinite_constant_and_unsupported_features(synthetic_measurements):
    frame = synthetic_measurements.copy()
    frame.loc[0, "measurement_a"] = np.nan
    frame.loc[1, "measurement_b"] = np.inf
    frame["constant"] = 1
    frame["empty"] = np.nan
    frame["text"] = "a"
    result = detect_anomalies(frame, list(frame))
    assert set(result.features) == {"measurement_a", "measurement_b"}
    assert set(result.excluded) == {"constant", "empty", "text"}
    assert result.rows.imputed_feature_count.iloc[:2].tolist() == [1, 1]
    assert result.pipeline.named_steps["imputer"].strategy == "median"


@pytest.mark.parametrize("contamination", [0, -0.1, 0.51, np.nan, True, "auto"])
def test_invalid_contamination(synthetic_measurements, contamination):
    with pytest.raises(ValueError, match="contamination"):
        detect_anomalies(
            synthetic_measurements, list(synthetic_measurements), contamination=contamination
        )


@pytest.mark.parametrize("seed", [-1, 2**32, 1.5, True])
def test_invalid_random_state(synthetic_measurements, seed):
    with pytest.raises(ValueError, match="random_state"):
        detect_anomalies(synthetic_measurements, list(synthetic_measurements), random_state=seed)


@pytest.mark.parametrize(
    "frame,features",
    [
        (pd.DataFrame({"x": [1]}), ["x"]),
        (pd.DataFrame({"x": [1] * 10}), ["x"]),
        (pd.DataFrame({"x": [np.nan] * 10}), ["x"]),
        (pd.DataFrame({"x": range(10)}), []),
        (pd.DataFrame({"x": range(10)}), ["missing"]),
    ],
)
def test_unsupported_datasets(frame, features):
    with pytest.raises(ValueError):
        detect_anomalies(frame, features)
