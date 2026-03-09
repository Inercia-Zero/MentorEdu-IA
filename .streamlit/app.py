# 6. CHAT COM AVATAR DO IF PARA AMBOS
st.markdown('<h1 class="main-title">MentorEdu</h1>', unsafe_allow_html=True)

# Avatar institucional único
av = LOGO_INSTITUCIONAL if os.path.exists(LOGO_INSTITUCIONAL) else None

for m in st.session_state.chat:
    with st.chat_message(m["role"], avatar=av):
        st.write(m["content"])

if prompt := st.chat_input("Dúvida acadêmica?"):
    # Mensagem do Aluno
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=av):
        st.write(prompt)

    # Resposta do Mentor (Professor)
    with st.chat_message("assistant", avatar=av):
        ctx = ""
        if st.session_state.db:
            v_q = model.encode([prompt])
            _, ids = st.session_state.db["idx"].search(np.array(v_q), k=2)
            for idx in ids[0]:
                ctx += f"[Pág {st.session_state.db['txts'][idx]}] {st.session_state.db['texts'][idx]}\n\n"

        if client:
            sys = f"Você é o MentorEdu, assistente do IF. Área: {area}. Responda apenas com texto direto e didático."
            
            # Correção para evitar o erro de código JSON no chat
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": sys},
                    {"role": "user", "content": f"Contexto: {ctx}\n\nPergunta: {prompt}"}
                ],
                stream=True
            )
            
            # Captura o texto de forma limpa
            full_res = ""
            placeholder = st.empty()
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    placeholder.markdown(full_res)
            
            st.session_state.chat.append({"role": "assistant", "content": full_res})
