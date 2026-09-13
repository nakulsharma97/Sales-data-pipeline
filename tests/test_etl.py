"""
Tests for the ETL pipeline (extract + transform).

Transform tests cover the acceptance criteria: date parsing, revenue
calculation, invalid-value handling, deduplication and category mapping.
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from etl.etl_main import extract, transform  # noqa: E402
from etl.product_catalog import PRODUCT_CATEGORIES  # noqa: E402

REQUIRED_COLUMNS = ["date", "product", "category", "quantity", "price", "total"]


def test_extract_real_dataset():
    df = extract("data/input.csv")
    assert not df.empty
    assert all(col in df.columns for col in ["date", "product", "quantity", "price"])


def test_transform_computes_total():
    df = pd.DataFrame({
        "date": ["2025-01-01"],
        "product": ["Bread"],
        "quantity": [10],
        "price": [1.20],
    })
    out = transform(df)
    assert out["total"].iloc[0] == 12.0


def test_transform_parses_dates():
    df = pd.DataFrame({
        "date": ["2025-01-01"],
        "product": ["Milk"],
        "quantity": [2],
        "price": [0.95],
    })
    out = transform(df)
    assert pd.api.types.is_datetime64_any_dtype(out["date"])
    assert out["date"].iloc[0] == pd.Timestamp("2025-01-01")


def test_transform_drops_missing_and_invalid_rows():
    df = pd.DataFrame({
        "date": ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"],
        "product": ["Bread", "Milk", "Cheese", "Eggs"],
        "quantity": [1, None, 3, -5],
        "price": [1.20, 0.95, "not-a-number", 0.25],
    })
    out = transform(df)
    # Row 2 has missing quantity, row 3 invalid price, row 4 negative quantity
    assert len(out) == 1
    assert out["product"].iloc[0] == "Bread"


def test_transform_removes_duplicates():
    df = pd.DataFrame({
        "date": ["2025-01-01", "2025-01-01"],
        "product": ["Bread", "Bread"],
        "quantity": [2, 2],
        "price": [1.20, 1.20],
    })
    out = transform(df)
    assert len(out) == 1


def test_transform_maps_categories():
    df = pd.DataFrame({
        "date": ["2025-01-01", "2025-01-01"],
        "product": ["Bread", "Mystery Item"],
        "quantity": [1, 1],
        "price": [1.20, 5.00],
    })
    out = transform(df)
    assert set(out["category"]) == {"Bakery", "Other"}


def test_transform_output_schema():
    df = pd.DataFrame({
        "date": ["2025-01-01"],
        "product": ["Bread"],
        "quantity": [1],
        "price": [1.20],
    })
    out = transform(df)
    assert list(out.columns) == REQUIRED_COLUMNS
    assert float(out["total"].iloc[0]) == pytest.approx(1.20)


def test_known_products_have_categories():
    # Every product in the generator catalog must be mapped
    assert "Bread" in PRODUCT_CATEGORIES
    assert "Toilet Paper" in PRODUCT_CATEGORIES
    assert all(isinstance(v, str) and v for v in PRODUCT_CATEGORIES.values())


def test_generate_dataset(tmp_path):
    """The synthetic generator stays reproducible and schema-correct."""
    np.random.seed(0)  # ensure numpy is exercised the same way as CI
    from generate_data import generate_dataset

    out_file = tmp_path / "synthetic.csv"
    generate_dataset(output_path=str(out_file), n_rows=50, seed=42)
    df = pd.read_csv(out_file)
    assert len(df) == 50
    assert list(df.columns) == ["date", "product", "quantity", "price"]
