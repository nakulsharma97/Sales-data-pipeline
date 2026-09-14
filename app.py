"""
Salesight — Sales Analytics (Streamlit).

Flow:
    Landing page
      ├─ "Try Demo Dataset"  → MySQL-backed demo dashboard (no login)
      └─ "Get Started"       → Signup / Login → Upload CSV → Analysis

Uploaded CSVs are validated, cleaned with the shared ETL logic and analyzed
in memory only — never written to the shared database.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import auth  # noqa: E402
from views import auth_view, dashboard, landing, upload_view  # noqa: E402

st.set_page_config(
    page_title="Salesight — Sales Analytics",
    page_icon="📊",
    layout="wide",
    # "auto": expanded on desktop (filters visible), collapsed drawer +
    # floating button on mobile — right behavior for a filter-heavy dashboard
    initial_sidebar_state="auto",
)

# Hide Streamlit chrome (Deploy button, kebab menu) on every page
st.markdown(
    """
    <style>
        [data-testid="stToolbar"] { display: none !important; }
        [data-testid="stDecoration"] { display: none !important; }
        #MainMenu, [data-testid="stMainMenu"] { display: none !important; }
        /* The header hosts the sidebar "expand filters" arrow on the
           dashboards: keep it transparent + click-through (buttons stay
           clickable) instead of hiding or squashing it. */
        [data-testid="stHeader"] {
            background: transparent; height: 1.5rem; pointer-events: none;
        }
        [data-testid="stHeader"] button { pointer-events: auto; }
        /* Style-only markdown blocks render invisible zero-height containers
           that still consume layout row-gap — hide their wrappers.
           Safe: <style> rules apply even when the element is display:none. */
        [data-testid="stElementContainer"]:has(style) { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Session defaults
for key, value in {"page": "landing", "df_source": None, "user": None,
                   "filters_visible": True}.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ------------------------------------------------------------------- top bar
def render_topbar(active=None):
    """App navbar: logo · Home · Upload CSV (active state) · user · logout.

    Deliberately has NO bottom border/divider — the navbar blends into the
    page background (per design spec).
    """
    st.markdown(
        f"""
        <style>
            .stopbar {{
                padding: 0.8rem 0 0.5rem 0;
                border-bottom: none !important;
                box-shadow: none !important;
            }}
            .brand {{ display:flex; align-items:center; gap:0.45rem; }}
            .brand .logo {{ color:#F55036; font-size:1.15rem; }}
            .brand .name {{ font-weight:800; font-size:1.25rem; color:#111827; letter-spacing:-0.3px; }}
            .suser {{
                display:flex; align-items:center; gap:0.6rem;
                justify-content:flex-end; min-height:2.6rem;
                width:fit-content; margin-left:auto;
                background:#FFFFFF; border:1px solid #F3ECE7;
                border-radius:12px; padding:0.32rem 0.75rem 0.32rem 0.38rem;
                box-shadow:0 2px 10px rgba(31,41,55,0.06);
            }}
            .suser .uav {{
                width:2.1rem; height:2.1rem; border-radius:50%; flex-shrink:0;
                background:#F55036; color:#fff; display:flex;
                align-items:center; justify-content:center;
                font-size:0.78rem; font-weight:800;
                box-shadow:0 3px 8px rgba(245,80,54,0.3);
            }}
            .suser .uinfo {{
                display:flex; flex-direction:column; min-width:0;
                line-height:1.3; gap:1px;
            }}
            .suser .uname {{
                font-weight:800; color:#111827; font-size:0.85rem;
                max-width:10.5rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
            }}
            .suser .uemail {{
                color:#6B7280; font-size:0.72rem;
                max-width:10.5rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
            }}
            .suser .chev {{
                color:#9CA3AF; font-size:0.8rem; flex-shrink:0; margin-left:0.15rem;
            }}
            @media (max-width: 1000px) {{
                .suser .uemail, .suser .chev {{ display:none; }}
            }}
            .sguest {{
                display:flex; align-items:center;
                width:fit-content; margin-left:auto;
                background:#F550360D; color:#F55036; border:1px solid #F5503633;
                border-radius:999px; padding:0.3rem 0.85rem;
                font-size:0.78rem; font-weight:700; white-space:nowrap;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    c_brand, c_home, c_up, c_user, c_out = st.columns(
        [1.1, 0.66, 0.92, 1.72, 0.6], vertical_alignment="center"
    )
    with c_brand:
        st.markdown(
            '<div class="stopbar"><div class="brand">'
            '<span class="logo">🔻</span><span class="name">Salesight</span>'
            "</div></div>",
            unsafe_allow_html=True,
        )
    with c_home:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()
    with c_up:
        if st.button(
            "📤 Upload CSV",
            type="primary" if active == "upload" else "secondary",
            use_container_width=True,
        ):
            go_upload_gated()
    user = auth.current_user()
    with c_user:
        if user:
            name = auth.display_name(user)
            initial = name[:1].upper()
            email = user.get("email", "")
            st.markdown(
                '<div class="stopbar"><div class="suser">'
                f'<span class="uav">{initial}</span>'
                '<span class="uinfo">'
                f'<span class="uname">{name}</span>'
                f'<span class="uemail">{email}</span>'
                '</span>'
                '<span class="chev">⌄</span>'
                "</div></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="stopbar"><div class="sguest">👤 Guest mode</div></div>',
                unsafe_allow_html=True,
            )
    with c_out:
        if user:
            if st.button("🚪 Log out", use_container_width=True):
                auth.logout()
                st.session_state.page = "landing"
                st.rerun()


# ------------------------------------------------------------------- router
def go_demo():
    st.session_state.df_source = "demo"
    st.session_state.page = "app"


def go_auth():
    st.session_state.page = "auth"


def go_upload_gated():
    """Upload CSV requires an account: guests are routed to the login screen
    with a clear notice; authenticated users go straight to the uploader."""
    if auth.current_user() is None:
        st.session_state.auth_notice = "upload"
        st.session_state.page = "auth"
    else:
        st.session_state.page = "upload"
    st.rerun()


def go_upload():
    """Landing CTA — same gate as the navbar button."""
    go_upload_gated()


page = st.session_state.page

if page == "landing":
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    landing.render(on_demo=go_demo, on_get_started=go_auth, on_upload=go_upload)

elif page == "auth":
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    auth_view.render(on_success=go_demo)

elif page == "upload":
    # Safety net: the gated buttons keep guests out, this guards direct state
    if auth.current_user() is None:
        st.session_state.auth_notice = "upload"
        st.session_state.page = "auth"
        st.rerun()
    render_topbar(active="upload")
    upload_view.render()

elif page == "app":
    render_topbar(active="app")
    if st.session_state.df_source == "uploaded":
        dashboard.render_uploaded_dashboard()
    else:
        dashboard.render_demo_dashboard()

else:
    st.session_state.page = "landing"
    st.rerun()
