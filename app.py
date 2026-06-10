import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.db import create_notebook, get_notebooks, delete_notebook
from src.document_processor import extract_text, chunk_text
from src.rag_engine import (
    index_document,
    query_context,
    get_indexed_docs,
    get_full_text,
    get_doc_text,
    delete_notebook_index,
)
from src.llm_client import chat as llm_chat, chat_stream
from src.notes_generator import generate_notes, NOTES_TYPES
from src.podcast_generator import generate_podcast, DETAIL_LEVELS_IT, DETAIL_LEVELS_EN
from src.mindmap_generator import generate_mindmap

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StudyLM — Il tuo assistente di studio",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS injection ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── App background ─────────────────────────────────────────────────────── */
.stApp {
    background: linear-gradient(135deg, #fdf4ff 0%, #f0e7ff 20%, #e8f0fe 50%, #e0f7fa 80%, #f0fdf4 100%) !important;
    background-attachment: fixed !important;
}

/* ── Hide clutter ───────────────────────────────────────────────────────── */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; display: none; }
[data-testid="stHeader"] { background: transparent !important; }

/* ── Sidebar ────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #1a0533 0%, #1e1b4b 40%, #0f2744 100%) !important;
    border-right: 1px solid rgba(124, 58, 237, 0.3) !important;
}
[data-testid="stSidebar"] * {
    color: #e2d9f3 !important;
}
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] caption {
    color: #a78bca !important;
}
[data-testid="stSidebar"] input[type="text"] {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(124,58,237,0.4) !important;
    border-radius: 10px !important;
    color: #f1ebff !important;
}
[data-testid="stSidebar"] input[type="text"]::placeholder {
    color: #8b7aa8 !important;
}
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
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
    color: #c4b5fd !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(124,58,237,0.25) !important;
}
[data-testid="stSidebar"] .stAlert {
    background: rgba(124,58,237,0.15) !important;
    border: 1px solid rgba(124,58,237,0.3) !important;
    border-radius: 10px !important;
    color: #e2d9f3 !important;
}

/* ── Main area buttons ──────────────────────────────────────────────────── */
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
.main .stButton button[kind="secondary"]:hover {
    background: rgba(124,58,237,0.08) !important;
}

/* ── Download buttons ───────────────────────────────────────────────────── */
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

/* ── Tabs ────────────────────────────────────────────────────────────────── */
[data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.65) !important;
    backdrop-filter: blur(12px) !important;
    border-radius: 16px !important;
    padding: 6px !important;
    border: 1px solid rgba(124,58,237,0.15) !important;
    box-shadow: 0 2px 12px rgba(124,58,237,0.08) !important;
    gap: 4px !important;
}
[data-baseweb="tab"] {
    border-radius: 10px !important;
    color: #6b7280 !important;
    font-weight: 500 !important;
    padding: 8px 18px !important;
    transition: all 0.2s ease !important;
}
[data-baseweb="tab"]:hover {
    background: rgba(124,58,237,0.08) !important;
    color: #7c3aed !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: linear-gradient(135deg, #7c3aed, #6366f1) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: 0 3px 10px rgba(124,58,237,0.35) !important;
}
[data-baseweb="tab-highlight"],
[data-baseweb="tab-border"] {
    display: none !important;
}

/* ── Chat input ─────────────────────────────────────────────────────────── */
[data-testid="stChatInput"] > div {
    background: rgba(255,255,255,0.85) !important;
    border: 1.5px solid rgba(124,58,237,0.35) !important;
    border-radius: 16px !important;
    box-shadow: 0 2px 12px rgba(124,58,237,0.1) !important;
    backdrop-filter: blur(8px) !important;
}

/* ── Progress bar shimmer ───────────────────────────────────────────────── */
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

/* ── Expander cards ─────────────────────────────────────────────────────── */
details[data-testid="stExpander"] {
    background: rgba(255,255,255,0.75) !important;
    border: 1px solid rgba(124,58,237,0.2) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(8px) !important;
    box-shadow: 0 2px 10px rgba(124,58,237,0.08) !important;
}

/* ── File uploader in main ──────────────────────────────────────────────── */
[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed #7c3aed !important;
    border-radius: 14px !important;
    background: rgba(124,58,237,0.04) !important;
}

/* ── Sidebar always visible — hide collapse button ──────────────────────── */
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="stSidebarCollapsed"] { display: none !important; }
[data-testid="stSidebar"] {
    transform: none !important;
    min-width: 244px !important;
    visibility: visible !important;
}

/* ── Scrollbar ──────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: #7c3aed;
    border-radius: 999px;
}

/* ── Select boxes ───────────────────────────────────────────────────────── */
[data-baseweb="select"] > div:first-child {
    border-radius: 12px !important;
    border: 1.5px solid rgba(124,58,237,0.35) !important;
    background: rgba(255,255,255,0.8) !important;
}

/* ── Text inputs & textareas in main ───────────────────────────────────── */
.main input[type="text"], .main textarea {
    border-radius: 12px !important;
    border: 1.5px solid rgba(124,58,237,0.3) !important;
    background: rgba(255,255,255,0.9) !important;
}
.main input[type="text"]:focus, .main textarea:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.12) !important;
}

/* ── Radio buttons ──────────────────────────────────────────────────────── */
[data-testid="stRadio"] label {
    background: rgba(255,255,255,0.7) !important;
    border: 1px solid rgba(124,58,237,0.2) !important;
    border-radius: 8px !important;
    padding: 4px 10px !important;
    transition: all 0.15s ease !important;
}
[data-testid="stRadio"] label:has(input:checked) {
    background: rgba(124,58,237,0.12) !important;
    border-color: #7c3aed !important;
    color: #7c3aed !important;
    font-weight: 600 !important;
}

/* ── Chat messages ──────────────────────────────────────────────────────── */
[data-testid="stChatMessageContent"] {
    background: rgba(255,255,255,0.8) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(124,58,237,0.1) !important;
}

/* ── Custom note card ───────────────────────────────────────────────────── */
.note-card {
    background: rgba(255,255,255,0.85);
    border: 1px solid rgba(124,58,237,0.2);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    backdrop-filter: blur(8px);
    box-shadow: 0 4px 20px rgba(124,58,237,0.08);
    margin-top: 1rem;
}

/* ── Podcast audio card ─────────────────────────────────────────────────── */
.podcast-card {
    background: linear-gradient(135deg, rgba(13,148,136,0.08), rgba(8,145,178,0.08));
    border: 1px solid rgba(13,148,136,0.25);
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-top: 0.75rem;
}

/* ── Time estimate pill ─────────────────────────────────────────────────── */
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

# ── Session state init ─────────────────────────────────────────────────────────
st.session_state.setdefault("active_notebook", None)
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("last_notebook_id", None)

# ── Notebook color palette ─────────────────────────────────────────────────────
NB_COLORS = ["#7c3aed", "#2563eb", "#0d9488", "#ea580c", "#db2777", "#d97706"]

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Brand header
    st.markdown("""
    <div style="text-align:center; padding: 1.2rem 0.5rem 0.8rem;">
        <div style="font-size: 2.4rem; margin-bottom:4px;">🎓</div>
        <div style="font-size: 1.4rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">StudyLM</div>
        <div style="font-size: 0.72rem; color: #8b7aa8; margin-top: 2px;">Powered by DeepSeek</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Section 1 — Nuovo Notebook
    st.markdown(
        '<p style="font-size:0.68rem; font-weight:700; text-transform:uppercase; '
        'letter-spacing:1.2px; color:#c4b5fd; margin-bottom:6px;">Nuovo Notebook</p>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns([3, 1])
    name_input = col1.text_input(
        "Nome notebook",
        placeholder="Nome notebook",
        label_visibility="collapsed",
        key="new_nb_name",
    )
    if col2.button("＋", use_container_width=True):
        if name_input.strip():
            nb = create_notebook(name_input.strip())
            st.session_state.active_notebook = nb
            st.session_state.chat_history = []
            st.rerun()

    st.divider()

    # Section 2 — I tuoi Notebook
    st.markdown(
        '<p style="font-size:0.68rem; font-weight:700; text-transform:uppercase; '
        'letter-spacing:1.2px; color:#c4b5fd; margin-bottom:6px;">I tuoi Notebook</p>',
        unsafe_allow_html=True,
    )
    notebooks = get_notebooks()
    if not notebooks:
        st.info("Nessun notebook. Creane uno sopra.")
    else:
        for idx, nb in enumerate(notebooks):
            doc_count = len(get_indexed_docs(nb["id"]))
            is_active = (st.session_state.active_notebook or {}).get("id") == nb["id"]
            nb_color = NB_COLORS[idx % len(NB_COLORS)]
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
                    st.session_state.chat_history = []
                    st.rerun()
            if col_del.button("🗑", key=f"del_{nb['id']}", help="Elimina notebook"):
                st.session_state[f"confirm_del_{nb['id']}"] = True
                st.rerun()
            if st.session_state.get(f"confirm_del_{nb['id']}"):
                st.warning(f"Eliminare '{nb['name']}'?")
                cc1, cc2 = st.columns(2)
                if cc1.button("Sì, elimina", key=f"yes_del_{nb['id']}", type="primary"):
                    delete_notebook(nb["id"])
                    delete_notebook_index(nb["id"])
                    if (st.session_state.active_notebook or {}).get("id") == nb["id"]:
                        st.session_state.active_notebook = None
                        st.session_state.chat_history = []
                    del st.session_state[f"confirm_del_{nb['id']}"]
                    st.rerun()
                if cc2.button("Annulla", key=f"no_del_{nb['id']}"):
                    del st.session_state[f"confirm_del_{nb['id']}"]
                    st.rerun()

    # Section 3 — Documenti (only if active notebook)
    active_nb = st.session_state.active_notebook
    if active_nb:
        st.divider()
        st.markdown(
            f'<p style="font-size:0.68rem; font-weight:700; text-transform:uppercase; '
            f'letter-spacing:1.2px; color:#c4b5fd; margin-bottom:6px;">📁 {active_nb["name"]}</p>',
            unsafe_allow_html=True,
        )

        indexed = get_indexed_docs(active_nb["id"])
        if indexed:
            for d in indexed:
                st.caption(f"• {d}")
        else:
            st.caption("Nessun documento ancora.")

        st.caption("Trascina PDF, DOCX, TXT, MD")
        uploaded = st.file_uploader(
            "Aggiungi documenti",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
            key=f"uploader_{active_nb['id']}",
            label_visibility="collapsed",
        )
        if st.button(
            "📥 Indicizza", use_container_width=True, disabled=not uploaded
        ):
            uploads_dir = os.path.join(
                os.path.dirname(__file__), "uploads", active_nb["id"]
            )
            os.makedirs(uploads_dir, exist_ok=True)
            progress_bar = st.progress(0)
            status = st.empty()
            results = []
            for i, f in enumerate(uploaded):
                progress_bar.progress((i + 1) / len(uploaded))
                dest = os.path.join(uploads_dir, f.name)
                with open(dest, "wb") as out:
                    out.write(f.read())
                try:
                    text = extract_text(dest)
                    if not text.strip():
                        results.append(
                            f"⚠️ {f.name}: testo non estraibile (PDF scansionato?)"
                        )
                        continue
                    chunks = chunk_text(text)
                    added = index_document(active_nb["id"], f.name, chunks)
                    results.append(f"✓ {f.name} ({added} chunk)")
                except ValueError as e:
                    results.append(f"✗ {f.name}: {e}")
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
    # ── Hero / Welcome screen ──────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding: 3rem 1rem 1rem;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">🎓</div>
        <h1 style="
            font-size: 3.2rem;
            font-weight: 900;
            background: linear-gradient(135deg, #7c3aed 0%, #6366f1 40%, #0d9488 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0 0 0.6rem;
            letter-spacing: -1.5px;
        ">StudyLM</h1>
        <p style="font-size: 1.15rem; color: #6b7280; max-width: 520px; margin: 0 auto 2.5rem;">
            Il tuo assistente di studio personale — carica i tuoi materiali e studia in modo più intelligente.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    feat_col1, feat_col2, feat_col3, feat_col4 = st.columns(4, gap="medium")

    with feat_col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(124,58,237,0.12), rgba(99,102,241,0.18));
                    border: 1px solid rgba(124,58,237,0.25); border-radius: 18px; padding: 1.5rem 1.2rem;
                    text-align: center; height: 100%;">
            <div style="font-size: 2rem; margin-bottom: 0.6rem;">💬</div>
            <div style="font-weight: 700; color: #4c1d95; font-size: 1rem; margin-bottom: 0.4rem;">Chat AI</div>
            <div style="font-size: 0.82rem; color: #6d28d9;">Fai domande sui tuoi documenti con contesto RAG intelligente</div>
        </div>
        """, unsafe_allow_html=True)

    with feat_col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(37,99,235,0.12), rgba(99,102,241,0.18));
                    border: 1px solid rgba(37,99,235,0.25); border-radius: 18px; padding: 1.5rem 1.2rem;
                    text-align: center; height: 100%;">
            <div style="font-size: 2rem; margin-bottom: 0.6rem;">📝</div>
            <div style="font-weight: 700; color: #1e3a8a; font-size: 1rem; margin-bottom: 0.4rem;">Note AI</div>
            <div style="font-size: 0.82rem; color: #1d4ed8;">Riassunti, mappe, flashcard e schemi generati automaticamente</div>
        </div>
        """, unsafe_allow_html=True)

    with feat_col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(13,148,136,0.12), rgba(8,145,178,0.18));
                    border: 1px solid rgba(13,148,136,0.25); border-radius: 18px; padding: 1.5rem 1.2rem;
                    text-align: center; height: 100%;">
            <div style="font-size: 2rem; margin-bottom: 0.6rem;">🎙️</div>
            <div style="font-weight: 700; color: #134e4a; font-size: 1rem; margin-bottom: 0.4rem;">Podcast</div>
            <div style="font-size: 0.82rem; color: #0f766e;">Audio overview con due host — come NotebookLM, ma tuo</div>
        </div>
        """, unsafe_allow_html=True)

    with feat_col4:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(234,88,12,0.12), rgba(217,119,6,0.18));
                    border: 1px solid rgba(234,88,12,0.25); border-radius: 18px; padding: 1.5rem 1.2rem;
                    text-align: center; height: 100%;">
            <div style="font-size: 2rem; margin-bottom: 0.6rem;">🗺️</div>
            <div style="font-weight: 700; color: #7c2d12; font-size: 1rem; margin-bottom: 0.4rem;">Mappa</div>
            <div style="font-size: 0.82rem; color: #c2410c;">Mappe concettuali interattive dei tuoi argomenti</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)

    # CTA box
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(124,58,237,0.08), rgba(99,102,241,0.12));
        border: 1.5px solid rgba(124,58,237,0.25);
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        max-width: 480px;
        margin: 0 auto;
    ">
        <div style="font-size: 1.2rem; margin-bottom: 0.3rem;">👈</div>
        <div style="font-weight: 700; color: #4c1d95; font-size: 0.95rem;">Inizia subito</div>
        <div style="font-size: 0.82rem; color: #6d28d9; margin-top: 0.3rem;">
            Crea un nuovo notebook dalla sidebar, poi carica i tuoi materiali di studio.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.stop()

active_nb = st.session_state.active_notebook

# Detect notebook change and clear chat
if st.session_state.last_notebook_id != active_nb["id"]:
    st.session_state.chat_history = []
    st.session_state.last_notebook_id = active_nb["id"]

# ── Notebook header card ───────────────────────────────────────────────────────
nb_doc_count = len(get_indexed_docs(active_nb["id"]))
st.markdown(f"""
<div style="
    background: rgba(255,255,255,0.75);
    border: 1px solid rgba(124,58,237,0.2);
    border-radius: 18px;
    padding: 1.25rem 1.75rem;
    margin-bottom: 1.25rem;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 20px rgba(124,58,237,0.08);
    display: flex;
    align-items: center;
    gap: 1rem;
">
    <div style="font-size: 2rem;">📚</div>
    <div style="flex: 1;">
        <h2 style="
            margin: 0;
            font-size: 1.6rem;
            font-weight: 800;
            background: linear-gradient(135deg, #7c3aed, #6366f1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.5px;
        ">{active_nb['name']}</h2>
        <div style="font-size: 0.8rem; color: #6b7280; margin-top: 2px;">
            {nb_doc_count} documento{'i' if nb_doc_count != 1 else ''} indicizzato{'i' if nb_doc_count != 1 else ''}
        </div>
    </div>
    <span style="
        background: linear-gradient(135deg, rgba(13,148,136,0.15), rgba(8,145,178,0.15));
        border: 1px solid rgba(13,148,136,0.35);
        color: #0f766e;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 999px;
        letter-spacing: 0.5px;
    ">✦ AI READY</span>
</div>
""", unsafe_allow_html=True)

tab_chat, tab_notes, tab_podcast, tab_map = st.tabs(
    ["💬 Chat", "📝 Note", "🎙️ Podcast", "🗺️ Mappa"]
)

# ── TAB: Chat ──────────────────────────────────────────────────────────────────
with tab_chat:
    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Check if docs available
    has_docs = len(get_indexed_docs(active_nb["id"])) > 0

    col_input, col_clear = st.columns([5, 1])
    if col_clear.button("🗑 Pulisci", key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun()

    chat_placeholder = (
        "Fai una domanda sui tuoi documenti..."
        if has_docs
        else "Carica prima dei documenti nel notebook"
    )
    if prompt := st.chat_input(chat_placeholder):
        if not has_docs:
            st.warning("Carica prima dei documenti nel notebook (vedi sidebar).")
        else:
            st.session_state.chat_history.append(
                {"role": "user", "content": prompt}
            )
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                context = query_context(active_nb["id"], prompt, n_results=6)
                system = (
                    "Sei un assistente di studio per studenti di medicina. "
                    "Rispondi SOLO basandoti sui documenti forniti nel contesto. "
                    "Se l'informazione non è nei documenti, dillo esplicitamente. "
                    "Sii preciso, utile e cita i concetti chiave. "
                    "Usa Markdown per strutturare le risposte complesse."
                )
                messages = [{"role": "system", "content": system}]
                # Add last 8 turns of history
                for h in st.session_state.chat_history[-8:]:
                    messages.append({"role": h["role"], "content": h["content"]})
                # Replace last user message with context-enriched version
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

# ── TAB: Note automatiche ──────────────────────────────────────────────────────
with tab_notes:
    st.subheader("📝 Note automatiche")
    note_type = st.radio(
        "Tipo di nota",
        NOTES_TYPES,
        horizontal=True,
        key="note_type_radio",
    )

    if st.button("✨ Genera Note", type="primary", use_container_width=False):
        with st.spinner(f"Generazione '{note_type}' in corso..."):
            full_text = get_full_text(active_nb["id"])
            if not full_text.strip():
                st.warning(
                    "Nessun documento indicizzato. Carica prima dei file."
                )
            else:
                notes = generate_notes(full_text, note_type)
                st.session_state[f"notes_{note_type}"] = notes

    if f"notes_{note_type}" in st.session_state:
        notes_content = st.session_state[f"notes_{note_type}"]
        st.markdown(
            f'<div class="note-card">{notes_content}</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇️ Scarica note",
            data=notes_content,
            file_name=f"{active_nb['name']}_{note_type.replace(' ', '_')}.md",
            mime="text/markdown",
        )

# ── TAB: Podcast ───────────────────────────────────────────────────────────────
with tab_podcast:
    st.subheader("🎙️ Audio Overview")
    st.markdown(
        "Genera un podcast con due host che discutono i tuoi documenti — come NotebookLM."
    )

    indexed_docs_podcast = get_indexed_docs(active_nb["id"])
    has_docs_podcast = len(indexed_docs_podcast) > 0

    if not has_docs_podcast:
        st.warning("Carica prima dei documenti nel notebook.")
    else:
        col_lang, col_detail = st.columns([1, 2])
        lang = col_lang.selectbox(
            "Lingua",
            ["Auto-detect", "Italiano", "English"],
            key="podcast_lang",
        )
        detail_options_it = list(DETAIL_LEVELS_IT.keys())
        detail_options_en = list(DETAIL_LEVELS_EN.keys())
        detail_options = detail_options_en if lang == "English" else detail_options_it
        detail_level = col_detail.selectbox(
            "Livello di dettaglio",
            detail_options,
            index=1,
            key="podcast_detail",
        )

        source_options = ["Tutti i documenti"] + indexed_docs_podcast
        source_doc = st.selectbox(
            "Sorgente documento",
            source_options,
            key="podcast_source",
            help="Seleziona una sbobina specifica oppure usa tutti i documenti del notebook",
        )

        topic = st.text_input(
            "Argomento del podcast",
            placeholder="Es: Patologie dell'aorta toracica e addominale, Shock cardiogeno, Stenosi aortica...",
            key="podcast_topic",
            help="Scrivi l'argomento esatto (tipicamente un titolo di capitolo). Il podcast tratterà SOLO questo.",
        )

        # Time estimate shown before generation starts
        _time_hint = {
            "Panoramica": "~3-5 min",
            "Approfondito": "~12-18 min",
            "Completo": "~30-40 min — tutti gli argomenti con meccanismi, diagnostica e terapia",
            "Dettagliato (esame)": "20-28 min per sezione — ripetizione completa da esame",
            "Overview": "~3-5 min",
            "In-depth": "~12-18 min",
            "Complete": "~30-40 min — all topics with mechanisms, diagnostics and treatment",
            "Detailed (exam)": "20-28 min per section — full exam-level repetition",
        }
        _hint_text = _time_hint.get(detail_level, "—")
        st.markdown(
            f'<div class="time-pill">⏱ Durata stimata: {_hint_text}</div>',
            unsafe_allow_html=True,
        )

        if st.button("🎙️ Genera Podcast", type="primary", use_container_width=True):
            lang_map = {"Auto-detect": "auto", "Italiano": "it", "English": "en"}
            lang_code = lang_map[lang]

            progress_bar = st.progress(0, text="Recupero documenti...")
            status_placeholder = st.empty()

            if source_doc == "Tutti i documenti":
                full_text = get_full_text(active_nb["id"])
            else:
                full_text = get_doc_text(active_nb["id"], source_doc)

            if not full_text.strip():
                st.error("Nessun testo disponibile per la sorgente selezionata.")
            else:
                progress_bar.progress(0.05, text="Avvio generazione...")

                def audio_progress(done, total):
                    pct = 0.45 + (done / total) * 0.50
                    progress_bar.progress(
                        pct, text=f"Sintesi audio: battuta {done}/{total}..."
                    )

                def on_status(msg: str):
                    is_script_phase = "script" in msg.lower() or "segmento" in msg.lower() or "generazione" in msg.lower()
                    if is_script_phase:
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

# ── TAB: Mappa concettuale ─────────────────────────────────────────────────────
with tab_map:
    from streamlit_agraph import agraph, Node, Edge, Config

    st.subheader("🗺️ Mappa concettuale interattiva")

    all_docs = get_indexed_docs(active_nb["id"])

    if not all_docs:
        st.warning("Carica prima dei documenti nel notebook.")
    else:
        # Selector: whole exam or single document
        doc_options = ["📚 Tutto l'esame"] + all_docs
        selected_source = st.selectbox(
            "Genera mappa di:",
            options=doc_options,
            key="map_source_select",
        )

        col_btn, col_saved = st.columns([2, 5])
        if col_btn.button("✨ Genera Mappa", type="primary"):
            with st.spinner("Analisi concetti con DeepSeek..."):
                if selected_source == "📚 Tutto l'esame":
                    text = get_full_text(active_nb["id"])
                else:
                    text = get_doc_text(active_nb["id"], selected_source)

                if not text.strip():
                    st.error("Nessun testo disponibile per questa selezione.")
                else:
                    try:
                        data = generate_mindmap(text)
                        # Store map keyed by source name so each is preserved
                        maps = st.session_state.setdefault("mindmaps", {})
                        maps[selected_source] = data
                        st.session_state["active_map_key"] = selected_source
                    except Exception as e:
                        st.error(f"Errore: {e}")

        # Show all previously generated maps as tabs
        maps = st.session_state.get("mindmaps", {})
        if maps:
            map_keys = list(maps.keys())
            if len(map_keys) == 1:
                active_map_key = map_keys[0]
            else:
                active_map_key = st.session_state.get("active_map_key", map_keys[-1])
                chosen = st.radio(
                    "Mappe generate:",
                    map_keys,
                    index=map_keys.index(active_map_key) if active_map_key in map_keys else 0,
                    horizontal=True,
                    key="map_radio",
                )
                active_map_key = chosen

            data = maps[active_map_key]
            label = active_map_key if active_map_key != "📚 Tutto l'esame" else "Tutto l'esame"
            st.caption(f"Mappa: **{label}**")

            COLORS = {
                0: {"background": "#4f46e5", "border": "#3730a3", "font": "#ffffff"},
                1: {"background": "#ddd6fe", "border": "#7c3aed", "font": "#1e1b4b"},
                2: {"background": "#bfdbfe", "border": "#2563eb", "font": "#1e3a8a"},
                3: {"background": "#bbf7d0", "border": "#16a34a", "font": "#14532d"},
            }
            SIZES = {0: 40, 1: 28, 2: 20, 3: 15}

            nodes = [
                Node(
                    id=n["id"],
                    label=n["label"],
                    size=SIZES.get(n.get("level", 2), 18),
                    color=COLORS.get(n.get("level", 2), COLORS[2])["background"],
                    borderColor=COLORS.get(n.get("level", 2), COLORS[2])["border"],
                    fontColor=COLORS.get(n.get("level", 2), COLORS[2])["font"],
                )
                for n in data.get("nodes", [])
            ]
            edges = [
                Edge(source=e["source"], target=e["target"], color="#c4b5fd")
                for e in data.get("edges", [])
            ]
            config = Config(
                width="100%",
                height=620,
                directed=False,
                physics=True,
                hierarchical=False,
            )
            agraph(nodes=nodes, edges=edges, config=config)
