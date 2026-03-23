import os
import re
import uuid
import math
import hashlib
import textwrap
import sqlite3
from datetime import datetime
from typing import Optional, Tuple, Dict, List

import streamlit as st
from pypdf import PdfReader
from groq import Groq
from PIL import Image, ImageDraw, ImageFont


# =========================================================
# CONFIGURAÇÃO GERAL
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

MAX_PDF_MB = 15
MAX_IMG_MB = 8
MAX_PERGUNTAS_SESSAO = 50
PDF_CONTEXT_LIMIT = 8000
CHAT_HISTORY_LIMIT = 6
TEXT_MODEL = "llama-3.3-70b-versatile"

os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================================================
# MENTORES / ÁREAS
# =========================================================
MENTOR_THEMES = {
    "Física": {
        "emoji": "⚛️",
        "desc_student": "cinemática, dinâmica, energia, ondas, circuitos, gráficos e interpretação física.",
        "desc_teacher": "metodologias de ensino, listas, experimentos, avaliações e sequências didáticas de Física.",
        "accent": "#8a7360",
        "soft": "#efe5da",
        "keywords": [
            "mru", "muv", "velocidade", "aceleração", "força", "newton", "energia", "trabalho",
            "calor", "temperatura", "corrente", "tensão", "resistência", "óptica", "optica", "onda",
            "frequência", "frequencia", "campo elétrico", "campo eletrico"
        ],
    },
    "Matemática": {
        "emoji": "📐",
        "desc_student": "equações, funções, geometria, trigonometria, porcentagem e raciocínio matemático.",
        "desc_teacher": "listas, planejamento, resolução comentada, avaliação e apoio a matemática escolar.",
        "accent": "#786a90",
        "soft": "#ece8f7",
        "keywords": [
            "equação", "equacao", "função", "funcao", "derivada", "integral", "log", "matriz",
            "determinante", "seno", "cosseno", "trigonometria", "porcentagem", "polinômio", "polinomio"
        ],
    },
    "Química": {
        "emoji": "🧪",
        "desc_student": "nomenclatura, reações, estequiometria, pH, tabela periódica e cálculos químicos.",
        "desc_teacher": "planejamento, roteiros, nomenclatura, contextualização e apoio ao ensino de Química.",
        "accent": "#6f8163",
        "soft": "#ebf3e5",
        "keywords": [
            "mol", "átomo", "atomo", "ácido", "acido", "base", "pH", "estequiometria", "reação",
            "reacao", "tabela periódica", "tabela periodica", "ligação", "ligacao", "nomenclatura"
        ],
    },
    "Linguagens": {
        "emoji": "📚",
        "desc_student": "português e inglês: interpretação, gramática, leitura, escrita e revisão textual.",
        "desc_teacher": "produção de materiais, avaliação, interpretação, gramática e apoio em Português/Inglês.",
        "accent": "#9b755f",
        "soft": "#f3e7df",
        "keywords": [
            "redação", "redacao", "gramática", "gramatica", "interpretação", "interpretacao", "sujeito",
            "predicado", "oração", "oracao", "inglês", "ingles", "translate", "grammar", "reading"
        ],
    },
}

PROFILE_OPTIONS = ["Aluno", "Professor"]
FILE_OPTIONS = ["PDF", "Imagem"]
IMAGE_EXTS = ["png", "jpg", "jpeg", "webp"]


# =========================================================
# TEMA / CSS
# =========================================================
def current_mentor_theme() -> Dict[str, str]:
    return MENTOR_THEMES.get(st.session_state.get("mentor_area", "Física"), MENTOR_THEMES["Física"])


def gerar_css() -> str:
    theme = current_mentor_theme()
    accent = theme["accent"]
    soft = theme["soft"]

    return f"""
    <style>
        :root {{
            --bg: #f7f3ee;
            --bg-top: #f4ede4;
            --sidebar: #f1e8de;
            --card: #fffdf9;
            --card-2: #faf5ef;
            --line: #dccfc0;
            --text: #3b312a;
            --muted: #7a6d61;
            --accent: {accent};
            --accent-soft: {soft};
            --accent-hover: #6f5e53;
            --badge: #f1e7dc;
            --user-bg: #efe4d7;
            --assistant-bg: #fffaf5;
            --shadow: 0 12px 28px rgba(92, 70, 48, 0.07);
        }}

        html, body, [class*="css"] {{
            color: var(--text) !important;
        }}

        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        section.main {{
            background: var(--bg) !important;
        }}

        .main .block-container {{
            max-width: 1120px !important;
            padding-top: .9rem !important;
            padding-bottom: 1rem !important;
        }}

        header[data-testid="stHeader"] {{
            background: var(--bg-top) !important;
            border-bottom: 1px solid var(--line) !important;
        }}

        [data-testid="stSidebar"] {{
            background: var(--sidebar) !important;
            border-right: 1px solid var(--line) !important;
        }}

        [data-testid="stSidebar"] * {{
            color: var(--text) !important;
        }}

        .hero-card,
        .painel-card,
        .status-card,
        .login-card,
        .choice-card,
        .account-card,
        .mini-soft-card,
        .mentor-card,
        .toolbar-card,
        .quick-card,
        .chem-card {{
            background: var(--card) !important;
            border: 1px solid var(--line) !important;
            border-radius: 24px !important;
            box-shadow: var(--shadow) !important;
        }}

        .login-card {{
            max-width: 920px;
            margin: 20px auto;
            padding: 28px;
        }}

        .hero-card,
        .painel-card,
        .toolbar-card {{
            padding: 22px;
        }}

        .project-badge {{
            display: inline-block;
            background: var(--badge) !important;
            color: #6a5849 !important;
            border: 1px solid #d9c9b6 !important;
            padding: 6px 12px !important;
            border-radius: 999px !important;
            font-size: .88rem !important;
            font-weight: 700 !important;
            margin-bottom: 14px !important;
        }}

        .hero-title {{
            color: #5b473b !important;
            font-size: 2.15rem !important;
            font-weight: 800 !important;
            line-height: 1.05 !important;
            margin-bottom: 6px !important;
        }}

        .hero-subtitle {{
            color: var(--muted) !important;
            font-size: 1rem !important;
            margin-bottom: 0 !important;
        }}

        .institution-title {{
            color: #5a4639 !important;
            font-size: 1.28rem !important;
            font-weight: 800 !important;
            margin-bottom: 2px !important;
        }}

        .course-title {{
            color: #7b6a5c !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
            margin-bottom: 0 !important;
        }}

        .main-title {{
            color: #5b473b !important;
            font-size: 1.8rem !important;
            font-weight: 800 !important;
            line-height: 1.1 !important;
            margin-bottom: 8px !important;
            text-align: center !important;
        }}

        .small-muted {{
            color: var(--muted) !important;
        }}

        .sidebar-logo-top {{
            display: flex;
            justify-content: center;
            margin-bottom: 8px;
            margin-top: 4px;
        }}

        .sidebar-inst {{
            text-align: center;
            margin-bottom: 18px;
        }}

        .sidebar-inst-title {{
            font-size: 1.08rem;
            font-weight: 800;
            color: #5b473b !important;
            line-height: 1.1;
        }}

        .sidebar-inst-sub {{
            color: var(--muted) !important;
            font-size: 0.94rem !important;
        }}

        .account-card {{
            padding: 14px;
            margin-bottom: 12px;
        }}

        .account-user-row {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .account-avatar,
        .name-avatar {{
            width: 52px;
            height: 52px;
            border-radius: 999px;
            background: var(--accent);
            color: white !important;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.15rem;
            font-weight: 800;
            flex-shrink: 0;
        }}

        .account-name {{
            font-weight: 800 !important;
            color: #4f3f34 !important;
            line-height: 1.1;
            margin-bottom: 2px;
        }}

        .account-role {{
            color: var(--muted) !important;
            font-size: 0.88rem !important;
        }}

        .login-center {{
            text-align: center;
            margin-bottom: 14px;
        }}

        .login-logo-wrap {{
            display: flex;
            justify-content: center;
            margin-bottom: 14px;
        }}

        .name-preview {{
            background: var(--card-2);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 14px;
            display: flex;
            align-items: center;
            gap: 14px;
            margin-top: 10px;
            margin-bottom: 14px;
        }}

        .mentor-card {{
            padding: 16px;
            min-height: 152px;
            border: 1px solid var(--line) !important;
        }}

        .mentor-emoji {{
            font-size: 2rem;
            line-height: 1;
            margin-bottom: 8px;
        }}

        .mentor-title {{
            font-size: 1.05rem;
            font-weight: 800;
            color: #5b473b !important;
            margin-bottom: 6px;
        }}

        .mentor-desc {{
            color: var(--muted) !important;
            font-size: .92rem !important;
        }}

        .mini-soft-card {{
            padding: 12px 14px;
            border-radius: 16px !important;
        }}

        .chem-card {{
            padding: 12px 16px;
        }}

        .stButton > button {{
            background: var(--accent) !important;
            color: #fffdfa !important;
            border: 1px solid var(--accent) !important;
            border-radius: 14px !important;
            min-height: 44px !important;
        }}

        .stButton > button:hover {{
            background: #6e5c51 !important;
            border-color: #6e5c51 !important;
        }}

        .stDownloadButton > button,
        .stPopover > button,
        button[kind="secondary"],
        button[kind="tertiary"] {{
            border-radius: 14px !important;
        }}

        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div,
        .stFileUploader,
        .stFileUploader section,
        .stFileUploader div[data-testid="stFileUploaderDropzone"] {{
            background: #fffaf5 !important;
            color: #3b312a !important;
            border: 1px solid #dccfc0 !important;
            border-radius: 14px !important;
        }}

        .stFileUploader small,
        .stFileUploader label,
        .stFileUploader span {{
            color: #6f6257 !important;
        }}

        div[data-baseweb="popover"],
        div[data-baseweb="popover"] * {{
            color: #3b312a !important;
        }}

        div[data-baseweb="popover"] > div,
        [data-baseweb="menu"],
        [data-baseweb="menu"] > div,
        ul[role="listbox"],
        div[role="option"] {{
            background: #fffaf5 !important;
            border: 1px solid #dccfc0 !important;
            border-radius: 14px !important;
            color: #3b312a !important;
            box-shadow: 0 12px 28px rgba(92, 70, 48, 0.10) !important;
        }}

        [data-testid="stBottomBlockContainer"] {{
            background: var(--bg) !important;
            border-top: 1px solid var(--line) !important;
        }}

        [data-testid="stChatInputContainer"],
        [data-testid="stChatInputContainer"] > div,
        [data-testid="stChatInput"],
        [data-testid="stChatInput"] > div,
        section[data-testid="stChatInput"] {{
            background: var(--bg) !important;
            border: none !important;
            box-shadow: none !important;
        }}

        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInput"] input {{
            background: #fffaf5 !important;
            color: #3b312a !important;
            border: 1px solid #dccfc0 !important;
            border-radius: 16px !important;
        }}

        [data-testid="stChatMessageContent"] {{
            color: var(--text) !important;
            border: 1px solid var(--line) !important;
            border-radius: 16px !important;
            padding: .65rem .8rem !important;
        }}

        .stChatMessage:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {{
            background: var(--user-bg) !important;
        }}

        .stChatMessage:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {{
            background: var(--assistant-bg) !important;
        }}

        .conversation-hint {{
            background: var(--accent-soft);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 10px 12px;
            margin-top: 8px;
            color: var(--text) !important;
            font-size: 0.92rem;
        }}

        p, span, label, div, li, h1, h2, h3, h4, small {{
            color: var(--text) !important;
        }}
    </style>
    """


# =========================================================
# BANCO DE DADOS
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
            mentor_area TEXT,
            pdf_path TEXT,
            pdf_name TEXT,
            image_path TEXT,
            image_name TEXT
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
    cols = [row[1] for row in cur.fetchall()]

    migrations = {
        "profile": "ALTER TABLE conversations ADD COLUMN profile TEXT",
        "nickname": "ALTER TABLE conversations ADD COLUMN nickname TEXT",
        "mentor_area": "ALTER TABLE conversations ADD COLUMN mentor_area TEXT",
        "pdf_path": "ALTER TABLE conversations ADD COLUMN pdf_path TEXT",
        "pdf_name": "ALTER TABLE conversations ADD COLUMN pdf_name TEXT",
        "image_path": "ALTER TABLE conversations ADD COLUMN image_path TEXT",
        "image_name": "ALTER TABLE conversations ADD COLUMN image_name TEXT",
        "user_key": "ALTER TABLE conversations ADD COLUMN user_key TEXT",
    }
    for col, sql in migrations.items():
        if col not in cols:
            cur.execute(sql)

    conn.commit()
    conn.close()


# =========================================================
# ESTADO DE SESSÃO
# =========================================================
def init_session_state():
    defaults = {
        "auth_complete": False,
        "profile": "Aluno",
        "nickname": "",
        "mentor_area": "Física",
        "chat": [],
        "db_texto_pdf": None,
        "pdf_nome": None,
        "image_nome": None,
        "current_conversation_id": None,
        "loaded_conversation_id": None,
        "contador_perguntas": 0,
        "ultima_imagem_visual": None,
        "last_detected_intent": None,
        "pending_file_key": str(uuid.uuid4()),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_db()
init_session_state()
st.markdown(gerar_css(), unsafe_allow_html=True)


# =========================================================
# UTILITÁRIOS
# =========================================================
def get_first_name(name: str) -> str:
    txt = (name or "").strip()
    return txt.split()[0] if txt else "Usuário"


def get_logged_email() -> str:
    try:
        if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
            return str(getattr(st.user, "email", "") or "").strip().lower()
    except Exception:
        return ""
    return ""


def build_user_key() -> str:
    email = get_logged_email()
    base = email or f"{st.session_state.profile}|{st.session_state.nickname.strip().lower()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def profile_description(profile: str) -> str:
    mentor = st.session_state.get("mentor_area", "Física")
    tema = MENTOR_THEMES[mentor]
    return tema["desc_teacher"] if profile == "Professor" else tema["desc_student"]


def list_conversations():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, title, created_at, updated_at, profile, nickname, mentor_area, pdf_name, image_name
        FROM conversations
        WHERE user_key = ?
        ORDER BY updated_at DESC, id DESC
        """,
        (build_user_key(),),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_conversation(conversation_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, title, created_at, updated_at, profile, nickname, mentor_area,
               pdf_path, pdf_name, image_path, image_name, user_key
        FROM conversations
        WHERE id = ? AND user_key = ?
        """,
        (conversation_id, build_user_key()),
    )
    row = cur.fetchone()
    conn.close()
    return row


def create_conversation(title: str = "Nova conversa") -> int:
    now = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO conversations(
            user_key, title, created_at, updated_at, profile, nickname, mentor_area,
            pdf_path, pdf_name, image_path, image_name
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            build_user_key(),
            title,
            now,
            now,
            st.session_state.profile,
            st.session_state.nickname,
            st.session_state.mentor_area,
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


def delete_conversation(conversation_id: int):
    conv = get_conversation(conversation_id)
    if conv:
        pdf_path = conv[7]
        image_path = conv[9]
        for path in [pdf_path, image_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    cur.execute("DELETE FROM conversations WHERE id = ? AND user_key = ?", (conversation_id, build_user_key()))
    conn.commit()
    conn.close()


def save_message(conversation_id: int, role: str, content: str):
    now = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (conversation_id, role, content, now),
    )
    cur.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
    conn.commit()
    conn.close()


def get_messages(conversation_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY id ASC",
        (conversation_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def update_conversation_files(conversation_id: int, *, pdf_path=None, pdf_name=None, image_path=None, image_name=None):
    conv = get_conversation(conversation_id)
    if not conv:
        return

    atual_pdf_path, atual_pdf_name, atual_img_path, atual_img_name = conv[7], conv[8], conv[9], conv[10]
    pdf_path = atual_pdf_path if pdf_path is None else pdf_path
    pdf_name = atual_pdf_name if pdf_name is None else pdf_name
    image_path = atual_img_path if image_path is None else image_path
    image_name = atual_img_name if image_name is None else image_name

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE conversations
        SET pdf_path = ?, pdf_name = ?, image_path = ?, image_name = ?, updated_at = ?
        WHERE id = ? AND user_key = ?
        """,
        (
            pdf_path,
            pdf_name,
            image_path,
            image_name,
            datetime.utcnow().isoformat(),
            conversation_id,
            build_user_key(),
        ),
    )
    conn.commit()
    conn.close()


def maybe_update_title_from_first_message(conversation_id: int, text: str):
    texto = re.sub(r"\s+", " ", (text or "").strip())
    if not texto:
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT title FROM conversations WHERE id = ? AND user_key = ?",
        (conversation_id, build_user_key()),
    )
    row = cur.fetchone()
    if row and row[0] == "Nova conversa":
        cur.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ? AND user_key = ?",
            (texto[:72], datetime.utcnow().isoformat(), conversation_id, build_user_key()),
        )
        conn.commit()
    conn.close()


def resetar_sessao_visual():
    st.session_state.chat = []
    st.session_state.db_texto_pdf = None
    st.session_state.pdf_nome = None
    st.session_state.image_nome = None
    st.session_state.contador_perguntas = 0
    st.session_state.ultima_imagem_visual = None
    st.session_state.last_detected_intent = None
    st.session_state.pending_file_key = str(uuid.uuid4())


def carregar_conversa_no_estado(conversation_id: int):
    conv = get_conversation(conversation_id)
    if not conv:
        return

    _, _, _, _, profile, nickname, mentor_area, pdf_path, pdf_name, image_path, image_name, _ = conv
    st.session_state.chat = [{"role": role, "content": content} for role, content, _ in get_messages(conversation_id)]
    st.session_state.profile = profile or st.session_state.profile
    st.session_state.nickname = nickname or st.session_state.nickname
    st.session_state.mentor_area = mentor_area or st.session_state.mentor_area
    st.session_state.pdf_nome = pdf_name
    st.session_state.image_nome = image_name
    st.session_state.current_conversation_id = conversation_id
    st.session_state.loaded_conversation_id = conversation_id
    st.session_state.ultima_imagem_visual = None

    if pdf_path and os.path.exists(pdf_path):
        st.session_state.db_texto_pdf = processar_pdf_from_path(pdf_path)
    else:
        st.session_state.db_texto_pdf = None


def formatar_conversation_label(row) -> str:
    _, title, _, _, _, _, mentor_area, pdf_name, image_name = row
    extras = []
    if mentor_area:
        extras.append(mentor_area)
    if pdf_name:
        extras.append("PDF")
    if image_name:
        extras.append("IMG")
    suffix = f" [{' • '.join(extras)}]" if extras else ""
    return f"{title}{suffix}"


def chemistry_panel_markdown() -> str:
    groups = [
        ["H", "Li", "Na", "K", "Rb", "Cs"],
        ["Be", "Mg", "Ca", "Sr", "Ba"],
        ["B", "Al", "Ga", "In", "Tl"],
        ["C", "Si", "Ge", "Sn", "Pb"],
        ["N", "P", "As", "Sb", "Bi"],
        ["O", "S", "Se", "Te", "Po"],
        ["F", "Cl", "Br", "I", "At"],
        ["He", "Ne", "Ar", "Kr", "Xe", "Rn"],
    ]
    linhas = []
    names = ["1A", "2A", "3A", "4A", "5A", "6A", "7A", "8A"]
    for name, group in zip(names, groups):
        linhas.append(f"**{name}**: " + " • ".join(group))
    return "\n\n".join(linhas)


# =========================================================
# GROQ
# =========================================================
def carregar_cliente() -> Tuple[Optional[Groq], Optional[str]]:
    try:
        chave = str(st.secrets.get("GROQ_API_KEY", "")).strip()
    except Exception:
        chave = ""
    if not chave:
        return None, "A chave GROQ_API_KEY não foi encontrada ou está vazia nos Secrets."
    try:
        return Groq(api_key=chave), None
    except Exception as e:
        return None, f"Erro ao iniciar cliente Groq: {e}"


client, erro_cliente = carregar_cliente()


# =========================================================
# ARQUIVOS / PDF / IMAGEM
# =========================================================
def processar_pdf_from_path(pdf_path: str) -> Optional[str]:
    try:
        reader = PdfReader(pdf_path)
        textos = []
        for page in reader.pages:
            txt = (page.extract_text() or "").strip()
            if txt:
                textos.append(re.sub(r"\s+", " ", txt))
        conteudo = "\n\n".join(textos).strip()
        return conteudo if conteudo else None
    except Exception:
        return None


def tamanho_mb(uploaded_file) -> float:
    return round(len(uploaded_file.getbuffer()) / (1024 * 1024), 2)


def validar_upload(uploaded_file) -> Optional[str]:
    nome = uploaded_file.name.lower()
    mb = tamanho_mb(uploaded_file)

    if nome.endswith(".pdf"):
        if mb > MAX_PDF_MB:
            return f"O PDF excede o limite de {MAX_PDF_MB} MB."
        return None

    if any(nome.endswith(f".{ext}") for ext in IMAGE_EXTS):
        if mb > MAX_IMG_MB:
            return f"A imagem excede o limite de {MAX_IMG_MB} MB."
        return None

    return "Envie apenas PDF ou imagem (PNG, JPG, JPEG ou WEBP)."


def salvar_upload(uploaded_file) -> Tuple[str, str]:
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    destino = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(destino, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return destino, uploaded_file.name


# =========================================================
# INTENÇÃO / PROMPTS
# =========================================================
def formatar_historico_curto(chat: List[Dict[str, str]], limite: int = CHAT_HISTORY_LIMIT) -> str:
    if not chat:
        return ""
    blocos = []
    for msg in chat[-limite:]:
        papel = "Usuário" if msg["role"] == "user" else "Assistente"
        conteudo = (msg["content"] or "").strip()
        if conteudo:
            blocos.append(f"{papel}: {conteudo[:500]}")
    return "\n".join(blocos)


def detect_intent(texto: str, has_pdf: bool, has_image: bool, profile: str, mentor_area: str) -> str:
    t = (texto or "").lower()

    def has_any(*keys) -> bool:
        return any(k in t for k in keys)

    if has_pdf and has_any("resuma", "resumir", "resumo", "sintetize", "explique esse pdf", "leia esse pdf"):
        return "resumo_pdf"
    if has_pdf:
        return "usar_pdf"
    if has_image and has_any("descreva", "explique", "analise", "analisa", "o que tem", "interprete"):
        return "imagem_anexada"
    if has_any("latex", "fórmula", "formula", "equação", "equacao", "notação", "notacao"):
        return "latex"
    if has_any("esquema visual", "mapa mental", "quadro resumo", "diagrama", "visual"):
        return "visual"
    if has_any("questão", "questao", "exercício", "exercicio", "simulado", "quiz", "lista"):
        return "exercicios"
    if has_any("corrija", "corrigir", "onde errei", "onde eu errei", "confere minha resposta"):
        return "correcao"
    if profile == "Professor" and has_any("média", "media", "nota", "notas", "turma", "planilha", "desempenho"):
        return "apoio_docente"
    if profile == "Professor" and has_any("plano de aula", "sequência didática", "sequencia didatica", "atividade", "roteiro"):
        return "planejamento_docente"
    if profile == "Professor" and has_any("pibid", "artigo", "projeto", "resumo expandido", "iniciação científica", "iniciacao cientifica"):
        return "pesquisa_docente"
    if mentor_area == "Química" and has_any("tabela periódica", "tabela periodica", "nomenclatura"):
        return "quimica"
    return "explicacao"


def intent_label(intent: str) -> str:
    labels = {
        "resumo_pdf": "Resumo de PDF",
        "usar_pdf": "Uso de PDF",
        "imagem_anexada": "Imagem anexada",
        "latex": "Explicação com LaTeX",
        "visual": "Esquema visual",
        "exercicios": "Exercícios / quiz",
        "correcao": "Correção",
        "apoio_docente": "Apoio docente",
        "planejamento_docente": "Planejamento docente",
        "pesquisa_docente": "Pesquisa / iniciação científica",
        "quimica": "Química / nomenclatura",
        "explicacao": "Explicação geral",
    }
    return labels.get(intent, "Explicação geral")


def obter_prompt_sistema(intent: str) -> str:
    nome = get_first_name(st.session_state.nickname)
    profile = st.session_state.profile
    mentor_area = st.session_state.mentor_area

    base = f"""
Você é o MentorEdu IA, um mentor acadêmico institucional do {INSTITUTION_NAME}, ligado ao {PROJECT_NAME} e à {COURSE_NAME}.
Você está atendendo {nome}, no perfil {profile}, com mentor especializado em {mentor_area}.
Responda em português do Brasil.
Seja didático, claro, acolhedor e direto.
Não invente dados, referências ou resultados.
Quando houver matemática, física ou química com fórmulas, use LaTeX válido com $...$ e $$...$$.
Não peça que o usuário configure manualmente ferramentas; interprete o pedido e aja.
""".strip()

    if profile == "Aluno":
        base += "\nVocê está ajudando um estudante. Priorize explicação clara, passo a passo, erros comuns e uma linguagem acessível."
    else:
        base += "\nVocê está ajudando um docente. Priorize metodologia, planejamento, organização de material, avaliação, médias e iniciação científica."

    if mentor_area == "Física":
        base += "\nEspecialidade: Física escolar e início da graduação, com ênfase em interpretação física antes de apenas aplicar fórmula."
    elif mentor_area == "Matemática":
        base += "\nEspecialidade: Matemática escolar, explicando raciocínio, estratégia, simbologia e verificação do resultado."
    elif mentor_area == "Química":
        base += "\nEspecialidade: Química com foco em nomenclatura, estequiometria, tabela periódica, reações e cálculos químicos."
    else:
        base += "\nEspecialidade: Linguagens, trabalhando português e inglês com clareza, interpretação e correção textual."

    extras = {
        "resumo_pdf": "Tarefa principal: resumir o PDF com clareza e destacar conceitos-chave.",
        "usar_pdf": "Tarefa principal: usar o PDF como base da resposta, sem copiar trechos longos.",
        "imagem_anexada": "Tarefa principal: considere que há uma imagem anexada, mas seja honesto se a análise visual detalhada não estiver disponível.",
        "latex": "Tarefa principal: usar notação matemática organizada e bem formatada.",
        "visual": "Tarefa principal: estruturar o conteúdo de forma excelente para posterior esquema visual.",
        "exercicios": "Tarefa principal: gerar ou resolver exercícios no nível adequado, com comentários curtos.",
        "correcao": "Tarefa principal: apontar acertos, erros e como melhorar a resposta do usuário.",
        "apoio_docente": "Tarefa principal: apoiar o professor com notas, médias, organização e feedback de turma.",
        "planejamento_docente": "Tarefa principal: montar plano, sequência didática, atividade ou roteiro de aula.",
        "pesquisa_docente": "Tarefa principal: apoiar projeto, PIBID, artigo, resumo expandido ou iniciação científica.",
        "quimica": "Tarefa principal: responder com linguagem consistente de Química e, quando útil, relacionar com a tabela periódica.",
        "explicacao": "Tarefa principal: responder com explicação clara e contextualizada.",
    }
    base += "\n" + extras.get(intent, extras["explicacao"])
    return base


def montar_prompt_usuario(pergunta: str, pdf_texto: Optional[str], intent: str, has_image: bool) -> str:
    partes = [
        f"Perfil do usuário: {st.session_state.profile}",
        f"Nome de preferência: {get_first_name(st.session_state.nickname)}",
        f"Mentor escolhido: {st.session_state.mentor_area}",
        f"Intenção inferida: {intent_label(intent)}",
    ]

    historico = formatar_historico_curto(st.session_state.get("chat", []))
    if historico:
        partes.append("Histórico recente:\n" + historico)

    if pdf_texto:
        partes.append("Trecho do PDF para contexto:\n" + pdf_texto[:PDF_CONTEXT_LIMIT])

    if has_image:
        partes.append(
            "Há uma imagem anexada. Se a pergunta depender totalmente da leitura da imagem, avise com honestidade que a análise visual detalhada pode exigir módulo de visão dedicado."
        )

    partes.append("Pedido atual:\n" + pergunta.strip())
    return "\n\n".join(partes)


def limpar_resposta(texto: str) -> str:
    if not texto:
        return "Não consegui gerar uma resposta útil."
    texto = texto.strip()
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto or "Não consegui gerar uma resposta útil."


def gerar_resposta_groq(prompt_sistema: str, prompt_usuario: str) -> str:
    if client is None:
        return f"Não consegui iniciar a IA. {erro_cliente or ''}".strip()
    try:
        resp = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
            temperature=0.25,
            max_tokens=1200,
        )
        return limpar_resposta(resp.choices[0].message.content.strip())
    except Exception as e:
        return f"Ocorreu um erro ao gerar a resposta: {e}"


def gerar_texto_visual(resposta: str, pergunta: str) -> str:
    if client is None:
        return "Resumo visual indisponível no momento."

    prompt_sistema = """
Você cria resumos visuais curtos para estudos.
Transforme a explicação em um esquema visual textual, curto, organizado e claro.
Use títulos curtos, setas, tópicos e fórmulas simples quando útil.
Não escreva parágrafos longos.
No máximo 12 linhas.
""".strip()

    prompt_usuario = f"""
Mentor: {st.session_state.mentor_area}
Perfil: {st.session_state.profile}
Pedido: {pergunta}

Resposta-base:
{resposta}

Agora gere um esquema visual resumido.
""".strip()

    try:
        resp = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
            temperature=0.2,
            max_tokens=280,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return "Resumo visual indisponível no momento."


# =========================================================
# IMAGEM LOCAL
# =========================================================
def _get_font(size: int = 24):
    possiveis = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for caminho in possiveis:
        if os.path.exists(caminho):
            try:
                return ImageFont.truetype(caminho, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def criar_imagem_esquema(titulo: str, corpo: str) -> str:
    largura = 1400
    altura = 1000
    bg = (248, 245, 239)
    fg = (43, 38, 33)
    accent = (133, 108, 87)

    img = Image.new("RGB", (largura, altura), bg)
    draw = ImageDraw.Draw(img)

    font_titulo = _get_font(42)
    font_sub = _get_font(24)
    font_corpo = _get_font(28)

    margem_x = 70
    y = 60

    draw.rounded_rectangle((40, 30, largura - 40, altura - 30), radius=28, outline=(215, 201, 184), width=3)
    draw.text((margem_x, y), titulo, fill=accent, font=font_titulo)
    y += 70

    subt = f"{st.session_state.mentor_area} • {st.session_state.profile}"
    draw.text((margem_x, y), subt, fill=(100, 88, 76), font=font_sub)
    y += 55

    linhas_final = []
    for paragrafo in corpo.splitlines():
        paragrafo = paragrafo.strip()
        if not paragrafo:
            linhas_final.append("")
            continue
        wrap = textwrap.wrap(paragrafo, width=56)
        linhas_final.extend(wrap)

    for linha in linhas_final[:24]:
        draw.text((margem_x, y), linha, fill=fg, font=font_corpo)
        y += 38
        if y > altura - 80:
            break

    nome = f"visual_{uuid.uuid4().hex}.png"
    caminho = os.path.join(UPLOAD_DIR, nome)
    img.save(caminho)
    return caminho


# =========================================================
# TELA DE ENTRADA
# =========================================================
def render_login_screen():
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-center">', unsafe_allow_html=True)
    if os.path.exists(IF_LOGO):
        st.markdown('<div class="login-logo-wrap">', unsafe_allow_html=True)
        st.image(IF_LOGO, width=160)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="project-badge">{PROJECT_NAME}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="institution-title">{INSTITUTION_NAME}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="course-title">{COURSE_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-title" style="margin-top:16px;">Escolha seu mentor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="small-muted" style="text-align:center; margin-bottom:18px;">Seu nome, perfil e área já definem o estilo de ajuda. Depois disso, basta conversar naturalmente com a IA.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    nome = st.text_input(
        "Como você quer ser chamado pelo mentor?",
        value=st.session_state.nickname,
        placeholder="Ex.: João, Maria, Professor Roberto...",
    )
    perfil = st.selectbox("Perfil", PROFILE_OPTIONS, index=PROFILE_OPTIONS.index(st.session_state.profile))

    nome_preview = get_first_name(nome) if nome else "Você"
    st.markdown(
        f"""
        <div class="name-preview">
            <div class="name-avatar">{nome_preview[:1].upper()}</div>
            <div>
                <div style="font-weight:800; color:#4f3f34;">{nome_preview}</div>
                <div class="small-muted">Esse será o nome usado pelo mentor na conversa.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div style="font-weight:800; margin-bottom:10px; color:#5b473b;">O que você vai estudar hoje?</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    mentor_click = None
    mentor_labels = list(MENTOR_THEMES.keys())
    for i, area in enumerate(mentor_labels):
        data = MENTOR_THEMES[area]
        with cols[i]:
            st.markdown(
                f"""
                <div class="mentor-card">
                    <div class="mentor-emoji">{data['emoji']}</div>
                    <div class="mentor-title">{area}</div>
                    <div class="mentor-desc">{data['desc_teacher'] if perfil == 'Professor' else data['desc_student']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Escolher {area}", key=f"mentor_{area}", use_container_width=True):
                mentor_click = area

    if mentor_click:
        if not nome.strip():
            st.warning("Digite como você quer ser chamado antes de entrar.")
        else:
            st.session_state.nickname = nome.strip()
            st.session_state.profile = perfil
            st.session_state.mentor_area = mentor_click
            st.session_state.auth_complete = True
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


if not st.session_state.auth_complete:
    render_login_screen()
    st.stop()


# =========================================================
# ESTADO INICIAL DE CONVERSA
# =========================================================
rows = list_conversations()
if not rows:
    cid = create_conversation()
    st.session_state.current_conversation_id = cid
    carregar_conversa_no_estado(cid)
elif st.session_state.current_conversation_id is None:
    st.session_state.current_conversation_id = rows[0][0]
    carregar_conversa_no_estado(rows[0][0])

st.markdown(gerar_css(), unsafe_allow_html=True)


# =========================================================
# SIDEBAR ENXUTA
# =========================================================
with st.sidebar:
    if os.path.exists(IF_LOGO):
        st.markdown('<div class="sidebar-logo-top">', unsafe_allow_html=True)
        st.image(IF_LOGO, width=180)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="sidebar-inst">
            <div class="sidebar-inst-title">{INSTITUTION_NAME}</div>
            <div class="sidebar-inst-sub">{COURSE_NAME}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    apelido = get_first_name(st.session_state.nickname)
    papel = st.session_state.profile
    mentor = st.session_state.mentor_area

    st.markdown(
        f"""
        <div class="account-card">
            <div class="account-user-row">
                <div class="account-avatar">{apelido[:1].upper()}</div>
                <div>
                    <div class="account-name">{apelido}</div>
                    <div class="account-role">{papel} • Mentor de {mentor}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Trocar perfil / mentor", use_container_width=True):
        st.session_state.auth_complete = False
        st.rerun()

    st.markdown("---")
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown("### Conversas")
    with c2:
        with st.popover("⋯"):
            if st.button("Nova conversa", use_container_width=True):
                novo_id = create_conversation()
                st.session_state.current_conversation_id = novo_id
                resetar_sessao_visual()
                carregar_conversa_no_estado(novo_id)
                st.rerun()
            if st.button("Apagar conversa atual", use_container_width=True):
                apagar_id = st.session_state.current_conversation_id
                delete_conversation(apagar_id)
                resetar_sessao_visual()
                restantes = list_conversations()
                novo_atual = restantes[0][0] if restantes else create_conversation()
                st.session_state.current_conversation_id = novo_atual
                carregar_conversa_no_estado(novo_atual)
                st.rerun()

    conv_rows = list_conversations()
    conv_map = {f"{formatar_conversation_label(r)} • #{r[0]}": r[0] for r in conv_rows}
    conv_keys = list(conv_map.keys())
    conv_ids = list(conv_map.values())
    current_id = st.session_state.current_conversation_id
    if current_id not in conv_ids and conv_ids:
        current_id = conv_ids[0]

    if conv_keys:
        idx = conv_ids.index(current_id)
        escolhido_key = st.selectbox("Histórico", conv_keys, index=idx, label_visibility="collapsed")
        escolhido_id = conv_map[escolhido_key]
    else:
        escolhido_id = create_conversation()
        st.session_state.current_conversation_id = escolhido_id
        carregar_conversa_no_estado(escolhido_id)

    if escolhido_id != st.session_state.current_conversation_id:
        carregar_conversa_no_estado(escolhido_id)
        st.rerun()

    st.markdown(
        '<div class="conversation-hint">O nome da conversa nasce da sua primeira pergunta. O histórico fica separado por usuário.</div>',
        unsafe_allow_html=True,
    )


# =========================================================
# TOPO
# =========================================================
desc = profile_description(st.session_state.profile)
mentor_meta = MENTOR_THEMES[st.session_state.mentor_area]

st.markdown(
    f"""
    <div class="hero-card">
        <div class="project-badge">{PROJECT_NAME}</div>
        <div class="hero-title">{APP_NAME}</div>
        <div class="institution-title">{INSTITUTION_NAME}</div>
        <div class="course-title">{COURSE_NAME}</div>
        <div class="hero-subtitle">
            Olá, {get_first_name(st.session_state.nickname)}. Você está no perfil <b>{st.session_state.profile}</b> com o mentor de <b>{st.session_state.mentor_area}</b> {mentor_meta['emoji']}.<br>
            Área atual: {desc}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.mentor_area == "Química":
    st.markdown('<div class="chem-card" style="margin-top:14px;">', unsafe_allow_html=True)
    st.markdown("**Tabela periódica rápida**")
    st.markdown(chemistry_panel_markdown())
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="painel-card" style="margin-top:16px;">', unsafe_allow_html=True)
st.markdown('<div class="main-title">Converse naturalmente com o mentor</div>', unsafe_allow_html=True)

if st.session_state.profile == "Aluno":
    st.caption(
        "Exemplos: ‘explique MRU’, ‘resuma este PDF’, ‘faça 5 questões’, ‘responda em LaTeX’, ‘crie um esquema visual’."
    )
else:
    st.caption(
        "Exemplos: ‘monte um plano de aula’, ‘crie questões’, ‘calcule a média desta turma’, ‘use este PDF como base’, ‘me ajude no PIBID’."
    )

if st.session_state.last_detected_intent:
    st.markdown(
        f"""
        <div class="mini-soft-card" style="margin-top:10px;">
            <div style="font-weight:800; margin-bottom:4px;">Leitura atual do mentor</div>
            <div class="small-muted">{intent_label(st.session_state.last_detected_intent)} • {st.session_state.mentor_area}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# CHAT
# =========================================================
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=False)

if st.session_state.ultima_imagem_visual and os.path.exists(st.session_state.ultima_imagem_visual):
    st.image(
        st.session_state.ultima_imagem_visual,
        caption="Esquema visual gerado",
        use_container_width=True,
    )


# =========================================================
# BARRA DE ARQUIVOS AO LADO DO CHAT
# =========================================================
st.markdown('<div class="toolbar-card" style="margin-top:14px;">', unsafe_allow_html=True)
left, right = st.columns([3, 2])
with left:
    arquivo = st.file_uploader(
        "Anexar arquivo",
        type=["pdf", "png", "jpg", "jpeg", "webp"],
        key=f"uploader_{st.session_state.pending_file_key}",
        label_visibility="visible",
        help="Envie PDF ou imagem diretamente por aqui.",
    )
with right:
    st.markdown(
        f"""
        <div class="mini-soft-card">
            <div style="font-weight:800; margin-bottom:4px;">Anexos desta conversa</div>
            <div class="small-muted">PDF: {st.session_state.pdf_nome or 'nenhum'}<br>Imagem: {st.session_state.image_nome or 'nenhuma'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

b1, b2 = st.columns(2)
with b1:
    if st.button("Limpar PDF", use_container_width=True):
        update_conversation_files(st.session_state.current_conversation_id, pdf_path=None, pdf_name=None)
        st.session_state.db_texto_pdf = None
        st.session_state.pdf_nome = None
        st.rerun()
with b2:
    if st.button("Limpar imagem", use_container_width=True):
        update_conversation_files(st.session_state.current_conversation_id, image_path=None, image_name=None)
        st.session_state.image_nome = None
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# PROCESSAMENTO DE ANEXO
# =========================================================
houve_pdf = False
houve_imagem = False
if arquivo is not None:
    erro_upload = validar_upload(arquivo)
    if erro_upload:
        st.warning(erro_upload)
    else:
        destino, nome_original = salvar_upload(arquivo)
        nome_lower = nome_original.lower()
        if nome_lower.endswith(".pdf"):
            st.session_state.db_texto_pdf = processar_pdf_from_path(destino)
            st.session_state.pdf_nome = nome_original
            update_conversation_files(st.session_state.current_conversation_id, pdf_path=destino, pdf_name=nome_original)
            houve_pdf = True
            st.toast(f"PDF ativo: {nome_original}")
        else:
            st.session_state.image_nome = nome_original
            update_conversation_files(st.session_state.current_conversation_id, image_path=destino, image_name=nome_original)
            houve_imagem = True
            st.toast(f"Imagem anexada: {nome_original}")
            try:
                st.image(destino, caption="Imagem anexada", use_container_width=True)
            except Exception:
                pass


# =========================================================
# ENTRADA DO CHAT
# =========================================================
prompt = st.chat_input("Escreva sua dúvida, peça um resumo, exercício, correção ou análise do arquivo anexado...")

if prompt and prompt.strip():
    if st.session_state.contador_perguntas >= MAX_PERGUNTAS_SESSAO:
        st.warning("Você atingiu o limite de perguntas desta sessão.")
    else:
        conv_id = st.session_state.current_conversation_id
        pergunta = prompt.strip()
        maybe_update_title_from_first_message(conv_id, pergunta)

        save_message(conv_id, "user", pergunta)
        st.session_state.chat.append({"role": "user", "content": pergunta})
        st.session_state.contador_perguntas += 1

        conv = get_conversation(conv_id)
        has_pdf = bool(st.session_state.db_texto_pdf)
        has_image = bool(conv and conv[10])
        intent = detect_intent(
            texto=pergunta,
            has_pdf=has_pdf,
            has_image=has_image,
            profile=st.session_state.profile,
            mentor_area=st.session_state.mentor_area,
        )
        st.session_state.last_detected_intent = intent

        prompt_sistema = obter_prompt_sistema(intent)
        prompt_usuario = montar_prompt_usuario(
            pergunta=pergunta,
            pdf_texto=st.session_state.db_texto_pdf,
            intent=intent,
            has_image=has_image,
        )

        with st.spinner("Pensando..."):
            resposta = gerar_resposta_groq(prompt_sistema, prompt_usuario)

        if intent == "imagem_anexada":
            resposta += "\n\n> Observação: nesta versão a imagem fica anexada e visível na conversa, mas a leitura visual detalhada ainda depende de um módulo de visão."

        save_message(conv_id, "assistant", resposta)
        st.session_state.chat.append({"role": "assistant", "content": resposta})

        if intent == "visual" or "esquema visual" in pergunta.lower():
            try:
                texto_visual = gerar_texto_visual(resposta, pergunta)
                titulo_visual = f"{st.session_state.mentor_area} • esquema visual"
                caminho_img = criar_imagem_esquema(titulo_visual, texto_visual)
                st.session_state.ultima_imagem_visual = caminho_img
            except Exception:
                st.session_state.ultima_imagem_visual = None
        else:
            st.session_state.ultima_imagem_visual = None

        st.rerun()


st.caption(f"{APP_NAME} • {PROJECT_NAME} • {INSTITUTION_NAME} • {COURSE_NAME}")
