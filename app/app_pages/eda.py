import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from app.state import active, show_chart
from dataguard.profiling import column_profile, iqr_mask, numeric_columns

workspace = active()
frame = workspace.current
kind = st.selectbox(
    "Visualization",
    [
        "Missing values",
        "Numerical distribution",
        "Boxplot",
        "Correlation heatmap",
        "Category frequencies",
        "Potential outliers",
    ],
    key="eda_kind",
)
numbers = numeric_columns(frame)
if kind == "Missing values":
    show_chart(
        px.bar(
            column_profile(frame),
            x="column",
            y="missing_pct",
            labels={"missing_pct": "Missing (%)"},
        ),
        "Missing-value percentage by column",
    )
elif kind == "Category frequencies":
    categories = [c for c in frame if c not in numbers]
    if not categories:
        st.info("No categorical columns are available.")
        st.stop()
    column = st.selectbox("Categorical column", categories, key="eda_category")
    top = st.slider("Number of categories", 5, 40, 15, key="eda_top")
    counts = (
        frame[column]
        .astype("string")
        .fillna("(missing)")
        .value_counts()
        .head(top)
        .rename_axis("category")
        .reset_index(name="records")
    )
    show_chart(
        px.bar(counts, x="records", y="category", orientation="h"),
        f"Most frequent values in {column}",
    )
else:
    if not numbers:
        st.info(
            "Select a dataset with numerical columns, or explicitly convert compatible columns in Data cleaning."
        )
        st.stop()
    if kind == "Correlation heatmap":
        columns = st.multiselect(
            "Numerical columns",
            numbers,
            default=numbers[:12],
            max_selections=25,
            key=f"corr_{workspace.fingerprint}",
        )
        if len(columns) < 2:
            st.info("Select at least two numerical columns.")
        else:
            corr = frame[columns].replace([np.inf, -np.inf], np.nan).corr()
            show_chart(
                px.imshow(corr, zmin=-1, zmax=1, color_continuous_scale="RdBu_r", aspect="auto"),
                "Pairwise Pearson correlations; undefined constant or insufficient-data pairs are blank",
            )
            st.caption(
                "Pairwise complete finite observations; correlation does not establish causation. Constant columns produce undefined correlations."
            )
    else:
        column = st.selectbox("Numerical column", numbers, key="eda_numeric")
        finite = frame[[column]].replace([np.inf, -np.inf], np.nan).dropna()
        if finite.empty:
            st.info("This column has no finite numerical observations.")
            st.stop()
        plot_data = finite.sample(min(10_000, len(finite)), random_state=42)
        st.caption(
            f"Charts use up to 10,000 finite rows sampled with seed 42; current finite rows: {len(finite):,}."
        )
        if kind == "Numerical distribution":
            bins = st.slider("Histogram bins", 5, 100, 30, key="eda_bins")
            show_chart(px.histogram(plot_data, x=column, nbins=bins), f"Distribution of {column}")
        elif kind == "Boxplot":
            show_chart(
                px.box(plot_data, y=column, points="outliers"),
                f"Boxplot of {column}; points indicate statistical tails",
            )
        else:
            flags = iqr_mask(frame[column])
            counts = pd.DataFrame(
                {
                    "observation": ["Within IQR fences", "Potential outlier"],
                    "records": [
                        int((~flags & frame[column].notna() & np.isfinite(frame[column])).sum()),
                        int(flags.sum()),
                    ],
                }
            )
            show_chart(
                px.bar(counts, x="observation", y="records"),
                f"Counts within and outside 1.5 IQR fences for {column}",
            )
            st.caption(
                "1.5 IQR fences are exploratory. Missing/infinite values are excluded; a zero IQR produces no flags. Potential outliers are not confirmed errors."
            )
