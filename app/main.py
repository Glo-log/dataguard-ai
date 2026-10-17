"""Entry point: python -m streamlit run app/main.py (from repository root)."""

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for location in (ROOT, ROOT / "src"):
    if str(location) not in sys.path:
        sys.path.insert(0, str(location))

import streamlit as st  # noqa: E402

from app.state import DEMOS, demo_bytes, workspace_from_bytes  # noqa: E402
from dataguard.ingestion import IngestionError  # noqa: E402

st.set_page_config(page_title="DataGuard AI", page_icon=":material/fact_check:", layout="wide")
st.session_state.setdefault("workspace", None)
st.session_state.setdefault("loaded_token", None)
st.session_state.setdefault("source_selection", None)

with st.sidebar:
    st.header("DataGuard AI", divider="green")
    st.caption("Understand the data. Review the exceptions.")
    selected = st.selectbox("Dataset", [*DEMOS, "Upload CSV"], key="dataset_source")
    if selected != st.session_state.source_selection:
        st.session_state.workspace = None
        st.session_state.loaded_token = None
        st.session_state.source_selection = selected
    if selected in DEMOS:
        filename = DEMOS[selected]
        if st.session_state.loaded_token != filename:
            try:
                st.session_state.workspace = workspace_from_bytes(
                    demo_bytes(filename), filename, "UCI public sample · CC BY 4.0"
                )
                st.session_state.loaded_token = filename
            except (OSError, IngestionError) as exc:
                st.error(
                    f"Sample unavailable: {exc}. Run the dataset scripts described in README.md."
                )
        st.caption("Real UCI records; seeded coverage sample. Rates describe this sample only.")
    else:
        st.caption("Up to 25 MB · 200,000 rows · 250 columns. This demo runs in server memory.")
        upload = st.file_uploader("CSV file", type=["csv"], key="csv_upload")
        encoding = st.selectbox("Encoding", ["utf-8-sig", "cp1252", "latin-1"], key="csv_encoding")
        delimiter_label = st.selectbox(
            "Delimiter", ["Comma", "Semicolon", "Tab", "Pipe"], key="csv_delimiter"
        )
        delimiter = {"Comma": ",", "Semicolon": ";", "Tab": "\t", "Pipe": "|"}[delimiter_label]
        if upload is not None:
            content = upload.getvalue()
            token = (hashlib.sha256(content).hexdigest(), encoding, delimiter)
            if st.session_state.loaded_token != token:
                try:
                    with st.spinner("Inspecting CSV…"):
                        workspace = workspace_from_bytes(
                            content,
                            upload.name,
                            "User upload",
                            encoding=encoding,
                            delimiter=delimiter,
                        )
                    st.session_state.workspace = workspace
                    st.session_state.loaded_token = token
                except IngestionError as exc:
                    st.session_state.workspace = None
                    st.error(str(exc))
        else:
            st.session_state.workspace = None
            st.session_state.loaded_token = None
    workspace = st.session_state.workspace
    if workspace:
        st.divider()
        st.caption(
            f"{workspace.name}\n\n{len(workspace.current):,} rows · {workspace.current.shape[1]} columns\n\nRevision {workspace.revision}"
        )
        if st.button("Restore original dataset", key="restore", width="stretch"):
            workspace.reset()
            st.rerun()
    st.divider()
    st.caption(
        "Flags support investigation. An anomaly is not a confirmed error. Source files remain unchanged."
    )

page = st.navigation(
    [
        st.Page(
            "app_pages/overview.py", title="Overview", icon=":material/dashboard:", default=True
        ),
        st.Page("app_pages/explorer.py", title="Dataset explorer", icon=":material/table_view:"),
        st.Page("app_pages/quality.py", title="Data quality report", icon=":material/fact_check:"),
        st.Page("app_pages/eda.py", title="Exploratory data analysis", icon=":material/bar_chart:"),
        st.Page(
            "app_pages/anomalies.py", title="Anomaly detection", icon=":material/troubleshoot:"
        ),
        st.Page(
            "app_pages/cleaning.py", title="Data cleaning", icon=":material/cleaning_services:"
        ),
        st.Page("app_pages/sql.py", title="SQL analytics", icon=":material/database:"),
        st.Page("app_pages/exports.py", title="Export results", icon=":material/download:"),
    ],
    position="sidebar",
)
st.title(page.title, icon=page.icon)
page.run()
