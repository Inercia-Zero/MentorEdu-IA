import streamlit as st
from pypdf import PdfReader
import os, faiss, numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================

st.set_page_config(page_title="MentorEdu | IFCE", page_icon="🎓")

IF_LOGO = "logo.png"

st.markdown("""
<style>
.stApp {background-color: #ffffff;}

.main-title{
text-align:center;
color:#32a041;
font-weight:800;
font-size:2.3rem;
}

.sub-title{
text-align:center;
font-size:1rem;
color:#444;
}

.project{
text-align:center;
font-size:0.9rem;
color:#888;
margin-bottom:25px;
}

.stButton>button{
background-color:#32a041 !important;
color:white !important;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# ESTADOS
# =====================================================

if "chat" not in st.session_state:
    st.session_state.chat = []

if "db" not in st.session_state:
    st.session_state.db = None

# =====================================================
# CARREGAMENTO
# =====================================================

@st.cache_resource
def carregar_sistema():
    chave = st.secrets.get("GROQ_API_KEY", "").strip()
    client = Groq(api_key=chave)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return client, model

client, model = carregar_sistema()

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    if os.path.exists(IF_LOGO):
        st.image(IF_LOGO, use_container_width=True)

    st.markdown("---")

    perfil = st.radio(
        "Selecione o Mentor:",
        [
            "Especialista Normativo",
            "Tutor de Exercícios",
            "Professor Didático",
            "Coordenador Educacional IFCE"
        ]
    )

    pdf_input = st.file_uploader("Enviar material PDF", type="pdf")

    if st.button("Limpar conversa"):
        st.session_state.chat = []
        st.session_state.db = None
        st.rerun()

# =====================================================
# PROCESSAMENTO PDF
# =====================================================

if pdf_input and st.session_state.db is None:

    with st.spinner("Processando PDF..."):

        leitor = PdfReader(pdf_input)

        txts = []
        pgs = []

        for i, pag in enumerate(leitor.pages):

            conteudo = pag.extract_text()

            if conteudo:

                partes = [conteudo[j:j+500] for j in range(0, len(conteudo), 500)]

                for p in partes:
                    txts.append(p.strip())
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

# =====================================================
# CABEÇALHO
# =====================================================

st.markdown('<h1 class="main-title">MentorEdu IFCE</h1>', unsafe_allow_html=True)

st.markdown(
'<div class="sub-title">Assistente acadêmico educacional</div>',
unsafe_allow_html=True
)

st.markdown(
'<div class="project">Projeto de Pesquisa • Inércia Zero</div>',
unsafe_allow_html=True
)

# =====================================================
# HISTÓRICO CHAT
# =====================================================

av = IF_LOGO if os.path.exists(IF_LOGO) else None

for m in st.session_state.chat:

    with st.chat_message(m["role"], avatar=av):
        st.write(m["content"])

# =====================================================
# PROMPTS DAS IAs
# =====================================================

def obter_prompt(perfil):

    if perfil == "Especialista Normativo":

        return """
Você é um especialista acadêmico em elaboração de relatórios,
artigos científicos, documentos institucionais e normas acadêmicas.

Seu papel é ajudar estudantes e pesquisadores a produzir textos
profissionais seguindo padrões formais, técnicos e acadêmicos.

Use linguagem formal, objetiva e bem estruturada.
"""

    elif perfil == "Tutor de Exercícios":

        return """
Você é um tutor especialista em resolução de exercícios.

Seu objetivo é ajudar o aluno a resolver problemas passo a passo,
explicando cada etapa de forma clara.

Sempre mostre o raciocínio e incentive o aprendizado.
"""

    elif perfil == "Professor Didático":

        return """
Você é um professor didático especializado em ensino médio e superior.

Explique conteúdos de forma clara, simples e pedagógica.
Use exemplos, analogias e linguagem acessível para facilitar o entendimento.
"""

    else:

        return """
Você é o Coordenador Educacional do IFCE.

Seu papel é orientar estudantes sobre:

• funcionamento da instituição
• dúvidas acadêmicas
• disciplinas
• organização dos estudos
• orientações educacionais

Responda de forma clara e institucional.
"""

# =====================================================
# CHAT
# =====================================================

if prompt := st.chat_input("Como posso ajudar?"):

    st.session_state.chat.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar=av):
        st.write(prompt)

    with st.chat_message("assistant", avatar=av):

        contexto = ""

        if st.session_state.db:

            v_q = model.encode([prompt])

            v_q = np.array(v_q).astype("float32")

            _, ids = st.session_state.db["idx"].search(v_q, k=2)

            for i in ids[0]:

                contexto += f"[Pág {st.session_state.db['pgs'][i]}] {st.session_state.db['txts'][i]}\n\n"

        sys = obter_prompt(perfil)

        resposta = ""

        stream = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": f"Contexto: {contexto}\n\nPergunta: {prompt}"}
            ],
            stream=True
        )

        placeholder = st.empty()

        for chunk in stream:

            delta = chunk.choices[0].delta.content

            if delta:
                resposta += delta
                placeholder.markdown(resposta)

        st.session_state.chat.append({"role": "assistant", "content": resposta})
