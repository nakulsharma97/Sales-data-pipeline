"""
SQL queries for the sales dashboard.

Every query is a SQLAlchemy text() clause. Filters are always passed as
bound parameters — never string-formatted — to prevent SQL injection.
All KPI/chart queries accept optional start_date / end_date / categories.
"""

from sqlalchemy import text


def _build(base_sql: str, tail_sql: str, start_date=None, end_date=None,
           categories=None, products=None, min_total=None, max_total=None):
    """
    Combine a base SELECT ... FROM sales_staging statement with optional
    WHERE filters (dates, categories, products) and a tail
    (GROUP BY / ORDER BY / LIMIT).

    Returns (text_query, params) ready for pd.read_sql or engine.execute.
    """
    conditions, params = [], {}

    if start_date is not None:
        conditions.append("date >= :start_date")
        params["start_date"] = start_date
    if end_date is not None:
        conditions.append("date <= :end_date")
        params["end_date"] = end_date

    if categories:
        params.update({f"cat_{i}": c for i, c in enumerate(categories)})
        placeholders = ", ".join(f":cat_{i}" for i in range(len(categories)))
        conditions.append(f"category IN ({placeholders})")

    if products:
        params.update({f"prod_{i}": p for i, p in enumerate(products)})
        placeholders = ", ".join(f":prod_{i}" for i in range(len(products)))
        conditions.append(f"product IN ({placeholders})")

    if min_total is not None:
        conditions.append("total >= :min_total")
        params["min_total"] = min_total
    if max_total is not None:
        conditions.append("total <= :max_total")
        params["max_total"] = max_total

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    return text(base_sql + where + tail_sql), params


def get_total_revenue(start_date=None, end_date=None, categories=None,
                      products=None, min_total=None, max_total=None):
    return _build(
        "SELECT COALESCE(SUM(total), 0) AS total_revenue FROM sales_staging",
        "",
        start_date, end_date, categories, products, min_total, max_total,
    )


def get_total_orders(start_date=None, end_date=None, categories=None,
                     products=None, min_total=None, max_total=None):
    return _build(
        "SELECT COUNT(*) AS total_orders FROM sales_staging",
        "",
        start_date, end_date, categories, products, min_total, max_total,
    )


def get_total_products(start_date=None, end_date=None, categories=None,
                       products=None, min_total=None, max_total=None):
    return _build(
        "SELECT COUNT(DISTINCT product) AS total_products FROM sales_staging",
        "",
        start_date, end_date, categories, products, min_total, max_total,
    )


def get_avg_order_value(start_date=None, end_date=None, categories=None,
                        products=None, min_total=None, max_total=None):
    return _build(
        "SELECT COALESCE(AVG(total), 0) AS avg_order_value FROM sales_staging",
        "",
        start_date, end_date, categories, products, min_total, max_total,
    )


def get_kpis(start_date=None, end_date=None, categories=None,
             products=None, min_total=None, max_total=None):
    """All five KPI figures in one round-trip (used by the demo dashboard)."""
    return _build(
        "SELECT COALESCE(SUM(total), 0) AS total_revenue, COUNT(*) AS total_orders, "
        "COUNT(DISTINCT product) AS total_products, "
        "COALESCE(AVG(total), 0) AS avg_order_value, "
        "COALESCE(SUM(quantity), 0) AS total_units FROM sales_staging",
        "",
        start_date, end_date, categories, products, min_total, max_total,
    )


def get_revenue_by_month(start_date=None, end_date=None, categories=None,
                         products=None, min_total=None, max_total=None):
    """Month-level revenue trend — powers the monthly comparison chart.

    Uses SUBSTR(CAST(date AS CHAR), 1, 7) instead of MySQL's DATE_FORMAT so
    the same SQL runs on MySQL (production) and SQLite (the test suite)."""
    return _build(
        "SELECT SUBSTR(CAST(date AS CHAR), 1, 7) AS month, "
        "SUM(total) AS monthly_revenue FROM sales_staging",
        " GROUP BY SUBSTR(CAST(date AS CHAR), 1, 7) ORDER BY month",
        start_date, end_date, categories, products, min_total, max_total,
    )


def get_sales_by_product(start_date=None, end_date=None, categories=None,
                         products=None, min_total=None, max_total=None):
    return _build(
        "SELECT product, SUM(total) AS revenue, SUM(quantity) AS units FROM sales_staging",
        " GROUP BY product ORDER BY revenue DESC",
        start_date, end_date, categories, products, min_total, max_total,
    )


def get_sales_by_category(start_date=None, end_date=None, categories=None,
                          products=None, min_total=None, max_total=None):
    return _build(
        "SELECT category, SUM(total) AS revenue, SUM(quantity) AS units FROM sales_staging",
        " GROUP BY category ORDER BY revenue DESC",
        start_date, end_date, categories, products, min_total, max_total,
    )


def get_revenue_by_date(start_date=None, end_date=None, categories=None,
                        products=None, min_total=None, max_total=None):
    return _build(
        "SELECT DATE(date) AS sale_date, SUM(total) AS daily_revenue FROM sales_staging",
        " GROUP BY DATE(date) ORDER BY sale_date",
        start_date, end_date, categories, products, min_total, max_total,
    )


def get_top_selling_products(limit=10, start_date=None, end_date=None,
                             categories=None, products=None,
                             min_total=None, max_total=None):
    return _build(
        "SELECT product, SUM(total) AS revenue, SUM(quantity) AS total_quantity FROM sales_staging",
        f" GROUP BY product ORDER BY revenue DESC LIMIT {int(limit)}",
        start_date, end_date, categories, products, min_total, max_total,
    )


def get_distinct_categories():
    """Category list for the sidebar filter."""
    return text("SELECT DISTINCT category FROM sales_staging ORDER BY category"), {}


def get_products_in_categories(categories=None):
    """Product list scoped to the selected categories (for the product filter)."""
    if not categories:
        return text("SELECT DISTINCT product FROM sales_staging ORDER BY product"), {}
    params = {f"cat_{i}": c for i, c in enumerate(categories)}
    placeholders = ", ".join(f":cat_{i}" for i in range(len(categories)))
    sql = text(
        f"SELECT DISTINCT product FROM sales_staging "
        f"WHERE category IN ({placeholders}) ORDER BY product"
    )
    return sql, params


def get_sales_data_filtered(start_date=None, end_date=None, categories=None,
                            products=None, min_total=None, max_total=None,
                            limit=None):
    """Row-level table for the dashboard, with the shared filters applied.
    `limit` caps rows fetched for on-screen display — pass None for the
    unlimited CSV-export query."""
    tail = " ORDER BY date DESC"
    if limit is not None:
        tail += f" LIMIT {int(limit)}"
    return _build(
        "SELECT date, product, category, quantity, price, total FROM sales_staging",
        tail,
        start_date, end_date, categories, products, min_total, max_total,
    )
