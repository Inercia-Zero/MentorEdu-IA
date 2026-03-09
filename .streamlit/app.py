import streamlit as st
from pypdf import PdfReader
import os, faiss, numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer

# 1. SETUP DA PÁGINA (LOGO DO IF)
st.set_page_config(page_title="MentorEdu | IF", page_icon="🎓")
IF_LOGO = "logo.png"

# CSS para estilo Institucional
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .main-title { text-align: center; color: #32a041; font-weight: 800; font-size: 2.5rem; }
    .stButton>button { background-color: #32a041 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# 2. INICIALIZAÇÃO DE VARIÁVEIS
if "chat" not in st.session_state: st.session_state.chat = []
if "db" not in st.session_state: st.session_state.db = None

@st.cache_resource
def load_ai():
    key = st.secrets.get("GROQ_API_KEY", "")
    return Groq(api_key=key), SentenceTransformer("all-MiniLM-L6-v2")

client, model = load_ai()

# 3. BARRA LATERAL
with st.sidebar:
    if os.path.exists(IF_LOGO):
        st.image(IF_LOGO, use_container_width=True)
    st.markdown("---")
    area = st.selectbox("Área Técnica:", ["Geral", "Informática", "Mecânica", "Química"])
    arquivo = st.file_uploader("Subir PDF", type="pdf")
    if st.button("🔄 Reiniciar Ambiente"):
        st.session_state.chat = []
        st.session_state.db = None
        st.rerun()

# 4. PROCESSAMENTO RAG
if arquivo and st.session_state.db is None:
    with st.spinner("Lendo material..."):
        reader = PdfReader(arquivo)
        textos, pgs = [], []
        for i, page in enumerate(reader.pages):
            c = page.extract_text()
            if c:
                chunks = [c[j:j+500] for j in range(0, len(c), 500)]
                for ch in chunks:
                    textos.append(ch.strip())
                    pgs.append(i+1)
        if textos:
            embs = model.encode(textos)
            idx = faiss.IndexFlatL2(embs.shape[1])
            idx.add(np.array(embs))
            st.session_state.db = {"idx": idx, "textos": textos, "pgs": pgs}

# 5. CHAT COM AVATAR UNIFICADO (ALUNO E PROFESSOR)
st.markdown('<h1 class="main-title">MentorEdu</h1>', unsafe_allow_html=True)

# Define a logo do IF como avatar para ambos
avatar_if = IF_LOGO if os.path.exists(IF_LOGO) else None

for m in st.session_state.chat:
    with st.chat_message(m["role"], avatar=avatar_if):
        st.write(m["content"])

if prompt := st.chat_input("Dúvida acadêmica?"):
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=avatar_if):
        st.write(prompt)

    with st.chat_message("assistant", avatar=avatar_if):
        contexto = ""
        if st.session_state.db:
            v_q = model.encode([prompt])
            _, ids = st.session_state.db["idx"].search(np.array(v_q), k=2)
            for idx in ids[0]:
                contexto += f"[Pág {st.session_state.db['pgs'][idx]}] {st.session_state.db['textos'][idx]}\n\n"

        if client:
            # Resposta limpa (sem JSON/ChoiceDelta)
            sys = f"Você é o MentorEdu, assistente oficial do IF. Área: {area}. Responda apenas com texto."
            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": sys}, 
                          {"role": "user", "content": f"Contexto: {contexto}\n\nPergunta: {prompt}"}],
                stream=True
            )
            
            full_res = ""
            placeholder = st.empty()
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    placeholder.markdown(full_res)
            st.session_state.chat.append({"role": "assistant", "content": full_res})
