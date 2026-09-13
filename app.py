"""
Sales Analytics Dashboard (Streamlit).

Reads processed data from MySQL (loaded by etl/etl_main.py) and renders
an interactive dashboard: KPIs, category/product charts, revenue trend,
top sellers and a filterable data table.

Run from the project root:
    streamlit run app.py
"""

import os
import sys
from datetime import datetime, time

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

# Allow "streamlit run app.py" from any working directory.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.connection import get_mysql_engine  # noqa: E402
from etl.product_catalog import CATEGORIES  # noqa: E402
from queries import sales_queries as sq  # noqa: E402
from utils.format import count, money  # noqa: E402

st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------------------------------------------------- Data layer
@st.cache_resource(show_spinner=False)
def get_engine():
    """Create and cache the MySQL engine (survives reruns)."""
    return get_mysql_engine()


@st.cache_data(ttl=300, show_spinner=False)
def run_query(sql_text: str, params) -> pd.DataFrame:
    """Execute one parameterized query and return the result as a DataFrame.

    The SQL is passed as a plain string (Streamlit caches on it safely).
    """
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql_text), con=conn, params=params)


def fetch(query_fn, *args, **kwargs) -> pd.DataFrame:
    """Run a query function; show a friendly error instead of crashing."""
    try:
        sql, params = query_fn(*args, **kwargs)
        return run_query(sql.text, params)
    except Exception as exc:  # noqa: BLE001 - surfaced in the UI
        st.error(f"Database error while running a query: {exc}")
        return pd.DataFrame()


# ------------------------------------------------------------------- Filters
@st.cache_data(ttl=600, show_spinner=False)
def load_filter_options() -> dict:
    """Date bounds + full category/product lists used by the sidebar."""
    with get_engine().connect() as conn:
        bounds = pd.read_sql(
            "SELECT MIN(date) AS min_date, MAX(date) AS max_date FROM sales_staging",
            con=conn,
        )
        products = pd.read_sql(
            "SELECT DISTINCT product FROM sales_staging ORDER BY product", con=conn
        )
    return {
        "min_date": bounds["min_date"].iloc[0],
        "max_date": bounds["max_date"].iloc[0],
        "products": products["product"].tolist(),
    }


def build_sidebar_filters(options: dict) -> dict:
    """Render sidebar widgets and return the active filter values."""
    st.sidebar.header("🔎 Filters")

    min_raw, max_raw = options["min_date"], options["max_date"]
    min_date = pd.to_datetime(min_raw).date()
    max_date = pd.to_datetime(max_raw).date()

    st.sidebar.subheader("Date range")
    start_date = st.sidebar.date_input("Start", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End", value=max_date, min_value=min_date, max_value=max_date)
    if start_date > end_date:
        st.sidebar.warning("Start date is after end date — using the full range instead.")
        start_date, end_date = min_date, max_date

    st.sidebar.subheader("Category")
    selected_categories = st.sidebar.multiselect(
        "Filter by category", options=CATEGORIES, placeholder="All categories"
    )

    st.sidebar.subheader("Product")
    selected_products = st.sidebar.multiselect(
        "Filter by product", options=options["products"], placeholder="All products"
    )

    st.sidebar.caption(
        "Tip: the product list comes from the whole dataset, so combine it "
        "with a category to narrow things down."
    )
    return {
        "start": datetime.combine(start_date, time.min),
        "end": datetime.combine(end_date, time.max),
        "categories": selected_categories or None,
        "products": selected_products or None,
    }


# -------------------------------------------------------------------- Charts
def bar_chart(df, x, y, title, color_scale="Blues", horizontal=False):
    orientation = "h" if horizontal else "v"
    fig = px.bar(
        df,
        x=y if horizontal else x,
        y=x if horizontal else y,
        orientation=orientation,
        title=title,
        labels={x: x.replace("_", " ").title(), y: y.replace("_", " ").title()},
        color=y,
        color_continuous_scale=color_scale,
    )
    fig.update_layout(showlegend=False, margin=dict(t=40, b=10))
    if horizontal:
        fig.update_yaxes(autorange="reversed")
    return fig


def line_chart(df, x, y, title):
    fig = px.line(
        df,
        x=x,
        y=y,
        title=title,
        markers=True,
        labels={x: "Date", y: "Revenue ($)"},
    )
    fig.update_traces(line_color="#1f77b4")
    fig.update_layout(hovermode="x unified", margin=dict(t=40, b=10))
    return fig


def category_chart(df):
    fig = px.pie(
        df,
        names="category",
        values="revenue",
        title="Revenue Share by Category",
        hole=0.45,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(t=40, b=10))
    return fig


# ---------------------------------------------------------------------- Page
def main() -> None:
    st.title("📊 Sales Analytics Dashboard")
    st.caption("Retail sales data · CSV → ETL (pandas) → MySQL → Streamlit")

    # ---- Connection gate -------------------------------------------------
    try:
        get_engine()
    except ConnectionError as exc:
        st.error("## ⚠️ Cannot connect to MySQL")
        st.markdown(
            """
            **To fix this:**
            1. Make sure your MySQL server is running.
            2. Create `.env` from `.env.example` (`cp .env.example .env`) and
               fill in your real credentials.
            3. Create the database: `mysql -u root -p < sql/schema.sql`
            4. Load the data: `python etl/etl_main.py`
            5. Restart this app: `streamlit run app.py`
            """
        )
        st.caption(str(exc))
        st.stop()

    # ---- Filter options --------------------------------------------------
    try:
        options = load_filter_options()
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not read filter options: {exc}")
        st.stop()

    if options["min_date"] is None or pd.isna(options["min_date"]):
        st.warning(
            "The `sales_staging` table is empty. Run the ETL first:  \n"
            "`python etl/etl_main.py`"
        )
        st.stop()

    filters = build_sidebar_filters(options)
    f_start, f_end = filters["start"], filters["end"]
    f_cats, f_prods = filters["categories"], filters["products"]

    # ---- KPI cards -------------------------------------------------------
    st.subheader("Key metrics")
    kpi_cols = st.columns(4)
    with st.spinner("Loading KPIs…"):
        kpis = [
            ("💰 Total Revenue", fetch(sq.get_total_revenue, f_start, f_end, f_cats, f_prods), "total_revenue", money),
            ("🧾 Total Orders", fetch(sq.get_total_orders, f_start, f_end, f_cats, f_prods), "total_orders", count),
            ("📦 Total Products", fetch(sq.get_total_products, f_start, f_end, f_cats, f_prods), "total_products", count),
            ("🧮 Avg Order Value", fetch(sq.get_avg_order_value, f_start, f_end, f_cats, f_prods), "avg_order_value", money),
        ]
    for col, (label, df, col_name, fmt) in zip(kpi_cols, kpis):
        value = fmt(df[col_name].iloc[0]) if not df.empty else "—"
        col.metric(label, value)

    st.divider()

    # ---- Charts ----------------------------------------------------------
    with st.spinner("Loading charts…"):
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.subheader("Sales by Product")
            by_product = fetch(sq.get_sales_by_product, f_start, f_end, f_cats, f_prods)
            if by_product.empty:
                st.info("No data for the selected filters.")
            else:
                fig = bar_chart(by_product, "product", "revenue", "Revenue by Product")
                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("Sales by Category")
            by_category = fetch(sq.get_sales_by_category, f_start, f_end, f_cats, f_prods)
            if by_category.empty:
                st.info("No data for the selected filters.")
            else:
                st.plotly_chart(category_chart(by_category), use_container_width=True)

        st.subheader("Revenue by Date")
        by_date = fetch(sq.get_revenue_by_date, f_start, f_end, f_cats, f_prods)
        if by_date.empty:
            st.info("No data for the selected filters.")
        else:
            by_date["sale_date"] = pd.to_datetime(by_date["sale_date"])
            st.plotly_chart(line_chart(by_date, "sale_date", "daily_revenue", "Daily Revenue Trend"), use_container_width=True)

        st.subheader("Top-Selling Products")
        top = fetch(sq.get_top_selling_products, 10, f_start, f_end, f_cats, f_prods)
        if top.empty:
            st.info("No data for the selected filters.")
        else:
            top["revenue"] = top["revenue"].map(money)
            top["total_quantity"] = top["total_quantity"].map(count)
            top = top.rename(columns={
                "product": "Product",
                "revenue": "Revenue",
                "total_quantity": "Units Sold",
            })
            st.dataframe(top, use_container_width=True, hide_index=True)

    st.divider()

    # ---- Detailed data table --------------------------------------------
    st.subheader("Sales Data")
    with st.spinner("Loading table…"):
        details = fetch(sq.get_sales_data_filtered, f_start, f_end, f_cats, f_prods)

    if details.empty:
        st.info("No sales match the selected filters. Try widening the date range.")
    else:
        table = details.copy()
        table["date"] = pd.to_datetime(table["date"]).dt.strftime("%Y-%m-%d")
        table["price"] = table["price"].map(money)
        table["total"] = table["total"].map(money)
        table = table.rename(columns={
            "date": "Date",
            "product": "Product",
            "category": "Category",
            "quantity": "Quantity",
            "price": "Unit Price",
            "total": "Total",
        })
        st.dataframe(table, use_container_width=True, height=400)

        csv_bytes = details.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download filtered data as CSV",
            data=csv_bytes,
            file_name="filtered_sales_data.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
