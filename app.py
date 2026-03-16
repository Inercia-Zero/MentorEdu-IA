import os
import re
import io
import html
import math
import base64
import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import streamlit as st
import fitz  # PyMuPDF
from pypdf import PdfReader
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
from PIL import Image
from groq import Groq


# =========================================================
# CONFIGURAÇÃO
# =========================================================
st.set_page_config(
    page_title="MentorEdu | Projeto Inércia Zero",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "MentorEdu IFCE"
PROJECT_NAME = "Projeto Inércia Zero"
DB_PATH = "mentoredu.db"
UPLOAD_DIR = "uploads"
LOGO_PATH = "logo.png"

TEXT_MODEL = "llama-3.3-70b-versatile"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

MAX_PDF_MB = 15
MAX_IMG_MB = 8
MAX_PERGUNTAS_SESSAO = 30
ALLOWED_FILE_TYPES = ["pdf", "png", "jpg", "jpeg", "webp"]

os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================================================
# CSS
# =========================================================
def inject_css():
    st.markdown("""
    <style>
    :root{
        --bg:#f6f8fb;
        --panel:#ffffff;
        --line:rgba(15,23,42,0.08);
        --text:#0f172a;
        --muted:#64748b;
        --green:#16a34a;
        --green2:#15803d;
        --blue:#2563eb;
        --warn:#d97706;
        --danger:#dc2626;
        --shadow:0 8px 22px rgba(15,23,42,0.07);
        --radius:18px;
    }

    .stApp{
        background:
            radial-gradient(circle at top left, rgba(34,197,94,0.06), transparent 18%),
            radial-gradient(circle at top right, rgba(37,99,235,0.05), transparent 16%),
            linear-gradient(180deg, #f8fafc 0%, #eef4f8 100%);
        color: var(--text);
    }

    section[data-testid="stSidebar"]{
        background: linear-gradient(180deg, #f8fbff 0%, #f1f5f9 100%);
        border-right: 1px solid rgba(15,23,42,0.06);
    }

    .hero-card{
        background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,0.98) 100%);
        border: 1px solid var(--line);
        border-radius: 24px;
        padding: 1.3rem 1.2rem;
        box-shadow: var(--shadow);
        margin-bottom: 1rem;
    }

    .project-badge{
        display:inline-block;
        color:white;
        background: linear-gradient(90deg, var(--green), var(--green2));
        padding: .45rem .9rem;
        border-radius: 999px;
        font-weight: 800;
        font-size: .86rem;
        margin-bottom: .85rem;
    }

    .main-title{
        color:#166534;
        font-weight:900;
        font-size:2.1rem;
        text-align:center;
        margin:0;
    }

    .subtitle{
        text-align:center;
        color:#475569;
        margin-top:.45rem;
        line-height:1.55;
        font-size:.98rem;
    }

    .chip-wrap{
        text-align:center;
        margin-top:.6rem;
    }

    .if-chip{
        display:inline-block;
        padding:.34rem .72rem;
        border-radius:999px;
        background:#f1f5f9;
        border:1px solid rgba(15,23,42,0.06);
        color:#334155;
        font-size:.8rem;
        font-weight:700;
        margin:.2rem;
    }

    .card{
        background:#fff;
        border:1px solid var(--line);
        border-radius:16px;
        box-shadow:var(--shadow);
        padding:1rem;
    }

    .mentor-card{
        background:#fff;
        border:1px solid var(--line);
        border-radius:16px;
        box-shadow:var(--shadow);
        padding:1rem;
        margin-bottom:.8rem;
    }

    .mentor-card h4{
        margin:0 0 .25rem 0;
        font-size:1rem;
        font-weight:800;
    }

    .mentor-card p{
        margin:0;
        color:#475569;
        line-height:1.5;
        font-size:.93rem;
    }

    .soft-note{
        color:#64748b;
        font-size:.9rem;
        line-height:1.5;
    }

    .kpi{
        background:#fff;
        border:1px solid var(--line);
        border-radius:14px;
        padding:.8rem .9rem;
        box-shadow:var(--shadow);
        margin-bottom:.7rem;
    }

    .status-ok{color:#16a34a;font-weight:800;}
    .status-info{color:#2563eb;font-weight:800;}
    .status-warn{color:#d97706;font-weight:800;}
    .status-danger{color:#dc2626;font-weight:800;}

    .source-box{
        background:#fbfdff;
        border:1px solid var(--line);
        border-radius:14px;
        padding:.75rem .9rem;
        margin-top:.75rem;
        color:#475569;
        font-size:.9rem;
    }

    .user-bubble{
        background:#ecfdf3;
        border:1px solid rgba(22,163,74,0.16);
        border-radius:16px;
        padding:.95rem 1rem;
    }

    .assistant-bubble{
        background:#ffffff;
        border:1px solid rgba(15,23,42,0.08);
        border-radius:16px;
        padding:.95rem 1rem;
    }

    .math-box{
        background:#ffffff;
        border:1px solid var(--line);
        border-radius:16px;
        box-shadow:var(--shadow);
        padding:1rem;
        margin:.6rem 0;
    }

    .footer-note{
        text-align:center;
        color:#64748b;
        font-size:.9rem;
        margin-top:1rem;
    }

    .stButton > button{
        width:100%;
        background: linear-gradient(90deg, var(--green), var(--green2)) !important;
        color:white !important;
        border:none !important;
        border-radius:14px !important;
        font-weight:800 !important;
        padding:.65rem 1rem !important;
        box-shadow:0 8px 18px rgba(22,163,74,0.14) !important;
    }

    .stTextInput input,
    .stTextArea textarea,
    div[data-baseweb="select"] > div{
        background:#fff !important;
        color:#0f172a !important;
        border:1px solid rgba(15,23,42,0.10) !important;
        border-radius:14px !important;
    }

    div[data-testid="stChatInput"] textarea{
        background:#fff !important;
        color:#0f172a !important;
        border:1px solid rgba(15,23,42,0.10) !important;
        border-radius:16px !important;
    }
    </style>
    """, unsafe_allow_html=True)


# =========================================================
# ESTADO
# =========================================================
def init_session_state():
    defaults = {
        "chat": [],
        "db": None,
        "pdf_nome": None,
        "img_nome": None,
        "contador_perguntas": 0,
        "current_conversation_id": None,
        "last_sources": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


inject_css()
init_session_state()


# =========================================================
# BANCO SQLITE
# =========================================================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            pdf_path TEXT,
            pdf_name TEXT,
            image_path TEXT,
            image_name TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


def list_conversations():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, created_at, updated_at, pdf_name, image_name
        FROM conversations
        ORDER BY updated_at DESC, id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def create_conversation(title="Nova conversa"):
    now = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO conversations (title, created_at, updated_at)
        VALUES (?, ?, ?)
    """, (title, now, now))
    cid = cur.lastrowid
    conn.commit()
    conn.close()
    return cid


def get_conversation(conversation_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, created_at, updated_at, pdf_path, pdf_name, image_path, image_name
        FROM conversations
        WHERE id = ?
    """, (conversation_id,))
    row = cur.fetchone()
    conn.close()
    return row


def rename_conversation(conversation_id, new_title):
    new_title = (new_title or "").strip()[:90]
    if not new_title:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE conversations
        SET title = ?, updated_at = ?
        WHERE id = ?
    """, (new_title, datetime.utcnow().isoformat(), conversation_id))
    conn.commit()
    conn.close()


def delete_conversation(conversation_id):
    conv = get_conversation(conversation_id)
    if not conv:
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    cur.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()

    conv_dir = os.path.join(UPLOAD_DIR, f"conv_{conversation_id}")
    if os.path.isdir(conv_dir):
        for root, dirs, files in os.walk(conv_dir, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except:
                    pass
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except:
                    pass
        try:
            os.rmdir(conv_dir)
        except:
            pass


def update_conversation_timestamp(conversation_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE conversations
        SET updated_at = ?
        WHERE id = ?
    """, (datetime.utcnow().isoformat(), conversation_id))
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
        cur.execute("""
            UPDATE conversations
            SET title = ?, updated_at = ?
            WHERE id = ?
        """, (title, datetime.utcnow().isoformat(), conversation_id))
        conn.commit()

    conn.close()


def save_message(conversation_id, role, content):
    now = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO messages (conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?)
    """, (conversation_id, role, content, now))
    cur.execute("""
        UPDATE conversations
        SET updated_at = ?
        WHERE id = ?
    """, (now, conversation_id))
    conn.commit()
    conn.close()


def get_messages(conversation_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT role, content, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
    """, (conversation_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def update_conversation_files(conversation_id, pdf_path=None, pdf_name=None, image_path=None, image_name=None):
    conn = get_conn()
    cur = conn.cursor()

    if pdf_path is not None:
        cur.execute("""
            UPDATE conversations
            SET pdf_path = ?, pdf_name = ?, updated_at = ?
            WHERE id = ?
        """, (pdf_path, pdf_name, datetime.utcnow().isoformat(), conversation_id))

    if image_path is not None:
        cur.execute("""
            UPDATE conversations
            SET image_path = ?, image_name = ?, updated_at = ?
            WHERE id = ?
        """, (image_path, image_name, datetime.utcnow().isoformat(), conversation_id))

    conn.commit()
    conn.close()


# =========================================================
# GROQ
# =========================================================
def carregar_cliente():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "A chave GROQ_API_KEY não foi encontrada nos Secrets do Streamlit."
    chave = str(st.secrets["GROQ_API_KEY"]).strip()
    if not chave:
        return None, "A chave GROQ_API_KEY está vazia."
    try:
        return Groq(api_key=chave), None
    except Exception as e:
        return None, f"Erro ao iniciar cliente Groq: {e}"


client, erro_cliente = carregar_cliente()


# =========================================================
# UTILIDADES
# =========================================================
def pode_perguntar():
    return st.session_state.contador_perguntas < MAX_PERGUNTAS_SESSAO


def registrar_pergunta():
    st.session_state.contador_perguntas += 1


def resetar_estado_visual():
    st.session_state.chat = []
    st.session_state.db = None
    st.session_state.pdf_nome = None
    st.session_state.img_nome = None
    st.session_state.contador_perguntas = 0
    st.session_state.last_sources = []


def salvar_uploaded_file(conversation_id, uploaded_file):
    conv_dir = os.path.join(UPLOAD_DIR, f"conv_{conversation_id}")
    os.makedirs(conv_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", uploaded_file.name)
    path = os.path.join(conv_dir, f"{timestamp}_{safe_name}")

    uploaded_file.seek(0)
    with open(path, "wb") as f:
        f.write(uploaded_file.read())
    uploaded_file.seek(0)

    return path


def limpar_texto(txt: str) -> str:
    if not txt:
        return ""
    txt = txt.replace("\x00", " ")
    txt = txt.replace("\u00ad", "")
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()


def tokenizer_basico(txt: str) -> List[str]:
    return re.findall(r"[a-zA-ZÀ-ÿ0-9_]+", (txt or "").lower())


def score_keywords(query: str, text: str) -> float:
    q_tokens = set(tokenizer_basico(query))
    if not q_tokens:
        return 0.0
    t_tokens = set(tokenizer_basico(text))
    if not t_tokens:
        return 0.0
    return len(q_tokens.intersection(t_tokens)) / max(1, len(q_tokens))


def render_texto_seguro(container, texto: str, bubble_class: str = "assistant-bubble"):
    texto = html.escape(texto or "")
    container.markdown(
        f"""
        <div class="{bubble_class}">
            <pre style="white-space:pre-wrap; margin:0; font-family:inherit;">{texto}</pre>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_markdown_seguro(container, texto: str, bubble_class: str = "assistant-bubble"):
    with container:
        try:
            st.markdown(f"<div class='{bubble_class}'>", unsafe_allow_html=True)
            st.markdown(texto)
            st.markdown("</div>", unsafe_allow_html=True)
        except Exception:
            st.markdown(
                f"""
                <div class="{bubble_class}">
                    <pre style="white-space:pre-wrap; margin:0; font-family:inherit;">{html.escape(texto or "")}</pre>
                </div>
                """,
                unsafe_allow_html=True,
            )


def chunk_text(texto: str, chunk_size: int = 1000, overlap: int = 180) -> List[str]:
    texto = limpar_texto(texto)
    if not texto:
        return []

    paragrafos = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    chunks = []
    atual = ""

    for p in paragrafos:
        candidato = (atual + "\n\n" + p).strip() if atual else p
        if len(candidato) <= chunk_size:
            atual = candidato
        else:
            if atual:
                chunks.append(atual.strip())
            if len(p) <= chunk_size:
                atual = p
            else:
                inicio = 0
                while inicio < len(p):
                    fim = inicio + chunk_size
                    sub = p[inicio:fim].strip()
                    if sub:
                        chunks.append(sub)
                    if fim >= len(p):
                        break
                    inicio = max(0, fim - overlap)
                atual = ""

    if atual.strip():
        chunks.append(atual.strip())

    return [c for c in chunks if c.strip()]


def imagem_path_para_data_url(path):
    ext = os.path.splitext(path)[1].lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    mime = mime_map.get(ext, "image/png")
    with open(path, "rb") as f:
        dados = f.read()
    b64 = base64.b64encode(dados).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def construir_memoria_conversa(max_msgs: int = 6) -> str:
    msgs = st.session_state.chat[-max_msgs:]
    linhas = []
    for msg in msgs:
        role = "Usuário" if msg["role"] == "user" else "Assistente"
        linhas.append(f"{role}: {msg['content']}")
    return "\n".join(linhas).strip()


# =========================================================
# PDF / RAG LEVE
# =========================================================
def _extract_with_pymupdf(pdf_bytes: bytes) -> List[Dict]:
    blocks = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        raw_text = limpar_texto(page.get_text("text"))
        if raw_text:
            blocks.append({"page": page_num + 1, "text": raw_text, "source": "pdf"})
    doc.close()
    return blocks


def _extract_with_pypdf(pdf_bytes: bytes) -> List[Dict]:
    blocks = []
    reader = PdfReader(io.BytesIO(pdf_bytes))
    for i, pagina in enumerate(reader.pages):
        try:
            txt = limpar_texto(pagina.extract_text() or "")
        except Exception:
            txt = ""
        if txt:
            blocks.append({"page": i + 1, "text": txt, "source": "pdf"})
    return blocks


def processar_pdf_from_bytes(pdf_bytes: bytes) -> Optional[Dict]:
    blocks = []
    try:
        blocks = _extract_with_pymupdf(pdf_bytes)
    except Exception:
        blocks = []

    if not blocks:
        try:
            blocks = _extract_with_pypdf(pdf_bytes)
        except Exception:
            blocks = []

    if not blocks:
        return None

    textos, pgs, metas = [], [], []

    for bloco in blocks:
        partes = chunk_text(bloco["text"])
        for ch in partes:
            textos.append(ch)
            pgs.append(bloco["page"])
            metas.append({"page": bloco["page"], "source": bloco["source"]})

    if not textos:
        return None

    return {"txts": textos, "pgs": pgs, "metas": metas}


def processar_pdf_from_path(pdf_path: str) -> Optional[Dict]:
    with open(pdf_path, "rb") as f:
        return processar_pdf_from_bytes(f.read())


def buscar_contexto_em_db(db: Dict, pergunta: str, k: int = 5) -> List[Dict]:
    resultados = []
    if not db or not pergunta:
        return resultados

    for i, texto in enumerate(db["txts"]):
        score = score_keywords(pergunta, texto)
        if score > 0:
            resultados.append({
                "score": score,
                "page": db["pgs"][i],
                "text": texto,
                "source": db["metas"][i]["source"],
            })

    resultados = sorted(resultados, key=lambda x: x["score"], reverse=True)
    return resultados[:k]


def buscar_contexto(pergunta: str, k: int = 5) -> Tuple[str, List[str]]:
    resultados = []
    if st.session_state.db:
        resultados.extend(buscar_contexto_em_db(st.session_state.db, pergunta, k=k))

    if not resultados:
        return "", []

    contexto = []
    refs = []
    vistos = set()

    for item in resultados:
        chave = f"{item['page']}|{item['text'][:120]}"
        if chave in vistos:
            continue
        vistos.add(chave)

        contexto.append(f"[PDF | Página {item['page']}] {item['text']}")
        refs.append(f"PDF pág. {item['page']}")

        if len(contexto) >= k:
            break

    return "\n\n".join(contexto), refs


# =========================================================
# MENTORES
# =========================================================
def obter_estrutura_mentores():
    return {
        "Ensino Médio": {
            "disciplinas": {
                "Física": ["Didático", "Feynman", "GrokFísica"],
                "Química": ["Didático", "Vestibular"],
                "Matemática": ["Didático", "Feynman", "Vestibular"],
                "Metodologia Científica": ["Professor", "Socrático"],
            }
        },
        "Ensino Superior": {
            "disciplinas": {
                "Física": ["Professor", "Cientista", "Feynman"],
                "Química": ["Professor", "Cientista"],
                "Matemática": ["Professor", "Cientista"],
                "Metodologia Científica": ["Professor", "Orientador de TCC"],
            }
        }
    }


def resumo_mentor(nivel: str, disciplina: str, estilo: str) -> str:
    descricoes = {
        "Didático": "Explica passo a passo com linguagem simples e exemplos claros.",
        "Feynman": "Explica conceitos complexos de forma simples usando analogias.",
        "Vestibular": "Foco em resolução de questões e estratégias para provas.",
        "Professor": "Explicação estruturada como em uma aula.",
        "Cientista": "Abordagem técnica e conceitual com mais rigor científico.",
        "Socrático": "Estimula o raciocínio fazendo perguntas.",
        "Orientador de TCC": "Ajuda em pesquisa, metodologia científica e estrutura acadêmica.",
        "GrokFísica": "Explica física com humor leve e analogias divertidas.",
    }
    return f"{nivel} • {disciplina} • {descricoes.get(estilo, 'Mentor educacional especializado.')}"


def obter_prompt_mentor_especializado(nivel: str, disciplina: str, estilo: str) -> str:
    base = f"""
Você é o MentorEdu, um assistente educacional especializado em {disciplina} para {nivel}.

REGRAS:
- Nunca invente conteúdo do PDF ou da imagem.
- Se não souber algo, diga com honestidade.
- Se houver cálculo, mostre o raciocínio passo a passo.
- Se houver conceito, explique a intuição e depois a definição formal.
- Priorize clareza.
"""

    niveis = {
        "Ensino Médio": """
NÍVEL:
- Use linguagem acessível.
- Evite excesso de formalismo.
- Use exemplos do cotidiano.
""",
        "Ensino Superior": """
NÍVEL:
- Use maior rigor conceitual.
- Pode aprofundar mais a teoria.
- Mantenha clareza mesmo em temas técnicos.
"""
    }

    estilos = {
        "Didático": """
ESTILO:
- Explique passo a passo.
- Use linguagem simples.
""",
        "Feynman": """
ESTILO:
- Ensine como para alguém que nunca viu o assunto.
- Use analogias.
""",
        "Vestibular": """
ESTILO:
- Foque em provas, resolução e estratégia.
""",
        "Professor": """
ESTILO:
- Explique como um professor em aula.
- Seja organizado e progressivo.
""",
        "Cientista": """
ESTILO:
- Use rigor conceitual.
- Destaque relações teóricas e precisão.
""",
        "Socrático": """
ESTILO:
- Estimule o raciocínio com perguntas.
""",
        "Orientador de TCC": """
ESTILO:
- Ajude com pesquisa, escrita acadêmica e metodologia.
""",
        "GrokFísica": """
ESTILO:
- Fale de forma humana, leve e inteligente.
- Pode usar humor quando couber.
"""
    }

    disciplinas = {
        "Física": """
DISCIPLINA:
- Explique fenômenos físicos com clareza.
- Una intuição física com cálculo.
""",
        "Química": """
DISCIPLINA:
- Explique estrutura da matéria, reações, estequiometria e lógica química.
""",
        "Matemática": """
DISCIPLINA:
- Explique álgebra, funções, geometria, trigonometria e cálculo.
- Valorize a lógica por trás da conta.
""",
        "Metodologia Científica": """
DISCIPLINA:
- Ajude com problema, hipótese, objetivos, justificativa, revisão, metodologia e escrita acadêmica.
"""
    }

    return base + "\n" + niveis.get(nivel, "") + "\n" + estilos.get(estilo, "") + "\n" + disciplinas.get(disciplina, "")


def obter_instrucao_modo(modo_atual: str) -> str:
    if modo_atual == "Matemática":
        return """
Você está no modo Matemática.
- Priorize resolução, demonstração, interpretação matemática, gráficos e explicações conceituais.
- Quando houver matemática, use LaTeX.
- Organize a resposta em etapas.
"""
    elif modo_atual == "Análise de Conteúdo":
        return """
Você está no modo Análise de Conteúdo.
- Priorize interpretação de PDF e imagem.
- Resuma, compare fontes, explique páginas, identifique conceitos e relacione materiais.
"""
    elif modo_atual == "Chat Criativo":
        return """
Você está no modo Chat Criativo.
- Ajude com ideias, aulas, planejamentos, metodologias, projetos e apresentações.
- Seja criativo, estratégico, útil e prático.
"""
    elif modo_atual == "GrokFísica (zoeira + didática)":
        return """
Você está no modo GrokFísica (zoeira + didática).
- Fale de forma humana, descontraída, engraçada e inteligente.
- Pode usar humor leve.
"""
    return """
Você está no modo Chat Geral.
- Responda com clareza, objetividade e adaptação ao mentor selecionado.
"""


def montar_prompt_usuario(
    prompt_usuario: str,
    modo_atual: str,
    contexto: str = "",
    memoria: str = "",
    referencias: Optional[List[str]] = None
) -> str:
    referencias = referencias or []

    instrucoes_math = """
REGRAS DE FORMATAÇÃO:
- Sempre que houver matemática, use LaTeX corretamente.
- Para expressões curtas, use $...$
- Para fórmulas destacadas, use $$...$$
- Nunca deixe LaTeX aberto.
"""

    return f"""
{obter_instrucao_modo(modo_atual)}

{instrucoes_math if modo_atual == "Matemática" else ""}

Memória recente:
{memoria if memoria else "Sem memória recente relevante."}

Contexto recuperado:
{contexto if contexto else "Nenhum contexto documental adicional disponível."}

Referências:
{", ".join(referencias) if referencias else "Nenhuma referência específica."}

Pedido do usuário:
{prompt_usuario}

Instruções finais:
- Responda de forma natural.
- Evite textão desnecessário.
- Se houver contexto de PDF/imagem, use sem inventar.
"""


# =========================================================
# GROQ CHAMADAS
# =========================================================
def analisar_imagem_com_vision(
    prompt_usuario: str,
    prompt_sistema: str,
    modo_atual: str,
    image_path: str,
    contexto: str = "",
    referencias: Optional[List[str]] = None,
):
    if client is None:
        return "Cliente Groq não disponível."

    data_url = imagem_path_para_data_url(image_path)
    memoria = construir_memoria_conversa()
    prompt_final = montar_prompt_usuario(
        prompt_usuario=prompt_usuario,
        modo_atual=modo_atual,
        contexto=contexto,
        memoria=memoria,
        referencias=referencias or [],
    )

    instrucao = (
        f"{prompt_sistema}\n\n"
        f"Você pode receber uma imagem contendo exercício, quadro, caderno, print, slide, gráfico ou documento. "
        f"Transcreva o que for legível, interprete com cuidado e integre com o contexto recuperado quando existir. "
        f"Se a imagem estiver parcialmente ilegível, diga isso.\n\n"
        f"{prompt_final}"
    )

    resp = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {"role": "system", "content": instrucao},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_usuario},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        temperature=0.2,
        max_completion_tokens=1800,
        stream=False,
    )
    return (resp.choices[0].message.content or "").strip()


def responder_texto(prompt_usuario: str, prompt_sistema: str, contexto: str, modo_atual: str, referencias=None):
    referencias = referencias or []
    memoria = construir_memoria_conversa()

    mensagem_usuario = montar_prompt_usuario(
        prompt_usuario=prompt_usuario,
        modo_atual=modo_atual,
        contexto=contexto,
        memoria=memoria,
        referencias=referencias,
    )

    stream = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": mensagem_usuario},
        ],
        temperature=0.35,
        max_completion_tokens=2200,
        stream=True,
    )

    resposta = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            resposta += delta
            yield resposta


# =========================================================
# MATEMÁTICA / VISUAIS
# =========================================================
def extrair_expressao_grafico(prompt: str):
    texto = prompt.lower().strip()
    padroes = [
        r"gr[aá]fico de (.+)",
        r"plot de (.+)",
        r"desenhe a fun[cç][aã]o (.+)",
        r"fa[cç]a o gr[aá]fico de (.+)",
    ]
    for padrao in padroes:
        m = re.search(padrao, texto)
        if m:
            return m.group(1).strip(" .,:;")
    return None


def normalizar_expressao(expr: str):
    expr = expr.replace("^", "**")
    expr = expr.replace("sen(", "sin(")
    expr = expr.replace("tg(", "tan(")
    expr = expr.replace("ln(", "log(")
    return expr


def expressao_valida(expr: str):
    proibidos = ["__", "import", "exec", "eval", "open", "os.", "sys.", "subprocess"]
    expr_lower = expr.lower()
    return not any(item in expr_lower for item in proibidos)


def gerar_grafico_basico(expressao_str: str):
    try:
        expr_limpa = normalizar_expressao(expressao_str)
        x = sp.symbols("x")
        expr = sp.sympify(expr_limpa)
        f = sp.lambdify(x, expr, "numpy")

        valores_x = np.linspace(-10, 10, 600)
        valores_y = f(valores_x)
        y = np.array(valores_y, dtype=float)
        y[np.abs(y) > 1e6] = np.nan

        fig, ax = plt.subplots(figsize=(8.5, 4.6))
        ax.plot(valores_x, y, linewidth=2.0)
        ax.axhline(0, linewidth=1)
        ax.axvline(0, linewidth=1)
        ax.set_title(f"Gráfico de y = {expressao_str}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.grid(True, alpha=0.35)
        st.pyplot(fig)
        plt.close(fig)
        return True, None
    except Exception as e:
        return False, str(e)


def gerar_quadro_formula(titulo: str, linhas: List[str]):
    altura = max(4.6, 1.35 + 0.95 * len(linhas))
    fig, ax = plt.subplots(figsize=(10, altura))
    ax.axis("off")

    y = 0.93
    ax.text(0.02, y, titulo, fontsize=18, fontweight="bold", transform=ax.transAxes)
    y -= 0.12

    for linha in linhas:
        ax.text(0.03, y, linha, fontsize=15.5, transform=ax.transAxes)
        y -= 0.11

    st.pyplot(fig)
    plt.close(fig)


def demonstrar_bhaskara():
    linhas = [
        r"Equação do 2º grau: $ax^2+bx+c=0$, com $a\neq0$",
        r"Dividindo tudo por $a$: $x^2+\frac{b}{a}x+\frac{c}{a}=0$",
        r"Isolando: $x^2+\frac{b}{a}x=-\frac{c}{a}$",
        r"Completando quadrados:",
        r"$x^2+\frac{b}{a}x+\frac{b^2}{4a^2}=-\frac{c}{a}+\frac{b^2}{4a^2}$",
        r"$\left(x+\frac{b}{2a}\right)^2=\frac{b^2-4ac}{4a^2}$",
        r"Extraindo a raiz:",
        r"$x+\frac{b}{2a}=\pm\frac{\sqrt{b^2-4ac}}{2a}$",
        r"$$x=\frac{-b\pm\sqrt{b^2-4ac}}{2a}$$",
    ]
    gerar_quadro_formula("Demonstração da fórmula de Bhaskara", linhas)


def desenhar_circunferencia_trigonometrica():
    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    t = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(t), np.sin(t), linewidth=2)
    ax.axhline(0, linewidth=1)
