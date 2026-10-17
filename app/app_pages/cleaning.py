import hashlib
import json
from dataclasses import asdict

import streamlit as st

from app.state import active, show_frame
from dataguard.cleaning import CleaningPlan, clean
from dataguard.profiling import numeric_columns

workspace = active()
frame = workspace.current
st.caption(
    "Preview selected operations on a copy. Apply adopts that preview as the next dataset revision. The original source remains available through Restore original dataset."
)
numeric = numeric_columns(frame)
categorical = [c for c in frame if c not in numeric]
drop = st.checkbox("Remove exact duplicate rows", value=False, key="clean_duplicates")
numeric_cols = st.multiselect(
    "Impute missing numerical values", numeric, key=f"clean_numeric_{workspace.fingerprint}"
)
numeric_strategy = st.selectbox(
    "Numerical imputation", ["median", "mean"], key="clean_numeric_strategy"
)
cat_cols = st.multiselect(
    "Impute missing categorical values",
    categorical,
    key=f"clean_categorical_{workspace.fingerprint}",
)
cat_strategy = st.selectbox(
    "Categorical imputation", ["mode", "constant"], key="clean_categorical_strategy"
)
constant = st.text_input(
    "Constant for categorical missing values", value="Unknown", key="clean_constant"
)
text_cols = st.multiselect(
    "Trim and casefold selected text columns",
    categorical,
    key=f"clean_text_{workspace.fingerprint}",
)
with st.expander("Explicit type and date conversions"):
    conversion_text = st.text_area(
        "Conversions as JSON (column → numeric or string)",
        value="{}",
        key=f"clean_conversions_{workspace.fingerprint}",
    )
    date_text = st.text_area(
        "Date formats as JSON (column → format)",
        value="{}",
        key=f"clean_dates_{workspace.fingerprint}",
    )
    st.caption(
        'Example: {"Quantity": "numeric"} and {"InvoiceDate": "ISO8601"}. Invalid values become missing only when selected. Order: type/date conversion → text normalization → imputation → deduplication.'
    )
try:
    conversions, dates = json.loads(conversion_text), json.loads(date_text)
    if (
        not isinstance(conversions, dict)
        or not isinstance(dates, dict)
        or not all(isinstance(v, str) for v in [*conversions.values(), *dates.values()])
    ):
        raise ValueError("Conversions and date formats must be JSON objects with string values.")
    plan = CleaningPlan(
        drop,
        {c: numeric_strategy for c in numeric_cols},
        {c: cat_strategy for c in cat_cols},
        constant,
        conversions,
        text_cols,
        dates,
    )
    signature = (
        workspace.revision,
        hashlib.sha256(json.dumps(asdict(plan), sort_keys=True).encode()).hexdigest(),
    )
except (ValueError, TypeError) as exc:
    st.error(f"Invalid cleaning configuration: {exc}")
    st.stop()
if st.button("Preview transformations", key="preview_cleaning", type="primary"):
    try:
        with st.spinner("Preparing a cleaning preview…"):
            workspace.pending = (signature, clean(frame, plan))
    except (ValueError, TypeError) as exc:
        workspace.pending = None
        st.error(str(exc))
pending = workspace.pending
if pending and pending[0] == signature:
    result = pending[1]
    st.subheader("Transformation preview")
    st.caption(
        f"Rows: {len(frame):,} → {len(result.frame):,}. Affected-record counts can overlap between operations."
    )
    show_frame(result.frame.head(50), "Preview of cleaned records before adoption")
    if result.log:
        import pandas as pd

        show_frame(
            pd.DataFrame(result.log),
            "Proposed transformations with affected-record counts and parameters",
        )
    if st.button(
        "Apply preview to working copy", key="apply_cleaning", disabled=not bool(result.log)
    ):
        workspace.apply(result)
        st.rerun()
elif pending:
    st.info("The configuration changed. Preview it again before applying.")
if workspace.log:
    st.subheader("Applied transformation history")
    import pandas as pd

    show_frame(pd.DataFrame(workspace.log), "Transformation history for accepted dataset revisions")
