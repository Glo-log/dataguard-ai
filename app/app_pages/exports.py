import pandas as pd
import streamlit as st

from app.state import active
from dataguard.reporting import anomaly_export, csv_bytes, json_bytes

workspace = active()
report = workspace.report()
st.caption(
    "Exports use the accepted current revision and stored model run. A pending cleaning preview is excluded. Choosing another dataset, applying cleaning, or restoring the original clears earlier model results."
)
safe = st.checkbox(
    "Protect text starting with spreadsheet formula characters",
    value=True,
    key="export_safe",
    help="Prefixes risky text with an apostrophe for spreadsheet use. This changes those text values; uncheck for a faithful machine-readable export. Numeric negative values are preserved.",
)
prefix = f"dataguard_revision_{workspace.revision}"
st.download_button(
    "Download current dataset (CSV)",
    csv_bytes(workspace.current, spreadsheet_safe=safe),
    f"{prefix}_dataset.csv",
    "text/csv",
    key="download_dataset",
)
st.download_button(
    "Download quality findings (CSV)",
    csv_bytes(report.findings_frame(), spreadsheet_safe=safe),
    f"{prefix}_findings.csv",
    "text/csv",
    key="download_findings",
)
payload = {
    "dataset": workspace.name,
    "source": workspace.source,
    "source_sha256": workspace.fingerprint,
    "revision": workspace.revision,
    "quality": report.to_dict(),
}
st.download_button(
    "Download structured quality report (JSON)",
    json_bytes(payload),
    f"{prefix}_quality.json",
    "application/json",
    key="download_report",
)
st.download_button(
    "Download transformation log (JSON)",
    json_bytes(
        {"dataset": workspace.name, "revision": workspace.revision, "operations": workspace.log}
    ),
    f"{prefix}_transformations.json",
    "application/json",
    key="download_log",
)
if workspace.log:
    st.download_button(
        "Download transformation log (CSV)",
        csv_bytes(pd.DataFrame(workspace.log), spreadsheet_safe=safe),
        f"{prefix}_transformations.csv",
        "text/csv",
        key="download_log_csv",
    )
if workspace.anomaly is not None:
    result = workspace.anomaly
    try:
        exported = anomaly_export(workspace.current, result.rows)
        st.download_button(
            "Download anomaly results with source rows (CSV)",
            csv_bytes(exported, spreadsheet_safe=safe),
            f"{prefix}_anomalies.csv",
            "text/csv",
            key="download_anomalies",
        )
    except ValueError as exc:
        st.warning(str(exc))
        st.download_button(
            "Download positional anomaly scores (CSV)",
            csv_bytes(result.rows),
            f"{prefix}_anomaly_scores.csv",
            "text/csv",
            key="download_scores",
        )
    st.download_button(
        "Download model settings (JSON)",
        json_bytes(
            {
                "revision": workspace.revision,
                "features": result.features,
                "excluded": result.excluded,
                "parameters": result.parameters,
                "interpretation": "Statistical screening only; flags are not confirmed errors.",
            }
        ),
        f"{prefix}_model.json",
        "application/json",
        key="download_model",
    )
else:
    st.info("Run Anomaly detection on the current revision to enable model result downloads.")
