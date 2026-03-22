import os
import re
import uuid
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
IF_LOGO = "logo.png"
DB_PATH = "mentoredu.db"
UPLOAD_DIR = "uploads"

MAX_PDF_MB = 15
MAX_PERGUNTAS_SESSAO = 30
PDF_CONTEXT_LIMIT = 6500
CHAT_HISTORY_LIMIT = 6
MODEL_NAME = "llama-3.3-70b-versatile"

os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================================================
# TEMA
# =========================================================
def gerar_css() -> str:
    return """
    <style>
        :root {
            --bg: #f7f3ee;
            --bg-top: #f5efe7;
            --sidebar: #efe6dc;
            --card: #fffdf9;
            --line: #dccfc0;
            --text: #3b312a;
            --muted: #7a6d61;
            --accent: #9a8676;
            --accent-hover: #826f60;
            --badge: #f1e7dc;
            --chip: #f7efe6;
            --user-bg: #efe4d7;
            --assistant-bg: #fffaf5;
        }

        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"] {
            background: var(--bg) !important;
        }

        .main .block-container {
            padding-top: 1.1rem !important;
            padding-bottom: 1rem !important;
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

        .painel-card,
        .status-card {
            background: var(--card) !important;
            border: 1px solid var(--line) !important;
            border-radius: 22px !important;
            box-shadow: 0 12px 28px rgba(92, 70, 48, 0.07) !important;
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

        .main-title {
            color: #5b473b !important;
            font-size: 2.3rem !important;
            font-weight: 700 !important;
            line-height: 1.08 !important;
            margin-bottom: 6px !important;
            text-align: center !important;
        }

        .small-muted {
            color: var(--muted) !important;
        }

        .stButton > button {
            background: var(--accent) !important;
            color: #fffdfa !important;
            border: 1px solid var(--accent) !important;
            border-radius: 14px !important;
            min-height: 46px !important;
        }

        .stButton > button:hover {
            background: var(--accent-hover) !important;
            border-color: var(--accent-hover) !important;
        }

        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {
            background: #fffaf5 !important;
            color: #3b312a !important;
            border: 1px solid #dccfc0 !important;
            border-radius: 14px !important;
        }

        /* Dropdown aberto */
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

        ul[role="listbox"] {
            background: #fffaf5 !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 6px !important;
        }

        ul[role="listbox"] li,
        div[role="option"] {
            background: #fffaf5 !important;
            color: #3b312a !important;
            border-radius: 10px !important;
        }

        ul[role="listbox"] li:hover,
        div[role="option"]:hover {
            background: #efe4d7 !important;
            color: #3b312a !important;
        }

        ul[role="listbox"] li[aria-selected="true"],
        div[role="option"][aria-selected="true"] {
            background: #e9dfd3 !important;
            color: #3b312a !important;
        }

        [data-baseweb="menu"],
        [data-baseweb="menu"] > div,
        [data-baseweb="menu"] ul,
        [data-baseweb="menu"] li {
            background: #fffaf5 !important;
            color: #3b312a !important;
        }

        body [data-baseweb="popover"] {
            background: transparent !important;
        }

        body [data-baseweb="popover"] [role="listbox"],
        body [data-baseweb="popover"] [role="option"] {
            background: #fffaf5 !important;
            color: #3b312a !important;
        }

        /* Parte inferior / input */
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

        /* Bolhas do chat */
        [data-testid="stChatMessageContent"] {
            color: var(--text) !important;
            border: 1px solid var(--line) !important;
            border-radius: 16px !important;
            padding: .55rem .7rem !important;
        }

        .stChatMessage:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
            background: var(--user-bg) !important;
        }

        .stChatMessage:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
            background: var(--assistant-bg) !important;
        }

        [data-testid="stExpander"] {
            background: var(--card) !important;
            border: 1px solid var(--line) !important;
            border-radius: 14px !important;
        }

        [data-testid="stExpander"] * {
            color: var(--text) !important;
        }

        p, span, label, div, li {
            color: var(--text) !important;
        }
    </style>
    """


st.markdown(gerar_css(), unsafe_allow_html=True)


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
        "current_conversation_id": None,
        "loaded_conversation_id": None,
        "confirm_delete": False,
        "contador_perguntas": 0,
        "pending_prompt": None,
        "area": "Exatas",
        "nivel": "Ensino Médio",
        "materia": "Matemática",
        "tipo_ajuda": "Resolver exercício",
        "estilo_resposta": "Didático",
        "reforcos": ["Passo a passo", "Fórmula em LaTeX"],
        "ultima_imagem_visual": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session_state()


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
            st.caption("Entre com sua conta para personalizar a experiência.")
            if hasattr(st, "login"):
                if st.button("Entrar com Google", use_container_width=True, key="login_btn"):
                    st.login()
        st.markdown("---")
    except Exception:
        pass


# =========================================================
# CONVERSAS
# =========================================================
def list_conversations():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, created_at, updated_at, pdf_name FROM conversations ORDER BY updated_at DESC, id DESC"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_conversation(conversation_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, created_at, updated_at, pdf_path, pdf_name FROM conversations WHERE id = ?",
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
    if conv and conv[4] and os.path.exists(conv[4]):
        try:
            os.remove(conv[4])
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


def update_conversation_pdf(conversation_id, pdf_path=None, pdf_name=None):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        "UPDATE conversations SET pdf_path = ?, pdf_name = ?, updated_at = ? WHERE id = ?",
        (pdf_path, pdf_name, now, conversation_id),
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
    st.session_state.contador_perguntas = 0
    st.session_state.confirm_delete = False
    st.session_state.ultima_imagem_visual = None


def carregar_conversa_no_estado(conversation_id):
    conv = get_conversation(conversation_id)
    if not conv:
        return

    _, _, _, _, pdf_path, pdf_name = conv
    st.session_state.chat = [
        {"role": role, "content": content}
        for role, content, _ in get_messages(conversation_id)
    ]
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
    _, title, _, _, pdf_name = row
    suffix = " [PDF]" if pdf_name else ""
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
# DOMÍNIO ACADÊMICO
# =========================================================
def opcoes_area() -> Dict[str, List[str]]:
    return {
        "Exatas": ["Matemática", "Física"],
        "Química": ["Química"],
        "Linguagens": ["Português", "Inglês"],
    }


def opcoes_tipo_ajuda(materia: str) -> List[str]:
    if materia in ["Matemática", "Física"]:
        return [
            "Entender conteúdo",
            "Resolver exercício",
            "Corrigir resolução",
            "Revisar para prova",
            "Montar lista de treino",
            "Fazer trabalho",
        ]
    if materia == "Química":
        return [
            "Entender conteúdo",
            "Resolver exercício",
            "Balanceamento / estequiometria",
            "Revisar para prova",
            "Resumir assunto",
            "Fazer trabalho",
        ]
    return [
        "Entender conteúdo",
        "Interpretar texto",
        "Corrigir texto",
        "Melhorar escrita",
        "Revisar gramática",
        "Fazer trabalho",
    ]


def opcoes_reforco(materia: str) -> List[str]:
    if materia in ["Matemática", "Física"]:
        return ["Passo a passo", "Fórmula em LaTeX", "Exemplo resolvido", "Esquema visual"]
    if materia == "Química":
        return ["Passo a passo", "Equações em LaTeX", "Resumo em tópicos", "Esquema visual"]
    return ["Exemplo comentado", "Resumo em tópicos", "Comparação lado a lado", "Esquema visual"]


def formato_resposta_instrucao(estilo: str) -> str:
    mapa = {
        "Direto": "Vá direto ao ponto e evite rodeios.",
        "Didático": "Explique com clareza e em linguagem acessível.",
        "Passo a passo": "Separe a explicação em etapas curtas e numeradas.",
        "Revisão rápida": "Resuma apenas o essencial para revisão.",
    }
    return mapa.get(estilo, "Seja claro e útil.")


# =========================================================
# ARQUIVOS
# =========================================================
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


# =========================================================
# PROMPTS
# =========================================================
def construir_contexto_curto() -> str:
    return (
        f"Nível={st.session_state.nivel}; Área={st.session_state.area}; "
        f"Matéria={st.session_state.materia}; Tipo de ajuda={st.session_state.tipo_ajuda}; "
        f"Estilo={st.session_state.estilo_resposta}; "
        f"Reforços={', '.join(st.session_state.reforcos) if st.session_state.reforcos else 'nenhum'}."
    )


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


def construir_instrucao_reforco(reforcos: List[str]) -> str:
    regras = []

    if "Passo a passo" in reforcos:
        regras.append("Organize a resposta em etapas curtas e numeradas.")

    if "Fórmula em LaTeX" in reforcos or "Equações em LaTeX" in reforcos:
        regras.append(
            "Toda expressão matemática deve ser escrita em LaTeX. "
            "Use $...$ para expressões curtas e $$...$$ para equações principais. "
            "Não escreva fórmulas como texto comum."
        )

    if "Exemplo resolvido" in reforcos:
        regras.append("Inclua um exemplo resolvido curto ao final.")

    if "Exemplo comentado" in reforcos:
        regras.append("Inclua um exemplo comentado e explique o erro mais comum.")

    if "Resumo em tópicos" in reforcos:
        regras.append("Feche a explicação com um resumo em tópicos.")

    if "Comparação lado a lado" in reforcos:
        regras.append("Use comparação lado a lado entre formas corretas e incorretas, quando útil.")

    if "Esquema visual" in reforcos:
        regras.append("Após explicar, prepare uma versão resumida própria para virar um esquema visual.")

    return " ".join(regras)


def obter_prompt_sistema() -> str:
    return (
        "Você é um mentor acadêmico especializado em apoio didático para estudantes do Ensino Médio e Ensino Superior. "
        "Responda sempre em português do Brasil, exceto quando a matéria for Inglês e o usuário pedir explicitamente prática em inglês. "
        "Seja claro, objetivo, didático e útil. "
        "Evite introduções longas, repetições e floreios. "
        "Quando a pergunta for simples, responda de forma simples. "
        "Quando houver cálculo, mostre apenas os passos necessários. "
        "Quando houver teoria, comece pela ideia principal e depois explique. "
        "Adapte a linguagem ao nível de ensino informado. "
        "Não invente informações. "
        "Se o conteúdo depender do PDF, use o PDF apenas quando ele for relevante. "
        "Quando houver matemática, física ou química com fórmulas, escreva as expressões obrigatoriamente em LaTeX válido. "
    )


def montar_prompt_usuario(pergunta: str, pdf_texto: Optional[str]) -> str:
    partes = [
        construir_contexto_curto(),
        f"Instrução de estilo: {formato_resposta_instrucao(st.session_state.estilo_resposta)}",
        construir_instrucao_reforco(st.session_state.reforcos),
    ]

    historico = formatar_historico_curto(st.session_state.get("chat", []))
    if historico:
        partes.append("Histórico recente:\n" + historico)

    if pdf_texto:
        partes.append("Trecho do PDF para contexto:\n" + pdf_texto[:PDF_CONTEXT_LIMIT])

    partes.append("Pergunta atual:\n" + pergunta.strip())
    return "\n\n".join([p for p in partes if p.strip()])


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
            temperature=0.35,
            max_tokens=1100,
        )
        return limpar_resposta(resp.choices[0].message.content.strip())
    except Exception as e:
        return f"Ocorreu um erro ao gerar a resposta: {e}"


def gerar_texto_visual(resposta: str, pergunta: str) -> str:
    if client is None:
        return "Resumo visual indisponível no momento."

    prompt_sistema = (
        "Você cria resumos visuais curtos para estudos. "
        "Transforme a explicação em um esquema visual textual, curto, organizado e claro. "
        "Use títulos curtos, setas, tópicos e fórmulas simples quando útil. "
        "Não escreva parágrafos longos. "
        "No máximo 12 linhas."
    )

    prompt_usuario = (
        f"Matéria: {st.session_state.materia}\n"
        f"Nível: {st.session_state.nivel}\n"
        f"Pergunta: {pergunta}\n\n"
        f"Resposta-base:\n{resposta}\n\n"
        "Agora gere um esquema visual resumido."
    )

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
            temperature=0.25,
            max_tokens=300,
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

    subt = f"{st.session_state.materia} • {st.session_state.nivel}"
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
            "Digite sua pergunta...",
            accept_file=True,
            file_type=["pdf"],
            key="main_chat_input",
        )
        return payload
    except TypeError:
        st.caption("Seu Streamlit não suporta anexo embutido no chat. Atualize para uma versão mais nova.")
        up = st.file_uploader("Anexe PDF", type=["pdf"], label_visibility="collapsed")
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
with st.sidebar:
    exibir_bloco_login_sidebar()

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
    st.markdown("### PDF")
    conv = get_conversation(st.session_state.current_conversation_id)
    pdf_name = conv[5] if conv else None

    st.markdown(
        f"""
        <div class="status-card" style="padding:14px; margin-top:10px;">
            <div><b>PDF ativo</b></div>
            <div>{pdf_name if pdf_name else 'Nenhum'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Limpar PDF da conversa", use_container_width=True):
        update_conversation_pdf(st.session_state.current_conversation_id, None, None)
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


# =========================================================
# TOPO
# =========================================================
st.markdown(
    f"""
    <div style="margin-bottom:10px;">
        <div class="project-badge">{PROJECT_NAME}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# PAINEL CENTRAL
# =========================================================
st.markdown('<div class="painel-card" style="padding:28px; margin-bottom:18px;">', unsafe_allow_html=True)
st.markdown('<div class="main-title">Como posso te ajudar hoje?</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    nivel = st.selectbox(
        "Nível",
        ["Ensino Médio", "Ensino Superior"],
        index=0 if st.session_state.nivel == "Ensino Médio" else 1,
        key="painel_nivel"
    )

    area = st.selectbox(
        "Área",
        ["Exatas", "Química", "Linguagens"],
        index=["Exatas", "Química", "Linguagens"].index(st.session_state.area)
        if st.session_state.area in ["Exatas", "Química", "Linguagens"] else 0,
        key="painel_area"
    )

with col2:
    materias = opcoes_area()[area]
    materia = st.selectbox(
        "Matéria",
        materias,
        index=materias.index(st.session_state.materia) if st.session_state.materia in materias else 0,
        key="painel_materia"
    )

    objetivos = opcoes_tipo_ajuda(materia)
    objetivo = st.selectbox(
        "Objetivo",
        objetivos,
        index=objetivos.index(st.session_state.tipo_ajuda) if st.session_state.tipo_ajuda in objetivos else 0,
        key="painel_objetivo"
    )

with st.expander("Opções avançadas"):
    estilo = st.selectbox(
        "Estilo da resposta",
        ["Direto", "Didático", "Passo a passo", "Revisão rápida"],
        index=["Direto", "Didático", "Passo a passo", "Revisão rápida"].index(st.session_state.estilo_resposta)
        if st.session_state.estilo_resposta in ["Direto", "Didático", "Passo a passo", "Revisão rápida"] else 1,
        key="painel_estilo"
    )

    reforcos_disp = opcoes_reforco(materia)
    reforcos_validos = [r for r in st.session_state.reforcos if r in reforcos_disp]
    if not reforcos_validos:
        reforcos_validos = [reforcos_disp[0]]

    reforcos = st.multiselect(
        "Reforços",
        reforcos_disp,
        default=reforcos_validos,
        key="painel_reforcos"
    )

if st.button("Buscar", use_container_width=True, key="painel_buscar"):
    st.session_state.nivel = nivel
    st.session_state.area = area
    st.session_state.materia = materia
    st.session_state.tipo_ajuda = objetivo
    st.session_state.estilo_resposta = estilo
    st.session_state.reforcos = reforcos
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# HISTÓRICO DO CHAT
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
# ENTRADA DO USUÁRIO
# =========================================================
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
            st.session_state.db_texto_pdf = processar_pdf_from_path(destino)
            st.session_state.pdf_nome = nome_original
            update_conversation_pdf(conv_id, destino, nome_original)
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

            prompt_sistema = obter_prompt_sistema()
            prompt_usuario = montar_prompt_usuario(
                pergunta=pergunta,
                pdf_texto=st.session_state.db_texto_pdf,
            )

            with st.spinner("Pensando..."):
                resposta = gerar_resposta_groq(prompt_sistema, prompt_usuario)

            save_message(conv_id, "assistant", resposta)
            st.session_state.chat.append({"role": "assistant", "content": resposta})

            if "Esquema visual" in st.session_state.reforcos:
                try:
                    texto_visual = gerar_texto_visual(resposta, pergunta)
                    titulo_visual = f"{st.session_state.materia} • esquema visual"
                    caminho_img = criar_imagem_esquema(titulo_visual, texto_visual)
                    st.session_state.ultima_imagem_visual = caminho_img
                except Exception:
                    st.session_state.ultima_imagem_visual = None
            else:
                st.session_state.ultima_imagem_visual = None

            st.rerun()


# =========================================================
# RODAPÉ
# =========================================================
st.caption("MentorEdu IA • foco em Matemática, Física, Química, Português e Inglês.")
