"""
End-to-end pipeline test: extract -> transform -> load -> read back.

Uses SQLite so it runs anywhere without a MySQL server; it proves the
pipeline produces a consistent, queryable dataset. MySQL-specific DDL
is exercised by sql/schema.sql and the Docker setup.
"""

import os
import sys

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from etl.etl_main import extract, load, transform  # noqa: E402


@pytest.fixture(scope="module")
def loaded_engine(tmp_path_factory):
    df = transform(extract("data/input.csv"))
    db_file = tmp_path_factory.mktemp("e2e") / "sales.db"
    engine = create_engine(f"sqlite:///{db_file}")
    rows = load(df, mysql_uri=f"sqlite:///{db_file}")
    engine._source_df = df
    engine._rows_loaded = rows
    return engine


def test_pipeline_loads_all_rows(loaded_engine):
    assert loaded_engine._rows_loaded == len(loaded_engine._source_df)
    with loaded_engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM sales_staging")).scalar_one()
    assert count == len(loaded_engine._source_df)


def test_pipeline_revenue_is_consistent(loaded_engine):
    with loaded_engine.connect() as conn:
        db_total = conn.execute(
            text("SELECT COALESCE(SUM(total), 0) FROM sales_staging")
        ).scalar_one()
    assert float(db_total) == pytest.approx(float(loaded_engine._source_df["total"].sum()))


def test_pipeline_roundtrip_preserves_categories(loaded_engine):
    from etl.product_catalog import CATEGORIES

    with loaded_engine.connect() as conn:
        cats = pd.read_sql(
            "SELECT DISTINCT category FROM sales_staging ORDER BY category",
            con=loaded_engine.connect(),
        )
    actual = set(cats["category"])
    # The real dataset is fully mapped, so no product falls through to "Other"
    assert actual <= set(CATEGORIES)
    assert actual == set(CATEGORIES)  # every catalog category is present


def test_pipeline_is_rerunnable(loaded_engine, tmp_path):
    """Running load() twice without truncate must not crash (append)."""
    df = transform(extract("data/input.csv")).head(50)
    db_file = tmp_path / "rerun.db"
    uri = f"sqlite:///{db_file}"
    load(df, mysql_uri=uri)
    load(df, mysql_uri=uri)  # second append should not raise
    engine = create_engine(uri)
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM sales_staging")).scalar_one()
    assert count == 100  # 50 + 50
