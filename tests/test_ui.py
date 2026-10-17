"""Widget-level workflows using Streamlit's real script runner, without a browser."""

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from tests.conftest import ROOT

pytestmark = pytest.mark.ui


def start():
    app = AppTest.from_file(str(ROOT / "app/main.py"), default_timeout=30).run()
    assert not app.exception
    return app


@pytest.mark.parametrize(
    "page", ["overview", "explorer", "quality", "eda", "anomalies", "cleaning", "sql", "exports"]
)
def test_all_pages_render_without_exceptions(page):
    app = start()
    app.switch_page(f"app_pages/{page}.py").run()
    assert not app.exception
    assert app.title[0].value


def test_preview_apply_restore_and_stale_model_lifecycle():
    app = start()
    source = app.session_state["workspace"].original.copy(deep=True)
    initial_rows = len(source)
    app.switch_page("app_pages/cleaning.py").run()
    app.checkbox(key="clean_duplicates").check().run()
    app.button(key="preview_cleaning").click().run()
    workspace = app.session_state["workspace"]
    assert not app.exception and len(workspace.current) == initial_rows
    assert workspace.pending is not None and workspace.revision == 0
    app.button(key="apply_cleaning").click().run()
    workspace = app.session_state["workspace"]
    assert not app.exception and workspace.revision == 1
    assert len(workspace.current) == initial_rows - int(source.duplicated().sum())
    pd.testing.assert_frame_equal(workspace.original, source)
    app.button(key="restore").click().run()
    assert not app.exception
    pd.testing.assert_frame_equal(app.session_state["workspace"].current, source)
    assert app.session_state["workspace"].log == []


def test_changed_configuration_cannot_apply_old_preview():
    app = start().switch_page("app_pages/cleaning.py").run()
    app.checkbox(key="clean_duplicates").check().run()
    app.button(key="preview_cleaning").click().run()
    assert app.button(key="apply_cleaning")
    app.checkbox(key="clean_duplicates").uncheck().run()
    assert not app.exception
    assert not any(b.key == "apply_cleaning" for b in app.button)


def test_wine_model_export_and_dataset_switch_invalidates_results():
    app = start()
    app.selectbox(key="dataset_source").select("Wine Quality · red").run()
    app.switch_page("app_pages/anomalies.py").run()
    app.form_submit_button[0].click().run()
    assert not app.exception
    workspace = app.session_state["workspace"]
    assert workspace.anomaly is not None
    assert len(workspace.anomaly.features) == 11 and "quality" not in workspace.anomaly.features
    assert int(workspace.anomaly.rows.is_anomaly.sum()) > 0
    app.switch_page("app_pages/exports.py").run()
    assert not app.exception
    assert any(d.key == "download_anomalies" for d in app.get("download_button"))
    app.selectbox(key="dataset_source").select("Online Retail · primary").run()
    assert not app.exception and app.session_state["workspace"].anomaly is None
    assert not any(d.key == "download_anomalies" for d in app.get("download_button"))


def test_invalid_rule_json_keeps_previous_rules():
    app = start().switch_page("app_pages/quality.py").run()
    before = app.session_state["workspace"].rules.copy()
    app.text_area[0].set_value('{"Quantity": {"minimum": "wrong"}}')
    app.form_submit_button[0].click().run()
    assert not app.exception and app.error
    assert app.session_state["workspace"].rules == before


def test_upload_empty_state_is_helpful():
    app = start()
    app.selectbox(key="dataset_source").select("Upload CSV").run()
    assert not app.exception and app.info
    assert app.session_state["workspace"] is None


@pytest.mark.parametrize(
    "kind",
    [
        "Numerical distribution",
        "Boxplot",
        "Correlation heatmap",
        "Category frequencies",
        "Potential outliers",
    ],
)
def test_eda_visualizations_render(kind):
    app = start().switch_page("app_pages/eda.py").run()
    app.selectbox(key="eda_kind").select(kind).run()
    assert not app.exception
    assert app.get("plotly_chart")
