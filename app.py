import os
import re
import html
import math
import uuid
import base64
import hashlib
import sqlite3
from datetime import datetime
from typing import Optional, Tuple, Dict, List

import streamlit as st
from groq import Groq
from pypdf import PdfReader
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, Arc

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

# =========================================================
# MENTORES
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
- se o aluno acertou por um método longo, reconheça isso e mostre um caminho mais enxuto
Se o pedido envolver visual, use o recurso visual do app como apoio.
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
- quando houver gráfico, conecte a expressão ao comportamento visual
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
- exemplos curtos e claros
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

    [data-testid="stSidebar"] * { color: var(--text) !important; }

    .hero-card, .panel-card, .login-card, .mentor-card, .soft-card, .periodic-card, .top-mini-card {
        background: var(--card) !important;
        border: 1px solid var(--line) !important;
        border-radius: 22px !important;
        box-shadow: var(--shadow) !important;
    }

    .hero-card, .panel-card, .periodic-card, .top-mini-card { padding: 16px 18px !important; }
    .login-card { padding: 22px !important; max-width: 1120px !important; margin: 0 auto 18px auto !important; }
    .mentor-card { padding: 16px !important; min-height: 180px !important; display: flex !important; flex-direction: column !important; justify-content: space-between !important; }
    .soft-card { padding: 14px 16px !important; border-radius: 18px !important; }

    .project-badge {
        display: inline-block; padding: 6px 12px; border-radius: 999px; border: 1px solid var(--line);
        background: var(--accent-soft); color: #5e4e40 !important; font-weight: 800; font-size: .9rem; margin-bottom: 10px;
    }

    .title-main { font-size: 1.9rem; line-height: 1.05; font-weight: 900; color: #564538 !important; margin-bottom: 4px; }
    .inst-big { font-size: 1.15rem; font-weight: 900; color: #524236 !important; }
    .inst-sub, .muted, .small-clean { color: var(--muted) !important; }
    .mentor-emoji { font-size: 1.7rem; margin-bottom: 8px; }
    .mentor-title { font-size: 1.04rem; font-weight: 900; color: #564538 !important; }
    .mentor-sub { color: var(--muted) !important; font-size: .92rem; margin-top: 4px; margin-bottom: 8px; }

    .brand-box img, .logo-center img { display: block; margin: 0 auto 10px auto; max-width: 180px; width: 100%; }
    .brand-title { font-size: 1rem; font-weight: 900; line-height: 1.05; color: #564538 !important; text-align: center; }
    .brand-sub { text-align: center; color: var(--muted) !important; font-size: .9rem; }

    .account-box {
        background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 12px; margin-bottom: 8px;
    }
    .account-name { font-weight: 900; color: #4f4034 !important; }
    .account-sub { color: var(--muted) !important; font-size: .88rem; }

    .stButton > button,
    div[data-testid="baseButton-secondary"] > button,
    div[data-testid="baseButton-primary"] > button {
        background: var(--accent) !important; color: #fffaf4 !important; border: 1px solid var(--accent) !important;
        border-radius: 14px !important; min-height: 40px !important; box-shadow: none !important;
    }
    .stButton > button:hover,
    div[data-testid="baseButton-secondary"] > button:hover,
    div[data-testid="baseButton-primary"] > button:hover {
        background: var(--accent-2) !important; border-color: var(--accent-2) !important;
    }

    .stSelectbox div[data-baseweb="select"] > div,
    .stTextInput input, .stTextArea textarea, .stFileUploader section,
    [data-baseweb="input"] > div, [data-baseweb="base-input"] > div,
    .stRadio > div, .stSegmentedControl {
        background: var(--card-2) !important; color: var(--text) !important; border-color: var(--line) !important;
    }

    [data-testid="stChatInputContainer"], [data-testid="stBottomBlockContainer"],
    [data-testid="stChatInput"], [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] textarea {
        background: var(--bg) !important; color: var(--text) !important; border-color: var(--line) !important; box-shadow: none !important;
    }
    [data-testid="stChatInput"] textarea {
        background: var(--card-2) !important; border: 1px solid var(--line) !important; border-radius: 16px !important;
    }

    [data-testid="stChatMessageContent"] {
        color: var(--text) !important; background: var(--card) !important; border: 1px solid var(--line) !important;
        border-radius: 16px !important; padding: .72rem .86rem !important;
    }

    .attach-note {
        margin-top: 8px; padding: 10px 12px; border: 1px dashed var(--line); border-radius: 14px;
        background: #fbf5ed; color: var(--muted) !important;
    }

    .mode-chip {
        display: inline-block; padding: 6px 10px; border-radius: 999px; background: #f0e4d5; border: 1px solid var(--line);
        font-size: .85rem; font-weight: 800; color: #5e4d40 !important;
    }

    .periodic-wrap { overflow-x: auto; }
    table.periodic { width: 100%; border-collapse: separate; border-spacing: 4px; }
    table.periodic td {
        min-width: 40px; height: 42px; text-align: center; font-weight: 800; border-radius: 10px;
        border: 1px solid var(--line); background: #f8efe4; color: #5a483b; font-size: .88rem;
    }
    table.periodic td.empty { background: transparent !important; border: none !important; }

    .series-row { display: grid; grid-template-columns: repeat(15, 1fr); gap: 4px; margin-top: 6px; }
    .series-cell {
        text-align: center; padding: 8px 3px; border-radius: 10px; border: 1px solid var(--line);
        background: #f8efe4; font-weight: 800; color: #5a483b;
    }

    .mini-title { font-weight: 900; color: #544236 !important; margin-bottom: 4px; }
    .mini-desc { color: var(--muted) !important; font-size: .9rem; }

    .stMarkdown p, .stCaption, label, span, div { color: var(--text) !important; }
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
        "last_summary_offer": False,
        "contador_perguntas": 0,
        "rename_target": None,
        "teacher_answer_key": "",
        "teacher_rubric": "",
        "teacher_points": "",
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


def save_plot(fig, prefix: str) -> str:
    path = os.path.join(UPLOAD_DIR, f"{prefix}_{uuid.uuid4().hex}.png")
    fig.savefig(path, bbox_inches="tight", dpi=180)
    plt.close(fig)
    return path


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
            build_user_key(), title, now, now, st.session_state.profile,
            st.session_state.nickname, mentor, st.session_state.last_detected_mode,
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


def rename_conversation(cid: int, new_title: str):
    new_title = re.sub(r"\s+", " ", (new_title or "").strip())
    if not new_title:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ? AND user_key = ?",
        (new_title[:72], now_iso(), cid, build_user_key()),
    )
    conn.commit()
    conn.close()


def rename_first_message_title(cid: int, text: str):
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT title FROM conversations WHERE id = ? AND user_key = ?", (cid, build_user_key()))
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


def update_conversation_mentor(cid: int, mentor: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE conversations SET mentor = ?, updated_at = ? WHERE id = ? AND user_key = ?",
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
    st.session_state.last_summary_offer = False
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
        _id, _title, _created_at, _updated_at, profile, nickname, mentor, last_mode,
        attachment_path, attachment_name, attachment_type, _user_key,
    ) = conv

    st.session_state.profile = profile or st.session_state.profile
    st.session_state.nickname = nickname or st.session_state.nickname
    st.session_state.mentor = mentor or st.session_state.mentor
    st.session_state.last_detected_mode = last_mode or "Livre"
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
                chunks.append(re.sub(r"\s+", " ", txt))
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
# VISUAIS
# =========================================================
def generate_trig_plot() -> str:
    xs_deg = list(range(0, 361))
    xs = [math.radians(v) for v in xs_deg]
    sen = [math.sin(v) for v in xs]
    cos = [math.cos(v) for v in xs]
    tan = []
    for v in xs:
        c = math.cos(v)
        if abs(c) < 0.08:
            tan.append(None)
        else:
            t = math.tan(v)
            tan.append(t if -5 <= t <= 5 else None)

    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=170)
    ax.plot(xs_deg, sen, label="sen(x)")
    ax.plot(xs_deg, cos, label="cos(x)")

    seg_x, seg_y = [], []
    for x, y in zip(xs_deg, tan):
        if y is None:
            if seg_x:
                ax.plot(seg_x, seg_y, label="tan(x)" if "tan_added" not in locals() else None)
                tan_added = True
                seg_x, seg_y = [], []
        else:
            seg_x.append(x)
            seg_y.append(y)
    if seg_x:
        ax.plot(seg_x, seg_y, label="tan(x)" if "tan_added" not in locals() else None)

    ax.axhline(0)
    ax.axvline(0)
    ax.set_xlim(0, 360)
    ax.set_ylim(-5, 5)
    ax.set_xlabel("Ângulo (graus)")
    ax.set_ylabel("Valor")
    ax.set_title("Funções trigonométricas")
    ax.legend()
    ax.grid(True, alpha=0.25)
    return save_plot(fig, "trig")


def safe_eval_expression(expr: str, x: float) -> float:
    expr = expr.strip().lower()
    expr = expr.replace("^", "**")
    expr = expr.replace("sen", "sin")
    allowed = {
        "x": x,
        "pi": math.pi,
        "e": math.e,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "sqrt": math.sqrt,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "abs": abs,
    }
    return eval(expr, {"__builtins__": {}}, allowed)


def extract_expression(text: str) -> Optional[str]:
    patterns = [
        r"y\s*=\s*([^\n]+)",
        r"f\(x\)\s*=\s*([^\n]+)",
        r"gr[aá]fico de\s+([^\n]+)",
        r"gr[aá]fico da fun[cç][aã]o\s+([^\n]+)",
    ]
    lower = text.lower()
    for p in patterns:
        m = re.search(p, lower)
        if m:
            expr = m.group(1).strip().strip(".")
            expr = expr.split(" com ")[0].split(" no plano ")[0]
            return expr
    return None


def generate_function_plot(expr: str, x_min: float = -10, x_max: float = 10) -> str:
    xs = [x_min + (x_max - x_min) * i / 399 for i in range(400)]
    ys = []
    for x in xs:
        try:
            y = safe_eval_expression(expr, x)
            if isinstance(y, complex) or abs(y) > 1e4:
                ys.append(None)
            else:
                ys.append(float(y))
        except Exception:
            ys.append(None)

    fig, ax = plt.subplots(figsize=(8, 5), dpi=170)
    seg_x, seg_y = [], []
    started = False
    for x, y in zip(xs, ys):
        if y is None or math.isnan(y):
            if seg_x:
                ax.plot(seg_x, seg_y, label=f"y = {expr}" if not started else None)
                started = True
                seg_x, seg_y = [], []
        else:
            seg_x.append(x)
            seg_y.append(y)
    if seg_x:
        ax.plot(seg_x, seg_y, label=f"y = {expr}" if not started else None)

    ax.axhline(0)
    ax.axvline(0)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(f"Gráfico de y = {expr}")
    ax.grid(True, alpha=0.25)
    ax.legend()
    return save_plot(fig, "func")


def generate_mru_plot() -> str:
    t = [i for i in range(0, 11)]
    s = [4 + 3 * i for i in t]
    v = [3 for _ in t]
    fig, ax = plt.subplots(figsize=(8.4, 4.6), dpi=170)
    ax.plot(t, s, label="posição s(t) = 4 + 3t")
    ax.plot(t, v, label="velocidade v(t) = 3")
    ax.axhline(0)
    ax.axvline(0)
    ax.set_xlabel("tempo")
    ax.set_ylabel("valor")
    ax.set_title("Exemplo de MRU")
    ax.grid(True, alpha=0.25)
    ax.legend()
    return save_plot(fig, "mru")


def generate_mruv_plot() -> str:
    t = [i * 0.5 for i in range(0, 21)]
    s = [2 + 2 * x + 0.5 * 1.5 * x * x for x in t]
    v = [2 + 1.5 * x for x in t]
    a = [1.5 for _ in t]
    fig, ax = plt.subplots(figsize=(8.8, 4.8), dpi=170)
    ax.plot(t, s, label="s(t) = 2 + 2t + 0,75t²")
    ax.plot(t, v, label="v(t) = 2 + 1,5t")
    ax.plot(t, a, label="a(t) = 1,5")
    ax.axhline(0)
    ax.axvline(0)
    ax.set_xlabel("tempo")
    ax.set_ylabel("valor")
    ax.set_title("Exemplo de MRUV")
    ax.grid(True, alpha=0.25)
    ax.legend()
    return save_plot(fig, "mruv")


def generate_projectile_diagram() -> str:
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=170)
    xs = [i / 10 for i in range(0, 81)]
    ys = [0.7 * x - 0.05 * x * x for x in xs]
    ys = [y if y >= 0 else None for y in ys]
    valid = [(x, y) for x, y in zip(xs, ys) if y is not None]
    ax.plot([p[0] for p in valid], [p[1] for p in valid])
    ax.arrow(0, 0, 1.2, 0.84, head_width=0.14, length_includes_head=True)
    ax.text(1.25, 0.88, "v₀")
    ax.add_patch(Arc((0, 0), 1.6, 1.2, theta1=0, theta2=35))
    ax.text(0.58, 0.18, "θ")
    ax.axhline(0)
    ax.axvline(0)
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 3)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Lançamento oblíquo")
    ax.grid(True, alpha=0.25)
    return save_plot(fig, "proj")


def generate_forces_diagram() -> str:
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=170)
    ax.add_patch(Rectangle((3.4, 1.8), 1.2, 0.8, fill=False))
    ax.plot([0.8, 7.5], [1.6, 1.6])
    ax.arrow(4.0, 2.6, 0, 1.1, head_width=0.12, length_includes_head=True)
    ax.text(4.08, 3.65, "N")
    ax.arrow(4.0, 1.8, 0, -1.1, head_width=0.12, length_includes_head=True)
    ax.text(4.1, 0.55, "P")
    ax.arrow(4.6, 2.2, 1.3, 0, head_width=0.12, length_includes_head=True)
    ax.text(5.95, 2.3, "F")
    ax.arrow(3.4, 2.2, -1.0, 0, head_width=0.12, length_includes_head=True)
    ax.text(2.1, 2.3, "atrito")
    ax.set_xlim(0.5, 7.8)
    ax.set_ylim(0.2, 4.3)
    ax.set_title("Diagrama de forças em bloco")
    ax.axis("off")
    return save_plot(fig, "forces")


def generate_linus_pauling_diagram() -> str:
    fig, ax = plt.subplots(figsize=(10, 7), dpi=180)
    fig.patch.set_facecolor("#f7f1e8")
    ax.set_facecolor("#fffaf3")
    ax.axis("off")
    levels = [["1s"], ["2s", "2p"], ["3s", "3p", "3d"], ["4s", "4p", "4d", "4f"], ["5s", "5p", "5d", "5f"], ["6s", "6p", "6d"], ["7s", "7p"]]
    xs = [1, 3, 5, 7]
    ys = list(range(len(levels), 0, -1))
    for row_idx, subs in enumerate(levels):
        y = ys[row_idx]
        for col_idx, sub in enumerate(subs):
            x = xs[min(col_idx, len(xs)-1)]
            ax.text(x, y, sub, ha="center", va="center", fontsize=16, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.35", facecolor="#f3e8da", edgecolor="#d8c6b4"))
    arrows = [((7.7, 7.3), (0.8, 6.2)), ((7.7, 6.3), (0.8, 5.2)), ((7.7, 5.3), (0.8, 4.2)), ((7.7, 4.3), (0.8, 3.2)), ((7.7, 3.3), (0.8, 2.2)), ((5.7, 2.3), (0.8, 1.2))]
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="->", mutation_scale=18, linewidth=2.2, color="#8c7764"))
    ax.text(4.1, 8.0, "Diagrama de Linus Pauling", ha="center", fontsize=19, fontweight="bold")
    ax.text(4.1, 0.35, "Ordem de preenchimento: 1s → 2s → 2p → 3s → 3p → 4s ...", ha="center", fontsize=12)
    ax.set_xlim(0, 8.5)
    ax.set_ylim(0, 8.5)
    return save_plot(fig, "linus")

# =========================================================
# INTENÇÃO / SUMÁRIO / GERAÇÃO
# =========================================================
def detect_intent(text: str) -> str:
    t = (text or "").lower()
    if "linus pauling" in t or "diagrama de linus" in t:
        return "linus"
    if "tabela periódica" in t or "tabela periodica" in t:
        return "tabela_periodica"
    if any(k in t for k in ["corrigir prova", "corrija a prova", "corrigir questão", "corrigir questao", "gabarito", "rubrica", "corrija essa", "corrige essa"]):
        return "correcao"
    if any(k in t for k in ["analise minha resolução", "analise minha resolucao", "onde compliquei", "onde eu errei", "meu método", "meu metodo", "veja minha resolução", "veja minha resolucao"]):
        return "analise_resolucao"
    if any(k in t for k in ["resumão", "resumao", "resuma", "resumo", "revise tudo", "resuma essa conversa"]):
        return "resumo"
    if any(k in t for k in ["plano de aula", "sequência didática", "sequencia didatica", "monte uma aula"]):
        return "plano_aula"
    if any(k in t for k in ["gere questões", "gere questoes", "crie questões", "crie questoes", "lista de exercícios", "lista de exercicios", "simulado", "monte questões", "monte questoes"]):
        return "lista_exercicios"
    if any(k in t for k in ["exemplo", "exemplos", "demonstre", "demonstra", "mostre um exemplo"]):
        return "exemplos"
    if any(k in t for k in ["gráfico", "grafico", "plote", "plota", "plano cartesiano", "trajetória", "trajetoria", "vetor", "forças", "forcas", "lancamento", "lançamento"]):
        return "visual"
    if any(k in t for k in ["questão", "questao", "resolver", "resolva"]):
        return "resolver"
    return "explicacao"


def detect_mode_label(intent: str) -> str:
    mapping = {
        "correcao": "Correção",
        "analise_resolucao": "Análise de resolução",
        "resumo": "Resumo",
        "plano_aula": "Plano de aula",
        "lista_exercicios": "Geração de questões",
        "exemplos": "Geração de exemplos",
        "resolver": "Resolução",
        "explicacao": "Explicação",
        "visual": "Interpretação visual",
        "linus": "Diagrama",
        "tabela_periodica": "Consulta",
    }
    return mapping.get(intent, "Livre")


def offer_summary_if_conversation_long() -> bool:
    if len(st.session_state.chat) >= 6 and not st.session_state.last_summary_offer:
        st.session_state.last_summary_offer = True
        return True
    return False


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
        "explicacao": "Explique como um mentor muito bom: ideia central, desenvolvimento, exemplo concreto e significado físico/matemático.",
        "resolver": "Resolva com clareza: dados, pedido, raciocínio, resolução e, no final, caminho mais curto se houver.",
        "analise_resolucao": "Analise a resolução: correto/parcial/incorreto, eficiência do método, onde complicou e caminho melhor.",
        "correcao": "Atue como assistente de correção: compare com gabarito quando houver, sugira pontuação e feedback curto.",
        "resumo": "Faça um resumão útil para revisão: conceitos, fórmulas, erros comuns e revisão final.",
        "plano_aula": "Monte planejamento didático: objetivo, conteúdo, abordagem, atividade, avaliação e observações.",
        "lista_exercicios": "Gere questões organizadas por nível e, quando útil, inclua gabarito.",
        "exemplos": "Gere exemplos claros, progressivos e, se fizer sentido, conectados ao cotidiano.",
        "visual": "A imagem ou o recurso visual serve para apoiar entendimento; conecte a explicação ao visual gerado.",
    }
    return prompts.get(intent, prompts["explicacao"])


def system_prompt(profile: str, mentor: str, intent: str) -> str:
    return clean_text(f"""
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
- Se o aluno acertou por método longo, reconheça isso e mostre um método mais eficiente.
- Não invente detalhes visuais não visíveis.
- Em correção, trate sua saída como sugestão de correção assistida.
- Evite respostas genéricas.

Prompt do mentor:
{MENTORS[mentor]['prompt']}

Prompt do perfil:
{build_profile_prompt(profile)}

Prompt da tarefa:
{build_task_prompt(intent)}
""")


def build_teacher_context() -> str:
    parts = []
    if st.session_state.profile == "Professor":
        if st.session_state.teacher_answer_key.strip():
            parts.append("Gabarito informado pelo professor:\n" + st.session_state.teacher_answer_key.strip())
        if st.session_state.teacher_rubric.strip():
            parts.append("Critérios/rubrica informados:\n" + st.session_state.teacher_rubric.strip())
        if st.session_state.teacher_points.strip():
            parts.append("Pontuação/observações do professor:\n" + st.session_state.teacher_points.strip())
    return "\n\n".join(parts)


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
    teacher_ctx = build_teacher_context()
    if teacher_ctx:
        parts.append(teacher_ctx)
    if st.session_state.attachment_text:
        parts.append("Contexto do anexo textual/PDF:\n" + st.session_state.attachment_text[:PDF_CONTEXT_LIMIT])
    if st.session_state.attachment_name and st.session_state.attachment_type == "image":
        parts.append("Há uma imagem anexada nesta conversa. Se a imagem estiver disponível no fluxo visual, ela deve ser analisada junto com o pedido.")
    parts.append("Pedido atual:\n" + text.strip())
    return "\n\n".join(parts)

# =========================================================
# MODELOS
# =========================================================
def ask_text_model(user_text: str) -> str:
    if client is None:
        return client_error or "Não foi possível iniciar a IA."
    intent = detect_intent(user_text)
    try:
        resp = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt(st.session_state.profile, st.session_state.mentor, intent)},
                {"role": "user", "content": build_user_prompt(user_text)},
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
                {"role": "system", "content": system_prompt(st.session_state.profile, st.session_state.mentor, intent)},
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

# =========================================================
# HANDLERS
# =========================================================
def handle_visual_request(user_text: str) -> Optional[str]:
    t = user_text.lower()
    if any(k in t for k in ["seno", "cosseno", "tangente", "sen(", "cos(", "tan("]):
        st.session_state.last_generated_image = generate_trig_plot()
        return "Gerei um gráfico real de seno, cosseno e tangente para apoiar a explicação. Agora posso interpretar o comportamento de cada curva também."
    if any(k in t for k in ["mruv", "movimento uniformemente variado", "movimento uniformemente acelerado"]):
        st.session_state.last_generated_image = generate_mruv_plot()
        return "Gerei um gráfico real de MRUV com posição, velocidade e aceleração para apoiar a explicação."
    if any(k in t for k in ["mru", "movimento uniforme"]):
        st.session_state.last_generated_image = generate_mru_plot()
        return "Gerei um gráfico real de MRU para apoiar a explicação."
    if any(k in t for k in ["lançamento oblíquo", "lancamento obliquo", "trajetória", "trajetoria parabólica"]):
        st.session_state.last_generated_image = generate_projectile_diagram()
        return "Gerei uma trajetória de lançamento oblíquo para apoiar o entendimento visual."
    if any(k in t for k in ["forças", "forcas", "plano inclinado", "bloco", "diagrama de forças", "diagrama de forcas"]):
        st.session_state.last_generated_image = generate_forces_diagram()
        return "Gerei um diagrama simples de forças para apoiar a explicação."
    expr = extract_expression(user_text)
    if expr:
        try:
            st.session_state.last_generated_image = generate_function_plot(expr)
            return f"Gerei o gráfico real de $y={expr}$ para apoiar a explicação."
        except Exception:
            return None
    return None


def handle_generation_request(user_text: str) -> Optional[str]:
    intent = detect_intent(user_text)
    if intent in {"lista_exercicios", "exemplos", "plano_aula", "resumo", "analise_resolucao", "correcao", "resolver", "explicacao"}:
        return ask_text_model(user_text)
    return None


def generate_conversation_summary() -> str:
    if client is None:
        return client_error or "Não foi possível iniciar a IA."
    if not st.session_state.chat:
        return "Ainda não há conversa suficiente para resumir."
    history = chat_history_text(st.session_state.chat, limit=50)
    prompt = f"""
Resuma a conversa abaixo para estudo.
Formato desejado:
1. O que vimos
2. Ideias-chave
3. Fórmulas ou relações importantes
4. Onde costuma errar
5. Revisão final em poucas linhas

Conversa:
{history}
"""
    try:
        resp = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt(st.session_state.profile, st.session_state.mentor, "resumo")},
                {"role": "user", "content": prompt},
            ],
            temperature=0.25,
            max_tokens=1300,
        )
        return clean_text((resp.choices[0].message.content or "").strip())
    except Exception as e:
        return f"Ocorreu um erro ao gerar o resumão: {e}"


def answer_user(user_text: str) -> str:
    intent = detect_intent(user_text)
    if intent == "linus":
        st.session_state.last_generated_image = generate_linus_pauling_diagram()
        return "Gerei um diagrama de Linus Pauling para apoio visual. Se quiser, também posso aplicá-lo a um elemento específico."
    if intent == "tabela_periodica":
        return "A tabela periódica rápida está exibida acima para consulta. Se quiser, também posso comentar famílias, períodos e propriedades."
    if intent == "visual":
        visual_answer = handle_visual_request(user_text)
        if visual_answer:
            return visual_answer
    if st.session_state.attachment_type == "image" and st.session_state.attachment_preview_path:
        return ask_vision_model(user_text, st.session_state.attachment_preview_path)
    return handle_generation_request(user_text) or ask_text_model(user_text)

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
    st.markdown('<div class="muted">Agora o mentor decide automaticamente se vai explicar, resolver, corrigir, gerar exemplos, questões, gráficos e resumão.</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1.4, 1])
    with col1:
        nickname = st.text_input("Como você quer ser chamado?", value=st.session_state.nickname, placeholder="Ex.: Iago, Professor João, Maria...")
        role = st.radio("Escolha o perfil", ["Aluno", "Professor"], horizontal=True)
    with col2:
        preview_name = get_first_name(nickname)
        st.markdown(
            f"""
            <div class="soft-card">
                <div class="mini-title">Prévia</div>
                <div class="mini-desc">Nome: <b>{html.escape(preview_name)}</b></div>
                <div class="mini-desc">Perfil: <b>{html.escape(role)}</b></div>
                <div class="mini-desc">A IA adapta o tom e decide sozinha se vai explicar, corrigir, gerar questões, exemplos ou resumão.</div>
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

    new_mentor = st.selectbox("Trocar mentor", list(MENTORS.keys()), index=list(MENTORS.keys()).index(st.session_state.mentor))
    if new_mentor != st.session_state.mentor:
        st.session_state.mentor = new_mentor
        update_conversation_mentor(st.session_state.current_conversation_id, new_mentor)

    if st.button("Nova conversa", use_container_width=True):
        reset_visual_state(clear_file=True)
        cid = create_conversation(mentor=st.session_state.mentor)
        st.session_state.current_conversation_id = cid
        load_conversation_into_state(cid)
        st.rerun()

    st.markdown("### Conversas")
    for row in list_conversations():
        cid, title, _upd, mentor, _att, _mode = row
        cols = st.columns([6, 1], vertical_alignment="center")
        with cols[0]:
            label = f"{title} • {mentor}"
            if st.button(label, key=f"open_{cid}", use_container_width=True):
                load_conversation_into_state(cid)
                st.rerun()
        with cols[1]:
            with st.popover("⋯"):
                if st.button("Renomear", key=f"rename_btn_{cid}", use_container_width=True):
                    st.session_state.rename_target = cid
                if st.button("Excluir", key=f"delete_btn_{cid}", use_container_width=True):
                    delete_conversation(cid)
                    remaining = list_conversations()
                    if remaining:
                        st.session_state.current_conversation_id = remaining[0][0]
                        load_conversation_into_state(remaining[0][0])
                    else:
                        reset_visual_state(clear_file=True)
                        new_cid = create_conversation(mentor=st.session_state.mentor)
                        st.session_state.current_conversation_id = new_cid
                        load_conversation_into_state(new_cid)
                    st.rerun()

    if st.session_state.rename_target is not None:
        target = st.session_state.rename_target
        current_title = next((r[1] for r in list_conversations() if r[0] == target), "")
        with st.popover("Renomear conversa aberta"):
            new_title = st.text_input("Novo nome", value=current_title, key="rename_input_global")
            if st.button("Salvar nome", use_container_width=True):
                rename_conversation(target, new_title)
                st.session_state.rename_target = None
                st.rerun()

    if st.session_state.profile == "Professor":
        st.markdown("### Correção assistida")
        st.session_state.teacher_answer_key = st.text_area("Gabarito opcional", value=st.session_state.teacher_answer_key, height=100, placeholder="Ex.: 1) B\n2) 12 m/s\n3) usar 2ª lei de Newton...")
        st.session_state.teacher_rubric = st.text_area("Critérios/rubrica opcionais", value=st.session_state.teacher_rubric, height=100, placeholder="Ex.: conceito 0,4; desenvolvimento 0,3; unidade 0,3")
        st.session_state.teacher_points = st.text_area("Pontuação/observações", value=st.session_state.teacher_points, height=80, placeholder="Ex.: cada questão vale 1,0")

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
    if st.session_state.attachment_type == "image" and st.session_state.attachment_preview_path and os.path.exists(st.session_state.attachment_preview_path):
        st.image(st.session_state.attachment_preview_path, caption=st.session_state.attachment_name, use_container_width=True)

# =========================================================
# CHAT HISTORY
# =========================================================
for msg in st.session_state.chat:
    avatar = avatar_if()
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"], unsafe_allow_html=False)

if st.session_state.last_generated_image and os.path.exists(st.session_state.last_generated_image):
    st.image(st.session_state.last_generated_image, caption="Imagem gerada para apoio visual", use_container_width=True)

# =========================================================
# TOOLS PANEL
# =========================================================
st.markdown('<div class="panel-card" style="margin-top:12px;">', unsafe_allow_html=True)
t1, t2, t3 = st.columns([1.2, 1.2, 3])
with t1:
    if st.button("Gerar resumão", use_container_width=True):
        summary = generate_conversation_summary()
        st.session_state.last_detected_mode = "Resumo"
        save_message(st.session_state.current_conversation_id, "assistant", summary)
        st.session_state.chat.append({"role": "assistant", "content": summary})
        st.rerun()
with t2:
    with st.popover("Anexar arquivo"):
        upload = st.file_uploader("Envie PDF, imagem ou TXT", type=["pdf", "png", "jpg", "jpeg", "webp", "txt"], label_visibility="collapsed", key="chat_attachment_pop")
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
        if st.button("Limpar anexo", use_container_width=True):
            update_attachment(st.session_state.current_conversation_id, None, None, None)
            st.session_state.attachment_text = None
            st.session_state.attachment_name = None
            st.session_state.attachment_type = None
            st.session_state.attachment_preview_path = None
            st.rerun()
with t3:
    st.markdown('<div class="mini-desc" style="margin-top:8px;">Pergunte normalmente: explique, resolva, gere questões, crie exemplos, plote gráfico, mostre trajetória, corrija prova ou gere um resumão.</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# CHAT INPUT
# =========================================================
user_prompt = st.chat_input("Pergunte normalmente: explique, resolva, corrija, gere questões, crie exemplos, plote gráficos, mostre trajetórias ou faça um resumão...")
if user_prompt and user_prompt.strip():
    if st.session_state.contador_perguntas >= MAX_PERGUNTAS_SESSAO:
        st.warning("Você atingiu o limite de perguntas desta sessão.")
    else:
        question = user_prompt.strip()
        cid = st.session_state.current_conversation_id
        intent = detect_intent(question)
        st.session_state.last_detected_mode = detect_mode_label(intent)
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

if offer_summary_if_conversation_long():
    st.info("Essa conversa já está ficando rica. Use o botão **Gerar resumão** para transformar tudo em revisão rápida.")

st.caption(f"{APP_NAME} • {INSTITUTION_NAME} • {COURSE_NAME}")
