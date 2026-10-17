import streamlit as st

from app.state import active, show_frame
from dataguard.sql_analytics import QUERIES, build_retail_database, query_sql, run_query

workspace = active()
if not workspace.is_retail:
    st.info("Choose Online Retail to explore the relational transaction and customer tables.")
    st.stop()
st.caption(
    "Each run builds a temporary in-memory SQLite database from an explicitly validated subset. Returns, zero prices, duplicate rows, and missing customer identifiers are retained. Invalid dates, missing keys/country, nonfinite/nonintegral quantities, and negative/nonfinite prices are excluded from this analytical view only."
)
name = st.selectbox("Example query", list(QUERIES), format_func=QUERIES.get, key="sql_query")
country = st.text_input("Country filter (WHERE example)", value="United Kingdom", key="sql_country")
st.code(query_sql(name), language="sql")
try:
    with (
        st.spinner("Building isolated relational view…"),
        build_retail_database(workspace.current) as database,
    ):
        eligibility = database.eligibility
        result = run_query(database, name, country=country)
    st.caption(
        f"Source rows: {eligibility['source_rows']:,} · Eligible: {eligibility['eligible_rows']:,} · Excluded by analytical policy: {eligibility['excluded_rows']:,}"
    )
    show_frame(result, "Curated SQL query result")
except ValueError as exc:
    st.error(str(exc))
st.caption(
    "Queries are curated and read-only; filter values are parameterized. Net line value = Quantity × UnitPrice in GBP and can include returns. Sample totals describe the sample, not the retailer's total revenue. No customer identities are inferred."
)
