# Assessment, screening, and revision methodology

## Ingestion and profiling

Uploads are bounded to 25 MiB, 200,000 records, and 250 columns. A strict CSV pass checks headers, duplicate names, row widths, quoting, and empty inputs before Pandas parsing. UTF-8 with optional BOM is the default; Windows-1252 and Latin-1 require explicit selection, as does a non-comma separator. NUL bytes and unsupported encodings are rejected. Embedded quoted newlines are supported. Blank records are skipped; fields that are empty are missing, while literals such as `NA` stay data. Original bytes are not written or changed.

Conventional `ID`/`Id`, `_id`, `Code`, `InvoiceNo`, and `CustomerID` headers stay strings; other dtypes are inferred. This avoids losing leading zeros in common identifiers without treating `citric_acid` as an ID. Users should inspect ambiguous fields and convert or configure them explicitly. The profile reports missing cells, unique non-null values, dtypes, numeric/categorical roles, descriptive statistics, and repeated rows after the first occurrence. Infinities are excluded from descriptive statistics only and remain visible to validation.

## Validation and score

Checks detect missing cells, exact repeats, infinities, and potential 1.5-IQR outliers. Explicit rules add numeric/integer/string/date expectations, numeric limits, allowed categorical values, and required columns. No universal business validity is inferred from a column's range or category frequency. Nonempty values that fail conversion are findings; validation does not coerce source values. Missing cells are counted separately from validity opportunities.

The **project-specific quality score** is:

```text
C = 1 - missing_cells / (rows * columns)
U = 1 - exact_repeat_rows_after_first / rows
V = 1 - failed_rule_opportunities / evaluated_rule_opportunities
score = 100 * (0.4*C + 0.2*U + 0.4*V)
```

Each applicable type, range, category, date, or finite-value check on a non-null value contributes a validity opportunity. Numeric-type checks and finite checks are separate; bounds are evaluated on finite, parseable numbers. An absent required column contributes one failed schema opportunity; optional absent columns contribute none. A missing required column is marked error severity. Value violations, missingness, and repeats are warnings for review, while outliers and retail context are informational. These severity labels are review priorities, not confirmed diagnoses.

If a category is unavailable, its weight is omitted and remaining weights are renormalized. A dataset with no records or no columns has no score. Missingness includes all fields, even optional fields. Many valid fields can dilute an important problem: the full retail score of 98.55 coexists with ~25% missing CustomerID values. Always inspect column-level findings. The score is neither an industry standard nor an acceptance criterion.

Findings retain the total count, severity, remediation recommendation, and at most 20 zero-based row positions in the **current revision**. Counts overlap; never sum findings to estimate affected unique records. Index labels are not used as positional identifiers. IQR flags and cancellation/negative-quantity/zero-price context are excluded from scoring. Zero IQR is treated as insufficient spread for this exploratory rule; no artificial fence is introduced.

## Isolation Forest

Wine defaults use all 11 physicochemical measurements, excluding the sensory `quality` rating. Red and white models are fitted independently. Generic uploads start with numerical features except conventional IDs and target/label names; the user must still review feature suitability.

The pipeline replaces infinite values with missing **in a modeling copy**, excludes all-null/constant/unsupported selected features, applies median imputation, and fits scikit-learn `IsolationForest` with 200 trees, `n_jobs=1`, fixed default seed 42, and default contamination 0.05. The interactive range is 10–50,000 rows. No automatic feature coercion, record deletion, or scaling is performed. Tree splits do not require unit scaling in this implementation.

The model returns scikit-learn labels (`-1` flagged, `1` unflagged), `decision_function`, and `anomaly_score = -score_samples`; **higher anomaly scores are more unusual** and negative decisions are flagged. Scores are not error probabilities. Contamination sets the fitted threshold; ties can make the exact fraction differ from the parameter. Imputed-feature counts help users identify records affected by preprocessing.

These are **in-sample exploratory scores**, not predictions evaluated against ground truth. No true-error labels exist in these datasets, so flagged counts are descriptive rather than detection accuracy. The reproducibility checks repeat fitting and compare scores/labels and verify that input frames remain identical. Numerical reproducibility is checked within the pinned environment; other architectures/library versions may vary.

## Cleaning and analytical state

Operations run on a deep copy in a fixed order: explicit type/date conversions, selected text strip/casefold, numeric/categorical imputation, then selected exact deduplication. Invalid conversions become missing only when chosen. Numeric imputation uses finite observations and leaves existing infinite values for separate review; all-null statistics and undefined categorical modes raise actionable errors. Mode ties use Pandas' first returned mode. Categorical constant imputation is available for all-null fields.

Preview shows proposed values and operation counts. Changing the configuration invalidates that preview for adoption. Applying increments the dataset revision, records operation/columns/affected records/parameters, and invalidates quality and model results. Original data remains a separate deep copy. Restore replaces the working copy from the original and clears transformation history and model results. Dataset switches also discard earlier analysis. Affected-record counts can overlap across operations; dtype conversions can change a column's dtype without changing individual values (zero value-change count).

Exports contain only the current accepted revision and stored model run; previews are excluded. Anomaly exports align through zero-based row positions and reject reserved output-column collisions. Strict JSON converts unavailable/nonfinite statistics to `null`. CSV preserves values unless optional spreadsheet formula protection is selected; protection prefixes risky text with an apostrophe, changes those strings explicitly, and preserves negative numbers.

## SQL analytics

Each query builds and closes a private `:memory:` SQLite connection. `transactions` contains an explicitly eligible subset and a `customers` dimension contains unique non-null customer identifiers; a unique index prevents join fan-out. A `LEFT JOIN` retains unknown customers. `input_quality` reports source counts and eligibility. Only predefined SQL files can execute; the database is set to `query_only`, and country values use bound parameters.

The analytical subset requires non-null invoice/stock/country, valid ISO dates, finite integral quantities, and finite nonnegative prices. Returns, zero prices, repeats, and missing customers remain. In the full source this excludes two negative-price rows; no upload/source rows are changed. Net line value is Quantity × UnitPrice in GBP, including returns. Duplicates remain by policy, so totals are not claimed as audited revenue. The sample totals cannot represent full-business revenue. The examples cover SELECT, WHERE, GROUP BY, LEFT JOIN, CTE, window frames, and source quality summaries.
