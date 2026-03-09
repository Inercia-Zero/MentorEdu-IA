import os
import streamlit as st
from pypdf import PdfReader
import faiss
import numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer

# 1. IDENTIDADE VISUAL IFCE
st.set_page_config(page_title="MentorEdu | IFCE", page_icon="🎓")
IF_LOGO = "logo.png"

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .main-title {
        text-align: center;
        color: #32a041;
        font-weight: 800;
        font-size: 2.3rem;
    }
    .stButton > button {
        background-color: #32a041 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. ESTADO INICIAL
if "chat" not in st.session_state:
    st.session_state.chat = []

if "db" not in st.session_state:
    st.session_state.db = None

# 3. CARREGAMENTO DO SISTEMA
@st.cache_resource
def carregar_modelo():
    return SentenceTransformer("all-MiniLM-L6-v2")

def carregar_cliente_groq():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "A chave GROQ_API_KEY não foi encontrada nos Secrets do Streamlit Cloud."
    
    chave = st.secrets["GROQ_API_KEY"]

    if not chave or not str(chave).strip():
        return None, "A chave GROQ_API_KEY está vazia nos Secrets."
    
    try:
        client = Groq(api_key=chave.strip())
        return client, None
    except Exception as e:
        return None, f"Erro ao inicializar cliente Groq: {e}"

model = carregar_modelo()
client, erro_cliente = carregar_cliente_groq()

# 4. BARRA LATERAL
with st.sidebar:
    if os.path.exists(IF_LOGO):
        st.image(IF_LOGO, use_container_width=True)

    st.markdown("---")

    perfil = st.radio(
        "Selecione o Mentor:",
        ["Reitor (Sério)", "Professor (Engraçado)", "Coordenador (Educacional)"]
    )

    pdf_input = st.file_uploader("Subir Material (PDF)", type="pdf")

    if st.button("Limpar Ambiente"):
        st.session_state.chat = []
        st.session_state.db = None
        st.rerun()

# 5. PROCESSAMENTO DO PDF
if pdf_input and st.session_state.db is None:
    with st.spinner("Processando material..."):
        try:
            leitor = PdfReader(pdf_input)
            txts, pgs = [], []

            for i, pag in enumerate(leitor.pages):
                conteudo = pag.extract_text()
                if conteudo:
                    partes = [conteudo[j:j+500] for j in range(0, len(conteudo), 500)]
                    for p in partes:
                        p = p.strip()
                        if p:
                            txts.append(p)
                            pgs.append(i + 1)

            if txts:
                vecs = model.encode(txts)
                vecs = np.array(vecs).astype("float32")

                idx = faiss.IndexFlatL2(vecs.shape[1])
                idx.add(vecs)

                st.session_state.db = {
                    "idx": idx,
                    "txts": txts,
                    "pgs": pgs
                }
                st.success("PDF processado com sucesso.")
            else:
                st.warning("Não foi possível extrair texto do PDF.")
        except Exception as e:
            st.error(f"Erro ao processar o PDF: {e}")

# 6. TÍTULO
st.markdown('<h1 class="main-title">MentorEdu IFCE</h1>', unsafe_allow_html=True)

av = IF_LOGO if os.path.exists(IF_LOGO) else None

# 7. ALERTA DE CHAVE
if erro_cliente:
    st.error(erro_cliente)
    st.info("No Streamlit Cloud, abra Manage app → Secrets e adicione:\n\nGROQ_API_KEY = \"sua_chave_aqui\"")

# 8. HISTÓRICO DO CHAT
for m in st.session_state.chat:
    with st.chat_message(m["role"], avatar=av):
        st.write(m["content"])

# 9. FUNÇÃO DE PERSONALIDADE
def obter_prompt_sistema(perfil_escolhido):
    if "Reitor" in perfil_escolhido:
        return (
            "Você é o Reitor do IFCE. "
            "Responda de forma formal, séria, institucional e clara. "
            "Priorize excelência acadêmica, ética e objetividade."
        )
    elif "Professor" in perfil_escolhido:
        return (
            "Você é um professor do IFCE. "
            "Responda de forma leve, motivadora, didática e com humor sutil, "
            "sem perder a clareza e o respeito."
        )
    else:
        return (
            "Você é o Coordenador Pedagógico do IFCE. "
            "Responda com didática, paciência, organização e foco em aprendizagem."
        )

# 10. CHAT
if prompt := st.chat_input("Como posso ajudar?"):
    st.session_state.chat.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar=av):
        st.write(prompt)

    with st.chat_message("assistant", avatar=av):
        if client is None:
            resposta_final = "Não consegui responder porque a chave da API Groq não está configurada corretamente."
            st.write(resposta_final)
            st.session_state.chat.append({"role": "assistant", "content": resposta_final})
        else:
            contexto = ""

            if st.session_state.db:
                try:
                    v_q = model.encode([prompt])
                    v_q = np.array(v_q).astype("float32")

                    k = min(2, len(st.session_state.db["txts"]))
                    _, ids = st.session_state.db["idx"].search(v_q, k=k)

                    for i in ids[0]:
                        contexto += f"[Pág {st.session_state.db['pgs'][i]}] {st.session_state.db['txts'][i]}\n\n"
                except Exception as e:
                    st.warning(f"Não foi possível consultar o PDF: {e}")

            sys = obter_prompt_sistema(perfil)

            mensagem_usuario = f"""
Use o contexto abaixo apenas se for relevante para responder.

Contexto:
{contexto if contexto else "Nenhum contexto adicional fornecido."}

Pergunta do usuário:
{prompt}
"""

            resposta_placeholder = st.empty()
            resposta_texto = ""

            try:
                stream = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": sys},
                        {"role": "user", "content": mensagem_usuario}
                    ],
                    temperature=0.7,
                    stream=True
                )

                for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        resposta_texto += delta
                        resposta_placeholder.markdown(resposta_texto)

                if not resposta_texto.strip():
                    resposta_texto = "Não consegui gerar uma resposta no momento."
                    resposta_placeholder.markdown(resposta_texto)

            except Exception as e:
                resposta_texto = f"Erro ao consultar a Groq: {e}"
                resposta_placeholder.markdown(resposta_texto)

            st.session_state.chat.append({"role": "assistant", "content": resposta_texto})
