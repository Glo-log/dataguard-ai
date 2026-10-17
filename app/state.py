"""Per-session dataset revisions prevent stale exports and preserve the source."""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import streamlit as st

from dataguard.cleaning import CleaningResult
from dataguard.ingestion import read_csv
from dataguard.validation import ColumnRule, QualityReport, retail_rules, validate

ROOT = Path(__file__).resolve().parents[1]
DEMOS = {
    "Online Retail · primary": "online_retail_sample.csv",
    "Wine Quality · red": "wine_red_sample.csv",
    "Wine Quality · white": "wine_white_sample.csv",
}


@dataclass
class Workspace:
    original: pd.DataFrame
    current: pd.DataFrame
    name: str
    source: str
    fingerprint: str
    rules: dict[str, ColumnRule] = field(default_factory=dict)
    revision: int = 0
    log: list[dict] = field(default_factory=list)
    quality: QualityReport | None = None
    anomaly: object | None = None
    pending: object | None = None

    @property
    def is_retail(self) -> bool:
        return {"InvoiceNo", "StockCode", "Quantity", "UnitPrice"}.issubset(self.current)

    def report(self) -> QualityReport:
        if self.quality is None:
            self.quality = validate(self.current, self.rules, retail_context=self.is_retail)
        return self.quality

    def apply(self, result: CleaningResult) -> None:
        self.current = result.frame.reset_index(drop=True).copy(deep=True)
        self.revision += 1
        self.log.extend([{**entry, "revision": self.revision} for entry in result.log])
        self.invalidate()

    def invalidate(self) -> None:
        self.quality = None
        self.anomaly = None
        self.pending = None

    def reset(self) -> None:
        self.current = self.original.copy(deep=True)
        self.revision += 1
        self.log = []
        self.invalidate()


def workspace_from_bytes(content: bytes, name: str, source: str, **kwargs) -> Workspace:
    loaded = read_csv(content, **kwargs)
    rules = retail_rules() if {"InvoiceNo", "UnitPrice", "Quantity"}.issubset(loaded.frame) else {}
    return Workspace(
        loaded.frame.copy(deep=True),
        loaded.frame.copy(deep=True),
        name,
        source,
        hashlib.sha256(content).hexdigest(),
        rules,
    )


@st.cache_data(ttl=3600, max_entries=3, show_spinner=False)
def demo_bytes(filename: str) -> bytes:
    """Only public bundled UCI samples enter a shared cache."""
    if filename not in DEMOS.values():
        raise ValueError("Unknown demonstration dataset.")
    return (ROOT / "data" / "sample" / filename).read_bytes()


def active() -> Workspace:
    workspace = st.session_state.get("workspace")
    if workspace is None:
        st.info(
            "Choose a bundled demonstration or upload a CSV in the sidebar.",
            icon=":material/upload_file:",
        )
        st.stop()
    st.caption(
        f"{workspace.name}  ·  Revision {workspace.revision}  ·  {len(workspace.current):,} records"
    )
    return workspace


def show_frame(frame: pd.DataFrame, label: str, *, limit: int = 1000) -> None:
    """Bound browser payloads; convert mixed objects to display-only strings."""
    display = frame.head(limit).copy()
    for c in display.select_dtypes(include="object"):
        display[c] = display[c].astype("string")
    st.dataframe(display, hide_index=True, width="stretch", alt=label)
    if len(frame) > limit:
        st.caption(
            f"Showing {limit:,} of {len(frame):,} records. Exports include the complete current result."
        )


def show_chart(figure, label: str) -> None:
    figure.update_layout(margin={"l": 12, "r": 12, "t": 40, "b": 12}, height=370)
    st.plotly_chart(
        figure, width="stretch", alt=label, config={"scrollZoom": False, "displaylogo": False}
    )
