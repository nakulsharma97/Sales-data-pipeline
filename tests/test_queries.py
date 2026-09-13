"""
Tests for the dashboard SQL queries.

They run against an in-file SQLite database loaded with the real ETL
transform output, so the SQL logic (filters, grouping, sorting, limits)
is verified without needing a MySQL server. MySQL compatibility of the
schema is covered separately by sql/schema.sql + the ETL.
"""

import os
import sys

import pandas as pd
import pytest
from sqlalchemy import create_engine

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from etl.etl_main import extract, transform  # noqa: E402
from queries import sales_queries as sq  # noqa: E402


@pytest.fixture(scope="module")
def engine(tmp_path_factory):
    """SQLite database with the transformed real dataset."""
    df = transform(extract("data/input.csv"))
    db_file = tmp_path_factory.mktemp("db") / "sales.db"
    eng = create_engine(f"sqlite:///{db_file}")
    df.to_sql("sales_staging", con=eng, if_exists="replace", index=False)
    eng._test_df = df  # keep the source frame for comparisons
    return eng


def run(engine, sql, params):
    with engine.connect() as conn:
        return pd.read_sql(sql, con=conn, params=params)


# ------------------------------------------------------------------- KPIs
def test_total_revenue(engine):
    df = engine._test_df
    out = run(engine, *sq.get_total_revenue())
    assert float(out["total_revenue"].iloc[0]) == pytest.approx(float(df["total"].sum()))


def test_total_orders(engine):
    df = engine._test_df
    out = run(engine, *sq.get_total_orders())
    assert int(out["total_orders"].iloc[0]) == len(df)


def test_total_products(engine):
    df = engine._test_df
    out = run(engine, *sq.get_total_products())
    assert int(out["total_products"].iloc[0]) == df["product"].nunique()


def test_avg_order_value(engine):
    df = engine._test_df
    out = run(engine, *sq.get_avg_order_value())
    assert float(out["avg_order_value"].iloc[0]) == pytest.approx(float(df["total"].mean()))


# ----------------------------------------------------------------- Filters
def test_date_filters(engine):
    df = engine._test_df
    # ISO strings as parameters: portable across SQLite and MySQL bindings
    start, end = "2025-01-01", "2025-03-31 23:59:59"
    out = run(engine, *sq.get_total_revenue(start_date=start, end_date=end))
    expected = df[
        (df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))
    ]["total"].sum()
    assert float(out["total_revenue"].iloc[0]) == pytest.approx(float(expected))


def test_category_filter(engine):
    df = engine._test_df
    out = run(engine, *sq.get_total_revenue(categories=["Bakery"]))
    expected = df[df["category"] == "Bakery"]["total"].sum()
    assert float(out["total_revenue"].iloc[0]) == pytest.approx(float(expected))


def test_product_filter(engine):
    df = engine._test_df
    out = run(engine, *sq.get_total_orders(products=["Milk"]))
    expected = int((df["product"] == "Milk").sum())
    assert int(out["total_orders"].iloc[0]) == expected


def test_combined_filters(engine):
    df = engine._test_df
    out = run(engine, *sq.get_total_revenue(
        start_date="2024-06-01",
        end_date="2024-12-31 23:59:59",
        categories=["Beverages"],
        products=["Coffee", "Tea"],
    ))
    mask = (
        (df["date"] >= "2024-06-01")
        & (df["date"] <= "2024-12-31 23:59:59")
        & (df["product"].isin(["Coffee", "Tea"]))
    )
    assert float(out["total_revenue"].iloc[0]) == pytest.approx(float(df[mask]["total"].sum()))


def test_filter_matching_nothing_returns_empty(engine):
    out = run(engine, *sq.get_total_revenue(products=["Nonexistent Product"]))
    assert out["total_revenue"].iloc[0] == 0 or out.empty


# ------------------------------------------------------------------ Charts
def test_sales_by_product_groups_correctly(engine):
    df = engine._test_df
    out = run(engine, *sq.get_sales_by_product())
    assert list(out.columns) == ["product", "revenue", "units"]
    assert len(out) == df["product"].nunique()
    top_row = df.groupby("product")["total"].sum().idxmax()
    assert out["product"].iloc[0] == top_row  # sorted by revenue DESC


def test_sales_by_category(engine):
    df = engine._test_df
    out = run(engine, *sq.get_sales_by_category())
    assert set(out["category"]) <= set(df["category"].unique())
    assert len(out) == df["category"].nunique()


def test_revenue_by_date(engine):
    df = engine._test_df
    out = run(engine, *sq.get_revenue_by_date())
    expected = df.groupby(df["date"].dt.date)["total"].sum()
    assert len(out) == len(expected)
    assert float(out["daily_revenue"].sum()) == pytest.approx(float(df["total"].sum()))


def test_top_selling_products_limit(engine):
    out = run(engine, *sq.get_top_selling_products(limit=3))
    assert len(out) == 3


def test_top_selling_products_limit_is_sanitized(engine):
    """A string limit must be cast to int, never interpolated raw."""
    out = run(engine, *sq.get_top_selling_products(limit="5"))
    assert len(out) == 5


def test_products_in_categories(engine):
    df = engine._test_df
    sql, params = sq.get_products_in_categories(["Bakery"])
    out = run(engine, sql, params)
    expected = set(df[df["category"] == "Bakery"]["product"].unique())
    assert set(out["product"]) == expected


def test_sales_data_filtered_schema(engine):
    out = run(engine, *sq.get_sales_data_filtered())
    assert list(out.columns) == ["date", "product", "category", "quantity", "price", "total"]
