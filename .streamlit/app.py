import streamlit as st
from pypdf import PdfReader
import os, faiss, numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer

# CONFIGURAÇÃO DA PÁGINA (INSTITUCIONAL IF)
st.set_page_config(page_title="MentorEdu | IF", page_icon="🎓")
LOGO_INSTITUCIONAL = "logo.png"

# CSS PARA CORES DO IF
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .main-title { text-align: center; color: #32a041; font-weight: 800; font-size: 2.5rem; }
    .stButton>button { background-color: #32a041 !important; color: white !important; width: 100%; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# INICIALIZAÇÃO DE MOTORES (COM CACHE)
@st.cache_resource
def iniciar_motores():
    try:
        chave = st.secrets["GROQ_API_KEY"]
        return Groq(api_key=chave), SentenceTransformer("all-MiniLM-L6-v2")
    except:
        return None, SentenceTransformer("all-MiniLM-L6-v2")

client, model = iniciar_motores()

# MEMÓRIA DA SESSÃO
if "chat" not in st.session_state: st.session_state.chat = []
if "db" not in st.session_state: st.session_state.db = None

# BARRA LATERAL
with st.sidebar:
    if os.path.exists(LOGO_INSTITUCIONAL):
        st.image(LOGO_INSTITUCIONAL, use_container_width=True)
    st.markdown("---")
    area = st.selectbox("Área Técnica:", ["Geral", "Informática", "Mecânica", "Química"])
    pdf_up = st.file_uploader("Subir Material Didático (PDF)", type="pdf")
    if st.button("🔄 Reiniciar Ambiente"):
        st.session_state.chat = []
        st.session_state.db = None
        st.rerun()

# PROCESSAMENTO DO PDF
if pdf_up and st.session_state.db is None:
    with st.spinner("Indexando conteúdo..."):
        leitor = PdfReader(pdf_up)
        textos, pgs = [], []
        for i, pagina in enumerate(leitor.pages):
            c = pagina.extract_text()
            if c:
                blocos = [c[j:j+600] for j in range(0, len(c), 600)]
                for b in blocos:
                    textos.append(b.strip())
                    pgs.append(i+1)
        if textos:
            embs = model.encode(textos)
            idx = faiss.IndexFlatL2(embs.shape[1])
            idx.add(np.array(embs))
            st.session_state.db = {"idx": idx, "textos": textos, "pgs": pgs}

# INTERFACE DE CHAT
st.markdown('<h1 class="main-title">MentorEdu</h1>', unsafe_allow_html=True)

# Avatar único do IF para aluno e professor
avatar_if = LOGO_INSTITUCIONAL if os.path.exists(LOGO_INSTITUCIONAL) else None

for m in st.session_state.chat:
    with st.chat_message(m["role"], avatar=avatar_if):
        st.write(m["content"])

if p := st.chat_input("Dúvida acadêmica?"):
    # Mensagem do Aluno (com logo IF)
    st.session_state.chat.append({"role": "user", "content": p})
    with st.chat_message("user", avatar=avatar_if):
        st.write(p)

    # Resposta do Mentor (com logo IF)
    with st.chat_message("assistant", avatar=avatar_if):
        contexto = ""
        if st.session_state.db:
            v_q = model.encode([p])
            _, ids = st.session_state.db["idx"].search(np.array(v_q), k=2)
            for idx in ids[0]:
                contexto += f"[Pág {st.session_state.db['pgs'][idx]}] {st.session_state.db['textos'][idx]}\n\n"

        if client:
            sys = f"Você é o MentorEdu, assistente oficial do IF. Área: {area}. Responda de forma acadêmica e técnica."
            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role":"system","content":sys}, {"role":"user","content":f"Contexto: {contexto}\n\nPergunta: {p}"}],
                stream=True
            )
            res = st.write_stream(stream)
            st.session_state.chat.append({"role": "assistant", "content": res})
        else:
            st.error("Por favor, adicione a GROQ_API_KEY nos Secrets do Streamlit.")
