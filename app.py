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


# ---------------------------------------------------------------- URL routing
# Every page maps to a URL query string so the browser back/forward
# buttons work.  Streamlit re-runs the script on every navigation,
# so reading query_params here is enough to honour the URL state.

# Map between internal page names and URL-safe query-param values.
_PAGE_MAP = {
    "landing": "",
    "auth": "auth",
    "upload": "upload",
    "app": "dashboard",
}
_REVERSE_MAP = {v: k for k, v in _PAGE_MAP.items()}
_REVERSE_MAP[""] = "landing"  # empty query string = landing page


def _sync_page_from_url() -> None:
    """Read ?page=… from the browser URL and apply it to session state.

    Called once at the top of every Streamlit rerun.  When the user clicks
    the browser back / forward button the URL changes and Streamlit re-runs
    this script — the query_param value wins over session_state so the
    browser history works naturally.
    """
    qp = st.query_params
    url_page = qp.get("page", "")          # empty string = landing
    internal = _REVERSE_MAP.get(url_page)    # None → unknown page
    if internal is not None:
        # Honour the source= param for the dashboard page
        if internal == "app":
            st.session_state.df_source = qp.get("source", "demo")
        st.session_state.page = internal
    # If the URL has no recognisable page param the current session_state
    # page is kept (first visit defaults to "landing" via the init block).


def navigate_to(page: str, *, source: str | None = None) -> None:
    """Programmatic navigation that updates BOTH session state AND the
    browser URL so back/forward buttons keep working.

    Parameters
    ----------
    page : str
        Internal page name ("landing", "auth", "upload", "app").
    source : str | None
        Only for "app": "demo" or "uploaded".
    """
    st.session_state.page = page
    if source is not None:
        st.session_state.df_source = source

    # Build query params for the URL bar.  Clear every existing param first
    # so navigating to the landing page (empty URL) actually removes stale
    # ?page=...&source=... from the browser bar.
    for key in list(st.query_params):
        st.query_params[key] = ""

    if page != "landing":
        st.query_params["page"] = _PAGE_MAP.get(page, "")
    if page == "app" and source:
        st.query_params["source"] = source

    st.rerun()


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
                padding: 0.55rem 0;
                border-bottom: 1px solid #F3ECE7 !important;
                box-shadow: none !important;
                margin-bottom: 0.6rem;
            }}
            .brand {{ display:flex; align-items:center; gap:0.4rem; height:2.5rem; }}
            .brand .logo {{ color:#F55036; font-size:1.1rem; }}
            .brand .name {{ font-weight:800; font-size:1.2rem; color:#111827; letter-spacing:-0.3px; }}

            /* every pill in the navbar — Home, Upload CSV, Guest mode —
               shares the same height/radius/padding so the row reads as
               one aligned set instead of mismatched buttons */
            [data-testid="stElementContainer"]:has(.nav-anchor) {{ display:none; }}
            [data-testid="stVerticalBlock"]:has(.home-anchor) button,
            [data-testid="stVerticalBlock"]:has(.upload-anchor) button {{
                height:2.5rem !important; min-height:2.5rem !important;
                border-radius:10px !important; font-weight:700 !important;
                font-size:0.85rem !important;
            }}
            [data-testid="stVerticalBlock"]:has(.home-anchor) button {{
                background:#FFFFFF !important; color:#111827 !important;
                border:1px solid #E7E1DB !important; box-shadow:none !important;
            }}
            [data-testid="stVerticalBlock"]:has(.home-anchor) button:hover {{
                border-color:#F55036 !important; color:#F55036 !important;
                background:#FFF4EC !important;
            }}
            [data-testid="stVerticalBlock"]:has(.upload-anchor) button[kind="primary"] {{
                background:#F55036 !important; color:#FFFFFF !important;
                border:none !important; box-shadow:none !important;
            }}
            [data-testid="stVerticalBlock"]:has(.upload-anchor) button[kind="primary"]:hover {{
                background:#E0432A !important;
            }}
            [data-testid="stVerticalBlock"]:has(.upload-anchor) button[kind="secondary"] {{
                background:#FFFFFF !important; color:#111827 !important;
                border:1px solid #E7E1DB !important; box-shadow:none !important;
            }}
            [data-testid="stVerticalBlock"]:has(.upload-anchor) button[kind="secondary"]:hover {{
                border-color:#F55036 !important; color:#F55036 !important;
                background:#FFF4EC !important;
            }}
            [data-testid="stVerticalBlock"]:has(.logout-anchor) button {{
                height:2.5rem !important; min-height:2.5rem !important;
                background:#FFFFFF !important; color:#111827 !important;
                border:1px solid #E7E1DB !important; border-radius:10px !important;
                font-weight:700 !important; font-size:0.85rem !important;
                box-shadow:none !important;
            }}
            [data-testid="stVerticalBlock"]:has(.logout-anchor) button:hover {{
                border-color:#F55036 !important; color:#F55036 !important;
                background:#FFF4EC !important;
            }}
            .suser {{
                display:flex; align-items:center; gap:0.55rem;
                justify-content:flex-end; height:2.5rem;
                width:fit-content; margin-left:auto;
                background:#FFFFFF; border:1px solid #E7E1DB;
                border-radius:10px; padding:0 0.7rem 0 0.32rem;
            }}
            .suser .uav {{
                width:1.85rem; height:1.85rem; border-radius:50%; flex-shrink:0;
                background:#F55036; color:#fff; display:flex;
                align-items:center; justify-content:center;
                font-size:0.72rem; font-weight:800;
            }}
            .suser .uinfo {{
                display:flex; flex-direction:column; min-width:0;
                line-height:1.25; gap:1px;
            }}
            .suser .uname {{
                font-weight:700; color:#111827; font-size:0.82rem;
                max-width:10.5rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
            }}
            .suser .uemail {{
                color:#6B7280; font-size:0.7rem;
                max-width:10.5rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
            }}
            .suser .chev {{
                color:#9CA3AF; font-size:0.75rem; flex-shrink:0; margin-left:0.1rem;
            }}
            @media (max-width: 1000px) {{
                .suser .uemail, .suser .chev {{ display:none; }}
            }}
            .sguest {{
                display:flex; align-items:center; justify-content:center;
                height:2.5rem; width:fit-content; margin-left:auto;
                background:#FFF4EC; color:#F55036; border:1px solid #F5D6C8;
                border-radius:10px; padding:0 0.9rem;
                font-size:0.8rem; font-weight:700; white-space:nowrap;
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
        st.markdown('<span class="nav-anchor home-anchor"></span>',
                    unsafe_allow_html=True)
        if st.button("🏠 Home", use_container_width=True):
            navigate_to("landing")
    with c_up:
        st.markdown('<span class="nav-anchor upload-anchor"></span>',
                    unsafe_allow_html=True)
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
            st.markdown('<span class="nav-anchor logout-anchor"></span>',
                        unsafe_allow_html=True)
            if st.button("🚪 Log out", use_container_width=True):
                auth.logout()
                navigate_to("landing")


# ------------------------------------------------------------------- router
def go_demo():
    navigate_to("app", source="demo")


def go_auth():
    navigate_to("auth")


def go_upload_gated():
    """Upload CSV requires an account: guests are routed to the login screen
    with a clear notice; authenticated users go straight to the uploader."""
    if auth.current_user() is None:
        st.session_state.auth_notice = "upload"
        navigate_to("auth")
    else:
        navigate_to("upload")


def go_upload():
    """Landing CTA — same gate as the navbar button."""
    go_upload_gated()


# Read URL query params to honour browser back/forward
_sync_page_from_url()

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
        navigate_to("auth")
    render_topbar(active="upload")
    upload_view.render()

elif page == "app":
    render_topbar(active="app")
    if st.session_state.df_source == "uploaded":
        dashboard.render_uploaded_dashboard()
    else:
        dashboard.render_demo_dashboard()

else:
    navigate_to("landing")
