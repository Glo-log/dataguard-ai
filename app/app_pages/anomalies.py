import numpy as np
import plotly.express as px
import streamlit as st

from app.state import active, show_chart, show_frame
from dataguard.anomaly_detection import MAX_MODEL_ROWS, MIN_ROWS, detect_anomalies
from dataguard.ingestion import is_identifier_column
from dataguard.profiling import numeric_columns

workspace = active()
frame = workspace.current
st.info(
    "Isolation Forest screens for unusual combinations of numerical measurements. Flags are not confirmed data errors, and scores are not probabilities. No records are deleted. The contamination setting controls the threshold rather than estimating an error rate."
)
if not MIN_ROWS <= len(frame) <= MAX_MODEL_ROWS:
    st.warning(f"Use {MIN_ROWS}–{MAX_MODEL_ROWS:,} rows for interactive anomaly screening.")
    st.stop()
numeric = numeric_columns(frame)
if not numeric:
    st.info("No numerical features are available. Try the Wine Quality demonstration.")
    st.stop()
# Targets, numeric identifiers, and known retail keys are excluded by default.
default = [
    c
    for c in numeric
    if c.lower() not in {"quality", "target", "label"} and not is_identifier_column(c)
]
with st.form("anomaly_form"):
    features = st.multiselect(
        "Numerical features",
        numeric,
        default=default,
        key=f"anomaly_features_{workspace.fingerprint}",
    )
    contamination = st.slider(
        "Contamination (threshold fraction)", 0.01, 0.50, 0.05, 0.01, key="anomaly_contamination"
    )
    seed = st.number_input(
        "Random state", min_value=0, max_value=2**32 - 1, value=42, step=1, key="anomaly_seed"
    )
    st.caption(
        "Wine defaults use the 11 physicochemical measurements and exclude the quality rating. Red and white wine are analyzed separately. Avoid identifier columns and targets. All-null/constant features are excluded; missing and infinite inputs are median-imputed for modeling only."
    )
    if st.form_submit_button("Run Isolation Forest", type="primary"):
        workspace.anomaly = None
        try:
            with st.spinner("Fitting median imputation and Isolation Forest…"):
                workspace.anomaly = detect_anomalies(
                    frame, features, contamination=float(contamination), random_state=int(seed)
                )
        except ValueError as exc:
            st.error(str(exc))
result = workspace.anomaly
if result is None:
    st.caption("Choose features and run the model to view scores and flagged observations.")
    st.stop()
rows = result.rows
st.caption(
    f"Stored run for revision {workspace.revision}: features={', '.join(result.features)}; contamination={result.parameters['contamination']}; seed={result.parameters['random_state']}. Form changes take effect on Run."
)
if result.excluded:
    st.warning(f"Excluded features: {result.excluded}")
with st.container(horizontal=True):
    st.metric("Flagged records", int(rows.is_anomaly.sum()), border=True)
    st.metric("Flagged fraction", f"{rows.is_anomaly.mean():.2%}", border=True)
    st.metric("Features used", len(result.features), border=True)
show_chart(
    px.histogram(
        rows,
        x="anomaly_score",
        color="is_anomaly",
        nbins=35,
        labels={"anomaly_score": "Anomaly score (higher = more unusual)"},
    ),
    "In-sample anomaly score distributions for flagged and unflagged records",
)
if len(result.features) >= 2:
    axes = st.multiselect(
        "Scatter axes (choose two)",
        result.features,
        default=result.features[:2],
        max_selections=2,
        key=f"anomaly_axes_{workspace.fingerprint}",
    )
    if len(axes) == 2:
        chart = frame[axes].reset_index(drop=True).replace([np.inf, -np.inf], np.nan).copy()
        chart["flag"] = rows.is_anomaly.map({True: "Flagged", False: "Unflagged"})
        chart["row_position"] = rows.row_position
        chart = chart.sample(min(5000, len(chart)), random_state=42)
        show_chart(
            px.scatter(
                chart,
                x=axes[0],
                y=axes[1],
                color="flag",
                hover_data=["row_position"],
                render_mode="svg",
            ),
            "Anomaly flags on two original measurement axes; missing points are omitted",
        )
        st.caption(
            "Scatter plot uses up to 5,000 rows. Flags use all selected features; axes show original values."
        )
show_frame(
    rows.sort_values("anomaly_score", ascending=False), "Observations ranked by anomaly score"
)
st.caption(
    "In-sample exploratory screening; no ground-truth error labels, held-out evaluation, accuracy, precision, or recall are claimed. Imputation and cohort composition can influence which observations are flagged."
)
