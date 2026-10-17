"""Convert official Excel/semicolon CSV inputs without removing or imputing records."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.download_data import CATALOG, ROOT, sha256

RETAIL_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]
WINE_FEATURES = [
    "fixed_acidity",
    "volatile_acidity",
    "citric_acid",
    "residual_sugar",
    "chlorides",
    "free_sulfur_dioxide",
    "total_sulfur_dioxide",
    "density",
    "ph",
    "sulphates",
    "alcohol",
]


def _write_csv(frame: pd.DataFrame, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S")
    return {"rows": len(frame), "columns": list(frame.columns), "sha256": sha256(path)}


def retail_sample_positions(frame: pd.DataFrame, n: int = 1200, seed: int = 42) -> list[int]:
    """Seeded coverage sample, enriched for real exceptions, never fabricated rows.

    Include both copies of one actual duplicate, then up to 12 positions from each
    context/missingness slice, then fill uniformly without replacement. Return in
    original source order. This is a demo sample, not a population estimate.
    """
    if n < 100:
        raise ValueError("Use at least 100 rows for the retail coverage sample.")
    rng = np.random.default_rng(seed)
    selected: set[int] = set()
    hashes = pd.util.hash_pandas_object(frame, index=False)
    duplicates = hashes[hashes.duplicated(keep=False)]
    if not duplicates.empty:
        group = hashes.index[hashes.eq(duplicates.iloc[0])].tolist()
        selected.update(group[:2])
    masks = [
        frame["CustomerID"].isna(),
        frame["Description"].isna(),
        frame["UnitPrice"].lt(0),
        frame["UnitPrice"].eq(0),
        frame["Quantity"].lt(0),
        frame["InvoiceNo"].str.upper().str.startswith("C", na=False),
        frame["Country"].ne("United Kingdom"),
    ]
    for mask in masks:
        positions = np.flatnonzero(mask.to_numpy(dtype=bool, na_value=False))
        selected.update(rng.choice(positions, min(12, len(positions)), replace=False).tolist())
    target = min(n, len(frame))
    remaining = np.setdiff1d(np.arange(len(frame)), sorted(selected))
    selected.update(rng.choice(remaining, max(0, target - len(selected)), replace=False).tolist())
    return sorted(selected)[:target]


def wine_sample_positions(frame: pd.DataFrame, n: int = 400, seed: int = 42) -> list[int]:
    """Cover each observed quality grade with up to five real rows, then random fill."""
    rng = np.random.default_rng(seed)
    selected: set[int] = set()
    for quality in sorted(frame["quality"].unique()):
        positions = np.flatnonzero(frame["quality"].eq(quality).to_numpy())
        selected.update(rng.choice(positions, min(5, len(positions)), replace=False).tolist())
    remaining = np.setdiff1d(np.arange(len(frame)), sorted(selected))
    selected.update(
        rng.choice(remaining, max(0, min(n, len(frame)) - len(selected)), replace=False).tolist()
    )
    return sorted(selected)


def preprocess(data_dir: Path, *, seed: int = 42) -> dict:
    """Validate source-file hashes, serialize deterministic CSVs and provenance."""
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    provenance = {"seed": seed, "preprocessing_version": 1, "datasets": {}, "samples": {}}
    retail_path = data_dir / "raw" / "online_retail" / "Online Retail.xlsx"
    retail = pd.read_excel(
        retail_path,
        engine="openpyxl",
        dtype={c: "string" for c in ["InvoiceNo", "StockCode", "CustomerID"]},
        keep_default_na=False,
        na_values=[""],
    )
    if retail.columns.tolist() != RETAIL_COLUMNS:
        raise ValueError("Retail source schema changed; review conversion before continuing.")
    if not pd.api.types.is_datetime64_any_dtype(retail["InvoiceDate"]):
        raise ValueError("Unexpected retail dates; no implicit date parsing is performed.")
    info = _write_csv(retail, data_dir / "processed" / "online_retail.csv")
    info.update(
        {
            "source_file_sha256": sha256(retail_path),
            "source": catalog["online_retail"]["source"],
            "license": "CC BY 4.0",
            "changes": "Excel to UTF-8 CSV; identifiers serialized as text, dates as ISO timestamps; no filtering/imputation/deduplication.",
        }
    )
    provenance["datasets"]["online_retail"] = info
    positions = retail_sample_positions(retail, seed=seed)
    sample_info = _write_csv(
        retail.iloc[positions], data_dir / "sample" / "online_retail_sample.csv"
    )
    sample_info.update(
        {
            "source_positions_zero_based": positions,
            "sampling": "Coverage enriched: both copies of one real duplicate; up to 12 rows per missing/context slice; uniform fill without replacement; original order.",
            "population_representative": False,
        }
    )
    provenance["samples"]["online_retail_sample.csv"] = sample_info
    for kind, expected_rows in [("red", 1599), ("white", 4898)]:
        path = data_dir / "raw" / "wine_quality" / f"winequality-{kind}.csv"
        wine = pd.read_csv(path, sep=";")
        wine.columns = wine.columns.str.strip().str.lower().str.replace(" ", "_")
        if wine.columns.tolist() != WINE_FEATURES + ["quality"] or len(wine) != expected_rows:
            raise ValueError(f"Wine {kind} schema/row count changed; review source.")
        if not all(pd.api.types.is_numeric_dtype(wine[c]) for c in wine):
            raise ValueError("Wine measurements must remain numerical.")
        name = f"wine_{kind}"
        info = _write_csv(wine, data_dir / "processed" / f"{name}.csv")
        info.update(
            {
                "source_file_sha256": sha256(path),
                "source": catalog["wine_quality"]["source"],
                "license": "CC BY 4.0",
                "changes": "Semicolon to comma CSV; headers lowercased with spaces replaced by underscores; no row/value filtering.",
            }
        )
        provenance["datasets"][name] = info
        positions = wine_sample_positions(wine, seed=seed)
        filename = f"{name}_sample.csv"
        sample_info = _write_csv(wine.iloc[positions], data_dir / "sample" / filename)
        sample_info.update(
            {
                "source_positions_zero_based": positions,
                "sampling": "Up to five real rows per quality grade; uniform fill without replacement; original order.",
                "population_representative": False,
            }
        )
        provenance["samples"][filename] = sample_info
    # Hashes of original inputs are bound to the reviewed archive manifest in download_data.
    provenance["source_catalog_sha256"] = hashlib.sha256(CATALOG.read_bytes()).hexdigest()
    (data_dir / "sample" / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    for name, info in provenance["datasets"].items():
        print(
            f"{name}: {info['rows']:,} rows, {len(info['columns'])} columns; SHA-256 {info['sha256']}"
        )
    return provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    # Re-verify cached archives and re-extract allowlisted sources before conversion.
    from scripts.download_data import download

    download(["online_retail", "wine_quality"], args.data_dir, offline=True)
    preprocess(args.data_dir, seed=args.seed)


if __name__ == "__main__":
    main()
