# DataGuard AI final repository audit

**Date:** 2026-10-17 (Africa/Tunis). **Outcome:** publication readiness verified, with a clean local initial commit prepared on `main`. No remote repository, push, or public deployment has been created. Publication requires explicit approval.

## Publication audit findings and fixes

- Re-ran the original suite: **88 tests passed in 56.41 seconds**; Ruff and dependency consistency passed.
- Created a separate source snapshot containing only Git candidate files and a **fresh Python 3.12 virtual environment**, with no inherited Python paths, user site packages, raw/processed datasets, previous application environment, or existing caches. Installed all **50 exact locked packages** from `requirements.txt` and compared the installed package set with the lock.
- In that isolated environment, **88 tests passed in 50.96 seconds**; Ruff, format checks, compilation, dependency checks, and all sample workflows passed. A real temporary Streamlit server and headless Chrome passed startup, rendering, wine screening, dataset/anomaly CSV downloads, real-sample upload, malformed-upload rejection, and the mobile export viewport.
- Confirmed and fixed a Windows checkout issue: this machine's `core.autocrlf=true` could rewrite checksum-pinned sample CSVs. Added `.gitattributes` to enforce LF text/CSV/JSON endings and preserve binary PNGs. Exported the staged tree under Windows CRLF defaults and verified all three sample SHA-256 values, unchanged provenance content, and identical PNG bytes.
- Removed an extra blank line at the end of `pyproject.toml` reported by the staged Git whitespace check. Updated stale pre-commit publication instructions; working application features and dataset values were not changed.
- Git writes required the desktop account, while `.git` was initialized by the sandbox account. Used a `safe.directory` exception limited to this project and each command; no global Git trust settings were changed. The exact PowerShell publication commands include the same folder-scoped option.
- Validated every local Markdown link against publishable files, reviewed all README screenshots visually, and rechecked source citations and licensing against the official UCI pages. Sample and full-data results were regenerated locally and match the recorded retail findings and wine results.
- Scanned publishable content for AWS/GitHub/OpenAI/Slack credential patterns, private keys, embedded URL credentials, and assigned secrets: **no matches**. Verified 13 ignore probes covering secrets, environments, raw/full data, local audit copies, caches, and databases. No large-file or ignored-file additions were found.

Machine-readable evidence is in `reports/reference/publication_audit.json`. Raw logs, fresh environments, and local audit snapshots remain under ignored `artifacts/tmp/` and `reports/local/`.

## Completed functionality

| Area | Implemented and checked |
|---|---|
| Environment | Python 3.12 project, isolated `.venv`, exact direct/transitive dependency lock, modular package layout, local Git repository on `main` |
| Ingestion | Explicit CSV encodings/separators, byte/row/column limits, header checks, strict malformed-row handling, identifier preservation, empty/binary rejection |
| Profiling | Preview, dimensions, dtypes, finite descriptive statistics, missing percentages, unique counts, numeric/categorical roles, exact-repeat counts |
| Validation | Configurable types, dates/formats, required columns, ranges, categories, inferred infinity checks, IQR review flags, severity/actions, documented project score |
| Retail interpretation | Missing identifiers/descriptions and repeated rows reported; returns/cancellations/zero prices retained as context; negative prices violate a configurable rule |
| Cleaning | Copy-based operations, preview and explicit adoption, mean/median/mode/constant imputation, type/date conversion, text normalization, selected deduplication, operation logs |
| EDA | Plotly missingness, histograms, boxplots, pairwise correlation, categorical frequencies, potential-outlier counts; bounded chart payloads |
| Anomaly screening | Median-imputation pipeline + 200-tree Isolation Forest, numerical exclusions, safeguards, labels/scores, contamination/seed controls, no automatic deletion |
| SQL | Validated temporary retail subset, unique customer dimension, LEFT JOIN retaining unknown IDs, seven curated read-only examples, parameterized filter |
| Dashboard | All eight pages, shared dataset selector, upload controls, clear empty/errors, revision lifecycle, immutable source copy, original restore |
| Exports | Current dataset, quality CSV/strict JSON, transformation JSON/CSV, anomaly rows/parameters, explicit spreadsheet-text protection option |
| Real data | Official UCI retrieval, pinned archive checksums, deterministic Excel/CSV conversion, three attributed real coverage samples, exact provenance |
| Review materials | Actual screenshots, measured reports, README/methodology/dataset documentation, CI configuration, deployment steps, Git commands, three CV bullets, five interview answers |

## Commands actually executed and outcomes

- `python -m pytest -q`: **88 passed** in both the original and independently installed clean environment during the publication audit (timings above). Includes unit tests, real-sample integration tests, all page rendering, all EDA variants, cleaning preview/apply/restore, stale-preview protection, invalid rule configuration, wine model/export state, and dataset switching.
- `python -m ruff check src app scripts tests`: **passed**.
- `python -m ruff format --check src app scripts tests`: **33 files already formatted**.
- `python -m compileall -q src app scripts`: **passed**.
- `python -m pip check`: **no broken requirements found**.
- Official UCI archives downloaded successfully using TLS verification and Certifi, then pinned and re-verified from the offline cache. The environment's initial default-CA certificate error was resolved without disabling TLS.
- `python -m scripts.preprocess_data`: converted all retail and both wine datasets, retaining source rows, and generated deterministic samples/provenance.
- A second complete preprocessing run compared the entire deterministic provenance manifest, including all processed/sample hashes and source positions: **identical**.
- `python -m scripts.validate_demos --output-dir reports/reference`: **passed** for bundled samples, including repeated identical wine model fits and all seven retail SQL queries.
- `python -m scripts.validate_demos --full --output-dir reports/reference`: **passed** for all 541,909 retail rows, 1,599 red wines, and 4,898 white wines; all SQL examples executed, and repeated wine scores/labels matched exactly.
- `python -m scripts.browser_smoke`: **passed** against a real temporary local Streamlit server and headless Chrome with a fresh profile. Verified health endpoint, navigation, fully rendered charts, retail report, wine model run, fresh 400×12 dataset CSV and 400×18 anomaly CSV downloads, real retail sample upload, clear rejection of a synthetic malformed CSV, and a 430×932 mobile export viewport. The helper closed its own processes.

The original checks used the project's `.venv\Scripts\python.exe`; the independent checks used the separate fresh environment under ignored `artifacts/tmp/publication-audit/clean-source/.venv/`. No test, screenshot, deployment, or model accuracy was inferred from code alone.

## Measured dataset results

| Measure | Full dataset | Bundled sample |
|---|---:|---:|
| Retail rows / columns | 541,909 / 8 | 1,200 / 8 |
| Missing CustomerID | 135,080 | 314 |
| Missing Description | 1,454 | 22 |
| Exact repeated rows after first | 5,268 | 1 |
| Negative UnitPrice under configured rule | 2 | 2 |
| Retail project score | 98.55 | 98.58 |
| SQL eligible retail rows | 541,907 | 1,198 |
| Wine red flags / rows | 80 / 1,599 | 20 / 400 |
| Wine white flags / rows | 245 / 4,898 | 20 / 400 |

Wine uses 11 measurements, excluding `quality`; seed 42, 200 trees, contamination 0.05, median imputation, separate cohorts. These flags are statistical observations for investigation, **not confirmed data errors**. No accuracy, precision, recall, or business impact is claimed. Samples are enriched for coverage and do not support population-rate estimates. Repeated retail transactions may be legitimate and negative quantities can be returns/adjustments.

Evidence is committed as reviewable files under `reports/reference/` (full/sample aggregate reports and browser outcome) and `data/sample/provenance.json` (hashes and exact row positions). Screenshots under `assets/screenshots/` were visually inspected: retail overview and quality page, wine model configuration/results, and mobile exports. Charts are rendered, not loading placeholders.

## Repository and source review

- Started from an empty project folder; no pre-existing user work was deleted or overwritten. Generated project outputs are documented as reproducibly replaceable by their scripts.
- Sources, DOI citations, license links, and changes are recorded in `data/sources.json`, `data/LICENSE_DATA.md`, and `docs/DATASETS.md`. Both official UCI source pages state CC BY 4.0. Code has a separate MIT license; data-bearing screenshots/reports retain source attribution.
- `.gitignore` excludes raw/full processed data, environments, bytecode, caches, databases, secrets, local reports, and browser downloads. `git check-ignore` confirmed 13 representative paths are excluded. `.gitattributes` protects checksum-sensitive text from platform newline conversion.
- Reviewable content is under 1 MiB including four actual screenshots and three CSV samples; no reviewable file exceeds 2 MiB. Full raw/converted data remains local, outside the Git candidate list.
- Reviewed all seven SQL files and query selection. Schema checks reject missing required fields; the customer key prevents join fan-out; a read-only database and parameter binding are tested.
- Repository-scoped pattern scan found no AWS/GitHub/OpenAI/Slack credential patterns, private-key blocks, embedded URL credentials, or assigned secrets. No credentials are needed by the application. This is a targeted scan, not an external security assessment.
- README metrics were checked against generated reference reports. Documentation distinguishes full-data findings from biased sample findings and distinguishes anomaly flags from data errors. Career material claims only implemented functionality.
- Only intended source, metadata, attributed samples, screenshots, tests, documentation, and aggregate evidence are included in the initial commit. No remote, push, or deployment was created. Commit review and exact publication commands are in `docs/GITHUB.md`.
- Temporary browser/server logs and downloaded artifacts are isolated under ignored `reports/local/`; they are not included in repository review. The `.venv` and source archives are intentionally retained locally for reproducibility.

## Limitations and unverified functionality

- There are no verified data-error labels or held-out model performance results. Imputation, feature choice, cohort mix, and contamination affect flags. Different platform/library versions may change numerical results.
- The quality score can dilute important field-specific problems and is not a standard or acceptance guarantee. Domain review remains necessary.
- The browser smoke covers representative flows, not every native file-picker/drag-and-drop gesture, every chart hover/zoom interaction, every encoding in the browser, every viewport, or screen-reader behavior. Core encoding/limit/malformed cases are unit-tested.
- There is no authenticated multi-user persistence, durable audit log, automated identity recovery, production-scale load test, or security certification. Uploads are processed on the server; public deployments should use non-sensitive demo data.
- Interactive limits: 25 MiB / 200,000 CSV rows / 250 columns; model 10–50,000 rows; bounded chart/table display. Full retail evaluation uses the offline CLI.
- Session state is temporary and may be lost on refresh/reconnection/restart. Users must export accepted results before leaving.
- Windows/Python 3.12 was verified locally. The configured Linux GitHub Actions workflow, packaging as a distributable wheel, other browsers, and actual Streamlit Community Cloud deployment have not been executed.

## Deployment readiness and remaining manual actions

The entry point is `app/main.py`, requirements are pinned at the root, runtime paths are relative to project files, and bundled samples require no startup download or credentials. Community Cloud setup is documented for Python 3.12. **No public deployment exists.**

Before publishing: review the local initial commit and attribution, explicitly approve publication, and choose the GitHub account/repository visibility. Create the empty **`dataguard-ai`** remote and push using `docs/GITHUB.md` only after approval. GitHub CLI was not installed during the audit; the documented website-and-Git route works without it. After publication, inspect the actual remote CI result. If deploying, follow `docs/DEPLOYMENT.md`, then verify the real public URL and cloud logs before adding a live-demo link to the portfolio.
