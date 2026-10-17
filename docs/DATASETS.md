# Dataset sources and reproducibility

Source and license metadata were checked against the official UCI pages on **2026-10-17**. `data/sources.json` is the machine-readable source registry and pins SHA-256 hashes for the downloaded archives. `data/LICENSE_DATA.md` contains the redistribution attribution.

| Dataset | Source dimensions | Bundled sample | Purpose |
|---|---|---|---|
| [UCI Online Retail, ID 352](https://archive.ics.uci.edu/dataset/352/online+retail) | 541,909 rows × 8 columns, including two identifiers | 1,200 × 8 | Primary data quality, cleaning, EDA, and relational SQL demonstration |
| [UCI Wine Quality, ID 186](https://archive.ics.uci.edu/dataset/186/wine+quality), red | 1,599 × 12 (11 measurements + quality rating) | 400 × 12 | Secondary Isolation Forest demonstration |
| Same source, white | 4,898 × 12 (11 measurements + quality rating) | 400 × 12 | Separate cohort for numerical screening |

These dimensions were verified from the actual downloaded files. UCI lists six retail features plus two identifier fields and highlights the white-wine instance count on its wine landing page; these are not the same as total CSV column/combined-row counts.

## Retrieval

Run from the repository root after installing `requirements.txt`:

```powershell
.\.venv\Scripts\python.exe -m scripts.download_data
.\.venv\Scripts\python.exe -m scripts.preprocess_data
.\.venv\Scripts\python.exe -m scripts.validate_demos --output-dir reports/local
.\.venv\Scripts\python.exe -m scripts.validate_demos --full --output-dir reports/local
```

Downloads are the official UCI ZIP files, not third-party repackagings. The downloader streams with a 60 MB cap, uses TLS verification with the pinned Certifi CA bundle, retries network failures, verifies the archive hash, and extracts only named members with a 100 MB member cap. If the primary host is unavailable, it tries UCI's official `archive-beta.ics.uci.edu` host; the same hash must still match. It never disables certificate verification.

Downloaded archives are cached in `data/raw/<dataset>/`. Subsequent runs verify the cache. `--offline` prohibits network access. `--dataset online_retail` or `--dataset wine_quality` fetches a single archive; `--force` explicitly refreshes it. Do not combine `--force` with `--offline`. If UCI changes bytes, stop and review the source before deliberately updating the catalog; do not disable verification to make a new hash pass.

The preprocessing CLI re-verifies both cached archives and re-extracts their allowlisted source members, then writes full CSVs to `data/processed/` and small CSVs plus provenance to `data/sample/`. These generated destinations are reproducibly replaced when rerun. Keep custom data elsewhere. Use `--data-dir <folder>` on download/preprocessing for a separate working directory. `--seed 42` is the default. Tests use bundled samples and require no network or raw downloads.

If automated download is unavailable, use the official source pages' Download buttons, save the ZIPs as:

```text
data/raw/online_retail/online_retail.zip
data/raw/wine_quality/wine_quality.zip
```

Then run `download_data --offline` and `preprocess_data` as modules using the commands above. Unverified Excel/CSV files alone do not satisfy the pinned-archive verification step. Missing archives and checksum failures produce explicit errors.

## Conversion and sample selection

Retail conversion retains every source row, column, missing value, and transaction sign. Invoice, stock, and customer identifiers are serialized as text; dates use `YYYY-MM-DD HH:MM:SS`; output is UTF-8 with comma separators and LF endings. Excel cell formatting is not preserved in CSV. No sales-only filtering, imputation, or duplicate removal occurs.

Retail sample: seed 42, both copies of one actual repeated record, up to 12 original positions each from missing CustomerID, missing Description, negative price, zero price, negative quantity, cancellation prefix, and non-UK country slices; uniform sampling without replacement fills the remaining positions to 1,200. Positions are sorted back into original order. Slices can overlap. The enrichment ensures the demo exposes real quality/context cases.

Wine conversion retains red and white as separate CSVs. The 12 original headers are lowercased and spaces become underscores (`pH` becomes `ph`). Measurements and quality ratings are retained unchanged numerically. Each 400-row sample includes up to five original positions per observed quality grade, then uniform random fill without replacement, in original order. Sampling uses the rating for grade coverage; the model excludes it.

These are **coverage samples**, not unbiased statistical samples. They preserve real records and varied cases but intentionally change prevalence. Sample percentages, SQL totals, and anomaly flags must not be generalized to the source population. Full and sample model runs are fitted separately and need not flag the same records.

`data/sample/provenance.json` records source and processed hashes, sampling descriptions, exact original zero-based positions, row counts, schemas, and the catalog hash. Rerunning with the locked environment and default seed should reproduce the same sample bytes. No generated timestamp is included in this deterministic manifest.

## Known limitations and interpretation

**Retail:** UK non-store retailer, transactions from December 2010 to December 2011; historical and dominated by the UK. Missing customer IDs cannot be assumed to mean guests. Negative quantities may represent returns, cancellations, or adjustments. `C` prefixes mark cancellations according to UCI. Zero prices and negative prices need source context. Negative prices violate this project's configurable nonnegative-price rule; this is not proof of a source-system error. Exact repeats may still be legitimate transaction lines. No customer names or inferred identities are added.

The current UCI retail page says no missing values, but the downloaded workbook contains missing CustomerID and Description cells. This project reports the measured file contents (135,080 and 1,454 respectively) instead of copying that metadata claim.

**Wine:** Portuguese red and white Vinho Verde physicochemical and sensory data, not a general wine population. Quality grades are ordinal and imbalanced. No verified data-error/anomaly labels exist. No accuracy/precision/recall or proven measurement errors are claimed. A rare chemical profile can be a legitimate sample. Keep cohorts separate to avoid treating wine type as an anomaly signal. No missing measurements were observed in the downloaded wine files; synthetic missing-value fixtures exercise the model pipeline's imputation behavior.

## Repository size and licenses

Both source pages state [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribution permits these small adapted samples; code and data licensing are kept separate. Full archives (retail ~22.6 MB) and larger converted data are excluded via `.gitignore`; the application works offline with the bundled samples. Reports contain only aggregate counts and at most 20 positional examples per finding. Do not commit private uploads, virtual environments, caches, databases, or local browser downloads.
