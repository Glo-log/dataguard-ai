"""Produce measured, reproducible retail/wine demonstration reports."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from dataguard.anomaly_detection import detect_anomalies  # noqa: E402
from dataguard.ingestion import read_csv  # noqa: E402
from dataguard.profiling import profile  # noqa: E402
from dataguard.reporting import json_bytes  # noqa: E402
from dataguard.sql_analytics import QUERIES, build_retail_database, run_query  # noqa: E402
from dataguard.validation import retail_rules, validate  # noqa: E402
from scripts.download_data import sha256  # noqa: E402
from scripts.preprocess_data import WINE_FEATURES  # noqa: E402


def evaluate(*, full: bool, output_dir: Path) -> dict:
    """Assert invariants, not fabricated model accuracy or data-error labels."""
    directory = ROOT / "data" / ("processed" if full else "sample")
    suffix = "" if full else "_sample"
    retail_path = directory / f"online_retail{suffix}.csv"
    retail = (
        pd.read_csv(
            retail_path,
            dtype={"InvoiceNo": "string", "StockCode": "string", "CustomerID": "string"},
            keep_default_na=False,
            na_values=[""],
        )
        if full
        else read_csv(retail_path.read_bytes()).frame
    )
    report = validate(retail, retail_rules(), retail_context=True)
    results = {
        "scope": "full source-derived CSVs" if full else "bundled coverage samples",
        "seed": 42,
        "contamination": 0.05,
        "interpretation": "All counts are measured by this script. Quality findings are rule violations or review context; statistical anomalies are not confirmed errors. No anomaly accuracy is measured. Sample rates are not population estimates.",
        "retail": {
            **profile(retail),
            "file_sha256": sha256(retail_path),
            "quality": report.to_dict(),
        },
        "wine": {},
    }
    with build_retail_database(retail) as database:
        results["retail"]["sql_eligibility"] = database.eligibility
        results["retail"]["sql_queries_verified"] = {
            name: len(run_query(database, name)) for name in QUERIES
        }
    for kind in ("red", "white"):
        path = directory / f"wine_{kind}{suffix}.csv"
        wine = pd.read_csv(path) if full else read_csv(path.read_bytes()).frame
        before = wine.copy(deep=True)
        result = detect_anomalies(wine, WINE_FEATURES, contamination=0.05, random_state=42)
        second = detect_anomalies(wine, WINE_FEATURES, contamination=0.05, random_state=42)
        pd.testing.assert_frame_equal(wine, before)
        np.testing.assert_array_equal(result.rows.anomaly_label, second.rows.anomaly_label)
        np.testing.assert_allclose(
            result.rows.anomaly_score, second.rows.anomaly_score, rtol=0, atol=0
        )
        assert "quality" not in result.features and len(result.features) == 11
        results["wine"][kind] = {
            **profile(wine),
            "file_sha256": sha256(path),
            "features": result.features,
            "parameters": result.parameters,
            "flagged_records": int(result.rows.is_anomaly.sum()),
            "flagged_pct": float(result.rows.is_anomaly.mean() * 100),
            "scores_finite": bool(np.isfinite(result.rows.anomaly_score).all()),
            "repeat_run_identical": True,
            "ground_truth_error_labels": None,
        }
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = "full_results.json" if full else "sample_results.json"
    (output_dir / filename).write_bytes(json_bytes(results))
    print(
        f"Retail: {len(retail):,} rows; {results['retail']['missing_cells']:,} missing cells; {results['retail']['duplicate_rows']:,} repeated rows; score {report.score}"
    )
    for kind, result in results["wine"].items():
        print(
            f"Wine {kind}: {result['rows']:,} rows; {result['flagged_records']} flags ({result['flagged_pct']:.3f}%); deterministic repeated run"
        )
    print(f"Report written to {output_dir / filename}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports" / "local")
    args = parser.parse_args()
    evaluate(full=args.full, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
