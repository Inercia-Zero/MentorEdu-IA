import os
import io
import re
import base64
import tempfile

import streamlit as st
from pypdf import PdfReader
import faiss
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
from PIL import Image
from groq import Groq
from sentence_transformers import SentenceTransformer

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="MentorEdu | Projeto Inércia Zero",
    page_icon="🎓",
    layout="wide"
)

IF_LOGO = "logo.png"

# =========================================================
# ESTILO
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
        font-size: 2.5rem;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        text-align: center;
        color: #4b5563;
        font-size: 1rem;
        margin-bottom: 1.2rem;
    }

    .project-badge {
        text-align: center;
        color: white;
        background: #2f8f3a;
        padding: 0.45rem 0.9rem;
        border-radius: 999px;
        width: fit-content;
        margin: 0 auto 1rem auto;
        font-weight: 700;
    }

    .stButton > button {
        background-color: #2f8f3a !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.55rem 1rem !important;
    }

    .status-box {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 0.8rem 1rem;
        background: #f8fafc;
    }

    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# ESTADO DA SESSÃO
# =========================================================
if "chat" not in st.session_state:
    st.session_state.chat = []

if "db" not in st.session_state:
    st.session_state.db = None

if "pdf_nome" not in st.session_state:
    st.session_state.pdf_nome = None

if "ultima_imagem_nome" not in st.session_state:
    st.session_state.ultima_imagem_nome = None

# =========================================================
# RECURSOS
# =========================================================
@st.cache_resource
def carregar_embeddings():
    return SentenceTransformer("all-MiniLM-L6-v2")

def carregar_cliente():
    if "GROQ_API_KEY" not in st.secrets:
        return None, "A chave GROQ_API_KEY não foi encontrada nos Secrets do Streamlit Cloud."

    chave = str(st.secrets["GROQ_API_KEY"]).strip()
    if not chave:
        return None, "A chave GROQ_API_KEY está vazia."

    try:
        client = Groq(api_key=chave)
        return client, None
    except Exception as e:
        return None, f"Erro ao iniciar cliente Groq: {e}"

embed_model = carregar_embeddings()
client, erro_cliente = carregar_cliente()

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================
def obter_prompt_sistema(perfil_escolhido: str) -> str:
    if perfil_escolhido == "Especialista Normativo":
        return (
            "Você é um especialista acadêmico e institucional em normas, relatórios, projetos, "
            "documentos oficiais e produção textual formal. "
            "Responda com linguagem clara, formal, técnica e organizada. "
            "Ao escrever relatórios, pareceres, justificativas ou textos acadêmicos, use estrutura lógica, "
            "objetividade e tom institucional."
        )

    elif perfil_escolhido == "Tutor de Exercícios":
        return (
            "Você é um tutor especialista em resolução de exercícios, com foco muito forte em matemática. "
            "Resolva passo a passo, explique cada etapa com clareza, destaque fórmulas, raciocínio e verificação final. "
            "Nunca pule etapas importantes."
        )

    elif perfil_escolhido == "Professor de Matemática (Ensino Médio)":
        return (
            "Você é um professor de matemática do ensino médio. "
            "Explique com linguagem simples, didática, paciente e clara. "
            "Domina conteúdos como operações algébricas, equações, sistemas, funções, geometria, trigonometria, "
            "logaritmos, progressões, análise combinatória e probabilidade básica. "
            "Use exemplos simples e ensine como se estivesse explicando em sala de aula."
        )

    elif perfil_escolhido == "Professor de Matemática (Ensino Superior)":
        return (
            "Você é um professor universitário de matemática. "
            "Responda com profundidade, rigor e clareza. "
            "Domina pré-cálculo, cálculo 1, cálculo 2, cálculo 3, limites, derivadas, integrais, "
            "equações diferenciais introdutórias, álgebra linear, geometria analítica e demonstrações matemáticas. "
            "Quando apropriado, utilize notação matemática, linguagem técnica e argumentação formal."
        )

    elif perfil_escolhido == "Coordenador Institucional":
        return (
            "Você é um coordenador institucional e educacional do IFCE. "
            "Responda dúvidas sobre cursos, rotinas acadêmicas, procedimentos, documentos, apoio ao estudante, "
            "orientação pedagógica e informações institucionais. "
            "Seu tom deve ser acolhedor, claro, organizado e confiável."
        )

    return "Você é um assistente educacional útil, claro e objetivo."

def processar_pdf(pdf_file):
    leitor = PdfReader(pdf_file)
    txts = []
    pgs = []

    for i, pagina in enumerate(leitor.pages):
        conteudo = pagina.extract_text()
        if conteudo:
            conteudo = conteudo.strip()
            if conteudo:
                partes = [conteudo[j:j+700] for j in range(0, len(conteudo), 700)]
                for parte in partes:
                    parte = parte.strip()
                    if parte:
                        txts.append(parte)
                        pgs.append(i + 1)

    if not txts:
        return None

    vecs = embed_model.encode(txts)
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
        v_q = embed_model.encode([pergunta])
        v_q = np.array(v_q).astype("float32")
        total_chunks = len(st.session_state.db["txts"])
        k = min(k, total_chunks)

        _, ids = st.session_state.db["idx"].search(v_q, k=k)

        contexto = []
        for i in ids[0]:
            pagina = st.session_state.db["pgs"][i]
            texto = st.session_state.db["txts"][i]
            contexto.append(f"[Página {pagina}] {texto}")

        return "\n\n".join(contexto)
    except Exception as e:
        return f"Erro ao buscar contexto do PDF: {e}"

def imagem_para_data_url(uploaded_file):
    mime = uploaded_file.type or "image/png"
    dados = uploaded_file.read()
    b64 = base64.b64encode(dados).decode("utf-8")
    return f"data:{mime};base64,{b64}"

def analisar_imagem_com_vision(prompt_usuario: str, perfil: str, uploaded_image):
    """
    Usa modelo multimodal da Groq para interpretar imagem.
    A Groq documenta visão com o modelo meta-llama/llama-4-scout-17b-16e-instruct. 
    """
    if client is None:
        return "Cliente Groq não disponível."

    uploaded_image.seek(0)
    data_url = imagem_para_data_url(uploaded_image)

    sys_prompt = obter_prompt_sistema(perfil)
    instrucao = (
        f"{sys_prompt}\n\n"
        "A imagem enviada pode conter conteúdo matemático, gráfico, anotação, exercício, página de caderno, "
        "quadro ou material impresso. Identifique o que aparece, transcreva o que for legível, "
        "explique o conteúdo e ajude o usuário com base na imagem."
    )

    resp = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": instrucao},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_usuario},
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url}
                    }
                ]
            }
        ],
        temperature=0.3,
        max_completion_tokens=1400,
        stream=False
    )

    return resp.choices[0].message.content

def responder_texto(prompt_usuario: str, perfil: str, contexto: str):
    sys_prompt = obter_prompt_sistema(perfil)

    mensagem_usuario = f"""
Responda à pergunta do usuário com base no contexto abaixo quando ele for útil.
Se o contexto não for suficiente, responda com honestidade e use conhecimento geral de forma prudente.

Se a pergunta for de matemática:
- explique passo a passo;
- mostre fórmulas quando necessário;
- organize a resolução com clareza;
- priorize o aprendizado;
- se houver demonstração, explique a lógica da demonstração;
- se houver mais de um caminho, cite o melhor.

Contexto:
{contexto if contexto else "Nenhum contexto adicional disponível."}

Pergunta do usuário:
{prompt_usuario}
"""

    stream = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": mensagem_usuario}
        ],
        temperature=0.5,
        max_completion_tokens=1800,
        stream=True
    )

    resposta = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            resposta += delta
            yield resposta

def extrair_expressao_grafico(prompt: str):
    texto = prompt.lower().strip()

    padroes = [
        r"gr[aá]fico de (.+)",
        r"plot de (.+)",
        r"desenhe a fun[cç][aã]o (.+)",
        r"fa[cç]a o gr[aá]fico de (.+)"
    ]

    for padrao in padroes:
        m = re.search(padrao, texto)
        if m:
            return m.group(1).strip()

    return None

def normalizar_expressao(expr: str):
    expr = expr.replace("^", "**")
    expr = expr.replace("sen(", "sin(")
    expr = expr.replace("tg(", "tan(")
    expr = expr.replace("ln(", "log(")
    return expr

def gerar_grafico_basico(expressao_str: str):
    try:
        expr_limpa = normalizar_expressao(expressao_str)

        x = sp.symbols("x")
        expr = sp.sympify(expr_limpa)
        f = sp.lambdify(x, expr, "numpy")

        valores_x = np.linspace(-10, 10, 600)
        valores_y = f(valores_x)

        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(valores_x, valores_y)
        ax.axhline(0)
        ax.axvline(0)
        ax.set_title(f"Gráfico de y = {expressao_str}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.grid(True)

        st.pyplot(fig)
        plt.close(fig)
        return True, None
    except Exception as e:
        return False, str(e)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    if os.path.exists(IF_LOGO):
        st.image(IF_LOGO, use_container_width=True)

    st.markdown("---")

    perfil = st.radio(
        "Selecione o Mentor:",
        [
            "Especialista Normativo",
            "Tutor de Exercícios",
            "Professor de Matemática (Ensino Médio)",
            "Professor de Matemática (Ensino Superior)",
            "Coordenador Institucional"
        ]
    )

    st.markdown("### Materiais")
    pdf_input = st.file_uploader("Enviar PDF", type=["pdf"])
    img_input = st.file_uploader("Enviar imagem", type=["png", "jpg", "jpeg", "webp"])

    st.markdown("### Modo")
    modo = st.selectbox(
        "Escolha o modo de trabalho:",
        [
            "Chat Geral",
            "Matemática",
            "Análise de Imagem",
            "PDF + Chat"
        ]
    )

    if st.button("Limpar Ambiente"):
        st.session_state.chat = []
        st.session_state.db = None
        st.session_state.pdf_nome = None
        st.session_state.ultima_imagem_nome = None
        st.rerun()

# =========================================================
# PROCESSAMENTO PDF
# =========================================================
if pdf_input is not None:
    if st.session_state.pdf_nome != pdf_input.name:
        with st.spinner("Processando PDF..."):
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
                st.error(f"Erro ao processar PDF: {e}")

# =========================================================
# CABEÇALHO
# =========================================================
st.markdown('<div class="project-badge">Projeto Inércia Zero</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">MentorEdu IFCE</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Assistente acadêmico inteligente com foco institucional, educacional e matemático</div>',
    unsafe_allow_html=True
)

# =========================================================
# STATUS
# =========================================================
c1, c2, c3 = st.columns(3)

with c1:
    if erro_cliente:
        st.error("Groq: erro de configuração")
    else:
        st.success("Groq conectada")

with c2:
    if st.session_state.db:
        st.success(f"PDF ativo: {st.session_state.pdf_nome}")
    else:
        st.info("Sem PDF ativo")

with c3:
    if img_input is not None:
        st.success(f"Imagem ativa: {img_input.name}")
    else:
        st.info("Sem imagem ativa")

# =========================================================
# PRÉ-VISUALIZAÇÃO DA IMAGEM
# =========================================================
if img_input is not None:
    try:
        img = Image.open(img_input)
        st.image(img, caption=f"Imagem enviada: {img_input.name}", use_container_width=True)
        img_input.seek(0)
    except Exception as e:
        st.warning(f"Não consegui abrir a imagem: {e}")

# =========================================================
# HISTÓRICO
# =========================================================
avatar_path = IF_LOGO if os.path.exists(IF_LOGO) else None

for msg in st.session_state.chat:
    with st.chat_message(msg["role"], avatar=avatar_path):
        st.markdown(msg["content"])

# =========================================================
# ENTRADA
# =========================================================
placeholder_text = "Digite sua pergunta..."
if modo == "Matemática":
    placeholder_text = "Ex.: resolva x² - 5x + 6 = 0 ou faça o gráfico de x^2 - 4"
elif modo == "Análise de Imagem":
    placeholder_text = "Ex.: interprete esta foto / leia esta questão / explique este gráfico"
elif modo == "PDF + Chat":
    placeholder_text = "Ex.: resuma o PDF / explique a página 3 / resolva a questão do material"

prompt = st.chat_input(placeholder_text)

if prompt:
    st.session_state.chat.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar=avatar_path):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=avatar_path):
        placeholder = st.empty()

        if client is None:
            resposta_final = (
                "Não consegui responder porque a chave da API Groq não está configurada corretamente."
            )
            placeholder.markdown(resposta_final)
            st.session_state.chat.append({"role": "assistant", "content": resposta_final})

        else:
            try:
                # 1) MODO IMAGEM
                if modo == "Análise de Imagem":
                    if img_input is None:
                        resposta_final = "Envie uma imagem na barra lateral para que eu possa interpretá-la."
                    else:
                        img_input.seek(0)
                        resposta_final = analisar_imagem_com_vision(prompt, perfil, img_input)

                    placeholder.markdown(resposta_final)
                    st.session_state.chat.append({"role": "assistant", "content": resposta_final})

                # 2) MODO MATEMÁTICA
                elif modo == "Matemática":
                    expr_grafico = extrair_expressao_grafico(prompt)

                    contexto = buscar_contexto(prompt, k=3) if st.session_state.db else ""

                    resposta_final = ""
                    for parcial in responder_texto(prompt, perfil, contexto):
                        resposta_final = parcial
                        placeholder.markdown(resposta_final)

                    if expr_grafico:
                        ok, erro = gerar_grafico_basico(expr_grafico)
                        if not ok:
                            st.warning(f"Não consegui gerar o gráfico: {erro}")

                    if not resposta_final.strip():
                        resposta_final = "Não consegui gerar uma resposta no momento."

                    st.session_state.chat.append({"role": "assistant", "content": resposta_final})

                # 3) MODO PDF + CHAT
                elif modo == "PDF + Chat":
                    contexto = buscar_contexto(prompt, k=4) if st.session_state.db else ""
                    resposta_final = ""

                    for parcial in responder_texto(prompt, perfil, contexto):
                        resposta_final = parcial
                        placeholder.markdown(resposta_final)

                    if not resposta_final.strip():
                        resposta_final = "Não consegui gerar uma resposta no momento."

                    st.session_state.chat.append({"role": "assistant", "content": resposta_final})

                # 4) CHAT GERAL
                else:
                    contexto = buscar_contexto(prompt, k=3) if st.session_state.db else ""
                    resposta_final = ""

                    for parcial in responder_texto(prompt, perfil, contexto):
                        resposta_final = parcial
                        placeholder.markdown(resposta_final)

                    if not resposta_final.strip():
                        resposta_final = "Não consegui gerar uma resposta no momento."

                    st.session_state.chat.append({"role": "assistant", "content": resposta_final})

            except Exception as e:
                resposta_erro = f"Erro ao consultar a Groq: {e}"
                placeholder.markdown(resposta_erro)
                st.session_state.chat.append({"role": "assistant", "content": resposta_erro})
