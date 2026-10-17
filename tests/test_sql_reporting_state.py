import json
import sqlite3

import numpy as np
import pandas as pd
import pytest

from app.state import workspace_from_bytes
from dataguard.cleaning import CleaningPlan, clean
from dataguard.reporting import anomaly_export, csv_bytes, json_bytes
from dataguard.sql_analytics import QUERIES, build_retail_database, run_query


def test_sql_eligibility_returns_joins_and_net_value(synthetic_retail):
    # Bad date and negative price are excluded; the valid return remains.
    with build_retail_database(synthetic_retail) as database:
        assert database.eligibility["eligible_rows"] == 2
        assert database.eligibility["excluded_rows"] == 2
        returns = run_query(database, "filter_returns")
        assert returns.quantity.tolist() == [-1]
        assert run_query(database, "country_totals").net_line_value_gbp.sum() == 3
        assert len(run_query(database, "customer_join")) == 2
        assert run_query(database, "running_totals").cumulative_net_line_value_gbp.iloc[-1] == 3
        for name in QUERIES:
            assert isinstance(run_query(database, name), pd.DataFrame)


def test_unknown_customer_retained_and_sql_read_only(synthetic_retail):
    synthetic_retail.loc[0, "CustomerID"] = None
    with build_retail_database(synthetic_retail) as database:
        assert (
            run_query(database, "customer_join").customer_status.iloc[0]
            == "unknown customer identifier"
        )
        assert run_query(database, "filter_returns", country="' OR 1=1 --").empty
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            database.connection.execute("DELETE FROM transactions")
        with pytest.raises(ValueError):
            run_query(database, "../arbitrary")


def test_sql_empty_eligible_and_missing_columns(synthetic_retail):
    with pytest.raises(ValueError, match="requires"):
        build_retail_database(pd.DataFrame({"x": [1]}))
    synthetic_retail["InvoiceDate"] = "invalid"
    with build_retail_database(synthetic_retail) as database:
        assert database.eligibility["eligible_rows"] == 0
        assert run_query(database, "country_totals").empty


def test_exports_portable_json_csv_and_formula_protection():
    payload = json.loads(json_bytes({"x": np.nan, "y": np.inf, "z": np.int64(3), "a": pd.NA}))
    assert payload == {"x": None, "y": None, "z": 3, "a": None}
    frame = pd.DataFrame({"text": ["=1+1", "plain"], "quantity": [-1, 2]})
    raw = csv_bytes(frame).decode("utf-8-sig")
    safe = csv_bytes(frame, spreadsheet_safe=True).decode("utf-8-sig")
    assert "=1+1,-1" in raw
    assert "'=1+1,-1" in safe
    assert frame.text.iloc[0] == "=1+1"


def test_anomaly_export_position_alignment_and_collisions():
    frame = pd.DataFrame({"x": [10, 20]}, index=[7, 7])
    rows = pd.DataFrame({"row_position": [0, 1], "anomaly_score": [0.2, 0.7]})
    assert anomaly_export(frame, rows).x.tolist() == [10, 20]
    with pytest.raises(ValueError):
        anomaly_export(frame, rows.iloc[::-1])
    with pytest.raises(ValueError):
        anomaly_export(frame.rename(columns={"x": "anomaly_score"}), rows)


def test_revision_lifecycle_discards_stale_results_and_preserves_original():
    workspace = workspace_from_bytes(
        b"x,y\n1,a\n1,a\n2,b", "synthetic.csv", "synthetic test fixture"
    )
    original = workspace.original.copy(deep=True)
    workspace.quality = workspace.report()
    workspace.anomaly = "old model"
    workspace.pending = "old preview"
    workspace.apply(clean(workspace.current, CleaningPlan(drop_duplicates=True)))
    assert len(workspace.current) == 2 and workspace.revision == 1
    assert workspace.anomaly is None and workspace.pending is None and workspace.quality is None
    assert workspace.log[0]["revision"] == 1
    pd.testing.assert_frame_equal(workspace.original, original)
    workspace.reset()
    assert workspace.revision == 2 and workspace.log == []
    pd.testing.assert_frame_equal(workspace.current, original)
