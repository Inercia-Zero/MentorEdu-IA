import streamlit as st
from pypdf import PdfReader
import os, faiss, numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer

# 1. IDENTIDADE VISUAL IFCE
st.set_page_config(page_title="MentorEdu | IFCE", page_icon="🎓")
IF_LOGO = "logo.png"

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .main-title { text-align: center; color: #32a041; font-weight: 800; font-size: 2.3rem; }
    .stButton>button { background-color: #32a041 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# 2. INICIALIZAÇÃO E CACHE
if "chat" not in st.session_state: st.session_state.chat = []
if "db" not in st.session_state: st.session_state.db = None

@st.cache_resource
def carregar_sistema():
    chave = st.secrets.get("GROQ_API_KEY", "")
    return Groq(api_key=chave), SentenceTransformer("all-MiniLM-L6-v2")

client, model = carregar_sistema()

# 3. BARRA LATERAL (PERSONALIDADES IFCE)
with st.sidebar:
    if os.path.exists(IF_LOGO):
        st.image(IF_LOGO, use_container_width=True)
    st.markdown("---")
    
    perfil = st.radio("Selecione o Mentor:", 
                     ["Reitor (Sério)", "Professor (Engraçado)", "Coordenador (Educacional)"])
    
    pdf_input = st.file_uploader("Subir Material (PDF)", type="pdf")
    
    if st.button("Limpar Ambiente"):
        st.session_state.chat = []
        st.session_state.db = None
        st.rerun()

# 4. PROCESSAMENTO DO PDF
if pdf_input and st.session_state.db is None:
    with st.spinner("Processando..."):
        leitor = PdfReader(pdf_input)
        txts, pgs = [], []
        for i, pag in enumerate(leitor.pages):
            conteudo = pag.extract_text()
            if conteudo:
                partes = [conteudo[j:j+500] for j in range(0, len(conteudo), 500)]
                for p in partes:
                    txts.append(p.strip())
                    pgs.append(i+1)
        if txts:
            vecs = model.encode(txts)
            idx = faiss.IndexFlatL2(vecs.shape[1])
            idx.add(np.array(vecs))
            st.session_state.db = {"idx": idx, "txts": txts, "pgs": pgs}

# 5. INTERFACE DE CHAT (LOGO UNIFICADA)
st.markdown('<h1 class="main-title">MentorEdu IFCE</h1>', unsafe_allow_html=True)
av = IF_LOGO if os.path.exists(IF_LOGO) else None

for m in st.session_state.chat:
    with st.chat_message(m["role"], avatar=av):
        st.write(m["content"])

if prompt := st.chat_input("Como posso ajudar?"):
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=av):
        st.write(prompt)

    with st.chat_message("assistant", avatar=av):
        contexto = ""
        if st.session_state.db:
            v_q = model.encode([prompt])
            _, ids = st.session_state.db["idx"].search(np.array(v_q), k=2)
            for i in ids[0]:
                contexto += f"[Pág {st.session_state.db['pgs'][i]}] {st.session_state.db['txts'][i]}\n\n"

        # DEFINIÇÃO DE PERSONALIDADE
        if "Reitor" in perfil:
            sys = "Você é o Reitor do IFCE. Seu tom é formal, sério e institucional. Foque em excelência."
        elif "Professor" in perfil:
            sys = "Você é um professor do IFCE. Use um tom leve, motivador e levemente engraçado."
        else:
            sys = "Você é o Coordenador Pedagógico. Foco total em didática, paciência e métodos de estudo."

        if client:
            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": sys}, 
                          {"role": "user", "content": f"Contexto: {contexto}\n\nPergunta: {prompt}"}],
                stream=True
            )
