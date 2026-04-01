import os
import re
import html
import uuid
import base64
import hashlib
import sqlite3
from datetime import datetime
from typing import Optional, Tuple, Dict, List

import streamlit as st
from groq import Groq
from pypdf import PdfReader
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import numpy as np


# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="MentorEdu | Projeto Inércia Zero",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "MentorEdu IA"
PROJECT_NAME = "Projeto Inércia Zero"
INSTITUTION_NAME = "Instituto Federal do Ceará"
COURSE_NAME = "Licenciatura em Física"

IF_LOGO = "logo.png"
DB_PATH = "mentoredu.db"
UPLOAD_DIR = "uploads"

TEXT_MODEL = "llama-3.3-70b-versatile"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

MAX_PDF_MB = 15
MAX_FILE_MB = 12
MAX_PERGUNTAS_SESSAO = 60
PDF_CONTEXT_LIMIT = 12000
CHAT_HISTORY_LIMIT = 8

os.makedirs(UPLOAD_DIR, exist_ok=True)


MENTORS = {
    "Física": {
        "emoji": "⚛️",
        "title": "Mentor de Física",
        "subtitle": "cinemática, dinâmica, energia, circuitos, gráficos e interpretação física",
        "description": "Explicações guiadas, analogias do cotidiano, interpretação física e resolução organizada.",
        "prompt": """
Você é um mentor especialista em Física escolar e início da graduação.
Priorize:
- interpretação física antes da conta
- unidades, sentido físico e leitura de gráficos
- analogias com situações do cotidiano
- explicações passo a passo quando o aluno precisar
- linguagem técnica quando falar com professor
- humor leve e contextual quando ajudar, sem exagero
Se o aluno acertou por um método muito longo, reconheça que está correto, mas mostre um caminho mais enxuto e explique por que ele funciona.
""".strip(),
    },
    "Matemática": {
        "emoji": "📐",
        "title": "Mentor de Matemática",
        "subtitle": "álgebra, funções, trigonometria, geometria e notação matemática",
        "description": "Passo a passo, bizus com fundamento, organização algébrica e leitura de padrões.",
        "prompt": """
Você é um mentor especialista em Matemática.
Priorize:
- clareza algébrica
- organização por etapas
- leitura de padrões
- atalhos apenas com explicação da origem
- linguagem amigável para aluno
- linguagem técnica para professor
Se houver um método mais curto, mostre sem desmerecer o método original do aluno.
""".strip(),
    },
    "Química": {
        "emoji": "🧪",
        "title": "Mentor de Química",
        "subtitle": "nomenclatura, estequiometria, tabela periódica, ligações e distribuições eletrônicas",
        "description": "Explicações químicas, nomenclatura, cálculos e consulta visual de Química.",
        "prompt": """
Você é um mentor especialista em Química.
Priorize:
- nomenclatura correta
- distribuição eletrônica e tabela periódica quando fizer sentido
- explicação de cálculos químicos de forma progressiva
- distinção entre linguagem técnica e linguagem didática
""".strip(),
    },
    "Linguagens": {
        "emoji": "📚",
        "title": "Mentor de Linguagens",
        "subtitle": "português, inglês, leitura, interpretação, gramática e produção textual",
        "description": "Apoio em escrita, correção, interpretação e explicação clara.",
        "prompt": """
Você é um mentor especialista em Linguagens, com foco em Português e Inglês.
Priorize:
- clareza
- interpretação textual
- correção com justificativa
- linguagem adequada ao perfil do usuário
""".strip(),
    },
}

PERIODIC_ROWS = [
    ["H", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "He"],
    ["Li", "Be", "", "", "", "", "", "", "", "", "", "", "B", "C", "N", "O", "F", "Ne"],
    ["Na", "Mg", "", "", "", "", "", "", "", "", "", "", "Al", "Si", "P", "S", "Cl", "Ar"],
    ["K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr"],
    ["Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe"],
    ["Cs", "Ba", "La*", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn"],
    ["Fr", "Ra", "Ac*", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"],
]
LANTHANIDES = ["La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"]
ACTINIDES = ["Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"]


# =========================================================
# CSS
# =========================================================
def app_css() -> str:
    return """
    <style>
    :root {
        --bg: #f7f1e8;
        --bg-soft: #f2e8db;
        --bg-sidebar: #eee1d1;
        --card: #fffaf3;
        --card-2: #f9f1e6;
        --line: #d9c5b0;
        --text: #392f26;
        --muted: #6f6257;
        --accent: #8a735f;
        --accent-2: #9a846f;
        --accent-soft: #efe1d0;
        --shadow: 0 10px 26px rgba(78, 60, 44, .08);
    }

    html, body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"], section.main {
        background: var(--bg) !important;
        color: var(--text) !important;
    }

    .main .block-container {
        max-width: 1250px !important;
        padding-top: .55rem !important;
        padding-bottom: .8rem !important;
    }

    header[data-testid="stHeader"] {
        background: var(--bg-soft) !important;
        border-bottom: 1px solid var(--line) !important;
    }

    [data-testid="stSidebar"] {
        background: var(--bg-sidebar) !important;
        border-right: 1px solid var(--line) !important;
    }

    [data-testid="stSidebar"] * {
        color: var(--text) !important;
    }

    .hero-card, .panel-card, .login-card, .mentor-card, .soft-card, .periodic-card, .top-mini-card, .conversation-card {
        background: var(--card) !important;
        border: 1px solid var(--line) !important;
        border-radius: 22px !important;
        box-shadow: var(--shadow) !important;
    }

    .hero-card, .panel-card, .periodic-card, .top-mini-card {
        padding: 16px 18px !important;
    }

    .conversation-card {
        padding: 8px 10px !important;
        margin-bottom: 8px !important;
        border-radius: 16px !important;
    }

    .login-card {
        padding: 22px !important;
        max-width: 1120px !important;
        margin: 0 auto 18px auto !important;
    }

    .mentor-card {
        padding: 16px !important;
        min-height: 180px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
    }

    .soft-card {
        padding: 14px 16px !important;
        border-radius: 18px !important;
    }

    .project-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 999px;
        border: 1px solid var(--line);
        background: var(--accent-soft);
        color: #5e4e40 !important;
        font-weight: 800;
        font-size: .9rem;
        margin-bottom: 10px;
    }

    .title-main {
        font-size: 1.9rem;
        line-height: 1.05;
        font-weight: 900;
        color: #564538 !important;
        margin-bottom: 4px;
    }

    .inst-big {
        font-size: 1.15rem;
        font-weight: 900;
        color: #524236 !important;
    }

    .inst-sub, .muted, .small-clean {
        color: var(--muted) !important;
    }

    .mentor-emoji {
        font-size: 1.7rem;
        margin-bottom: 8px;
    }

    .mentor-title {
        font-size: 1.04rem;
        font-weight: 900;
        color: #564538 !important;
    }

    .mentor-sub {
        color: var(--muted) !important;
        font-size: .92rem;
        margin-top: 4px;
        margin-bottom: 8px;
    }

    .brand-box img, .logo-center img {
        display: block;
        margin: 0 auto 10px auto;
        max-width: 180px;
        width: 100%;
    }

    .brand-title {
        font-size: 1rem;
        font-weight: 900;
        line-height: 1.05;
        color: #564538 !important;
        text-align: center;
    }

    .brand-sub {
        text-align: center;
        color: var(--muted) !important;
        font-size: .9rem;
    }

    .account-box {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 12px;
        margin-bottom: 8px;
    }

    .account-name {
        font-weight: 900;
        color: #4f4034 !important;
    }

    .account-sub {
        color: var(--muted) !important;
        font-size: .88rem;
    }

    .stButton > button,
    div[data-testid="baseButton-secondary"] > button,
    div[data-testid="baseButton-primary"] > button,
    div[data-testid="stBaseButton-secondary"] > button {
        background: var(--accent) !important;
        color: #fffaf4 !important;
        border: 1px solid var(--accent) !important;
        border-radius: 14px !important;
        min-height: 40px !important;
        box-shadow: none !important;
    }

    .stButton > button:hover,
    div[data-testid="baseButton-secondary"] > button:hover,
    div[data-testid="baseButton-primary"] > button:hover,
    div[data-testid="stBaseButton-secondary"] > button:hover {
        background: var(--accent-2) !important;
        border-color: var(--accent-2) !important;
    }

    .stSelectbox div[data-baseweb="select"] > div,
    .stTextInput input,
    .stTextArea textarea,
    .stFileUploader section,
    [data-baseweb="input"] > div,
    [data-baseweb="base-input"] > div,
    .stRadio > div,
    .stSegmentedControl {
        background: var(--card-2) !important;
        color: var(--text) !important;
        border-color: var(--line) !important;
    }

    [data-testid="stChatInputContainer"],
    [data-testid="stBottomBlockContainer"],
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] textarea {
        background: var(--bg) !important;
        color: var(--text) !important;
        border-color: var(--line) !important;
        box-shadow: none !important;
    }

    [data-testid="stChatInput"] textarea {
        background: var(--card-2) !important;
        border: 1px solid var(--line) !important;
        border-radius: 16px !important;
    }

    [data-testid="stChatMessageContent"] {
        color: var(--text) !important;
        background: var(--card) !important;
        border: 1px solid var(--line) !important;
        border-radius: 16px !important;
        padding: .72rem .86rem !important;
    }

    .attach-note {
        margin-top: 8px;
        padding: 10px 12px;
        border: 1px dashed var(--line);
        border-radius: 14px;
        background: #fbf5ed;
        color: var(--muted) !important;
    }

    .mode-chip {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        background: #f0e4d5;
        border: 1px solid var(--line);
        font-size: .85rem;
        font-weight: 800;
        color: #5e4d40 !important;
    }

    .periodic-wrap { overflow-x: auto; }
    table.periodic {
        width: 100%;
        border-collapse: separate;
        border-spacing: 4px;
    }

    table.periodic td {
        min-width: 40px;
        height: 42px;
        text-align: center;
        font-weight: 800;
        border-radius: 10px;
        border: 1px solid var(--line);
        background: #f8efe4;
        color: #5a483b;
        font-size: .88rem;
    }

    table.periodic td.empty {
        background: transparent !important;
        border: none !important;
    }

    .series-row {
        display: grid;
        grid-template-columns: repeat(15, 1fr);
        gap: 4px;
        margin-top: 6px;
    }

    .series-cell {
        text-align: center;
        padding: 8px 3px;
        border-radius: 10px;
        border: 1px solid var(--line);
        background: #f8efe4;
        font-weight: 800;
        color: #5a483b;
    }

    .mini-title {
        font-weight: 900;
        color: #544236 !important;
        margin-bottom: 4px;
    }

    .mini-desc {
        color: var(--muted) !important;
        font-size: .9rem;
    }

    .conversation-title {
        font-weight: 800;
        font-size: .92rem;
        line-height: 1.15;
        margin-bottom: 2px;
        color: #4d3d31 !important;
    }

    .conversation-meta {
        color: var(--muted) !important;
        font-size: .78rem;
        line-height: 1.1;
    }

    .stMarkdown p, .stCaption, label, span, div {
        color: var(--text) !important;
    }
    </style>
    """


st.markdown(app_css(), unsafe_allow_html=True)


# =========================================================
# DB
# =========================================================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_key TEXT,
            title TEXT NOT NULL DEFAULT 'Nova conversa',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            profile TEXT,
            nickname TEXT,
            mentor TEXT,
            last_mode TEXT,
            attachment_path TEXT,
            attachment_name TEXT,
            attachment_type TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(conversation_id) REFERENCES conversations(id)
        )
        """
    )

    cur.execute("PRAGMA table_info(conversations)")
    cols = [r[1] for r in cur.fetchall()]
    migrations = [
        ("user_key", "ALTER TABLE conversations ADD COLUMN user_key TEXT"),
        ("profile", "ALTER TABLE conversations ADD COLUMN profile TEXT"),
        ("nickname", "ALTER TABLE conversations ADD COLUMN nickname TEXT"),
        ("mentor", "ALTER TABLE conversations ADD COLUMN mentor TEXT"),
        ("last_mode", "ALTER TABLE conversations ADD COLUMN last_mode TEXT"),
        ("attachment_path", "ALTER TABLE conversations ADD COLUMN attachment_path TEXT"),
        ("attachment_name", "ALTER TABLE conversations ADD COLUMN attachment_name TEXT"),
        ("attachment_type", "ALTER TABLE conversations ADD COLUMN attachment_type TEXT"),
    ]
    for col, ddl in migrations:
        if col not in cols:
            cur.execute(ddl)

    conn.commit()
    conn.close()


# =========================================================
# SESSION
# =========================================================
def init_session_state():
    defaults = {
        "auth_complete": False,
        "profile": "Aluno",
        "nickname": "",
        "mentor": "Física",
        "last_detected_mode": "Livre",
        "chat": [],
        "current_conversation_id": None,
        "loaded_conversation_id": None,
        "attachment_text": None,
        "attachment_name": None,
        "attachment_type": None,
        "attachment_preview_path": None,
        "last_generated_image": None,
        "contador_perguntas": 0,
        "rename_target_id": None,
        "gabarito_rapido": "",
        "criterios_correcao": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_db()
init_session_state()


# =========================================================
# HELPERS
# =========================================================
def get_first_name(name: str) -> str:
    name = (name or "").strip()
    return name.split()[0] if name else "Usuário"


def get_logged_email() -> str:
    try:
        if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
            return str(getattr(st.user, "email", "") or "").strip().lower()
    except Exception:
        pass
    return ""


def build_user_key() -> str:
    email = get_logged_email()
    base = email or f"{st.session_state.profile}|{st.session_state.nickname.strip().lower()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def load_client() -> Tuple[Optional[Groq], Optional[str]]:
    try:
        key = str(st.secrets.get("GROQ_API_KEY", "")).strip()
    except Exception:
        key = ""
    if not key:
        return None, "A chave GROQ_API_KEY não foi encontrada nos Secrets."
    try:
        return Groq(api_key=key), None
    except Exception as e:
        return None, f"Erro ao iniciar Groq: {e}"


client, client_error = load_client()


def avatar_if() -> str:
    return IF_LOGO if os.path.exists(IF_LOGO) else "🎓"


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def clean_text(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", (text or "").strip())


def list_conversations() -> List[tuple]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, title, updated_at, mentor, attachment_name, last_mode
        FROM conversations
        WHERE user_key = ?
        ORDER BY updated_at DESC, id DESC
        """,
        (build_user_key(),),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_conversation(cid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, title, created_at, updated_at, profile, nickname, mentor, last_mode,
               attachment_path, attachment_name, attachment_type, user_key
        FROM conversations
        WHERE id = ? AND user_key = ?
        """,
        (cid, build_user_key()),
    )
    row = cur.fetchone()
    conn.close()
    return row


def create_conversation(title: str = "Nova conversa", mentor: Optional[str] = None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    mentor = mentor or st.session_state.mentor
    now = now_iso()
    cur.execute(
        """
        INSERT INTO conversations(
            user_key, title, created_at, updated_at, profile, nickname, mentor, last_mode
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            build_user_key(),
            title,
            now,
            now,
            st.session_state.profile,
            st.session_state.nickname,
            mentor,
            st.session_state.last_detected_mode,
        ),
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid


def save_message(cid: int, role: str, content: str):
    conn = get_conn()
    cur = conn.cursor()
    now = now_iso()
    cur.execute(
        "INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (cid, role, content, now),
    )
    cur.execute(
        "UPDATE conversations SET updated_at = ?, mentor = ?, last_mode = ? WHERE id = ? AND user_key = ?",
        (now, st.session_state.mentor, st.session_state.last_detected_mode, cid, build_user_key()),
    )
    conn.commit()
    conn.close()


def save_chat_item(cid: int, item: dict):
    role = item.get("role", "assistant")
    item_type = item.get("type", "text")
    if item_type == "image":
        path = item.get("content", "")
        caption = item.get("caption", "Imagem")
        payload = f"__IMAGE__|{path}|{caption}"
    else:
        payload = item.get("content", "")
    save_message(cid, role, payload)


def get_messages(cid: int) -> List[tuple]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY id ASC",
        (cid,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def rename_first_message_title(cid: int, text: str):
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT title FROM conversations WHERE id = ? AND user_key = ?",
        (cid, build_user_key()),
    )
    row = cur.fetchone()
    if row and row[0] == "Nova conversa":
        cur.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ? AND user_key = ?",
            (text[:72], now_iso(), cid, build_user_key()),
        )
        conn.commit()
    conn.close()


def rename_conversation(cid: int, new_title: str):
    new_title = re.sub(r"\s+", " ", (new_title or "").strip())
    if not new_title:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ? AND user_key = ?",
        (new_title[:80], now_iso(), cid, build_user_key()),
    )
    conn.commit()
    conn.close()


def delete_conversation(cid: int):
    conv = get_conversation(cid)
    if conv:
        attachment_path = conv[8]
        if attachment_path and os.path.exists(attachment_path):
            try:
                os.remove(attachment_path)
            except Exception:
                pass

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE conversation_id = ?", (cid,))
    cur.execute("DELETE FROM conversations WHERE id = ? AND user_key = ?", (cid, build_user_key()))
    conn.commit()
    conn.close()


def update_attachment(cid: int, path: Optional[str], name: Optional[str], ftype: Optional[str]):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE conversations
        SET attachment_path = ?, attachment_name = ?, attachment_type = ?, updated_at = ?
        WHERE id = ? AND user_key = ?
        """,
        (path, name, ftype, now_iso(), cid, build_user_key()),
    )
    conn.commit()
    conn.close()


def update_conversation_mentor(cid: int, mentor: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE conversations
        SET mentor = ?, updated_at = ?
        WHERE id = ? AND user_key = ?
        """,
        (mentor, now_iso(), cid, build_user_key()),
    )
    conn.commit()
    conn.close()


def reset_visual_state(clear_file: bool = True):
    st.session_state.chat = []
    st.session_state.loaded_conversation_id = None
    st.session_state.last_generated_image = None
    st.session_state.contador_perguntas = 0
    st.session_state.last_detected_mode = "Livre"
    if clear_file:
        st.session_state.attachment_text = None
        st.session_state.attachment_name = None
        st.session_state.attachment_type = None
        st.session_state.attachment_preview_path = None


def load_conversation_into_state(cid: int):
    conv = get_conversation(cid)
    if not conv:
        return

    (
        _id,
        _title,
        _created_at,
        _updated_at,
        profile,
        nickname,
        mentor,
        last_mode,
        attachment_path,
        attachment_name,
        attachment_type,
        _user_key,
    ) = conv

    st.session_state.profile = profile or st.session_state.profile
    st.session_state.nickname = nickname or st.session_state.nickname
    st.session_state.mentor = mentor or st.session_state.mentor
    st.session_state.last_detected_mode = last_mode or "Livre"
    loaded_chat = []
    for r, c, _ in get_messages(cid):
        if isinstance(c, str) and c.startswith("__IMAGE__|"):
            parts = c.split("|", 2)
            img_path = parts[1] if len(parts) > 1 else ""
            caption = parts[2] if len(parts) > 2 else "Imagem"
            loaded_chat.append({"role": r, "type": "image", "content": img_path, "caption": caption})
        else:
            loaded_chat.append({"role": r, "type": "text", "content": c})
    st.session_state.chat = loaded_chat
    st.session_state.current_conversation_id = cid
    st.session_state.loaded_conversation_id = cid
    st.session_state.last_generated_image = None
    st.session_state.attachment_name = attachment_name
    st.session_state.attachment_type = attachment_type
    st.session_state.attachment_preview_path = attachment_path if attachment_type == "image" else None

    if attachment_path and os.path.exists(attachment_path):
        if attachment_type == "pdf":
            st.session_state.attachment_text = extract_pdf_text(attachment_path)
        elif attachment_type == "text":
            try:
                with open(attachment_path, "r", encoding="utf-8") as f:
                    st.session_state.attachment_text = f.read()
            except Exception:
                st.session_state.attachment_text = None
        else:
            st.session_state.attachment_text = None
    else:
        st.session_state.attachment_text = None


# =========================================================
# FILES
# =========================================================
def file_mb(uploaded_file) -> float:
    return round(len(uploaded_file.getbuffer()) / (1024 * 1024), 2)


def validate_upload(uploaded_file) -> Optional[str]:
    name = uploaded_file.name.lower()
    mb = file_mb(uploaded_file)

    if name.endswith(".pdf"):
        if mb > MAX_PDF_MB:
            return f"O PDF excede o limite de {MAX_PDF_MB} MB."
        return None

    allowed = (".png", ".jpg", ".jpeg", ".webp", ".txt")
    if not name.endswith(allowed):
        return "Envie PDF, imagem (PNG/JPG/WEBP) ou TXT."

    if mb > MAX_FILE_MB:
        return f"O arquivo excede o limite de {MAX_FILE_MB} MB."
    return None


def save_upload(uploaded_file) -> Tuple[str, str, str]:
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    dest = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if ext == ".pdf":
        ftype = "pdf"
    elif ext == ".txt":
        ftype = "text"
    else:
        ftype = "image"

    return dest, uploaded_file.name, ftype


def extract_pdf_text(path: str) -> Optional[str]:
    try:
        reader = PdfReader(path)
        chunks = []
        for page in reader.pages:
            txt = (page.extract_text() or "").strip()
            if txt:
                txt = re.sub(r"\s+", " ", txt)
                chunks.append(txt)
        result = "\n\n".join(chunks).strip()
        return result or None
    except Exception:
        return None


def image_to_data_url(path: str) -> Optional[str]:
    if not path or not os.path.exists(path):
        return None

    ext = os.path.splitext(path)[1].lower()
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "image/jpeg")

    try:
        with open(path, "rb") as f:
            raw = f.read()
        b64 = base64.b64encode(raw).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None


# =========================================================
# RENDERERS
# =========================================================
def render_periodic_table():
    rows_html = []
    for row in PERIODIC_ROWS:
        tds = []
        for el in row:
            if el:
                tds.append(f"<td>{html.escape(el)}</td>")
            else:
                tds.append('<td class="empty"></td>')
        rows_html.append("<tr>" + "".join(tds) + "</tr>")

    lan = "".join(f'<div class="series-cell">{x}</div>' for x in LANTHANIDES)
    act = "".join(f'<div class="series-cell">{x}</div>' for x in ACTINIDES)

    st.markdown(
        f"""
        <div class="periodic-card">
            <div class="mini-title">Tabela periódica rápida</div>
            <div class="mini-desc" style="margin-bottom:8px;">Consulta visual para o mentor de Química.</div>
            <div class="periodic-wrap">
                <table class="periodic">{''.join(rows_html)}</table>
                <div class="small-clean" style="margin-top:8px;">Lantanídeos</div>
                <div class="series-row">{lan}</div>
                <div class="small-clean" style="margin-top:8px;">Actinídeos</div>
                <div class="series-row">{act}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_linus_pauling_diagram() -> str:
    path = os.path.join(UPLOAD_DIR, f"linus_{uuid.uuid4().hex}.png")

    fig, ax = plt.subplots(figsize=(10, 7), dpi=180)
    fig.patch.set_facecolor("#f7f1e8")
    ax.set_facecolor("#fffaf3")
    ax.axis("off")

    levels = [
        ["1s"],
        ["2s", "2p"],
        ["3s", "3p", "3d"],
        ["4s", "4p", "4d", "4f"],
        ["5s", "5p", "5d", "5f"],
        ["6s", "6p", "6d"],
        ["7s", "7p"],
    ]

    xs = [1, 3, 5, 7]
    ys = list(range(len(levels), 0, -1))

    for row_idx, subs in enumerate(levels):
        y = ys[row_idx]
        for col_idx, sub in enumerate(subs):
            x = xs[min(col_idx, len(xs) - 1)]
            ax.text(
                x, y, sub,
                ha="center",
                va="center",
                fontsize=16,
                fontweight="bold",
                color="#5a483b",
                bbox=dict(boxstyle="round,pad=0.35", facecolor="#f3e8da", edgecolor="#d8c6b4")
            )

    arrows = [
        ((7.7, 7.3), (0.8, 6.2)),
        ((7.7, 6.3), (0.8, 5.2)),
        ((7.7, 5.3), (0.8, 4.2)),
        ((7.7, 4.3), (0.8, 3.2)),
        ((7.7, 3.3), (0.8, 2.2)),
        ((5.7, 2.3), (0.8, 1.2)),
    ]

    for start, end in arrows:
        arrow = FancyArrowPatch(start, end, arrowstyle="->", mutation_scale=18, linewidth=2.2, color="#8c7764")
        ax.add_patch(arrow)

    ax.text(4.1, 8.0, "Diagrama de Linus Pauling", ha="center", fontsize=19, fontweight="bold", color="#5a483b")
    ax.text(4.1, 0.35, "Ordem de preenchimento: 1s → 2s → 2p → 3s → 3p → 4s ...", ha="center", fontsize=12, color="#75695e")
    ax.set_xlim(0, 8.5)
    ax.set_ylim(0, 8.5)

    plt.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


# =========================================================
# INTENTS / PROMPTS
# =========================================================
def detect_intent(text: str) -> str:
    t = (text or "").lower()

    if any(k in t for k in [
        "demonstração", "demonstracao", "demonstre",
        "dedução", "deducao", "deduza",
        "derivação", "derivacao", "derive",
        "prova", "prove", "provar",
        "origem da fórmula", "origem da formula",
        "mostre de onde vem", "explique a fórmula", "explique a formula"
    ]):
        return "demonstracao"

    if "linus pauling" in t or "diagrama de linus" in t:
        return "linus"

    if "tabela periódica" in t or "tabela periodica" in t:
        return "tabela_periodica"

    if any(k in t for k in [
        "corrigir prova", "corrija a prova", "corrigir questão", "corrigir questao",
        "gabarito", "rubrica", "corrija essa", "corrige essa", "corrija isto",
        "avalie esta resposta", "corrija a resposta"
    ]):
        return "correcao"

    if any(k in t for k in [
        "analise minha resolução", "analise minha resolucao", "onde compliquei",
        "onde eu errei", "meu método", "meu metodo", "veja minha resolução",
        "veja minha resolucao"
    ]):
        return "analise_resolucao"

    if any(k in t for k in ["resuma", "resumir", "resumo", "resuma esse slide", "resuma esse pdf"]):
        return "resumo"

    if any(k in t for k in ["plano de aula", "sequência didática", "sequencia didatica", "monte uma aula"]):
        return "plano_aula"

    if any(k in t for k in [
        "gere questões", "gere questoes", "crie questões", "crie questoes",
        "lista de exercícios", "lista de exercicios", "simulado", "monte questões", "monte questoes"
    ]):
        return "lista_exercicios"

    if any(k in t for k in ["gráfico", "grafico", "diagrama", "esquema visual", "imagem", "slide"]):
        return "visual"

    if any(k in t for k in ["questão", "questao", "resolver", "resolva"]):
        return "resolver"

    return "explicacao"


def detect_mode_label(intent: str) -> str:
    mapping = {
        "demonstracao": "Demonstração",
        "correcao": "Correção",
        "analise_resolucao": "Análise de resolução",
        "resumo": "Resumo",
        "plano_aula": "Plano de aula",
        "lista_exercicios": "Geração de questões",
        "resolver": "Resolução",
        "explicacao": "Explicação",
        "visual": "Interpretação visual",
        "linus": "Diagrama",
        "tabela_periodica": "Consulta",
    }
    return mapping.get(intent, "Livre")


def chat_history_text(chat: List[Dict[str, str]], limit: int = CHAT_HISTORY_LIMIT) -> str:
    parts = []
    for msg in chat[-limit:]:
        who = "Usuário" if msg["role"] == "user" else "Assistente"
        parts.append(f"{who}: {msg['content'][:900]}")
    return "\n".join(parts)


def build_profile_prompt(profile: str) -> str:
    if profile == "Professor":
        return """
Você está falando com um PROFESSOR.
Adote tom técnico, organizado e profissional.
Priorize:
- precisão conceitual
- metodologia
- critérios de correção
- análise pedagógica
- objetividade
- sugestões de feedback para alunos
Ao corrigir, diferencie:
- erro conceitual
- erro algébrico/aritmético
- erro de unidade/notação
- método válido porém pouco eficiente
Não infantilize a resposta.
""".strip()

    return """
Você está falando com um ALUNO.
Adote tom amigável, acolhedor e didático.
Priorize:
- entendimento real
- passo a passo quando necessário
- analogias com cotidiano
- mostrar erros comuns
- mostrar caminho mais simples quando existir
- "bizu" apenas junto com a explicação da origem
Pode usar humor leve e natural quando ajudar a fixar a ideia, sem forçar.
Nunca humilhe o aluno; corrija com firmeza e acolhimento.
""".strip()


def build_task_prompt(intent: str) -> str:
    prompts = {
        "demonstracao": """
Explique a origem da fórmula, identidade ou resultado pedido.
Priorize dedução passo a passo.
Mostre de onde cada etapa vem.
Não gere gráfico automaticamente, a menos que o usuário peça explicitamente junto.
""",
        "explicacao": """
Explique como um mentor muito bom:
- comece pela ideia central
- depois desenvolva
- use exemplos concretos
- se houver fórmula, explique o significado antes de usar
""",
        "resolver": """
Resolva com foco em clareza:
- identifique dados
- diga o que a questão pede
- monte o raciocínio
- resolva
- destaque o resultado
- se houver caminho mais rápido, mostre no final
""",
        "analise_resolucao": """
Analise a resolução do aluno:
- diga se o raciocínio está certo, parcialmente certo ou errado
- avalie a eficiência do método
- mostre onde complicou sem necessidade, se for o caso
- proponha um caminho mais simples
- explique por que o caminho mais simples funciona
""",
        "correcao": """
Atue como assistente de correção.
Não aja como avaliador arbitrário.
Faça:
- identificar resposta esperada, se houver
- comparar com a resposta do aluno
- apontar acertos e erros
- sugerir pontuação quando fizer sentido
- diferenciar método correto porém longo de erro real
- gerar feedback curto útil para professor e, se couber, para aluno
""",
        "resumo": """
Resuma de forma útil para estudo:
- tópicos principais
- conceitos-chave
- fórmulas importantes
- pontos de atenção
- mini revisão final
""",
        "plano_aula": """
Monte uma resposta voltada a planejamento didático:
- objetivo
- conteúdo
- abordagem
- atividade
- avaliação
- observações
""",
        "lista_exercicios": """
Gere exercícios organizados por nível:
- fácil
- médio
- desafiador
Quando útil, inclua gabarito ou sugestões de resolução.
""",
        "visual": """
Analise a imagem com inteligência:
- extraia o máximo possível
- identifique tema, dados e pedido
- só diga que falta informação se realmente faltar um dado essencial
""",
        "linus": "Gere ou explique o diagrama de Linus Pauling quando solicitado.",
        "tabela_periodica": "Use a tabela periódica como apoio visual quando solicitado.",
    }
    return prompts.get(intent, prompts["explicacao"]).strip()


def build_teacher_correction_context() -> str:
    parts = []
    if st.session_state.profile == "Professor":
        if st.session_state.gabarito_rapido.strip():
            parts.append("Gabarito/Resposta esperada fornecida pelo professor:\n" + st.session_state.gabarito_rapido.strip())
        if st.session_state.criterios_correcao.strip():
            parts.append("Critérios de correção/Pontuação fornecidos pelo professor:\n" + st.session_state.criterios_correcao.strip())
    return "\n\n".join(parts).strip()


def system_prompt(profile: str, mentor: str, intent: str) -> str:
    mentor_prompt = MENTORS[mentor]["prompt"]
    profile_prompt = build_profile_prompt(profile)
    task_prompt = build_task_prompt(intent)

    base = f"""
Você é o {APP_NAME}, um mentor acadêmico institucional ligado ao {PROJECT_NAME} do {INSTITUTION_NAME}.
Atenda em português do Brasil.
Perfil atual do usuário: {profile}.
Área atual do mentor: {mentor}.
Intenção atual detectada: {intent}.

Regras gerais:
- Seja claro, didático e confiável.
- Quando houver matemática, use LaTeX válido com $...$ e $$...$$.
- Se o material vier incompleto, tente inferir com cautela antes de dizer que faltam informações.
- Se faltar dado essencial, diga exatamente o que faltou.
- Quando o usuário for aluno, foque em entendimento.
- Quando o usuário for professor, foque em análise técnica e utilidade pedagógica.
- Se o aluno acertou por método muito longo, reconheça isso e depois mostre um método mais eficiente.
- Não invente leitura de detalhes visuais que não estejam suficientemente visíveis.
- Se estiver corrigindo prova, trate sua saída como sugestão de correção assistida, não sentença absoluta.
- Ao sugerir nota, deixe claro o critério usado.
- Evite respostas genéricas.
- Nunca use comandos como \\includegraphics nem finja que exibiu uma imagem; quando o pedido for visual, prefira explicar a imagem realmente gerada pelo app.
- Se o usuário pedir demonstração, dedução, derivação ou origem de uma fórmula, priorize a explicação simbólica e não gere gráfico automaticamente.
- Nunca use comandos como \includegraphics, não finja que exibiu uma imagem; quando o pedido for visual, prefira explicar a imagem realmente gerada pelo app.

Prompt do mentor:
{mentor_prompt}

Prompt do perfil:
{profile_prompt}

Prompt da tarefa:
{task_prompt}
"""
    return clean_text(base)


def build_user_prompt(text: str) -> str:
    intent = detect_intent(text)
    history = chat_history_text(st.session_state.chat)

    parts = [
        f"Usuário: {get_first_name(st.session_state.nickname)}",
        f"Perfil: {st.session_state.profile}",
        f"Mentor escolhido: {st.session_state.mentor}",
        f"Intenção detectada: {intent}",
    ]

    if history:
        parts.append("Histórico recente:\n" + history)

    correction_context = build_teacher_correction_context()
    if correction_context:
        parts.append(correction_context)

    if st.session_state.attachment_text:
        parts.append("Contexto do anexo textual/PDF:\n" + st.session_state.attachment_text[:PDF_CONTEXT_LIMIT])

    if st.session_state.attachment_name and st.session_state.attachment_type == "image":
        parts.append(
            "Há uma imagem anexada nesta conversa. "
            "Se a imagem estiver disponível no fluxo visual, ela deve ser analisada junto com o pedido."
        )

    parts.append("Pedido atual:\n" + text.strip())
    return "\n\n".join(parts)


# =========================================================
# MODELS
# =========================================================
def ask_text_model(user_text: str) -> str:
    if client is None:
        return client_error or "Não foi possível iniciar a IA."

    intent = detect_intent(user_text)

    try:
        resp = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt(
                        profile=st.session_state.profile,
                        mentor=st.session_state.mentor,
                        intent=intent,
                    ),
                },
                {
                    "role": "user",
                    "content": build_user_prompt(user_text),
                },
            ],
            temperature=0.3,
            max_tokens=1700,
        )
        text = (resp.choices[0].message.content or "").strip()
        return clean_text(text) if text else "Não consegui gerar uma resposta útil."
    except Exception as e:
        return f"Ocorreu um erro ao gerar a resposta: {e}"


def ask_vision_model(user_text: str, image_path: str) -> str:
    if client is None:
        return client_error or "Não foi possível iniciar a IA."

    image_data_url = image_to_data_url(image_path)
    if not image_data_url:
        return "Não consegui preparar a imagem para análise."

    intent = detect_intent(user_text)
    vision_instruction = f"""
Você está recebendo uma imagem relacionada ao pedido do usuário.
Analise a imagem com cuidado.
Se for uma questão, slide, prova, quadro, gráfico ou resolução:
- extraia o máximo de informação útil
- identifique o tema
- só diga que falta informação se realmente faltar um dado essencial
- se o enunciado estiver parcialmente legível, ainda assim tente interpretar com cautela
- não invente texto que não está visível
Pedido do usuário: {user_text}
"""

    try:
        resp = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt(
                        profile=st.session_state.profile,
                        mentor=st.session_state.mentor,
                        intent=intent,
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": build_user_prompt(user_text)},
                        {"type": "text", "text": vision_instruction},
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ],
                },
            ],
            temperature=0.2,
            max_tokens=1900,
        )
        text = (resp.choices[0].message.content or "").strip()
        return clean_text(text) if text else "Não consegui gerar uma análise útil da imagem."
    except Exception as e:
        return f"Ocorreu um erro ao analisar a imagem: {e}"




def save_plot_figure(fig, prefix: str) -> str:
    path = os.path.join(UPLOAD_DIR, f"{prefix}_{uuid.uuid4().hex}.png")
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor(), dpi=180)
    plt.close(fig)
    return path




def request_wants_derivation(text: str) -> bool:
    t = (text or "").lower()
    terms = [
        "demonstração", "demonstracao", "demonstre",
        "dedução", "deducao", "deduza",
        "derivação", "derivacao", "derive",
        "prova", "prove", "provar",
        "origem da fórmula", "origem da formula",
        "mostre de onde vem", "explique a fórmula", "explique a formula"
    ]
    return any(term in t for term in terms)

def inherit_visual_context_from_history(user_text: str) -> str:
    t = (user_text or "").lower()

    direct_terms = [
        "gráfico", "grafico", "plote", "plot", "curva", "plano cartesiano",
        "função", "funcao", "equação", "equacao", "afim", "linear",
        "primeiro grau", "segundo grau", "terceiro grau", "quadrática", "quadratica",
        "parábola", "parabola", "exponencial", "logarítmica", "logaritmica",
        "modular", "módulo", "modulo", "seno", "cosseno", "coseno", "tangente",
        "mru", "mruv", "trajetória", "trajetoria", "forças", "forcas"
    ]
    if any(term in t for term in direct_terms):
        return t

    continuation_terms = [
        "agora", "outro", "outra", "mais um", "mais uma", "exemplo", "exemplo de",
        "faça uma", "faca uma", "gere uma", "gera uma", "mostre uma", "quero uma"
    ]
    if not any(term in t for term in continuation_terms):
        return t

    recent_texts = []
    for msg in reversed(st.session_state.chat[-6:]):
        if msg.get("type") == "text":
            recent_texts.append((msg.get("content") or "").lower())

    history = " ".join(recent_texts)
    if history:
        return history + " " + t
    return t

def request_wants_visual_generation(text: str) -> bool:
    t = inherit_visual_context_from_history(text)
    visual_terms = [
        "gráfico", "grafico", "plote", "plot", "curva", "trajetória", "trajetoria",
        "plano cartesiano", "diagrama", "desenhe", "desenha", "esquema", "vetor",
        "vetores", "força", "forcas", "forças", "função", "funcao", "equação",
        "equacao", "primeiro grau", "segundo grau", "terceiro grau", "quadrática", "quadratica", "parábola", "parabola",
        "linear", "afim", "cúbica", "cubica", "exponencial", "logarítmica", "logaritmica", "modular", "módulo", "modulo",
        "trigonometria", "razões trigonométricas", "razoes trigonometricas",
        "razão trigonométrica", "razao trigonometrica", "seno", "cosseno", "coseno", "tangente"
    ]
    return any(term in t for term in visual_terms)


def generate_trig_plot() -> str:
    x = np.linspace(0, 360, 1200)
    rad = np.deg2rad(x)
    y_sin = np.sin(rad)
    y_cos = np.cos(rad)
    y_tan = np.tan(rad)
    y_tan = np.where(np.abs(y_tan) > 5, np.nan, y_tan)

    fig, ax = plt.subplots(figsize=(10, 5), dpi=180)
    fig.patch.set_facecolor("#f7f1e8")
    ax.set_facecolor("#fffaf3")
    ax.plot(x, y_sin, label="sen(θ)", linewidth=2.4)
    ax.plot(x, y_cos, label="cos(θ)", linewidth=2.4)
    ax.plot(x, y_tan, label="tan(θ)", linewidth=2.1)
    for xv in [90, 270]:
        ax.axvline(x=xv, linestyle="--", linewidth=1)
    ax.axhline(0, linewidth=1)
    ax.set_xlim(0, 360)
    ax.set_ylim(-5, 5)
    ax.set_xticks([0, 30, 45, 60, 90, 120, 180, 270, 360])
    ax.set_xlabel("Ângulo θ (graus)")
    ax.set_ylabel("Valor da razão")
    ax.set_title("Gráfico de seno, cosseno e tangente")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    return save_plot_figure(fig, "trig")


def safe_math_expression_from_text(text: str) -> str:
    lower = (text or "").lower().strip()

    patterns = [
        r"y\s*=\s*([^\n\r]+)",
        r"fun[cç][aã]o\s+([^\n\r]+)",
        r"equa[cç][aã]o\s+([^\n\r]+)",
    ]
    expr = ""
    for pat in patterns:
        m = re.search(pat, lower)
        if m:
            expr = m.group(1).strip()
            break

    if not expr:
        expr = lower

    expr = expr.replace("^", "**")
    expr = expr.replace("sen", "sin")
    expr = expr.replace("tg", "tan")
    expr = expr.replace("ln(", "log(")
    expr = expr.replace("|x|", "abs(x)")

    fillers = [
        "gere um gráfico de", "gere um grafico de", "faça um gráfico de", "faca um grafico de",
        "plote", "mostre", "desenhe", "gráfico de", "grafico de",
        "função", "funcao", "equação", "equacao", "da", "do"
    ]
    for f in fillers:
        expr = expr.replace(f, " ")

    expr = expr.strip()
    expr = re.sub(r"(\d)(x)", r"\1*\2", expr)
    expr = re.sub(r"(x)(\d)", r"\1*\2", expr)
    expr = re.sub(r"(\))(x)", r"\1*\2", expr)
    expr = re.sub(r"(x)(\()", r"\1*\2", expr)
    expr = re.sub(r"[^0-9x\+\-\*\/\.^\(\)\s_a-z]", "", expr)

    allowed = {
        "sin": "np.sin",
        "cos": "np.cos",
        "tan": "np.tan",
        "sqrt": "np.sqrt",
        "log": "np.log",
        "exp": "np.exp",
        "pi": "np.pi",
        "abs": "np.abs",
    }
    for k, v in allowed.items():
        expr = re.sub(rf"\b{k}\b", v, expr)
    expr = re.sub(r"\bx\b", "x", expr)
    return expr.strip()




def infer_math_constraints_from_prompt(text: str) -> dict:
    t = (text or "").lower()
    info = {
        "kind": None,
        "a_sign": None,
        "delta_sign": None,
        "concavity": None,
    }

    if any(k in t for k in ["função afim", "funcao afim", "primeiro grau", "reta", "linear"]):
        info["kind"] = "linear"
    elif any(k in t for k in ["segundo grau", "quadrática", "quadratica", "parábola", "parabola"]):
        info["kind"] = "quadratic"
    elif any(k in t for k in ["terceiro grau", "cúbica", "cubica"]):
        info["kind"] = "cubic"
    elif "exponencial" in t:
        info["kind"] = "exp"
    elif any(k in t for k in ["logarítmica", "logaritmica", "logaritmo"]):
        info["kind"] = "log"
    elif any(k in t for k in ["modular", "módulo", "modulo"]):
        info["kind"] = "abs"

    if any(k in t for k in ["a < 0", "a menor que 0", "coeficiente angular negativo", "reta decrescente", "decrescente", "concavidade para baixo", "aberta para baixo"]):
        info["a_sign"] = "negative"
    elif any(k in t for k in ["a > 0", "a maior que 0", "coeficiente angular positivo", "reta crescente", "crescente", "concavidade para cima", "aberta para cima"]):
        info["a_sign"] = "positive"

    if any(k in t for k in ["delta > 0", "delta maior que 0", "duas raízes", "duas raizes", "duas soluções reais", "duas solucoes reais"]):
        info["delta_sign"] = "positive"
    elif any(k in t for k in ["delta = 0", "delta igual a 0", "uma raiz", "uma raiz real", "raiz dupla"]):
        info["delta_sign"] = "zero"
    elif any(k in t for k in ["delta < 0", "delta menor que 0", "nenhuma raiz real", "sem raízes reais", "sem raizes reais"]):
        info["delta_sign"] = "negative"

    return info


def choose_default_expression_from_constraints(text: str) -> str:
    info = infer_math_constraints_from_prompt(text)
    kind = info["kind"]
    a_sign = info["a_sign"]
    delta_sign = info["delta_sign"]

    if kind == "linear":
        return "-2*x + 3" if a_sign == "negative" else "2*x + 1"

    if kind == "quadratic":
        if delta_sign == "positive":
            return "-1*x**2 + 4*x - 3" if a_sign == "negative" else "x**2 - 5*x + 6"
        if delta_sign == "zero":
            return "-1*x**2 - 4*x - 4" if a_sign == "negative" else "x**2 - 4*x + 4"
        if delta_sign == "negative":
            return "-1*x**2 + 2*x - 5" if a_sign == "negative" else "x**2 + 2*x + 5"
        return "-1*x**2 + 4*x - 3" if a_sign == "negative" else "x**2 + 3*x - 4"

    if kind == "cubic":
        return "x**3 - 3*x"
    if kind == "exp":
        return "2**x"
    if kind == "log":
        return "log(x)"
    if kind == "abs":
        return "abs(x)"
    return ""

def generate_function_plot_from_text(text: str) -> tuple[str, str]:
    raw = (text or "").lower()

    if "y=" not in raw and "x" not in raw:
        expr = choose_default_expression_from_constraints(text)
        if not expr:
            raise ValueError("Não identifiquei qual função você quer plotar.")
    else:
        expr = safe_math_expression_from_text(text)

    if not expr:
        raise ValueError("Não consegui identificar a função.")

    x = np.linspace(-10, 10, 1200)
    safe_globals = {"np": np, "__builtins__": {}}
    y = eval(expr, safe_globals, {"x": x})
    y = np.where(np.abs(y) > 50, np.nan, y)

    fig, ax = plt.subplots(figsize=(8.8, 5), dpi=180)
    fig.patch.set_facecolor("#f7f1e8")
    ax.set_facecolor("#fffaf3")
    ax.plot(x, y, linewidth=2.4)
    ax.axhline(0, linewidth=1)
    ax.axvline(0, linewidth=1)
    ax.set_title(f"Gráfico da função y = {expr.replace('np.', '')}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return save_plot_figure(fig, "funcao"), expr.replace("np.", "")


def generate_mru_plot() -> str:
    t = np.linspace(0, 10, 200)
    s = 5 + 3 * t
    v = np.full_like(t, 3.0)

    fig, ax = plt.subplots(figsize=(9, 5), dpi=180)
    fig.patch.set_facecolor("#f7f1e8")
    ax.set_facecolor("#fffaf3")
    ax.plot(t, s, label="s(t) = 5 + 3t", linewidth=2.5)
    ax.plot(t, v, label="v(t) = 3", linewidth=2.2)
    ax.set_title("Exemplo visual de MRU")
    ax.set_xlabel("Tempo")
    ax.set_ylabel("Valor")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    return save_plot_figure(fig, "mru")


def generate_mruv_plot() -> str:
    t = np.linspace(0, 10, 200)
    s = 2 + 4*t + 0.5*1.5*(t**2)
    v = 4 + 1.5*t
    a = np.full_like(t, 1.5)

    fig, ax = plt.subplots(figsize=(9, 5), dpi=180)
    fig.patch.set_facecolor("#f7f1e8")
    ax.set_facecolor("#fffaf3")
    ax.plot(t, s, label="s(t) = 2 + 4t + 0,75t²", linewidth=2.5)
    ax.plot(t, v, label="v(t) = 4 + 1,5t", linewidth=2.2)
    ax.plot(t, a, label="a(t) = 1,5", linewidth=2.0)
    ax.set_title("Exemplo visual de MRUV")
    ax.set_xlabel("Tempo")
    ax.set_ylabel("Valor")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    return save_plot_figure(fig, "mruv")


def generate_projectile_diagram() -> str:
    g = 9.8
    v0 = 18
    ang = np.deg2rad(45)
    t_max = 2 * v0 * np.sin(ang) / g
    t = np.linspace(0, t_max, 200)
    x = v0 * np.cos(ang) * t
    y = v0 * np.sin(ang) * t - 0.5 * g * t**2

    fig, ax = plt.subplots(figsize=(8.8, 5), dpi=180)
    fig.patch.set_facecolor("#f7f1e8")
    ax.set_facecolor("#fffaf3")
    ax.plot(x, y, linewidth=2.6)
    ax.scatter([x[0]], [y[0]], s=70)
    ax.annotate("v₀", (x[8], y[8]), xytext=(x[8]+2, y[8]+2),
                arrowprops=dict(arrowstyle="->", lw=1.4))
    ax.axhline(0, linewidth=1)
    ax.set_title("Trajetória de lançamento oblíquo")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return save_plot_figure(fig, "trajetoria")


def generate_forces_diagram(inclined: bool = False) -> str:
    fig, ax = plt.subplots(figsize=(8, 5), dpi=180)
    fig.patch.set_facecolor("#f7f1e8")
    ax.set_facecolor("#fffaf3")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")

    if inclined:
        ax.plot([1, 8], [1, 4], linewidth=2.2)
        block_x, block_y = 4.5, 2.65
        ax.add_patch(plt.Rectangle((block_x, block_y), 1.3, 0.9, angle=23, fill=False, linewidth=2))
        ax.annotate("", xy=(block_x+1.5, block_y+2.2), xytext=(block_x+0.9, block_y+1.1),
                    arrowprops=dict(arrowstyle="->", lw=2))
        ax.text(block_x+1.55, block_y+2.25, "N", fontsize=12)
        ax.annotate("", xy=(block_x+0.65, block_y-1.3), xytext=(block_x+0.65, block_y+0.35),
                    arrowprops=dict(arrowstyle="->", lw=2))
        ax.text(block_x+0.75, block_y-1.35, "P", fontsize=12)
        ax.annotate("", xy=(block_x-0.6, block_y+0.1), xytext=(block_x+0.25, block_y+0.55),
                    arrowprops=dict(arrowstyle="->", lw=2))
        ax.text(block_x-0.85, block_y, "Atrito", fontsize=11)
        title = "Diagrama de forças em plano inclinado"
    else:
        ax.plot([1, 9], [2, 2], linewidth=2.2)
        ax.add_patch(plt.Rectangle((4.2, 2), 1.6, 1.2, fill=False, linewidth=2))
        ax.annotate("", xy=(5, 5), xytext=(5, 3.2), arrowprops=dict(arrowstyle="->", lw=2))
        ax.text(5.1, 5.05, "N", fontsize=12)
        ax.annotate("", xy=(5, 0.5), xytext=(5, 2), arrowprops=dict(arrowstyle="->", lw=2))
        ax.text(5.1, 0.4, "P", fontsize=12)
        ax.annotate("", xy=(7.6, 2.6), xytext=(5.8, 2.6), arrowprops=dict(arrowstyle="->", lw=2))
        ax.text(7.7, 2.7, "F", fontsize=12)
        title = "Diagrama simples de forças"

    ax.set_title(title)
    fig.tight_layout()
    return save_plot_figure(fig, "forcas")


def try_generate_visual_response(user_text: str) -> tuple[Optional[str], Optional[str]]:
    t = inherit_visual_context_from_history(user_text)

    if request_wants_derivation(user_text):
        return None, None

    if not request_wants_visual_generation(t):
        return None, None

    if any(k in t for k in ["seno", "cosseno", "coseno", "tangente", "trigonom"]):
        path = generate_trig_plot()
        msg = (
            "Gerei um gráfico real de seno, cosseno e tangente.\n\n"
            "Nele, o seno e o cosseno oscilam entre -1 e 1, enquanto a tangente cresce muito perto de 90° e 270°, "
            "por isso ela foi limitada visualmente para o gráfico ficar legível."
        )
        return path, msg

    if any(k in t for k in ["mruv", "movimento uniformemente variado", "movimento uniformemente acelerado"]):
        path = generate_mruv_plot()
        msg = (
            "Gerei um gráfico real de MRUV.\n\n"
            "A posição cresce em curva, a velocidade cresce em reta e a aceleração permanece constante."
        )
        return path, msg

    if any(k in t for k in ["mru", "movimento uniforme"]):
        path = generate_mru_plot()
        msg = (
            "Gerei um gráfico real de MRU.\n\n"
            "A posição varia linearmente com o tempo e a velocidade permanece constante."
        )
        return path, msg

    if any(k in t for k in ["trajetória", "trajetoria", "lançamento oblíquo", "lancamento obliquo", "projétil", "projetil"]):
        path = generate_projectile_diagram()
        msg = (
            "Gerei um esquema visual de lançamento oblíquo.\n\n"
            "A trajetória é parabólica: horizontalmente o movimento é uniforme, e verticalmente ele é acelerado pela gravidade."
        )
        return path, msg

    if any(k in t for k in ["plano inclinado", "normal", "atrito", "forças", "forcas", "diagrama de forças"]):
        inclined = "plano inclinado" in t
        path = generate_forces_diagram(inclined=inclined)
        msg = (
            "Gerei um diagrama simples de forças.\n\n"
            "Use esse esquema para visualizar as setas físicas antes de partir para as equações."
        )
        return path, msg

    if any(k in t for k in [
        "função", "funcao", "equação", "equacao", "y=", "reta", "parábola", "parabola",
        "plano cartesiano", "segundo grau", "quadrática", "quadratica",
        "primeiro grau", "função afim", "funcao afim", "afim", "linear", "cúbica", "cubica",
        "terceiro grau", "exponencial", "logarítmica", "logaritmica", "logaritmo",
        "módulo", "modulo", "modular"
    ]):
        try:
            path, expr = generate_function_plot_from_text(user_text)
            extra = ""
            if "x**2 + 3*x - 4" in expr:
                extra = " Como você pediu a equação do segundo grau sem informar coeficientes, usei o exemplo $y=x^2+3x-4$."
            msg = (
                f"Gerei um gráfico real da função $y={expr}$.{extra}\n\n"
                "Se quiser, também posso interpretar crescimento, raízes, vértice, interceptações ou domínio."
            )
            return path, msg
        except Exception:
            return None, None

    return None, None


def answer_user(user_text: str) -> str:
    intent = detect_intent(user_text)

    visual_path, visual_message = try_generate_visual_response(user_text)
    if visual_path:
        st.session_state.last_generated_image = visual_path
        return visual_message

    if intent == "linus":
        image_path = build_linus_pauling_diagram()
        st.session_state.last_generated_image = image_path
        return (
            "Gerei um diagrama de Linus Pauling para apoio visual.\n\n"
            "Use-o para seguir a ordem de preenchimento dos subníveis. "
            "Se quiser, também posso aplicar isso a um elemento específico, como cálcio, ferro ou cloro, "
            "e montar a distribuição eletrônica passo a passo."
        )

    if intent == "tabela_periodica":
        return (
            "A tabela periódica rápida está exibida acima para consulta. "
            "Se quiser, também posso classificar elementos, famílias, períodos ou propriedades periódicas."
        )

    if st.session_state.attachment_type == "image" and st.session_state.attachment_preview_path:
        return ask_vision_model(user_text, st.session_state.attachment_preview_path)

    return ask_text_model(user_text)


# =========================================================
# LOGIN
# =========================================================
def render_login_screen():
    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    st.markdown('<div class="logo-center">', unsafe_allow_html=True)
    if os.path.exists(IF_LOGO):
        st.image(IF_LOGO, width=190)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="project-badge">{PROJECT_NAME}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="inst-big">{INSTITUTION_NAME}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="inst-sub">{COURSE_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="title-main">Escolha como quer entrar</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">A IA decide sozinha se vai explicar, resolver, corrigir, resumir ou gerar questões.</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1.4, 1])

    with col1:
        nickname = st.text_input(
            "Como você quer ser chamado?",
            value=st.session_state.nickname,
            placeholder="Ex.: Iago, Professor João, Maria...",
        )
        role = st.radio("Escolha o perfil", ["Aluno", "Professor"], horizontal=True)

    with col2:
        preview_name = get_first_name(nickname)
        st.markdown(
            f"""
            <div class="soft-card">
                <div class="mini-title">Prévia</div>
                <div class="mini-desc">Nome: <b>{html.escape(preview_name)}</b></div>
                <div class="mini-desc">Perfil: <b>{html.escape(role)}</b></div>
                <div class="mini-desc">O tom muda para explicação amigável ou apoio docente mais técnico.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="mini-title" style="margin-bottom:10px;">Escolha seu mentor</div>', unsafe_allow_html=True)

    cols = st.columns(4)
    picked = None

    for idx, (mentor, meta) in enumerate(MENTORS.items()):
        with cols[idx]:
            st.markdown(
                f"""
                <div class="mentor-card">
                    <div>
                        <div class="mentor-emoji">{meta['emoji']}</div>
                        <div class="mentor-title">{mentor}</div>
                        <div class="mentor-sub">{meta['subtitle']}</div>
                    </div>
                    <div class="small-clean">{meta['description']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Entrar em {mentor}", key=f"pick_{mentor}", use_container_width=True):
                picked = mentor

    if picked:
        if not nickname.strip():
            st.warning("Digite como você quer ser chamado antes de entrar.")
        else:
            st.session_state.nickname = nickname.strip()
            st.session_state.profile = role
            st.session_state.mentor = picked
            st.session_state.auth_complete = True
            reset_visual_state(clear_file=True)
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


if not st.session_state.auth_complete:
    render_login_screen()
    st.stop()


# =========================================================
# LOAD INITIAL CONVERSATION
# =========================================================
rows = list_conversations()
if not rows:
    cid = create_conversation(mentor=st.session_state.mentor)
    st.session_state.current_conversation_id = cid
    load_conversation_into_state(cid)
elif st.session_state.current_conversation_id is None:
    st.session_state.current_conversation_id = rows[0][0]
    load_conversation_into_state(rows[0][0])


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown('<div class="brand-box">', unsafe_allow_html=True)
    if os.path.exists(IF_LOGO):
        st.image(IF_LOGO, width=170)
    st.markdown(f'<div class="brand-title">{INSTITUTION_NAME}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="brand-sub">{COURSE_NAME}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="account-box">
            <div class="account-name">{html.escape(get_first_name(st.session_state.nickname))}</div>
            <div class="account-sub">{html.escape(st.session_state.profile)} • Mentor de {html.escape(st.session_state.mentor)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    new_mentor = st.selectbox(
        "Trocar mentor",
        list(MENTORS.keys()),
        index=list(MENTORS.keys()).index(st.session_state.mentor),
    )

    if new_mentor != st.session_state.mentor:
        st.session_state.mentor = new_mentor
        update_conversation_mentor(st.session_state.current_conversation_id, new_mentor)

    if st.session_state.profile == "Professor":
        with st.expander("Ferramentas do professor", expanded=False):
            st.session_state.gabarito_rapido = st.text_area(
                "Gabarito / resposta esperada (opcional)",
                value=st.session_state.gabarito_rapido,
                height=90,
                placeholder="Ex.: 1) alternativa C\n2) F=ma\n3) 2,0 pontos se acertar o conceito...",
            )
            st.session_state.criterios_correcao = st.text_area(
                "Critérios / pontuação (opcional)",
                value=st.session_state.criterios_correcao,
                height=90,
                placeholder="Ex.: conceito 0,5 | cálculo 0,3 | unidade 0,2",
            )

    st.markdown("### Conversas")

    conv_rows = list_conversations()
    for row in conv_rows:
        cid, title, _updated, mentor, _attachment_name, last_mode = row
        c1, c2 = st.columns([6, 1], gap="small")

        with c1:
            if st.button(
                f"{title[:32]}{'...' if len(title) > 32 else ''}\n{mentor} • {last_mode or 'Livre'}",
                key=f"open_conv_{cid}",
                use_container_width=True,
            ):
                load_conversation_into_state(cid)
                st.rerun()

        with c2:
            with st.popover("⋯", use_container_width=True):
                novo_nome = st.text_input("Renomear", value=title, key=f"rename_input_{cid}")
                if st.button("Salvar nome", key=f"rename_btn_{cid}", use_container_width=True):
                    rename_conversation(cid, novo_nome)
                    if cid == st.session_state.current_conversation_id:
                        load_conversation_into_state(cid)
                    st.rerun()
                if st.button("Excluir conversa", key=f"delete_btn_{cid}", use_container_width=True):
                    deleting_current = cid == st.session_state.current_conversation_id
                    delete_conversation(cid)
                    remaining = list_conversations()
                    if deleting_current:
                        reset_visual_state(clear_file=True)
                        if remaining:
                            st.session_state.current_conversation_id = remaining[0][0]
                            load_conversation_into_state(remaining[0][0])
                        else:
                            new_id = create_conversation(mentor=st.session_state.mentor)
                            st.session_state.current_conversation_id = new_id
                            load_conversation_into_state(new_id)
                    st.rerun()

    coln1, coln2 = st.columns(2)
    with coln1:
        if st.button("Nova", use_container_width=True):
            reset_visual_state(clear_file=True)
            cid = create_conversation(mentor=st.session_state.mentor)
            st.session_state.current_conversation_id = cid
            load_conversation_into_state(cid)
            st.rerun()
    with coln2:
        if st.button("Sair", use_container_width=True):
            st.session_state.auth_complete = False
            st.rerun()


# =========================================================
# MAIN HEADER
# =========================================================
meta = MENTORS[st.session_state.mentor]

top1, top2 = st.columns([1.8, 1])

with top1:
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="project-badge">{PROJECT_NAME}</div>
            <div class="title-main">{APP_NAME}</div>
            <div style="font-weight:900; color:#5a483b; margin-top:4px;">{meta['title']}</div>
            <div class="muted" style="margin-top:6px;">{meta['description']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top2:
    st.markdown(
        f"""
        <div class="top-mini-card">
            <div class="mini-title">Ação detectada</div>
            <div class="mode-chip">{html.escape(st.session_state.last_detected_mode)}</div>
            <div style="height:8px"></div>
            <div class="mini-desc">Perfil: <b>{html.escape(st.session_state.profile)}</b></div>
            <div class="mini-desc">Mentor: <b>{html.escape(st.session_state.mentor)}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if st.session_state.mentor == "Química":
    render_periodic_table()

if st.session_state.attachment_name:
    st.markdown(
        f"<div class='attach-note'>Anexo ativo: <b>{html.escape(st.session_state.attachment_name)}</b> ({html.escape(st.session_state.attachment_type or 'arquivo')})</div>",
        unsafe_allow_html=True,
    )

    if (
        st.session_state.attachment_type == "image"
        and st.session_state.attachment_preview_path
        and os.path.exists(st.session_state.attachment_preview_path)
    ):
        st.image(
            st.session_state.attachment_preview_path,
            caption=st.session_state.attachment_name,
            use_container_width=True,
        )


# =========================================================
# CHAT HISTORY
# =========================================================
for msg in st.session_state.chat:
    avatar = avatar_if()
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("type") == "image":
            img_path = msg.get("content")
            caption = msg.get("caption", "Imagem")
            if img_path and os.path.exists(img_path):
                st.image(img_path, caption=caption, use_container_width=True)
            else:
                st.caption("Imagem não encontrada.")
        else:
            st.markdown(msg["content"], unsafe_allow_html=False)


# =========================================================
# ATTACH / CHAT BAR
# =========================================================
bar1, bar2 = st.columns([1.2, 4.8], gap="small")
with bar1:
    with st.popover("📎 Anexar", use_container_width=True):
        upload = st.file_uploader(
            "Envie PDF, imagem ou TXT",
            type=["pdf", "png", "jpg", "jpeg", "webp", "txt"],
            label_visibility="collapsed",
            key="chat_attachment",
        )
        if st.button("Remover anexo", use_container_width=True):
            update_attachment(st.session_state.current_conversation_id, None, None, None)
            st.session_state.attachment_text = None
            st.session_state.attachment_name = None
            st.session_state.attachment_type = None
            st.session_state.attachment_preview_path = None
            st.rerun()

        if upload is not None:
            err = validate_upload(upload)
            if err:
                st.warning(err)
            else:
                dest, name, ftype = save_upload(upload)
                update_attachment(st.session_state.current_conversation_id, dest, name, ftype)
                st.session_state.attachment_name = name
                st.session_state.attachment_type = ftype
                st.session_state.attachment_preview_path = dest if ftype == "image" else None

                if ftype == "pdf":
                    st.session_state.attachment_text = extract_pdf_text(dest)
                elif ftype == "text":
                    try:
                        with open(dest, "r", encoding="utf-8") as f:
                            st.session_state.attachment_text = f.read()
                    except Exception:
                        st.session_state.attachment_text = None
                else:
                    st.session_state.attachment_text = None

                st.toast(f"Anexo ativo: {name}")
                st.rerun()

with bar2:
    st.markdown(
        "<div class='panel-card' style='padding:10px 14px !important;'><div class='mini-desc'>Você pode pedir normalmente: explique, resolva, corrija, analise sua resolução, gere questões ou resuma um slide.</div></div>",
        unsafe_allow_html=True,
    )


# =========================================================
# CHAT INPUT
# =========================================================
user_prompt = st.chat_input(
    "Pergunte normalmente: explique, resolva, corrija, gere questões, resuma um slide, analise sua resolução..."
)

if user_prompt and user_prompt.strip():
    if st.session_state.contador_perguntas >= MAX_PERGUNTAS_SESSAO:
        st.warning("Você atingiu o limite de perguntas desta sessão.")
    else:
        question = user_prompt.strip()
        cid = st.session_state.current_conversation_id

        intent = detect_intent(question)
        st.session_state.last_detected_mode = detect_mode_label(intent)

        rename_first_message_title(cid, question)

        user_item = {"role": "user", "type": "text", "content": question}
        save_chat_item(cid, user_item)
        st.session_state.chat.append(user_item)
        st.session_state.contador_perguntas += 1

        existing_images = {
            m.get("content") for m in st.session_state.chat
            if m.get("type") == "image"
        }

        with st.spinner("Pensando..."):
            answer = answer_user(question)

        new_image_path = st.session_state.last_generated_image
        assistant_text_item = {"role": "assistant", "type": "text", "content": answer}
        save_chat_item(cid, assistant_text_item)
        st.session_state.chat.append(assistant_text_item)

        if new_image_path and new_image_path not in existing_images and os.path.exists(new_image_path):
            image_item = {
                "role": "assistant",
                "type": "image",
                "content": new_image_path,
                "caption": "Imagem gerada para apoio visual",
            }
            save_chat_item(cid, image_item)
            st.session_state.chat.append(image_item)

        st.rerun()

st.caption(f"{APP_NAME} • {INSTITUTION_NAME} • {COURSE_NAME}")
