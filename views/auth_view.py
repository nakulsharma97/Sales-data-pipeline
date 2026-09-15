"""
Auth screen — premium two-column login/signup experience.

Layout (mirrors the reference design):
- navbar: Salesight logo · decorative links · Continue as Guest · Get Started
- left hero: badge, headline, subcopy, three feature rows, decorative
  analytics illustration (pure SVG shapes — no numbers, no fake metrics)
- right: white rounded auth card with Log in / Sign up tabs, email +
  password inputs, Forgot password, coral submit, guest bypass and
  mode-switch link
- footer strip

All authentication logic lives in auth.py and is used unchanged.
"""

import textwrap

import streamlit as st

import auth

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


def render(on_success):
    """Render the auth screen; on_success is called for the guest/demo path."""
    mode = st.session_state.get("auth_mode", "login")

    # Show notice when redirected from Upload CSV gate
    if st.session_state.pop("auth_notice", None) == "upload":
        _html(
            f"""
            <div style="margin-bottom:1rem; padding:0.85rem 1.1rem; border-radius:12px;
                        background:{CORAL_SOFT}; border:1px solid #F8CDBB;">
                <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.3rem;">
                    <span style="font-size:1.1rem;">🔐</span>
                    <strong style="color:{INK}; font-size:0.92rem;">Sign in to upload your data</strong>
                </div>
                <p style="color:{SLATE}; font-size:0.84rem; margin:0; line-height:1.5;">
                    Please sign in to upload your own CSV data. Guest mode keeps the demo
                    dataset accessible — uploading your personal files needs an account
                    so your session stays private to you.
                </p>
            </div>
            """,
        )

    # ------------------------------------------------------------ page CSS
    _html(
        f"""
        <style>
            [data-testid="stHeader"] {{
                background: transparent !important; height: 1.5rem !important;
                pointer-events: none;
            }}
            [data-testid="stHeader"] button {{ pointer-events: auto; }}
            [data-testid="stToolbar"] {{ display: none !important; }}
            [data-testid="stDecoration"] {{ display: none !important; }}
            #MainMenu, [data-testid="stMainMenu"] {{ display: none !important; }}
            .block-container {{
                padding: 0 1.5rem 1rem 1.5rem !important;
                max-width: 100% !important;
            }}
            [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] {{
                row-gap: 0.6rem !important;
            }}
            [data-testid="stElementContainer"]:has(style) {{ display: none !important; }}

            .stApp {{
                background:
                    radial-gradient(52rem 34rem at 88% 6%, #FCE0D2 0%, rgba(252,224,210,0) 60%),
                    radial-gradient(46rem 30rem at 2% 96%, #FCE7DC 0%, rgba(252,231,220,0) 55%),
                    radial-gradient(rgba(31,41,55,0.05) 1px, transparent 1.5px) 0 0/22px 22px,
                    #FFFCFA;
            }}

            /* buttons */
            .stButton > button {{
                border-radius: 10px !important;
                font-weight: 700 !important;
                border: 1px solid {LINE} !important;
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
            .linkbtn > button {{
                background: none !important; border: none !important;
                box-shadow: none !important; color: {CORAL} !important;
                padding: 0 !important; height: auto !important;
                font-weight: 600 !important;
            }}
            .linkbtn > button:hover {{
                transform: none !important; text-decoration: underline;
                box-shadow: none !important;
            }}

            /* navbar */
            .anav {{ padding: 0.9rem 0 0.8rem 0; }}
            .brand {{ display:flex; align-items:center; gap:0.45rem; }}
            .brand .logo {{ color:{CORAL}; font-size:1.15rem; }}
            .brand .name {{ font-weight:800; font-size:1.25rem; color:{NAVY}; letter-spacing:-0.3px; }}
            .menu {{
                display:flex; justify-content:center; gap:2.2rem;
                font-size:0.9rem; font-weight:600; color:{SLATE};
            }}
            .menu span:hover {{ color:{CORAL}; }}

            /* hero left */
            .abadge {{
                display:inline-block; margin-top:2.2rem;
                border-radius:999px; background:{CORAL_SOFT}; color:{CORAL};
                font-size:0.68rem; font-weight:700; letter-spacing:1.4px;
                padding:0.42rem 1.1rem;
            }}
            h1.ahero {{
                font-size:3.3rem; line-height:1.08; font-weight:800;
                color:{NAVY}; letter-spacing:-1.5px; margin:1.1rem 0 0 0;
            }}
            h1.ahero .accent {{ color:{CORAL}; font-weight:800; }}
            .asub {{
                color:{SLATE}; font-size:1.02rem; line-height:1.6;
                margin-top:1.1rem; max-width:30rem;
            }}
            .afeats {{ display:flex; flex-direction:column; gap:1.15rem; margin-top:2.1rem; }}
            .afeat {{ display:flex; gap:0.95rem; align-items:flex-start; }}
            .afeat .fico {{
                width:2.7rem; height:2.7rem; border-radius:12px; flex-shrink:0;
                background:{CORAL_SOFT}; display:flex; align-items:center;
                justify-content:center; font-size:1.15rem;
            }}
            .afeat .t {{ font-size:1rem; font-weight:800; color:{INK}; }}
            .afeat .d {{ font-size:0.85rem; color:{SLATE}; margin-top:0.12rem; }}
            .illu {{ margin-top:2rem; position:relative; }}
            .hand {{
                font-family: 'Segoe Script', 'Bradley Hand', cursive;
                color:{SLATE}; font-size:0.95rem; font-style:italic;
            }}
            .hand-note {{ position:absolute; top:-0.4rem; right:8%; text-align:center; }}
            .hand-note .arrow {{ color:{CORAL}; font-size:1.3rem; display:block; }}

            /* auth card */
            .auth-card-flag {{ display:none; }}
            [data-testid="stColumn"]:has(.auth-card-flag) > div:first-child {{
                background:#FFFFFF;
                border:1px solid {LINE};
                border-radius:20px;
                box-shadow:0 28px 70px rgba(31,41,55,0.12);
                padding:1.9rem 2.1rem 1.7rem 2.1rem;
                margin-top:1.4rem;
            }}
            .acard-head {{ text-align:center; margin-bottom:1.15rem; }}
            .acard-head h2 {{ font-size:1.75rem; font-weight:800; color:{NAVY}; margin:0; letter-spacing:-0.5px; }}
            .acard-head p {{ color:{SLATE}; font-size:0.92rem; margin:0.45rem 0 0 0; }}
            /* Streamlit pulls the tabs row up over the header — push it down */
            [data-testid="stColumn"]:has(.auth-card-flag)
                [data-testid="stHorizontalBlock"] {{
                margin-top: 0.35rem !important;
            }}
            .or-row {{
                display:flex; align-items:center; gap:0.9rem;
                color:{MUTED}; font-size:0.82rem; margin:1.15rem 0;
            }}
            .or-row::before, .or-row::after {{
                content:""; flex:1; height:1px; background:{LINE};
            }}
            .newrow {{
                text-align:center; color:{SLATE}; font-size:0.88rem;
                display:flex; justify-content:center; gap:0.4rem; align-items:center;
            }}

            /* inputs + form polish */
            .stTextInput label {{ font-weight:600 !important; color:{INK} !important; }}
            .stTextInput input {{
                border-radius:10px !important; border:1px solid {LINE} !important;
                padding:0.55rem 0.9rem !important;
            }}
            .stTextInput input:focus {{
                border-color:{CORAL} !important;
                box-shadow:0 0 0 3px rgba(245,80,54,0.12) !important;
            }}
            .stFormSubmitButton > button {{
                border-radius:10px !important; padding:0.6rem 1rem !important;
            }}

            /* footer */
            .afooter {{
                margin-top:2.2rem; border-top:1px solid {LINE};
                padding:1rem 0 0.4rem 0; display:flex;
                justify-content:space-between; color:{MUTED}; font-size:0.78rem;
            }}

            @media (max-width: 900px) {{
                h1.ahero {{ font-size:2.3rem; letter-spacing:-1px; }}
                .menu {{ display:none; }}
                .block-container {{ padding: 0 1rem 1rem 1rem !important; }}
                [data-testid="stColumn"]:has(.auth-card-flag) > div:first-child {{
                    margin-top:0.4rem; padding:1.4rem 1.3rem 1.3rem 1.3rem;
                }}
            }}
        </style>
        """,
    )

    # ------------------------------------------------------------- navbar
    nav_l, nav_m, nav_r = st.columns([1.2, 2.1, 1.9], vertical_alignment="center")
    with nav_l:
        _html(
            f"""
            <div class="brand">
                <span class="logo">🔻</span>
                <span class="name">Salesight</span>
            </div>
            """,
        )
    with nav_m:
        _html(
            """
            <div class="menu">
                <span>Features</span><span>Pricing</span>
                <span>Docs</span><span>About</span>
            </div>
            """,
        )
    with nav_r:
        g1, g2 = st.columns([1, 1], gap="small")
        with g1:
            nav_guest = st.button("Continue as Guest", use_container_width=True)
        with g2:
            nav_started = st.button("Get Started", type="primary", use_container_width=True)
    if nav_guest:
        on_success()
        st.rerun()
    if nav_started:
        st.session_state.auth_mode = "signup"
        st.rerun()

    # ---------------------------------------------------------- hero grid
    hero_l, hero_r = st.columns([1.06, 0.96], gap="large")

    # ---------------------------------------------------------- left hero
    with hero_l:
        _html(
            f"""
            <div>
                <span class="abadge">SALES ANALYTICS, SIMPLIFIED</span>
                <h1 class="ahero">Turn your sales data<br>into
                    <span class="accent">clear decisions</span></h1>
                <p class="asub">Upload your sales data, explore trends, uncover
                opportunities and make smarter decisions with Salesight.</p>
                <div class="afeats">
                    <div class="afeat">
                        <div class="fico">📊</div>
                        <div><div class="t">Easy Analysis</div>
                        <div class="d">Upload your CSV and get instant insights.</div></div>
                    </div>
                    <div class="afeat">
                        <div class="fico">🥧</div>
                        <div><div class="t">Interactive Dashboards</div>
                        <div class="d">Visualize your sales data beautifully.</div></div>
                    </div>
                    <div class="afeat">
                        <div class="fico">💡</div>
                        <div><div class="t">Data-Driven Decisions</div>
                        <div class="d">Find trends, top products and growth opportunities.</div></div>
                    </div>
                </div>
                <div class="illu">
                    <div class="hand hand-note">From raw data
                        <span class="arrow">↘</span> to real insights</div>
                    <svg viewBox="0 0 460 250" width="100%" style="max-width:29rem;">
                        <!-- decorative illustration: shapes only, no data values -->
                        <rect x="18" y="30" width="300" height="200" rx="14"
                              fill="#FFFFFF" stroke="{LINE}"/>
                        <rect x="38" y="52" width="60" height="9" rx="4.5" fill="{CORAL_SOFT}"/>
                        <rect x="38" y="72" width="240" height="8" rx="4" fill="#F5F0EB"/>
                        <rect x="60" y="150" width="26" height="52" rx="5" fill="{CORAL_SOFT}"/>
                        <rect x="100" y="132" width="26" height="70" rx="5" fill="#F8B79F"/>
                        <rect x="140" y="158" width="26" height="44" rx="5" fill="{CORAL_SOFT}"/>
                        <rect x="180" y="118" width="26" height="84" rx="5" fill="{CORAL}"/>
                        <rect x="220" y="140" width="26" height="62" rx="5" fill="#F8B79F"/>
                        <rect x="260" y="100" width="26" height="102" rx="5" fill="{CORAL}"/>
                        <polyline points="46,120 96,102 146,112 196,84 246,94 286,70"
                                  fill="none" stroke="{CORAL}" stroke-width="3"
                                  stroke-linecap="round" stroke-linejoin="round"
                                  opacity="0.55"/>
                        <rect x="336" y="70" width="112" height="112" rx="14"
                              fill="#FFFFFF" stroke="{LINE}"/>
                        <circle cx="392" cy="126" r="34" fill="none"
                                stroke="{CORAL_SOFT}" stroke-width="15"/>
                        <path d="M 392 92 A 34 34 0 0 1 424 138"
                              fill="none" stroke="{CORAL}" stroke-width="15"
                              stroke-linecap="round"/>
                        <rect x="60" y="52" width="8" height="9" rx="4" fill="{CORAL}"/>
                    </svg>
                    <div class="hand" style="margin-top:0.6rem; margin-left:4%;">
                        Analyze.<br>&nbsp;Visualize.<br>&nbsp;&nbsp;Grow.
                        <span style="color:{CORAL};">⌒</span>
                    </div>
                </div>
            </div>
            """,
        )

    # --------------------------------------------------------- auth card
    with hero_r:
        _html('<div class="auth-card-flag"></div>')
        _html(
            """
            <div class="acard-head">
                <h2>Welcome to Salesight</h2>
                <p>Sign in to your account or create a new one.</p>
            </div>
            """,
        )

        tab1, tab2 = st.columns(2, gap="small")
        with tab1:
            if st.button(
                "Log in",
                key="tab_login",
                type="primary" if mode == "login" else "secondary",
                use_container_width=True,
            ):
                st.session_state.auth_mode = "login"
                st.rerun()
        with tab2:
            if st.button(
                "Sign up",
                key="tab_signup",
                type="primary" if mode == "signup" else "secondary",
                use_container_width=True,
            ):
                st.session_state.auth_mode = "signup"
                st.rerun()

        if mode == "login":
            with st.form("login_form", clear_on_submit=False, border=False):
                email_l = st.text_input("Email", key="li_email", placeholder="you@example.com")
                password_l = st.text_input(
                    "Password", type="password", key="li_password", placeholder="Your password"
                )
                submitted_l = st.form_submit_button(
                    "Log in", type="primary", use_container_width=True
                )
            f1, f2 = st.columns([1.4, 1])
            with f1:
                forgot = st.button("Forgot password?", key="forgot_btn")
            if forgot:
                st.info(
                    "Password reset is coming soon. For now, please create a new "
                    "account or continue as guest."
                )
            if submitted_l:
                error = auth.login_user(email_l.strip(), password_l)
                if error:
                    st.error(error)
                else:
                    st.session_state.page = "upload"
                    st.query_params.update({"page": "upload"})
                    st.toast("Welcome back!", icon="👋")
                    st.rerun()
        else:
            with st.form("signup_form", clear_on_submit=False, border=False):
                full_name = st.text_input(
                    "Full Name", key="su_name", placeholder="Enter your full name"
                )
                email = st.text_input("Email", key="su_email", placeholder="Enter your email")
                password = st.text_input(
                    "Password", type="password", key="su_password",
                    placeholder="Enter your password (at least 6 characters)",
                )
                confirm = st.text_input(
                    "Confirm Password", type="password", key="su_confirm",
                    placeholder="Confirm your password",
                )
                submitted = st.form_submit_button(
                    "Create account", type="primary", use_container_width=True
                )
            if submitted:
                error = auth.signup_user(email.strip(), password, confirm, full_name)
                if error:
                    st.error(error)
                else:
                    st.session_state.page = "upload"
                    st.query_params.update({"page": "upload"})
                    st.toast("Account created — welcome to Salesight!", icon="✅")
                    st.rerun()

        _html('<div class="or-row">or</div>')

        if st.button(
            "👤 Continue as Guest — Try the Demo Dataset", use_container_width=True
        ):
            on_success()
            st.rerun()

        # Cancel button — return to previous page if coming from upload gate
        if st.session_state.get("auth_notice") == "upload":
            if st.button("← Cancel and go back", use_container_width=True, key="auth_cancel"):
                if st.session_state.get("df_source"):
                    st.session_state.page = "app"
                    st.query_params.update({"page": "dashboard", "source": st.session_state.df_source})
                else:
                    st.session_state.page = "landing"
                    st.query_params.update({"page": ""})
                st.rerun()

        _html(
            f"""
            <div class="newrow" style="margin-top:1.05rem;">
                <span>{'Already have an account?' if mode == 'signup' else 'New to Salesight?'}</span>
            </div>
            """,
        )
        switch_label = "Log in instead" if mode == "signup" else "Create an account"
        if st.button(switch_label, key="switch_mode_btn"):
            st.session_state.auth_mode = "signup" if mode == "login" else "login"
            st.rerun()

    # ------------------------------------------------------------- footer
    _html(
        """
        <div class="afooter">
            <span>© 2026 Salesight. All rights reserved.</span>
            <span>A smarter way to understand your sales data.</span>
        </div>
        """,
    )
