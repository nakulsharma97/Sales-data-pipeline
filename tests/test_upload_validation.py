"""
Tests for uploaded-CSV validation: schema enforcement, value rules and
the full validate -> transform path.
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import upload_validation as uv  # noqa: E402
from etl.etl_main import transform as etl_transform  # noqa: E402


def csv_bytes(text: str) -> bytes:
    return text.encode("utf-8")


VALID_CSV = (
    "date,product,quantity,price\n"
    "2025-01-01,Coffee,2,3.50\n"
    "2025-01-02,Bread,1,1.20\n"
)


# ------------------------------------------------------------------ schema
def test_valid_schema_passes():
    df = uv.validate_upload(csv_bytes(VALID_CSV))
    assert list(df.columns) == ["date", "product", "quantity", "price"]
    assert len(df) == 2


def test_case_insensitive_columns_accepted():
    raw = csv_bytes("DATE,PRODUCT,QUANTITY,PRICE\n2025-01-01,Tea,1,2.00\n")
    df = uv.validate_upload(raw)
    assert list(df.columns) == ["date", "product", "quantity", "price"]


def test_missing_column_rejected_with_specific_message():
    raw = csv_bytes("date,product,quantity\n2025-01-01,Tea,1\n")
    with pytest.raises(uv.UploadValidationError) as e:
        uv.validate_upload(raw)
    assert "price" in str(e.value)
    assert "date, product, quantity, price" in str(e.value)


def test_extra_column_rejected():
    raw = csv_bytes("date,product,quantity,price,region\n2025-01-01,Tea,1,2.00,south\n")
    with pytest.raises(uv.UploadValidationError) as e:
        uv.validate_upload(raw)
    assert "region" in str(e.value)


def test_empty_file_rejected():
    with pytest.raises(uv.UploadValidationError) as e:
        uv.validate_upload(b"")
    assert "empty" in str(e.value).lower()


def test_header_only_file_rejected():
    with pytest.raises(uv.UploadValidationError):
        uv.validate_upload(csv_bytes("date,product,quantity,price\n"))


def test_not_a_csv_rejected():
    with pytest.raises(uv.UploadValidationError):
        uv.validate_upload(b"\x00\x01\x02binary-garbage")


# ------------------------------------------------------------------ values
def test_non_numeric_quantity_rejected():
    raw = csv_bytes("date,product,quantity,price\n2025-01-01,Tea,two,2.00\n")
    with pytest.raises(uv.UploadValidationError) as e:
        uv.validate_upload(raw)
    assert "quantity" in str(e.value)


def test_negative_price_rejected():
    raw = csv_bytes("date,product,quantity,price\n2025-01-01,Tea,1,-2.00\n")
    with pytest.raises(uv.UploadValidationError) as e:
        uv.validate_upload(raw)
    assert "negative" in str(e.value)


def test_unparseable_date_rejected():
    raw = csv_bytes("date,product,quantity,price\nnotadate,Tea,1,2.00\n")
    with pytest.raises(uv.UploadValidationError) as e:
        uv.validate_upload(raw)
    assert "date" in str(e.value)


def test_missing_product_rejected():
    raw = csv_bytes("date,product,quantity,price\n2025-01-01,,1,2.00\n")
    with pytest.raises(uv.UploadValidationError) as e:
        uv.validate_upload(raw)
    assert "product" in str(e.value)


# ------------------------------------------------- full pipeline behaviour
def test_validated_upload_flows_through_etl_transform():
    df = uv.validate_upload(csv_bytes(VALID_CSV))
    cleaned = etl_transform(df)
    assert "total" in cleaned.columns
    assert cleaned["total"].iloc[0] == pytest.approx(7.00)   # 2 * 3.50
    assert cleaned["category"].iloc[0] == "Beverages"        # Coffee


def test_transform_still_cleans_dirty_but_schema_valid_rows():
    """Validation only rejects structural errors; ETL cleaning stays in charge."""
    raw = csv_bytes(
        "date,product,quantity,price\n"
        "2025-01-01,Tea,2,2.00\n"
        "2025-01-01,Tea,2,2.00\n"   # duplicate row -> removed by transform
    )
    df = uv.validate_upload(raw)
    cleaned = etl_transform(df)
    assert len(cleaned) == 1


def test_real_dataset_still_validates():
    """The project's own data/input.csv must pass the upload contract."""
    with open("data/input.csv", "rb") as f:
        df = uv.validate_upload(f.read())
    assert len(df) == 4000
