import os
import re
import io
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
MAX_PERGUNTAS_SESSAO = 50
PDF_CONTEXT_LIMIT = 12000
CHAT_HISTORY_LIMIT = 8

os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================================================
# MENTORES / PERFIS
# =========================================================
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

TASK_MODES = [
    "Livre",
    "Explicar conteúdo",
    "Resolver questão",
    "Analisar resolução",
    "Corrigir questão/prova",
    "Resumir material",
    "Planejar aula",
    "Gerar lista de exercícios",
]

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
        --green-if: #1f8f4d;
        --shadow: 0 10px 26px rgba(78, 60, 44, .08);
    }

    html, body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"], section.main {
        background: var(--bg) !important;
        color: var(--text) !important;
    }

    .main .block-container {
        max-width: 1240px !important;
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

    .hero-card, .panel-card, .login-card, .mentor-card, .soft-card, .periodic-card, .top-mini-card {
        background: var(--card) !important;
        border: 1px solid var(--line) !important;
        border-radius: 22px !important;
        box-shadow: var(--shadow) !important;
    }

    .hero-card, .panel-card, .periodic-card, .top-mini-card {
        padding: 16px 18px !important;
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
    div[data-testid="baseButton-primary"] > button {
        background: var(--accent) !important;
        color: #fffaf4 !important;
        border: 1px solid var(--accent) !important;
        border-radius: 14px !important;
        min-height: 40px !important;
        box-shadow: none !important;
    }

    .stButton > button:hover,
    div[data-testid="baseButton-secondary"] > button:hover,
    div[data-testid="baseButton-primary"] > button:hover {
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
            task_mode TEXT,
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
        ("task_mode", "ALTER TABLE conversations ADD COLUMN task_mode TEXT"),
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
        "task_mode": "Livre",
        "chat": [],
        "current_conversation_id": None,
        "loaded_conversation_id": None,
        "attachment_text": None,
        "attachment_name": None,
        "attachment_type": None,
        "attachment_preview_path": None,
        "last_generated_image": None,
        "contador_perguntas": 0,
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


def safe_open_image(path: str) -> Optional[Image.Image]:
    try:
        return Image.open(path)
    except Exception:
        return None


def list_conversations() -> List[tuple]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, title, updated_at, mentor, attachment_name, task_mode
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
        SELECT id, title, created_at, updated_at, profile, nickname, mentor, task_mode,
               attachment_path, attachment_name, attachment_type, user_key
        FROM conversations
        WHERE id = ? AND user_key = ?
        """,
        (cid, build_user_key()),
    )
    row = cur.fetchone()
    conn.close()
    return row


def create_conversation(title: str = "Nova conversa", mentor: Optional[str] = None, task_mode: Optional[str] = None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    mentor = mentor or st.session_state.mentor
    task_mode = task_mode or st.session_state.task_mode
    now = now_iso()
    cur.execute(
        """
        INSERT INTO conversations(
            user_key, title, created_at, updated_at, profile, nickname, mentor, task_mode
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
            task_mode,
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
        "UPDATE conversations SET updated_at = ?, mentor = ?, task_mode = ? WHERE id = ? AND user_key = ?",
        (now, st.session_state.mentor, st.session_state.task_mode, cid, build_user_key()),
    )
    conn.commit()
    conn.close()


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


def update_conversation_meta(cid: int, mentor: str, task_mode: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE conversations
        SET mentor = ?, task_mode = ?, updated_at = ?
        WHERE id = ? AND user_key = ?
        """,
        (mentor, task_mode, now_iso(), cid, build_user_key()),
    )
    conn.commit()
    conn.close()


def reset_visual_state(clear_file: bool = True):
    st.session_state.chat = []
    st.session_state.loaded_conversation_id = None
    st.session_state.last_generated_image = None
    st.session_state.contador_perguntas = 0
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
        task_mode,
        attachment_path,
        attachment_name,
        attachment_type,
        _user_key,
    ) = conv

    st.session_state.profile = profile or st.session_state.profile
    st.session_state.nickname = nickname or st.session_state.nickname
    st.session_state.mentor = mentor or st.session_state.mentor
    st.session_state.task_mode = task_mode or st.session_state.task_mode
    st.session_state.chat = [{"role": r, "content": c} for r, c, _ in get_messages(cid)]
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

    if "linus pauling" in t or "diagrama de linus" in t:
        return "linus"

    if "tabela periódica" in t or "tabela periodica" in t:
        return "tabela_periodica"

    if any(k in t for k in ["corrigir prova", "corrija a prova", "corrigir questão", "corrigir questao", "gabarito", "rubrica"]):
        return "correcao"

    if any(k in t for k in ["analise minha resolução", "analise minha resolucao", "onde compliquei", "onde eu errei", "meu método"]):
        return "analise_resolucao"

    if any(k in t for k in ["resuma", "resumir", "resumo"]):
        return "resumo"

    if any(k in t for k in ["plano de aula", "sequência didática", "sequencia didatica"]):
        return "plano_aula"

    if any(k in t for k in ["lista de exercícios", "lista de exercicios", "simulado", "questões", "questoes"]):
        return "lista_exercicios"

    if any(k in t for k in ["gráfico", "grafico", "diagrama", "esquema visual", "imagem"]):
        return "visual"

    if any(k in t for k in ["questão", "questao", "resolver", "resolva"]):
        return "resolver"

    return "explicacao"


def detect_task_mode_from_intent(intent: str) -> str:
    mapping = {
        "correcao": "Corrigir questão/prova",
        "analise_resolucao": "Analisar resolução",
        "resumo": "Resumir material",
        "plano_aula": "Planejar aula",
        "lista_exercicios": "Gerar lista de exercícios",
        "resolver": "Resolver questão",
        "explicacao": "Explicar conteúdo",
        "visual": "Resolver questão",
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


def build_task_prompt(task_mode: str, intent: str) -> str:
    mode = task_mode or "Livre"

    prompts = {
        "Explicar conteúdo": """
Explique como um mentor muito bom:
- comece pela ideia central
- depois desenvolva
- use exemplos concretos
- se houver fórmula, explique o significado antes de usar
""",
        "Resolver questão": """
Resolva com foco em clareza:
- identifique dados
- diga o que a questão pede
- monte o raciocínio
- resolva
- destaque o resultado
- se houver caminho mais rápido, mostre no final
""",
        "Analisar resolução": """
Analise a resolução do aluno:
- diga se o raciocínio está certo, parcialmente certo ou errado
- avalie a eficiência do método
- mostre onde complicou sem necessidade, se for o caso
- proponha um caminho mais simples
- explique por que o caminho mais simples funciona
""",
        "Corrigir questão/prova": """
Atue como assistente de correção.
Não aja como avaliador arbitrário.
Faça:
- identificar resposta esperada (se houver gabarito explícito)
- comparar com a resposta do aluno
- apontar acertos e erros
- sugerir pontuação quando fizer sentido
- diferenciar método correto porém longo de erro real
- gerar feedback curto útil para professor e, se couber, para aluno
""",
        "Resumir material": """
Resuma de forma útil para estudo:
- tópicos principais
- conceitos-chave
- fórmulas importantes
- pontos de atenção
- mini revisão final
""",
        "Planejar aula": """
Monte uma resposta voltada a planejamento didático:
- objetivo
- conteúdo
- abordagem
- atividade
- avaliação
- observações
""",
        "Gerar lista de exercícios": """
Gere exercícios organizados por nível:
- fácil
- médio
- desafiador
Quando útil, inclua gabarito ou sugestões de resolução.
""",
        "Livre": """
Responda da forma mais útil possível, priorizando clareza, contexto e aplicabilidade.
""",
    }

    extra = ""
    if intent == "correcao":
        extra += "\nSe não houver gabarito suficiente, deixe isso claro e corrija de forma guiada, não arbitrária."
    if intent == "analise_resolucao":
        extra += "\nSe o aluno acertou por um caminho ruim, reconheça o acerto e depois ensine o caminho melhor."
    if intent == "visual":
        extra += "\nSe houver imagem, tente extrair o máximo de informação possível antes de dizer que falta algo."
    return (prompts.get(mode, prompts["Livre"]) + "\n" + extra).strip()


def system_prompt(profile: str, mentor: str, task_mode: str, intent: str) -> str:
    mentor_prompt = MENTORS[mentor]["prompt"]
    profile_prompt = build_profile_prompt(profile)
    task_prompt = build_task_prompt(task_mode, intent)

    base = f"""
Você é o {APP_NAME}, um mentor acadêmico institucional ligado ao {PROJECT_NAME} do {INSTITUTION_NAME}.
Atenda em português do Brasil.
Perfil atual do usuário: {profile}.
Área atual do mentor: {mentor}.
Modo atual: {task_mode}.

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
- Não fique pedindo configuração manual desnecessária.
- Evite respostas genéricas.

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
        f"Modo atual: {st.session_state.task_mode}",
        f"Intenção provável: {intent}",
    ]

    if history:
        parts.append("Histórico recente:\n" + history)

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
# GROQ CALLS
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
                        task_mode=st.session_state.task_mode,
                        intent=intent,
                    ),
                },
                {
                    "role": "user",
                    "content": build_user_prompt(user_text),
                },
            ],
            temperature=0.3,
            max_tokens=1600,
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
                        task_mode=st.session_state.task_mode,
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
            max_tokens=1800,
        )
        text = (resp.choices[0].message.content or "").strip()
        return clean_text(text) if text else "Não consegui gerar uma análise útil da imagem."
    except Exception as e:
        return f"Ocorreu um erro ao analisar a imagem: {e}"


def answer_user(user_text: str) -> str:
    intent = detect_intent(user_text)

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
# LOGIN / ENTRADA
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
    st.markdown('<div class="muted">Mais compacto, mais didático e pronto para leitura de imagem.</div>', unsafe_allow_html=True)
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
                <div class="mini-desc">A IA adapta o tom para explicação ou apoio docente.</div>
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
            st.session_state.task_mode = "Livre"
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
    cid = create_conversation(mentor=st.session_state.mentor, task_mode=st.session_state.task_mode)
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

    new_task_mode = st.selectbox(
        "Modo de uso",
        TASK_MODES,
        index=TASK_MODES.index(st.session_state.task_mode) if st.session_state.task_mode in TASK_MODES else 0,
    )

    if new_mentor != st.session_state.mentor or new_task_mode != st.session_state.task_mode:
        st.session_state.mentor = new_mentor
        st.session_state.task_mode = new_task_mode
        update_conversation_meta(st.session_state.current_conversation_id, new_mentor, new_task_mode)

    conv_rows = list_conversations()
    labels = {
        f"{row[1]} • {row[3]} • {row[5] or 'Livre'}": row[0]
        for row in conv_rows
    }

    if labels:
        current = st.session_state.current_conversation_id
        keys = list(labels.keys())
        vals = list(labels.values())
        idx = vals.index(current) if current in vals else 0
        chosen_key = st.selectbox("Conversas", keys, index=idx)
        chosen_id = labels[chosen_key]
        if chosen_id != st.session_state.current_conversation_id:
            load_conversation_into_state(chosen_id)
            st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Nova", use_container_width=True):
            reset_visual_state(clear_file=True)
            cid = create_conversation(mentor=st.session_state.mentor, task_mode=st.session_state.task_mode)
            st.session_state.current_conversation_id = cid
            load_conversation_into_state(cid)
            st.rerun()

    with c2:
        if st.button("Sair", use_container_width=True):
            st.session_state.auth_complete = False
            st.rerun()

    if st.button("Apagar conversa atual", use_container_width=True):
        cid = st.session_state.current_conversation_id
        delete_conversation(cid)
        remaining = list_conversations()
        reset_visual_state(clear_file=True)

        if remaining:
            st.session_state.current_conversation_id = remaining[0][0]
            load_conversation_into_state(remaining[0][0])
        else:
            cid = create_conversation(mentor=st.session_state.mentor, task_mode=st.session_state.task_mode)
            st.session_state.current_conversation_id = cid
            load_conversation_into_state(cid)

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
            <div class="mini-title">Modo ativo</div>
            <div class="mode-chip">{html.escape(st.session_state.task_mode)}</div>
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
        st.markdown(msg["content"], unsafe_allow_html=False)

if st.session_state.last_generated_image and os.path.exists(st.session_state.last_generated_image):
    st.image(
        st.session_state.last_generated_image,
        caption="Imagem gerada para apoio visual",
        use_container_width=True,
    )


# =========================================================
# ATTACHMENT BAR
# =========================================================
st.markdown('<div class="panel-card" style="margin-top:12px;">', unsafe_allow_html=True)
st.markdown('<div class="mini-title">Anexos perto do chat</div>', unsafe_allow_html=True)
st.markdown('<div class="mini-desc" style="margin-bottom:8px;">PDF, imagem ou TXT. Imagens serão analisadas pelo fluxo visual.</div>', unsafe_allow_html=True)

col_attach, col_clear = st.columns([5, 1])

with col_attach:
    upload = st.file_uploader(
        "Envie PDF, imagem ou TXT",
        type=["pdf", "png", "jpg", "jpeg", "webp", "txt"],
        label_visibility="collapsed",
        key="chat_attachment",
    )

with col_clear:
    if st.button("Limpar", use_container_width=True):
        update_attachment(st.session_state.current_conversation_id, None, None, None)
        st.session_state.attachment_text = None
        st.session_state.attachment_name = None
        st.session_state.attachment_type = None
        st.session_state.attachment_preview_path = None
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

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


# =========================================================
# CHAT INPUT
# =========================================================
placeholder = {
    "Livre": "Escreva sua dúvida, mande uma questão, slide, prova ou peça uma explicação...",
    "Explicar conteúdo": "Ex.: explique MRU como se eu fosse iniciante, mas sem perder o rigor...",
    "Resolver questão": "Ex.: resolva esta questão passo a passo e depois mostre um bizu...",
    "Analisar resolução": "Ex.: analise meu método, diga onde compliquei e mostre um caminho melhor...",
    "Corrigir questão/prova": "Ex.: corrija esta questão, sugira pontuação e dê feedback curto...",
    "Resumir material": "Ex.: resuma este PDF/slide para revisão de prova...",
    "Planejar aula": "Ex.: monte uma aula de 50 minutos sobre leis de Newton para ensino médio...",
    "Gerar lista de exercícios": "Ex.: gere 8 questões sobre função horária do espaço com gabarito...",
}.get(st.session_state.task_mode, "Escreva sua dúvida...")

user_prompt = st.chat_input(placeholder)

if user_prompt and user_prompt.strip():
    if st.session_state.contador_perguntas >= MAX_PERGUNTAS_SESSAO:
        st.warning("Você atingiu o limite de perguntas desta sessão.")
    else:
        question = user_prompt.strip()
        cid = st.session_state.current_conversation_id

        intent = detect_intent(question)

        if st.session_state.task_mode == "Livre":
            inferred_mode = detect_task_mode_from_intent(intent)
            if inferred_mode != "Livre":
                st.session_state.task_mode = inferred_mode
                update_conversation_meta(cid, st.session_state.mentor, st.session_state.task_mode)

        rename_first_message_title(cid, question)

        save_message(cid, "user", question)
        st.session_state.chat.append({"role": "user", "content": question})
        st.session_state.contador_perguntas += 1
        st.session_state.last_generated_image = None

        with st.spinner("Pensando..."):
            answer = answer_user(question)

        save_message(cid, "assistant", answer)
        st.session_state.chat.append({"role": "assistant", "content": answer})
        st.rerun()

st.caption(f"{APP_NAME} • {INSTITUTION_NAME} • {COURSE_NAME}")
