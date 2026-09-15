"""
Dashboard rendering shared by demo (MySQL) and uploaded (in-memory) modes.

Demo mode pulls data through queries/sales_queries.py with sidebar filters.
Uploaded mode computes the same views in pandas from session_state.uploaded_df.
"""

import math
import textwrap
from contextlib import contextmanager
from datetime import datetime, time

import pandas as pd
import streamlit as st

from queries import sales_queries as sq
from utils.format import count, money
from views import charts
from views.upload_view import render_uploaded_complete

CORAL = "#F55036"
CORAL_SOFT = "#FDE7DD"
NAVY = "#111827"
INK = "#1F2937"
SLATE = "#6B7280"
MUTED = "#9CA3AF"
LINE = "#F3ECE7"


def _html(markup: str) -> None:
    st.markdown(textwrap.dedent(markup).strip(), unsafe_allow_html=True)


def _demo_page_css() -> None:
    """Page-scoped CSS for the demo dashboard (landing/upload keep their own)."""
    _html(
        f"""
        <style>
            /* header stays in the layout (transparent, click-through) so the
               sidebar expand-arrow survives collapsing the filters */
            [data-testid="stHeader"] {{
                background: transparent !important; height: 1.5rem !important;
                pointer-events: none;
            }}
            [data-testid="stHeader"] button {{ pointer-events: auto; }}
            .block-container {{
                padding: 0.3rem 1.5rem 2rem 1.5rem !important;
                max-width: 100% !important;
            }}
            .stApp {{
                background:
                    radial-gradient(46rem 30rem at 100% 0%, #FCE9DE 0%, rgba(252,233,222,0) 60%),
                    #FFFDFA;
            }}
            /* ---- compact sidebar: rounded white filter card ---- */
            [data-testid="stSidebar"] {{
                background: #FFFFFF !important;
                border: 1px solid {LINE} !important;
                border-radius: 16px !important;
                margin: 0.45rem !important;
                box-shadow: 0 6px 18px rgba(31,41,55,0.05) !important;
            }}
            /* sidebar buttons (hide «, Reset Filters): peach pill style */
            [data-testid="stSidebar"] button {{
                background: #FFFFFF; color: {CORAL};
                border: 1px solid #F8CDBB; border-radius: 10px;
                font-weight: 700;
            }}
            [data-testid="stSidebar"] button:hover {{
                border-color: {CORAL}; background: #FFF4EC;
                color: {CORAL};
            }}
            /* ---- compact filter toggle icons ----
               « sits in the sidebar header (hide); ☷ appears at the LEFT of
               the main header only while the panel is hidden (restore).
               Both are type="tertiary" buttons, so this CSS targets them
               alone — the full-width Reset Filters button is untouched. */
            [data-testid="stSidebar"] button[kind="tertiary"],
            [data-testid="stMain"] button[kind="tertiary"] {{
                width: 2.35rem !important; min-width: 2.35rem !important;
                height: 2.35rem !important; padding: 0 !important;
                display: inline-flex !important; align-items: center !important;
                justify-content: center !important;
                background: #FFFFFF !important; color: {SLATE} !important;
                border: 1px solid {LINE} !important; border-radius: 10px !important;
                font-size: 1.02rem !important; font-weight: 700 !important;
                line-height: 1 !important;
                box-shadow: 0 2px 8px rgba(31,41,55,0.06);
            }}
            [data-testid="stSidebar"] button[kind="tertiary"]:hover,
            [data-testid="stMain"] button[kind="tertiary"]:hover {{
                color: {CORAL} !important; border-color: #F8CDBB !important;
                background: #FFF4EC !important;
            }}
            /* pin the « icon to the TOP-RIGHT corner of the sidebar card
               (absolute, like the reference mock — immune to Streamlit's
               column stacking inside narrow sidebars) */
            [data-testid="stSidebar"] {{ position: relative; }}
            [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(button[kind="tertiary"]) {{
                position: absolute !important;
                top: 1.05rem; right: 0.95rem; z-index: 20;
                margin: 0 !important;
            }}
            /* button labels never wrap/truncate (no "♻️ …" pills) */
            [data-testid="stMain"] button p {{ white-space: nowrap; }}
            @media (max-width: 1100px) {{
                [data-testid="stMain"] button {{
                    font-size: 0.72rem !important;
                    padding-left: 0.5rem !important;
                    padding-right: 0.5rem !important;
                }}
            }}
            .stDateInput label, .stMultiSelect label, .stSlider label {{
                font-size: 0.78rem !important; font-weight: 700 !important;
                color: {INK} !important; margin-bottom: 0.15rem !important;
            }}
            .stDateInput input, .stMultiSelect [data-baseweb="select"] > div {{
                border-radius: 9px !important; font-size: 0.85rem !important;
            }}
            /* ---- header + section cards ---- */
            .dbadge {{
                display:inline-block; border-radius:999px; background:{CORAL_SOFT};
                color:{CORAL}; font-size:0.64rem; font-weight:800;
                letter-spacing:1.3px; padding:0.32rem 0.9rem;
            }}
            h1.dtitle {{
                font-size:2.15rem; font-weight:800; color:{NAVY};
                letter-spacing:-0.8px; margin:0.55rem 0 0 0; line-height:1.12;
            }}
            h1.dtitle .accent {{ color:{CORAL}; }}
            .dsub {{ color:{SLATE}; font-size:0.95rem; margin-top:0.45rem; }}
            .range-chip {{
                display:inline-flex; align-items:center; gap:0.4rem; flex-wrap:nowrap;
                background:#FFFFFF; border:1px solid {LINE}; border-radius:999px;
                padding:0.34rem 0.95rem; font-size:0.8rem; font-weight:700; color:{INK};
                box-shadow:0 2px 8px rgba(31,41,55,0.05); white-space:nowrap;
            }}
            .range-chip .dot {{ color:{CORAL}; }}
            .kpi-card {{
                background:#FFFFFF; border:1px solid {LINE}; border-radius:16px;
                padding:1.05rem 1.2rem; height:100%;
                box-shadow:0 8px 22px rgba(31,41,55,0.06);
                transition: transform 0.15s ease, box-shadow 0.15s ease;
            }}
            .kpi-card:hover {{
                transform: translateY(-3px);
                box-shadow:0 14px 30px rgba(245,80,54,0.14);
                border-color:#F8CDBB;
            }}
            /* Equal-height, wrapping KPI row: CSS grid gives every card the
               same height on desktop and reflows 2-up on small screens. */
            .grid-kpis {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(175px, 1fr));
                gap: 0.85rem;
                margin: 0.35rem 0 0.25rem 0;
            }}
            .filters-chip {{
                display:inline-flex; align-items:center; gap:0.4rem;
                background:{CORAL_SOFT}; color:{CORAL};
                border-radius:999px; padding:0.28rem 0.8rem;
                font-size:0.75rem; font-weight:700; white-space:nowrap;
            }}
            /* ---- unified chart/panel cards ----
               Each card is a real st.container() block: Streamlit keeps the
               header + chart inside one DOM wrapper, so styling that wrapper
               produces true cards (the old open/close-markdown approach
               created phantom empty divs and let charts float outside). */
            [data-testid="stVerticalBlockBorderWrap"]:has(.chead),
            [data-testid="stVerticalBlockBorderWrap"]:has(.phead) {{
                background:#FFFFFF; border:1px solid {LINE}; border-radius:16px;
                padding:0.95rem 1.05rem 0.75rem 1.05rem;
                box-shadow:0 8px 22px rgba(31,41,55,0.06);
            }}
            /* Card headers — plain text styles (the card surface is the
               container wrapper above) */
            .chead {{
                font-size:1.02rem; font-weight:800; color:{INK};
                padding:0.1rem 0.15rem 0 0.15rem;
            }}
            .csub {{
                font-size:0.78rem; color:{SLATE};
                padding:0 0.15rem; margin-top:0.12rem; margin-bottom:0.4rem;
            }}
            .phead {{
                font-size:1.02rem; font-weight:800; color:{INK};
                margin-bottom:0.4rem;
            }}
            .kpi-card .krow {{ display:flex; align-items:center; gap:0.55rem; }}
            .kpi-card .kico {{
                width:2.25rem; height:2.25rem; border-radius:11px; flex-shrink:0;
                background:{CORAL_SOFT}; display:flex; align-items:center;
                justify-content:center; font-size:1.02rem;
            }}
            .kpi-card .klabel {{ font-size:0.8rem; font-weight:700; color:{SLATE}; }}
            .kpi-card .kvalue {{
                font-size:1.72rem; font-weight:800; color:{NAVY};
                letter-spacing:-0.6px; margin-top:0.55rem;
            }}
            /* KPI row: equal-height cards via flex stretch on the real
               st.columns row; Streamlit re-flows columns automatically on
               narrow screens. */
            [data-testid="stHorizontalBlock"]:has(.kpi-card) {{
                align-items: stretch !important;
                flex-wrap: wrap !important;
            }}
            [data-testid="stHorizontalBlock"]:has(.kpi-card) > [data-testid="stColumn"] {{
                min-width: 172px;
            }}
            /* no floating plotly toolbar — it overlapped the top bars; the
               charts are sized to fit, so pan/zoom buttons add nothing */
            .js-plotly-plot .plotly .modebar-container {{
                display: none !important;
            }}
        </style>
        """,
    )


# ---------------------------------------------------------------- shared UI
def render_kpi_cards(kpis: list):
    """Row of premium KPI cards: (icon, label, value) tuples — real values only.
    Equal heights + wrapping come from CSS on the st.columns row."""
    cols = st.columns(len(kpis), gap="small")
    for col, (icon, label, value) in zip(cols, kpis):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="krow"><span class="kico">{icon}</span>
                        <span class="klabel">{label}</span></div>
                    <div class="kvalue">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _card_head(title: str, subtitle: str | None) -> None:
    html = f'<div class="chead">{title}</div>'
    if subtitle:
        html += f'<div class="csub">{subtitle}</div>'
    st.markdown(html, unsafe_allow_html=True)


@contextmanager
def chart_card(title: str, subtitle: str):
    """A real card: st.container(border=True) renders ONE DOM block that
    genuinely contains the header and the chart (markdown open/close divs
    can't do this — Streamlit closes raw HTML tags immediately, which made
    the old open/close-card divs phantom-empty)."""
    with st.container(border=True):
        _card_head(title, subtitle)
        yield


@contextmanager
def panel_card(title: str):
    """Same card surface for the top-sellers / data panels."""
    with st.container(border=True):
        st.markdown(f'<div class="phead">{title}</div>',
                    unsafe_allow_html=True)
        yield


# ------------------------------------------------- shared filter panel
FILTER_KEYS = ("demo_start", "demo_end", "demo_cats", "demo_prods",
               "demo_price")
UP_KEYS = ("up_start", "up_end", "up_cats", "up_prods", "up_price")


def _toggle_filters():
    """Hide/show the filter panel, preserving every widget value.

    Conditionally-rendered widgets forget their state when they disappear,
    so on HIDE the current values are snapshotted into session state; on
    SHOW they are written back into the widgets' keys before rerendering.
    """
    if st.session_state.get("filters_visible"):
        for key in FILTER_KEYS + UP_KEYS:
            if key in st.session_state:
                st.session_state[f"saved::{key}"] = st.session_state[key]
        st.session_state.filters_visible = False
    else:
        st.session_state.filters_visible = True
        for key in FILTER_KEYS + UP_KEYS:
            saved = st.session_state.pop(f"saved::{key}", None)
            if saved is not None:
                st.session_state[key] = saved
    st.rerun()


def _filters_header():
    """Sidebar panel heading; the « hide icon sits in the adjacent column."""
    st.markdown(
        f"""
        <div style="font-weight:800; color:{NAVY}; font-size:1.05rem;
                    display:flex; align-items:center; min-height:2.35rem;">
            ⚙️ Filters
        </div>
        """,
        unsafe_allow_html=True,
    )


def _reset(keys):
    for key in keys:
        st.session_state.pop(key, None)
        st.session_state.pop(f"saved::{key}", None)
    st.rerun()


def _demo_filters_sidebar(min_date, max_date, max_total, products):
    """Demo-mode filter panel: Date Range · Product · Category · Price Range.
    Returns the filter values; the hide («) button sits in the panel header."""
    hbtn_l, hbtn_r = st.sidebar.columns([3.2, 1], gap="small",
                                        vertical_alignment="center")
    with hbtn_l:
        _filters_header()
    with hbtn_r:
        st.sidebar.button("«", type="tertiary", on_click=_toggle_filters,
                          help="Hide filters")
    st.sidebar.caption("Narrow the demo data by date, product, category or price.")

    start_date = st.sidebar.date_input(
        "Start date", value=min_date, min_value=min_date, max_value=max_date,
        key="demo_start",
    )
    end_date = st.sidebar.date_input(
        "End date", value=max_date, min_value=min_date, max_value=max_date,
        key="demo_end",
    )
    if start_date > end_date:
        st.sidebar.warning("Start date is after end date — using the full range.")
        start_date, end_date = min_date, max_date

    selected_products = st.sidebar.multiselect(
        "Product", options=products, placeholder="All products",
        key="demo_prods",
    )
    from etl.product_catalog import CATEGORIES

    selected_categories = st.sidebar.multiselect(
        "Category", options=CATEGORIES, placeholder="All categories",
        key="demo_cats",
    )
    p_lo = st.sidebar.slider(
        "Price Range", min_value=0.0, max_value=float(max_total), step=0.5,
        value=(0.0, float(max_total)), format="$%.2f", key="demo_price",
    )
    st.sidebar.button("♻️ Reset Filters", on_click=_reset, args=(FILTER_KEYS,),
                      use_container_width=True)
    price_lo, price_hi = p_lo
    return start_date, end_date, selected_products, selected_categories, price_lo, price_hi


def _uploaded_filters_sidebar(d_min_all, d_max_all, df, price_max):
    """Uploaded-data filter panel — same design, pandas filtering."""
    hbtn_l, hbtn_r = st.sidebar.columns([3.2, 1], gap="small",
                                        vertical_alignment="center")
    with hbtn_l:
        _filters_header()
    with hbtn_r:
        st.sidebar.button("«", type="tertiary", on_click=_toggle_filters,
                          help="Hide filters")
    st.sidebar.caption("Narrow YOUR data by date, product, category or price.")

    start_date = st.sidebar.date_input(
        "Start date", value=d_min_all, min_value=d_min_all, max_value=d_max_all,
        key="up_start",
    )
    end_date = st.sidebar.date_input(
        "End date", value=d_max_all, min_value=d_min_all, max_value=d_max_all,
        key="up_end",
    )
    if start_date > end_date:
        st.sidebar.warning("Start date is after end date — using the full range.")
        start_date, end_date = d_min_all, d_max_all

    selected_products = st.sidebar.multiselect(
        "Product", options=sorted(df["product"].dropna().unique().tolist()),
        placeholder="All products", key="up_prods",
    )
    selected_categories = st.sidebar.multiselect(
        "Category", options=sorted(df["category"].dropna().unique().tolist()),
        placeholder="All categories", key="up_cats",
    )
    price_full = (0.0, price_max)
    p_lo = st.sidebar.slider(
        "Price Range", min_value=0.0, max_value=price_max, step=0.25,
        value=(0.0, price_max), format="$%.2f", key="up_price",
    )
    st.sidebar.button("♻️ Reset Filters", on_click=_reset, args=(UP_KEYS,),
                      use_container_width=True)
    return start_date, end_date, selected_products, selected_categories, p_lo


def render_dashboard_sections(by_product, by_category, by_date, by_month, top,
                              details, source, max_table_rows=None):
    """Premium charts, top-sellers, table and download — identical for both modes.

    `by_month` powers the month-vs-month revenue comparison; `max_table_rows`
    optionally caps the rendered table (the CSV download always has all rows)."""
    chart_l, chart_r = st.columns([3, 2], gap="small")

    with chart_l:
        with chart_card("Sales by Product",
                        "Actual revenue generated by each product"):
            if by_product.empty:
                st.info("No data for the selected filters.")
            else:
                # Height scales with the product count so every label keeps
                # ~28px of row space — nothing clips, never excessive scroll.
                n_products = max(1, len(by_product))
                bar_height = min(560, max(340, 96 + n_products * 24))
                fig = charts.bar_chart(
                    by_product, "product", "revenue", "",
                    horizontal=True, height=bar_height, hide_colorbar=True,
                )
                st.plotly_chart(fig, use_container_width=True,
                                config={"displayModeBar": False})

    with chart_r:
        with chart_card("Sales by Category",
                        "Revenue share across product categories"):
            if by_category.empty:
                st.info("No data for the selected filters.")
            else:
                fig = charts.category_chart(by_category, height=430,
                                            showlegend=True,
                                            textposition="outside")
                st.plotly_chart(fig, use_container_width=True,
                                config={"displayModeBar": False})

    with chart_card("Revenue by Date", "Daily revenue across the selected period"):
        if by_date.empty:
            st.info("No data for the selected filters.")
        else:
            by_date = by_date.copy()
            by_date["sale_date"] = pd.to_datetime(by_date["sale_date"])
            fig = charts.line_chart(by_date, "sale_date", "daily_revenue", "")
            fig.update_layout(height=360, autosize=True)
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False})

    with chart_card("Monthly Revenue Comparison",
                    "Month-vs-month totals to spot growth and seasonality"):
        if by_month.empty:
            st.info("No data for the selected filters.")
        else:
            month = by_month.copy()
            month["month"] = month["month"].astype(str)
            fig = charts.bar_chart(month, "month", "monthly_revenue", "",
                                   horizontal=False, height=340,
                                   hide_colorbar=True)
            fig.update_layout(xaxis=dict(type="category"), autosize=True)
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False})

    panel_l, panel_r = st.columns([2, 3], gap="small")

    with panel_l:
        with panel_card("🏆 Top-Selling Products"):
            if top.empty:
                st.info("No data for the selected filters.")
            else:
                top = top.copy()
                top["revenue"] = top["revenue"].map(money)
                if "total_quantity" in top.columns:
                    top["total_quantity"] = top["total_quantity"].map(count)
                    top = top.rename(columns={"product": "Product", "revenue": "Revenue",
                                              "total_quantity": "Units Sold"})
                else:
                    top = top.rename(columns={"product": "Product", "revenue": "Revenue"})
                st.dataframe(top, use_container_width=True, hide_index=True)

    with panel_r:
        with panel_card("📋 Sales Data"):
            if details.empty:
                st.info("No sales match the selected filters. Try widening the date range.")
            else:
                table = details.copy()
                if max_table_rows is not None:
                    table = table.head(max_table_rows)
                table = table.copy()
                table["date"] = pd.to_datetime(table["date"]).dt.strftime("%Y-%m-%d")
                table["price"] = table["price"].map(money)
                table["total"] = table["total"].map(money)
                table = table.rename(columns={
                    "date": "Date", "product": "Product", "category": "Category",
                    "quantity": "Quantity", "price": "Unit Price", "total": "Total",
                })
                if max_table_rows is not None and len(details) > max_table_rows:
                    st.caption(
                        f"Showing {max_table_rows:,} of {len(details):,} rows — "
                        "download the CSV for the full dataset."
                    )
                st.dataframe(table, use_container_width=True, height=420)
                csv_bytes = details.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download cleaned CSV", data=csv_bytes,
                                   file_name=f"cleaned_sales_{source}.csv", mime="text/csv")


# ------------------------------------------------------------- demo (MySQL)
@st.cache_resource(show_spinner=False)
def _cached_engine():
    """One engine per app lifetime — pool_pre_ping keeps it healthy."""
    from database.connection import get_mysql_engine

    return get_mysql_engine()


@st.cache_data(ttl=300, show_spinner=False)
def _demo_meta():
    """Date bounds + product list (rarely changes) — cached 5 min."""
    engine = _cached_engine()
    with engine.connect() as conn:
        bounds = pd.read_sql(
            "SELECT MIN(date) AS min_date, MAX(date) AS max_date, "
            "MAX(total) AS max_total FROM sales_staging",
            con=conn,
        )
        products_df = pd.read_sql(
            "SELECT DISTINCT product FROM sales_staging ORDER BY product", con=conn
        )
    return bounds, products_df


def _read_sql(query_pair, conn):
    """pd.read_sql for a (sql, params) pair from the query layer."""
    sql, params = query_pair
    return pd.read_sql(sql, params=params, con=conn)


@st.cache_data(ttl=300, show_spinner=False)
def _demo_data(start_date, end_date, categories, products,
               min_total=None, max_total=None):
    """All dashboard data for a filter combo in ONE connection + ONE round-trip
    batch (the five KPIs share a single query). Cached 5 min, so re-applying
    a filter combination you already viewed is instant."""
    engine = _cached_engine()
    cats = list(categories) if categories else None
    prods = list(products) if products else None
    with engine.connect() as conn:
        kpis = _read_sql(sq.get_kpis(start_date, end_date, cats, prods,
                                     min_total, max_total), conn)
        by_product = _read_sql(sq.get_sales_by_product(start_date, end_date, cats,
                                                       prods, min_total, max_total), conn)
        by_category = _read_sql(sq.get_sales_by_category(start_date, end_date, cats,
                                                         prods, min_total, max_total), conn)
        by_date = _read_sql(sq.get_revenue_by_date(start_date, end_date, cats,
                                                   prods, min_total, max_total), conn)
        by_month = _read_sql(sq.get_revenue_by_month(start_date, end_date, cats,
                                                     prods, min_total, max_total), conn)
        top = _read_sql(sq.get_top_selling_products(10, start_date, end_date, cats,
                                                    prods, min_total, max_total), conn)
        details = _read_sql(sq.get_sales_data_filtered(start_date, end_date, cats,
                                                       prods, min_total, max_total), conn)
    return kpis, by_product, by_category, by_date, by_month, top, details


def render_demo_dashboard():
    """Demo dataset dashboard — premium layout, real MySQL data only."""
    _demo_page_css()

    try:
        bounds, products_df = _demo_meta()
    except ConnectionError as exc:
        st.error("## ⚠️ Cannot connect to MySQL")
        st.markdown(
            "Create `.env` from `.env.example`, run `python etl/etl_main.py`, "
            "then restart the app."
        )
        st.caption(str(exc))
        return

    # Reachable DB but no data yet (ETL not run) — guide instead of crashing
    if bounds.empty or pd.isna(bounds["min_date"].iloc[0]):
        st.warning(
            "📭 The `sales_staging` table is empty. Run `python etl/etl_main.py` "
            "to load the demo dataset, then refresh this page."
        )
        return

    min_date = pd.to_datetime(bounds["min_date"].iloc[0]).date()
    max_date = pd.to_datetime(bounds["max_date"].iloc[0]).date()

    max_total = float(bounds["max_total"].iloc[0])
    price_full = (0.0, max_total)

    if st.session_state.filters_visible:
        (start_date, end_date, selected_products,
         selected_categories, price_lo, price_hi) = _demo_filters_sidebar(
            min_date, max_date, max_total, products_df["product"].tolist(),
        )
    else:
        # Panel hidden — reuse the snapshotted filter values so hiding the
        # sidebar never changes what the dashboard shows.
        start_date = st.session_state.get("saved::demo_start", min_date)
        end_date = st.session_state.get("saved::demo_end", max_date)
        selected_products = st.session_state.get("saved::demo_prods", [])
        selected_categories = st.session_state.get("saved::demo_cats", [])
        price_lo, price_hi = st.session_state.get("saved::demo_price", price_full)

    # ---- build filter args (same query layer as before) ----
    f_start = datetime.combine(start_date, time.min)
    f_end = datetime.combine(end_date, time.max)
    f_cats = tuple(selected_categories)
    f_prods = tuple(selected_products)
    f_min_total = price_lo if price_lo > 0 else None
    f_max_total = price_hi if price_hi < max_total else None

    # ---- one fetch for everything (cached per filter combo) ----
    try:
        kpis, by_product, by_category, by_date, by_month, top, details = _demo_data(
            f_start, f_end, f_cats, f_prods, f_min_total, f_max_total
        )
    except (ConnectionError, Exception) as exc:  # noqa: BLE001
        st.error(f"Database error while loading the dashboard: {exc}")
        return

    # ---- header ----
    # Active-filter summary: visible even when the sidebar is collapsed,
    # so filters are never a mystery ("what data am I looking at?").
    filter_bits = []
    if f_cats:
        filter_bits.append(f"{len(f_cats)} categor{'y' if len(f_cats)==1 else 'ies'}")
    if f_prods:
        filter_bits.append(f"{len(f_prods)} product{'s' if len(f_prods)>1 else ''}")

    # Header: two columns — left (badge + heading + subtitle),
    # right (restore icon · date range · Reset · Upload CSV).
    tl_col, _tl_spacer = st.columns([1, 5])
    with tl_col:
        st.button(
            "☷ Show Filters" if not st.session_state.get("filters_visible", True)
            else "☰ Hide Filters",
            on_click=_toggle_filters,
        )

    header_l, header_r = st.columns([2.3, 1], vertical_alignment="center")
    with header_l:
        st.markdown(
            f"""
            <div>
                <span class="dbadge">DEMO DATASET</span>
                <h1 class="dtitle">Sales trends, <span class="accent">real insights</span></h1>
                <div class="dsub">Explore sales trends and discover insights using our
                sample retail sales data.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with header_r:
        chips = (
            f'<span class="range-chip"><span class="dot">📅</span> '
            f'{start_date.strftime("%b %d, %Y")} → {end_date.strftime("%b %d, %Y")}</span>'
        )
        if filter_bits:
            chips += (
                '<span class="filters-chip">🔎 Active: '
                + ", ".join(filter_bits) + '</span>'
            )
        chip_row = (
            '<div style="display:flex; gap:0.45rem; justify-content:flex-end;">'
            f"{chips}</div>"
        )
        st.markdown(chip_row, unsafe_allow_html=True)
        up1, up2 = st.columns(2, gap="small")
        with up1:
            if st.button("♻️ Reset", use_container_width=True, key="hdr_reset"):
                _reset(FILTER_KEYS)
        with up2:
            if st.button("⬆️ Upload CSV", type="primary", use_container_width=True,
                         key="hdr_upload"):
                st.session_state.page = "upload"
                st.query_params.update({"page": "upload"})
                st.rerun()

    # ---- KPI cards (real values from MySQL — single combined query) ----
    if kpis.empty:
        st.error("No KPI data returned for the selected filters.")
        return
    kpis_row = [
        ("💰", "Total Revenue", money(kpis["total_revenue"].iloc[0])),
        ("🧾", "Total Orders", count(kpis["total_orders"].iloc[0])),
        ("📦", "Total Products", count(kpis["total_products"].iloc[0])),
        ("🧮", "Avg Order Value", money(kpis["avg_order_value"].iloc[0])),
        ("🔢", "Units Sold", count(kpis["total_units"].iloc[0])),
    ]
    render_kpi_cards(kpis_row)

    # Cap the rendered table at 500 rows for instant reruns; the CSV download
    # still contains the FULL filtered dataset.
    render_dashboard_sections(by_product, by_category, by_date, by_month, top,
                              details, source="demo", max_table_rows=500)


# -------------------------------------------------------- uploaded (memory)
def render_uploaded_dashboard():
    """Uploaded-data dashboard — same premium design system as the demo,
    with sidebar filters (date range, category, product) applied in pandas.
    Nothing leaves memory: filtering happens client-side on the session frame."""
    _demo_page_css()
    render_uploaded_complete()

    try:
        df: pd.DataFrame = st.session_state["uploaded_df"]
    except KeyError:
        st.warning("📭 No uploaded data found. Please upload a CSV first.")
        if st.button("⬆️ Go to Upload CSV"):
            st.session_state.page = "upload"
            st.query_params.update({"page": "upload"})
            st.rerun()
        return
    d_min_all = df["date"].min().date()
    d_max_all = df["date"].max().date()
    price_max = math.ceil(float(df["total"].max()) * 4) / 4.0
    price_full = (0.0, price_max)

    if st.session_state.filters_visible:
        (start_date, end_date, selected_products,
         selected_categories, price_range) = _uploaded_filters_sidebar(
            d_min_all, d_max_all, df, price_max,
        )
        price_lo, price_hi = price_range
    else:
        start_date = st.session_state.get("saved::up_start", d_min_all)
        end_date = st.session_state.get("saved::up_end", d_max_all)
        selected_products = st.session_state.get("saved::up_prods", [])
        selected_categories = st.session_state.get("saved::up_cats", [])
        price_lo, price_hi = st.session_state.get("saved::up_price", price_full)

    # ---- apply filters in pandas (in-memory only) ----
    mask = (df["date"] >= pd.Timestamp(start_date)) & (
        df["date"] <= pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    )
    if selected_categories:
        mask &= df["category"].isin(selected_categories)
    if selected_products:
        mask &= df["product"].isin(selected_products)
    if price_lo > 0:
        mask &= df["total"] >= price_lo
    if price_hi < price_max:
        mask &= df["total"] <= price_hi
    fdf = df.loc[mask]

    if fdf.empty:
        st.warning(
            "📭 No sales match the selected filters. Widen the date range or "
            "clear the category/product filters in the sidebar."
        )
        return

    with st.spinner("Crunching your data…"):
        total_revenue = float(fdf["total"].sum())
        total_orders = len(fdf)
        total_products = int(fdf["product"].nunique())
        total_units = int(fdf["quantity"].sum())
        aov = total_revenue / total_orders if total_orders else 0.0

        by_product = charts.compute_product_revenue(fdf)
        by_category = charts.compute_category_revenue(fdf)
        by_date = charts.compute_revenue_by_date(fdf)
        by_month = (
            fdf.assign(month=fdf["date"].dt.strftime("%Y-%m"))
            .groupby("month", as_index=False)["total"].sum()
            .rename(columns={"total": "monthly_revenue"})
            .sort_values("month")
        )
        top = by_product.head(10).copy()
        units = fdf.groupby("product", as_index=False)["quantity"].sum().rename(
            columns={"quantity": "total_quantity"}
        )
        top = top.merge(units, on="product", how="left")
        details = fdf.copy()

    # ---- header (YOUR DATA badge; chip shows the ACTIVE filtered range) ----
    header_l, header_r = st.columns([2.3, 1], vertical_alignment="center")
    with header_l:
        st.markdown(
            f"""
            <div>
                <span class="dbadge">YOUR DATA</span>
                <h1 class="dtitle">Your sales, <span class="accent">analyzed</span></h1>
                <div class="dsub">Cleaned and calculated in-memory from your upload —
                nothing is stored on our servers.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with header_r:
        chips = (
            '<span class="range-chip"><span class="dot">📅</span> '
            f'{start_date:%b %d, %Y} → {end_date:%b %d, %Y}</span>'
        )
        chip_row = (
            '<div style="display:flex; gap:0.45rem; justify-content:flex-end;">'
            f"{chips}</div>"
        )
        st.markdown(chip_row, unsafe_allow_html=True)
        up1, up2 = st.columns(2, gap="small")
        with up1:
            if st.button("♻️ Reset", use_container_width=True, key="hdr_reset_up"):
                _reset(UP_KEYS)
        with up2:
            if st.button("⬆️ Upload CSV", type="primary", use_container_width=True,
                         key="hdr_upload_up"):
                st.session_state.page = "upload"
                st.query_params.update({"page": "upload"})
                st.rerun()

    # ---- KPI cards (computed from the filtered upload) ----
    render_kpi_cards([
        ("💰", "Total Revenue", money(total_revenue)),
        ("🧾", "Total Orders", count(total_orders)),
        ("📦", "Total Products", count(total_products)),
        ("🧮", "Avg Order Value", money(aov)),
        ("🔢", "Units Sold", count(total_units)),
    ])

    render_dashboard_sections(by_product, by_category, by_date, by_month, top,
                              details, source="uploaded", max_table_rows=500)