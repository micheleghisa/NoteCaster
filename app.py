import os
import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.db import create_notebook, get_notebooks, delete_notebook
from src.auth import sign_in, sign_up, refresh_session
import extra_streamlit_components as stx
import datetime
from src.document_processor import extract_text, chunk_text
from src.storage import (
    index_document,
    get_indexed_docs,
    get_full_text,
    get_doc_text,
    query_context,
    delete_notebook_index,
)
from src.podcast_generator import generate_podcast, DETAIL_LEVELS_IT, DETAIL_LEVELS_EN
from src.notes_generator import generate_notes, NOTES_TYPES
from src.llm_client import chat_stream

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NoteCaster — Podcast dalle sbobbine",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
*, *::before, *::after { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important; }

/* Hide Streamlit chrome */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; display: none !important; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* Transparent app background — our injected bg shows through */
.stApp, [data-testid="stAppViewContainer"] {
    background: transparent !important;
}

/* Padding-top for the fixed navbar */
.main .block-container, [data-testid="stMainBlockContainer"] {
    padding-top: 76px !important;
    max-width: 1120px !important;
    position: relative !important;
    z-index: 1 !important;
}

/* Trigger buttons are hidden via JS (found by text content) */

/* Primary buttons */
.main .stButton button[kind="primary"] {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%) !important;
    border: none !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 15px rgba(30,58,95,0.35) !important;
    transition: all 0.2s ease !important;
    padding: 0.5rem 1.5rem !important;
}
.main .stButton button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(30,58,95,0.5) !important;
}
.main .stButton button[kind="secondary"] {
    background: rgba(255,255,255,0.8) !important;
    border: 1.5px solid #1e3a5f !important;
    color: #1e3a5f !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}

.stDownloadButton button {
    background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
    border: none !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(14,165,233,0.35) !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 18px rgba(14,165,233,0.5) !important;
}

[data-testid="stProgressBar"] > div > div > div > div {
    background: linear-gradient(90deg, #1e3a5f, #2563eb, #0ea5e9, #0284c7, #1e3a5f) !important;
    background-size: 200% 100% !important;
    animation: nc-shimmer 2s linear infinite !important;
    border-radius: 999px !important;
}
@keyframes nc-shimmer {
    0%   { background-position: 200% center; }
    100% { background-position: -200% center; }
}

details[data-testid="stExpander"] {
    background: rgba(255,255,255,0.75) !important;
    border: 1px solid rgba(30,58,95,0.2) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(8px) !important;
    box-shadow: 0 2px 10px rgba(30,58,95,0.08) !important;
}

[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed #1e3a5f !important;
    border-radius: 14px !important;
    background: rgba(30,58,95,0.04) !important;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 999px; }

[data-baseweb="select"] > div:first-child {
    border-radius: 12px !important;
    border: 1.5px solid rgba(30,58,95,0.35) !important;
    background: rgba(255,255,255,0.8) !important;
}

.main input[type="text"], .main textarea {
    border-radius: 12px !important;
    border: 1.5px solid rgba(30,58,95,0.3) !important;
    background: rgba(255,255,255,0.9) !important;
}
.main input[type="text"]:focus, .main textarea:focus {
    border-color: #1e3a5f !important;
    box-shadow: 0 0 0 3px rgba(30,58,95,0.12) !important;
}

.podcast-card {
    background: linear-gradient(135deg, rgba(14,165,233,0.08), rgba(2,132,199,0.08));
    border: 1px solid rgba(14,165,233,0.25);
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-top: 0.75rem;
}

.time-pill {
    display: inline-block;
    background: linear-gradient(135deg, rgba(14,165,233,0.15), rgba(2,132,199,0.15));
    border: 1px solid rgba(14,165,233,0.3);
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 0.82rem;
    color: #0369a1;
    font-weight: 600;
    margin-bottom: 0.75rem;
}

/* Mobile: stack columns vertically */
@media (max-width: 767px) {
    [data-testid="stHorizontalBlock"] { flex-direction: column !important; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        width: 100% !important;
        flex: none !important;
        min-width: 100% !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ── NAVBAR + BACKGROUND INJECTION (always present, before auth) ────────────────
components.html("""
<script>
(function () {
    var pd = window.parent.document;
    if (!pd) return;

    /* ── Inject CSS ── */
    if (!pd.getElementById('nc-injected-css')) {
        var style = pd.createElement('style');
        style.id = 'nc-injected-css';
        style.textContent = [
            /* Animated background */
            '.nc-app-bg{position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;background:linear-gradient(135deg,#f0f4f8 0%,#e8f0fe 50%,#f0f4f8 100%);}',
            '.nc-app-bg::before{content:"";position:absolute;top:-50%;right:-20%;width:600px;height:600px;border-radius:50%;background:radial-gradient(circle,rgba(14,165,233,.06) 0%,transparent 70%);animation:ncOrbA 12s ease-in-out infinite;}',
            '.nc-app-bg::after{content:"";position:absolute;bottom:-30%;left:-10%;width:400px;height:400px;border-radius:50%;background:radial-gradient(circle,rgba(30,58,95,.05) 0%,transparent 70%);animation:ncOrbB 15s ease-in-out infinite;}',
            '.nc-shape{position:absolute;border-radius:50%;opacity:.07;}',
            '.nc-shape:nth-child(1){width:80px;height:80px;background:#0ea5e9;top:15%;left:10%;animation:ncPart 18s ease-in-out infinite;}',
            '.nc-shape:nth-child(2){width:50px;height:50px;background:#1e3a5f;top:60%;left:5%;animation:ncPart 22s ease-in-out infinite reverse;}',
            '.nc-shape:nth-child(3){width:100px;height:100px;background:#0ea5e9;top:30%;right:15%;animation:ncPart 20s ease-in-out infinite 3s;}',
            '.nc-shape:nth-child(4){width:40px;height:40px;background:#2563eb;bottom:20%;right:25%;animation:ncPart 16s ease-in-out infinite 5s;}',
            '.nc-shape:nth-child(5){width:60px;height:60px;background:#0ea5e9;top:70%;right:10%;animation:ncPart 24s ease-in-out infinite 2s;}',
            '.nc-shape:nth-child(6){width:30px;height:30px;background:#1e3a5f;top:10%;left:40%;animation:ncPart 14s ease-in-out infinite 4s;}',
            '.nc-pill{position:absolute;border-radius:999px;opacity:.07;}',
            '.nc-pill:nth-child(7){width:60px;height:24px;background:#0ea5e9;top:40%;left:20%;animation:ncPillA 15s ease-in-out infinite;}',
            '.nc-pill:nth-child(8){width:80px;height:20px;background:#2563eb;top:75%;left:35%;animation:ncPillA 18s ease-in-out infinite reverse;}',
            '.nc-dna{position:absolute;top:8%;right:4%;width:60px;height:200px;animation:ncDna 20s ease-in-out infinite;}',
            '@keyframes ncOrbA{0%,100%{transform:translate(0,0) scale(1)}33%{transform:translate(30px,-40px) scale(1.05)}66%{transform:translate(-20px,20px) scale(0.95)}}',
            '@keyframes ncOrbB{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(-40px,30px) scale(1.08)}}',
            '@keyframes ncPart{0%,100%{transform:translate(0,0) rotate(0deg)}25%{transform:translate(30px,-40px) rotate(90deg)}50%{transform:translate(-20px,-80px) rotate(180deg)}75%{transform:translate(-50px,-20px) rotate(270deg)}}',
            '@keyframes ncPillA{0%,100%{transform:translate(0,0) rotate(0deg)}25%{transform:translate(40px,-30px) rotate(45deg)}50%{transform:translate(-20px,-60px) rotate(90deg)}75%{transform:translate(-40px,-10px) rotate(135deg)}}',
            '@keyframes ncDna{0%,100%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(-20px) rotate(5deg)}}',
            /* Navbar */
            '#nc-navbar{position:fixed;top:0;left:0;right:0;z-index:99999;padding:14px 0;transition:all .25s ease;font-family:"Inter",-apple-system,BlinkMacSystemFont,sans-serif;}',
            '#nc-navbar.scrolled{background:rgba(255,255,255,.92);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);box-shadow:0 1px 8px rgba(0,0,0,.06);padding:10px 0;}',
            '.nc-nav-inner{width:100%;max-width:1120px;margin:0 auto;padding:0 24px;display:flex;align-items:center;justify-content:space-between;}',
            '.nc-logo{display:flex;align-items:center;gap:8px;font-size:1.2rem;font-weight:700;color:#0f172a;text-decoration:none;cursor:default;letter-spacing:-.3px;}',
            '.nc-logo span{font-size:1.4rem;}',
            '.nc-nav-links{display:flex;align-items:center;gap:28px;}',
            '.nc-nav-link{font-size:.88rem;font-weight:500;color:#475569;text-decoration:none;cursor:pointer;transition:color .25s ease;background:none;border:none;padding:0;font-family:inherit;}',
            '.nc-nav-link:hover{color:#0f172a;}',
            '.nc-nav-btn{display:inline-flex;align-items:center;gap:6px;padding:9px 20px;background:#2563eb;color:#fff;border:none;border-radius:6px;font-size:.85rem;font-weight:600;cursor:pointer;font-family:inherit;transition:all .3s cubic-bezier(.4,0,.2,1);box-shadow:0 4px 14px rgba(37,99,235,.3);animation:ncNavGlow 3s ease-in-out infinite;}',
            '.nc-nav-btn:hover{background:#1d4ed8;box-shadow:0 6px 24px rgba(37,99,235,.45);transform:translateY(-2px);animation:none;}',
            '@keyframes ncNavGlow{0%,100%{box-shadow:0 4px 14px rgba(37,99,235,.3)}50%{box-shadow:0 4px 28px rgba(37,99,235,.55),0 0 40px rgba(37,99,235,.15)}}',
            '.nc-hamburger{display:none;background:none;border:none;cursor:pointer;padding:8px;color:#1e293b;}',
            '.nc-hamburger svg{width:26px;height:26px;stroke:currentColor;}',
            /* Mobile menu */
            '#nc-mobile-menu{display:none;position:fixed;inset:0;z-index:99998;background:rgba(255,255,255,.98);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);flex-direction:column;align-items:center;justify-content:center;gap:24px;font-family:"Inter",sans-serif;}',
            '#nc-mobile-menu.open{display:flex;}',
            '.nc-mob-link{font-size:1.2rem;font-weight:500;color:#1e293b;text-decoration:none;cursor:pointer;background:none;border:none;font-family:inherit;}',
            '.nc-mob-close{position:absolute;top:20px;right:24px;background:none;border:none;font-size:1.6rem;cursor:pointer;color:#1e293b;}',
            '@media(max-width:768px){.nc-nav-links{display:none!important}.nc-hamburger{display:block!important}}'
        ].join('');
        pd.head.appendChild(style);
    }

    function hideTriggerButtons() {
        var targets = ['☰ Notebook', '☰ Crea', '☰ Sbobine'];
        var btns = pd.querySelectorAll('button');
        for (var b = 0; b < btns.length; b++) {
            if (targets.indexOf((btns[b].textContent || '').trim()) >= 0) {
                var row = btns[b].closest('[data-testid="stHorizontalBlock"]');
                if (row && !row._ncHidden) {
                    row.style.position = 'fixed';
                    row.style.left = '-9999px';
                    row.style.top = '0';
                    row._ncHidden = true;
                }
            }
        }
    }

    function injectElements() {
        hideTriggerButtons();

        /* Background */
        if (!pd.getElementById('nc-app-bg')) {
            var bg = pd.createElement('div');
            bg.id = 'nc-app-bg';
            bg.className = 'nc-app-bg';
            bg.innerHTML = '<div class="nc-shape"></div><div class="nc-shape"></div><div class="nc-shape"></div><div class="nc-shape"></div><div class="nc-shape"></div><div class="nc-shape"></div><div class="nc-pill"></div><div class="nc-pill"></div>' +
                '<svg class="nc-dna" viewBox="0 0 60 200" fill="none" xmlns="http://www.w3.org/2000/svg">' +
                '<path d="M30 0 C10 25,50 50,30 75 C10 100,50 125,30 150 C10 175,50 200,30 200" stroke="#0ea5e9" stroke-width="1.5" opacity="0.2"/>' +
                '<path d="M30 0 C50 25,10 50,30 75 C50 100,10 125,30 150 C50 175,10 200,30 200" stroke="#2563eb" stroke-width="1.5" opacity="0.15"/>' +
                '</svg>';
            pd.body.insertBefore(bg, pd.body.firstChild);
        }

        /* Navbar */
        if (!pd.getElementById('nc-navbar')) {
            var nav = pd.createElement('nav');
            nav.id = 'nc-navbar';
            nav.innerHTML =
                '<div class="nc-nav-inner">' +
                  '<div class="nc-logo"><span>🎙️</span> NoteCaster</div>' +
                  '<div class="nc-nav-links">' +
                    '<button class="nc-nav-link nc-open-nb" data-nc-action="notebooks">📚 I tuoi Notebook</button>' +
                    '<button class="nc-nav-link nc-open-nb" data-nc-action="indexed">Sbobine indicizzate</button>' +
                    '<button class="nc-nav-btn nc-open-nb" data-nc-action="create">+ Crea Notebook</button>' +
                  '</div>' +
                  '<button class="nc-hamburger" id="nc-hamburger" aria-label="Menu">' +
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
                      '<path d="M3 12h18M3 6h18M3 18h18"/>' +
                    '</svg>' +
                  '</button>' +
                '</div>';
            var bgEl = pd.getElementById('nc-app-bg');
            pd.body.insertBefore(nav, bgEl ? bgEl.nextSibling : pd.body.firstChild);

            /* Mobile menu */
            var mob = pd.createElement('div');
            mob.id = 'nc-mobile-menu';
            mob.innerHTML =
                '<button class="nc-mob-close" id="nc-mob-close">✕</button>' +
                '<button class="nc-mob-link nc-open-nb" data-nc-action="notebooks">📚 I tuoi Notebook</button>' +
                '<button class="nc-mob-link nc-open-nb" data-nc-action="indexed">Sbobine indicizzate</button>' +
                '<button class="nc-mob-link nc-open-nb" data-nc-action="create">+ Crea Notebook</button>';
            pd.body.appendChild(mob);

            pd.getElementById('nc-hamburger').addEventListener('click', function () {
                pd.getElementById('nc-mobile-menu').classList.add('open');
            });
            pd.getElementById('nc-mob-close').addEventListener('click', function () {
                pd.getElementById('nc-mobile-menu').classList.remove('open');
            });

            pd.querySelectorAll('.nc-open-nb').forEach(function (el) {
                el.addEventListener('click', function () {
                    pd.getElementById('nc-mobile-menu').classList.remove('open');
                    clickNotebookBtn(pd, el.getAttribute('data-nc-action') || 'notebooks');
                });
            });
        }

        /* Scroll effect */
        if (!window.parent._ncScrollAttached) {
            window.parent._ncScrollAttached = true;
            window.parent.addEventListener('scroll', function () {
                var nav = pd.getElementById('nc-navbar');
                if (nav) nav.classList.toggle('scrolled', window.parent.scrollY > 50);
            });
        }
    }

    function clickNotebookBtn(pd, action) {
        var targetMap = {
            'notebooks': '☰ Notebook',
            'create':    '☰ Crea',
            'indexed':   '☰ Sbobine'
        };
        var target = targetMap[action] || '☰ Notebook';
        var buttons = pd.querySelectorAll('button');
        for (var i = 0; i < buttons.length; i++) {
            if ((buttons[i].textContent || '').trim() === target) {
                buttons[i].click();
                return true;
            }
        }
        return false;
    }

    injectElements();

    /* MutationObserver: hide trigger buttons the instant Streamlit adds them to the DOM,
       before the browser paints — works on first login and every subsequent rerun */
    if (!window.parent._ncObserver) {
        window.parent._ncObserver = new MutationObserver(function() {
            hideTriggerButtons();
        });
        window.parent._ncObserver.observe(pd.body, { childList: true, subtree: true });
    }

    setTimeout(injectElements, 400);
    setTimeout(injectElements, 1500);
    setTimeout(injectElements, 3500);
})();
</script>
""", height=0, scrolling=False)

# ── Auth ───────────────────────────────────────────────────────────────────────
_cookie_mgr = stx.CookieManager(key="nc_cookie_manager")

# CookieManager needs one render cycle before .set() is safe.
# Only delete _pending_cookie on successful set — don't lose the token on failure.
if "_pending_cookie" in st.session_state:
    pending = st.session_state["_pending_cookie"]
    try:
        _cookie_mgr.set(
            "nc_refresh", pending,
            expires_at=datetime.datetime.now() + datetime.timedelta(days=30),
        )
        del st.session_state["_pending_cookie"]
    except Exception:
        pass  # Retry on next render — pending stays in session_state

if "user" not in st.session_state:
    # CookieManager needs one render cycle to read browser cookies via JS.
    if not st.session_state.get("_cookie_init"):
        st.session_state["_cookie_init"] = True
        st.rerun()

    saved_token = _cookie_mgr.get("nc_refresh")
    if saved_token:
        try:
            res = refresh_session(saved_token)
            if res and res.user:
                st.session_state["user"] = {"id": str(res.user.id), "email": res.user.email}
                if res.session:
                    _cookie_mgr.set(
                        "nc_refresh", res.session.refresh_token,
                        expires_at=datetime.datetime.now() + datetime.timedelta(days=30),
                    )
                st.rerun()
        except Exception:
            _cookie_mgr.delete("nc_refresh")

if "user" not in st.session_state:
    st.markdown("""
    <div style="max-width:400px; margin: 5rem auto 0; text-align:center;">
        <div style="font-size:2.8rem; margin-bottom:0.4rem;">🎙️</div>
        <h1 style="
            font-size:2rem; font-weight:900; margin:0 0 0.3rem;
            background: linear-gradient(135deg, #1e3a5f, #2563eb, #0ea5e9);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
        ">NoteCaster</h1>
        <p style="color:#64748b; font-size:0.9rem; margin-bottom:2rem;">
            Accedi o crea un account per iniziare
        </p>
    </div>
    """, unsafe_allow_html=True)

    _col = st.columns([1, 2, 1])[1]
    with _col:
        _mode = st.radio("", ["Accedi", "Registrati"], horizontal=True, label_visibility="collapsed")
        _email = st.text_input("Email", placeholder="nome@esempio.com")
        _pwd = st.text_input("Password", type="password", placeholder="Almeno 6 caratteri")

        if st.button("Entra" if _mode == "Accedi" else "Crea account", type="primary", use_container_width=True):
            if not _email or not _pwd:
                st.error("Inserisci email e password.")
            else:
                _login_ok = False
                try:
                    if _mode == "Accedi":
                        res = sign_in(_email, _pwd)
                    else:
                        res = sign_up(_email, _pwd)

                    if res.user is None:
                        st.error("Credenziali non valide o account già esistente.")
                    else:
                        st.session_state["user"] = {
                            "id": str(res.user.id),
                            "email": res.user.email,
                        }
                        if res.session:
                            st.session_state["_pending_cookie"] = res.session.refresh_token
                        _login_ok = True
                except Exception as e:
                    st.error(f"Errore: {e}")
                # st.rerun() must be outside try/except: in Streamlit ≥1.27
                # RerunException subclasses Exception and would be swallowed,
                # silently preventing the rerun from firing.
                if _login_ok:
                    st.rerun()
    st.stop()

user = st.session_state["user"]

# ── Mobile notebook manager dialog ────────────────────────────────────────────
@st.dialog("📚 Notebook", width="large")
def _notebook_manager_dialog():
    _u = st.session_state["user"]

    # User info + logout
    _ucol, _lcol = st.columns([4, 1])
    _ucol.markdown(
        f'<p style="font-size:0.78rem;color:#64748b;margin:4px 0;">👤 {_u["email"]}</p>',
        unsafe_allow_html=True,
    )
    if _lcol.button("Esci", key="dlg_logout", use_container_width=True):
        _cookie_mgr.delete("nc_refresh")
        del st.session_state["user"]
        st.session_state.active_notebook = None
        st.session_state.chat_history = []
        st.rerun()

    # Section selector (driven by which navbar button was clicked)
    _section = st.radio(
        "",
        options=["📚 I tuoi Notebook", "➕ Crea Notebook", "📁 Sbobine indicizzate"],
        index=["notebooks", "create", "indexed"].index(
            st.session_state.get("_dialog_section", "notebooks")
        ),
        horizontal=True,
        label_visibility="collapsed",
        key="dlg_section_radio",
    )
    st.divider()

    # ── Sezione: I tuoi Notebook ──────────────────────────────────────────────
    if _section == "📚 I tuoi Notebook":
        _nbs = get_notebooks(user_id=_u["id"])
        if not _nbs:
            st.info("Nessun notebook. Vai su 'Crea Notebook' per iniziare.")
        else:
            for _nb in _nbs:
                _dcnt = len(get_indexed_docs(_nb["id"]))
                _active = (st.session_state.active_notebook or {}).get("id") == _nb["id"]
                _cn, _cd = st.columns([5, 1])
                if _cn.button(
                    f"{'▶ ' if _active else ''}{_nb['name']} ({_dcnt} doc)",
                    key=f"dlg_nb_{_nb['id']}",
                    type="primary" if _active else "secondary",
                    use_container_width=True,
                ):
                    if not _active:
                        st.session_state.active_notebook = _nb
                        st.rerun()
                if _cd.button("🗑", key=f"dlg_del_{_nb['id']}"):
                    st.session_state[f"dlg_cdel_{_nb['id']}"] = True
                    st.rerun()
                if st.session_state.get(f"dlg_cdel_{_nb['id']}"):
                    st.warning(f"Eliminare '{_nb['name']}'?")
                    _cy, _cn2 = st.columns(2)
                    if _cy.button("Sì, elimina", key=f"dlg_y_{_nb['id']}", type="primary"):
                        delete_notebook(_nb["id"], user_id=_u["id"])
                        delete_notebook_index(_nb["id"])
                        if (st.session_state.active_notebook or {}).get("id") == _nb["id"]:
                            st.session_state.active_notebook = None
                        del st.session_state[f"dlg_cdel_{_nb['id']}"]
                        st.rerun()
                    if _cn2.button("Annulla", key=f"dlg_n_{_nb['id']}"):
                        del st.session_state[f"dlg_cdel_{_nb['id']}"]
                        st.rerun()

    # ── Sezione: Crea Notebook ────────────────────────────────────────────────
    elif _section == "➕ Crea Notebook":
        st.markdown(
            '<p style="font-size:.9rem;color:#64748b;margin-bottom:12px;">'
            'Dai un nome al tuo notebook (es: Cardiologia, Patologia Anno 3…)</p>',
            unsafe_allow_html=True,
        )
        _c1, _c2 = st.columns([3, 1])
        _dlg_name = _c1.text_input(
            "Nome", placeholder="Es: Cardiologia",
            key="dlg_nb_name", label_visibility="collapsed",
        )
        if _c2.button("Crea →", key="dlg_add_nb", use_container_width=True, type="primary"):
            if _dlg_name.strip():
                _nb = create_notebook(_dlg_name.strip(), user_id=_u["id"])
                st.session_state.active_notebook = _nb
                st.session_state["_dialog_section"] = "indexed"
                st.rerun()
            else:
                st.error("Inserisci un nome per il notebook.")

    # ── Sezione: Sbobine indicizzate ──────────────────────────────────────────
    elif _section == "📁 Sbobine indicizzate":
        _anb = st.session_state.active_notebook
        if not _anb:
            st.info("Seleziona prima un notebook dalla sezione 'I tuoi Notebook'.")
        else:
            st.markdown(f"**📁 {_anb['name']}**")
            _indexed = get_indexed_docs(_anb["id"])
            for _d in _indexed:
                st.caption(f"• {_d}")
            if not _indexed:
                st.caption("Nessuna sbobina ancora.")
            _up = st.file_uploader(
                "Carica sbobine", type=["pdf", "docx", "txt", "md"],
                accept_multiple_files=True, key=f"dlg_up_{_anb['id']}",
            )
            if st.button("📥 Indicizza", key="dlg_idx", disabled=not _up, use_container_width=True):
                _prog = st.progress(0)
                _results = []
                for _i, _f in enumerate(_up):
                    _prog.progress((_i + 1) / len(_up))
                    _sfx = Path(_f.name).suffix
                    with tempfile.NamedTemporaryFile(suffix=_sfx, delete=False) as _tmp:
                        _tmp.write(_f.read())
                        _tp = _tmp.name
                    try:
                        _txt = extract_text(_tp)
                        if not _txt.strip():
                            _results.append(f"⚠️ {_f.name}: nessun testo")
                            continue
                        _cks = chunk_text(_txt)
                        _added = index_document(_anb["id"], _f.name, _cks)
                        _results.append(f"✓ {_f.name} ({_added} chunk)")
                    except ValueError as _e:
                        _results.append(f"✗ {_f.name}: {_e}")
                    finally:
                        os.unlink(_tp)
                _prog.empty()
                for _r in _results:
                    if _r.startswith("✓"):
                        st.success(_r)
                    elif _r.startswith("⚠"):
                        st.warning(_r)
                    else:
                        st.error(_r)
                st.rerun()

# ── Session state ──────────────────────────────────────────────────────────────
st.session_state.setdefault("active_notebook", None)
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("last_notebook_id", None)

NB_COLORS = ["#1e3a5f", "#2563eb", "#0ea5e9", "#ea580c", "#db2777", "#d97706"]

# ── MAIN AREA ──────────────────────────────────────────────────────────────────
# Three hidden trigger buttons — clicked by the injected navbar JS with data-nc-action.
# CSS moves them off-screen; JS clicks them by matching button text.
_tc1, _tc2, _tc3 = st.columns(3)
if _tc1.button("☰ Notebook", key="_btn_nb_list"):
    st.session_state["_dialog_section"] = "notebooks"
    _notebook_manager_dialog()
if _tc2.button("☰ Crea", key="_btn_nb_create"):
    st.session_state["_dialog_section"] = "create"
    _notebook_manager_dialog()
if _tc3.button("☰ Sbobine", key="_btn_nb_indexed"):
    st.session_state["_dialog_section"] = "indexed"
    _notebook_manager_dialog()

if not st.session_state.active_notebook:
    st.markdown("""
    <div style="text-align:center; padding: 3rem 1rem 2rem;">
        <div style="font-size: 3.5rem; margin-bottom: 0.5rem;">🎙️</div>
        <h1 style="
            font-size: 3rem; font-weight: 900;
            background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 40%, #0ea5e9 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text; margin: 0 0 0.6rem; letter-spacing: -1.5px;
        ">NoteCaster</h1>
        <p style="font-size: 1.1rem; color: #64748b; max-width: 480px; margin: 0 auto 2.5rem;">
            Trasforma le tue sbobbine in un podcast con due host AI — come NotebookLM, ma gratis e in italiano.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(30,58,95,0.1), rgba(37,99,235,0.15));
                    border: 1px solid rgba(30,58,95,0.25); border-radius: 18px; padding: 1.5rem 1.2rem;
                    text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">1️⃣</div>
            <div style="font-weight: 700; color: #1e293b; font-size: 0.95rem; margin-bottom: 0.4rem;">Crea un notebook</div>
            <div style="font-size: 0.82rem; color: #1d4ed8;">Uno per materia o per esame</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(37,99,235,0.1), rgba(37,99,235,0.15));
                    border: 1px solid rgba(37,99,235,0.25); border-radius: 18px; padding: 1.5rem 1.2rem;
                    text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">2️⃣</div>
            <div style="font-weight: 700; color: #1e293b; font-size: 0.95rem; margin-bottom: 0.4rem;">Carica le sbobine</div>
            <div style="font-size: 0.82rem; color: #1d4ed8;">PDF, DOCX o TXT — anche più file</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(14,165,233,0.1), rgba(2,132,199,0.15));
                    border: 1px solid rgba(14,165,233,0.25); border-radius: 18px; padding: 1.5rem 1.2rem;
                    text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">3️⃣</div>
            <div style="font-weight: 700; color: #0f172a; font-size: 0.95rem; margin-bottom: 0.4rem;">Genera il podcast</div>
            <div style="font-size: 0.82rem; color: #0369a1;">Scegli argomento, livello e scarica l'MP3</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(30,58,95,0.07), rgba(37,99,235,0.1));
        border: 1.5px solid rgba(30,58,95,0.2); border-radius: 14px;
        padding: 1rem 1.5rem; text-align: center; max-width: 400px; margin: 2rem auto 0;
    ">
        <span style="font-size: 1.1rem;">☰</span>
        <span style="font-weight: 700; color: #1e293b; font-size: 0.9rem; margin-left: 0.4rem;">
            Premi <strong>☰</strong> in alto a destra per iniziare
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

active_nb = st.session_state.active_notebook

# Clear chat history when switching notebooks
if st.session_state.last_notebook_id != active_nb["id"]:
    st.session_state.chat_history = []
    st.session_state.last_notebook_id = active_nb["id"]

# ── Notebook header ────────────────────────────────────────────────────────────
nb_doc_count = len(get_indexed_docs(active_nb["id"]))
st.markdown(f"""
<div style="
    background: rgba(255,255,255,0.75); border: 1px solid rgba(30,58,95,0.2);
    border-radius: 18px; padding: 1.25rem 1.75rem; margin-bottom: 1.5rem;
    backdrop-filter: blur(10px); box-shadow: 0 4px 20px rgba(30,58,95,0.08);
    display: flex; align-items: center; gap: 1rem;
">
    <div style="font-size: 2rem;">🎙️</div>
    <div style="flex: 1;">
        <h2 style="
            margin: 0; font-size: 1.6rem; font-weight: 800;
            background: linear-gradient(135deg, #1e3a5f, #2563eb);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text; letter-spacing: -0.5px;
        ">{active_nb['name']}</h2>
        <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">
            {nb_doc_count} sbobina{'e' if nb_doc_count != 1 else ''} indicizzata{'e' if nb_doc_count != 1 else ''}
        </div>
    </div>
    <span style="
        background: linear-gradient(135deg, rgba(14,165,233,0.15), rgba(2,132,199,0.15));
        border: 1px solid rgba(14,165,233,0.35); color: #0369a1;
        font-size: 0.72rem; font-weight: 700; padding: 4px 12px;
        border-radius: 999px; letter-spacing: 0.5px;
    ">✦ PODCAST READY</span>
</div>
""", unsafe_allow_html=True)

tab_chat, tab_podcast = st.tabs(["💬 Chat", "🎙️ Podcast"])

indexed_docs = get_indexed_docs(active_nb["id"])
has_docs = len(indexed_docs) > 0

# ── TAB: Chat ──────────────────────────────────────────────────────────────────
with tab_chat:
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    col_input, col_clear = st.columns([5, 1])
    if col_clear.button("🗑 Pulisci", key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun()

    chat_placeholder = (
        "Fai una domanda sui tuoi documenti..."
        if has_docs else "Carica prima dei documenti nel notebook (tocca ☰ in alto)"
    )
    if prompt := st.chat_input(chat_placeholder):
        if not has_docs:
            st.warning("Carica prima dei documenti nel notebook (tocca ☰ in alto).")
        else:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                context = query_context(active_nb["id"], prompt, n_results=6)
                system = (
                    "Sei un assistente di studio per studenti universitari. "
                    "Rispondi SOLO basandoti sui documenti forniti nel contesto. "
                    "Se l'informazione non è nei documenti, dillo esplicitamente. "
                    "Sii preciso, utile e cita i concetti chiave. "
                    "Usa Markdown per strutturare le risposte complesse."
                )
                messages = [{"role": "system", "content": system}]
                for h in st.session_state.chat_history[-8:]:
                    messages.append({"role": h["role"], "content": h["content"]})
                messages[-1]["content"] = (
                    f"Contesto dai documenti:\n{context}\n\nDomanda: {prompt}"
                )

                response_placeholder = st.empty()
                full_response = ""
                try:
                    for chunk in chat_stream(messages, temperature=0.3):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                    response_placeholder.markdown(full_response)
                except Exception as e:
                    full_response = f"Errore: {e}"
                    response_placeholder.error(full_response)

            st.session_state.chat_history.append(
                {"role": "assistant", "content": full_response}
            )

# ── TAB: Podcast ───────────────────────────────────────────────────────────────
with tab_podcast:
    if not has_docs:
        st.warning("Carica prima dei documenti nel notebook.")
    else:
        col_lang, col_detail = st.columns([1, 2])
        lang = col_lang.selectbox(
            "Lingua",
            ["Auto-detect", "Italiano", "English"],
            key="podcast_lang",
        )
        detail_options = list(DETAIL_LEVELS_EN.keys()) if lang == "English" else list(DETAIL_LEVELS_IT.keys())
        detail_level = col_detail.selectbox(
            "Livello di dettaglio",
            detail_options,
            index=1,
            key="podcast_detail",
        )

        source_options = ["📚 Tutte le sbobine"] + indexed_docs
        source_doc = st.selectbox(
            "Sorgente",
            source_options,
            key="podcast_source",
            help="Seleziona una sbobina specifica o usa tutto il materiale del notebook",
        )

        topic = st.text_input(
            "Argomento (opzionale)",
            placeholder="Es: Stenosi aortica, Shock cardiogeno, Patologie dell'aorta...",
            key="podcast_topic",
            help="Lascia vuoto per coprire tutto il materiale. Specifica un argomento per focalizzare il podcast.",
        )

        _TIME_HINTS = {
            "Panoramica": "~3-5 min",
            "Approfondito": "~12-18 min",
            "Completo": "~15-20 min",
            "Dettagliato (esame)": "~35-40 min",
            "Overview": "~3-5 min",
            "In-depth": "~12-18 min",
            "Complete": "~15-20 min",
            "Detailed (exam)": "~35-40 min",
        }
        st.markdown(
            f'<div class="time-pill">⏱ Durata stimata: {_TIME_HINTS.get(detail_level, "—")}</div>',
            unsafe_allow_html=True,
        )

        if st.button("🎙️ Genera Podcast", type="primary", use_container_width=True):
            lang_map = {"Auto-detect": "auto", "Italiano": "it", "English": "en"}
            lang_code = lang_map[lang]

            if source_doc == "📚 Tutte le sbobine":
                full_text = get_full_text(active_nb["id"])
            else:
                full_text = get_doc_text(active_nb["id"], source_doc)

            if not full_text.strip():
                st.error("Nessun testo disponibile per la sorgente selezionata.")
            else:
                progress_bar = st.progress(0, text="Avvio generazione...")
                status_placeholder = st.empty()

                def audio_progress(done, total):
                    pct = 0.45 + (done / total) * 0.50
                    progress_bar.progress(pct, text=f"Sintesi audio: battuta {done}/{total}...")

                def on_status(msg: str):
                    is_script = "script" in msg.lower() or "segmento" in msg.lower() or "generazione" in msg.lower()
                    if is_script:
                        progress_bar.progress(0.10, text=msg)
                    status_placeholder.info(f"⏳ {msg}")

                try:
                    script, audio_path = generate_podcast(
                        full_text=full_text,
                        notebook_id=active_nb["id"],
                        language=lang_code,
                        topic=topic,
                        detail_level=detail_level,
                        progress_cb=audio_progress,
                        status_cb=on_status,
                    )
                    progress_bar.progress(1.0, text="Podcast pronto!")
                    status_placeholder.success("✅ Podcast generato!")
                    st.session_state["last_podcast_script"] = script
                    st.session_state["last_podcast_path"] = audio_path
                except Exception as e:
                    progress_bar.empty()
                    status_placeholder.error(f"Errore: {e}")

    if "last_podcast_path" in st.session_state and os.path.exists(
        st.session_state["last_podcast_path"]
    ):
        st.markdown('<div class="podcast-card">', unsafe_allow_html=True)
        st.audio(st.session_state["last_podcast_path"])
        with open(st.session_state["last_podcast_path"], "rb") as f:
            st.download_button(
                "⬇️ Scarica MP3",
                data=f,
                file_name=Path(st.session_state["last_podcast_path"]).name,
                mime="audio/mpeg",
            )
        st.markdown('</div>', unsafe_allow_html=True)
        with st.expander("📄 Leggi lo script"):
            st.markdown(st.session_state.get("last_podcast_script", ""))
