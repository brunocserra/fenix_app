import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURAÇÃO IA ---
GENAI_KEY = "AIzaSyCAupRudeVbP7QSSw7v4BDjG0zJ4Y5XE-0"
genai.configure(api_key=GENAI_KEY)

# Tentativa de inicialização robusta
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    # Teste rápido para validar se o modelo responde
    _test = model.generate_content("test") 
    api_ready = True
except Exception as e:
    api_ready = False
    erro_msg = str(e)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IST Planner GPT", layout="wide", page_icon="🎓")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("planeamento_ist_detalhado_2026.csv", encoding="utf-8-sig")
        df['id_cadeira'] = df['id_cadeira'].astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar CSV: {e}")
        return pd.DataFrame()

df = load_data()

# --- INTERFACE ---
st.title("🚀 IST Smart Planner & AI Assistant")

if not api_ready:
    st.error(f"⚠️ Erro ao ligar ao Gemini 1.5 Flash: {erro_msg}")
    with st.expander("🛠️ Diagnóstico de Engenharia - Modelos Disponíveis"):
        try:
            # Lista todos os modelos disponíveis para esta chave
            modelos = [m.name for m in genai.list_models()]
            st.write("A tua chave API tem acesso aos seguintes modelos:")
            st.code("\n".join(modelos))
            st.info("Dica: Se 'models/gemini-1.5-flash' não aparecer, a tua região ou versão do SDK pode estar limitada.")
        except Exception as diag_err:
            st.write(f"Não foi possível listar os modelos: {diag_err}")

tab_explorador, tab_chat = st.tabs(["🔍 Explorador Manual", "🤖 Assistente IA"])

# --- TAB 1: EXPLORADOR MANUAL ---
with tab_explorador:
    st.sidebar.header("Filtros")
    search = st.sidebar.text_input("Procurar (Cadeira, Sigla ou ID)", "").lower()
    mask = (df['sigla_curso_ref'].str.lower().str.contains(search, na=False) | 
            df['nome_cadeira'].str.lower().str.contains(search, na=False))
    df_filtered = df[mask]
    
    if not df_filtered.empty:
        df_filtered['label'] = "[" + df_filtered['sigla_curso_ref'] + "] " + df_filtered['nome_cadeira']
        escolha = st.selectbox("Selecione uma UC:", ["-- Selecione --"] + sorted(df_filtered['label'].tolist()))
        if escolha != "-- Selecione --":
            row = df_filtered[df_filtered['label'] == escolha].iloc[0]
            st.header(row['nome_cadeira'])
            st.write(f"**Programa:** {row['programa']}")
            st.info(f"**Avaliação:** {row['metodo_avaliacao']}")

# --- TAB 2: ASSISTENTE IA (CHAT) ---
with tab_chat:
    if not api_ready:
        st.warning("O Chat está desativado devido ao erro de conexão acima.")
    else:
        st.header("🤖 Chat com os Dados")
        contexto_ia = df[['sigla_curso_ref', 'nome_cadeira', 'ects', 'periodo', 'metodo_avaliacao', 'programa']].to_csv(index=False)

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ex: Quais as cadeiras com exame em MEGE?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                full_prompt = f"Dados IST:\n{contexto_ia}\n\nPergunta: {prompt}\nResponde de forma técnica."
                try:
                    response = model.generate_content(full_prompt)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Erro no processamento: {e}")
