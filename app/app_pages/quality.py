import json
from dataclasses import asdict

import streamlit as st

from app.state import active, show_frame
from dataguard.validation import parse_rules

workspace = active()
st.caption(
    "Missingness and duplicates are always checked. Numeric infinities are checked automatically. Add explicit types, date formats, bounds, and allowed categories where validity needs domain knowledge."
)
with st.expander("Configure column rules"):
    with st.form("validation_rules"):
        text = st.text_area(
            "Rules as JSON",
            value=json.dumps({c: asdict(r) for c, r in workspace.rules.items()}, indent=2),
            height=260,
            key=f"rules_editor_{workspace.fingerprint}",
        )
        st.caption(
            'Example: {"amount": {"dtype": "numeric", "minimum": 0}, "status": {"allowed": ["paid", "pending"]}}. Missing fields are measured separately. Dates default to ISO8601; specify a format such as %d/%m/%Y when needed.'
        )
        if st.form_submit_button("Apply validation rules"):
            try:
                workspace.rules = parse_rules(json.loads(text))
                workspace.quality = None
                st.success("Rules applied to the current dataset revision.")
            except (ValueError, TypeError) as exc:
                st.error(f"Rules were not applied: {exc}")
with st.spinner("Evaluating quality rules…"):
    report = workspace.report()
with st.container(horizontal=True):
    st.metric(
        "Quality score", report.score if report.score is not None else "Unavailable", border=True
    )
    st.metric("Rule opportunities", f"{report.indicators['validity_evaluated']:,}", border=True)
    st.metric("Failed rule opportunities", f"{report.indicators['validity_failed']:,}", border=True)
st.info(report.methodology)
if workspace.is_retail:
    st.info(
        "Retail policy: negative quantities and C-prefixed invoices are context flags for possible returns/cancellations. Negative prices violate a configurable nonnegative-price rule; zero prices need review. Customer identifiers can be missing. No rows are removed by validation."
    )
findings = report.findings_frame()
if findings.empty:
    st.success(
        "No findings under the current checks. This does not establish business correctness."
    )
else:
    severities = st.multiselect(
        "Severity",
        ["error", "warning", "info"],
        default=["error", "warning", "info"],
        key="quality_severity",
    )
    show_frame(
        findings[findings.severity.isin(severities)], "Quality findings and recommended remediation"
    )
    st.caption(
        "Counts overlap across checks. row_positions contains up to 20 zero-based positions in the current revision. Potential outliers and business context flags do not reduce the score."
    )
