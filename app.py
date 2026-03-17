import os
import re
import io
import math
import base64
import shutil
import sqlite3
import html
from collections import Counter
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import streamlit as st
import fitz  # PyMuPDF
from pypdf import PdfReader
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
from PIL import Image
from groq import Groq


# =========================================================
# CONFIGURAÇÃO GERAL
# =========================================================
st.set_page_config(
    page_title="MentorEdu | Projeto Inércia Zero",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "MentorEdu IFCE"
PROJECT_NAME = "Projeto Inércia Zero"
IF_LOGO = "logo.png"
DB_PATH = "mentoredu.db"
UPLOAD_DIR = "uploads"

MAX_PDF_MB = 15
MAX_IMG_MB = 8
MAX_PERGUNTAS_SESSAO = 30
ALLOWED_FILE_TYPES = ["pdf", "png", "jpg", "jpeg", "webp"]

TEXT_MODEL = "llama-3.3-70b-versatile"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


# =========================================================
# ESTILO VISUAL CLARO
# =========================================================
def inject_css():
    st.markdown("""
    <style>
    :root{
        --bg:#f6f8fb;
        --bg2:#eef3f8;
        --panel:#ffffff;
        --panel-soft:#f8fafc;
        --line:rgba(15,23,42,0.08);
        --line-soft:rgba(15,23,42,0.05);
        --text:#0f172a;
        --muted:#475569;
        --muted-2:#64748b;
        --green:#16a34a;
        --green-2:#15803d;
        --green-soft:#166534;
        --info:#2563eb;
        --warn:#d97706;
        --danger:#dc2626;
        --shadow:0 10px 28px rgba(15,23,42,0.08);
        --radius:18px;
    }

    html, body, [class*="css"] {
        color: var(--text);
    }

    .stApp{
        background:
            radial-gradient(circle at top left, rgba(34,197,94,0.06), transparent 18%),
            radial-gradient(circle at top right, rgba(37,99,235,0.05), transparent 16%),
            linear-gradient(180deg, #f8fafc 0%, #eef4f8 100%);
        color: var(--text);
    }

    header[data-testid="stHeader"]{
        background: rgba(255,255,255,0.88);
        border-bottom: 1px solid rgba(15,23,42,0.05);
        backdrop-filter: blur(10px);
    }

    section[data-testid="stSidebar"]{
        background: linear-gradient(180deg, #f8fbff 0%, #f1f5f9 100%);
        border-right: 1px solid rgba(15,23,42,0.06);
    }

    .block-container{
        padding-top: 1.25rem;
        padding-bottom: 1.5rem;
    }

    .hero-wrap{
        margin-bottom: 1rem;
    }

    .hero-card{
        background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,0.98) 100%);
        border: 1px solid var(--line);
        border-radius: 24px;
        padding: 1.35rem 1.2rem;
        box-shadow: var(--shadow);
    }

    .project-badge{
        display:inline-block;
        color:white;
        background: linear-gradient(90deg, var(--green), var(--green-2));
        padding: .48rem .95rem;
        border-radius: 999px;
        font-weight: 800;
        font-size: .88rem;
        margin-bottom: .9rem;
        box-shadow: 0 10px 20px rgba(22,163,74,0.16);
    }

    .main-title{
        color: var(--green-soft);
        font-weight: 900;
        font-size: 2.2rem;
        text-align: center;
        letter-spacing: -.03em;
        margin: 0;
    }

    .subtitle{
        text-align:center;
        color: var(--muted);
        margin-top: .45rem;
        line-height: 1.55;
        font-size: .98rem;
    }

    .chip-wrap{
        text-align:center;
        margin-top: .55rem;
    }

    .if-chip{
        display:inline-block;
        padding:.35rem .72rem;
        border-radius:999px;
        background:#f1f5f9;
        border:1px solid rgba(15,23,42,0.06);
        color:#334155;
        font-size:.8rem;
        font-weight:700;
        margin:.25rem .25rem 0 0;
    }

    .status-card{
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 1rem;
        box-shadow: var(--shadow);
        min-height: 108px;
    }

    .status-card h4{
        margin: 0;
        color: var(--muted-2);
        font-size: .9rem;
        font-weight: 700;
    }

    .status-ok{color:#16a34a;font-weight:800;}
    .status-info{color:var(--info);font-weight:800;}
    .status-warn{color:var(--warn);font-weight:800;}
    .status-danger{color:var(--danger);font-weight:800;}

    .soft-card,
    .mentor-card,
    .folder-hint,
    .math-box,
    .final-answer-box,
    .source-box,
    .preview-card{
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 16px;
        box-shadow: var(--shadow);
    }

    .soft-card,
    .mentor-card,
    .folder-hint,
    .preview-card{
        padding: 1rem;
    }

    .mentor-card h4{
        margin:0 0 .3rem 0;
        font-size:1rem;
        font-weight:800;
        color: var(--text);
    }

    .mentor-card p{
        margin:0;
        color: var(--muted);
        line-height:1.5;
        font-size:.92rem;
    }

    .folder-hint{
        color: var(--muted);
        line-height:1.5;
        font-size: .92rem;
        background:#fcfdff;
    }

    .math-box{
        padding: 1rem;
        margin: .8rem 0;
        background:#ffffff;
    }

    .final-answer-box{
        padding: 1rem;
        margin: .8rem 0;
        border-color: rgba(22,163,74,0.18);
        background: linear-gradient(180deg, #f6fff8 0%, #ffffff 100%);
    }

    .source-box{
        padding:.8rem .95rem;
        color: var(--muted);
        font-size:.9rem;
        margin-top: .7rem;
        background:#fbfdff;
    }

    .small-note{
        color: var(--muted-2);
        font-size: .84rem;
        line-height: 1.5;
    }

    .section-title{
        font-size: 1rem;
        font-weight: 800;
        color: var(--text);
        margin-bottom: .5rem;
    }

    .stButton > button{
        width:100%;
        background: linear-gradient(90deg, var(--green), var(--green-2)) !important;
        color:white !important;
        border:none !important;
        border-radius:14px !important;
        font-weight:800 !important;
        padding:.65rem 1rem !important;
        box-shadow:0 8px 18px rgba(22,163,74,0.14) !important;
    }

    .stButton > button:hover{
        transform: translateY(-1px);
        filter: brightness(1.02);
    }

    .stTextInput input,
    .stTextArea textarea,
    div[data-baseweb="select"] > div{
        background: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid rgba(15,23,42,0.10) !important;
        border-radius: 14px !important;
    }

    div[data-testid="stChatInput"]{
        padding-top: .45rem;
        border-top: 1px solid rgba(15,23,42,0.06);
        margin-top: .35rem;
    }

    div[data-testid="stChatInput"] textarea{
        background: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid rgba(15,23,42,0.10) !important;
        border-radius: 16px !important;
    }

    div[data-testid="stExpander"]{
        background: #ffffff;
        border: 1px solid var(--line-soft);
        border-radius: 16px;
        overflow: hidden;
    }

    hr{
        border-color: rgba(15,23,42,0.06);
    }

    .footer-note{
        text-align:center;
        color:var(--muted-2);
        font-size:.9rem;
        margin-top:1rem;
        margin-bottom:.35rem;
    }

    .user-bubble{
        background: #ecfdf3;
        border: 1px solid rgba(22,163,74,0.16);
        border-radius: 16px;
        padding: .95rem 1rem;
    }

    .assistant-bubble{
        background: #ffffff;
        border: 1px solid rgba(15,23,42,0.08);
        border-radius: 16px;
        padding: .95rem 1rem;
    }

    .sidebar-kpi{
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: .85rem .9rem;
        margin-bottom: .7rem;
        box-shadow: 0 6px 16px rgba(15,23,42,0.05);
    }

    .sidebar-kpi b{
        color: var(--green-soft);
    }
    </style>
    """, unsafe_allow_html=True)


# =========================================================
# ESTADO DA SESSÃO
# =========================================================
def init_session_state():
    defaults = {
        "chat": [],
        "db": None,
        "pdf_nome": None,
        "img_nome": None,
        "current_conversation_id": None,
        "loaded_conversation_id": None,
        "contador_perguntas": 0,
        "confirm_delete": False,
        "last_sources": [],
        "user_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


inject_css()
init_session_state()

# =========================================================
# LOGIN
# =========================================================
if not st.user.is_logged_in:
    st.markdown("""
    <style>
    .login-card {
        max-width: 420px;
        margin: 12vh auto;
        padding: 2rem;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        text-align: center;
    }
    .login-title {
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: .5rem;
        color: #16a34a;
    }
    .login-sub {
        color: #64748b;
        font-size: .95rem;
        margin-bottom: 1.5rem;
    }
    </style>

    <div class="login-card">
        <div class="login-title">MentorEdu</div>
        <div class="login-sub">
            Plataforma acadêmica inteligente para estudos e análise de conteúdo
        </div>
    </div>
    """, unsafe_allow_html=True)

if st.button("Continuar com Google", use_container_width=True):
    st.login()
    st.markdown(
        "<p style='text-align:center;color:#94a3b8;font-size:.8rem;margin-top:1rem;'>Ao continuar, você concorda com os termos de uso</p>",
        unsafe_allow_html=True
    )

    st.stop()
USER_ID = st.user.get("sub") or st.user.get("email")
st.session_state.user_id = USER_ID

# =========================================================
# SQLITE
# =========================================================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            pdf_path TEXT,
            pdf_name TEXT,
            image_path TEXT,
            image_name TEXT,
            owner_id TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)

    cur.execute("PRAGMA table_info(conversations)")
    cols = [row[1] for row in cur.fetchall()]
    if "owner_id" not in cols:
        cur.execute("ALTER TABLE conversations ADD COLUMN owner_id TEXT")

    conn.commit()
    conn.close()


init_db()
os.makedirs(UPLOAD_DIR, exist_ok=True)


def list_conversations():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, created_at, updated_at, pdf_name, image_name
        FROM conversations
        WHERE owner_id = ?
        ORDER BY updated_at DESC, id DESC
    """, (USER_ID,))
    rows = cur.fetchall()
    conn.close()
    return rows


def create_conversation(title="Nova conversa"):
    now = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO conversations (title, created_at, updated_at, owner_id)
        VALUES (?, ?, ?, ?)
    """, (title, now, now, USER_ID))
    cid = cur.lastrowid
    conn.commit()
    conn.close()
    return cid


def get_conversation(conversation_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, created_at, updated_at, pdf_path, pdf_name, image_path, image_name
        FROM conversations
        WHERE id = ? AND owner_id = ?
    """, (conversation_id, USER_ID))
    row = cur.fetchone()
    conn.close()
    return row


def rename_conversation(conversation_id, new_title):
    new_title = (new_title or "").strip()[:90]
    if not new_title:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE conversations
        SET title = ?, updated_at = ?
        WHERE id = ? AND owner_id = ?
    """, (new_title, datetime.utcnow().isoformat(), conversation_id, USER_ID))
    conn.commit()
    conn.close()


def delete_conversation(conversation_id):
    conv = get_conversation(conversation_id)
    if not conv:
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    cur.execute("DELETE FROM conversations WHERE id = ? AND owner_id = ?", (conversation_id, USER_ID))
    conn.commit()
    conn.close()

    conv_dir = os.path.join(UPLOAD_DIR, f"conv_{conversation_id}")
    if os.path.isdir(conv_dir):
        shutil.rmtree(conv_dir, ignore_errors=True)

    pdf_path, image_path = conv[4], conv[6]
    for path in [pdf_path, image_path]:
        if path and os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass


def update_conversation_timestamp(conversation_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE conversations
        SET updated_at = ?
        WHERE id = ? AND owner_id = ?
    """, (datetime.utcnow().isoformat(), conversation_id, USER_ID))
    conn.commit()
    conn.close()


def maybe_update_title_from_first_message(conversation_id, text):
    texto = (text or "").strip()
    if not texto:
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT title FROM conversations
        WHERE id = ? AND owner_id = ?
    """, (conversation_id, USER_ID))
    row = cur.fetchone()

    if row and row[0] == "Nova conversa":
        title = texto.replace("\n", " ")
        title = re.sub(r"\s+", " ", title).strip()[:72]
        cur.execute("""
            UPDATE conversations
            SET title = ?, updated_at = ?
            WHERE id = ? AND owner_id = ?
        """, (title, datetime.utcnow().isoformat(), conversation_id, USER_ID))
        conn.commit()

    conn.close()


def save_message(conversation_id, role, content):
    conv = get_conversation(conversation_id)
    if not conv:
        return

    now = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO messages (conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?)
    """, (conversation_id, role, content, now))
    cur.execute("""
        UPDATE conversations
        SET updated_at = ?
        WHERE id = ? AND owner_id = ?
    """, (now, conversation_id, USER_ID))
    conn.commit()
    conn.close()


def get_messages(conversation_id):
    conv = get_conversation(conversation_id)
    if not conv:
        return []

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT role, content, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
    """, (conversation_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def update_conversation_files(conversation_id, pdf_path=None, pdf_name=None, image_path=None, image_name=None):
    conn = get_conn()
    cur = conn.cursor()

    if pdf_path is not None:
        cur.execute("""
            UPDATE conversations
            SET pdf_path = ?, pdf_name = ?, updated_at = ?
            WHERE id = ? AND owner_id = ?
        """, (pdf_path, pdf_name, datetime.utcnow().isoformat(), conversation_id, USER_ID))

    if image_path is not None:
        cur.execute("""
            UPDATE conversations
            SET image_path = ?, image_name = ?, updated_at = ?
            WHERE id = ? AND owner_id = ?
        """, (image_path, image_name, datetime.utcnow().isoformat(), conversation_id, USER_ID))

    conn.commit()
    conn.close()


# =========================================================
# CLIENTE GROQ
# =========================================================
def carregar_cliente():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "A chave GROQ_API_KEY não foi encontrada nos Secrets do Streamlit Cloud."

    chave = str(st.secrets["GROQ_API_KEY"]).strip()
    if not chave:
        return None, "A chave GROQ_API_KEY está vazia."

    try:
        return Groq(api_key=chave), None
    except Exception as e:
        return None, f"Erro ao iniciar cliente Groq: {e}"


client = None
erro_cliente = None
try:
    client, erro_cliente = carregar_cliente()
except Exception as e:
    client = None
    erro_cliente = f"Erro ao iniciar cliente Groq: {e}"


# =========================================================
# UTILIDADES
# =========================================================
def pode_perguntar():
    return st.session_state.contador_perguntas < MAX_PERGUNTAS_SESSAO


def registrar_pergunta():
    st.session_state.contador_perguntas += 1


def resetar_sessao_visual():
    st.session_state.chat = []
    st.session_state.db = None
    st.session_state.pdf_nome = None
    st.session_state.img_nome = None
    st.session_state.contador_perguntas = 0
    st.session_state.loaded_conversation_id = None
    st.session_state.confirm_delete = False
    st.session_state.last_sources = []


def salvar_uploaded_file(conversation_id, uploaded_file):
    conv_dir = os.path.join(UPLOAD_DIR, f"conv_{conversation_id}")
    os.makedirs(conv_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", uploaded_file.name)
    path = os.path.join(conv_dir, f"{timestamp}_{safe_name}")

    uploaded_file.seek(0)
    with open(path, "wb") as f:
        f.write(uploaded_file.read())
    uploaded_file.seek(0)

    return path


def limpar_texto(txt: str) -> str:
    if not txt:
        return ""
    txt = txt.replace("\x00", " ")
    txt = txt.replace("\u00ad", "")
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()


def tokenizer_basico(txt: str) -> List[str]:
    return re.findall(r"[a-zA-ZÀ-ÿ0-9_]+", (txt or "").lower())


def render_texto_stream_seguro(container, texto: str, bubble_class: str = "assistant-bubble"):
    texto = html.escape(texto or "")
    container.markdown(
        f"""
        <div class="{bubble_class}">
            <pre style="white-space:pre-wrap; margin:0; font-family:inherit;">{texto}</pre>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_markdown_final_seguro(container, texto: str, bubble_class: str = "assistant-bubble"):
    with container:
        try:
            st.markdown(f"<div class='{bubble_class}'>", unsafe_allow_html=True)
            st.markdown(texto)
            st.markdown("</div>", unsafe_allow_html=True)
            return
        except Exception:
            pass

        try:
            texto_limpo = (texto or "").replace("\r\n", "\n").strip()
            st.markdown(f"<div class='{bubble_class}'>", unsafe_allow_html=True)
            st.markdown(texto_limpo)
            st.markdown("</div>", unsafe_allow_html=True)
            return
        except Exception:
            pass

        st.markdown(
            f"""
            <div class="{bubble_class}">
                <pre style="white-space:pre-wrap; margin:0; font-family:inherit;">{html.escape(texto or "")}</pre>
            </div>
            """,
            unsafe_allow_html=True,
        )


def remover_linhas_repetidas_paginas(paginas_texto: List[str]) -> List[str]:
    if len(paginas_texto) <= 2:
        return paginas_texto

    line_counter = Counter()
    for txt in paginas_texto:
        linhas = [limpar_texto(l) for l in txt.splitlines()]
        linhas = [l for l in linhas if l and len(l) <= 120]
        for l in set(linhas):
            line_counter[l] += 1

    repetidas = {
        linha for linha, qtd in line_counter.items()
        if qtd >= max(3, math.ceil(len(paginas_texto) * 0.45))
    }

    novas_paginas = []
    for txt in paginas_texto:
        linhas = txt.splitlines()
        filtradas = []
        for linha in linhas:
            l = limpar_texto(linha)
            if l and l in repetidas:
                continue
            filtradas.append(linha)
        novas_paginas.append(limpar_texto("\n".join(filtradas)))

    return novas_paginas


def chunk_text(texto: str, chunk_size: int = 900, overlap: int = 180) -> List[str]:
    texto = limpar_texto(texto)
    if not texto:
        return []

    paragrafos = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    chunks = []
    atual = ""

    for p in paragrafos:
        candidato = (atual + "\n\n" + p).strip() if atual else p
        if len(candidato) <= chunk_size:
            atual = candidato
        else:
            if atual:
                chunks.append(atual.strip())
            if len(p) <= chunk_size:
                atual = p
            else:
                inicio = 0
                while inicio < len(p):
                    fim = inicio + chunk_size
                    sub = p[inicio:fim].strip()
                    if sub:
                        chunks.append(sub)
                    if fim >= len(p):
                        break
                    inicio = max(0, fim - overlap)
                atual = ""

    if atual.strip():
        chunks.append(atual.strip())

    if overlap > 0 and len(chunks) > 1:
        chunks_overlap = []
        for i, ch in enumerate(chunks):
            if i == 0:
                chunks_overlap.append(ch)
                continue
            prev_tail = chunks[i - 1][-overlap:]
            combinado = (prev_tail + "\n" + ch).strip()
            chunks_overlap.append(combinado)
        chunks = chunks_overlap

    return [c for c in chunks if c.strip()]


def _extract_with_pymupdf(pdf_bytes: bytes) -> List[Dict]:
    blocks = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    paginas_texto = []
    paginas_blocos = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        raw_text = limpar_texto(page.get_text("text"))
        paginas_texto.append(raw_text)

        page_blocks = []
        try:
            raw_blocks = page.get_text("blocks")
            raw_blocks = sorted(raw_blocks, key=lambda b: (round(b[1], 1), round(b[0], 1)))
            for block in raw_blocks:
                txt = limpar_texto(block[4])
                if txt and len(txt) >= 20:
                    page_blocks.append(txt)
        except Exception:
            if raw_text:
                page_blocks = [raw_text]

        paginas_blocos.append(page_blocks)

    paginas_texto = remover_linhas_repetidas_paginas(paginas_texto)

    for i, page_blocks in enumerate(paginas_blocos):
        if page_blocks:
            for b in page_blocks:
                blocks.append({"page": i + 1, "text": b, "source": "pdf"})
        else:
            if paginas_texto[i]:
                blocks.append({"page": i + 1, "text": paginas_texto[i], "source": "pdf"})

    doc.close()
    return blocks


def _extract_with_pypdf(pdf_bytes: bytes) -> List[Dict]:
    blocks = []
    reader = PdfReader(io.BytesIO(pdf_bytes))
    paginas_texto = []

    for i, pagina in enumerate(reader.pages):
        try:
            txt = limpar_texto(pagina.extract_text() or "")
        except Exception:
            txt = ""
        paginas_texto.append(txt)

    paginas_texto = remover_linhas_repetidas_paginas(paginas_texto)

    for i, txt in enumerate(paginas_texto):
        if txt:
            blocks.append({"page": i + 1, "text": txt, "source": "pdf"})
    return blocks


def processar_pdf_from_bytes(pdf_bytes: bytes) -> Optional[Dict]:
    blocks = []
    try:
        blocks = _extract_with_pymupdf(pdf_bytes)
    except Exception:
        blocks = []

    if not blocks:
        try:
            blocks = _extract_with_pypdf(pdf_bytes)
        except Exception:
            blocks = []

    if not blocks:
        return None

    textos = []
    pgs = []
    metas = []

    for bloco in blocks:
        chunks = chunk_text(bloco.get("text", ""))
        for ch in chunks:
            textos.append(ch)
            pgs.append(bloco.get("page"))
            metas.append({
                "page": bloco.get("page"),
                "source": bloco.get("source", "pdf"),
            })

    if not textos:
        return None

    return {
        "txts": textos,
        "pgs": pgs,
        "metas": metas,
        "source_name": "pdf",
    }


def processar_pdf_from_path(pdf_path: str) -> Optional[Dict]:
    with open(pdf_path, "rb") as f:
        return processar_pdf_from_bytes(f.read())


def score_keywords(query: str, text: str) -> float:
    q_tokens = set(tokenizer_basico(query))
    if not q_tokens:
        return 0.0
    t_tokens = set(tokenizer_basico(text))
    if not t_tokens:
        return 0.0
    inter = len(q_tokens.intersection(t_tokens))
    return inter / max(1, len(q_tokens))


def buscar_contexto_em_db(db: Dict, pergunta: str, k: int = 6) -> List[Dict]:
    if not db or not pergunta:
        return []

    resultados = []
    for i, texto in enumerate(db["txts"]):
        kw = score_keywords(pergunta, texto)
        if kw > 0:
            resultados.append({
                "score": kw,
                "semantic_score": 0.0,
                "keyword_score": kw,
                "page": db["pgs"][i],
                "text": texto,
                "source": db["metas"][i].get("source"),
            })

    resultados = sorted(resultados, key=lambda x: x["score"], reverse=True)
    return resultados[:k]


def buscar_contexto(pergunta: str, k: int = 5) -> Tuple[str, List[str]]:
    resultados = []

    if st.session_state.db:
        resultados.extend(buscar_contexto_em_db(st.session_state.db, pergunta, k=k))

    if not resultados:
        return "", []

    resultados = sorted(resultados, key=lambda x: x["score"], reverse=True)

    selecionados = []
    referencias = []
    vistos = set()

    for item in resultados:
        ref = f"{item['source']}|{item['page']}|{item['text'][:100]}"
        if ref in vistos:
            continue
        vistos.add(ref)
        selecionados.append(item)

        if item["source"] == "pdf" and item["page"]:
            referencias.append(f"PDF pág. {item['page']}")

        if len(selecionados) >= k:
            break

    contexto = []
    for item in selecionados:
        marcador = "[PDF"
        if item["page"]:
            marcador += f" | Página {item['page']}"
        marcador += "]"
        contexto.append(f"{marcador} {item['text']}")

    return "\n\n".join(contexto), referencias


def imagem_path_para_data_url(path):
    ext = os.path.splitext(path)[1].lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    mime = mime_map.get(ext, "image/png")
    with open(path, "rb") as f:
        dados = f.read()
    b64 = base64.b64encode(dados).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def construir_memoria_conversa(max_msgs: int = 6) -> str:
    msgs = st.session_state.chat[-max_msgs:]
    linhas = []
    for msg in msgs:
        role = "Usuário" if msg["role"] == "user" else "Assistente"
        linhas.append(f"{role}: {msg['content']}")
    return "\n".join(linhas).strip()


# =========================================================
# MENTORES
# =========================================================
def obter_estrutura_mentores():
    return {
        "Ensino Médio": {
            "disciplinas": {
                "Física": ["Didático", "Feynman", "GrokFísica"],
                "Química": ["Didático", "Vestibular"],
                "Matemática": ["Didático", "Feynman", "Vestibular"],
                "Metodologia Científica": ["Professor", "Socrático"],
            }
        },
        "Ensino Superior": {
            "disciplinas": {
                "Física": ["Professor", "Cientista", "Feynman"],
                "Química": ["Professor", "Cientista"],
                "Matemática": ["Professor", "Cientista"],
                "Metodologia Científica": ["Professor", "Orientador de TCC"],
            }
        }
    }


def resumo_mentor(nivel: str, disciplina: str, estilo: str) -> str:
    descricoes = {
        "Didático": "Explica passo a passo com linguagem simples e exemplos claros.",
        "Feynman": "Explica conceitos complexos de forma extremamente simples usando analogias.",
        "Vestibular": "Foco em resolução de questões e estratégias para provas.",
        "Professor": "Explicação estruturada como em uma aula universitária.",
        "Cientista": "Abordagem técnica e conceitual com maior rigor científico.",
        "Socrático": "Estimula o raciocínio fazendo perguntas que levam à resposta.",
        "Orientador de TCC": "Ajuda em pesquisa, metodologia científica e estrutura acadêmica.",
        "GrokFísica": "Explica física com humor leve e analogias divertidas.",
    }
    return f"{nivel} • {disciplina} • {descricoes.get(estilo, 'Mentor educacional especializado.')}"


def obter_prompt_mentor_especializado(nivel: str, disciplina: str, estilo: str) -> str:
    base = f"""
Você é o MentorEdu, um assistente educacional especializado em {disciplina} para {nivel}.

Seu papel é ajudar estudantes a aprender de forma clara, humana e didática.

REGRAS IMPORTANTES:
- Nunca invente conteúdo do PDF ou da imagem.
- Se não souber algo, diga com honestidade.
- Se houver cálculo, mostre o raciocínio passo a passo.
- Se houver conceito, explique primeiro a intuição e depois a definição formal.
- Priorize clareza em vez de complexidade.
"""

    if nivel == "Ensino Médio":
        nivel_instrucao = """
NÍVEL DE ENSINO MÉDIO:
- Use linguagem mais acessível.
- Explique como se estivesse ajudando um aluno em formação.
- Evite excesso de formalismo.
- Dê exemplos práticos do cotidiano quando possível.
"""
    else:
        nivel_instrucao = """
NÍVEL DE ENSINO SUPERIOR:
- Use maior rigor conceitual.
- Pode aprofundar mais a teoria.
- Relacione conceitos com linguagem acadêmica quando necessário.
- Mantenha clareza mesmo em temas mais técnicos.
"""

    estilos_instrucao = {
        "Didático": """
ESTILO DIDÁTICO:
- Explique passo a passo.
- Use linguagem simples.
- Use exemplos claros.
""",
        "Feynman": """
ESTILO FEYNMAN:
- Explique como se estivesse ensinando alguém que nunca viu o assunto.
- Use analogias do cotidiano.
- Simplifique sem perder a precisão.
""",
        "Vestibular": """
ESTILO VESTIBULAR:
- Foque no que mais cai em provas.
- Mostre atalhos e estratégias de resolução.
- Seja objetivo e treinável.
""",
        "Professor": """
ESTILO PROFESSOR:
- Explique como um professor em sala de aula.
- Seja organizado, claro e progressivo.
""",
        "Cientista": """
ESTILO CIENTISTA:
- Use maior rigor conceitual.
- Destaque relações teóricas e precisão científica.
""",
        "Socrático": """
ESTILO SOCRÁTICO:
- Estimule o raciocínio com perguntas.
- Não entregue tudo de imediato se for melhor conduzir o aluno.
""",
        "Orientador de TCC": """
ESTILO ORIENTADOR DE TCC:
- Ajude com pesquisa, escrita acadêmica, metodologia e estruturação científica.
- Oriente com clareza e organização.
""",
        "GrokFísica": """
ESTILO GROKFÍSICA:
- Explique com tom humano, leve e inteligente.
- Pode usar humor e analogias divertidas quando combinar.
- Não perca a precisão do conteúdo.
"""
    }

    prompts_disciplina = {
        "Física": """
DISCIPLINA: FÍSICA
- Explique movimento, força, energia, eletricidade, ondas, termologia e outros temas físicos com clareza.
- Una intuição física com cálculo quando necessário.
- Ajude o aluno a entender o fenômeno, não só decorar fórmula.
""",
        "Química": """
DISCIPLINA: QUÍMICA
- Explique estrutura da matéria, tabela periódica, ligações, reações, estequiometria, soluções e outros temas químicos.
- Mostre lógica química e interpretação, não apenas memorização.
""",
        "Matemática": """
DISCIPLINA: MATEMÁTICA
- Explique álgebra, funções, geometria, trigonometria, cálculo e raciocínio matemático conforme o nível.
- Mostre o passo a passo quando necessário.
- Valorize a lógica por trás da conta.
""",
        "Metodologia Científica": """
DISCIPLINA: METODOLOGIA CIENTÍFICA
- Ajude com pesquisa, problema, hipótese, objetivos, justificativa, revisão bibliográfica, metodologia, resumo, artigo e escrita acadêmica.
- Explique como estruturar pensamento científico de forma clara.
""",
    }

    return (
        base
        + "\n"
        + nivel_instrucao
        + "\n"
        + estilos_instrucao.get(estilo, "")
        + "\n"
        + prompts_disciplina.get(disciplina, "")
    )


def obter_instrucao_modo(modo_atual: str) -> str:
    if modo_atual == "Matemática":
        return """
Você está no modo Matemática.
- Priorize resolução, demonstração, interpretação matemática, gráficos e explicações conceituais.
- Quando houver matemática, use LaTeX.
- Se houver PDF ou imagem, use esse material como apoio principal.
- Organize a resposta em etapas.
"""
    elif modo_atual == "Análise de Conteúdo":
        return """
Você está no modo Análise de Conteúdo.
- Priorize interpretação de PDF e imagem.
- Resuma, compare fontes, explique páginas, identifique conceitos e relacione materiais.
- Se houver PDF e imagem, integre os dois em vez de tratá-los separadamente.
"""
    elif modo_atual == "Chat Criativo":
        return """
Você está no modo Chat Criativo.
- Ajude com ideias, aulas, planejamentos, metodologias, projetos e apresentações.
- Seja criativo, estratégico, útil e prático.
"""
    elif modo_atual == "GrokFísica (zoeira + didática)":
        return """
Você está no modo GrokFísica (zoeira + didática).
- Fale de forma humana, descontraída, engraçada e inteligente.
- Pode usar humor, ironia leve e comentários debochados quando combinar.
- Soe como alguém esperto explicando, não como apostila.
- Evite respostas longas demais.
- Se a pergunta for simples, responda de forma rápida e boa.
- Se a pergunta envolver cálculo ou física, explique sem perder a personalidade.
"""
    return """
Você está no modo Chat Geral.
- Responda com clareza, objetividade e adaptação ao mentor selecionado.
"""


def montar_prompt_usuario(
    prompt_usuario: str,
    modo_atual: str,
    contexto: str = "",
    memoria: str = "",
    referencias: Optional[List[str]] = None
) -> str:
    referencias = referencias or []

    instrucoes_math = """
REGRAS IMPORTANTES DE FORMATAÇÃO:
- Sempre que houver matemática, use LaTeX corretamente.
- Para expressões curtas, use $...$
- Para contas centrais e fórmulas destacadas, use $$...$$
- Nunca abra um bloco LaTeX sem fechá-lo.
- Organize a resolução em etapas.
"""

    return f"""
{obter_instrucao_modo(modo_atual)}

{instrucoes_math if modo_atual == "Matemática" else ""}

Memória recente da conversa:
{memoria if memoria else "Sem memória recente relevante."}

Contexto recuperado de materiais:
{contexto if contexto else "Nenhum contexto documental adicional disponível."}

Referências de apoio:
{", ".join(referencias) if referencias else "Nenhuma referência específica."}

Pedido do usuário:
{prompt_usuario}

Instruções finais:
- Responda de forma natural, humana e fluida.
- Evite textão quando não for necessário.
- Se o usuário pedir detalhamento, aprofunde.
- Se houver contexto de PDF/imagem, use esse contexto sem inventar.
"""


# =========================================================
# GROQ
# =========================================================
def analisar_imagem_com_vision(
    prompt_usuario: str,
    prompt_sistema: str,
    modo_atual: str,
    image_path: str,
    contexto: str = "",
    referencias: Optional[List[str]] = None,
):
    if client is None:
        return "Cliente Groq não disponível."

    data_url = imagem_path_para_data_url(image_path)
    memoria = construir_memoria_conversa()
    prompt_final = montar_prompt_usuario(
        prompt_usuario=prompt_usuario,
        modo_atual=modo_atual,
        contexto=contexto,
        memoria=memoria,
        referencias=referencias or [],
    )

    instrucao = (
        f"{prompt_sistema}\n\n"
        f"Você pode receber uma imagem contendo exercício, quadro, caderno, print, slide, gráfico ou documento. "
        f"Transcreva o que for legível, interprete com cuidado e integre com o contexto recuperado quando ele existir. "
        f"Se a imagem estiver parcialmente ilegível, diga isso.\n\n"
        f"{prompt_final}"
    )

    resp = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {"role": "system", "content": instrucao},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_usuario},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        temperature=0.2,
        max_completion_tokens=1800,
        stream=False,
    )
    return (resp.choices[0].message.content or "").strip()


def responder_texto(prompt_usuario: str, prompt_sistema: str, contexto: str, modo_atual: str, referencias=None):
    referencias = referencias or []
    memoria = construir_memoria_conversa()

    mensagem_usuario = montar_prompt_usuario(
        prompt_usuario=prompt_usuario,
        modo_atual=modo_atual,
        contexto=contexto,
        memoria=memoria,
        referencias=referencias,
    )

    stream = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": mensagem_usuario},
        ],
        temperature=0.35,
        max_completion_tokens=2200,
        stream=True,
    )

    resposta = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            resposta += delta
            yield resposta


# =========================================================
# GRÁFICOS E VISUAIS MATEMÁTICOS
# =========================================================
def extrair_expressao_grafico(prompt: str):
    texto = prompt.lower().strip()
    padroes = [
        r"gr[aá]fico de (.+)",
        r"plot de (.+)",
        r"desenhe a fun[cç][aã]o (.+)",
        r"fa[cç]a o gr[aá]fico de (.+)",
    ]
    for padrao in padroes:
        m = re.search(padrao, texto)
        if m:
            return m.group(1).strip(" .,:;")
    return None


def normalizar_expressao(expr: str):
    expr = expr.replace("^", "**")
    expr = expr.replace("sen(", "sin(")
    expr = expr.replace("tg(", "tan(")
    expr = expr.replace("ln(", "log(")
    return expr


def expressao_valida(expr: str):
    proibidos = ["__", "import", "exec", "eval", "open", "os.", "sys.", "subprocess"]
    expr_lower = expr.lower()
    return not any(item in expr_lower for item in proibidos)


def gerar_grafico_basico(expressao_str: str):
    try:
        expr_limpa = normalizar_expressao(expressao_str)
        x = sp.symbols("x")
        expr = sp.sympify(expr_limpa)
        f = sp.lambdify(x, expr, "numpy")

        valores_x = np.linspace(-10, 10, 600)
        valores_y = f(valores_x)
        y = np.array(valores_y, dtype=float)
        y[np.abs(y) > 1e6] = np.nan

        fig, ax = plt.subplots(figsize=(8.5, 4.6))
        ax.plot(valores_x, y, linewidth=2.0)
        ax.axhline(0, linewidth=1)
        ax.axvline(0, linewidth=1)
        ax.set_title(f"Gráfico de y = {expressao_str}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.grid(True, alpha=0.35)
        st.pyplot(fig)
        plt.close(fig)
        return True, None
    except Exception as e:
        return False, str(e)


def gerar_quadro_formula(titulo: str, linhas: List[str]):
    altura = max(4.6, 1.35 + 0.95 * len(linhas))
    fig, ax = plt.subplots(figsize=(10, altura))
    ax.axis("off")

    y = 0.93
    ax.text(0.02, y, titulo, fontsize=18, fontweight="bold", transform=ax.transAxes)
    y -= 0.12

    for linha in linhas:
        ax.text(0.03, y, linha, fontsize=15.5, transform=ax.transAxes)
        y -= 0.11

    st.pyplot(fig)
    plt.close(fig)


def demonstrar_equacao_circunferencia():
    linhas = [
        r"Definição: a circunferência é o conjunto dos pontos cuja distância ao centro é constante.",
        r"$d(P,C)=r$",
        r"Se $P=(x,y)$ e $C=(a,b)$, então:",
        r"$d(P,C)=\sqrt{(x-a)^2+(y-b)^2}$",
        r"Logo:",
        r"$\sqrt{(x-a)^2+(y-b)^2}=r$",
        r"Elevando ao quadrado:",
        r"$$(x-a)^2+(y-b)^2=r^2$$",
    ]
    gerar_quadro_formula("Demonstração da equação da circunferência", linhas)


def demonstrar_bhaskara():
    linhas = [
        r"Equação do 2º grau: $ax^2+bx+c=0$, com $a\neq0$",
        r"Dividindo tudo por $a$: $x^2+\frac{b}{a}x+\frac{c}{a}=0$",
        r"Isolando o termo constante: $x^2+\frac{b}{a}x=-\frac{c}{a}$",
        r"Completando quadrados:",
        r"$x^2+\frac{b}{a}x+\frac{b^2}{4a^2}=-\frac{c}{a}+\frac{b^2}{4a^2}$",
        r"$\left(x+\frac{b}{2a}\right)^2=\frac{b^2-4ac}{4a^2}$",
        r"Extraindo a raiz:",
        r"$x+\frac{b}{2a}=\pm\frac{\sqrt{b^2-4ac}}{2a}$",
        r"Resultado final:",
        r"$$x=\frac{-b\pm\sqrt{b^2-4ac}}{2a}$$",
    ]
    gerar_quadro_formula("Demonstração da fórmula de Bhaskara", linhas)


def demonstrar_derivada_potencia():
    linhas = [
        r"Queremos derivar $f(x)=x^n$.",
        r"Pela regra da potência:",
        r"$$\frac{d}{dx}(x^n)=n x^{n-1}$$",
        r"Exemplo: se $f(x)=x^5$, então",
        r"$$f'(x)=5x^4$$",
    ]
    gerar_quadro_formula("Derivada da potência", linhas)


def demonstrar_integral_potencia():
    linhas = [
        r"Para $n\neq -1$:",
        r"$$\int x^n\,dx=\frac{x^{n+1}}{n+1}+C$$",
        r"Exemplo:",
        r"$$\int x^3\,dx=\frac{x^4}{4}+C$$",
        r"Caso especial:",
        r"$$\int \frac{1}{x}\,dx=\ln|x|+C$$",
    ]
    gerar_quadro_formula("Integral da potência", linhas)


def demonstrar_equacao_reta():
    linhas = [
        r"Equação reduzida da reta:",
        r"$$y=mx+b$$",
        r"Onde $m$ é o coeficiente angular e $b$ o coeficiente linear.",
        r"Forma ponto-inclinação:",
        r"$$y-y_1=m(x-x_1)$$",
    ]
    gerar_quadro_formula("Equações da reta", linhas)


def desenhar_circunferencia_trigonometrica():
    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    t = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(t), np.sin(t), linewidth=2)
    ax.axhline(0, linewidth=1)
    ax.axvline(0, linewidth=1)

    pontos = [
        (0, "0"), (np.pi/6, "π/6"), (np.pi/4, "π/4"), (np.pi/3, "π/3"),
        (np.pi/2, "π/2"), (2*np.pi/3, "2π/3"), (3*np.pi/4, "3π/4"),
        (5*np.pi/6, "5π/6"), (np.pi, "π"), (3*np.pi/2, "3π/2"),
    ]
    for ang, label in pontos:
        x, y = np.cos(ang), np.sin(ang)
        ax.plot(x, y, "o")
        ax.text(x * 1.12, y * 1.12, label, fontsize=9, ha="center", va="center")

    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Circunferência trigonométrica")
    ax.grid(True, alpha=0.35)
    st.pyplot(fig)
    plt.close(fig)


def desenhar_triangulo_retangulo():
    fig, ax = plt.subplots(figsize=(7.2, 5))
    A, B, C = (0, 0), (4, 0), (4, 3)

    xs = [A[0], B[0], C[0], A[0]]
    ys = [A[1], B[1], C[1], A[1]]
    ax.plot(xs, ys, marker="o", linewidth=2)

    ax.text(A[0] - 0.2, A[1] - 0.2, "A")
    ax.text(B[0] + 0.1, B[1] - 0.2, "B")
    ax.text(C[0] + 0.1, C[1] + 0.1, "C")

    ax.text(2, -0.3, "cateto = 4", ha="center")
    ax.text(4.25, 1.5, "cateto = 3", va="center", rotation=90)
    ax.text(2.0, 1.75, "hipotenusa = 5")
    ax.plot([3.6, 3.6, 4.0], [0.0, 0.4, 0.4], color="black")

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-0.5, 5.5)
    ax.set_ylim(-0.8, 4.2)
    ax.set_title("Triângulo retângulo (3, 4, 5)")
    ax.grid(True, alpha=0.35)
    st.pyplot(fig)
    plt.close(fig)


def desenhar_vetores():
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    origem = np.array([0, 0])
    u = np.array([4, 2])
    v = np.array([2, 4])
    soma = u + v

    ax.quiver(*origem, *u, angles="xy", scale_units="xy", scale=1)
    ax.quiver(*origem, *v, angles="xy", scale_units="xy", scale=1)
    ax.quiver(*origem, *soma, angles="xy", scale_units="xy", scale=1)

    ax.text(u[0] + 0.1, u[1], "u = (4,2)")
    ax.text(v[0] + 0.1, v[1], "v = (2,4)")
    ax.text(soma[0] + 0.1, soma[1], "u + v")

    ax.axhline(0, linewidth=1)
    ax.axvline(0, linewidth=1)
    ax.set_xlim(-1, 8)
    ax.set_ylim(-1, 8)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Representação de vetores no plano")
    ax.grid(True, alpha=0.35)
    st.pyplot(fig)
    plt.close(fig)


def desenhar_parabola_exemplo():
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    x = np.linspace(-6, 6, 400)
    y = (x - 1) ** 2 - 4
    ax.plot(x, y, linewidth=2)
    ax.scatter([1], [-4], s=60)
    ax.text(1.15, -4, "Vértice (1, -4)")
    ax.axhline(0, linewidth=1)
    ax.axvline(0, linewidth=1)
    ax.set_title("Parábola exemplo: y = (x - 1)^2 - 4")
    ax.grid(True, alpha=0.35)
    st.pyplot(fig)
    plt.close(fig)


def detectar_visual_matematico(prompt: str):
    texto = (prompt or "").lower()

    if any(k in texto for k in ["circunferência trigonométrica", "circulo trigonometrico", "círculo trigonométrico", "trigonometrica"]):
        return "circ_trig"
    if any(k in texto for k in ["triângulo retângulo", "triangulo retangulo", "triângulo", "triangulo"]) and "gráfico de" not in texto and "grafico de" not in texto:
        return "triangulo"
    if any(k in texto for k in ["vetor", "vetores"]):
        return "vetores"
    if any(k in texto for k in ["parábola", "parabola"]) and "gráfico de" not in texto and "grafico de" not in texto:
        return "parabola"
    if any(k in texto for k in ["equação da circunferência", "equacao da circunferencia", "demonstre a circunferência", "demonstre a circunferencia"]):
        return "demo_circ"
    if any(k in texto for k in ["bhaskara", "fórmula de bhaskara", "formula de bhaskara"]):
        return "demo_bhaskara"
    if any(k in texto for k in ["derivada da potência", "derivada da potencia", "regra da potência", "regra da potencia"]):
        return "demo_derivada"
    if any(k in texto for k in ["integral da potência", "integral da potencia", "integração da potência", "integracao da potencia"]):
        return "demo_integral"
    if any(k in texto for k in ["equação da reta", "equacao da reta", "reta no plano", "forma da reta"]):
        return "demo_reta"

    return None


def renderizar_visual_matematico(prompt: str):
    tipo = detectar_visual_matematico(prompt)

    if tipo == "circ_trig":
        desenhar_circunferencia_trigonometrica()
        return True
    if tipo == "triangulo":
        desenhar_triangulo_retangulo()
        return True
    if tipo == "vetores":
        desenhar_vetores()
        return True
    if tipo == "parabola":
        desenhar_parabola_exemplo()
        return True
    if tipo == "demo_circ":
        demonstrar_equacao_circunferencia()
        return True
    if tipo == "demo_bhaskara":
        demonstrar_bhaskara()
        return True
    if tipo == "demo_derivada":
        demonstrar_derivada_potencia()
        return True
    if tipo == "demo_integral":
        demonstrar_integral_potencia()
        return True
    if tipo == "demo_reta":
        demonstrar_equacao_reta()
        return True

    return False


def renderizar_resposta_matematica(resposta_texto: str):
    st.markdown("<div class='math-box'>", unsafe_allow_html=True)

    try:
        st.markdown(resposta_texto)
    except Exception:
        texto_limpo = (resposta_texto or "").strip()
        if texto_limpo.count("$$") % 2 != 0:
            texto_limpo = texto_limpo.replace("$$", "$", 1)

        try:
            st.markdown(texto_limpo)
        except Exception:
            st.markdown(
                f"<pre style='white-space:pre-wrap; margin:0; font-family:inherit;'>{html.escape(resposta_texto or '')}</pre>",
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    padrao = r"(?:\*\*Resposta final:?\*\*|Resposta final:)(.*)"
    m = re.search(padrao, resposta_texto, flags=re.IGNORECASE | re.DOTALL)
    if m:
        trecho = m.group(1).strip()
        if trecho:
            st.markdown("<div class='final-answer-box'>", unsafe_allow_html=True)
            st.markdown("**Resposta final**")
            try:
                st.markdown(trecho)
            except Exception:
                st.markdown(
                    f"<pre style='white-space:pre-wrap; margin:0; font-family:inherit;'>{html.escape(trecho)}</pre>",
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# CONVERSAS
# =========================================================
def carregar_conversa_no_estado(conversation_id):
    conv = get_conversation(conversation_id)
    if conv is None:
        return

    _, _, _, _, pdf_path, pdf_name, image_path, image_name = conv

    st.session_state.chat = [
        {"role": role, "content": content}
        for role, content, _ in get_messages(conversation_id)
    ]
    st.session_state.pdf_nome = pdf_name
    st.session_state.img_nome = image_name
    st.session_state.last_sources = []

    if pdf_path and os.path.exists(pdf_path):
        try:
            st.session_state.db = processar_pdf_from_path(pdf_path)
        except Exception:
            st.session_state.db = None
    else:
        st.session_state.db = None

    st.session_state.current_conversation_id = conversation_id
    st.session_state.loaded_conversation_id = conversation_id
    st.session_state.confirm_delete = False


def formatar_conversation_label(row):
    conv_id, title, created_at, updated_at, pdf_name, image_name = row
    extras = []
    if pdf_name:
        extras.append("PDF")
    if image_name:
        extras.append("IMG")
    sufixo = f" [{' | '.join(extras)}]" if extras else ""
    return f"{title}{sufixo}"


# =========================================================
# CONVERSA INICIAL
# =========================================================
rows = list_conversations()
if not rows:
    cid = create_conversation()
    st.session_state.current_conversation_id = cid
    carregar_conversa_no_estado(cid)
elif st.session_state.current_conversation_id is None:
    st.session_state.current_conversation_id = rows[0][0]
    carregar_conversa_no_estado(rows[0][0])


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    if st.user.is_logged_in:
        st.markdown("### 👤 Conta")

        nome = st.user.name.split()[0] if st.user.name else "Usuário"
        st.markdown(f"**{nome}**")
        st.caption(getattr(st.user, "email", ""))

        if st.button("Sair", use_container_width=True):
            st.logout()

        st.markdown("---")

    if os.path.exists(IF_LOGO):
        st.image(IF_LOGO, use_container_width=True)

    st.markdown("### Conversas")

    conv_rows = list_conversations()

    conv_map = {
        f"{formatar_conversation_label(r)} • #{r[0]}": r[0]
        for r in conv_rows
    }

    conv_keys = list(conv_map.keys())
    conv_ids = list(conv_map.values())

    current_id = st.session_state.current_conversation_id

    if current_id not in conv_ids and conv_ids:
        current_id = conv_ids[0]

    if conv_keys:
        idx = conv_ids.index(current_id)
        escolhido_key = st.selectbox("Selecione a conversa", conv_keys, index=idx)
        escolhido_id = conv_map[escolhido_key]
    else:
        escolhido_id = create_conversation()

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("Nova conversa", use_container_width=True):
            novo_id = create_conversation()
            st.session_state.current_conversation_id = novo_id
            resetar_sessao_visual()
            carregar_conversa_no_estado(novo_id)
            st.rerun()

    with col_b:
        if st.button("Recarregar", use_container_width=True):
            carregar_conversa_no_estado(escolhido_id)
            st.rerun()

    if escolhido_id != st.session_state.current_conversation_id:
        carregar_conversa_no_estado(escolhido_id)
        st.rerun()

    st.markdown("---")
    st.markdown("### Gerenciar conversa")

    conv_atual = get_conversation(st.session_state.current_conversation_id)
    titulo_atual = conv_atual[1] if conv_atual else ""

    novo_titulo = st.text_input("Renomear conversa", value=titulo_atual)

    if st.button("Salvar nome", use_container_width=True):
        if novo_titulo.strip():
            rename_conversation(st.session_state.current_conversation_id, novo_titulo)
            st.rerun()

    st.session_state.confirm_delete = st.checkbox(
        "Confirmar exclusão da conversa atual",
        value=st.session_state.confirm_delete
    )

    if st.button("Apagar conversa atual", use_container_width=True):
        if st.session_state.confirm_delete:
            apagar_id = st.session_state.current_conversation_id
            delete_conversation(apagar_id)
            resetar_sessao_visual()

            restantes = list_conversations()
            if restantes:
                novo_atual = restantes[0][0]
            else:
                novo_atual = create_conversation()

            st.session_state.current_conversation_id = novo_atual
            carregar_conversa_no_estado(novo_atual)
            st.rerun()
        else:
            st.warning("Marque a confirmação antes de apagar.")

    # =========================================================
    # ESCOLHA DO MENTOR
    # =========================================================
with st.sidebar:
    st.markdown("---")
    st.markdown("### Escolha seu Mentor")

    st.markdown(
        """
        <div class="folder-hint">
        Escolha o <b>nível de ensino</b>, depois a <b>disciplina</b> e por fim o <b>estilo do professor</b>.
        </div>
        """,
        unsafe_allow_html=True
    )

    estrutura = obter_estrutura_mentores()

    nivel_escolhido = st.radio(
        "Nível de ensino",
        ["Ensino Médio", "Ensino Superior"]
    )

    disciplinas = list(estrutura[nivel_escolhido]["disciplinas"].keys())

    disciplina_escolhida = st.selectbox(
        "Disciplina",
        disciplinas
    )

    estilos = estrutura[nivel_escolhido]["disciplinas"][disciplina_escolhida]

    estilo_escolhido = st.radio(
        "Estilo do professor",
        estilos
    )

    st.markdown(
        f"""
        <div class="mentor-card">
            <h4>{disciplina_escolhida} • {estilo_escolhido}</h4>
            <p>{resumo_mentor(nivel_escolhido, disciplina_escolhida, estilo_escolhido)}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    modo = st.selectbox(
        "Modo de trabalho",
        [
            "Chat Geral",
            "Análise de Conteúdo",
            "Matemática",
            "Chat Criativo",
            "GrokFísica (zoeira + didática)"
        ],
    )

    st.markdown("---")
    st.markdown("### Estado da sessão")

    conv = get_conversation(st.session_state.current_conversation_id)
    pdf_name = conv[5] if conv else None
    image_name = conv[7] if conv else None

    st.markdown(
        f"""
        <div class="sidebar-kpi">
            <div><b>Perguntas</b></div>
            <div>{st.session_state.contador_perguntas}/{MAX_PERGUNTAS_SESSAO}</div>
        </div>

        <div class="sidebar-kpi">
            <div><b>PDF ativo</b></div>
            <div>{pdf_name if pdf_name else 'Nenhum'}</div>
        </div>

        <div class="sidebar-kpi">
            <div><b>Imagem ativa</b></div>
            <div>{image_name if image_name else 'Nenhuma'}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# CABEÇALHO
# =========================================================
st.markdown(
    f"""
    <div class="hero-wrap">
        <div class="hero-card">
            <div style="text-align:center;">
                <div class="project-badge">{PROJECT_NAME}</div>
                <div class="main-title">{APP_NAME}</div>
                <div class="subtitle">
                    Plataforma acadêmica para apoio em estudos, análise de materiais e orientação educacional
                </div>
                <div class="chip-wrap">
                    <span class="if-chip">Docentes</span>
                    <span class="if-chip">Discentes</span>
                    <span class="if-chip">PDF + Imagem</span>
                    <span class="if-chip">Ensino Superior</span>
                    <span class="if-chip">Iniciação Científica</span>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Como usar o MentorEdu"):
    st.markdown("""
- Escolha o **nível de ensino**.
- Escolha a **disciplina**.
- Escolha o **estilo do professor**.
- Escolha um **modo de trabalho**.
- Use o campo de mensagem abaixo e clique no **+** para anexar **PDF** ou **imagem**.

### Estrutura de mentores

**Ensino Médio**
- Física
- Química
- Matemática
- Metodologia Científica

**Ensino Superior**
- Física
- Química
- Matemática
- Metodologia Científica

### Modos disponíveis

**Análise de Conteúdo**
- interpretar PDF
- interpretar imagem
- comparar materiais
- resumir conteúdos
- explicar páginas

**Matemática**
- resolver exercícios
- interpretar foto de questão
- usar PDF matemático como apoio
- gerar gráficos
- mostrar figuras matemáticas
- explicar fórmulas e demonstrações

**Chat Geral**
- conversar normalmente
- tirar dúvidas
- pedir explicações e orientações

**Chat Criativo**
- desenvolver ideias
- planejar aula
- discutir metodologia
- estruturar trabalho
- pensar apresentação

### Exemplos
- Explique esta imagem e relacione com o PDF
- Resuma o capítulo 2 do PDF
- Faça o gráfico de $x^2 - 4$
- Demonstre a fórmula de Bhaskara
- Me ajude a montar um projeto de iniciação científica
- Como estruturar um trabalho científico?
""")


# =========================================================
# STATUS
# =========================================================
c1, c2, c3 = st.columns(3)

with c1:
    status_text = "Groq conectada" if not erro_cliente else "Erro de configuração"
    status_class = "status-ok" if not erro_cliente else "status-danger"
    st.markdown(
        f"""<div class="status-card">
                <h4>Conexão de IA</h4>
                <div style="margin-top:.55rem;" class="{status_class}">{status_text}</div>
                <div style="margin-top:.5rem;color:#94a3b8;font-size:.88rem;line-height:1.5;">
                    Modelo textual e visão habilitados quando a chave estiver correta.
                </div>
            </div>""",
        unsafe_allow_html=True
    )

with c2:
    pdf_info = st.session_state.pdf_nome if st.session_state.pdf_nome else "Sem PDF ativo"
    css_class = "status-info" if st.session_state.pdf_nome else "status-warn"
    st.markdown(
        f"""<div class="status-card">
                <h4>Documento</h4>
                <div style="margin-top:.55rem;" class="{css_class}">{pdf_info}</div>
                <div style="margin-top:.5rem;color:#94a3b8;font-size:.88rem;line-height:1.5;">
                    Busca leve por palavras-chave para manter estabilidade e rapidez.
                </div>
            </div>""",
        unsafe_allow_html=True
    )

with c3:
    img_info = st.session_state.img_nome if st.session_state.img_nome else "Sem imagem ativa"
    css_class = "status-info" if st.session_state.img_nome else "status-warn"
    st.markdown(
        f"""<div class="status-card">
                <h4>Imagem</h4>
                <div style="margin-top:.55rem;" class="{css_class}">{img_info}</div>
                <div style="margin-top:.5rem;color:#94a3b8;font-size:.88rem;line-height:1.5;">
                    Pode ser integrada ao PDF e enriquecer a interpretação da resposta.
                </div>
            </div>""",
        unsafe_allow_html=True
    )


# =========================================================
# PRÉVIA DA IMAGEM ATIVA
# =========================================================
conv = get_conversation(st.session_state.current_conversation_id)
image_path = conv[6] if conv else None
image_name = conv[7] if conv else None

if image_path and os.path.exists(image_path):
    try:
        with st.expander("Pré-visualização da imagem ativa", expanded=False):
            img = Image.open(image_path)
            st.image(img, caption=f"Imagem ativa: {image_name}", use_container_width=True)
    except Exception as e:
        st.warning(f"Não consegui abrir a imagem ativa: {e}")


# =========================================================
# HISTÓRICO DO CHAT
# =========================================================
assistant_avatar = IF_LOGO if os.path.exists(IF_LOGO) else "🎓"
user_avatar = "👤"

for msg in st.session_state.chat:
    avatar = user_avatar if msg["role"] == "user" else assistant_avatar
    bubble_class = "user-bubble" if msg["role"] == "user" else "assistant-bubble"

    with st.chat_message(msg["role"], avatar=avatar):
        if msg["role"] == "assistant":
            render_markdown_final_seguro(st.container(), msg["content"], bubble_class)
        else:
            render_texto_stream_seguro(st, msg["content"], bubble_class)


# =========================================================
# CHAT INPUT
# =========================================================
placeholder_text = "Digite sua pergunta..."
if modo == "Análise de Conteúdo":
    placeholder_text = "Ex.: explique esta imagem, resuma este PDF, relacione a imagem com o material"
elif modo == "Matemática":
    placeholder_text = "Ex.: resolva a questão, use o PDF, interprete a imagem, faça o gráfico de x^2 - 4"
elif modo == "Chat Criativo":
    placeholder_text = "Ex.: me ajude a montar uma aula, desenvolver uma ideia ou estruturar um projeto"

entrada = st.chat_input(
    placeholder=placeholder_text,
    accept_file="multiple",
    file_type=ALLOWED_FILE_TYPES,
    key="main_chat_input",
)


# =========================================================
# PROCESSAMENTO
# =========================================================
if entrada:
    if not pode_perguntar():
        st.warning("Limite de perguntas atingido nesta sessão.")
        st.stop()

    registrar_pergunta()

    prompt = ""
    arquivos = []

    if isinstance(entrada, str):
        prompt = entrada.strip()
    else:
        prompt = getattr(entrada, "text", "") or ""
        arquivos = getattr(entrada, "files", []) or []
        if not arquivos and isinstance(entrada, dict):
            prompt = entrada.get("text", prompt)
            arquivos = entrada.get("files", arquivos)

    prompt = (prompt or "").strip()
    conversation_id = st.session_state.current_conversation_id

    novo_pdf_path = None
    novo_pdf_name = None
    nova_img_path = None
    nova_img_name = None

    for arq in arquivos:
        ext = os.path.splitext(arq.name.lower())[1]
        size_bytes = len(arq.getvalue())

        if ext == ".pdf":
            if size_bytes > MAX_PDF_MB * 1024 * 1024:
                st.error(f"O PDF '{arq.name}' excede o limite de {MAX_PDF_MB} MB.")
                st.stop()
            novo_pdf_path = salvar_uploaded_file(conversation_id, arq)
            novo_pdf_name = arq.name

        elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
            if size_bytes > MAX_IMG_MB * 1024 * 1024:
                st.error(f"A imagem '{arq.name}' excede o limite de {MAX_IMG_MB} MB.")
                st.stop()
            nova_img_path = salvar_uploaded_file(conversation_id, arq)
            nova_img_name = arq.name

    if novo_pdf_path:
        update_conversation_files(conversation_id, pdf_path=novo_pdf_path, pdf_name=novo_pdf_name)
        try:
            st.session_state.db = processar_pdf_from_path(novo_pdf_path)
            st.session_state.pdf_nome = novo_pdf_name
        except Exception as e:
            st.error(f"Erro ao processar PDF anexado: {e}")

    if nova_img_path:
        update_conversation_files(conversation_id, image_path=nova_img_path, image_name=nova_img_name)
        st.session_state.img_nome = nova_img_name

    if not prompt and arquivos:
        nomes = ", ".join([a.name for a in arquivos])
        prompt = f"Arquivos anexados: {nomes}"

    if prompt:
        maybe_update_title_from_first_message(conversation_id, prompt)
        save_message(conversation_id, "user", prompt)
        update_conversation_timestamp(conversation_id)

        st.session_state.chat.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar=user_avatar):
            render_texto_stream_seguro(st, prompt, "user-bubble")

        with st.chat_message("assistant", avatar=assistant_avatar):
            placeholder = st.empty()
            final_box = st.container()

            if client is None:
                resposta_final = "Não consegui responder porque a chave da API Groq não está configurada corretamente."
                placeholder.code(resposta_final)
                save_message(conversation_id, "assistant", resposta_final)
                st.session_state.chat.append({"role": "assistant", "content": resposta_final})

            else:
                try:
                    conv = get_conversation(conversation_id)
                    image_path = conv[6] if conv else None

                    k_contexto = 5 if modo in ["Análise de Conteúdo", "Matemática"] else 3
                    contexto, referencias = buscar_contexto(prompt, k=k_contexto)
                    st.session_state.last_sources = referencias

                    usar_visao = bool(image_path and os.path.exists(image_path))
                    prompt_lower = prompt.lower()

                    if modo == "Análise de Conteúdo":
                        if usar_visao:
                            resposta_final = analisar_imagem_com_vision(
                                prompt_usuario=prompt,
                                prompt_sistema=prompt_sistema_ativo,
                                modo_atual=modo,
                                image_path=image_path,
                                contexto=contexto,
                                referencias=referencias,
                            )
                            placeholder.empty()
                            render_markdown_final_seguro(final_box, resposta_final, "assistant-bubble")
                        else:
                            resposta_final = ""
                            for parcial in responder_texto(prompt, prompt_sistema_ativo, contexto, modo, referencias=referencias):
                                resposta_final = parcial
                                render_texto_stream_seguro(placeholder, resposta_final, "assistant-bubble")

                            placeholder.empty()
                            render_markdown_final_seguro(final_box, resposta_final, "assistant-bubble")

                    elif modo == "Matemática":
                        expr_grafico = extrair_expressao_grafico(prompt)

                        gatilho_visao = any(
                            termo in prompt_lower
                            for termo in ["imagem", "foto", "questão", "questao", "caderno", "print", "figura"]
                        )

                        if usar_visao and gatilho_visao:
                            resposta_final = analisar_imagem_com_vision(
                                prompt_usuario=prompt,
                                prompt_sistema=prompt_sistema_ativo,
                                modo_atual=modo,
                                image_path=image_path,
                                contexto=contexto,
                                referencias=referencias,
                            )
                        else:
                            resposta_final = ""
                            for parcial in responder_texto(prompt, prompt_sistema_ativo, contexto, modo, referencias=referencias):
                                resposta_final = parcial
                                render_texto_stream_seguro(placeholder, resposta_final, "assistant-bubble")

                        renderizar_visual_matematico(prompt)

                        if expr_grafico:
                            if expressao_valida(expr_grafico):
                                ok, erro = gerar_grafico_basico(expr_grafico)
                                if not ok:
                                    st.warning(f"Não consegui gerar o gráfico: {erro}")
                            else:
                                st.warning("Expressão inválida para geração de gráfico.")

                        if not resposta_final.strip():
                            resposta_final = "Não consegui gerar uma resposta no momento."

                        placeholder.empty()
                        renderizar_resposta_matematica(resposta_final)

                    else:
                        resposta_final = ""
                        for parcial in responder_texto(prompt, prompt_sistema_ativo, contexto, modo, referencias=referencias):
                            resposta_final = parcial
                            render_texto_stream_seguro(placeholder, resposta_final, "assistant-bubble")

                        placeholder.empty()
                        render_markdown_final_seguro(final_box, resposta_final, "assistant-bubble")

                    if not resposta_final.strip():
                        resposta_final = "Não consegui gerar uma resposta no momento."
                        placeholder.empty()
                        render_markdown_final_seguro(final_box, resposta_final, "assistant-bubble")

                    if referencias:
                        st.markdown(
                            "<div class='source-box'><b>Fontes de apoio usadas nesta resposta:</b> "
                            + " • ".join(referencias) +
                            "</div>",
                            unsafe_allow_html=True,
                        )

                    save_message(conversation_id, "assistant", resposta_final)
                    st.session_state.chat.append({"role": "assistant", "content": resposta_final})

                except Exception as e:
                    resposta_erro = f"Erro ao consultar a IA:\n{str(e)}"
                    try:
                        placeholder.code(resposta_erro)
                    except Exception:
                        st.code(resposta_erro)

                    save_message(conversation_id, "assistant", resposta_erro)
                    st.session_state.chat.append({"role": "assistant", "content": resposta_erro})


# =========================================================
# RODAPÉ
# =========================================================
st.markdown("---")
st.markdown(
    "<div class='footer-note'>Projeto Inércia Zero • Licenciatura em Física • Instituto Federal do Ceará</div>",
    unsafe_allow_html=True,
)
