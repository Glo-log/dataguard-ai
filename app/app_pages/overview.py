import pandas as pd
import plotly.express as px
import streamlit as st

from app.state import active, show_chart, show_frame
from dataguard.profiling import column_profile, profile

st.markdown(
    "Assess completeness and consistency, inspect unusual observations, and prepare a traceable analytical dataset."
)
workspace = active()
with st.spinner("Profiling the current dataset…"):
    summary = profile(workspace.current)
    report = workspace.report()
with st.container(horizontal=True):
    st.metric("Records", f"{summary['rows']:,}", border=True)
    st.metric("Columns", summary["columns"], border=True)
    st.metric(
        "Quality score",
        f"{report.score:.2f} / 100" if report.score is not None else "Unavailable",
        border=True,
    )
    st.metric("Repeated rows", f"{summary['duplicate_rows']:,}", border=True)
st.caption(
    "The quality score is a documented project heuristic. Business rules and record context determine what needs remediation."
)
left, right = st.columns(2)
with left, st.container(border=True):
    st.subheader("Quality indicators")
    indicators = pd.DataFrame(
        [
            {"indicator": k.title(), "satisfaction_pct": v * 100}
            for k, v in report.indicators.items()
            if k in {"completeness", "uniqueness", "validity"} and v is not None
        ]
    )
    show_chart(
        px.bar(
            indicators,
            x="satisfaction_pct",
            y="indicator",
            orientation="h",
            range_x=[0, 100],
            labels={"satisfaction_pct": "Satisfaction (%)", "indicator": ""},
        ),
        "Completeness, uniqueness, and configured validity satisfaction percentages",
    )
with right, st.container(border=True):
    st.subheader("Missing values by column")
    show_chart(
        px.bar(
            column_profile(workspace.current),
            x="column",
            y="missing_pct",
            labels={"missing_pct": "Missing (%)", "column": ""},
        ),
        "Percentage of missing values for each column",
    )
with st.container(border=True):
    st.subheader("Start your review")
    st.markdown(
        "1. Inspect fields in **Dataset explorer** and set rules in **Data quality report**.\n2. Explore distributions; switch to Wine Quality for numerical anomaly screening.\n3. Preview cleaning, apply selected transformations, and export the current revision."
    )
show_frame(workspace.current.head(8), "First eight records of the current dataset")
st.caption(
    "Independent portfolio project · UCI sources and attribution are documented in docs/DATASETS.md."
)
