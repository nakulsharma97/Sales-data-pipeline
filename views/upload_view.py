"""
CSV upload screen — premium two-column layout.

Left: heading, drag-and-drop upload card, expected-columns info card.
Right: peach "From data to insights" card with a decorative (number-free)
SVG illustration and feature highlights.
Below: Recent Uploads with the real in-session history (no fake rows).

All validation flows through upload_validation + etl.etl_main.transform.
"""

import textwrap
from datetime import datetime

import streamlit as st

import upload_validation as uv
from etl.etl_main import transform as etl_transform

TEMPLATE_CSV = "date,product,quantity,price\n2025-01-15,Coffee,3,3.80\n2025-01-16,Bread,2,1.20\n"

CORAL = "#F55036"
CORAL_SOFT = "#FDE7DD"
INK = "#1F2937"
NAVY = "#111827"
SLATE = "#6B7280"
MUTED = "#9CA3AF"
LINE = "#F3ECE7"


def _html(markup: str) -> None:
    """Render an indented HTML template safely (dedent avoids code blocks)."""
    st.markdown(textwrap.dedent(markup).strip(), unsafe_allow_html=True)


def _record_history(name: str, status: str, detail: str) -> None:
    """Append a real upload attempt to the in-session history."""
    history = st.session_state.setdefault("upload_history", [])
    history.insert(
        0,
        {
            "file": name,
            "time": datetime.now().strftime("%b %d, %Y · %H:%M"),
            "status": status,
            "detail": detail,
        },
    )


def render():
    """Render the upload screen. On success, session_state.uploaded_df is set."""
    # ------------------------------------------------------------- page CSS
    _html(
        f"""
        <style>
            [data-testid="stHeader"] {{
                background: transparent !important; height: 1.5rem !important;
                pointer-events: none;
            }}
            [data-testid="stHeader"] button {{ pointer-events: auto; }}
            .block-container {{
                padding: 0.4rem 1.5rem 2rem 1.5rem !important;
                max-width: 100% !important;
            }}
            [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] {{
                row-gap: 0.55rem !important;
            }}
            .stApp {{
                background:
                    radial-gradient(50rem 32rem at 100% 0%, #FCE4D6 0%, rgba(252,228,214,0) 62%),
                    radial-gradient(44rem 30rem at 0% 100%, #FDEDE4 0%, rgba(253,237,228,0) 55%),
                    #FFFDFA;
            }}
            .stButton > button {{
                border-radius: 10px !important; font-weight: 700 !important;
                border: 1px solid {LINE} !important;
                transition: transform 0.12s ease, box-shadow 0.12s ease !important;
            }}
            .stButton > button:hover {{
                transform: translateY(-1px);
                box-shadow: 0 8px 18px rgba(31,41,55,0.12) !important;
            }}
            .stButton > button[kind="primary"] {{
                background: {CORAL} !important; border-color: {CORAL} !important;
                box-shadow: 0 6px 16px rgba(245,80,54,0.30) !important;
            }}

            /* -------- left hero -------- */
            .ubadge {{
                display:inline-block; margin-top:1.6rem;
                border-radius:999px; background:{CORAL_SOFT}; color:{CORAL};
                font-size:0.66rem; font-weight:800; letter-spacing:1.4px;
                padding:0.38rem 1rem;
            }}
            h1.uhero {{
                font-size:2.7rem; font-weight:800; color:{NAVY};
                letter-spacing:-1.2px; margin:0.7rem 0 0 0; line-height:1.1;
            }}
            h1.uhero .accent {{ color:{CORAL}; }}
            .usub {{
                color:{SLATE}; font-size:0.98rem; line-height:1.55; margin-top:0.7rem;
            }}

            /* -------- dropzone card (Streamlit uploader, restyled) -------- */
            .dropcard {{ margin-top:1.1rem; }}
            [data-testid="stFileUploader"] section {{
                border: 2px dashed #F5B79E !important;
                border-radius: 16px !important;
                background: #FFF8F4 !important;
                padding: 1.6rem 1rem 1.4rem 1rem !important;
            }}
            [data-testid="stFileUploader"] section:hover {{
                border-color: {CORAL} !important;
                background: #FFF3EC !important;
            }}
            [data-testid="stFileUploader"] button {{
                background: {CORAL} !important; color: #fff !important;
                border: none !important; border-radius: 10px !important;
                padding: 0.62rem 1.5rem !important; font-weight: 700 !important;
                box-shadow: 0 6px 16px rgba(245,80,54,0.30) !important;
            }}
            [data-testid="stFileUploader"] section {{
                display: flex; flex-direction: column; align-items: center;
                padding: 1.3rem 1rem 1.2rem 1rem !important;
            }}
            /* hide Streamlit's native instructions caption ("20MB per file •
               CSV") — we render one consistent copy via ::before/::after */
            [data-testid="stFileUploaderDropzoneInstructions"] {{
                display: none !important;
            }}
            /* hint text rendered INSIDE the dropzone, above the button */
            [data-testid="stFileUploader"] section::before {{
                content: "☁️\\A Drag and drop your CSV file here\\A or click the button below to browse from your device";
                white-space: pre-wrap; text-align: center;
                color: {INK}; font-size: 0.95rem; font-weight: 400;
                line-height: 1.8; margin-bottom: 0.8rem; display: block;
            }}
            /* one consistent file-size line, neatly below the button */
            [data-testid="stFileUploader"] section::after {{
                content: "Maximum file size: 20 MB  •  CSV only";
                display: block; text-align: center;
                color: {MUTED}; font-size: 0.76rem; margin-top: 0.7rem;
            }}
            [data-testid="stFileUploader"] button {{
                display: block; margin: 0 auto !important;
            }}
            .dz-hint {{ display: none; }} /* superseded — hint lives in the dropzone */

            /* -------- compact template download button (content-width, left-aligned) -------- */
            [data-testid="stDownloadButton"] {{
                margin: 1.15rem 0 1.2rem 0;
            }}
            [data-testid="stDownloadButton"] button {{
                background:#FFFFFF !important;
                color:{NAVY} !important;
                border:1px solid {LINE} !important;
                border-radius:10px !important;
                height:46px !important;
                padding:0 1.15rem !important;
                font-weight:700 !important; font-size:0.9rem !important;
                box-shadow:0 2px 10px rgba(31,41,55,0.07) !important;
                display:inline-flex; align-items:center;
            }}
            [data-testid="stDownloadButton"] button:hover {{
                border-color:{CORAL} !important;
                box-shadow:0 4px 14px rgba(245,80,54,0.16) !important;
                transform:translateY(-1px);
            }}
            [data-testid="stDownloadButton"] button::before {{
                content:"";
                width:16px; height:16px; margin-right:0.5rem;
                background:{CORAL};
                -webkit-mask:center/contain no-repeat url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/%3E%3Cpolyline points='7 10 12 15 17 10'/%3E%3Cline x1='12' y1='15' x2='12' y2='3'/%3E%3C/svg%3E");
                mask:center/contain no-repeat url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/%3E%3Cpolyline points='7 10 12 15 17 10'/%3E%3Cline x1='12' y1='15' x2='12' y2='3'/%3E%3C/svg%3E");
            }}

            /* -------- expected columns card -------- */
            .cols-card {{
                background:#EFF6FF; border:1px solid #BFDBFE; border-radius:14px;
                padding:0.95rem 1.15rem; display:flex; gap:0.9rem; align-items:flex-start;
                margin-top:1.15rem;
            }}
            .cols-card .cico {{
                width:2.1rem; height:2.1rem; border-radius:50%; flex-shrink:0;
                background:#2563EB; color:#fff; display:flex;
                align-items:center; justify-content:center; font-size:0.95rem;
            }}
            .cols-card .ct {{ font-size:0.92rem; color:#1E3A8A; }}
            .cols-card .ct b {{ color:#1D4ED8; }}
            .cols-card .cd {{ font-size:0.84rem; color:#3B5B92; margin-top:0.15rem; }}

            /* -------- right insight card -------- */
            .insight {{
                background:linear-gradient(160deg, #FFF3EC 0%, #FFE9DC 100%);
                border:1px solid #F8DCc8; border-radius:20px;
                padding:1.5rem 1.6rem 1.4rem 1.6rem; height:100%;
                box-shadow:0 18px 44px rgba(245,80,54,0.10);
            }}
            .insight .ibadge {{
                display:inline-block; border-radius:999px; background:{CORAL_SOFT};
                color:{CORAL}; font-size:0.62rem; font-weight:800;
                letter-spacing:1.2px; padding:0.32rem 0.85rem;
            }}
            .insight h3 {{
                font-size:1.45rem; font-weight:800; color:{NAVY};
                letter-spacing:-0.4px; margin:0.8rem 0 0 0; line-height:1.25;
            }}
            .insight .idesc {{ color:{SLATE}; font-size:0.92rem; line-height:1.55; margin-top:0.6rem; }}
            .ifeats {{ display:flex; gap:1.1rem; margin-top:1.25rem; flex-wrap:wrap; }}
            .ifeat {{ display:flex; gap:0.55rem; align-items:flex-start; flex:1; min-width:8rem; }}
            .ifeat .ifico {{
                width:2rem; height:2rem; border-radius:9px; flex-shrink:0;
                display:flex; align-items:center; justify-content:center; font-size:0.9rem;
            }}
            .ifeat .t {{ font-size:0.8rem; font-weight:800; color:{INK}; line-height:1.2; }}
            .ifeat .d {{ font-size:0.7rem; color:{SLATE}; margin-top:0.1rem; }}

            /* -------- recent uploads -------- */
            .recent {{
                background:#FFFFFF; border:1px solid {LINE}; border-radius:16px;
                padding:1.15rem 1.4rem 1.25rem 1.4rem; margin-top:1.5rem;
                box-shadow:0 10px 30px rgba(31,41,55,0.05);
            }}
            .recent .rhead {{ display:flex; align-items:center; gap:0.6rem; }}
            .recent .rhead .rico {{ font-size:1.05rem; color:{INK}; }}
            .recent .rhead h3 {{ font-size:1.05rem; font-weight:800; color:{INK}; margin:0; }}
            .rempty {{ text-align:center; padding:1.6rem 0 1.2rem 0; }}
            .rempty .eglyph {{ font-size:1.9rem; opacity:0.7; }}
            .rempty .et {{ font-size:0.92rem; font-weight:700; color:{INK}; margin-top:0.5rem; }}
            .rempty .ed {{ font-size:0.82rem; color:{SLATE}; margin-top:0.2rem; }}
            .rrow {{
                display:flex; align-items:center; gap:0.9rem;
                border:1px solid {LINE}; border-radius:11px;
                padding:0.65rem 1rem; margin-top:0.6rem;
            }}
            .rrow .rname {{ font-weight:700; color:{INK}; font-size:0.88rem; flex:1; }}
            .rrow .rmeta {{ color:{MUTED}; font-size:0.78rem; }}
            .rrow .ok {{ color:#16A34A; font-size:0.8rem; font-weight:700; }}
            .rrow .bad {{ color:#DC2626; font-size:0.8rem; font-weight:700; }}

            @media (max-width: 900px) {{
                h1.uhero {{ font-size:1.9rem; letter-spacing:-0.8px; }}
                .block-container {{ padding: 0.3rem 1rem 1.5rem 1rem !important; }}
                .insight {{ margin-top:1rem; }}
            }}
        </style>
        """,
    )

    # --------------------------------------------------------- two columns
    left, right = st.columns([1.55, 1], gap="medium")

    # -------------------------------------------------------------- left
    with left:
        _html(
            f"""
            <div>
                <span class="ubadge">DATA UPLOAD</span>
                <h1 class="uhero">Upload your <span class="accent">sales data</span></h1>
                <p class="usub">Upload your CSV file and let Salesight validate, clean
                and analyze your data. Your data is processed securely and nothing
                is shared publicly.</p>
            </div>
            """,
        )

        st.download_button(
            "Download Template CSV",
            data=TEMPLATE_CSV,
            file_name="sales_template.csv",
            mime="text/csv",
        )

        uploaded = st.file_uploader(
            "CSV file",
            type=["csv"],
            accept_multiple_files=False,
            label_visibility="collapsed",
        )

        _html(
            """
            <div class="cols-card">
                <div class="cico">i</div>
                <div>
                    <div class="ct">Expected columns: <b>date</b>, <b>product</b>,
                    <b>quantity</b>, <b>price</b></div>
                    <div class="cd">Column names must match exactly. Extra or missing
                    columns will be rejected.</div>
                </div>
            </div>
            """,
        )

    # ------------------------------------------------------------- right
    with right:
        _html(
            f"""
            <div class="insight">
                <span class="ibadge">FROM DATA TO INSIGHTS</span>
                <h3>Turn your raw sales data into meaningful insights</h3>
                <p class="idesc">Upload your CSV and get clean, structured and
                ready-to-analyze data — in just a few seconds.</p>
                <svg viewBox="0 0 380 170" width="100%" style="margin-top:1rem;">
                    <!-- decorative: CSV sheet -> arrow -> charts (no values) -->
                    <rect x="14" y="26" width="108" height="128" rx="12"
                          fill="#FFFFFF" stroke="{LINE}"/>
                    <rect x="42" y="14" width="52" height="26" rx="6" fill="#22A06B"/>
                    <text x="68" y="32" text-anchor="middle" fill="#fff"
                          font-size="12" font-weight="bold" font-family="sans-serif">CSV</text>
                    <rect x="30" y="56" width="76" height="10" rx="5" fill="#EEF0F3"/>
                    <rect x="30" y="76" width="76" height="10" rx="5" fill="#EEF0F3"/>
                    <rect x="30" y="96" width="76" height="10" rx="5" fill="#EEF0F3"/>
                    <rect x="30" y="116" width="76" height="10" rx="5" fill="#EEF0F3"/>
                    <path d="M 138 88 q 24 -18 48 -2" fill="none"
                          stroke="{CORAL}" stroke-width="4" stroke-linecap="round"/>
                    <path d="M 178 78 l 10 8 l -14 4 z" fill="{CORAL}"/>
                    <rect x="204" y="22" width="160" height="86" rx="12"
                          fill="#FFFFFF" stroke="{LINE}"/>
                    <polyline points="220,90 250,66 276,76 306,48 344,58"
                              fill="none" stroke="{CORAL}" stroke-width="4"
                              stroke-linecap="round" stroke-linejoin="round"/>
                    <rect x="204" y="120" width="160" height="34" rx="10"
                          fill="#FFFFFF" stroke="{LINE}"/>
                    <circle cx="230" cy="137" r="12" fill="none"
                            stroke="{CORAL_SOFT}" stroke-width="7"/>
                    <path d="M 230 125 A 12 12 0 0 1 241 141"
                          fill="none" stroke="{CORAL}" stroke-width="7"
                          stroke-linecap="round"/>
                    <rect x="254" y="128" width="52" height="7" rx="3.5" fill="#EEF0F3"/>
                    <rect x="254" y="140" width="36" height="7" rx="3.5" fill="#EEF0F3"/>
                </svg>
                <div class="ifeats">
                    <div class="ifeat">
                        <div class="ifico" style="background:#DCFCE7;">🛡️</div>
                        <div><div class="t">Secure Upload</div>
                        <div class="d">Your data stays private</div></div>
                    </div>
                    <div class="ifeat">
                        <div class="ifico" style="background:#FEF3C7;">⚡</div>
                        <div><div class="t">Automatic Validation</div>
                        <div class="d">Schema-checked instantly</div></div>
                    </div>
                    <div class="ifeat">
                        <div class="ifico" style="background:{CORAL_SOFT};">📊</div>
                        <div><div class="t">Ready for Analysis</div>
                        <div class="d">Cleaned in seconds</div></div>
                    </div>
                </div>
            </div>
            """,
        )

    # -------------------------------------------------- process the upload
    if uploaded is not None:
        size_kb = len(uploaded.getvalue()) / 1024
        st.caption(f"📄 {uploaded.name} — {size_kb:,.0f} KB")

        if st.button("🚀 Validate & Analyze this file", type="primary", use_container_width=True):
            with st.spinner("Validating, cleaning and preparing your data…"):
                try:
                    raw = uploaded.getvalue()
                    df = uv.validate_upload(raw)
                    cleaned = etl_transform(df)  # reuse the shared ETL logic
                    st.session_state.uploaded_df = cleaned
                    st.session_state.df_source = "uploaded"
                    st.session_state.page = "app"
                    st.query_params.update({"page": "dashboard", "source": "uploaded"})
                    _record_history(
                        uploaded.name, "ok",
                        f"{len(cleaned):,} clean rows — validated",
                    )
                    st.success(f"✅ Validated and processed {len(cleaned):,} rows.")
                    st.rerun()
                except uv.UploadValidationError as exc:
                    _record_history(uploaded.name, "bad", str(exc)[:80])
                    st.error(f"**Validation failed** — {exc}")
                except Exception as exc:  # noqa: BLE001 - surfaced to the user
                    _record_history(uploaded.name, "bad", f"error: {exc}")
                    st.error(f"Could not process the file: {exc}")
        else:
            # Peek at the file without committing it
            try:
                preview = uv.read_csv_bytes(uploaded.getvalue())
                preview = uv.validate_schema(preview)
                st.markdown("**Preview (first 5 rows):**")
                st.dataframe(preview.head(5), use_container_width=True, hide_index=True)
            except uv.UploadValidationError as exc:
                st.warning(f"This file will be rejected: {exc}")

    # ------------------------------------------------------ recent uploads
    history = st.session_state.get("upload_history", [])
    rows_html = ""
    for item in history[:5]:
        badge = (
            f'<span class="ok">✓ {item["detail"]}</span>'
            if item["status"] == "ok"
            else f'<span class="bad">✗ Rejected — {item["detail"]}</span>'
        )
        rows_html += (
            f'<div class="rrow"><span class="rname">📄 {item["file"]}</span>'
            f'<span class="rmeta">{item["time"]}</span>{badge}</div>'
        )

    empty_state = """
        <div class="rempty">
            <div class="eglyph">📄</div>
            <div class="et">No file uploaded yet</div>
            <div class="ed">Upload a CSV file to see your recent uploads and
            validation status here.</div>
        </div>
    """

    _html(
        f"""
        <div class="recent">
            <div class="rhead"><span class="rico">🕘</span><h3>Recent Uploads</h3></div>
            {rows_html if rows_html else empty_state}
        </div>
        """,
    )


def render_uploaded_complete():
    """Small status card once an upload has been processed."""
    df = st.session_state.get("uploaded_df")
    if df is None:
        return
    st.success(
        f"Analyzing your uploaded data — {len(df):,} rows, "
        f"{df['product'].nunique()} products, "
        f"{df['date'].min():%b %d, %Y} → {df['date'].max():%b %d, %Y}."
    )
    if st.button("Upload a different file"):
        st.session_state.pop("uploaded_df", None)
        st.session_state.df_source = None
        st.rerun()
