"""
ETL pipeline: CSV -> clean/transform -> MySQL (sales_staging table).

Stages:
    1. Extract   read the raw CSV sales data
    2. Transform clean, deduplicate, add category + revenue columns
    3. Load      create schema (idempotent) and append rows into MySQL

Run from the project root:
    python etl/etl_main.py                       # default file: data/input.csv
    python etl/etl_main.py --csv path/to/file.csv
    python etl/etl_main.py --truncate            # replace table contents
"""

import argparse
import os
import sys

import pandas as pd
from sqlalchemy import text

# Allow "python etl/etl_main.py" from the project root without installing.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import get_mysql_engine  # noqa: E402
from etl.product_catalog import PRODUCT_CATEGORIES  # noqa: E402

TABLE = "sales_staging"


# ---------------------------------------------------------------- 1. Extract
def extract(path: str = "data/input.csv") -> pd.DataFrame:
    """Read the raw sales CSV into a DataFrame."""
    df = pd.read_csv(path)
    return df


# -------------------------------------------------------------- 2. Transform
def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and enrich the raw data.

    - drop rows missing any required field
    - coerce quantity/price to numeric, drop invalid (NaN / negative) values
    - parse dates, drop unparseable ones
    - remove exact duplicate rows
    - map product -> category
    - calculate revenue: total = quantity * price
    """
    required = ["date", "product", "quantity", "price"]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Input CSV is missing required columns: {missing_cols}")

    df = df.copy()

    # Drop rows with missing required values
    before = len(df)
    df = df.dropna(subset=required)
    dropped_missing = before - len(df)

    # Coerce numerics; invalid strings become NaN and are dropped
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["quantity", "price"])

    # Business rules: quantities/prices must be positive
    df = df[(df["quantity"] > 0) & (df["price"] > 0)]

    # Parse dates; unparseable -> NaT -> dropped
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    # Normalize text fields
    df["product"] = df["product"].astype(str).str.strip()

    # Remove exact duplicates (same date, product, quantity, price)
    before = len(df)
    df = df.drop_duplicates(subset=["date", "product", "quantity", "price"])
    dropped_duplicates = before - len(df)

    # Category lookup; unknown products land in "Other"
    df["category"] = df["product"].map(PRODUCT_CATEGORIES).fillna("Other")

    # Revenue
    df["total"] = (df["quantity"] * df["price"]).round(2)

    # Final column order
    df = df[["date", "product", "category", "quantity", "price", "total"]]

    if dropped_missing or dropped_duplicates:
        print(
            f"Cleaning: dropped {dropped_missing} row(s) with missing/invalid values, "
            f"{dropped_duplicates} duplicate row(s)."
        )
    return df


# ------------------------------------------------------------------ 3. Load
def load(df: pd.DataFrame, mysql_uri: str | None = None, truncate: bool = False) -> int:
    """
    Create the schema if needed and append the DataFrame to MySQL.

    The CREATE TABLE is idempotent (IF NOT EXISTS), so the pipeline can be
    re-run safely. Use truncate=True to replace existing data.

    SQLite is also accepted (used for local testing / no-MySQL demos);
    it has no CREATE TABLE with indexes, so the table is created by pandas.

    Returns the number of rows written.
    """
    if not mysql_uri:
        mysql_uri = os.environ.get("MYSQL_URI")

    engine = get_mysql_engine(mysql_uri)
    is_sqlite = engine.dialect.name == "sqlite"

    if not is_sqlite:
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            sale_id     INT AUTO_INCREMENT PRIMARY KEY,
            date        DATETIME NOT NULL,
            product     VARCHAR(100) NOT NULL,
            category    VARCHAR(50)  NOT NULL,
            quantity    INT          NOT NULL,
            price       DECIMAL(10, 2) NOT NULL,
            total       DECIMAL(12, 2) NOT NULL,
            INDEX idx_date (date),
            INDEX idx_product (product),
            INDEX idx_category (category)
        )
        """
        with engine.begin() as conn:
            conn.execute(text(create_sql))
            if truncate:
                conn.execute(text(f"TRUNCATE TABLE {TABLE}"))

    if_exists = "replace" if (is_sqlite and truncate) else "append"
    df.to_sql(TABLE, con=engine, if_exists=if_exists, index=False)
    return len(df)


# ------------------------------------------------------------------- Runner
def run_pipeline(csv_path: str = "data/input.csv", truncate: bool = False) -> int:
    """Extract -> Transform -> Load, with progress output. Returns rows loaded."""
    print(f"[1/3] Extract: reading {csv_path}")
    df = extract(csv_path)
    print(f"      {len(df)} raw rows")

    print("[2/3] Transform: cleaning and enriching")
    df = transform(df)
    print(f"      {len(df)} clean rows")

    print("[3/3] Load: writing to MySQL")
    rows = load(df, truncate=truncate)
    print(f"      {rows} rows loaded into '{TABLE}'")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the sales ETL pipeline.")
    parser.add_argument("--csv", default="data/input.csv", help="Path to the input CSV")
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Empty the table before loading (full refresh)",
    )
    args = parser.parse_args()

    try:
        run_pipeline(args.csv, truncate=args.truncate)
        print("ETL finished successfully.")
    except Exception as exc:
        # Plain ASCII only: Windows consoles (cp1252) cannot print emoji
        print(f"ETL FAILED: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
