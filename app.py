import os
import tempfile
from pathlib import Path

import streamlit as st
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
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #fdf4ff 0%, #f0e7ff 20%, #e8f0fe 50%, #e0f7fa 80%, #f0fdf4 100%) !important;
    background-attachment: fixed !important;
}

#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; display: none; }
[data-testid="stHeader"] { background: transparent !important; }

[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #1a0533 0%, #1e1b4b 40%, #0f2744 100%) !important;
    border-right: 1px solid rgba(124, 58, 237, 0.3) !important;
}
[data-testid="stSidebar"] * { color: #e2d9f3 !important; }
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] caption { color: #a78bca !important; }
[data-testid="stSidebar"] input[type="text"] {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(124,58,237,0.4) !important;
    border-radius: 10px !important;
    color: #f1ebff !important;
}
[data-testid="stSidebar"] input[type="text"]::placeholder { color: #8b7aa8 !important; }
[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #e2d9f3 !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(124,58,237,0.25) !important;
    border-color: rgba(124,58,237,0.6) !important;
}
[data-testid="stSidebar"] .stButton button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed, #6366f1) !important;
    border: none !important;
    color: #ffffff !important;
    box-shadow: 0 2px 8px rgba(124,58,237,0.4) !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: rgba(124,58,237,0.12) !important;
    border: 2px dashed rgba(124,58,237,0.5) !important;
    border-radius: 12px !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * { color: #c4b5fd !important; }
[data-testid="stSidebar"] hr { border-color: rgba(124,58,237,0.25) !important; }
[data-testid="stSidebar"] .stAlert {
    background: rgba(124,58,237,0.15) !important;
    border: 1px solid rgba(124,58,237,0.3) !important;
    border-radius: 10px !important;
    color: #e2d9f3 !important;
}

.main .stButton button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed 0%, #6366f1 100%) !important;
    border: none !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 15px rgba(124,58,237,0.35) !important;
    transition: all 0.2s ease !important;
    padding: 0.5rem 1.5rem !important;
}
.main .stButton button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(124,58,237,0.5) !important;
}
.main .stButton button[kind="secondary"] {
    background: rgba(255,255,255,0.8) !important;
    border: 1.5px solid #7c3aed !important;
    color: #7c3aed !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}

.stDownloadButton button {
    background: linear-gradient(135deg, #0d9488 0%, #0891b2 100%) !important;
    border: none !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(13,148,136,0.35) !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 18px rgba(13,148,136,0.5) !important;
}

[data-testid="stProgressBar"] > div > div > div > div {
    background: linear-gradient(90deg, #7c3aed, #6366f1, #0d9488, #0891b2, #7c3aed) !important;
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
    border: 1px solid rgba(124,58,237,0.2) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(8px) !important;
    box-shadow: 0 2px 10px rgba(124,58,237,0.08) !important;
}

[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed #7c3aed !important;
    border-radius: 14px !important;
    background: rgba(124,58,237,0.04) !important;
}

[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="stSidebarCollapsed"] { display: none !important; }
[data-testid="stSidebar"] {
    transform: none !important;
    min-width: 244px !important;
    visibility: visible !important;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #7c3aed; border-radius: 999px; }

[data-baseweb="select"] > div:first-child {
    border-radius: 12px !important;
    border: 1.5px solid rgba(124,58,237,0.35) !important;
    background: rgba(255,255,255,0.8) !important;
}

.main input[type="text"], .main textarea {
    border-radius: 12px !important;
    border: 1.5px solid rgba(124,58,237,0.3) !important;
    background: rgba(255,255,255,0.9) !important;
}
.main input[type="text"]:focus, .main textarea:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.12) !important;
}

.podcast-card {
    background: linear-gradient(135deg, rgba(13,148,136,0.08), rgba(8,145,178,0.08));
    border: 1px solid rgba(13,148,136,0.25);
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-top: 0.75rem;
}

.time-pill {
    display: inline-block;
    background: linear-gradient(135deg, rgba(13,148,136,0.15), rgba(8,145,178,0.15));
    border: 1px solid rgba(13,148,136,0.3);
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 0.82rem;
    color: #0d7377;
    font-weight: 600;
    margin-bottom: 0.75rem;
}
</style>
""", unsafe_allow_html=True)

# ── Auth ───────────────────────────────────────────────────────────────────────
cm = stx.CookieManager()

if "user" not in st.session_state:
    # Prova a ripristinare la sessione dal cookie
    saved_token = cm.get("nc_refresh")
    if saved_token:
        try:
            res = refresh_session(saved_token)
            if res.user:
                st.session_state["user"] = {"id": str(res.user.id), "email": res.user.email}
                cm.set("nc_refresh", res.session.refresh_token,
                       expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                st.rerun()
        except Exception:
            cm.delete("nc_refresh")

if "user" not in st.session_state:
    st.markdown("""
    <div style="max-width:400px; margin: 5rem auto 0; text-align:center;">
        <div style="font-size:2.8rem; margin-bottom:0.4rem;">🎙️</div>
        <h1 style="
            font-size:2rem; font-weight:900; margin:0 0 0.3rem;
            background: linear-gradient(135deg, #7c3aed, #6366f1, #0d9488);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
        ">NoteCaster</h1>
        <p style="color:#6b7280; font-size:0.9rem; margin-bottom:2rem;">
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
                        cm.set("nc_refresh", res.session.refresh_token,
                               expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                        st.rerun()
                except Exception as e:
                    st.error(f"Errore: {e}")
    st.stop()

user = st.session_state["user"]

# ── Session state ──────────────────────────────────────────────────────────────
st.session_state.setdefault("active_notebook", None)
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("last_notebook_id", None)

NB_COLORS = ["#7c3aed", "#2563eb", "#0d9488", "#ea580c", "#db2777", "#d97706"]

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1.2rem 0.5rem 0.8rem;">
        <div style="font-size: 2.4rem; margin-bottom:4px;">🎙️</div>
        <div style="font-size: 1.4rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">NoteCaster</div>
        <div style="font-size: 0.72rem; color: #8b7aa8; margin-top: 2px;">Podcast dalle sbobbine</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-size:0.7rem; color:#8b7aa8; text-align:center; margin:0 0 4px;">{user["email"]}</p>',
        unsafe_allow_html=True,
    )
    if st.button("Esci", use_container_width=True):
        cm.delete("nc_refresh")
        del st.session_state["user"]
        st.session_state.active_notebook = None
        st.session_state.chat_history = []
        st.rerun()

    st.divider()

    st.markdown(
        '<p style="font-size:0.68rem; font-weight:700; text-transform:uppercase; '
        'letter-spacing:1.2px; color:#c4b5fd; margin-bottom:6px;">Nuovo Notebook</p>',
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
        'letter-spacing:1.2px; color:#c4b5fd; margin-bottom:6px;">I tuoi Notebook</p>',
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
            f'letter-spacing:1.2px; color:#c4b5fd; margin-bottom:6px;">📁 {active_nb_sidebar["name"]}</p>',
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

# ── MAIN AREA ──────────────────────────────────────────────────────────────────
if not st.session_state.active_notebook:
    st.markdown("""
    <div style="text-align:center; padding: 3rem 1rem 2rem;">
        <div style="font-size: 3.5rem; margin-bottom: 0.5rem;">🎙️</div>
        <h1 style="
            font-size: 3rem; font-weight: 900;
            background: linear-gradient(135deg, #7c3aed 0%, #6366f1 40%, #0d9488 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text; margin: 0 0 0.6rem; letter-spacing: -1.5px;
        ">NoteCaster</h1>
        <p style="font-size: 1.1rem; color: #6b7280; max-width: 480px; margin: 0 auto 2.5rem;">
            Trasforma le tue sbobbine in un podcast con due host AI — come NotebookLM, ma gratis e in italiano.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(124,58,237,0.1), rgba(99,102,241,0.15));
                    border: 1px solid rgba(124,58,237,0.25); border-radius: 18px; padding: 1.5rem 1.2rem;
                    text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">1️⃣</div>
            <div style="font-weight: 700; color: #4c1d95; font-size: 0.95rem; margin-bottom: 0.4rem;">Crea un notebook</div>
            <div style="font-size: 0.82rem; color: #6d28d9;">Uno per materia o per esame</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(37,99,235,0.1), rgba(99,102,241,0.15));
                    border: 1px solid rgba(37,99,235,0.25); border-radius: 18px; padding: 1.5rem 1.2rem;
                    text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">2️⃣</div>
            <div style="font-weight: 700; color: #1e3a8a; font-size: 0.95rem; margin-bottom: 0.4rem;">Carica le sbobine</div>
            <div style="font-size: 0.82rem; color: #1d4ed8;">PDF, DOCX o TXT — anche più file</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(13,148,136,0.1), rgba(8,145,178,0.15));
                    border: 1px solid rgba(13,148,136,0.25); border-radius: 18px; padding: 1.5rem 1.2rem;
                    text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">3️⃣</div>
            <div style="font-weight: 700; color: #134e4a; font-size: 0.95rem; margin-bottom: 0.4rem;">Genera il podcast</div>
            <div style="font-size: 0.82rem; color: #0f766e;">Scegli argomento, livello e scarica l'MP3</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(124,58,237,0.07), rgba(99,102,241,0.1));
        border: 1.5px solid rgba(124,58,237,0.2); border-radius: 14px;
        padding: 1rem 1.5rem; text-align: center; max-width: 400px; margin: 2rem auto 0;
    ">
        <span style="font-size: 1.1rem;">👈</span>
        <span style="font-weight: 700; color: #4c1d95; font-size: 0.9rem; margin-left: 0.4rem;">
            Inizia dalla sidebar
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
    background: rgba(255,255,255,0.75); border: 1px solid rgba(124,58,237,0.2);
    border-radius: 18px; padding: 1.25rem 1.75rem; margin-bottom: 1.5rem;
    backdrop-filter: blur(10px); box-shadow: 0 4px 20px rgba(124,58,237,0.08);
    display: flex; align-items: center; gap: 1rem;
">
    <div style="font-size: 2rem;">🎙️</div>
    <div style="flex: 1;">
        <h2 style="
            margin: 0; font-size: 1.6rem; font-weight: 800;
            background: linear-gradient(135deg, #7c3aed, #6366f1);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text; letter-spacing: -0.5px;
        ">{active_nb['name']}</h2>
        <div style="font-size: 0.8rem; color: #6b7280; margin-top: 2px;">
            {nb_doc_count} sbobina{'e' if nb_doc_count != 1 else ''} indicizzata{'e' if nb_doc_count != 1 else ''}
        </div>
    </div>
    <span style="
        background: linear-gradient(135deg, rgba(13,148,136,0.15), rgba(8,145,178,0.15));
        border: 1px solid rgba(13,148,136,0.35); color: #0f766e;
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
