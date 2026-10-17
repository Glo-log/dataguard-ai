# DataGuard AI implementation plan

This is an independent portfolio project. No deployment, business impact, or model accuracy is claimed.

## Scope and decisions

- Python 3.12, Pandas, NumPy, scikit-learn, SQLite, Plotly, Streamlit, pytest.
- UCI Online Retail is the primary validation/SQL demonstration; UCI Wine Quality is the numerical anomaly demonstration.
- Preserve source rows and values during format conversion. Cleaning is an explicit, previewed operation on a copy.
- Real samples are reproducible, small, attributed CC BY 4.0 derivatives. Raw/full processed datasets are ignored by Git.
- Anomaly flags and IQR outliers indicate observations for review, not confirmed errors.
- No publishing or pushing without user approval.

## Phases

1. Environment and architecture: inspect workspace, create virtual environment, dependency lock, package layout.
2. Ingestion and profiling: bounded strict CSV loading, encoding handling, immutable profiling.
3. Validation and cleaning: configurable rules, transparent score, preview and transformation log.
4. EDA: interactive missingness, distributions, boxplots, correlations, category frequencies.
5. Anomaly detection: numerical feature safeguards, median imputation pipeline, reproducible Isolation Forest.
6. SQL: isolated in-memory SQLite, read-only curated queries, validated retail relational model.
7. Dashboard: eight working pages, dataset/session lifecycle, exports and empty/error states.
8. Verification: pytest unit/integration/UI tests; real dataset download, conversion, and validation.
9. Documentation: sources/licenses, actual measured results, setup/deployment, career notes, actual screenshots if browser permits.
10. Audit: static checks, complete test suite, startup smoke, repository/license/secret/Git review; FINAL_AUDIT.md.

## Verification strategy

Use small explicitly synthetic fixtures for edge cases and bundled real UCI samples for offline integration tests. Verify download hashes and deterministic sample regeneration. Run full-data retail validation and wine anomaly analysis locally with separate reports. Exercise Streamlit pages with AppTest, and use a browser for screenshots if available. Record any checks that cannot be performed.

## Progress

- Initial inspection: workspace empty; Python 3.12.0 and Git 2.50 available. No existing files to overwrite.
- Phases 1–3 complete: isolated environment and lock; strict ingestion/profiling; explicit validation and previewed cleaning with logs, verified by unit tests and real retail samples.
- Phases 4–6 complete: all EDA modes, reproducible wine Isolation Forest, seven curated relational SQL examples, verified by tests and full-data evaluation.
- Phase 7 complete: eight working Streamlit pages, session revisions, source preservation, and current-state exports; all pages and main state transitions exercised with AppTest.
- Phase 8 complete: 88 tests passed; Ruff, compilation, and dependency consistency passed. Browser smoke verified startup, rendered charts, model execution, CSV upload/download, malformed upload, and a mobile viewport.
- Phase 9 complete: real screenshots, source/licenses and sampling provenance, measured full/sample results, setup/deployment/Git instructions, CV bullets, and interview answers written.
- Phase 10 complete: repository files, ignores, sizes, sources, SQL, secrets-pattern scan, Git status, and documentation reviewed. The publication audit independently installed a fresh environment and verified all 88 tests plus the real browser workflow. Windows checkout checks verified the LF checksum protection. A clean local initial commit is prepared on `main`; no push, remote, or deployment was created. See FINAL_AUDIT.md for evidence and remaining external/manual checks.
