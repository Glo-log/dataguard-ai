"""Isolated relational retail analytics, with curated read-only query selection."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

QUERIES = {
    "select_transactions": "SELECT · transaction preview",
    "filter_returns": "WHERE · returns by country",
    "country_totals": "GROUP BY · country totals",
    "customer_join": "JOIN · known and unknown customers",
    "monthly_cte": "CTE · monthly net line value",
    "running_totals": "Window · cumulative monthly value",
    "quality_summary": "Data quality · source and eligible rows",
}
SQL_DIR = Path(__file__).resolve().parents[2] / "sql"
REQUIRED = {
    "InvoiceNo",
    "StockCode",
    "Quantity",
    "UnitPrice",
    "CustomerID",
    "Country",
    "InvoiceDate",
}


@dataclass
class RetailDatabase:
    connection: sqlite3.Connection
    eligibility: dict

    def close(self) -> None:
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def build_retail_database(frame: pd.DataFrame) -> RetailDatabase:
    """Create a validated subset, customer dimension, and source quality summary.

    Retains negative quantities (returns), zero prices, exact duplicate rows, and
    missing CustomerIDs. Rejects nonfinite/nonintegral quantities, nonfinite or
    negative prices, invalid dates, and missing required transaction keys/country.
    This analytic policy is explicit and does not modify the source dataset.
    """
    if REQUIRED - set(frame.columns):
        raise ValueError(f"Retail SQL requires columns: {sorted(REQUIRED - set(frame.columns))}")
    data = frame.reset_index(drop=True).copy(deep=True)
    quantity = pd.to_numeric(data["Quantity"], errors="coerce")
    price = pd.to_numeric(data["UnitPrice"], errors="coerce")
    dates = pd.to_datetime(data["InvoiceDate"], errors="coerce", format="ISO8601")
    finite_quantity = quantity.notna() & np.isfinite(quantity) & quantity.mod(1).eq(0)
    finite_price = price.notna() & np.isfinite(price) & price.ge(0)
    keys = data[["InvoiceNo", "StockCode", "Country"]].notna().all(axis=1)
    valid = (finite_quantity & finite_price & dates.notna() & keys).fillna(False)
    eligibility = {
        "source_rows": len(data),
        "eligible_rows": int(valid.sum()),
        "excluded_rows": int((~valid).sum()),
        "source_missing_customer_rows": int(data["CustomerID"].isna().sum()),
        "source_duplicate_rows": int(data.duplicated().sum()),
    }
    transaction = pd.DataFrame(
        {
            "row_position": np.flatnonzero(valid.to_numpy(dtype=bool)),
            "invoice_no": data.loc[valid, "InvoiceNo"].astype("string").to_numpy(),
            "stock_code": data.loc[valid, "StockCode"].astype("string").to_numpy(),
            "customer_id": data.loc[valid, "CustomerID"].astype("string").to_numpy(),
            "country": data.loc[valid, "Country"].astype("string").to_numpy(),
            "quantity": quantity[valid].astype(float).to_numpy(),
            "unit_price": price[valid].astype(float).to_numpy(),
            "invoice_date": dates[valid].dt.strftime("%Y-%m-%d %H:%M:%S").to_numpy(),
        }
    )
    customers = transaction[["customer_id"]].dropna().drop_duplicates().copy()
    customers["customer_status"] = "known customer identifier"
    connection = sqlite3.connect(":memory:")
    try:
        transaction.to_sql("transactions", connection, index=False, if_exists="fail")
        customers.to_sql("customers", connection, index=False, if_exists="fail")
        connection.execute("CREATE UNIQUE INDEX customer_key ON customers(customer_id)")
        pd.DataFrame(
            [{"metric": key, "value": value} for key, value in eligibility.items()]
        ).to_sql("input_quality", connection, index=False)
        connection.execute("PRAGMA query_only=ON")
        return RetailDatabase(connection, eligibility)
    except Exception:
        connection.close()
        raise


def query_sql(name: str) -> str:
    if name not in QUERIES:
        raise ValueError("Choose one of the curated SQL examples.")
    return (SQL_DIR / f"{name}.sql").read_text(encoding="utf-8")


def run_query(
    database: RetailDatabase, name: str, *, country: str = "United Kingdom"
) -> pd.DataFrame:
    """No arbitrary SQL strings, file access, or persistent connections are exposed."""
    return pd.read_sql_query(query_sql(name), database.connection, params={"country": country})
