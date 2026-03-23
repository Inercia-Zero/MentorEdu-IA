import os
import re
import uuid
import html
import hashlib
import sqlite3
from io import BytesIO
from datetime import datetime
from typing import Optional, Tuple, Dict, List

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
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
MAX_FILE_MB = 10
MAX_PERGUNTAS_SESSAO = 40
PDF_CONTEXT_LIMIT = 8000
CHAT_HISTORY_LIMIT = 8

os.makedirs(UPLOAD_DIR, exist_ok=True)

MENTORS = {
    "Física": {
        "emoji": "⚛️",
        "title": "Mentor de Física",
        "subtitle": "cinemática, dinâmica, energia, circuitos, gráficos e interpretação física",
        "description": "Explicações guiadas, fórmulas, gráficos, fenômenos físicos e linguagem da Física.",
        "prompt": "Você é um mentor especialista em Física escolar e início da graduação. Priorize interpretação física, gráficos, unidades, significado das fórmulas e erros conceituais comuns.",
    },
    "Matemática": {
        "emoji": "📐",
        "title": "Mentor de Matemática",
        "subtitle": "álgebra, funções, trigonometria, geometria e notação matemática",
        "description": "Passo a passo, raciocínio lógico, LaTeX e resolução bem organizada.",
        "prompt": "Você é um mentor especialista em Matemática. Priorize passo a passo, notação clara, raciocínio lógico, gráficos e organização algébrica.",
    },
    "Química": {
        "emoji": "🧪",
        "title": "Mentor de Química",
        "subtitle": "nomenclatura, estequiometria, tabela periódica, ligações e distribuições eletrônicas",
        "description": "Explicações químicas, nomenclatura, cálculos e consulta visual de Química.",
        "prompt": "Você é um mentor especialista em Química. Priorize nomenclatura, tabela periódica, distribuição eletrônica, estequiometria, cálculos químicos e linguagem própria da Química.",
    },
    "Linguagens": {
        "emoji": "📚",
        "title": "Mentor de Linguagens",
        "subtitle": "português, inglês, leitura, interpretação, gramática e produção textual",
        "description": "Apoio em escrita, correção, explicação gramatical e prática de leitura.",
        "prompt": "Você é um mentor especialista em Linguagens, com foco em Português e Inglês. Priorize clareza, correção textual, interpretação e explicações acessíveis.",
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
        --bg-soft: #f1e8dc;
        --bg-sidebar: #efe3d4;
        --card: #fffaf4;
        --card-2: #faf2e8;
        --line: #d8c6b4;
        --text: #3c3128;
        --muted: #75695e;
        --accent: #8c7764;
        --accent-2: #9b8673;
        --accent-soft: #ede0d1;
        --shadow: 0 12px 28px rgba(81, 62, 44, .08);
    }

    html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"],
    section.main, .main .block-container {
        background: var(--bg) !important;
        color: var(--text) !important;
    }

    .main .block-container {
        max-width: 1180px !important;
        padding-top: 0.9rem !important;
        padding-bottom: 1rem !important;
    }

    header[data-testid="stHeader"] {
        background: var(--bg-soft) !important;
        border-bottom: 1px solid var(--line) !important;
    }

    [data-testid="stToolbar"] { right: 0.5rem !important; }

    [data-testid="stSidebar"] {
        background: var(--bg-sidebar) !important;
        border-right: 1px solid var(--line) !important;
    }

    [data-testid="stSidebar"] * { color: var(--text) !important; }

    .hero-card, .panel-card, .mentor-card, .login-card, .soft-card, .periodic-card {
        background: var(--card) !important;
        border: 1px solid var(--line) !important;
        border-radius: 24px !important;
        box-shadow: var(--shadow) !important;
    }

    .hero-card, .panel-card, .periodic-card { padding: 22px; }
    .login-card { padding: 28px; max-width: 1020px; margin: 10px auto 28px auto; }
    .soft-card { padding: 14px 16px; border-radius: 18px !important; }

    .project-badge {
        display: inline-block;
        background: var(--accent-soft);
        color: #665649 !important;
        border: 1px solid var(--line);
        padding: 7px 12px;
        border-radius: 999px;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .login-top {
        text-align: center;
        margin-bottom: 14px;
    }

    .logo-center img {
        display: block;
        margin: 0 auto 12px auto;
        max-width: 200px;
        width: 100%;
    }

    .inst-big { font-size: 1.28rem; font-weight: 800; color: #59473a !important; }
    .inst-sub { font-size: 1rem; color: var(--muted) !important; margin-top: 4px; }
    .title-main { font-size: 2.1rem; font-weight: 800; color: #5a483b !important; line-height: 1.05; }
    .muted { color: var(--muted) !important; }

    .mentor-card {
        padding: 18px;
        min-height: 210px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .mentor-emoji { font-size: 2rem; margin-bottom: 10px; }
    .mentor-title { font-size: 1.12rem; font-weight: 800; color: #5a483b !important; }
    .mentor-sub { color: var(--muted) !important; font-size: .95rem; margin: 6px 0 10px 0; }

    .brand-box { text-align: center; margin-top: 8px; margin-bottom: 18px; }
    .brand-box img { display:block; margin: 0 auto 10px auto; max-width: 190px; width: 100%; }
    .brand-title { font-size: 1.08rem; font-weight: 800; color: #5a483b !important; line-height: 1.1; }
    .brand-sub { color: var(--muted) !important; font-size: .95rem; }

    .account-box {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 14px;
        margin-bottom: 10px;
    }
    .account-name { font-weight: 800; color: #544236 !important; }
    .account-sub { color: var(--muted) !important; font-size: .9rem; }

    .stButton > button,
    div[data-testid="baseButton-secondary"] > button,
    div[data-testid="baseButton-primary"] > button {
        background: var(--accent) !important;
        color: #fffaf5 !important;
        border: 1px solid var(--accent) !important;
        border-radius: 14px !important;
        min-height: 42px !important;
        box-shadow: none !important;
    }
    .stButton > button:hover,
    div[data-testid="baseButton-secondary"] > button:hover,
    div[data-testid="baseButton-primary"] > button:hover {
        background: var(--accent-2) !important;
        border-color: var(--accent-2) !important;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stFileUploader,
    .stFileUploader section,
    .stSelectbox div[data-baseweb="select"] > div,
    .stPopover button,
    .stSegmentedControl,
    .stRadio > div,
    [data-baseweb="input"] > div,
    [data-baseweb="base-input"] > div {
        background: var(--card-2) !important;
        color: var(--text) !important;
        border-color: var(--line) !important;
    }

    [data-baseweb="popover"], [data-baseweb="popover"] * {
        background: var(--card) !important;
        color: var(--text) !important;
        border-color: var(--line) !important;
    }

    ul[role="listbox"], li[role="option"], div[role="option"] {
        background: var(--card) !important;
        color: var(--text) !important;
    }

    [data-testid="stChatInputContainer"],
    [data-testid="stBottomBlockContainer"],
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] input {
        background: var(--bg) !important;
        color: var(--text) !important;
        border-color: var(--line) !important;
        box-shadow: none !important;
    }

    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] input {
        background: var(--card-2) !important;
        border: 1px solid var(--line) !important;
        border-radius: 16px !important;
    }

    [data-testid="stChatMessageContent"] {
        color: var(--text) !important;
        border: 1px solid var(--line) !important;
        border-radius: 16px !important;
        padding: .7rem .85rem !important;
        background: var(--card) !important;
    }

    .periodic-wrap { overflow-x: auto; }
    table.periodic {
        width: 100%; border-collapse: separate; border-spacing: 5px;
    }
    table.periodic td {
        min-width: 42px; height: 44px; text-align: center; font-weight: 700;
        border-radius: 10px; border: 1px solid var(--line); background: #f8efe4; color: #5a483b;
        font-size: .9rem;
    }
    table.periodic td.empty { background: transparent !important; border: none !important; }
    .series-row { display: grid; grid-template-columns: repeat(15, 1fr); gap: 5px; margin-top: 8px; }
    .series-cell {
        text-align: center; padding: 10px 4px; border-radius: 10px; border: 1px solid var(--line);
        background: #f8efe4; font-weight: 700; color: #5a483b;
    }
    .attach-note {
        margin-top: 10px; padding: 10px 12px; border: 1px dashed var(--line);
        border-radius: 14px; background: #fbf5ed; color: var(--muted) !important;
    }

    .small-clean { font-size: .9rem; color: var(--muted) !important; }
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
    for col, ddl in [
        ("user_key", "ALTER TABLE conversations ADD COLUMN user_key TEXT"),
        ("profile", "ALTER TABLE conversations ADD COLUMN profile TEXT"),
        ("nickname", "ALTER TABLE conversations ADD COLUMN nickname TEXT"),
        ("mentor", "ALTER TABLE conversations ADD COLUMN mentor TEXT"),
        ("attachment_path", "ALTER TABLE conversations ADD COLUMN attachment_path TEXT"),
        ("attachment_name", "ALTER TABLE conversations ADD COLUMN attachment_name TEXT"),
        ("attachment_type", "ALTER TABLE conversations ADD COLUMN attachment_type TEXT"),
    ]:
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
        "chat": [],
        "current_conversation_id": None,
        "loaded_conversation_id": None,
        "attachment_text": None,
        "attachment_name": None,
        "attachment_type": None,
        "attachment_preview_path": None,
        "last_generated_image": None,
        "last_intent": None,
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


def list_conversations() -> List[tuple]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, title, updated_at, mentor, attachment_name
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
               attachment_path, attachment_name, attachment_type, user_key
        FROM conversations WHERE id = ? AND user_key = ?
        """,
        (cid, build_user_key()),
    )
    row = cur.fetchone()
    conn.close()
    return row


def create_conversation(title: str = "Nova conversa", mentor: Optional[str] = None) -> int:
    now = datetime.utcnow().isoformat()
    mentor = mentor or st.session_state.mentor
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO conversations(user_key, title, created_at, updated_at, profile, nickname, mentor)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (build_user_key(), title, now, now, st.session_state.profile, st.session_state.nickname, mentor),
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid


def save_message(cid: int, role: str, content: str):
    now = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (cid, role, content, now),
    )
    cur.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, cid))
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
    cur.execute("SELECT title FROM conversations WHERE id = ? AND user_key = ?", (cid, build_user_key()))
    row = cur.fetchone()
    if row and row[0] == "Nova conversa":
        cur.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ? AND user_key = ?",
            (text[:70], datetime.utcnow().isoformat(), cid, build_user_key()),
        )
        conn.commit()
    conn.close()


def delete_conversation(cid: int):
    conv = get_conversation(cid)
    if conv and conv[7] and os.path.exists(conv[7]):
        try:
            os.remove(conv[7])
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
        (path, name, ftype, datetime.utcnow().isoformat(), cid, build_user_key()),
    )
    conn.commit()
    conn.close()


def update_mentor(cid: int, mentor: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE conversations SET mentor = ?, updated_at = ? WHERE id = ? AND user_key = ?",
        (mentor, datetime.utcnow().isoformat(), cid, build_user_key()),
    )
    conn.commit()
    conn.close()


def reset_visual_state(clear_file=True):
    st.session_state.chat = []
    st.session_state.loaded_conversation_id = None
    st.session_state.last_generated_image = None
    st.session_state.last_intent = None
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
    _, _, _, _, profile, nickname, mentor, attachment_path, attachment_name, attachment_type, _ = conv
    st.session_state.profile = profile or st.session_state.profile
    st.session_state.nickname = nickname or st.session_state.nickname
    st.session_state.mentor = mentor or st.session_state.mentor
    st.session_state.chat = [{"role": r, "content": c} for r, c, _ in get_messages(cid)]
    st.session_state.current_conversation_id = cid
    st.session_state.loaded_conversation_id = cid
    st.session_state.last_generated_image = None
    st.session_state.attachment_name = attachment_name
    st.session_state.attachment_type = attachment_type
    st.session_state.attachment_preview_path = attachment_path if attachment_type == "image" else None
    if attachment_path and os.path.exists(attachment_path) and attachment_type == "pdf":
        st.session_state.attachment_text = extract_pdf_text(attachment_path)
    elif attachment_type == "text" and attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "r", encoding="utf-8") as f:
                st.session_state.attachment_text = f.read()
        except Exception:
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
        text = "\n\n".join(chunks).strip()
        return text or None
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
            <div style="font-weight:800; font-size:1.05rem; margin-bottom:8px; color:#5a483b;">Tabela periódica rápida</div>
            <div class="small-clean" style="margin-bottom:10px;">Consulta visual para o mentor de Química.</div>
            <div class="periodic-wrap">
                <table class="periodic">{''.join(rows_html)}</table>
                <div class="small-clean" style="margin-top:10px;">Lantanídeos</div>
                <div class="series-row">{lan}</div>
                <div class="small-clean" style="margin-top:10px;">Actinídeos</div>
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
    ax.set_facecolor("#fffaf4")
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

    positions = []
    for row_idx, subs in enumerate(levels):
        y = ys[row_idx]
        for col_idx, sub in enumerate(subs):
            x = xs[min(col_idx, len(xs)-1)]
            positions.append((x, y, sub))
            ax.text(
                x, y, sub,
                ha="center", va="center", fontsize=16, fontweight="bold", color="#5a483b",
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
# INTENT / PROMPTS
# =========================================================
def detect_intent(text: str) -> str:
    t = (text or "").lower()
    if "linus pauling" in t or "diagrama de linus" in t:
        return "linus"
    if "tabela periódica" in t or "tabela periodica" in t:
        return "tabela_periodica"
    if any(k in t for k in ["gráfico", "grafico", "diagrama", "esquema visual", "imagem"]):
        return "visual"
    if any(k in t for k in ["resuma", "resumir", "resumo"]) and st.session_state.attachment_text:
        return "resumo"
    if any(k in t for k in ["corrija", "corrigir", "onde eu errei"]):
        return "correcao"
    if any(k in t for k in ["questão", "questao", "exercício", "exercicio", "quiz", "simulado"]):
        return "exercicios"
    return "explicacao"


def chat_history_text(chat: List[Dict[str, str]], limit: int = CHAT_HISTORY_LIMIT) -> str:
    parts = []
    for msg in chat[-limit:]:
        who = "Usuário" if msg["role"] == "user" else "Assistente"
        parts.append(f"{who}: {msg['content'][:700]}")
    return "\n".join(parts)


def system_prompt() -> str:
    mentor = st.session_state.mentor
    profile = st.session_state.profile
    area_prompt = MENTORS[mentor]["prompt"]
    base = f"""
Você é o {APP_NAME}, um mentor acadêmico institucional ligado ao {PROJECT_NAME} do {INSTITUTION_NAME}.
Atenda em português do Brasil.
Perfil atual do usuário: {profile}.
Área atual do mentor: {mentor}.
{area_prompt}
Seja claro, didático, acolhedor e objetivo.
Não peça que o usuário configure funções manualmente.
Quando couber matemática, use LaTeX válido com $...$ e $$...$$.
Quando houver anexo relevante, use esse contexto.
Se a área for Química, trate nomenclaturas e distribuições com mais precisão.
Se a área for Física ou Matemática, trate fórmulas, gráficos e passos com rigor.
Se a área for Linguagens, foque em clareza, escrita e interpretação.
"""
    if profile == "Professor":
        base += "\nComo o usuário está no perfil Professor, também ajude com metodologia, avaliação, planejamento e materiais."
    else:
        base += "\nComo o usuário está no perfil Aluno, priorize compreensão, exemplos e prática guiada."
    return base.strip()


def build_user_prompt(text: str) -> str:
    parts = [
        f"Usuário: {get_first_name(st.session_state.nickname)}",
        f"Mentor escolhido: {st.session_state.mentor}",
        f"Perfil: {st.session_state.profile}",
        f"Intenção provável: {detect_intent(text)}",
    ]
    history = chat_history_text(st.session_state.chat)
    if history:
        parts.append("Histórico recente:\n" + history)
    if st.session_state.attachment_text:
        parts.append("Contexto do anexo:\n" + st.session_state.attachment_text[:PDF_CONTEXT_LIMIT])
    if st.session_state.attachment_name and st.session_state.attachment_type == "image":
        parts.append(f"Imagem anexada: {st.session_state.attachment_name}. Avise quando a resposta depender de leitura visual detalhada.")
    parts.append("Pedido atual:\n" + text.strip())
    return "\n\n".join(parts)


def ask_groq(user_text: str) -> str:
    if client is None:
        return client_error or "Não foi possível iniciar a IA."
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt()},
                {"role": "user", "content": build_user_prompt(user_text)},
            ],
            temperature=0.25,
            max_tokens=1200,
        )
        text = (resp.choices[0].message.content or "").strip()
        return re.sub(r"\n{3,}", "\n\n", text) if text else "Não consegui gerar uma resposta útil."
    except Exception as e:
        return f"Ocorreu um erro ao gerar a resposta: {e}"


# =========================================================
# LOGIN / MENTOR PICKER
# =========================================================
def render_login_screen():
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-top">', unsafe_allow_html=True)
    if os.path.exists(IF_LOGO):
        st.markdown('<div class="logo-center">', unsafe_allow_html=True)
        st.image(IF_LOGO, width=210)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="project-badge">{PROJECT_NAME}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="inst-big">{INSTITUTION_NAME}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="inst-sub">{COURSE_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="title-main">Escolha como quer entrar</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Tema café com leite, mentor especializado e fluxo mais intuitivo.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1.35, 1])
    with col1:
        nickname = st.text_input(
            "Como você quer ser chamado?",
            value=st.session_state.nickname,
            placeholder="Ex.: Iago, Professor João, Maria...",
        )
        role = st.radio("Escolha o perfil", ["Aluno", "Professor"], horizontal=True)
        st.session_state.profile = role
    with col2:
        st.markdown(
            f"""
            <div class="soft-card">
                <div style="font-weight:800; margin-bottom:6px; color:#5a483b;">Prévia</div>
                <div class="small-clean">Nome: <b>{html.escape(get_first_name(nickname))}</b></div>
                <div class="small-clean">Perfil: <b>{html.escape(role)}</b></div>
                <div class="small-clean">Logo e identidade visual centralizadas.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-weight:800; color:#5a483b; margin-bottom:10px;">Escolha seu mentor</div>', unsafe_allow_html=True)

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
        st.image(IF_LOGO, width=190)
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

    selected_mentor = st.selectbox("Trocar mentor", list(MENTORS.keys()), index=list(MENTORS.keys()).index(st.session_state.mentor))
    if selected_mentor != st.session_state.mentor:
        st.session_state.mentor = selected_mentor
        reset_visual_state(clear_file=True)
        cid = create_conversation(mentor=selected_mentor)
        st.session_state.current_conversation_id = cid
        load_conversation_into_state(cid)
        st.rerun()

    conv_rows = list_conversations()
    labels = {f"{row[1]} • {row[3]}": row[0] for row in conv_rows}
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
            cid = create_conversation(mentor=st.session_state.mentor)
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
            cid = create_conversation(mentor=st.session_state.mentor)
            st.session_state.current_conversation_id = cid
            load_conversation_into_state(cid)
        st.rerun()


# =========================================================
# MAIN HEADER
# =========================================================
meta = MENTORS[st.session_state.mentor]
st.markdown(
    f"""
    <div class="hero-card">
        <div class="project-badge">{PROJECT_NAME}</div>
        <div class="title-main">{APP_NAME}</div>
        <div style="font-weight:800; color:#5a483b; margin-top:6px;">{meta['title']}</div>
        <div class="muted" style="margin-top:6px;">{meta['description']}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.mentor == "Química":
    render_periodic_table()

if st.session_state.attachment_name:
    st.markdown(
        f"<div class='attach-note'>Anexo ativo nesta conversa: <b>{html.escape(st.session_state.attachment_name)}</b> ({html.escape(st.session_state.attachment_type or 'arquivo')})</div>",
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
# ATTACHMENT BAR + CHAT INPUT
# =========================================================
st.markdown('<div class="panel-card" style="margin-top:16px;">', unsafe_allow_html=True)
st.markdown('<div style="font-weight:800; color:#5a483b; margin-bottom:8px;">Anexos perto do chat</div>', unsafe_allow_html=True)
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

user_prompt = st.chat_input("Escreva sua dúvida, peça um resumo, gráfico, diagrama ou use um anexo...")

if user_prompt and user_prompt.strip():
    if st.session_state.contador_perguntas >= MAX_PERGUNTAS_SESSAO:
        st.warning("Você atingiu o limite de perguntas desta sessão.")
    else:
        question = user_prompt.strip()
        cid = st.session_state.current_conversation_id
        rename_first_message_title(cid, question)

        save_message(cid, "user", question)
        st.session_state.chat.append({"role": "user", "content": question})
        st.session_state.contador_perguntas += 1
        st.session_state.last_generated_image = None

        intent = detect_intent(question)
        st.session_state.last_intent = intent

        if intent == "linus":
            image_path = build_linus_pauling_diagram()
            st.session_state.last_generated_image = image_path
            answer = (
                "Gerei um diagrama de Linus Pauling para apoio visual.\n\n"
                "Use-o para seguir a ordem de preenchimento dos subníveis. Se quiser, também posso aplicar isso a um elemento específico, "
                "como cálcio, ferro ou cloro, e montar a distribuição eletrônica passo a passo."
            )
        elif intent == "tabela_periodica":
            answer = "A tabela periódica rápida está exibida acima para consulta. Se quiser, também posso classificar elementos, famílias, períodos ou propriedades periódicas."
        else:
            with st.spinner("Pensando..."):
                answer = ask_groq(question)

        save_message(cid, "assistant", answer)
        st.session_state.chat.append({"role": "assistant", "content": answer})
        st.rerun()

st.caption(f"{APP_NAME} • {INSTITUTION_NAME} • {COURSE_NAME}")
