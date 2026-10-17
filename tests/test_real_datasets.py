"""Offline integration tests against real, attributed UCI coverage samples."""

import hashlib
import json
import zipfile

import numpy as np
import pandas as pd
import pytest

from dataguard.anomaly_detection import detect_anomalies
from dataguard.validation import retail_rules, validate
from scripts.download_data import extract_verified
from scripts.preprocess_data import WINE_FEATURES, retail_sample_positions, wine_sample_positions
from tests.conftest import ROOT

pytestmark = pytest.mark.integration


def test_bundled_samples_match_provenance():
    manifest = json.loads((ROOT / "data/sample/provenance.json").read_text())
    for filename, info in manifest["samples"].items():
        path = ROOT / "data/sample" / filename
        assert hashlib.sha256(path.read_bytes()).hexdigest() == info["sha256"]
        assert len(pd.read_csv(path)) == info["rows"]
        assert len(info["source_positions_zero_based"]) == info["rows"]
        assert info["population_representative"] is False


def test_retail_validation_real_missing_duplicate_returns(retail_sample):
    original = retail_sample.copy(deep=True)
    report = validate(retail_sample, retail_rules(), retail_context=True)
    assert retail_sample.shape == (1200, 8)
    assert retail_sample.CustomerID.isna().any()
    assert retail_sample.Description.isna().any()
    assert retail_sample.duplicated().any()
    assert any(f["rule"] == "negative_quantity" for f in report.findings)
    assert any(f["rule"] == "below_minimum" and f["column"] == "UnitPrice" for f in report.findings)
    assert not any(f["rule"] == "invalid_date" for f in report.findings)
    assert all(c in retail_sample for c in retail_rules())
    pd.testing.assert_frame_equal(retail_sample, original)


def test_wine_measurements_screened_without_quality_target(wine_sample):
    before = wine_sample.copy(deep=True)
    first = detect_anomalies(wine_sample, WINE_FEATURES)
    second = detect_anomalies(wine_sample, WINE_FEATURES)
    assert wine_sample.shape == (400, 12)
    assert "quality" not in first.features and len(first.features) == 11
    assert 0 < first.rows.is_anomaly.sum() < len(wine_sample)
    assert np.isfinite(first.rows.anomaly_score).all()
    pd.testing.assert_frame_equal(first.rows, second.rows)
    pd.testing.assert_frame_equal(wine_sample, before)


def test_sample_validation_matches_measured_reference(retail_sample):
    reference = json.loads((ROOT / "reports/reference/sample_results.json").read_text())
    report = validate(retail_sample, retail_rules(), retail_context=True)
    assert report.to_dict() == reference["retail"]["quality"]


def test_seeded_coverage_sampling_is_deterministic(retail_sample, wine_sample):
    first = retail_sample_positions(retail_sample, n=200)
    assert first == retail_sample_positions(retail_sample, n=200)
    assert len(first) == len(set(first)) == 200
    assert wine_sample_positions(wine_sample, n=100) == wine_sample_positions(wine_sample, n=100)


def test_checksum_and_zip_allowlist_reject_tampering(tmp_path):
    archive = tmp_path / "fixture.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("allowed.csv", "x\n1\n")
        output.writestr("../outside.txt", "do not extract")
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    spec = {"sha256": checksum, "members": ["allowed.csv"]}
    extracted = extract_verified(archive, spec, tmp_path)
    assert [p.name for p in extracted] == ["allowed.csv"]
    assert not (tmp_path.parent / "outside.txt").exists()
    with pytest.raises(ValueError, match="Checksum"):
        extract_verified(archive, {**spec, "sha256": "0" * 64}, tmp_path)
    with pytest.raises(ValueError, match="Unsafe"):
        extract_verified(archive, {**spec, "members": ["../outside.txt"]}, tmp_path)
