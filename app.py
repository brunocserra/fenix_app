import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURAÇÃO IA ---
GENAI_KEY = "AIzaSyCAupRudeVbP7QSSw7v4BDjG0zJ4Y5XE-0"
genai.configure(api_key=GENAI_KEY)

# MUDANÇA CRÍTICA: Usar o 'gemini-2.0-flash' que tem TPM ILIMITADO no teu dashboard
model = genai.GenerativeModel('models/gemini-2.0-flash')

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IST Planner GPT - Unlocked", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("planeamento_ist_detalhado_2026.csv", encoding="utf-8-sig")
    df['id_cadeira'] = df['id_cadeira'].astype(str)
    return df

df = load_data()

st.title("🚀 IST Smart Planner (Contexto Ilimitado)")

tab1, tab2 = st.tabs(["🔍 Explorador", "🤖 Chat s/ Limites"])

with tab2:
    st.header("Chat com Gemini 2.0 Flash")
    
    # Agora podemos enviar o CSV completo porque o TPM é ilimitado!
    # Mas enviamos em CSV para ser mais rápido
    contexto_ia = df[['sigla_curso_ref', 'nome_cadeira', 'ects', 'periodo', 'metodo_avaliacao', 'programa']].to_csv(index=False)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Pergunta o que quiseres sobre qualquer cadeira..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            # Prompt direto e técnico
            full_prompt = f"Dados IST:\n{contexto_ia}\n\nPergunta: {prompt}"
            try:
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erro: {e}")
