import os
import streamlit as st
from pypdf import PdfReader
import faiss
import numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer

# =========================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="MentorEdu | IFCE",
    page_icon="🎓",
    layout="wide"
)

IF_LOGO = "logo.png"

# =========================================================
# 2. ESTILO VISUAL
# =========================================================
st.markdown("""
<style>
    .stApp {
        background-color: #ffffff;
    }

    .main-title {
        text-align: center;
        color: #2f8f3a;
        font-weight: 800;
        font-size: 2.4rem;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        text-align: center;
        color: #555555;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .stButton > button {
        background-color: #2f8f3a !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1rem !important;
    }

    .stButton > button:hover {
        opacity: 0.92;
    }

    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }

    .bloco-info {
        padding: 12px 16px;
        border-radius: 12px;
        background: #f5f7f8;
        border: 1px solid #e5e7eb;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 3. ESTADO DA SESSÃO
# =========================================================
if "chat" not in st.session_state:
    st.session_state.chat = []

if "db" not in st.session_state:
    st.session_state.db = None

if "pdf_nome" not in st.session_state:
    st.session_state.pdf_nome = None

# =========================================================
# 4. FUNÇÕES DE CARREGAMENTO
# =========================================================
@st.cache_resource
def carregar_modelo_embedding():
    return SentenceTransformer("all-MiniLM-L6-v2")

def carregar_cliente_groq():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "A chave GROQ_API_KEY não foi encontrada nos Secrets do Streamlit Cloud."

    chave = str(st.secrets["GROQ_API_KEY"]).strip()

    if not chave:
        return None, "A chave GROQ_API_KEY está vazia nos Secrets."

    try:
        client = Groq(api_key=chave)
        return client, None
    except Exception as e:
        return None, f"Erro ao inicializar o cliente Groq: {e}"

model = carregar_modelo_embedding()
client, erro_cliente = carregar_cliente_groq()

# =========================================================
# 5. FUNÇÕES AUXILIARES
# =========================================================
def obter_prompt_sistema(perfil_escolhido: str) -> str:
    if "Reitor" in perfil_escolhido:
        return (
            "Você é o Reitor do IFCE. "
            "Responda com tom formal, institucional, claro e objetivo. "
            "Priorize excelência acadêmica, credibilidade, ética, organização "
            "e linguagem apropriada ao ambiente educacional."
        )
    elif "Professor" in perfil_escolhido:
        return (
            "Você é um professor do IFCE. "
            "Responda com clareza, didática, motivação e leveza. "
            "Pode usar humor sutil e inteligente, sem exageros, mantendo respeito "
            "e foco educacional."
        )
    else:
        return (
            "Você é o Coordenador Pedagógico do IFCE. "
            "Responda de modo didático, paciente, acolhedor e organizado. "
            "Ajude o estudante a compreender melhor, estudar com método e aprender com clareza."
        )

def processar_pdf(pdf_file):
    leitor = PdfReader(pdf_file)
    txts = []
    pgs = []

    for i, pagina in enumerate(leitor.pages):
        conteudo = pagina.extract_text()
        if conteudo:
            conteudo = conteudo.strip()
            if conteudo:
                partes = [conteudo[j:j+500] for j in range(0, len(conteudo), 500)]
                for parte in partes:
                    parte = parte.strip()
                    if parte:
                        txts.append(parte)
                        pgs.append(i + 1)

    if not txts:
        return None

    vecs = model.encode(txts)
    vecs = np.array(vecs).astype("float32")

    idx = faiss.IndexFlatL2(vecs.shape[1])
    idx.add(vecs)

    return {
        "idx": idx,
        "txts": txts,
        "pgs": pgs
    }

def buscar_contexto(pergunta: str, k: int = 3) -> str:
    if not st.session_state.db:
        return ""

    try:
        v_q = model.encode([pergunta])
        v_q = np.array(v_q).astype("float32")

        total_chunks = len(st.session_state.db["txts"])
        k = min(k, total_chunks)

        distancias, ids = st.session_state.db["idx"].search(v_q, k=k)

        contexto = []
        for i in ids[0]:
            pagina = st.session_state.db["pgs"][i]
            texto = st.session_state.db["txts"][i]
            contexto.append(f"[Página {pagina}] {texto}")

        return "\n\n".join(contexto)
    except Exception as e:
        return f"Erro ao buscar contexto do PDF: {e}"

def responder_groq(prompt_usuario: str, perfil: str, contexto: str):
    sys_prompt = obter_prompt_sistema(perfil)

    mensagem_usuario = f"""
Responda à pergunta do usuário com base no contexto abaixo quando ele for útil.
Se o contexto não for suficiente, responda com honestidade e use conhecimento geral de forma prudente.

Contexto:
{contexto if contexto else "Nenhum contexto adicional disponível."}

Pergunta do usuário:
{prompt_usuario}
"""

    resposta_texto = ""

    stream = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": mensagem_usuario}
        ],
        temperature=0.7,
        stream=True
    )

    for chunk in stream:
        if hasattr(chunk.choices[0].delta, "content"):
            delta = chunk.choices[0].delta.content
            if delta:
                resposta_texto += delta
                yield resposta_texto

# =========================================================
# 6. SIDEBAR
# =========================================================
with st.sidebar:
    if os.path.exists(IF_LOGO):
        st.image(IF_LOGO, use_container_width=True)

    st.markdown("---")

    perfil = st.radio(
        "Selecione o Mentor:",
        ["Reitor (Sério)", "Professor (Engraçado)", "Coordenador (Educacional)"]
    )

    pdf_input = st.file_uploader("Subir Material (PDF)", type=["pdf"])

    if pdf_input is not None:
        if st.session_state.pdf_nome != pdf_input.name:
            with st.spinner("Processando material PDF..."):
                try:
                    db = processar_pdf(pdf_input)
                    if db:
                        st.session_state.db = db
                        st.session_state.pdf_nome = pdf_input.name
                        st.success("PDF processado com sucesso.")
                    else:
                        st.session_state.db = None
                        st.session_state.pdf_nome = None
                        st.warning("Não foi possível extrair texto do PDF.")
                except Exception as e:
                    st.session_state.db = None
                    st.session_state.pdf_nome = None
                    st.error(f"Erro ao processar o PDF: {e}")

    if st.button("Limpar Ambiente"):
        st.session_state.chat = []
        st.session_state.db = None
        st.session_state.pdf_nome = None
        st.rerun()

# =========================================================
# 7. CABEÇALHO
# =========================================================
st.markdown('<div class="main-title">MentorEdu IFCE</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Assistente acadêmico inteligente para apoio educacional, institucional e pedagógico</div>',
    unsafe_allow_html=True
)

# =========================================================
# 8. AVISOS DE STATUS
# =========================================================
col1, col2 = st.columns(2)

with col1:
    if erro_cliente:
        st.error(erro_cliente)
    else:
        st.success("Conexão com a Groq carregada.")

with col2:
    if st.session_state.db:
        st.success(f"Material ativo: {st.session_state.pdf_nome}")
    else:
        st.info("Nenhum PDF carregado no momento.")

# =========================================================
# 9. HISTÓRICO DO CHAT
# =========================================================
avatar_path = IF_LOGO if os.path.exists(IF_LOGO) else None

for msg in st.session_state.chat:
    with st.chat_message(msg["role"], avatar=avatar_path):
        st.markdown(msg["content"])

# =========================================================
# 10. ENTRADA DO USUÁRIO
# =========================================================
prompt = st.chat_input("Como posso ajudar?")

if prompt:
    st.session_state.chat.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar=avatar_path):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=avatar_path):
        placeholder = st.empty()

        if client is None:
            resposta_final = (
                "Não consegui responder porque a chave da API Groq não está configurada corretamente. "
                "Verifique os Secrets do Streamlit Cloud."
            )
            placeholder.markdown(resposta_final)
            st.session_state.chat.append({"role": "assistant", "content": resposta_final})

        else:
            try:
                contexto = buscar_contexto(prompt, k=3)

                resposta_final = ""
                for parcial in responder_groq(prompt, perfil, contexto):
                    resposta_final = parcial
                    placeholder.markdown(resposta_final)

                if not resposta_final.strip():
                    resposta_final = "Não consegui gerar uma resposta no momento."
                    placeholder.markdown(resposta_final)

                st.session_state.chat.append({"role": "assistant", "content": resposta_final})

            except Exception as e:
                resposta_erro = f"Erro ao consultar a Groq: {e}"
                placeholder.markdown(resposta_erro)
                st.session_state.chat.append({"role": "assistant", "content": resposta_erro})
