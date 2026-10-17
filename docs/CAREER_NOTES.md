# Independent portfolio project: CV and interviews

These statements describe the implemented and locally verified project, not employment or commercial impact.

## Three CV bullets

- Built an eight-page Streamlit data quality application using Python, Pandas, NumPy, and Plotly, with configurable validation, cleaning previews, transformation logs, and CSV/JSON exports.
- Implemented reproducible UCI dataset downloads and Excel-to-CSV preprocessing; validated 541,909 retail transaction rows and screened red/white wine measurements using a median-imputation and Isolation Forest pipeline.
- Developed isolated SQLite analytics with joins, CTEs, and window functions, and verified ingestion, validation, cleaning, anomaly screening, exports, and dashboard workflows with pytest.

## Five interview questions and answers

**1. Why separate the Streamlit pages from the analysis code?**

`src/dataguard` contains reusable functions and result objects that run without a UI. Page scripts only collect choices and display outputs. `Workspace` holds each session's original/current copies and accepted revision. This separation makes edge cases testable and prevents a page rerun from silently changing the source. Changing the dataset or accepting cleaning invalidates stale analysis results.

**2. How did you use Pandas without silently destroying valid transactions?**

Excel conversion retains all rows, signs, missingness, and original columns. Identifier columns stay strings; dates serialize as ISO timestamps. Profiling and validation leave frames unchanged. Cleaning uses a deep copy, explicit choices, and a preview with per-operation counts. Negative retail quantities remain because they can represent returns or adjustments; missing customer IDs are reported rather than invented. Synthetic tests and real-sample integration tests verify immutability.

**3. What relational modeling and SQL safety choices did you make?**

Each run creates a private in-memory SQLite database with eligible transaction lines, a unique customer-ID dimension, and input-quality metrics. A `LEFT JOIN` retains rows with missing customer identifiers and a unique customer key prevents multiplication of transaction rows. Queries are selected from seven reviewed SQL files, the database is read-only after construction, and country filters use bound parameters. CTEs and window frames calculate monthly and cumulative net line values. The analytical subset and its exclusions are reported explicitly.

**4. What does an Isolation Forest flag actually mean?**

It indicates a record that is relatively easy to isolate through random feature splits under this fitted model. Wine uses the 11 measurements and excludes the quality rating. A pipeline median-imputes missing numerical inputs, excludes unsupported/all-null/constant features, and uses 200 trees with a fixed seed. Scores are reported with higher values meaning more unusual, and contamination sets the threshold. A flagged legitimate rare wine is not necessarily an erroneous measurement. Without verified error labels, flag counts cannot establish model accuracy. Red and white cohorts are fitted separately.

**5. What did the tests establish, and what did they not establish?**

pytest checks strict CSV handling, profiling denominators, rule findings, score calculations, explicit cleaning/logs, immutable source data, anomaly reproducibility and edge cases, relational results and query restrictions, portable exports, sample hashes, and Streamlit page/revision workflows. A synthetic extreme measurement checks model ranking in a controlled case; real wine data checks deterministic finite results without claiming ground-truth correctness. Local browser checks add rendering and upload/download evidence. These checks do not establish production scale, scientific detection accuracy, universal business rules, or a public deployment.
