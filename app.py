import os
import re
import uuid
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
MAX_PERGUNTAS_SESSAO = 40
PDF_CONTEXT_LIMIT = 7000
CHAT_HISTORY_LIMIT = 6
MODEL_NAME = "llama-3.3-70b-versatile"

os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================================================
# TEMA / CSS
# =========================================================
def gerar_css() -> str:
    return """
    <style>
        :root {
            --bg: #f7f3ee;
            --bg-top: #f4ede4;
            --sidebar: #efe6dc;
            --card: #fffdf9;
            --card-2: #faf5ef;
            --line: #dccfc0;
            --text: #3b312a;
            --muted: #7a6d61;
            --accent: #9a8676;
            --accent-hover: #826f60;
            --badge: #f1e7dc;
            --user-bg: #efe4d7;
            --assistant-bg: #fffaf5;
            --shadow: 0 12px 28px rgba(92, 70, 48, 0.07);
        }

        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"] {
            background: var(--bg) !important;
        }

        .main .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            max-width: 1100px !important;
        }

        header[data-testid="stHeader"] {
            background: var(--bg-top) !important;
            border-bottom: 1px solid var(--line) !important;
        }

        [data-testid="stSidebar"] {
            background: var(--sidebar) !important;
            border-right: 1px solid var(--line) !important;
        }

        [data-testid="stSidebar"] * {
            color: var(--text) !important;
        }

        .hero-card,
        .painel-card,
        .status-card,
        .login-card,
        .choice-card,
        .account-card,
        .mini-soft-card {
            background: var(--card) !important;
            border: 1px solid var(--line) !important;
            border-radius: 24px !important;
            box-shadow: var(--shadow) !important;
        }

        .login-card {
            max-width: 760px;
            margin: 30px auto;
            padding: 28px;
        }

        .hero-card,
        .painel-card {
            padding: 24px;
        }

        .project-badge {
            display: inline-block;
            background: var(--badge) !important;
            color: #6a5849 !important;
            border: 1px solid #d9c9b6 !important;
            padding: 6px 12px !important;
            border-radius: 999px !important;
            font-size: .88rem !important;
            font-weight: 700 !important;
            margin-bottom: 14px !important;
        }

        .hero-title {
            color: #5b473b !important;
            font-size: 2.2rem !important;
            font-weight: 800 !important;
            line-height: 1.05 !important;
            margin-bottom: 6px !important;
        }

        .hero-subtitle {
            color: var(--muted) !important;
            font-size: 1rem !important;
            margin-bottom: 12px !important;
        }

        .institution-title {
            color: #5a4639 !important;
            font-size: 1.3rem !important;
            font-weight: 800 !important;
            margin-bottom: 2px !important;
        }

        .course-title {
            color: #7b6a5c !important;
            font-size: 1.02rem !important;
            font-weight: 600 !important;
            margin-bottom: 0 !important;
        }

        .main-title {
            color: #5b473b !important;
            font-size: 1.9rem !important;
            font-weight: 800 !important;
            line-height: 1.1 !important;
            margin-bottom: 10px !important;
            text-align: center !important;
        }

        .small-muted {
            color: var(--muted) !important;
        }

        .login-center {
            text-align: center;
            margin-bottom: 14px;
        }

        .login-logo-wrap {
            display: flex;
            justify-content: center;
            margin-bottom: 14px;
        }

        .name-preview {
            background: var(--card-2);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 14px;
            display: flex;
            align-items: center;
            gap: 14px;
            margin-top: 10px;
            margin-bottom: 14px;
        }

        .name-avatar,
        .account-avatar {
            width: 50px;
            height: 50px;
            border-radius: 999px;
            background: var(--accent);
            color: white !important;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.15rem;
            font-weight: 800;
            flex-shrink: 0;
        }

        .choice-card {
            padding: 18px;
            text-align: center;
            min-height: 150px;
        }

        .choice-card h3 {
            margin: 10px 0 8px 0;
            color: #5b473b !important;
        }

        .choice-card p {
            color: var(--muted) !important;
            font-size: 0.95rem !important;
        }

        .account-card {
            padding: 14px;
            margin-bottom: 12px;
        }

        .account-user-row {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .account-name {
            font-weight: 800 !important;
            color: #4f3f34 !important;
            line-height: 1.1;
            margin-bottom: 2px;
        }

        .account-role {
            color: var(--muted) !important;
            font-size: 0.88rem !important;
        }

        .sidebar-logo-top {
            display: flex;
            justify-content: center;
            margin-bottom: 14px;
        }

        .sidebar-inst {
            text-align: center;
            margin-bottom: 18px;
        }

        .sidebar-inst-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: #5b473b !important;
            line-height: 1.1;
        }

        .sidebar-inst-sub {
            color: var(--muted) !important;
            font-size: 0.92rem !important;
        }

        .mini-soft-card {
            padding: 12px 14px;
            border-radius: 16px !important;
        }

        .stButton > button {
            background: var(--accent) !important;
            color: #fffdfa !important;
            border: 1px solid var(--accent) !important;
            border-radius: 14px !important;
            min-height: 44px !important;
        }

        .stButton > button:hover {
            background: var(--accent-hover) !important;
            border-color: var(--accent-hover) !important;
        }

        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div {
            background: #fffaf5 !important;
            color: #3b312a !important;
            border: 1px solid #dccfc0 !important;
            border-radius: 14px !important;
        }

        div[data-baseweb="popover"],
        div[data-baseweb="popover"] * {
            color: #3b312a !important;
        }

        div[data-baseweb="popover"] > div {
            background: #fffaf5 !important;
            border: 1px solid #dccfc0 !important;
            border-radius: 14px !important;
            box-shadow: 0 12px 28px rgba(92, 70, 48, 0.10) !important;
        }

        ul[role="listbox"],
        ul[role="listbox"] li,
        div[role="option"] {
            background: #fffaf5 !important;
            color: #3b312a !important;
        }

        [data-testid="stBottomBlockContainer"] {
            background: var(--bg) !important;
            border-top: 1px solid var(--line) !important;
        }

        [data-testid="stChatInputContainer"],
        [data-testid="stChatInputContainer"] > div,
        [data-testid="stChatInput"],
        [data-testid="stChatInput"] > div,
        section[data-testid="stChatInput"] {
            background: var(--bg) !important;
            border: none !important;
            box-shadow: none !important;
        }

        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInput"] input {
            background: #fffaf5 !important;
            color: #3b312a !important;
            border: 1px solid #dccfc0 !important;
            border-radius: 16px !important;
        }

        [data-testid="stChatInput"] textarea::placeholder,
        [data-testid="stChatInput"] input::placeholder {
            color: #7a6d61 !important;
        }

        [data-testid="stChatMessageContent"] {
            color: var(--text) !important;
            border: 1px solid var(--line) !important;
            border-radius: 16px !important;
            padding: .65rem .8rem !important;
        }

        .stChatMessage:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
            background: var(--user-bg) !important;
        }

        .stChatMessage:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
            background: var(--assistant-bg) !important;
        }

        p, span, label, div, li, h1, h2, h3, h4, small {
            color: var(--text) !important;
        }
    </style>
    """


st.markdown(gerar_css(), unsafe_allow_html=True)


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
            pdf_path TEXT,
            pdf_name TEXT
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

    if "profile" not in cols:
        cur.execute("ALTER TABLE conversations ADD COLUMN profile TEXT")
    if "nickname" not in cols:
        cur.execute("ALTER TABLE conversations ADD COLUMN nickname TEXT")
    if "pdf_path" not in cols:
        cur.execute("ALTER TABLE conversations ADD COLUMN pdf_path TEXT")
    if "pdf_name" not in cols:
        cur.execute("ALTER TABLE conversations ADD COLUMN pdf_name TEXT")
    if "user_key" not in cols:
        cur.execute("ALTER TABLE conversations ADD COLUMN user_key TEXT")

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
        "chat": [],
        "db_texto_pdf": None,
        "pdf_nome": None,
        "current_conversation_id": None,
        "loaded_conversation_id": None,
        "confirm_delete": False,
        "contador_perguntas": 0,
        "ultima_imagem_visual": None,
        "last_detected_intent": None,
        "last_detected_subject": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_db()
init_session_state()


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
        pass
    return ""


def build_user_key() -> str:
    email = get_logged_email()
    base = email or f"{st.session_state.profile}|{st.session_state.nickname.strip().lower()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def list_conversations():
    user_key = build_user_key()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, title, created_at, updated_at, profile, nickname, pdf_name
        FROM conversations
        WHERE user_key = ?
        ORDER BY updated_at DESC, id DESC
        """,
        (user_key,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_conversation(conversation_id):
    user_key = build_user_key()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, title, created_at, updated_at, profile, nickname, pdf_path, pdf_name, user_key
        FROM conversations
        WHERE id = ? AND user_key = ?
        """,
        (conversation_id, user_key),
    )
    row = cur.fetchone()
    conn.close()
    return row


def create_conversation(title="Nova conversa"):
    now = datetime.utcnow().isoformat()
    user_key = build_user_key()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO conversations(title, created_at, updated_at, profile, nickname, pdf_path, pdf_name, user_key)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (title, now, now, st.session_state.profile, st.session_state.nickname, None, None, user_key),
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid


def rename_conversation(conversation_id, title):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ? AND user_key = ?",
        (title.strip(), datetime.utcnow().isoformat(), conversation_id, build_user_key()),
    )
    conn.commit()
    conn.close()


def delete_conversation(conversation_id):
    conv = get_conversation(conversation_id)
    if conv and conv[6] and os.path.exists(conv[6]):
        try:
            os.remove(conv[6])
        except Exception:
            pass

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    cur.execute("DELETE FROM conversations WHERE id = ? AND user_key = ?", (conversation_id, build_user_key()))
    conn.commit()
    conn.close()


def save_message(conversation_id, role, content):
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


def get_messages(conversation_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY id ASC",
        (conversation_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def update_conversation_pdf(conversation_id, pdf_path=None, pdf_name=None):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        """
        UPDATE conversations
        SET pdf_path = ?, pdf_name = ?, updated_at = ?
        WHERE id = ? AND user_key = ?
        """,
        (pdf_path, pdf_name, now, conversation_id, build_user_key()),
    )
    conn.commit()
    conn.close()


def maybe_update_title_from_first_message(conversation_id, text):
    texto = (text or "").strip()
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
        title = re.sub(r"\s+", " ", texto.replace("\n", " ")).strip()[:72]
        cur.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ? AND user_key = ?",
            (title, datetime.utcnow().isoformat(), conversation_id, build_user_key()),
        )
        conn.commit()
    conn.close()


def resetar_sessao_visual():
    st.session_state.chat = []
    st.session_state.db_texto_pdf = None
    st.session_state.pdf_nome = None
    st.session_state.contador_perguntas = 0
    st.session_state.confirm_delete = False
    st.session_state.ultima_imagem_visual = None
    st.session_state.last_detected_intent = None
    st.session_state.last_detected_subject = None


def carregar_conversa_no_estado(conversation_id):
    conv = get_conversation(conversation_id)
    if not conv:
        return

    _, _, _, _, profile, nickname, pdf_path, pdf_name, _ = conv

    st.session_state.chat = [{"role": role, "content": content} for role, content, _ in get_messages(conversation_id)]
    st.session_state.profile = profile or st.session_state.profile
    st.session_state.nickname = nickname or st.session_state.nickname
    st.session_state.pdf_nome = pdf_name
    st.session_state.current_conversation_id = conversation_id
    st.session_state.loaded_conversation_id = conversation_id
    st.session_state.confirm_delete = False
    st.session_state.ultima_imagem_visual = None

    if pdf_path and os.path.exists(pdf_path):
        st.session_state.db_texto_pdf = processar_pdf_from_path(pdf_path)
    else:
        st.session_state.db_texto_pdf = None


def formatar_conversation_label(row):
    _, title, _, _, profile, _, pdf_name = row
    extras = []
    if profile:
        extras.append(profile)
    if pdf_name:
        extras.append("PDF")
    suffix = f" [{' • '.join(extras)}]" if extras else ""
    return f"{title}{suffix}"


# =========================================================
# CLIENTE GROQ
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
# PDF
# =========================================================
def processar_pdf_from_path(pdf_path: str) -> Optional[str]:
    try:
        reader = PdfReader(pdf_path)
        textos = []
        for page in reader.pages:
            txt = (page.extract_text() or "").strip()
            if txt:
                txt = re.sub(r"\s+", " ", txt)
                textos.append(txt)
        conteudo = "\n\n".join(textos).strip()
        return conteudo if conteudo else None
    except Exception:
        return None


def tamanho_mb(uploaded_file) -> float:
    return round(len(uploaded_file.getbuffer()) / (1024 * 1024), 2)


def validar_upload(uploaded_file) -> Optional[str]:
    nome = uploaded_file.name.lower()
    mb = tamanho_mb(uploaded_file)

    if nome.endswith(".pdf") and mb > MAX_PDF_MB:
        return f"O PDF excede o limite de {MAX_PDF_MB} MB."
    if not nome.endswith(".pdf"):
        return "No momento, o anexo aceito é apenas PDF."

    return None


def salvar_upload(uploaded_file) -> Tuple[str, str]:
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    destino = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(destino, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return destino, uploaded_file.name


# =========================================================
# INTERPRETAÇÃO AUTOMÁTICA
# =========================================================
def infer_subject(texto: str, profile: str) -> str:
    t = (texto or "").lower()

    regras = [
        ("Física", ["mru", "muv", "cinemática", "força", "newton", "velocidade", "aceleração", "energia", "trabalho", "calor", "temperatura", "circuito", "corrente", "tensão", "resistência", "óptica", "onda", "frequência"]),
        ("Matemática", ["equação", "função", "derivada", "integral", "log", "matriz", "determinante", "seno", "cosseno", "trigonometria", "porcentagem"]),
        ("Química", ["mol", "ligações", "átomo", "pH", "ácido", "base", "reação", "estequiometria"]),
        ("Português", ["interpretação", "redação", "gramática", "sujeito", "predicado", "oração", "texto"]),
        ("Inglês", ["translate", "english", "inglês", "verb", "grammar", "reading"]),
        ("Linguagens", ["bncc", "letramento", "texto dissertativo", "linguagens"]),
        ("Metodologia Científica", ["artigo", "projeto de pesquisa", "metodologia", "objetivo geral", "objetivos específicos", "justificativa", "resumo expandido", "referencial teórico", "pibid", "iniciação científica"]),
    ]

    melhor = None
    maior = 0

    for assunto, palavras in regras:
        score = sum(1 for p in palavras if p in t)
        if score > maior:
            maior = score
            melhor = assunto

    if melhor:
        return melhor

    return "Metodologia Científica" if profile == "Professor" else "Física"


def detect_intent(texto: str, has_pdf: bool, profile: str) -> Dict[str, str]:
    t = (texto or "").lower()
    subject = infer_subject(texto, profile)

    def has_any(*keys) -> bool:
        return any(k in t for k in keys)

    if has_pdf and has_any("resuma", "resume", "resumir", "síntese", "sintese", "explique esse pdf", "leia esse pdf", "analise esse pdf"):
        intent = "resumo_pdf"
    elif has_pdf:
        intent = "usar_pdf"
    elif has_any("latex", "fórmula", "formula", "equação bonitinha", "equacao bonitinha", "notação matemática", "notacao matematica"):
        intent = "latex"
    elif has_any("esquema visual", "mapa mental", "visual", "diagrama", "quadro-resumo", "quadro resumo"):
        intent = "visual"
    elif has_any("questão", "questao", "exercício", "exercicio", "lista de exercícios", "lista de exercicios", "me teste", "quiz", "simulado"):
        intent = "exercicios"
    elif has_any("corrija", "corrigir", "onde eu errei", "revise minha resposta", "confere minha resposta"):
        intent = "correcao"
    elif profile == "Professor" and has_any("média", "media", "nota", "notas", "planilha", "desempenho da turma", "corrigir prova"):
        intent = "apoio_docente"
    elif profile == "Professor" and has_any("plano de aula", "aula", "sequência didática", "sequencia didatica", "atividade", "dinâmica", "dinamica"):
        intent = "planejamento_docente"
    elif profile == "Professor" and has_any("projeto", "pibid", "iniciação científica", "iniciacao cientifica", "artigo", "relatório", "relatorio", "resumo expandido"):
        intent = "pesquisa_docente"
    else:
        intent = "explicacao"

    return {"intent": intent, "subject": subject}


def intent_label(intent: str) -> str:
    mapa = {
        "resumo_pdf": "Resumo de PDF",
        "usar_pdf": "Uso de PDF",
        "latex": "Explicação com LaTeX",
        "visual": "Esquema visual",
        "exercicios": "Exercícios / quiz",
        "correcao": "Correção / feedback",
        "apoio_docente": "Apoio docente",
        "planejamento_docente": "Planejamento docente",
        "pesquisa_docente": "Pesquisa / iniciação científica",
        "explicacao": "Explicação geral",
    }
    return mapa.get(intent, "Explicação geral")


# =========================================================
# PROMPTS
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


def obter_prompt_sistema(intent: str, subject: str) -> str:
    nome = get_first_name(st.session_state.nickname)
    profile = st.session_state.profile

    base = f"""
Você é o MentorEdu IA, um mentor acadêmico institucional do {INSTITUTION_NAME}, ligado ao {PROJECT_NAME} e à {COURSE_NAME}.

Você está atendendo {nome}, no perfil {profile}.
Assunto inferido: {subject}.
Intenção inferida: {intent_label(intent)}.

Responda em português do Brasil.
Seja didático, claro, acolhedor e direto.
Não invente dados, referências ou resultados.
Quando houver matemática, física ou química com fórmulas, use LaTeX válido com $...$ e $$...$$.
Não peça para o usuário configurar funções manualmente; aja como uma IA que interpreta o pedido.
Se houver PDF anexado, use o conteúdo do PDF apenas se ele for relevante ao pedido.
Quando o pedido estiver ambíguo, faça uma suposição razoável e siga.
"""

    if profile == "Aluno":
        base += """
Você está ajudando um estudante.
Priorize:
- explicação clara;
- passo a passo quando necessário;
- erros conceituais comuns;
- exercícios curtos quando fizer sentido;
- linguagem acessível.
"""
    else:
        base += """
Você está ajudando um docente.
Priorize:
- metodologia;
- planejamento;
- criação de questões;
- organização de material;
- análise de desempenho;
- iniciação científica e pesquisa quando apropriado.
"""

    if intent == "resumo_pdf":
        base += """
Tarefa principal: resumir o PDF com clareza, destacando ideias centrais, conceitos-chave e possíveis aplicações.
"""
    elif intent == "usar_pdf":
        base += """
Tarefa principal: usar o PDF como base para explicar, responder ou organizar o conteúdo solicitado.
"""
    elif intent == "latex":
        base += """
Tarefa principal: responder com notação matemática bem formatada e explicações claras.
"""
    elif intent == "visual":
        base += """
Tarefa principal: explicar de forma organizada para facilitar posterior conversão em esquema visual.
"""
    elif intent == "exercicios":
        base += """
Tarefa principal: gerar ou resolver exercícios, com nível adequado e correção comentada quando útil.
"""
    elif intent == "correcao":
        base += """
Tarefa principal: analisar a resposta do usuário, apontar acertos, erros e como melhorar.
"""
    elif intent == "apoio_docente":
        base += """
Tarefa principal: apoiar o professor em tarefas docentes práticas, incluindo médias, notas, correções e organização.
Se o usuário fornecer dados numéricos, analise-os com cuidado e explique o resultado.
"""
    elif intent == "planejamento_docente":
        base += """
Tarefa principal: apoiar planejamento de aula, sequência didática, questões, avaliação e estratégias pedagógicas.
"""
    elif intent == "pesquisa_docente":
        base += """
Tarefa principal: apoiar projeto, artigo, resumo expandido, PIBID, relatório e iniciação científica.
Seja acadêmico, mas claro.
"""

    return base.strip()


def montar_prompt_usuario(pergunta: str, pdf_texto: Optional[str], intent: str, subject: str) -> str:
    partes = [
        f"Perfil do usuário: {st.session_state.profile}",
        f"Nome de preferência: {get_first_name(st.session_state.nickname)}",
        f"Assunto inferido: {subject}",
        f"Intenção inferida: {intent_label(intent)}",
    ]

    historico = formatar_historico_curto(st.session_state.get("chat", []))
    if historico:
        partes.append("Histórico recente:\n" + historico)

    if pdf_texto:
        partes.append("Trecho do PDF para contexto:\n" + pdf_texto[:PDF_CONTEXT_LIMIT])

    partes.append("Pedido atual:\n" + pergunta.strip())
    return "\n\n".join(partes)


def limpar_resposta(texto: str) -> str:
    if not texto:
        return "Não consegui gerar uma resposta útil."

    texto = texto.strip()
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    aberturas = [
        "Claro!",
        "Claro.",
        "Com certeza!",
        "Com certeza.",
        "Vamos lá!",
        "Vamos lá.",
        "Perfeito!",
        "Perfeito.",
        "Aqui está:",
        "Segue abaixo:",
    ]
    for item in aberturas:
        if texto.startswith(item):
            texto = texto[len(item):].strip()

    return texto or "Não consegui gerar uma resposta útil."


def gerar_resposta_groq(prompt_sistema: str, prompt_usuario: str) -> str:
    if client is None:
        return f"Não consegui iniciar a IA. {erro_cliente or ''}".strip()

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
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


def gerar_texto_visual(resposta: str, pergunta: str, subject: str) -> str:
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
Assunto: {subject}
Pedido: {pergunta}

Resposta-base:
{resposta}

Agora gere um esquema visual resumido.
""".strip()

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
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

    subt = f"{st.session_state.profile}"
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
# INPUT
# =========================================================
def render_chat_input():
    try:
        payload = st.chat_input(
            "Escreva sua dúvida ou envie um PDF...",
            accept_file=True,
            file_type=["pdf"],
            key="main_chat_input",
        )
        return payload
    except TypeError:
        st.caption("Seu Streamlit não suporta anexo embutido no chat. Atualize para uma versão mais nova.")
        up = st.file_uploader("Anexe PDF", type=["pdf"], label_visibility="collapsed")
        txt = st.chat_input("Escreva sua dúvida...", key="fallback_chat_input")
        return {"text": txt, "files": [up] if up else []}


# =========================================================
# TELA DE ENTRADA
# =========================================================
def render_login_screen():
    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    st.markdown('<div class="login-center">', unsafe_allow_html=True)
    if os.path.exists(IF_LOGO):
        st.markdown('<div class="login-logo-wrap">', unsafe_allow_html=True)
        st.image(IF_LOGO, width=110)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f'<div class="project-badge">{PROJECT_NAME}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="institution-title">{INSTITUTION_NAME}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="course-title">{COURSE_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-title" style="margin-top:16px;">Como você quer começar?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="small-muted" style="text-align:center; margin-bottom:18px;">Entre primeiro e depois use o chat livremente. O mentor interpreta sua intenção automaticamente.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    nome = st.text_input(
        "Como você quer ser chamado pelo mentor?",
        value=st.session_state.nickname,
        placeholder="Ex.: João, Maria, Professor Roberto...",
    )

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

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-weight:800; margin-bottom:10px; color:#5b473b;">Você é aluno ou professor?</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            <div class="choice-card">
                <div style="font-size:2.1rem;">🎓</div>
                <h3>Aluno</h3>
                <p>Foco em conteúdo, exercícios, revisão, PDF, fórmulas e explicações visuais.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        aluno_click = st.button("Entrar como aluno", use_container_width=True)

    with c2:
        st.markdown(
            """
            <div class="choice-card">
                <div style="font-size:2.1rem;">📘</div>
                <h3>Professor</h3>
                <p>Foco em metodologia, aulas, questões, PDFs, notas, médias e iniciação científica.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        professor_click = st.button("Entrar como professor", use_container_width=True)

    if aluno_click or professor_click:
        nome_limpo = nome.strip()
        if not nome_limpo:
            st.warning("Digite como você quer ser chamado antes de entrar.")
        else:
            st.session_state.nickname = nome_limpo
            st.session_state.profile = "Aluno" if aluno_click else "Professor"
            st.session_state.auth_complete = True
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


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


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    if os.path.exists(IF_LOGO):
        st.markdown('<div class="sidebar-logo-top">', unsafe_allow_html=True)
        st.image(IF_LOGO, width=120)
        st.markdown("</div>", unsafe_allow_html=True)

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

    st.markdown(
        f"""
        <div class="account-card">
            <div class="account-user-row">
                <div class="account-avatar">{apelido[:1].upper()}</div>
                <div>
                    <div class="account-name">{apelido}</div>
                    <div class="account-role">{papel} do IFCE</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Trocar perfil / entrar novamente", use_container_width=True):
        st.session_state.auth_complete = False
        st.rerun()

    st.markdown("---")
    st.markdown("### Conversas")

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

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Nova", use_container_width=True):
            novo_id = create_conversation()
            st.session_state.current_conversation_id = novo_id
            resetar_sessao_visual()
            carregar_conversa_no_estado(novo_id)
            st.rerun()
    with col_b:
        if st.button("Atualizar", use_container_width=True):
            carregar_conversa_no_estado(escolhido_id)
            st.rerun()

    if escolhido_id != st.session_state.current_conversation_id:
        carregar_conversa_no_estado(escolhido_id)
        st.rerun()

    conv = get_conversation(st.session_state.current_conversation_id)
    pdf_name = conv[7] if conv else None
    titulo_atual = conv[1] if conv else ""

    st.markdown("---")
    st.markdown("### Status")
    st.markdown(
        f"""
        <div class="mini-soft-card">
            <div style="font-weight:800; margin-bottom:4px;">PDF ativo</div>
            <div class="small-muted">{pdf_name if pdf_name else 'Nenhum PDF anexado nesta conversa.'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Limpar PDF ativo", use_container_width=True):
        update_conversation_pdf(st.session_state.current_conversation_id, None, None)
        carregar_conversa_no_estado(st.session_state.current_conversation_id)
        st.rerun()

    st.markdown("---")
    st.markdown("### Gerenciar")

    novo_titulo = st.text_input("Renomear conversa", value=titulo_atual)
    if st.button("Salvar nome", use_container_width=True):
        if novo_titulo.strip():
            rename_conversation(st.session_state.current_conversation_id, novo_titulo)
            st.rerun()

    st.session_state.confirm_delete = st.checkbox(
        "Confirmar exclusão",
        value=st.session_state.confirm_delete,
    )

    if st.button("Apagar conversa", use_container_width=True):
        if st.session_state.confirm_delete:
            apagar_id = st.session_state.current_conversation_id
            delete_conversation(apagar_id)
            resetar_sessao_visual()
            restantes = list_conversations()
            novo_atual = restantes[0][0] if restantes else create_conversation()
            st.session_state.current_conversation_id = novo_atual
            carregar_conversa_no_estado(novo_atual)
            st.rerun()
        else:
            st.warning("Marque a confirmação antes de apagar.")


# =========================================================
# TOPO
# =========================================================
descricao = (
    "apoio em conteúdo, exercícios, revisão, PDF e explicações guiadas"
    if st.session_state.profile == "Aluno"
    else "apoio em metodologia, aulas, questões, médias, PDF e iniciação científica"
)

st.markdown(
    f"""
    <div class="hero-card">
        <div class="project-badge">{PROJECT_NAME}</div>
        <div class="hero-title">{APP_NAME}</div>
        <div class="institution-title">{INSTITUTION_NAME}</div>
        <div class="course-title">{COURSE_NAME}</div>
        <div class="hero-subtitle">
            Olá, {get_first_name(st.session_state.nickname)}. Você está no perfil <b>{st.session_state.profile}</b>, com {descricao}.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="painel-card" style="margin-top:16px;">', unsafe_allow_html=True)
st.markdown('<div class="main-title">Como posso te ajudar hoje?</div>', unsafe_allow_html=True)

if st.session_state.profile == "Aluno":
    st.caption("Exemplos: “explique MRU”, “resuma este PDF”, “me dê 5 questões”, “responda com LaTeX”, “faça um esquema visual”.")
else:
    st.caption("Exemplos: “monte um plano de aula”, “crie 10 questões”, “calcule a média destes alunos”, “use este PDF como base”, “me ajude no projeto PIBID”.")

if st.session_state.last_detected_intent or st.session_state.last_detected_subject:
    st.markdown(
        f"""
        <div class="mini-soft-card" style="margin-top:10px;">
            <div style="font-weight:800; margin-bottom:4px;">Leitura atual do mentor</div>
            <div class="small-muted">
                Intenção: {intent_label(st.session_state.last_detected_intent or "explicacao")} •
                Assunto: {st.session_state.last_detected_subject or "—"}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)


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

payload = render_chat_input()

if payload:
    if hasattr(payload, "text"):
        prompt = payload.text
        arquivos = payload.files
    elif isinstance(payload, dict):
        prompt = payload.get("text")
        arquivos = payload.get("files", [])
    else:
        prompt = payload
        arquivos = []

    conv_id = st.session_state.current_conversation_id
    houve_pdf = False

    if arquivos:
        arq = arquivos[0]
        erro_upload = validar_upload(arq)
        if erro_upload:
            st.warning(erro_upload)
        else:
            destino, nome_original = salvar_upload(arq)
            st.session_state.db_texto_pdf = processar_pdf_from_path(destino)
            st.session_state.pdf_nome = nome_original
            update_conversation_pdf(conv_id, destino, nome_original)
            houve_pdf = True
            st.toast(f"PDF ativo: {nome_original}")

    if prompt and prompt.strip():
        if st.session_state.contador_perguntas >= MAX_PERGUNTAS_SESSAO:
            st.warning("Você atingiu o limite de perguntas desta sessão.")
        else:
            pergunta = prompt.strip()
            maybe_update_title_from_first_message(conv_id, pergunta)

            save_message(conv_id, "user", pergunta)
            st.session_state.chat.append({"role": "user", "content": pergunta})
            st.session_state.contador_perguntas += 1

            inferencia = detect_intent(
                texto=pergunta,
                has_pdf=bool(st.session_state.db_texto_pdf) or houve_pdf,
                profile=st.session_state.profile,
            )

            intent = inferencia["intent"]
            subject = inferencia["subject"]

            st.session_state.last_detected_intent = intent
            st.session_state.last_detected_subject = subject

            prompt_sistema = obter_prompt_sistema(intent=intent, subject=subject)
            prompt_usuario = montar_prompt_usuario(
                pergunta=pergunta,
                pdf_texto=st.session_state.db_texto_pdf,
                intent=intent,
                subject=subject,
            )

            with st.spinner("Pensando..."):
                resposta = gerar_resposta_groq(prompt_sistema, prompt_usuario)

            save_message(conv_id, "assistant", resposta)
            st.session_state.chat.append({"role": "assistant", "content": resposta})

            if intent in {"visual"} or "esquema visual" in pergunta.lower():
                try:
                    texto_visual = gerar_texto_visual(resposta, pergunta, subject)
                    titulo_visual = f"{subject} • esquema visual"
                    caminho_img = criar_imagem_esquema(titulo_visual, texto_visual)
                    st.session_state.ultima_imagem_visual = caminho_img
                except Exception:
                    st.session_state.ultima_imagem_visual = None
            else:
                st.session_state.ultima_imagem_visual = None

            st.rerun()

st.caption(f"{APP_NAME} • {PROJECT_NAME} • {INSTITUTION_NAME} • {COURSE_NAME}")
