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
# CONFIG
# =========================================================
st.set_page_config(
    page_title="MentorEdu IFCE",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "MentorEdu IFCE"
IF_LOGO = "logo.png"
DB_PATH = "mentoredu.db"
UPLOAD_DIR = "uploads"
MAX_PDF_MB = 15
MAX_IMG_MB = 8
MAX_PERGUNTAS_SESSAO = 40
PDF_CONTEXT_LIMIT = 6000
CHAT_HISTORY_FOR_PROMPT = 6
DEFAULT_MODEL = "llama-3.3-70b-versatile"

os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================================================
# TEMA
# =========================================================
def init_theme_state():
    if "tema_visual" not in st.session_state:
        st.session_state.tema_visual = "Escuro"


def gerar_css_tema(tema: str) -> str:
    if tema == "Claro Creme":
        return """
        <style>
            :root {
                --bg: #f6f1ea;
                --sidebar: #efe6db;
                --card: #fffdf9;
                --line: #d9ccbe;
                --text: #332b25;
                --muted: #75685d;
                --primary: #6c8c55;
                --primary-hover: #5d7949;
                --chip: #f7efe5;
                --user: #ebe3d8;
                --assistant: #fffaf3;
            }
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
                background: var(--bg) !important;
            }
            [data-testid="stSidebar"] {
                background: var(--sidebar) !important;
                border-right: 1px solid var(--line) !important;
            }
            [data-testid="stSidebar"] * {
                color: var(--text) !important;
            }
            [data-testid="stChatMessageContent"] {
                color: var(--text) !important;
                border-radius: 16px !important;
                border: 1px solid var(--line) !important;
            }
            .stChatMessage:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
                background: var(--user) !important;
            }
            .stChatMessage:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
                background: var(--assistant) !important;
            }
            .panel-card {
                background: var(--card);
                border: 1px solid var(--line);
                border-radius: 18px;
                padding: 14px;
                margin-bottom: 12px;
            }
            .small-muted { color: var(--muted) !important; }
            .chip {
                display: inline-block;
                padding: 6px 10px;
                border-radius: 999px;
                background: var(--chip);
                border: 1px solid var(--line);
                font-size: .85rem;
                margin: 3px 6px 3px 0;
            }
            .stButton > button {
                background: var(--primary) !important;
                color: white !important;
                border: 1px solid var(--primary) !important;
                border-radius: 12px !important;
            }
            .stButton > button:hover {
                background: var(--primary-hover) !important;
                border-color: var(--primary-hover) !important;
            }
            .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
                background: #fffaf4 !important;
                color: var(--text) !important;
                border: 1px solid var(--line) !important;
            }
            [data-testid="stChatInput"] textarea, [data-testid="stChatInput"] input {
                color: var(--text) !important;
            }
            p, span, div, label, li { color: var(--text) !important; }
        </style>
        """

    return """
    <style>
        :root {
            --bg: #0d1117;
            --sidebar: #111827;
            --card: #151c24;
            --line: #2a3441;
            --text: #edf2f7;
            --muted: #9aa7b6;
            --primary: #3f8f5b;
            --primary-hover: #34774b;
            --chip: #18212b;
            --user: #1b2530;
            --assistant: #121923;
        }
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
            background: var(--bg) !important;
        }
        [data-testid="stSidebar"] {
            background: var(--sidebar) !important;
            border-right: 1px solid var(--line) !important;
        }
        [data-testid="stSidebar"] * {
            color: var(--text) !important;
        }
        [data-testid="stChatMessageContent"] {
            color: var(--text) !important;
            border-radius: 16px !important;
            border: 1px solid var(--line) !important;
        }
        .stChatMessage:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
            background: var(--user) !important;
        }
        .stChatMessage:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
            background: var(--assistant) !important;
        }
        .panel-card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 14px;
            margin-bottom: 12px;
        }
        .small-muted { color: var(--muted) !important; }
        .chip {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            background: var(--chip);
            border: 1px solid var(--line);
            font-size: .85rem;
            margin: 3px 6px 3px 0;
        }
        .stButton > button {
            background: var(--primary) !important;
            color: white !important;
            border: 1px solid var(--primary) !important;
            border-radius: 12px !important;
        }
        .stButton > button:hover {
            background: var(--primary-hover) !important;
            border-color: var(--primary-hover) !important;
        }
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
            background: #101720 !important;
            color: var(--text) !important;
            border: 1px solid var(--line) !important;
        }
        [data-testid="stChatInput"] textarea, [data-testid="stChatInput"] input {
            color: var(--text) !important;
        }
        p, span, div, label, li { color: var(--text) !important; }
    </style>
    """


init_theme_state()
st.markdown(gerar_css_tema(st.session_state.tema_visual), unsafe_allow_html=True)


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
    st.session_state.contador_perguntas = 0
    st.session_state.confirm_delete = False


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
        return None, "A chave GROQ_API_KEY não foi encontrada nos Secrets."
    try:
        return Groq(api_key=chave), None
    except Exception as e:
        return None, f"Erro ao iniciar cliente Groq: {e}"


client, erro_cliente = carregar_cliente()


# =========================================================
# CONFIG DIDÁTICA
# =========================================================
def obter_estrutura_mentores() -> Dict[str, Dict[str, List[str]]]:
    base = {
        "Física": ["Didático", "Feynman", "Rigoroso"],
        "Química": ["Didático", "Vestibular", "Laboratório"],
        "Matemática": ["Didático", "Objetivo", "Rigoroso"],
        "Programação": ["Didático", "Prático", "Monitor"],
        "Redação": ["Didático", "Acadêmico", "Vestibular"],
        "Metodologia Científica": ["Didático", "Acadêmico", "Orientador"],
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
    return f"{nivel} • {disciplina} • {estilo}: explicação curta, clara e focada no que realmente ajuda."


def gerar_sugestoes_rapidas(perfil: str) -> List[str]:
    if perfil == "Professor":
        return [
            "Monte um plano de aula de 50 minutos sobre MRU.",
            "Crie uma rubrica simples para apresentação em grupo.",
            "Escreva um aviso formal para a turma.",
        ]
    return [
        "Explique função horária do espaço com exemplo.",
        "Monte um plano de estudo para prova amanhã.",
        "Resuma este PDF em tópicos para revisão.",
    ]


def formatar_historico_curto(chat: List[Dict[str, str]], limite: int = CHAT_HISTORY_FOR_PROMPT) -> str:
    if not chat:
        return ""
    blocos = []
    for msg in chat[-limite:]:
        papel = "Usuário" if msg["role"] == "user" else "Assistente"
        texto = (msg["content"] or "").strip()
        if texto:
            blocos.append(f"{papel}: {texto[:700]}")
    return "\n".join(blocos)


def construir_contexto_institucional() -> str:
    perfil = st.session_state.get("perfil_usuario", "Aluno")
    campus = st.session_state.get("campus", "IFCE - Geral")
    curso = st.session_state.get("curso", "")
    turma = st.session_state.get("turma", "")
    return (
        f"Perfil={perfil}; Instituição=IFCE; Campus={campus}; "
        f"Curso={curso or 'não informado'}; Turma={turma or 'não informada'}."
    )


def bloco_servico_extra(servico: str) -> str:
    regras = {
        "Planejamento de Aula": "Entregue em: objetivo, conteúdos, metodologia, recursos e avaliação.",
        "Criar Lista de Exercícios": "Crie exercícios em ordem crescente de dificuldade.",
        "Montar Avaliação": "Monte uma avaliação equilibrada e objetiva.",
        "Gerar Rubrica": "Use critérios claros e níveis de desempenho.",
        "Escrever Aviso Institucional": "Use linguagem formal e direta.",
        "Estudo Guiado": "Entregue em etapas curtas, com metas realistas.",
        "Preparação para Prova": "Comece pelo que mais cai e feche com revisão.",
        "Correção de Redação": "Aponte pontos fortes, problemas e melhorias.",
        "Dúvidas de Programação": "Explique erro, causa, correção e código final.",
        "Resumo de PDF": "Resuma em tópicos, sem copiar trechos longos.",
        "Resumir PDF/Plano": "Resuma em tópicos, com foco prático.",
    }
    return regras.get(servico, "")


def obter_prompt_mentor_especializado(nivel, disciplina, estilo, perfil, servico):
    partes = [
        "Você é um mentor acadêmico do IFCE.",
        "Responda sempre em português do Brasil.",
        "Seja direto, claro e didático.",
        "Evite introduções longas, repetições, autoexplicações e informações óbvias.",
        "Prefira frases curtas e blocos organizados.",
        "Quando a pergunta for simples, responda de forma simples.",
        "Quando houver cálculo, mostre apenas os passos necessários.",
        "Quando houver teoria, comece com a ideia principal e depois explique.",
        "Não invente regras internas do IFCE.",
        "Se não tiver certeza de algo institucional, diga isso claramente.",
        "Formato preferido: resposta direta, explicação curta, exemplo breve se necessário.",
        f"Contexto atual: perfil={perfil}; nível={nivel}; disciplina={disciplina}; estilo={estilo}; serviço={servico}.",
    ]

    if estilo == "Feynman":
        partes.append("Explique como se estivesse ensinando alguém inteligente que está vendo o assunto pela primeira vez.")
    elif estilo == "Rigoroso":
        partes.append("Priorize precisão conceitual e justificativas bem fundamentadas.")
    elif estilo == "Monitor":
        partes.append("Explique como um monitor paciente e prático.")
    elif estilo == "Objetivo":
        partes.append("Vá direto ao ponto.")
    elif estilo == "Prático":
        partes.append("Dê exemplos rápidos e úteis.")

    extra = bloco_servico_extra(servico)
    if extra:
        partes.append(extra)

    return " ".join(partes)


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
        f"Contexto institucional: {construir_contexto_institucional()}",
        f"Modo: {modo}",
        f"Serviço: {servico}",
    ]

    historico = formatar_historico_curto(st.session_state.get("chat", []))
    if historico:
        partes.append("Histórico recente da conversa:\n" + historico)

    partes.append("Pergunta atual:\n" + pergunta.strip())

    if pdf_path and os.path.exists(pdf_path):
        texto_pdf = st.session_state.get("db_texto_pdf")
        if texto_pdf:
            partes.append(f"PDF ativo: {pdf_name}")
            partes.append("Use o PDF apenas se ele for relevante para responder.")
            partes.append("Trecho do PDF:\n" + texto_pdf[:PDF_CONTEXT_LIMIT])

    if image_path and os.path.exists(image_path):
        partes.append(f"Imagem ativa: {image_name}")
        partes.append(ler_imagem_resumo(image_path))
        partes.append("Só comente a imagem se isso for necessário para a resposta.")

    if modo == "Matemática":
        partes.append("Resolva passo a passo e destaque a fórmula principal.")
    elif modo == "Análise de Conteúdo":
        partes.append("Priorize resumo, explicação e tópicos-chave.")
    elif modo == "Chat Criativo":
        partes.append("Pode ser um pouco mais criativo, mas continue útil e claro.")

    return "\n\n".join(partes)


def limpar_resposta(texto: str) -> str:
    if not texto:
        return "Não consegui gerar uma resposta útil."

    texto = texto.strip()
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    trocas = {
        "Claro!": "",
        "Com certeza!": "",
        "Vamos lá!": "",
        "Segue abaixo": "",
        "Aqui está": "",
    }
    for origem, destino in trocas.items():
        texto = texto.replace(origem, destino).strip()

    return texto


def gerar_resposta_groq(prompt_sistema: str, prompt_usuario: str) -> str:
    if client is None:
        return f"Não consegui iniciar a IA. {erro_cliente or ''}".strip()

    try:
        resp = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
            temperature=0.35,
            max_tokens=1100,
        )
        conteudo = resp.choices[0].message.content.strip()
        return limpar_resposta(conteudo)
    except Exception as e:
        return f"Ocorreu um erro ao gerar a resposta: {e}"


# =========================================================
# ARQUIVOS
# =========================================================
def tamanho_mb(uploaded_file) -> float:
    return round(len(uploaded_file.getbuffer()) / (1024 * 1024), 2)


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
            txt = re.sub(r"\s+", " ", txt).strip()
            if txt:
                textos.append(txt)
        conteudo = "\n\n".join(textos).strip()
        return conteudo if conteudo else None
    except Exception:
        return None


def ler_imagem_resumo(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        return f"Imagem carregada. Resolução: {img.size[0]}x{img.size[1]}. Formato: {img.format or 'desconhecido'}."
    except Exception:
        return "Imagem carregada."


def extrair_contexto_ativo(conversation_id):
    conv = get_conversation(conversation_id)
    if not conv:
        return None, None, None, None
    return conv[4], conv[5], conv[6], conv[7]


def validar_upload(uploaded_file) -> Optional[str]:
    nome = uploaded_file.name.lower()
    mb = tamanho_mb(uploaded_file)
    if nome.endswith(".pdf") and mb > MAX_PDF_MB:
        return f"O PDF excede o limite de {MAX_PDF_MB} MB."
    if nome.endswith((".png", ".jpg", ".jpeg")) and mb > MAX_IMG_MB:
        return f"A imagem excede o limite de {MAX_IMG_MB} MB."
    return None


# =========================================================
# INPUT
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
        up = st.file_uploader("Anexe PDF ou imagem", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed")
        txt = st.chat_input("Digite sua pergunta...", key="fallback_chat_input")
        return {"text": txt, "files": [up] if up else []}


# =========================================================
# LOGIN
# =========================================================
def exibir_bloco_login_sidebar():
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
            st.caption("Faça login para personalizar a experiência.")
            if hasattr(st, "login"):
                if st.button("Entrar com Google", use_container_width=True, key="login_btn"):
                    st.login()
        st.markdown("---")
    except Exception:
        pass


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
with st.sidebar:
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
        st.session_state.current_conversation_id = escolhido_id
        carregar_conversa_no_estado(escolhido_id)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Nova", use_container_width=True):
            novo_id = create_conversation()
            st.session_state.current_conversation_id = novo_id
            resetar_sessao_visual()
            carregar_conversa_no_estado(novo_id)
            st.rerun()
    with c2:
        if st.button("Atualizar", use_container_width=True):
            carregar_conversa_no_estado(escolhido_id)
            st.rerun()

    if escolhido_id != st.session_state.current_conversation_id:
        carregar_conversa_no_estado(escolhido_id)
        st.rerun()

    with st.expander("Configuração didática", expanded=True):
        st.session_state.perfil_usuario = st.radio(
            "Quem está usando?",
            ["Aluno", "Professor"],
            index=0 if st.session_state.perfil_usuario == "Aluno" else 1,
        )

        campus_options = ["IFCE - Geral", "Fortaleza", "Maracanaú", "Sobral", "Juazeiro do Norte", "Outro"]
        campus_index = campus_options.index(st.session_state.campus) if st.session_state.campus in campus_options else 0
        st.session_state.campus = st.selectbox("Campus", campus_options, index=campus_index)
        st.session_state.curso = st.text_input("Curso", value=st.session_state.curso, placeholder="Ex.: Licenciatura em Física")
        st.session_state.turma = st.text_input("Turma / semestre", value=st.session_state.turma, placeholder="Ex.: 1º semestre")

        estrutura = obter_estrutura_mentores()
        nivel_escolhido = st.radio("Nível", ["Ensino Médio", "Ensino Superior"])
        disciplinas = list(estrutura[nivel_escolhido]["disciplinas"].keys())
        disciplina_escolhida = st.selectbox("Disciplina", disciplinas)
        estilos = estrutura[nivel_escolhido]["disciplinas"][disciplina_escolhida]
        estilo_escolhido = st.selectbox("Estilo", estilos)
        servicos = obter_servicos_por_perfil(st.session_state.perfil_usuario)
        servico_escolhido = st.selectbox("Atendimento", servicos)
        modo = st.selectbox("Modo", ["Chat Geral", "Análise de Conteúdo", "Matemática", "Chat Criativo"])

        st.markdown(
            f"<div class='panel-card'><b>Mentor ativo</b><br>{resumo_mentor(nivel_escolhido, disciplina_escolhida, estilo_escolhido)}</div>",
            unsafe_allow_html=True,
        )

    with st.expander("Atalhos", expanded=False):
        if st.button("Plano de aula", use_container_width=True):
            st.session_state.pending_prompt = "Monte um plano de aula completo sobre: "
        if st.button("Estudo guiado", use_container_width=True):
            st.session_state.pending_prompt = "Monte um estudo guiado sobre: "
        if st.button("Resumo do material", use_container_width=True):
            st.session_state.pending_prompt = "Resuma este material em tópicos claros: "

    conv = get_conversation(st.session_state.current_conversation_id)
    pdf_name = conv[5] if conv else None
    image_name = conv[7] if conv else None

    st.markdown(
        f"""
        <div class='panel-card'>
            <b>Sessão</b><br>
            <span class='small-muted'>Perguntas:</span> {st.session_state.contador_perguntas}/{MAX_PERGUNTAS_SESSAO}<br>
            <span class='small-muted'>PDF:</span> {pdf_name or 'Nenhum'}<br>
            <span class='small-muted'>Imagem:</span> {image_name or 'Nenhuma'}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Limpar anexos", use_container_width=True):
        update_conversation_files(st.session_state.current_conversation_id, None, None, None, None)
        carregar_conversa_no_estado(st.session_state.current_conversation_id)
        st.rerun()

    with st.expander("Gerenciar conversa", expanded=False):
        conv_atual = get_conversation(st.session_state.current_conversation_id)
        titulo_atual = conv_atual[1] if conv_atual else ""
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
# CABEÇALHO
# =========================================================
st.markdown(
    f"""
    <div class='panel-card'>
        <div style='font-size:1.35rem; font-weight:800;'>{APP_NAME}</div>
        <div class='small-muted'>IA mais direta, mais didática e com menos informação desnecessária.</div>
        <div style='margin-top:10px;'>
            <span class='chip'>{st.session_state.perfil_usuario}</span>
            <span class='chip'>{st.session_state.campus}</span>
            <span class='chip'>{disciplina_escolhida}</span>
            <span class='chip'>{servico_escolhido}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.pending_prompt:
    st.info(f"Sugestão pronta: {st.session_state.pending_prompt}")


# =========================================================
# HISTÓRICO
# =========================================================
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# =========================================================
# GERAÇÃO
# =========================================================
def pode_perguntar():
    return st.session_state.contador_perguntas < MAX_PERGUNTAS_SESSAO


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
        erro_upload = validar_upload(arq)
        if erro_upload:
            st.warning(erro_upload)
        else:
            destino, nome_original = salvar_upload(arq)
            nome_lower = arq.name.lower()
            if nome_lower.endswith(".pdf"):
                st.session_state.db_texto_pdf = processar_pdf_from_path(destino)
                st.session_state.pdf_nome = nome_original
                update_conversation_files(conv_id, destino, nome_original, None, None)
                st.toast(f"PDF ativo: {nome_original}")
            elif nome_lower.endswith((".png", ".jpg", ".jpeg")):
                st.session_state.img_nome = nome_original
                update_conversation_files(conv_id, None, None, destino, nome_original)
                st.toast(f"Imagem ativa: {nome_original}")

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

            prompt_sistema_ativo = obter_prompt_mentor_especializado(
                nivel_escolhido,
                disciplina_escolhida,
                estilo_escolhido,
                st.session_state.perfil_usuario,
                servico_escolhido,
            )

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
st.caption("MentorEdu IFCE • versão enxuta, didática e focada no chat.")
