"""
Salesight landing page — follows the reference design:

- full-width slim navbar: logo · Log in / Sign Up
- hero: badge, two-line headline with italic coral accent, subcopy,
  "Upload Your CSV" + "Try Demo Dataset →" CTAs, three feature chips
- right: product preview (dashboard mockup) with honest EMPTY states —
  every KPI shows "—" and "Upload data to view", charts show
  "No data available". No mock numbers anywhere. The greeting uses the
  real logged-in user's name when available.
- features section: "Everything You Need for Sales Analytics" with 4 cards
- trust banner at the bottom

Note: every HTML block goes through _html() (textwrap.dedent) because
Markdown renders indented lines as code blocks otherwise.
"""

import textwrap

import streamlit as st

import auth

CORAL = "#F55036"       # primary accent (buttons, highlights)
CORAL_SOFT = "#FDE7DD"  # peach fills
INK = "#1F2937"         # headline / dark text
SLATE = "#6B7280"       # body text
MUTED = "#9CA3AF"
LINE = "#F3ECE7"        # card borders


def _html(markup: str) -> None:
    """Render an indented HTML template safely (dedent avoids code blocks)."""
    st.markdown(textwrap.dedent(markup).strip(), unsafe_allow_html=True)


def _display_name() -> str:
    """Real user's display name from the session, or 'Guest'."""
    return auth.display_name(auth.current_user())


def _initial() -> str:
    return (_display_name()[:1] or "G").upper()


def render(on_demo, on_get_started, on_upload):
    """Render the landing page; the arguments are routing callbacks."""
    _html(
        f"""
        <style>
            [data-testid="stToolbar"] {{ display: none !important; }}
            [data-testid="stDecoration"] {{ display: none !important; }}
            #MainMenu, [data-testid="stMainMenu"] {{ display: none !important; }}
            [data-testid="stHeader"] {{
                background: transparent !important; height: 1.5rem !important;
                pointer-events: none;
            }}
            [data-testid="stHeader"] button {{ pointer-events: auto; }}
            .block-container {{
                padding: 0 1.5rem 2rem 1.5rem !important;
                max-width: 100% !important;
            }}
            .stApp {{ background: #FFFFFF; }}

            /* style-only markdown wrappers eat row-gap; app.py hides them
               globally — the landing just tightens the main row-gap */
            [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] {{
                row-gap: 0.6rem !important;
            }}

            /* polished buttons across the landing page */
            .stButton > button {{
                border-radius: 10px !important;
                font-weight: 700 !important;
                border: 1px solid {LINE} !important;
                box-shadow: 0 1px 2px rgba(31,41,55,0.06) !important;
                transition: transform 0.12s ease, box-shadow 0.12s ease !important;
            }}
            .stButton > button:hover {{
                transform: translateY(-1px);
                box-shadow: 0 8px 18px rgba(31,41,55,0.12) !important;
            }}
            .stButton > button[kind="primary"] {{
                background: {CORAL} !important;
                border-color: {CORAL} !important;
                box-shadow: 0 6px 16px rgba(245,80,54,0.30) !important;
            }}

            /* ---------------- nav bar ---------------- */
            .nav {{
                display: flex; align-items: center;
                padding: 0.55rem 0 0.8rem 0;
            }}
            /* nav row: auth buttons vertically centered on the brand's
               centerline (buttons render 8px high) — no underline line */
            [data-testid="stLayoutWrapper"]:has(.brand) .stButton > button {{
                margin-top: 16px !important;
            }}
            .brand {{ display:flex; align-items:center; gap:0.45rem; }}
            .brand .logo {{ color:{CORAL}; font-size:1.05rem; }}
            .brand .name {{ font-weight:800; font-size:1.12rem; color:{INK}; letter-spacing:-0.2px; }}

            /* ---------------- hero ---------------- */
            .badge {{
                display:inline-block; margin-top:1.8rem;
                border-radius:999px; background:{CORAL_SOFT}; color:{CORAL};
                font-size:0.68rem; font-weight:700; letter-spacing:1.1px;
                padding:0.38rem 1rem;
            }}
            h1.hero-title {{
                font-size:3.4rem; line-height:1.06; font-weight:800;
                color:{INK}; letter-spacing:-1.6px; margin:1rem 0 0 0;
            }}
            h1.hero-title .accent {{
                color:{CORAL}; font-style:italic; font-weight:700;
                background: linear-gradient(transparent 68%, {CORAL_SOFT} 68%);
                padding: 0 0.15rem; border-radius: 4px;
            }}
            .sub {{
                color:{SLATE}; font-size:1rem; line-height:1.6;
                margin-top:1.1rem; max-width:27rem;
            }}
            .chips {{ display:flex; gap:0.9rem; margin-top:2rem; flex-wrap:wrap; }}
            .chipitem {{
                display:flex; gap:0.6rem; align-items:flex-start;
                background:#FFFFFF; border:1px solid {LINE}; border-radius:12px;
                padding:0.7rem 0.95rem; box-shadow:0 2px 10px rgba(31,41,55,0.05);
            }}
            .chipitem .ico {{ font-size:1.05rem; }}
            .chipitem .t {{ font-size:0.83rem; font-weight:700; color:{INK}; }}
            .chipitem .d {{ font-size:0.76rem; color:{SLATE}; margin-top:0.08rem; }}

            /* ------------- product mockup ------------- */
            .mockwrap {{ position:relative; padding:2.1rem 0 1rem 1rem; }}
            .blob {{
                position:absolute; top:0.6rem; right:-2.5rem;
                width:26rem; height:26rem; z-index:0;
                background:radial-gradient(circle at 40% 40%, #FCE3D6 0%, #FDEDE4 55%, rgba(255,255,255,0) 75%);
                border-radius:50%;
            }}
            .mock {{
                position:relative; z-index:1;
                background:#FFFFFF; border:1px solid {LINE}; border-radius:16px;
                box-shadow:0 24px 60px rgba(31,41,55,0.12);
                overflow:hidden; display:flex; min-height:26rem;
            }}
            .mside {{
                width:26%; min-width:9.5rem; border-right:1px solid {LINE};
                padding:0.9rem 0.7rem; background:#FFFFFF;
            }}
            .mside .mbrand {{ display:flex; align-items:center; gap:0.4rem; padding:0 0.3rem 0.8rem 0.3rem; }}
            .mside .mbrand .logo {{ color:{CORAL}; font-size:0.85rem; }}
            .mside .mbrand .name {{ font-weight:800; font-size:0.85rem; color:{INK}; }}
            .mitem {{
                display:flex; align-items:center; gap:0.5rem;
                font-size:0.76rem; font-weight:600; color:{SLATE};
                padding:0.5rem 0.6rem; border-radius:8px; margin-bottom:0.15rem;
            }}
            .mitem.active {{ background:{CORAL_SOFT}; color:{CORAL}; }}
            .mmain {{ flex:1; padding:0.8rem 1rem; background:#FBFBFA; }}
            .mtop {{ display:flex; align-items:center; gap:0.8rem; margin-bottom:0.9rem; }}
            .msearch {{
                flex:1; background:#F3F4F6; border-radius:999px;
                font-size:0.74rem; color:{MUTED}; padding:0.42rem 0.9rem;
            }}
            .mavatar {{
                display:flex; align-items:center; gap:0.4rem;
                font-size:0.74rem; font-weight:700; color:{INK};
            }}
            .mavatar .av {{
                width:1.5rem; height:1.5rem; border-radius:50%;
                background:{INK}; color:#fff; display:flex;
                align-items:center; justify-content:center; font-size:0.62rem;
            }}
            .mwelcome {{ display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:0.8rem; }}
            .mwelcome h4 {{ font-size:1.02rem; font-weight:800; color:{INK}; margin:0; }}
            .mwelcome p {{ font-size:0.75rem; color:{SLATE}; margin:0.15rem 0 0 0; }}
            .mbtn {{
                background:{CORAL}; color:#fff; font-size:0.74rem; font-weight:700;
                border-radius:9px; padding:0.5rem 0.9rem; white-space:nowrap;
            }}
            .mkpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:0.6rem; margin-bottom:0.7rem; }}
            .mcard {{
                background:#FFFFFF; border:1px solid {LINE}; border-radius:11px;
                padding:0.6rem 0.7rem;
            }}
            .mkpi .mrow {{ display:flex; align-items:center; gap:0.4rem; }}
            .mkpi .kico {{
                width:1.35rem; height:1.35rem; border-radius:7px;
                background:{CORAL_SOFT}; display:flex; align-items:center;
                justify-content:center; font-size:0.68rem;
            }}
            .mkpi .klabel {{ font-size:0.66rem; font-weight:700; color:{SLATE}; }}
            .mkpi .kvalue {{ font-size:1.05rem; font-weight:800; color:{INK}; text-align:center; margin:0.45rem 0 0.2rem 0; }}
            .mkpi .khint {{ font-size:0.6rem; color:{MUTED}; text-align:center; }}
            .mcharts {{ display:grid; grid-template-columns:1.45fr 1fr; gap:0.6rem; }}
            .mchart h5 {{ font-size:0.78rem; font-weight:800; color:{INK}; margin:0; }}
            .mchart .mc-sub {{ font-size:0.63rem; color:{SLATE}; margin:0.12rem 0 0.55rem 0; }}
            .mempty {{
                display:flex; flex-direction:column; align-items:center;
                justify-content:center; text-align:center; padding:0.9rem 0.5rem 1rem 0.5rem;
            }}
            .mempty .glyph {{ font-size:1.5rem; opacity:0.75; }}
            .mempty .notitle {{ font-size:0.7rem; font-weight:700; color:{INK}; margin-top:0.45rem; }}
            .mempty .nosub {{ font-size:0.62rem; color:{MUTED}; margin-top:0.15rem; }}
            .donut-ring {{ width:2.4rem; height:2.4rem; }}

            /* ------------- features section ------------- */
            .section {{ margin-top:3.2rem; }}
            .sec-head {{ text-align:center; }}
            .sec-head h2 {{ font-size:2rem; font-weight:800; color:{INK}; letter-spacing:-0.6px; margin:0; }}
            .sec-head p {{ color:{SLATE}; font-size:0.95rem; margin:0.5rem 0 0 0; }}
            .fcard2 {{
                background:#FFFFFF; border:1px solid {LINE}; border-radius:14px;
                padding:1.15rem 1.2rem; height:100%;
            }}
            .fcard2 .fico {{
                width:2.4rem; height:2.4rem; border-radius:10px;
                display:flex; align-items:center; justify-content:center;
                font-size:1.05rem; margin-bottom:0.8rem;
            }}
            .fcard2 h3 {{ font-size:1.02rem; font-weight:800; color:{INK}; margin:0 0 0.35rem 0; }}
            .fcard2 p {{ font-size:0.84rem; color:{SLATE}; line-height:1.5; margin:0; }}

            /* ------------- trust banner ------------- */
            .trustband {{
                margin-top:2.6rem; background:#FDEBE2; border-radius:999px;
                display:flex; align-items:center; gap:0.9rem;
                padding:0.85rem 2rem; justify-content:center;
            }}
            .trustband .ticon {{
                width:2.1rem; height:2.1rem; border-radius:50%;
                background:{CORAL}; color:#fff; display:flex;
                align-items:center; justify-content:center; font-size:0.95rem;
            }}
            .trustband .tb {{ text-align:left; }}
            .trustband .tb .t1 {{ font-size:0.86rem; font-weight:700; color:{CORAL}; }}
            .trustband .tb .t2 {{ font-size:0.76rem; color:{SLATE}; margin-top:0.05rem; }}

            /* ------------- how-it-works + footer ------------- */
            .step {{
                background:#FFFFFF; border:1px solid {LINE}; border-radius:14px;
                padding:1.15rem 1.2rem; height:100%;
            }}
            .stepnum {{
                width:1.9rem; height:1.9rem; border-radius:50%;
                background:{CORAL}; color:#FFFFFF; font-size:0.85rem; font-weight:800;
                display:flex; align-items:center; justify-content:center;
                margin-bottom:0.7rem; box-shadow:0 4px 10px rgba(245,80,54,0.28);
            }}
            .step h3 {{ font-size:0.98rem; font-weight:800; color:{INK}; margin:0 0 0.3rem 0; }}
            .step p {{ font-size:0.83rem; color:{SLATE}; line-height:1.5; margin:0; }}
            .footer {{
                margin-top:2.2rem; border-top:1px solid {LINE};
                padding:1.1rem 0 0.5rem 0; text-align:center;
                color:{MUTED}; font-size:0.78rem;
            }}

            @media (max-width: 900px) {{
                h1.hero-title {{ font-size:2.4rem; letter-spacing:-1px; }}
                .mkpis {{ grid-template-columns:repeat(2,1fr); }}
                .mcharts {{ grid-template-columns:1fr; }}
                .block-container {{ padding: 0 1.1rem 2rem 1.1rem !important; }}
            }}
        </style>
        """,
    )

    # ------------------------------------------------------------- nav bar
    nav_logo, nav_auth = st.columns([3.4, 1], vertical_alignment="center")
    with nav_logo:
        _html(
            f"""
            <div class="brand">
                <span class="logo">🔻</span>
                <span class="name">Salesight</span>
            </div>
            """,
        )
    with nav_auth:
        b1, b2 = st.columns([1, 1], gap="small")
        login_clicked = b1.button("Log in", use_container_width=True)
        signup_clicked = b2.button("Sign Up", type="primary", use_container_width=True)
    if login_clicked or signup_clicked:
        on_get_started()
        st.rerun()

    # ---------------------------------------------------------- hero row
    hero_left, hero_right = st.columns([1, 1.22], gap="medium")

    with hero_left:
        name = _display_name()
        _html(
            f"""
            <span class="badge">#1 SALES ANALYTICS TOOL</span>
            <h1 class="hero-title">Smarter Sales<br>Bigger <span class="accent">Insights</span></h1>
            <p class="sub">Salesight gives you tools to explore, understand and present
            your sales data without the chaos — from raw CSV to
            real-time interactive dashboards.</p>
            """,
        )

        uc1, uc2 = st.columns([1.15, 1.25], gap="small")
        with uc1:
            upload_clicked = st.button("⬆️ Upload Your CSV", type="primary", use_container_width=True)
        with uc2:
            try_demo = st.button("Try Demo Dataset →", use_container_width=True)
        if upload_clicked:
            on_upload()
            st.rerun()
        if try_demo:
            on_demo()
            st.rerun()

        _html(
            f"""
            <div class="chips">
                <div class="chipitem">
                    <span class="ico">⚡</span>
                    <span><div class="t">Fast Analysis</div><div class="d">Get insights in seconds</div></span>
                </div>
                <div class="chipitem">
                    <span class="ico">📊</span>
                    <span><div class="t">Interactive Dashboards</div><div class="d">Visualize your data easily</div></span>
                </div>
                <div class="chipitem">
                    <span class="ico">🔒</span>
                    <span><div class="t">Your Data Stays Private</div><div class="d">Secure &amp; confidential</div></span>
                </div>
            </div>
            """,
        )

    with hero_right:
        initial = _initial()
        _html(
            f"""
            <div class="mockwrap">
                <div class="blob"></div>
                <div class="mock">
                    <div class="mside">
                        <div class="mbrand">
                            <span class="logo">🔻</span><span class="name">Salesight</span>
                        </div>
                        <div class="mitem active">🏠 Dashboard</div>
                        <div class="mitem">⬆️ Upload Data</div>
                        <div class="mitem">📊 Analytics</div>
                        <div class="mitem">📄 Reports</div>
                        <div class="mitem">💡 Insights</div>
                        <div class="mitem">⚙️ Settings</div>
                    </div>
                    <div class="mmain">
                        <div class="mtop">
                            <div class="msearch">🔍&nbsp; Search…</div>
                            <div class="mavatar"><span class="av">{initial}</span> {name}</div>
                        </div>
                        <div class="mwelcome">
                            <div>
                                <h4>Welcome, {name}!</h4>
                                <p>Upload your sales data to start analyzing.</p>
                            </div>
                            <div class="mbtn">⬆️ Upload CSV</div>
                        </div>
                        <div class="mkpis">
                            <div class="mcard mkpi">
                                <div class="mrow"><span class="kico">💰</span><span class="klabel">Total Revenue</span></div>
                                <div class="kvalue">—</div>
                                <div class="khint">Upload data to view</div>
                            </div>
                            <div class="mcard mkpi">
                                <div class="mrow"><span class="kico">🧾</span><span class="klabel">Total Orders</span></div>
                                <div class="kvalue">—</div>
                                <div class="khint">Upload data to view</div>
                            </div>
                            <div class="mcard mkpi">
                                <div class="mrow"><span class="kico">📦</span><span class="klabel">Total Products</span></div>
                                <div class="kvalue">—</div>
                                <div class="khint">Upload data to view</div>
                            </div>
                            <div class="mcard mkpi">
                                <div class="mrow"><span class="kico">🏷️</span><span class="klabel">Top Category</span></div>
                                <div class="kvalue">—</div>
                                <div class="khint">Upload data to view</div>
                            </div>
                        </div>
                        <div class="mcharts">
                            <div class="mcard mchart">
                                <h5>Sales Trend</h5>
                                <div class="mc-sub">Upload your data to see the sales trend over time.</div>
                                <div class="mempty">
                                    <svg width="52" height="30" viewBox="0 0 52 30">
                                        <polyline points="2,26 15,17 26,21 37,8 50,13"
                                            fill="none" stroke="#D1D5DB" stroke-width="2.5"
                                            stroke-linecap="round" stroke-linejoin="round"/>
                                    </svg>
                                    <div class="notitle">No data available</div>
                                    <div class="nosub">Upload a CSV file to generate your sales trend chart.</div>
                                </div>
                            </div>
                            <div class="mcard mchart">
                                <h5>Category Share</h5>
                                <div class="mc-sub">Your product category distribution will appear here.</div>
                                <div class="mempty">
                                    <svg class="donut-ring" viewBox="0 0 36 36">
                                        <circle cx="18" cy="18" r="13" fill="none"
                                            stroke="#E5E7EB" stroke-width="6"/>
                                    </svg>
                                    <div class="notitle">No data available</div>
                                    <div class="nosub">Upload a CSV file to view category share.</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """,
        )

    # ------------------------------------------------- features section
    _html(
        """
        <div class="section sec-head">
            <h2>Everything You Need for Sales Analytics</h2>
            <p>Powerful features to turn your sales data into meaningful insights</p>
        </div>
        """,
    )
    feature_cols = st.columns(4, gap="small")
    features = [
        ("⬆️", "#FDE7DD", "Easy CSV Upload",
         "Simply upload your sales data and we'll handle the rest."),
        ("📊", "#DCFCE7", "Interactive Dashboards",
         "Explore your data with beautiful, interactive visualizations."),
        ("💡", "#DBEAFE", "Key Insights",
         "Discover trends, top products, and growth opportunities."),
        ("⬇️", "#EDE9FE", "Export Reports",
         "Download insights and share with your team."),
    ]
    for col, (icon, bg, title, desc) in zip(feature_cols, features):
        with col:
            _html(
                f"""
                <div class="fcard2">
                    <div class="fico" style="background:{bg};">{icon}</div>
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
                """,
            )

    # ------------------------------------------------------ trust banner
    _html(
        """
        <div class="trustband">
            <div class="ticon">👥</div>
            <div class="tb">
                <div class="t1">Trusted by students, professionals and growing businesses</div>
                <div class="t2">Turn your sales data into smarter decisions with Salesight.</div>
            </div>
        </div>
        """,
    )

    # -------------------------------------------------- how-it-works band
    _html(
        """
        <div class="section sec-head" style="margin-top:2.8rem;">
            <h2>From Raw CSV to Insights in Three Steps</h2>
            <p>No setup, no configuration — upload and analyze instantly</p>
        </div>
        """,
    )
    step_cols = st.columns(3, gap="small")
    steps = [
        ("1", "Upload Your CSV",
         "Drop in any sales export with date, product, quantity and price columns."),
        ("2", "Automatic Cleaning",
         "The ETL pipeline validates, deduplicates and categorizes every row."),
        ("3", "Explore Your Dashboard",
         "Interactive KPIs, trends and top-sellers update in real time."),
    ]
    for col, (num, title, desc) in zip(step_cols, steps):
        with col:
            _html(
                f"""
                <div class="step">
                    <div class="stepnum">{num}</div>
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
                """,
            )

    # ------------------------------------------------------------- footer
    _html(
        """
        <div class="footer">
            Salesight — Sales analytics built on a production-grade pipeline
            (pandas · MySQL · Streamlit · Plotly · Docker)
        </div>
        """,
    )
