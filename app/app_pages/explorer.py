import numpy as np
import streamlit as st

from app.state import active, show_frame
from dataguard.profiling import column_profile, profile

workspace = active()
frame = workspace.current
summary = profile(frame)
st.subheader("Dataset preview")
selected = st.multiselect(
    "Preview columns",
    list(frame),
    default=list(frame),
    key=f"explorer_columns_{workspace.fingerprint}",
)
if selected:
    show_frame(frame[selected], "Selected dataset columns")
else:
    st.info("Select a column to preview its values.")
st.subheader("Column profile")
show_frame(column_profile(frame), "Column types, missing-value percentages, and distinct counts")
st.caption(
    f"Numeric columns: {', '.join(summary['numeric_columns']) or 'None'} · Approximate memory: {summary['memory_bytes'] / 1024**2:.2f} MB"
)
st.subheader("Descriptive statistics")
if len(frame.columns):
    # Nonfinite observations are excluded from descriptive statistics, not the data.
    show_frame(
        frame.replace([np.inf, -np.inf], np.nan)
        .describe(include="all")
        .T.reset_index(names="column"),
        "Descriptive statistics excluding infinite values",
    )
st.caption(
    "Only empty CSV fields are treated as missing at ingestion. Conventional ID/Id, _id, Code, CustomerID and InvoiceNo headers are read as text. Other dtypes are inferred; configure rules for ambiguous fields."
)
