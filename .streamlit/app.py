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
    .stButton>button { background-color: #32a041 !important; color: white !important; width: 100%; }
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
    # Reduzi as áreas para focar nos perfis solicitados
    perfil = st.radio("Selecione o Mentor:", 
                     ["Reitor (Sério)", "Professor (Descontraído)", "Coordenador (Educacional)"])
    
    pdf_input = st.file_uploader("Subir Material de Estudo (PDF)", type="pdf")
    
    if st.button("Limpar Ambiente"):
        st.session_state.chat = []
        st.session_state.db = None
        st.rerun()

# 4. PROCESSAMENTO DO MATERIAL (RAG)
if pdf_input and st.session_state.db is None:
    with st.spinner("Processando base de conhecimento..."):
        leitor = PdfReader(pdf_input)
        frases, paginas = [], []
        for i, pagina in enumerate(leitor.pages):
            texto_pag = pagina.extract_text()
            if texto_pag:
                blocos = [texto_pag[j:j+500] for j in range(0, len(texto_pag), 500)]
                for b in blocos:
                    frases.append(b.strip())
                    paginas.append(i+1)
        if frases:
            vetores = model.encode(frases)
            index_faiss = faiss.IndexFlatL2(vetores.shape[1])
            index_faiss.add(np.array(vetores))
            st.session_state.db = {"idx": index_faiss, "textos": frases, "pgs": paginas}

# 5. INTERFACE DE CHAT UNIFICADA (LOGO DO IF)
st.markdown('<h1 class="main-title">MentorEdu IFCE</h1>', unsafe_allow_html=True)

# Avatar institucional para todas as mensagens
avatar_institucional = IF_LOGO if os.path.exists(IF_LOGO) else None

for m in st.session_state.chat:
    with st.chat_message(m["role"], avatar=avatar_institucional):
        st.write(m["content"])

if prompt := st.chat_input("Diga aí, como posso ajudar nos seus estudos?"):
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=avatar_institucional):
        st.write(prompt)

    with st.chat_message("assistant", avatar=avatar_institucional):
        contexto_pdf = ""
        if st.session_state.db:
            v_query = model.encode([prompt])
            _, ids = st.session_state.db["idx"].search(np.array(v_query), k=2)
            for id_idx in ids[0]:
                contexto_pdf += f"[Pág {st.session_state.db['pgs'][id_idx]}] {st.session_state.db['textos'][id_idx]}\n\n"

        # DEFINIÇÃO DA PERSONALIDADE BASEADA NA ESCOLHA
        if "Reitor" in perfil:
            sys_instrucao = "Você é o Reitor do IFCE. Seu tom é extremamente formal, sério, autoritário mas justo. Responda com foco em normas, excelência e seriedade acadêmica."
        elif "Professor" in perfil:
            sys_instrucao = "Você é um professor gente boa do IFCE. Use um tom leve, levemente engraçado e motivador, mas sem perder o foco no conteúdo técnico."
        else: # Coordenador
            sys_instrucao = "Você é o Coordenador Pedagógico. Seu tom é puramente educativo, focado em metod
