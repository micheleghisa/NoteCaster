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
from streamlit_cookies_controller import CookieController
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
    initial_sidebar_state="auto",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
*, *::before, *::after { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important; }
.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #f0f4f8 50%, #e8f4fd 100%) !important;
    background-attachment: fixed !important;
}

#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; display: none; }
[data-testid="stHeader"] { background: transparent !important; }

[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0f172a 0%, #1e293b 40%, #0d1e35 100%) !important;
    border-right: 1px solid rgba(30,58,95,0.4) !important;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] caption { color: #7aa3c4 !important; }
[data-testid="stSidebar"] input[type="text"] {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(30,58,95,0.4) !important;
    border-radius: 10px !important;
    color: #f0f9ff !important;
}
[data-testid="stSidebar"] input[type="text"]::placeholder { color: #64748b !important; }
[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(30,58,95,0.25) !important;
    border-color: rgba(30,58,95,0.6) !important;
}
[data-testid="stSidebar"] .stButton button[kind="primary"] {
    background: linear-gradient(135deg, #1e3a5f, #2563eb) !important;
    border: none !important;
    color: #ffffff !important;
    box-shadow: 0 2px 8px rgba(30,58,95,0.4) !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: rgba(30,58,95,0.12) !important;
    border: 2px dashed rgba(30,58,95,0.5) !important;
    border-radius: 12px !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * { color: #93c5fd !important; }
[data-testid="stSidebar"] hr { border-color: rgba(30,58,95,0.25) !important; }
[data-testid="stSidebar"] .stAlert {
    background: rgba(30,58,95,0.15) !important;
    border: 1px solid rgba(30,58,95,0.3) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}

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
    animation: shimmer 2s linear infinite !important;
    border-radius: 999px !important;
}
@keyframes shimmer {
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

/* ── Responsive sidebar ───────────────────────────────────────── */

/* Desktop ≥ 1024 px: sidebar sempre aperta, nessun bottone toggle */
@media (min-width: 1024px) {
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    [data-testid="stSidebarCollapsed"]       { display: none !important; }
    [data-testid="stSidebar"] {
        transform: none !important;
        min-width: 244px !important;
        visibility: visible !important;
    }
}

/* Tablet 768–1023 px: sidebar collassabile, mostra il bottone toggle */
@media (min-width: 768px) and (max-width: 1023px) {
    [data-testid="stSidebarCollapseButton"] {
        display: flex !important;
        color: #93c5fd !important;
    }
    [data-testid="stSidebarCollapseButton"] svg { fill: #93c5fd !important; }
}

/* Mobile < 768 px: sidebar nascosta di default, hamburger stilizzato */
@media (max-width: 767px) {
    [data-testid="stSidebarCollapseButton"] { display: flex !important; }

    /* Bottone hamburger (appare quando la sidebar è chiusa) */
    [data-testid="collapsedControl"] {
        background: linear-gradient(135deg, #1e3a5f, #2563eb) !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 12px rgba(30,58,95,0.4) !important;
        padding: 4px !important;
    }
    [data-testid="collapsedControl"] svg { fill: #ffffff !important; }

    /* Le colonne Streamlit diventano verticali su mobile */
    [data-testid="stHorizontalBlock"] { flex-direction: column !important; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        width: 100% !important;
        flex: none !important;
        min-width: 100% !important;
    }

    /* Respiro extra in cima al contenuto principale */
    .main .block-container { padding-top: 2rem !important; }
}

/* Hint sidebar: visibilità responsive */
.hint-desktop { display: inline !important; }
.hint-mobile  { display: none !important; }
@media (max-width: 767px) {
    .hint-desktop { display: none !important; }
    .hint-mobile  { display: inline !important; }
}

/* Mobile FAB (Floating Action Button) per aprire il notebook manager.
   Iniettato nel DOM parent via components.html — visibile solo su <1024px. */
#nc-fab {
    position: fixed;
    bottom: 24px;
    right: 20px;
    z-index: 999999;
    width: 58px;
    height: 58px;
    border-radius: 50%;
    border: none;
    background: linear-gradient(135deg, #1e3a5f, #2563eb);
    color: #fff;
    font-size: 24px;
    cursor: pointer;
    display: none;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 20px rgba(30,58,95,0.5);
    transition: transform .15s ease, box-shadow .15s ease;
}
#nc-fab:active { transform: scale(.91); }
@media (max-width: 1023px) { #nc-fab { display: flex !important; } }

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
</style>
""", unsafe_allow_html=True)

# ── Auth ───────────────────────────────────────────────────────────────────────
_cookies = CookieController()

# CookieController needs one render cycle before .set() is safe.
# Handle any token that was deferred from the previous render.
if "_pending_cookie" in st.session_state:
    try:
        _cookies.set("nc_refresh", st.session_state.pop("_pending_cookie"),
                     max_age=30 * 24 * 60 * 60)
    except Exception:
        pass

if "user" not in st.session_state:
    # CookieController needs one render cycle to read browser cookies via JS.
    # On first load the component hasn't fired yet, so we force a single rerun.
    if not st.session_state.get("_cookie_init"):
        st.session_state["_cookie_init"] = True
        st.rerun()

    try:
        saved_token = _cookies.get("nc_refresh")
    except (TypeError, AttributeError):
        saved_token = None
    if saved_token:
        try:
            res = refresh_session(saved_token)
            if res.user:
                st.session_state["user"] = {"id": str(res.user.id), "email": res.user.email}
                _cookies.set("nc_refresh", res.session.refresh_token,
                             max_age=30 * 24 * 60 * 60)
                st.rerun()
        except Exception:
            _cookies.remove("nc_refresh")

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

    st.markdown(
        '<p style="font-size:.75rem;font-weight:700;text-transform:uppercase;'
        'letter-spacing:1px;color:#1e3a5f;margin-bottom:6px;">Nuovo Notebook</p>',
        unsafe_allow_html=True,
    )
    _c1, _c2 = st.columns([3, 1])
    _dlg_name = _c1.text_input(
        "Nome", placeholder="Es: Cardiologia",
        key="dlg_nb_name", label_visibility="collapsed",
    )
    if _c2.button("＋", key="dlg_add_nb", use_container_width=True, type="primary"):
        if _dlg_name.strip():
            _nb = create_notebook(_dlg_name.strip(), user_id=_u["id"])
            st.session_state.active_notebook = _nb
            st.rerun()

    st.divider()

    st.markdown(
        '<p style="font-size:.75rem;font-weight:700;text-transform:uppercase;'
        'letter-spacing:1px;color:#1e3a5f;margin-bottom:6px;">I tuoi Notebook</p>',
        unsafe_allow_html=True,
    )
    _nbs = get_notebooks(user_id=_u["id"])
    if not _nbs:
        st.info("Nessun notebook. Creane uno sopra.")
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

    _anb = st.session_state.active_notebook
    if _anb:
        st.divider()
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

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1.2rem 0.5rem 0.8rem;">
        <div style="font-size: 2.4rem; margin-bottom:4px;">🎙️</div>
        <div style="font-size: 1.4rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">NoteCaster</div>
        <div style="font-size: 0.72rem; color: #64748b; margin-top: 2px;">Podcast dalle sbobbine</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-size:0.7rem; color:#64748b; text-align:center; margin:0 0 4px;">{user["email"]}</p>',
        unsafe_allow_html=True,
    )
    if st.button("Esci", use_container_width=True):
        _cookies.remove("nc_refresh")
        del st.session_state["user"]
        st.session_state.active_notebook = None
        st.session_state.chat_history = []
        st.rerun()

    st.divider()

    st.markdown(
        '<p style="font-size:0.68rem; font-weight:700; text-transform:uppercase; '
        'letter-spacing:1.2px; color:#93c5fd; margin-bottom:6px;">Nuovo Notebook</p>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns([3, 1])
    name_input = col1.text_input(
        "Nome notebook",
        placeholder="Es: Cardiologia",
        label_visibility="collapsed",
        key="new_nb_name",
    )
    if col2.button("＋", use_container_width=True):
        if name_input.strip():
            nb = create_notebook(name_input.strip(), user_id=user["id"])
            st.session_state.active_notebook = nb
            st.rerun()

    st.divider()

    st.markdown(
        '<p style="font-size:0.68rem; font-weight:700; text-transform:uppercase; '
        'letter-spacing:1.2px; color:#93c5fd; margin-bottom:6px;">I tuoi Notebook</p>',
        unsafe_allow_html=True,
    )
    notebooks = get_notebooks(user_id=user["id"])
    if not notebooks:
        st.info("Nessun notebook. Creane uno sopra.")
    else:
        for idx, nb in enumerate(notebooks):
            doc_count = len(get_indexed_docs(nb["id"]))
            is_active = (st.session_state.active_notebook or {}).get("id") == nb["id"]
            btn_label = f"{'▶ ' if is_active else ''}{nb['name']} ({doc_count} doc)"
            col_nb, col_del = st.columns([5, 1])
            if col_nb.button(
                btn_label,
                key=f"nb_{nb['id']}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                if not is_active:
                    st.session_state.active_notebook = nb
                    st.rerun()
            if col_del.button("🗑", key=f"del_{nb['id']}", help="Elimina notebook"):
                st.session_state[f"confirm_del_{nb['id']}"] = True
                st.rerun()
            if st.session_state.get(f"confirm_del_{nb['id']}"):
                st.warning(f"Eliminare '{nb['name']}'?")
                cc1, cc2 = st.columns(2)
                if cc1.button("Sì, elimina", key=f"yes_del_{nb['id']}", type="primary"):
                    delete_notebook(nb["id"], user_id=user["id"])
                    delete_notebook_index(nb["id"])
                    if (st.session_state.active_notebook or {}).get("id") == nb["id"]:
                        st.session_state.active_notebook = None
                    del st.session_state[f"confirm_del_{nb['id']}"]
                    st.rerun()
                if cc2.button("Annulla", key=f"no_del_{nb['id']}"):
                    del st.session_state[f"confirm_del_{nb['id']}"]
                    st.rerun()

    # Upload section
    active_nb_sidebar = st.session_state.active_notebook
    if active_nb_sidebar:
        st.divider()
        st.markdown(
            f'<p style="font-size:0.68rem; font-weight:700; text-transform:uppercase; '
            f'letter-spacing:1.2px; color:#93c5fd; margin-bottom:6px;">📁 {active_nb_sidebar["name"]}</p>',
            unsafe_allow_html=True,
        )
        indexed = get_indexed_docs(active_nb_sidebar["id"])
        if indexed:
            for d in indexed:
                st.caption(f"• {d}")
        else:
            st.caption("Nessuna sbobina ancora.")

        st.caption("Carica PDF, DOCX, TXT, MD")
        uploaded = st.file_uploader(
            "Carica sbobine",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
            key=f"uploader_{active_nb_sidebar['id']}",
            label_visibility="collapsed",
        )
        if st.button("📥 Indicizza", use_container_width=True, disabled=not uploaded):
            progress_bar = st.progress(0)
            results = []
            for i, f in enumerate(uploaded):
                progress_bar.progress((i + 1) / len(uploaded))
                suffix = Path(f.name).suffix
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(f.read())
                    tmp_path = tmp.name
                try:
                    text = extract_text(tmp_path)
                    if not text.strip():
                        results.append(f"⚠️ {f.name}: nessun testo (PDF scansionato?)")
                        continue
                    chunks = chunk_text(text)
                    added = index_document(active_nb_sidebar["id"], f.name, chunks)
                    results.append(f"✓ {f.name} ({added} chunk)")
                except ValueError as e:
                    results.append(f"✗ {f.name}: {e}")
                finally:
                    os.unlink(tmp_path)
            progress_bar.empty()
            for r in results:
                if r.startswith("✓"):
                    st.success(r)
                elif r.startswith("⚠"):
                    st.warning(r)
                else:
                    st.error(r)
            st.rerun()

# ── MOBILE FAB ────────────────────────────────────────────────────────────────
# Inject a floating action button into the parent document via JS.
# The FAB is only visible on screens < 1024px (CSS above) and opens the
# notebook manager dialog by clicking Streamlit's sidebar toggle (with
# fallback to the #nc-nb-btn trigger button below).
components.html("""
<script>
(function () {
    function setup() {
        var pd = window.parent.document;
        if (!pd || pd.getElementById('nc-fab')) return;

        var fab = pd.createElement('button');
        fab.id = 'nc-fab';
        fab.title = 'Gestisci Notebook';
        fab.textContent = '☰';   /* ☰ */

        fab.addEventListener('click', function () {
            /* Try Streamlit's own sidebar toggles first */
            var sels = [
                '[data-testid="stSidebarCollapsed"] button',
                '[data-testid="collapsedControl"] button',
                '[data-testid="stSidebarCollapseButton"] button',
            ];
            for (var i = 0; i < sels.length; i++) {
                var el = pd.querySelector(sels[i]);
                if (el) { el.click(); return; }
            }
            /* Fallback: click the "☰ Notebook" button by text content */
            var buttons = pd.querySelectorAll('[data-testid="stButton"] button');
            for (var j = 0; j < buttons.length; j++) {
                if (buttons[j].textContent.indexOf('Notebook') >= 0) {
                    buttons[j].click();
                    return;
                }
            }
        });
        pd.body.appendChild(fab);
    }
    setup();
    setTimeout(setup, 600);
    setTimeout(setup, 2000);
})();
</script>
""", height=0, scrolling=False)

# ── MAIN AREA ──────────────────────────────────────────────────────────────────
# "☰ Notebook" button — always visible, primary mobile navigation.
# The JS FAB above clicks this button by text when the sidebar toggle is absent.
_nb_btn_col = st.columns([1, 6])[0]
if _nb_btn_col.button("☰ Notebook", key="_nb_panel_btn", use_container_width=True):
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
        <span class="hint-desktop">
            <span style="font-size: 1.1rem;">👈</span>
            <span style="font-weight: 700; color: #1e293b; font-size: 0.9rem; margin-left: 0.4rem;">
                Inizia dalla sidebar
            </span>
        </span>
        <span class="hint-mobile">
            <span style="font-size: 1.1rem;">☰</span>
            <span style="font-weight: 700; color: #1e293b; font-size: 0.9rem; margin-left: 0.4rem;">
                Tocca <strong>☰ Notebook</strong> in alto
            </span>
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
        if has_docs else "Carica prima dei documenti nella sidebar"
    )
    if prompt := st.chat_input(chat_placeholder):
        if not has_docs:
            st.warning("Carica prima dei documenti nel notebook (vedi sidebar).")
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
            "Completo": "~30-40 min",
            "Dettagliato (esame)": "~20-28 min per sezione",
            "Overview": "~3-5 min",
            "In-depth": "~12-18 min",
            "Complete": "~30-40 min",
            "Detailed (exam)": "~20-28 min per section",
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
