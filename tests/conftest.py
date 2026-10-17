"""Small fixtures in this module are synthetic, not UCI observations."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from dataguard.ingestion import read_csv

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def synthetic_retail():
    return pd.DataFrame(
        {
            "InvoiceNo": ["100001", "C100002", "100003", "100004"],
            "StockCode": ["001", "002", "003", "004"],
            "Description": ["Gift", "Return", None, "Adjustment"],
            "Quantity": [2, -1, 1, 1],
            "InvoiceDate": [
                "2011-01-01 10:00:00",
                "2011-01-02 11:00:00",
                "bad-date",
                "2011-02-01 09:00:00",
            ],
            "UnitPrice": [3.0, 3.0, 4.0, -5.0],
            "CustomerID": ["00123", "00123", None, "00456"],
            "Country": ["United Kingdom", "United Kingdom", "France", "France"],
        }
    )


@pytest.fixture
def synthetic_measurements():
    rng = np.random.default_rng(7)
    normal = rng.normal(0, 0.2, size=(99, 2))
    return pd.DataFrame(np.vstack([normal, [15, -15]]), columns=["measurement_a", "measurement_b"])


@pytest.fixture
def retail_sample():
    return read_csv((ROOT / "data/sample/online_retail_sample.csv").read_bytes()).frame


@pytest.fixture
def wine_sample():
    return read_csv((ROOT / "data/sample/wine_red_sample.csv").read_bytes()).frame
