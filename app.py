import os
import re
import uuid
import html
import hashlib
import sqlite3
from datetime import datetime
from typing import Optional, Tuple, Dict, List

import streamlit as st
from groq import Groq
from pypdf import PdfReader


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
MODEL_NAME = "llama-3.3-70b-versatile"
MAX_PDF_MB = 15
MAX_FILE_MB = 8
MAX_PERGUNTAS_SESSAO = 40
PDF_CONTEXT_LIMIT = 7500
CHAT_HISTORY_LIMIT = 8

os.makedirs(UPLOAD_DIR, exist_ok=True)

MENTORS = {
    "Física": {
        "emoji": "⚛️",
        "subtitle": "cinemática, dinâmica, energia, circuitos e interpretação física",
        "accent": "#8f7a67",
        "description": "Explicações guiadas, linguagem física, fórmulas, gráficos e aplicações.",
        "quick": ["Explique MRU", "Resolva uma questão", "Faça um esquema visual"],
    },
    "Matemática": {
        "emoji": "📐",
        "subtitle": "álgebra, funções, geometria, trigonometria e notação matemática",
        "accent": "#8a735f",
        "description": "Passo a passo, LaTeX, raciocínio lógico e exercícios por nível.",
        "quick": ["Explique função do 2º grau", "Responda com LaTeX", "Gere 5 questões"],
    },
    "Química": {
        "emoji": "🧪",
        "subtitle": "nomenclatura, estequiometria, pH, ligações e tabela periódica",
        "accent": "#937b69",
        "description": "Conceitos químicos, cálculos e consulta rápida à tabela periódica.",
        "quick": ["Explique estequiometria", "Use o PDF anexado", "Monte um resumo"],
    },
    "Linguagens": {
        "emoji": "📚",
        "subtitle": "português, inglês, interpretação, gramática e produção textual",
        "accent": "#8a7568",
        "description": "Leitura, escrita, correção, análise textual e apoio em português e inglês.",
        "quick": ["Corrija este texto", "Explique gramática", "Pratique inglês"],
    },
}

PERIODIC_TABLE = [
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
        --bg-soft: #f2e8dc;
        --bg-sidebar: #efe2d3;
        --card: #fffaf4;
        --card-2: #fcf6ef;
        --line: #dac8b7;
        --text: #3b3027;
        --muted: #75685d;
        --accent: #8d7763;
        --accent-soft: #efe1d2;
        --shadow: 0 12px 30px rgba(78, 58, 40, .08);
    }

    html, body, [class*="css"] {
        color: var(--text) !important;
    }

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    section.main,
    .main .block-container {
        background: var(--bg) !important;
        color: var(--text) !important;
    }

    .main .block-container {
        max-width: 1180px !important;
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
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

    .hero-card, .panel-card, .mentor-card, .login-card, .soft-card, .table-card {
        background: var(--card) !important;
        border: 1px solid var(--line) !important;
        border-radius: 24px !important;
        box-shadow: var(--shadow) !important;
    }

    .hero-card, .panel-card, .table-card {
        padding: 22px;
    }

    .login-card {
        padding: 28px;
        max-width: 980px;
        margin: 28px auto;
    }

    .soft-card {
        padding: 14px 16px;
        border-radius: 18px !important;
    }

    .project-badge {
        display:inline-block;
        padding: 7px 12px;
        background: var(--accent-soft);
        border: 1px solid var(--line);
        border-radius: 999px;
        font-weight: 700;
        color: #66574a !important;
        margin-bottom: 10px;
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1.05;
        margin-bottom: 4px;
        color: #5a483b !important;
    }

    .hero-sub, .muted {
        color: var(--muted) !important;
    }

    .sidebar-brand {
        text-align: center;
        margin-bottom: 16px;
    }

    .sidebar-brand img {
        display: block;
        margin: 0 auto 10px auto;
        max-width: 180px;
    }

    .sidebar-inst-title {
        font-size: 1.12rem;
        font-weight: 800;
        color: #5a483b !important;
        line-height: 1.12;
    }

    .sidebar-inst-sub {
        color: var(--muted) !important;
        font-size: .96rem;
        margin-top: 4px;
    }

    .mentor-card {
        padding: 18px;
        min-height: 220px;
        display:flex;
        flex-direction:column;
        justify-content:space-between;
    }

    .mentor-emoji {
        font-size: 2rem;
        margin-bottom: 8px;
    }

    .mentor-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #544236 !important;
        margin-bottom: 6px;
    }

    .mentor-subtitle {
        color: var(--muted) !important;
        font-size: .95rem;
        margin-bottom: 8px;
    }

    .mentor-chip {
        display:inline-block;
        margin: 3px 4px 0 0;
        padding: 5px 9px;
        border-radius: 999px;
        border: 1px solid var(--line);
        background: #f8efe5;
        color: #66574a !important;
        font-size: .8rem;
    }

    .account-box {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 14px;
        margin-bottom: 10px;
    }

    .account-name {
        font-weight: 800;
        color: #534236 !important;
    }

    .account-sub {
        color: var(--muted) !important;
        font-size: .9rem;
    }

    .metric-strip {
        display:grid;
        grid-template-columns: repeat(3, minmax(0,1fr));
        gap: 12px;
        margin-top: 14px;
    }

    .metric-box {
        background: var(--card-2);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 12px;
    }

    .metric-label { color: var(--muted) !important; font-size: .85rem; }
    .metric-value { font-size: 1.02rem; font-weight: 800; color: #564439 !important; }

    .attach-pill {
        display:inline-block;
        padding: 7px 12px;
        border-radius: 999px;
        background: #f7ecdf;
        border:1px solid var(--line);
        font-size: .88rem;
        color: #66574a !important;
        margin-right: 8px;
        margin-bottom: 8px;
    }

    .periodic-table {
        display:grid;
        grid-template-columns: repeat(18, minmax(0,1fr));
        gap: 6px;
        margin-top: 14px;
    }

    .pt-cell {
        min-height: 42px;
        border-radius: 12px;
        border: 1px solid #d6c2af;
        background: #fff6eb;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size: .82rem;
        font-weight: 700;
        color: #5b493d !important;
    }

    .pt-cell-empty {
        background: transparent;
        border: none;
    }

    .series-row {
        display:grid;
        grid-template-columns: repeat(15, minmax(0,1fr));
        gap: 6px;
        margin-top: 8px;
    }

    [data-testid="stChatInputContainer"],
    [data-testid="stBottomBlockContainer"] {
        background: var(--bg) !important;
        border-top: 1px solid var(--line) !important;
    }

    [data-testid="stChatInput"] textarea,
    [data-testid="stTextInputRootElement"] input,
    .stTextInput input,
    .stTextArea textarea,
    [data-baseweb="select"] > div,
    [data-baseweb="base-input"] > div {
        background: #fffaf4 !important;
        color: var(--text) !important;
        border: 1px solid var(--line) !important;
        border-radius: 16px !important;
    }

    [data-testid="stChatInput"] textarea::placeholder,
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: var(--muted) !important;
    }

    .stButton > button,
    [data-testid="baseButton-secondary"],
    [data-testid="baseButton-primary"] {
        background: var(--accent) !important;
        color: #fffaf4 !important;
        border: 1px solid var(--accent) !important;
        border-radius: 14px !important;
        min-height: 42px !important;
    }

    .stButton > button:hover,
    [data-testid="baseButton-secondary"]:hover,
    [data-testid="baseButton-primary"]:hover {
        filter: brightness(.97);
    }

    button[kind="secondary"], button[kind="tertiary"] {
        color: var(--text) !important;
    }

    [data-baseweb="popover"],
    [data-baseweb="popover"] > div,
    [data-baseweb="menu"],
    [role="listbox"],
    [role="dialog"] {
        background: #fffaf4 !important;
        color: var(--text) !important;
        border-color: var(--line) !important;
    }

    [role="option"], [data-baseweb="menu"] * {
        color: var(--text) !important;
    }

    [data-testid="stChatMessageContent"] {
        color: var(--text) !important;
        border-radius: 18px !important;
        border: 1px solid var(--line) !important;
        padding: .7rem .85rem !important;
    }

    .stChatMessage:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
        background: #fff9f2 !important;
    }

    .stChatMessage:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
        background: #efe2d3 !important;
    }

    p, span, label, li, h1, h2, h3, h4, h5, h6, small, div {
        color: var(--text);
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
            user_key TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT 'Nova conversa',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            profile TEXT,
            nickname TEXT,
            mentor TEXT,
            pdf_path TEXT,
            pdf_name TEXT,
            image_path TEXT,
            image_name TEXT,
            attachment_kind TEXT
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
    for col, ddl in {
        "mentor": "ALTER TABLE conversations ADD COLUMN mentor TEXT",
        "pdf_path": "ALTER TABLE conversations ADD COLUMN pdf_path TEXT",
        "pdf_name": "ALTER TABLE conversations ADD COLUMN pdf_name TEXT",
        "image_path": "ALTER TABLE conversations ADD COLUMN image_path TEXT",
        "image_name": "ALTER TABLE conversations ADD COLUMN image_name TEXT",
        "attachment_kind": "ALTER TABLE conversations ADD COLUMN attachment_kind TEXT",
    }.items():
        if col not in cols:
            cur.execute(ddl)
    conn.commit()
    conn.close()


init_db()


# =========================================================
# STATE
# =========================================================
def init_state():
    defaults = {
        "auth_complete": False,
        "profile": "Aluno",
        "nickname": "",
        "mentor": "Física",
        "chat": [],
        "db_texto_pdf": None,
        "pdf_nome": None,
        "image_nome": None,
        "current_conversation_id": None,
        "loaded_conversation_id": None,
        "contador_perguntas": 0,
        "last_detected_intent": None,
        "pending_upload": None,
        "pending_upload_label": None,
        "pending_upload_kind": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# =========================================================
# HELPERS
# =========================================================
def get_first_name(name: str) -> str:
    txt = (name or "").strip()
    return txt.split()[0] if txt else "Usuário"


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


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def reset_visual_state():
    st.session_state.chat = []
    st.session_state.db_texto_pdf = None
    st.session_state.pdf_nome = None
    st.session_state.image_nome = None
    st.session_state.contador_perguntas = 0
    st.session_state.last_detected_intent = None
    st.session_state.pending_upload = None
    st.session_state.pending_upload_label = None
    st.session_state.pending_upload_kind = None


def list_conversations():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, title, updated_at, mentor, profile, pdf_name, image_name
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
        SELECT id, title, created_at, updated_at, profile, nickname, mentor,
               pdf_path, pdf_name, image_path, image_name, attachment_kind
        FROM conversations
        WHERE id = ? AND user_key = ?
        """,
        (cid, build_user_key()),
    )
    row = cur.fetchone()
    conn.close()
    return row


def create_conversation(title: str = "Nova conversa") -> int:
    conn = get_conn()
    cur = conn.cursor()
    now = now_iso()
    cur.execute(
        """
        INSERT INTO conversations(
            user_key, title, created_at, updated_at, profile, nickname, mentor,
            pdf_path, pdf_name, image_path, image_name, attachment_kind
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            build_user_key(),
            title,
            now,
            now,
            st.session_state.profile,
            st.session_state.nickname,
            st.session_state.mentor,
            None,
            None,
            None,
            None,
            None,
        ),
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid


def save_message(cid: int, role: str, content: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (cid, role, content, now_iso()),
    )
    cur.execute("UPDATE conversations SET updated_at = ?, mentor = ?, profile = ?, nickname = ? WHERE id = ?",
                (now_iso(), st.session_state.mentor, st.session_state.profile, st.session_state.nickname, cid))
    conn.commit()
    conn.close()


def get_messages(cid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY id ASC",
        (cid,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def maybe_update_title_from_first_message(cid: int, text: str):
    txt = re.sub(r"\s+", " ", (text or "").strip())
    if not txt:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT title FROM conversations WHERE id = ? AND user_key = ?", (cid, build_user_key()))
    row = cur.fetchone()
    if row and row[0] == "Nova conversa":
        cur.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ? AND user_key = ?",
            (txt[:70], now_iso(), cid, build_user_key()),
        )
        conn.commit()
    conn.close()


def update_conversation_attachment(cid: int, *, pdf_path=None, pdf_name=None, image_path=None, image_name=None, attachment_kind=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE conversations
        SET pdf_path = ?, pdf_name = ?, image_path = ?, image_name = ?, attachment_kind = ?, updated_at = ?, mentor = ?
        WHERE id = ? AND user_key = ?
        """,
        (pdf_path, pdf_name, image_path, image_name, attachment_kind, now_iso(), st.session_state.mentor, cid, build_user_key()),
    )
    conn.commit()
    conn.close()


def delete_conversation(cid: int):
    conv = get_conversation(cid)
    if conv:
        for p in [conv[7], conv[9]]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE conversation_id = ?", (cid,))
    cur.execute("DELETE FROM conversations WHERE id = ? AND user_key = ?", (cid, build_user_key()))
    conn.commit()
    conn.close()


def load_conversation_into_state(cid: int):
    conv = get_conversation(cid)
    if not conv:
        return
    (_, _, _, _, profile, nickname, mentor, pdf_path, pdf_name, image_path, image_name, _) = conv
    st.session_state.profile = profile or st.session_state.profile
    st.session_state.nickname = nickname or st.session_state.nickname
    st.session_state.mentor = mentor or st.session_state.mentor
    st.session_state.chat = [{"role": r, "content": c} for r, c, _ in get_messages(cid)]
    st.session_state.current_conversation_id = cid
    st.session_state.loaded_conversation_id = cid
    st.session_state.pdf_nome = pdf_name
    st.session_state.image_nome = image_name
    st.session_state.db_texto_pdf = process_pdf_from_path(pdf_path) if pdf_path and os.path.exists(pdf_path) else None


def get_file_ext(name: str) -> str:
    return os.path.splitext(name or "")[1].lower()


def size_mb(uploaded_file) -> float:
    return round(len(uploaded_file.getbuffer()) / (1024 * 1024), 2)


def validate_upload(uploaded_file) -> Optional[str]:
    ext = get_file_ext(uploaded_file.name)
    mb = size_mb(uploaded_file)
    if ext == ".pdf" and mb > MAX_PDF_MB:
        return f"O PDF excede o limite de {MAX_PDF_MB} MB."
    if ext in {".png", ".jpg", ".jpeg", ".webp"} and mb > MAX_FILE_MB:
        return f"A imagem excede o limite de {MAX_FILE_MB} MB."
    if ext not in {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt", ".md"}:
        return "Anexe PDF, imagem, TXT ou MD."
    return None


def save_upload(uploaded_file) -> Tuple[str, str]:
    ext = get_file_ext(uploaded_file.name)
    dest = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return dest, uploaded_file.name


def process_pdf_from_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    try:
        reader = PdfReader(path)
        texts = []
        for page in reader.pages:
            txt = (page.extract_text() or "").strip()
            if txt:
                texts.append(re.sub(r"\s+", " ", txt))
        final = "\n\n".join(texts).strip()
        return final or None
    except Exception:
        return None


def read_text_file(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read().strip()
        return txt or None
    except Exception:
        return None


# =========================================================
# GROQ
# =========================================================
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


# =========================================================
# MENTOR / PROMPT
# =========================================================
def infer_intent(text: str, has_pdf: bool, has_image: bool) -> str:
    t = (text or "").lower()
    if has_pdf and any(k in t for k in ["resuma", "resumir", "resumo", "use o pdf", "leia o pdf", "analise o pdf"]):
        return "resumo_pdf"
    if has_image and any(k in t for k in ["imagem", "foto", "analise a imagem", "olhe a imagem"]):
        return "imagem"
    if any(k in t for k in ["latex", "fórmula", "formula", "equação", "equacao", "notação", "notacao"]):
        return "latex"
    if any(k in t for k in ["questão", "questao", "exercício", "exercicio", "quiz", "simulado"]):
        return "exercicios"
    if any(k in t for k in ["corrija", "corrigir", "revise", "onde eu errei", "feedback"]):
        return "correcao"
    if st.session_state.profile == "Professor" and any(k in t for k in ["plano de aula", "sequência didática", "sequencia didatica", "atividade", "metodologia"]):
        return "planejamento"
    if st.session_state.profile == "Professor" and any(k in t for k in ["média", "media", "notas", "nota", "turma"]):
        return "apoio_docente"
    return "explicacao"


def format_recent_history(chat: List[Dict[str, str]], limit: int = CHAT_HISTORY_LIMIT) -> str:
    parts = []
    for msg in chat[-limit:]:
        role = "Usuário" if msg["role"] == "user" else "Assistente"
        content = (msg["content"] or "").strip()
        if content:
            parts.append(f"{role}: {content[:500]}")
    return "\n".join(parts)


def mentor_system_prompt(intent: str) -> str:
    mentor = st.session_state.mentor
    profile = st.session_state.profile
    name = get_first_name(st.session_state.nickname)
    base = f"""
Você é o {mentor}Mentor do MentorEdu IA, projeto institucional do {INSTITUTION_NAME}, ligado ao {PROJECT_NAME} e à {COURSE_NAME}.
Atenda {name}, no perfil {profile}.
Área/mentor atual: {mentor}.
Responda em português do Brasil.
Use tom claro, didático, elegante e humano.
Não peça para o usuário configurar funções manualmente.
Quando houver matemática, física ou química com fórmulas, use LaTeX válido com $...$ e $$...$$.
Quando houver PDF, use o conteúdo do PDF apenas se ele for relevante.
Se o usuário pedir imagem, reconheça a limitação caso não haja leitura visual suficiente e peça descrição complementar sem inventar detalhes.
""".strip()

    area_rules = {
        "Física": "Especialize suas respostas em linguagem física, significado das grandezas, interpretação de gráficos, unidades e erros conceituais comuns.",
        "Matemática": "Especialize suas respostas em raciocínio lógico, demonstração passo a passo, organização algébrica, interpretação simbólica e notação matemática.",
        "Química": "Especialize suas respostas em nomenclaturas, reações, estequiometria, linguagem química, balanceamento e uso conceitual da tabela periódica.",
        "Linguagens": "Especialize suas respostas em leitura, produção textual, gramática, interpretação, português e inglês quando pedido.",
    }
    base += "\n" + area_rules.get(mentor, "")

    if profile == "Professor":
        base += "\nAo atender professores, priorize metodologia, planejamento, avaliações, organização didática, médias e iniciação científica."
    else:
        base += "\nAo atender alunos, priorize explicação progressiva, exercícios, revisão, correção e acolhimento."

    extras = {
        "resumo_pdf": "Sua tarefa principal é resumir, explicar e organizar o PDF anexado.",
        "latex": "Sua tarefa principal é responder com boa notação matemática e clareza formal.",
        "exercicios": "Sua tarefa principal é criar ou resolver exercícios com dificuldade adequada.",
        "correcao": "Sua tarefa principal é apontar acertos, erros e melhorias.",
        "planejamento": "Sua tarefa principal é montar planejamento, sequência didática ou atividade.",
        "apoio_docente": "Sua tarefa principal é apoiar tarefas docentes práticas, incluindo notas e médias.",
        "imagem": "Se a imagem não puder ser lida de forma confiável, deixe isso explícito e peça uma breve descrição; não invente conteúdo visual.",
    }
    return base + "\n" + extras.get(intent, "")


def build_user_prompt(question: str, attachment_text: Optional[str], attachment_hint: Optional[str], intent: str) -> str:
    parts = [
        f"Perfil: {st.session_state.profile}",
        f"Nome: {get_first_name(st.session_state.nickname)}",
        f"Mentor atual: {st.session_state.mentor}",
        f"Intenção inferida: {intent}",
    ]
    hist = format_recent_history(st.session_state.chat)
    if hist:
        parts.append("Histórico recente:\n" + hist)
    if attachment_hint:
        parts.append("Anexo ativo:\n" + attachment_hint)
    if attachment_text:
        parts.append("Conteúdo de apoio do anexo:\n" + attachment_text[:PDF_CONTEXT_LIMIT])
    parts.append("Pedido atual:\n" + question.strip())
    return "\n\n".join(parts)


def generate_response(system_prompt: str, user_prompt: str) -> str:
    if client is None:
        return client_error or "Não consegui iniciar a IA."
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1250,
        )
        text = (resp.choices[0].message.content or "").strip()
        return re.sub(r"\n{3,}", "\n\n", text) or "Não consegui gerar uma resposta útil."
    except Exception as e:
        return f"Ocorreu um erro ao gerar a resposta: {e}"


# =========================================================
# UI BUILDERS
# =========================================================
def render_periodic_table():
    st.markdown('<div class="table-card">', unsafe_allow_html=True)
    st.markdown("**Tabela periódica rápida**")
    st.caption("Consulta visual leve para o mentor de Química.")
    html_rows = ['<div class="periodic-table">']
    for row in PERIODIC_TABLE:
        for cell in row:
            if cell:
                html_rows.append(f'<div class="pt-cell">{html.escape(cell)}</div>')
            else:
                html_rows.append('<div class="pt-cell pt-cell-empty"></div>')
    html_rows.append('</div>')
    html_rows.append('<div style="margin-top:14px; font-weight:700; color:#5b493d;">Lantanídeos</div>')
    html_rows.append('<div class="series-row">' + ''.join(f'<div class="pt-cell">{html.escape(x)}</div>' for x in LANTHANIDES) + '</div>')
    html_rows.append('<div style="margin-top:10px; font-weight:700; color:#5b493d;">Actinídeos</div>')
    html_rows.append('<div class="series-row">' + ''.join(f'<div class="pt-cell">{html.escape(x)}</div>' for x in ACTINIDES) + '</div>')
    st.markdown(''.join(html_rows), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_login_screen():
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    top_col1, top_col2 = st.columns([1.1, 1.3])
    with top_col1:
        if os.path.exists(IF_LOGO):
            st.image(IF_LOGO, width=220)
        st.markdown(f'<div class="project-badge">{PROJECT_NAME}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="hero-title">{APP_NAME}</div>', unsafe_allow_html=True)
        st.markdown(f'<div><b>{INSTITUTION_NAME}</b><br><span class="muted">{COURSE_NAME}</span></div>', unsafe_allow_html=True)
        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="muted">Escolha seu nome, seu perfil e o mentor principal. A experiência continua simples, mas cada mentor já entra com contexto próprio.</div>', unsafe_allow_html=True)

    with top_col2:
        st.text_input(
            "Como você quer ser chamado?",
            key="nickname_input_login",
            value=st.session_state.nickname,
            placeholder="Ex.: Iago, Professor André...",
        )
        if st.session_state.get("nickname_input_login") != st.session_state.nickname:
            st.session_state.nickname = st.session_state.get("nickname_input_login", "")
        profile = st.radio("Perfil", ["Aluno", "Professor"], horizontal=True, index=0 if st.session_state.profile == "Aluno" else 1)
        st.session_state.profile = profile

    st.markdown("### Escolha seu mentor")
    cols = st.columns(4)
    selected = st.session_state.mentor
    for idx, (mentor_name, meta) in enumerate(MENTORS.items()):
        with cols[idx]:
            st.markdown(
                f'''<div class="mentor-card"><div><div class="mentor-emoji">{meta["emoji"]}</div><div class="mentor-title">{mentor_name}</div><div class="mentor-subtitle">{meta["subtitle"]}</div><div class="muted">{meta["description"]}</div></div><div>{''.join(f'<span class="mentor-chip">{html.escape(ch)}</span>' for ch in meta["quick"])}</div></div>''',
                unsafe_allow_html=True,
            )
            if st.button(f"Escolher {mentor_name}", key=f"pick_{mentor_name}", use_container_width=True):
                selected = mentor_name
                st.session_state.mentor = mentor_name

    st.markdown(f'<div class="soft-card" style="margin-top:16px;"><b>Mentor atual:</b> {selected} <span class="muted">• {MENTORS[selected]["subtitle"]}</span></div>', unsafe_allow_html=True)
    if st.button("Entrar", type="primary", use_container_width=True):
        if not st.session_state.nickname.strip():
            st.warning("Digite como você quer ser chamado.")
        else:
            st.session_state.auth_complete = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def ensure_current_conversation():
    rows = list_conversations()
    if not rows:
        cid = create_conversation()
        st.session_state.current_conversation_id = cid
        load_conversation_into_state(cid)
    elif st.session_state.current_conversation_id is None:
        st.session_state.current_conversation_id = rows[0][0]
        load_conversation_into_state(rows[0][0])


def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">', unsafe_allow_html=True)
        if os.path.exists(IF_LOGO):
            st.image(IF_LOGO, width=190)
        st.markdown(f'<div class="sidebar-inst-title">{INSTITUTION_NAME}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sidebar-inst-sub">{COURSE_NAME}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            f'''<div class="account-box"><div class="account-name">{get_first_name(st.session_state.nickname)}</div><div class="account-sub">{st.session_state.profile} • Mentor {st.session_state.mentor}</div></div>''',
            unsafe_allow_html=True,
        )

        if st.button("Nova conversa", use_container_width=True):
            cid = create_conversation()
            reset_visual_state()
            st.session_state.current_conversation_id = cid
            load_conversation_into_state(cid)
            st.rerun()

        rows = list_conversations()
        options = {f"{r[1]} • {r[3] or '—'}": r[0] for r in rows}
        keys = list(options.keys())
        current_id = st.session_state.current_conversation_id
        index = 0
        for i, v in enumerate(options.values()):
            if v == current_id:
                index = i
                break
        picked = st.selectbox("Conversas", keys, index=index, label_visibility="collapsed") if keys else None
        if picked and options[picked] != current_id:
            load_conversation_into_state(options[picked])
            st.rerun()

        pop = getattr(st, "popover", None)
        if pop:
            with st.popover("⋯ Opções da conversa", use_container_width=True):
                st.caption("A conversa já recebe nome automático pela primeira pergunta.")
                if st.button("Apagar conversa atual", use_container_width=True):
                    delete_conversation(st.session_state.current_conversation_id)
                    reset_visual_state()
                    remain = list_conversations()
                    new_id = remain[0][0] if remain else create_conversation()
                    st.session_state.current_conversation_id = new_id
                    load_conversation_into_state(new_id)
                    st.rerun()
        else:
            if st.button("Apagar conversa atual", use_container_width=True):
                delete_conversation(st.session_state.current_conversation_id)
                reset_visual_state()
                remain = list_conversations()
                new_id = remain[0][0] if remain else create_conversation()
                st.session_state.current_conversation_id = new_id
                load_conversation_into_state(new_id)
                st.rerun()

        if st.button("Trocar perfil / mentor", use_container_width=True):
            st.session_state.auth_complete = False
            st.rerun()


def render_main_header():
    mentor = st.session_state.mentor
    st.markdown(
        f'''
        <div class="hero-card">
            <div class="project-badge">{PROJECT_NAME}</div>
            <div class="hero-title">{APP_NAME}</div>
            <div><b>{INSTITUTION_NAME}</b> • <span class="muted">{COURSE_NAME}</span></div>
            <div class="hero-sub" style="margin-top:10px;">Olá, {get_first_name(st.session_state.nickname)}. Você está com o mentor de <b>{mentor}</b> no perfil <b>{st.session_state.profile}</b>.</div>
            <div class="metric-strip">
                <div class="metric-box"><div class="metric-label">Mentor</div><div class="metric-value">{mentor}</div></div>
                <div class="metric-box"><div class="metric-label">Perfil</div><div class="metric-value">{st.session_state.profile}</div></div>
                <div class="metric-box"><div class="metric-label">Anexo ativo</div><div class="metric-value">{st.session_state.pdf_nome or st.session_state.image_nome or 'Nenhum'}</div></div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_mentor_switcher():
    st.markdown('<div class="panel-card" style="margin-top:14px;">', unsafe_allow_html=True)
    st.markdown("### Escolha de mentor")
    st.caption("A interface mantém o mesmo clima visual, mas o mentor muda o contexto pedagógico.")
    cols = st.columns(4)
    for idx, (mentor_name, meta) in enumerate(MENTORS.items()):
        with cols[idx]:
            active = mentor_name == st.session_state.mentor
            label = f"{meta['emoji']} {mentor_name}" + (" • atual" if active else "")
            if st.button(label, key=f"switch_{mentor_name}", use_container_width=True):
                st.session_state.mentor = mentor_name
                if st.session_state.current_conversation_id:
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("UPDATE conversations SET mentor = ?, updated_at = ? WHERE id = ? AND user_key = ?",
                                (mentor_name, now_iso(), st.session_state.current_conversation_id, build_user_key()))
                    conn.commit()
                    conn.close()
                st.rerun()
    st.markdown(f'<div class="soft-card" style="margin-top:10px;"><b>{st.session_state.mentor}</b> • <span class="muted">{MENTORS[st.session_state.mentor]["description"]}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_attachment_bar():
    st.markdown('<div class="panel-card" style="margin-top:14px;">', unsafe_allow_html=True)
    st.markdown("### Arquivos e apoio")
    st.caption("Os anexos ficam perto do chat, para uso mais intuitivo no celular e no desktop.")

    c1, c2 = st.columns([1.2, 1])
    with c1:
        if getattr(st, "popover", None):
            with st.popover("Anexar arquivo", use_container_width=True):
                st.file_uploader("PDF", type=["pdf"], key="up_pdf")
                st.file_uploader("Imagem", type=["png", "jpg", "jpeg", "webp"], key="up_img")
                st.file_uploader("Texto", type=["txt", "md"], key="up_text")
        else:
            st.file_uploader("PDF, imagem ou texto", type=["pdf", "png", "jpg", "jpeg", "webp", "txt", "md"], key="up_any")

        uploaded = None
        kind = None
        label = None
        if st.session_state.get("up_pdf") is not None:
            uploaded = st.session_state.get("up_pdf")
            kind = "pdf"
            label = uploaded.name
        elif st.session_state.get("up_img") is not None:
            uploaded = st.session_state.get("up_img")
            kind = "image"
            label = uploaded.name
        elif st.session_state.get("up_text") is not None:
            uploaded = st.session_state.get("up_text")
            kind = "text"
            label = uploaded.name
        elif st.session_state.get("up_any") is not None:
            uploaded = st.session_state.get("up_any")
            ext = get_file_ext(uploaded.name)
            kind = "pdf" if ext == ".pdf" else ("image" if ext in {".png", ".jpg", ".jpeg", ".webp"} else "text")
            label = uploaded.name

        if uploaded is not None:
            st.session_state.pending_upload = uploaded
            st.session_state.pending_upload_label = label
            st.session_state.pending_upload_kind = kind

        if st.button("Usar anexo nesta conversa", use_container_width=True):
            uploaded = st.session_state.pending_upload
            if uploaded is None:
                st.info("Selecione um arquivo primeiro.")
            else:
                error = validate_upload(uploaded)
                if error:
                    st.warning(error)
                else:
                    path, original_name = save_upload(uploaded)
                    cid = st.session_state.current_conversation_id
                    if st.session_state.pending_upload_kind == "pdf":
                        st.session_state.db_texto_pdf = process_pdf_from_path(path)
                        st.session_state.pdf_nome = original_name
                        st.session_state.image_nome = None
                        update_conversation_attachment(cid, pdf_path=path, pdf_name=original_name, image_path=None, image_name=None, attachment_kind="pdf")
                    elif st.session_state.pending_upload_kind == "image":
                        st.session_state.image_nome = original_name
                        st.session_state.pdf_nome = None
                        st.session_state.db_texto_pdf = None
                        update_conversation_attachment(cid, pdf_path=None, pdf_name=None, image_path=path, image_name=original_name, attachment_kind="image")
                    else:
                        txt = read_text_file(path)
                        st.session_state.db_texto_pdf = txt
                        st.session_state.pdf_nome = original_name
                        st.session_state.image_nome = None
                        update_conversation_attachment(cid, pdf_path=path, pdf_name=original_name, image_path=None, image_name=None, attachment_kind="text")
                    st.success(f"Anexo ativo: {original_name}")
                    st.session_state.pending_upload = None
                    st.session_state.pending_upload_label = None
                    st.session_state.pending_upload_kind = None
                    for key in ["up_pdf", "up_img", "up_text", "up_any"]:
                        if key in st.session_state:
                            st.session_state[key] = None
                    st.rerun()

    with c2:
        active = st.session_state.pdf_nome or st.session_state.image_nome
        if active:
            st.markdown(f'<span class="attach-pill">Ativo: {html.escape(active)}</span>', unsafe_allow_html=True)
        if st.session_state.pending_upload_label:
            st.markdown(f'<span class="attach-pill">Selecionado: {html.escape(st.session_state.pending_upload_label)}</span>', unsafe_allow_html=True)
        if st.button("Limpar anexo ativo", use_container_width=True):
            update_conversation_attachment(st.session_state.current_conversation_id, pdf_path=None, pdf_name=None, image_path=None, image_name=None, attachment_kind=None)
            st.session_state.db_texto_pdf = None
            st.session_state.pdf_nome = None
            st.session_state.image_nome = None
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def render_context_panels():
    cols = st.columns([1.25, 1])
    with cols[0]:
        st.markdown('<div class="panel-card" style="margin-top:14px;">', unsafe_allow_html=True)
        st.markdown("### Como posso te ajudar hoje?")
        if st.session_state.profile == "Aluno":
            st.caption("Exemplos: “explique com LaTeX”, “resuma este PDF”, “me dê 5 questões”, “corrija minha resposta”.")
        else:
            st.caption("Exemplos: “monte um plano de aula”, “crie uma atividade”, “calcule médias”, “use este PDF como base”.")
        mentor = st.session_state.mentor
        chips = ''.join(f'<span class="mentor-chip">{html.escape(x)}</span>' for x in MENTORS[mentor]["quick"])
        st.markdown(chips, unsafe_allow_html=True)
        if st.session_state.last_detected_intent:
            st.markdown(f'<div class="soft-card" style="margin-top:12px;"><b>Leitura do mentor:</b> {html.escape(st.session_state.last_detected_intent)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[1]:
        if st.session_state.mentor == "Química":
            render_periodic_table()
        else:
            st.markdown('<div class="panel-card" style="margin-top:14px;">', unsafe_allow_html=True)
            st.markdown(f"### Painel do mentor de {st.session_state.mentor}")
            st.caption(MENTORS[st.session_state.mentor]["subtitle"])
            st.markdown(f'<div class="soft-card"><b>Dica:</b> {MENTORS[st.session_state.mentor]["description"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


def render_chat():
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=False)

    payload = None
    try:
        payload = st.chat_input("Escreva sua dúvida. O mentor interpreta o pedido automaticamente.")
    except Exception:
        payload = st.text_input("Escreva sua dúvida", key="fallback_prompt")

    if payload and str(payload).strip():
        question = str(payload).strip()
        cid = st.session_state.current_conversation_id
        if st.session_state.contador_perguntas >= MAX_PERGUNTAS_SESSAO:
            st.warning("Você atingiu o limite de perguntas desta sessão.")
            return

        maybe_update_title_from_first_message(cid, question)
        save_message(cid, "user", question)
        st.session_state.chat.append({"role": "user", "content": question})
        st.session_state.contador_perguntas += 1

        conv = get_conversation(cid)
        has_pdf = bool(st.session_state.db_texto_pdf)
        has_image = bool(conv and conv[10])
        intent = infer_intent(question, has_pdf, has_image)
        st.session_state.last_detected_intent = intent

        attachment_hint = None
        attachment_text = None
        if conv:
            if conv[8]:
                attachment_hint = f"Arquivo ativo: {conv[8]}"
            elif conv[10]:
                attachment_hint = f"Imagem ativa: {conv[10]}"
        if st.session_state.db_texto_pdf:
            attachment_text = st.session_state.db_texto_pdf

        system_prompt = mentor_system_prompt(intent)
        user_prompt = build_user_prompt(question, attachment_text, attachment_hint, intent)
        with st.spinner("Pensando..."):
            answer = generate_response(system_prompt, user_prompt)

        save_message(cid, "assistant", answer)
        st.session_state.chat.append({"role": "assistant", "content": answer})
        st.rerun()


# =========================================================
# APP FLOW
# =========================================================
if not st.session_state.auth_complete:
    render_login_screen()
    st.stop()

ensure_current_conversation()
render_sidebar()
render_main_header()
render_mentor_switcher()
render_attachment_bar()
render_context_panels()
render_chat()

st.caption(f"{APP_NAME} • {PROJECT_NAME} • {INSTITUTION_NAME} • {COURSE_NAME}")
