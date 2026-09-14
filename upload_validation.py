"""
Schema validation for uploaded sales CSVs.

The upload contract is intentionally strict: the file must match the
project schema (date, product, quantity, price) or it is rejected with a
specific error — no silent column guessing. Cleaning/revenue logic itself
is reused from etl.etl_main.transform.
"""

from __future__ import annotations

import io

import pandas as pd

REQUIRED_COLUMNS = ["date", "product", "quantity", "price"]
MAX_FILE_MB = 20


class UploadValidationError(ValueError):
    """Raised when an uploaded CSV fails schema or value validation."""


def read_csv_bytes(raw: bytes) -> pd.DataFrame:
    """Decode and parse an uploaded CSV; raises on empty/unreadable files."""
    if not raw:
        raise UploadValidationError("The uploaded file is empty. Please choose a CSV with data.")
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except UnicodeDecodeError as exc:
        raise UploadValidationError("The file is not readable as CSV/UTF-8 text.") from exc
    except pd.errors.ParserError as exc:
        raise UploadValidationError("The file could not be parsed as CSV. Check commas and line breaks.") from exc
    except Exception as exc:  # noqa: BLE001 - surfaced to the user
        raise UploadValidationError(f"Could not read the CSV file: {exc}") from exc

    if df.empty:
        raise UploadValidationError("The CSV has no data rows. Please upload a file with sales records.")
    return df


def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce the exact schema.

    - Column names are matched case-insensitively but the set must match
      the required columns exactly (extra/missing columns are rejected).
    - Returns a DataFrame with the canonical lowercase column names.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise UploadValidationError("The CSV has no data rows. Please upload a file with sales records.")

    incoming = [str(c).strip() for c in df.columns]
    incoming_lower = [c.lower() for c in incoming]
    required_set = set(REQUIRED_COLUMNS)
    incoming_set = {c.lower() for c in incoming_lower}

    missing = [c for c in REQUIRED_COLUMNS if c not in incoming_set]
    if missing:
        raise UploadValidationError(
            f"Missing required column(s): {', '.join(missing)}. "
            f"Expected columns: {', '.join(REQUIRED_COLUMNS)}."
        )

    extra = [c for c in incoming_lower if c not in required_set]
    if extra:
        raise UploadValidationError(
            f"Unexpected column(s): {', '.join(extra)}. "
            f"Expected exactly: {', '.join(REQUIRED_COLUMNS)}."
        )

    # Canonical names + original order preserved (date, product, quantity, price)
    out = df.copy()
    out.columns = incoming_lower
    return out[REQUIRED_COLUMNS]


def validate_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce value rules before ETL cleaning:

    - date must contain at least one parseable date and no fully invalid column
    - quantity and price must be numeric and non-negative
    Raises UploadValidationError with a specific message on failure.
    """
    df = df.copy()

    # Dates: at least one valid value required
    parsed = pd.to_datetime(df["date"], errors="coerce")
    valid_dates = parsed.notna().sum()
    if valid_dates == 0:
        raise UploadValidationError(
            "Column 'date' contains no valid dates. Expected format like 2025-01-15."
        )
    invalid_dates = len(df) - valid_dates
    if invalid_dates:
        raise UploadValidationError(
            f"Column 'date' has {invalid_dates} unparseable value(s). "
            "Expected a date format like 2025-01-15."
        )

    # Numeric columns: must convert cleanly, then be non-negative
    for col in ("quantity", "price"):
        as_num = pd.to_numeric(df[col], errors="coerce")
        bad_format = as_num.isna().sum()
        if bad_format:
            raise UploadValidationError(
                f"Column '{col}' must be numeric, but {bad_format} value(s) "
                "could not be converted to a number."
            )
        negatives = (as_num < 0).sum()
        if negatives:
            raise UploadValidationError(
                f"Column '{col}' must be non-negative, but {negatives} negative value(s) were found."
            )
        df[col] = as_num

    # Product: no missing values
    missing_products = df["product"].isna().sum()
    if missing_products:
        raise UploadValidationError(
            f"Column 'product' has {missing_products} missing value(s)."
        )
    return df


def validate_upload(raw: bytes) -> pd.DataFrame:
    """
    Full pipeline for an uploaded CSV: parse -> schema -> value checks.
    Returns a validated DataFrame with canonical columns (not yet cleaned
    by the ETL — that happens separately via etl.etl_main.transform).
    """
    if len(raw) > MAX_FILE_MB * 1024 * 1024:
        raise UploadValidationError(f"File is larger than {MAX_FILE_MB} MB.")
    df = read_csv_bytes(raw)
    df = validate_schema(df)
    df = validate_values(df)
    return df
