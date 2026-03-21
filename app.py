import os
import re
import uuid
import sqlite3
from datetime import datetime
from typing import Optional, Tuple, Dict, List

import streamlit as st
from pypdf import PdfReader
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

os.makedirs(UPLOAD_DIR, exist_ok=True)

# =========================================================
# TEMA / ESTILO
# =========================================================
def init_theme_state():
    if "tema_visual" not in st.session_state:
        st.session_state.tema_visual = "Escuro"


def gerar_css_tema(tema: str) -> str:
    if tema == "Claro Creme":
        return """
        <style>
            :root {
                --bg: #f7f3ee;
                --bg-top: #f5efe7;
                --sidebar: #efe6dc;
                --card: #fffdf9;
                --card-2: #f8f1e8;
                --line: #dccfc0;
                --text: #3b312a;
                --muted: #7a6d61;
                --accent: #9a8676;
                --accent-hover: #826f60;
                --badge: #f1e7dc;
                --chip: #f7efe6;
            }

            .stApp {
                background: var(--bg) !important;
            }

            [data-testid="stAppViewContainer"] {
                background: var(--bg) !important;
            }

            [data-testid="stMain"] {
                background: var(--bg) !important;
            }

            [data-testid="stMainBlockContainer"] {
                background: var(--bg) !important;
            }

            .main .block-container {
                background: transparent !important;
            }

            header[data-testid="stHeader"] {
                background: var(--bg-top) !important;
                border-bottom: 1px solid var(--line) !important;
            }

            [data-testid="stToolbar"] {
                background: transparent !important;
            }

            [data-testid="stSidebar"] {
                background: var(--sidebar) !important;
                border-right: 1px solid var(--line) !important;
            }

            [data-testid="stSidebar"] * {
                color: var(--text) !important;
            }

            .hero-card,
            .mentor-card,
            .status-card,
            .mini-card,
            .status-inline,
            .notice-box {
                background: var(--card) !important;
                border: 1px solid var(--line) !important;
                border-radius: 18px !important;
                box-shadow: 0 10px 26px rgba(92, 70, 48, 0.06) !important;
            }

            .folder-hint {
                background: var(--card-2) !important;
                border: 1px solid var(--line) !important;
                border-radius: 14px !important;
                color: var(--muted) !important;
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
                margin-bottom: 10px !important;
            }

            .main-title {
                color: #2f2722 !important;
                font-size: 1.85rem !important;
                font-weight: 800 !important;
                line-height: 1.1 !important;
                margin-bottom: 6px !important;
            }

            .subtitle,
            .small-muted {
                color: var(--muted) !important;
            }

            .chip-wrap {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }

            .if-chip {
                background: var(--chip) !important;
                border: 1px solid var(--line) !important;
                border-radius: 999px !important;
                padding: 7px 12px !important;
                color: var(--text) !important;
                font-size: .87rem !important;
            }

            .notice-box {
                border-left: 4px solid #b59676 !important;
                color: var(--text) !important;
                padding: 12px 14px !important;
                margin-bottom: 12px !important;
            }

            .status-inline {
                color: var(--text) !important;
                padding: 12px 14px !important;
                margin-bottom: 10px !important;
            }

            .stButton > button {
                background: #9a8676 !important;
                color: #fffdfa !important;
                border: 1px solid #9a8676 !important;
                border-radius: 12px !important;
                box-shadow: none !important;
            }

            .stButton > button:hover {# =========================================================
# TEMA / ESTILO
# =========================================================
def init_theme_state():
    if "tema_visual" not in st.session_state:
        st.session_state.tema_visual = "Escuro"


def gerar_css_tema(tema: str) -> str:
    if tema == "Claro Creme":
        return """
        <style>
            :root {
                --bg: #f7f3ee;
                --bg-top: #f5efe7;
                --sidebar: #efe6dc;
                --card: #fffdf9;
                --card-2: #f8f1e8;
                --line: #dccfc0;
                --text: #3b312a;
                --muted: #7a6d61;
                --accent: #9a8676;
                --accent-hover: #826f60;
                --badge: #f1e7dc;
                --chip: #f7efe6;
            }

            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stMain"],
            [data-testid="stMainBlockContainer"] {
                background: var(--bg) !important;
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
            .mentor-card,
            .status-card,
            .mini-card,
            .status-inline,
            .notice-box {
                background: var(--card) !important;
                border: 1px solid var(--line) !important;
                border-radius: 18px !important;
                box-shadow: 0 10px 26px rgba(92, 70, 48, 0.06) !important;
            }

            .folder-hint {
                background: var(--card-2) !important;
                border: 1px solid var(--line) !important;
                border-radius: 14px !important;
                color: var(--muted) !important;
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
                margin-bottom: 10px !important;
            }

            .main-title {
                color: #2f2722 !important;
                font-size: 1.85rem !important;
                font-weight: 800 !important;
                line-height: 1.1 !important;
                margin-bottom: 6px !important;
            }

            .subtitle,
            .small-muted {
                color: var(--muted) !important;
            }

            .chip-wrap {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }

            .if-chip {
                background: var(--chip) !important;
                border: 1px solid var(--line) !important;
                border-radius: 999px !important;
                padding: 7px 12px !important;
                color: var(--text) !important;
                font-size: .87rem !important;
            }

            .notice-box {
                border-left: 4px solid #b59676 !important;
                color: var(--text) !important;
                padding: 12px 14px !important;
                margin-bottom: 12px !important;
            }

            .status-inline {
                color: var(--text) !important;
                padding: 12px 14px !important;
                margin-bottom: 10px !important;
            }

            .stButton > button {
                background: #9a8676 !important;
                color: #fffdfa !important;
                border: 1px solid #9a8676 !important;
                border-radius: 12px !important;
                box-shadow: none !important;
            }

            .stButton > button:hover {
                background: #826f60 !important;
                border-color: #826f60 !important;
            }

            .stTextInput input,
            .stTextArea textarea,
            .stSelectbox div[data-baseweb="select"] > div,
            .stMultiSelect div[data-baseweb="select"] > div {
                background: #fffaf5 !important;
                color: var(--text) !important;
                border: 1px solid var(--line) !important;
            }

            [data-testid="stBottomBlockContainer"] {
                background: var(--bg) !important;
                border-top: 1px solid var(--line) !important;
            }

            [data-testid="stChatInputContainer"] {
                background: var(--bg) !important;
            }

            [data-testid="stChatInputContainer"] > div,
            [data-testid="stChatInput"],
            [data-testid="stChatInput"] > div,
            section[data-testid="stChatInput"] {
                background: #f6efe7 !important;
                border-top: 1px solid var(--line) !important;
            }

            [data-testid="stChatInput"] textarea,
            [data-testid="stChatInput"] input {
                background: #f6efe7 !important;
                color: var(--text) !important;
            }

            [data-testid="stChatInput"] textarea::placeholder,
            [data-testid="stChatInput"] input::placeholder {
                color: var(--muted) !important;
            }

            .stChatMessage {
                background: transparent !important;
            }

            [data-testid="stChatMessageContent"] {
                background: #fffaf5 !important;
                color: var(--text) !important;
                border: 1px solid var(--line) !important;
                border-radius: 14px !important;
            }

            [data-testid="stExpander"] {
                background: var(--card) !important;
                border: 1px solid var(--line) !important;
                border-radius: 14px !important;
            }

            [data-testid="stExpander"] * {
                color: var(--text) !important;
            }
        </style>
        """

    return """
    <style>
        :root {
            --bg: #0d0f12;
            --bg-top: #111317;
            --sidebar: #111317;
            --card: #171a1f;
            --card-2: #14171b;
            --line: #2a2f36;
            --text: #eceff3;
            --muted: #9ca3af;
            --accent: #1b1f25;
            --accent-hover: #252a31;
            --badge: #1a1e24;
            --chip: #181c22;
        }

        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"] {
            background: var(--bg) !important;
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
        .mentor-card,
        .status-card,
        .mini-card,
        .status-inline,
        .notice-box {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 18px;
            box-shadow: 0 14px 30px rgba(0, 0, 0, 0.22);
        }

        .folder-hint {
            background: var(--card-2);
            border: 1px solid var(--line);
            border-radius: 14px;
            color: var(--muted);
        }

        .project-badge {
            display: inline-block;
            background: var(--badge);
            color: #e5e7eb;
            border: 1px solid #303640;
            padding: 6px 12px;
            border-radius: 999px;
            font-size: .88rem;
            font-weight: 700;
            margin-bottom: 10px;
        }

        .main-title {
            color: #f3f4f6;
            font-size: 1.85rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 6px;
        }

        .subtitle,
        .small-muted {
            color: var(--muted) !important;
        }

        .chip-wrap {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .if-chip {
            background: var(--chip);
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 7px 12px;
            color: var(--text);
            font-size: .87rem;
        }

        .notice-box {
            border-left: 4px solid #d1d5db;
            color: var(--text);
            padding: 12px 14px;
            margin-bottom: 12px;
        }

        .status-inline {
            color: var(--text);
            padding: 12px 14px;
            margin-bottom: 10px;
        }

        .stButton > button {
            background: var(--accent) !important;
            color: #f3f4f6 !important;
            border: 1px solid #343a43 !important;
            border-radius: 12px !important;
            box-shadow: none !important;
        }

        .stButton > button:hover {
            background: var(--accent-hover) !important;
            border-color: #434a55 !important;
        }
    </style>
    """


init_theme_state()
st.markdown(gerar_css_tema(st.session_state.tema_visual), unsafe_allow_html=True)

# =========================================================
# LOGIN / AUTENTICAÇÃO
# =========================================================
def exibir_bloco_login_sidebar():
    with st.sidebar:
        try:
            st.markdown("### 👤 Conta")
            if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
                nome = st.user.name.split()[0] if getattr(st.user, "name", None) else "Usuário"
                st.markdown(f"**{nome}**")
                email = getattr(st.user, "email", "")
                if email:
                    st.caption(email)
                if st.button("Sair", use_container_width=True, key="logout_btn"):
                    st.logout()
            else:
                st.caption("Entre com sua conta institucional para personalizar a experiência.")
                if hasattr(st, "login"):
                    if st.button("Entrar com Google", use_container_width=True, key="login_btn"):
                        st.login()
            st.markdown("---")
        except Exception:
            pass


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
            title TEXT NOT NULL DEFAULT 'Nova conversa',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
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
    conn.commit()
    conn.close()


init_db()

# =========================================================
# SESSÃO
# =========================================================
def init_session_state():
    defaults = {
        "chat": [],
        "db_texto_pdf": None,
        "pdf_nome": None,
        "img_nome": None,
        "current_conversation_id": None,
        "loaded_conversation_id": None,
        "confirm_delete": False,
        "contador_perguntas": 0,
        "last_sources": [],
        "pending_prompt": None,
        "perfil_usuario": "Aluno",
        "campus": "IFCE - Geral",
        "curso": "",
        "turma": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session_state()

# =========================================================
# CONVERSAS
# =========================================================
def list_conversations():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, created_at, updated_at, pdf_name, image_name FROM conversations ORDER BY updated_at DESC, id DESC"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_conversation(conversation_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, created_at, updated_at, pdf_path, pdf_name, image_path, image_name FROM conversations WHERE id = ?",
        (conversation_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def create_conversation(title="Nova conversa"):
    now = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO conversations(title, created_at, updated_at) VALUES (?, ?, ?)",
        (title, now, now),
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid


def rename_conversation(conversation_id, title):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
        (title.strip(), datetime.utcnow().isoformat(), conversation_id),
    )
    conn.commit()
    conn.close()


def delete_conversation(conversation_id):
    conv = get_conversation(conversation_id)
    if conv:
        for p in [conv[4], conv[6]]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    cur.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
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


def update_conversation_files(conversation_id, pdf_path=None, pdf_name=None, image_path=None, image_name=None):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        "UPDATE conversations SET pdf_path = ?, pdf_name = ?, image_path = ?, image_name = ?, updated_at = ? WHERE id = ?",
        (pdf_path, pdf_name, image_path, image_name, now, conversation_id),
    )
    conn.commit()
    conn.close()


def maybe_update_title_from_first_message(conversation_id, text):
    texto = (text or "").strip()
    if not texto:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT title FROM conversations WHERE id = ?", (conversation_id,))
    row = cur.fetchone()
    if row and row[0] == "Nova conversa":
        title = re.sub(r"\s+", " ", texto.replace("\n", " ")).strip()[:72]
        cur.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, datetime.utcnow().isoformat(), conversation_id),
        )
        conn.commit()
    conn.close()


def resetar_sessao_visual():
    st.session_state.chat = []
    st.session_state.db_texto_pdf = None
    st.session_state.pdf_nome = None
    st.session_state.img_nome = None
    st.session_state.last_sources = []
    st.session_state.contador_perguntas = 0


def carregar_conversa_no_estado(conversation_id):
    conv = get_conversation(conversation_id)
    if not conv:
        return
    _, _, _, _, pdf_path, pdf_name, image_path, image_name = conv
    st.session_state.chat = [{"role": role, "content": content} for role, content, _ in get_messages(conversation_id)]
    st.session_state.pdf_nome = pdf_name
    st.session_state.img_nome = image_name
    st.session_state.current_conversation_id = conversation_id
    st.session_state.loaded_conversation_id = conversation_id
    st.session_state.last_sources = []
    st.session_state.confirm_delete = False
    if pdf_path and os.path.exists(pdf_path):
        st.session_state.db_texto_pdf = processar_pdf_from_path(pdf_path)
    else:
        st.session_state.db_texto_pdf = None


def formatar_conversation_label(row):
    conv_id, title, _, _, pdf_name, image_name = row
    extras = []
    if pdf_name:
        extras.append("PDF")
    if image_name:
        extras.append("IMG")
    suffix = f" [{' | '.join(extras)}]" if extras else ""
    return f"{title}{suffix}"


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
# PERFIS / MENTORES / SERVIÇOS
# =========================================================
def obter_estrutura_mentores() -> Dict[str, Dict[str, List[str]]]:
    base = {
        "Física": ["Didático", "Feynman", "GrokFísica"],
        "Química": ["Didático", "Vestibular", "Laboratório"],
        "Matemática": ["Didático", "Objetivo", "Rigoroso"],
        "Programação": ["Didático", "Prático", "Monitor"],
        "Redação": ["Didático", "Acadêmico", "Vestibular"],
        "Metodologia Científica": ["Acadêmico", "Didático", "Orientador"],
    }
    return {
        "Ensino Médio": {"disciplinas": base},
        "Ensino Superior": {"disciplinas": base},
    }


def obter_servicos_por_perfil(perfil: str) -> List[str]:
    if perfil == "Professor":
        return [
            "Atendimento Geral",
            "Planejamento de Aula",
            "Criar Lista de Exercícios",
            "Montar Avaliação",
            "Gerar Rubrica",
            "Escrever Aviso Institucional",
            "Resumir PDF/Plano",
        ]
    return [
        "Atendimento Geral",
        "Estudo Guiado",
        "Explicação Passo a Passo",
        "Resumo de PDF",
        "Preparação para Prova",
        "Correção de Redação",
        "Dúvidas de Programação",
    ]


def resumo_mentor(nivel, disciplina, estilo):
    return f"{nivel} • {disciplina} • {estilo}: explicação clara, progressiva e adaptada ao contexto do IFCE."


def construir_contexto_institucional() -> str:
    perfil = st.session_state.get("perfil_usuario", "Aluno")
    campus = st.session_state.get("campus", "IFCE - Geral")
    curso = st.session_state.get("curso", "")
    turma = st.session_state.get("turma", "")
    return (
        f"Contexto institucional: perfil={perfil}; instituição=IFCE; campus={campus}; "
        f"curso={curso or 'não informado'}; turma={turma or 'não informada'}."
    )


def obter_prompt_mentor_especializado(nivel, disciplina, estilo, perfil, servico):
    base = (
        f"Você é um assistente acadêmico institucional do IFCE. "
        f"Atende principalmente o perfil {perfil}. "
        f"Atue como mentor especializado em {disciplina} para {nivel}, com estilo {estilo}. "
        "Responda sempre em português do Brasil, com clareza, organização e tom respeitoso. "
        "Quando houver cálculo, mostre passos. Quando houver teoria, resuma ideias-chave antes de aprofundar. "
        "Se o pedido envolver rotina escolar ou universitária, proponha passos concretos e realistas. "
        "Não invente normas internas específicas do IFCE; quando algo institucional depender de regulamento local, deixe isso explícito. "
        f"Serviço selecionado no momento: {servico}."
    )

    if perfil == "Professor":
        base += " Dê suporte pedagógico, planejamento, avaliação, comunicação com turma e organização de aula."
    else:
        base += " Dê suporte a estudo, revisão, compreensão conceitual, organização acadêmica e desempenho em atividades."

    if estilo == "Feynman":
        base += " Simplifique ideias difíceis sem perder a precisão."
    elif estilo == "GrokFísica":
        base += " Use humor leve, mas mantenha o rigor conceitual."
    elif estilo == "Rigoroso":
        base += " Priorize precisão formal, definições e justificativas."
    elif estilo == "Monitor":
        base += " Responda como um monitor paciente e prático."

    if servico == "Planejamento de Aula":
        base += " Estruture objetivos, habilidades, metodologia, recursos e avaliação."
    elif servico == "Criar Lista de Exercícios":
        base += " Gere itens progressivos, do básico ao aplicado, com gabarito ao final quando pedido."
    elif servico == "Montar Avaliação":
        base += " Monte avaliação equilibrada com nível, critérios e distribuição de dificuldade."
    elif servico == "Gerar Rubrica":
        base += " Produza critérios claros, níveis de desempenho e descritores observáveis."
    elif servico == "Estudo Guiado":
        base += " Organize um roteiro de estudo por etapas, com metas e checkpoints."
    elif servico == "Preparação para Prova":
        base += " Priorize revisão estratégica, tópicos-chave, treino e gestão de tempo."
    elif servico == "Correção de Redação":
        base += " Avalie estrutura, coesão, argumentação, gramática e sugestões de melhoria."
    elif servico == "Dúvidas de Programação":
        base += " Explique o código, a lógica e os erros de forma prática e testável."

    return base


def gerar_sugestoes_rapidas(perfil: str) -> List[str]:
    if perfil == "Professor":
        return [
            "Monte um plano de aula de 50 minutos sobre MRU para 1º ano.",
            "Crie uma rubrica simples para seminário em grupo.",
            "Escreva um aviso formal para a turma sobre entrega de atividade.",
            "Gere 10 questões objetivas com gabarito sobre ligações químicas.",
        ]
    return [
        "Explique função horária do espaço com exemplo.",
        "Monte um plano de estudo para prova amanhã.",
        "Resuma este PDF em tópicos para revisão.",
        "Corrija meu raciocínio nesta questão passo a passo.",
    ]


# =========================================================
# PROCESSAMENTO DE ARQUIVOS
# =========================================================
def salvar_upload(uploaded_file) -> Tuple[str, str]:
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    destino = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(destino, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return destino, uploaded_file.name


def processar_pdf_from_path(pdf_path: str) -> Optional[str]:
    try:
        reader = PdfReader(pdf_path)
        textos = []
        for page in reader.pages:
            txt = page.extract_text() or ""
            if txt.strip():
                textos.append(txt)
        conteudo = "\n\n".join(textos).strip()
        return conteudo if conteudo else None
    except Exception:
        return None


def ler_imagem_resumo(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        return f"Imagem carregada com sucesso. Resolução: {img.size[0]}x{img.size[1]}. Formato: {img.format or 'desconhecido'}."
    except Exception:
        return "Imagem carregada com sucesso."


def extrair_contexto_ativo(conversation_id):
    conv = get_conversation(conversation_id)
    if not conv:
        return None, None, None, None
    return conv[4], conv[5], conv[6], conv[7]


# =========================================================
# PROMPTS
# =========================================================
def pode_perguntar():
    return st.session_state.contador_perguntas < MAX_PERGUNTAS_SESSAO


def bloco_servico_extra(servico: str) -> str:
    regras = {
        "Planejamento de Aula": "Entregue em blocos: objetivo geral, objetivos específicos, conteúdos, metodologia, recursos e avaliação.",
        "Criar Lista de Exercícios": "Monte exercícios graduais; se pertinente, inclua gabarito separado no final.",
        "Montar Avaliação": "Distribua dificuldade e sinalize o que avalia em cada questão.",
        "Gerar Rubrica": "Use tabela textual clara com critérios e níveis de desempenho.",
        "Escrever Aviso Institucional": "Use linguagem formal, clara e respeitosa.",
        "Estudo Guiado": "Entregue como roteiro de estudo em etapas curtas e realistas.",
        "Preparação para Prova": "Comece pelo que mais cai, depois vá para treino e revisão final.",
        "Correção de Redação": "Aponte pontos fortes, problemas e uma versão melhorada de trechos-chave.",
        "Dúvidas de Programação": "Explique o erro, mostre a correção e justifique a mudança.",
    }
    return regras.get(servico, "")


def montar_prompt_usuario(
    pergunta: str,
    modo: str,
    servico: str,
    pdf_path: Optional[str],
    pdf_name: Optional[str],
    image_path: Optional[str],
    image_name: Optional[str],
):
    partes = [
        construir_contexto_institucional(),
        f"Modo selecionado: {modo}",
        f"Serviço selecionado: {servico}",
        f"Pergunta do usuário: {pergunta.strip()}",
    ]

    regra_extra = bloco_servico_extra(servico)
    if regra_extra:
        partes.append(regra_extra)

    if pdf_path and os.path.exists(pdf_path):
        texto_pdf = st.session_state.get("db_texto_pdf")
        if texto_pdf:
            partes.append(f"PDF ativo: {pdf_name}")
            partes.append("Trecho do PDF para contexto:\n" + texto_pdf[:18000])

    if image_path and os.path.exists(image_path):
        partes.append(f"Imagem ativa: {image_name}")
        partes.append(ler_imagem_resumo(image_path))
        partes.append(
            "Se a pergunta depender de leitura visual detalhada da imagem, responda com cautela e explicite qualquer limitação."
        )

    if modo == "Análise de Conteúdo":
        partes.append("Priorize resumo, interpretação, comparação e explicação do material anexado.")
    elif modo == "Matemática":
        partes.append("Resolva passo a passo. Use LaTeX quando útil, com $...$ para inline e $$...$$ para destaque.")
    elif modo == "Chat Criativo":
        partes.append("Pode responder de forma mais criativa, porém ainda útil e informativa.")
    elif modo == "GrokFísica (zoeira + didática)":
        partes.append("Use humor leve, sem perder didática e correção conceitual.")

    return "\n\n".join(partes)


def gerar_resposta_groq(prompt_sistema: str, prompt_usuario: str) -> str:
    if client is None:
        return f"Não consegui iniciar a IA. {erro_cliente or ''}".strip()
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
            temperature=0.45,
            max_tokens=1600,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Ocorreu um erro ao gerar a resposta: {e}"


# =========================================================
# CHAT INPUT COM ANEXO
# =========================================================
def render_chat_input():
    try:
        payload = st.chat_input(
            "Digite sua pergunta...",
            accept_file=True,
            file_type=["pdf", "png", "jpg", "jpeg"],
            key="main_chat_input",
        )
        return payload
    except TypeError:
        st.caption(
            "Seu Streamlit não suporta anexo embutido no chat. Atualize para uma versão mais nova para usar o botão + dentro da caixa."
        )
        up = st.file_uploader("Anexe PDF ou imagem", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed")
        txt = st.chat_input("Digite sua pergunta...", key="fallback_chat_input")
        return {"text": txt, "files": [up] if up else []}


# =========================================================
# ESTADO INICIAL
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
exibir_bloco_login_sidebar()

st.markdown("### Aparência")
novo_tema = st.radio(
    "Tema",
    ["Escuro", "Claro Creme"],
    index=0 if st.session_state.tema_visual == "Escuro" else 1,
    key="tema_radio",
)

if novo_tema != st.session_state.tema_visual:
    st.session_state.tema_visual = novo_tema
    st.rerun()

st.markdown("---")
    if os.path.exists(IF_LOGO):
        st.image(IF_LOGO, use_container_width=True)

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
    st.markdown("### Perfil institucional")
    st.session_state.perfil_usuario = st.radio(
        "Quem está usando?",
        ["Aluno", "Professor"],
        index=0 if st.session_state.perfil_usuario == "Aluno" else 1,
    )
    campus_options = ["IFCE - Geral", "Fortaleza", "Maracanaú", "Sobral", "Juazeiro do Norte", "Outro"]
    campus_index = campus_options.index(st.session_state.campus) if st.session_state.campus in campus_options else 0
    st.session_state.campus = st.selectbox("Campus / unidade", campus_options, index=campus_index)
    st.session_state.curso = st.text_input("Curso", value=st.session_state.curso, placeholder="Ex.: Licenciatura em Física")
    st.session_state.turma = st.text_input("Turma / semestre", value=st.session_state.turma, placeholder="Ex.: 1º semestre / 2º ano B")

    st.markdown("---")
    st.markdown("### Escolha seu Mentor")
    st.markdown(
        "<div class='folder-hint'>Escolha o <b>nível</b>, a <b>disciplina</b>, o <b>estilo</b> e o <b>tipo de atendimento</b>.</div>",
        unsafe_allow_html=True,
    )
    estrutura = obter_estrutura_mentores()
    nivel_escolhido = st.radio("Nível de ensino", ["Ensino Médio", "Ensino Superior"])
    disciplinas = list(estrutura[nivel_escolhido]["disciplinas"].keys())
    disciplina_escolhida = st.selectbox("Disciplina", disciplinas)
    estilos = estrutura[nivel_escolhido]["disciplinas"][disciplina_escolhida]
    estilo_escolhido = st.radio("Estilo do professor", estilos)
    servicos = obter_servicos_por_perfil(st.session_state.perfil_usuario)
    servico_escolhido = st.selectbox("Tipo de atendimento", servicos)

    st.markdown(
        f"""
        <div class="mentor-card" style="padding:14px; margin-top:10px;">
            <h4 style="margin:0 0 6px 0;">{disciplina_escolhida} • {estilo_escolhido}</h4>
            <p style="margin:0;">{resumo_mentor(nivel_escolhido, disciplina_escolhida, estilo_escolhido)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    modo = st.selectbox(
        "Modo de trabalho",
        ["Chat Geral", "Análise de Conteúdo", "Matemática", "Chat Criativo", "GrokFísica (zoeira + didática)"],
    )

    st.markdown("---")
    st.markdown("### Ferramentas rápidas")
    if st.button("Inserir prompt de plano de aula", use_container_width=True):
        st.session_state.pending_prompt = "Monte um plano de aula completo sobre o tema abaixo, com objetivos, metodologia, recursos e avaliação: "
    if st.button("Inserir prompt de estudo guiado", use_container_width=True):
        st.session_state.pending_prompt = "Monte um estudo guiado com etapas, metas e revisão final sobre o conteúdo: "
    if st.button("Inserir prompt de resumo institucional", use_container_width=True):
        st.session_state.pending_prompt = "Resuma este material em linguagem clara, com tópicos, destaques e possíveis aplicações em sala: "

    st.markdown("---")
    st.markdown("### Estado da sessão")
    conv = get_conversation(st.session_state.current_conversation_id)
    pdf_name = conv[5] if conv else None
    image_name = conv[7] if conv else None
    st.markdown(
        f"""
        <div class="status-card" style="padding:14px; margin-top:10px;">
            <div><b>Perguntas</b></div>
            <div>{st.session_state.contador_perguntas}/{MAX_PERGUNTAS_SESSAO}</div>
            <hr style="margin:10px 0; border:none; border-top:1px solid #2a313b;">
            <div><b>PDF ativo</b></div>
            <div>{pdf_name if pdf_name else 'Nenhum'}</div>
            <hr style="margin:10px 0; border:none; border-top:1px solid #2a313b;">
            <div><b>Imagem ativa</b></div>
            <div>{image_name if image_name else 'Nenhuma'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Limpar anexos da conversa", use_container_width=True):
        update_conversation_files(st.session_state.current_conversation_id, None, None, None, None)
        carregar_conversa_no_estado(st.session_state.current_conversation_id)
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
        value=st.session_state.confirm_delete,
    )
    if st.button("Apagar conversa atual", use_container_width=True):
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
            
st.markdown(gerar_css_tema(st.session_state.tema_visual), unsafe_allow_html=True)

# =========================================================
# CABEÇALHO / PRINCIPAL
# =========================================================
prompt_sistema_ativo = obter_prompt_mentor_especializado(
    nivel_escolhido,
    disciplina_escolhida,
    estilo_escolhido,
    st.session_state.perfil_usuario,
    servico_escolhido,
)

st.markdown(
    f"""
    <div class="hero-card" style="padding: 18px 22px; margin-bottom: 12px;">
        <div style="text-align:center;">
            <div class="project-badge">{PROJECT_NAME}</div>
            <div class="main-title">{APP_NAME}</div>
            <div class="subtitle">IA institucional para apoio a alunos e professores do IFCE.</div>
            <div class="chip-wrap" style="justify-content:center; margin-top:10px;">
                <span class="if-chip">Aluno + Professor</span>
                <span class="if-chip">PDF + imagem</span>
                <span class="if-chip">Planos e avaliações</span>
                <span class="if-chip">Mentoria por disciplina</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"<div class='notice-box'><b>Perfil ativo:</b> {st.session_state.perfil_usuario} • <b>Campus:</b> {st.session_state.campus} • <b>Atendimento:</b> {servico_escolhido}</div>",
    unsafe_allow_html=True,
)

conv = get_conversation(st.session_state.current_conversation_id)
pdf_name = conv[5] if conv else None
image_name = conv[7] if conv else None
status_arquivo = f"📄 PDF ativo: {pdf_name}" if pdf_name else (f"🖼️ Imagem ativa: {image_name}" if image_name else "Sem anexo ativo")
st.markdown(f"<div class='status-inline'><b>Status:</b> {status_arquivo}</div>", unsafe_allow_html=True)

st.markdown("### Atalhos úteis")
col1, col2 = st.columns(2)
with col1:
    if st.button("Explicar conteúdo passo a passo", use_container_width=True):
        st.session_state.pending_prompt = "Explique passo a passo o seguinte conteúdo: "
        st.rerun()
    if st.button("Resumir PDF em tópicos", use_container_width=True):
        st.session_state.pending_prompt = "Resuma este material em tópicos claros para revisão: "
        st.rerun()
with col2:
    if st.button("Montar plano de estudo", use_container_width=True):
        st.session_state.pending_prompt = "Monte um plano de estudo objetivo sobre: "
        st.rerun()
    if st.button("Criar atividade ou lista", use_container_width=True):
        st.session_state.pending_prompt = "Crie uma lista de exercícios sobre: "
        st.rerun()

with st.expander("Como usar o MentorEdu"):
    st.markdown(
        """
- Escolha o **perfil**, o **mentor** e o **tipo de atendimento** na esquerda.
- Use a caixa de mensagem no rodapé.
- Clique no **+** para anexar **PDF** ou **imagem**.
- Peça resumos, questões, planos de aula, rubricas, revisões, correções e explicações.
        """
    )

# =========================================================
# HISTÓRICO DO CHAT
# =========================================================
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =========================================================
# ENTRADA DO USUÁRIO
# =========================================================
if st.session_state.pending_prompt:
    st.info(f"Sugestão pronta para usar: {st.session_state.pending_prompt}")

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

    if st.session_state.pending_prompt and prompt:
        prompt = f"{st.session_state.pending_prompt}{prompt}"
        st.session_state.pending_prompt = None

    conv_id = st.session_state.current_conversation_id

    if arquivos:
        arq = arquivos[0]
        destino, nome_original = salvar_upload(arq)
        nome_lower = arq.name.lower()
        if nome_lower.endswith(".pdf"):
            st.session_state.db_texto_pdf = processar_pdf_from_path(destino)
            st.session_state.pdf_nome = nome_original
            update_conversation_files(conv_id, destino, nome_original, None, None)
        elif nome_lower.endswith((".png", ".jpg", ".jpeg")):
            st.session_state.img_nome = nome_original
            update_conversation_files(conv_id, None, None, destino, nome_original)

    if prompt and prompt.strip():
        if not pode_perguntar():
            st.warning("Você atingiu o limite de perguntas desta sessão.")
        else:
            pergunta = prompt.strip()
            maybe_update_title_from_first_message(conv_id, pergunta)
            save_message(conv_id, "user", pergunta)
            st.session_state.chat.append({"role": "user", "content": pergunta})
            st.session_state.contador_perguntas += 1

            pdf_path, pdf_name, image_path, image_name = extrair_contexto_ativo(conv_id)
            prompt_usuario = montar_prompt_usuario(
                pergunta,
                modo,
                servico_escolhido,
                pdf_path,
                pdf_name,
                image_path,
                image_name,
            )

            with st.spinner("Pensando..."):
                resposta = gerar_resposta_groq(prompt_sistema_ativo, prompt_usuario)

            save_message(conv_id, "assistant", resposta)
            st.session_state.chat.append({"role": "assistant", "content": resposta})
            st.rerun()

# =========================================================
# RODAPÉ
# =========================================================
st.caption(
    "MentorEdu IFCE: interface focada no chat, com apoio institucional para alunos e professores e compatibilidade com seu fluxo de login."
)
