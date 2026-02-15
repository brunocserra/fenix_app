import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURAÇÃO IA ---
GENAI_KEY = "AIzaSyCAupRudeVbP7QSSw7v4BDjG0zJ4Y5XE-0"
genai.configure(api_key=GENAI_KEY)

# Ajuste para o modelo que está na tua lista e é ultra-rápido
# Usamos o 2.0-flash para melhor interpretação do programa e avaliação
model = genai.GenerativeModel('models/gemini-2.0-flash')

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IST Planner GPT v2.0", layout="wide", page_icon="🚀")

@st.cache_data
def load_data():
    try:
        # Carregamento do CSV gerado
        df = pd.read_csv("planeamento_ist_detalhado_2026.csv", encoding="utf-8-sig")
        df['id_cadeira'] = df['id_cadeira'].astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar CSV: {e}")
        return pd.DataFrame()

df = load_data()

# --- INTERFACE ---
st.title("🚀 IST Smart Planner & AI Assistant")
st.caption(f"Modelo Ativo: Gemini 2.0 Flash | Utilizador: Bruno (Eng. Aeroespacial)")

tab_explorador, tab_chat = st.tabs(["🔍 Explorador Manual", "🤖 Assistente IA (Nova Geração)"])

# --- TAB 1: EXPLORADOR MANUAL ---
with tab_explorador:
    st.sidebar.header("Filtros de Procura")
    search = st.sidebar.text_input("Procurar por Nome ou Sigla", "").lower()
    
    mask = (df['sigla_curso_ref'].str.lower().str.contains(search, na=False) | 
            df['nome_cadeira'].str.lower().str.contains(search, na=False))
    
    df_filtered = df[mask]
    
    if not df_filtered.empty:
        df_filtered['label'] = "[" + df_filtered['sigla_curso_ref'] + "] " + df_filtered['nome_cadeira']
        escolha = st.selectbox("Selecione uma disciplina:", ["-- Selecione --"] + sorted(df_filtered['label'].tolist()))
        
        if escolha != "-- Selecione --":
            row = df_filtered[df_filtered['label'] == escolha].iloc[0]
            c1, c2 = st.columns([2, 1])
            with c1:
                st.header(row['nome_cadeira'])
                st.subheader("📖 Programa")
                st.write(row['programa'] if pd.notna(row['programa']) else "Informação em falta.")
                st.subheader("📝 Avaliação")
                st.info(row['metodo_avaliacao'] if pd.notna(row['metodo_avaliacao']) else "Sem detalhes.")
            with c2:
                st.metric("Créditos ECTS", row['ects'])
                st.metric("Período", row['periodo'])
                st.write("**Docentes:**", row['docentes'])
                st.link_button("🌐 Abrir no Fénix", row['url_curso'])
    else:
        st.warning("Nenhum resultado encontrado.")

# --- TAB 2: ASSISTENTE IA (CHAT) ---
with tab_chat:
    st.header("🤖 Consulta Inteligente (Gemini 2.0)")
    
    # Preparação do contexto em CSV para economia de tokens
    contexto_ia = df[['sigla_curso_ref', 'nome_cadeira', 'ects', 'periodo', 'metodo_avaliacao', 'programa']].to_csv(index=False)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ex: Quais as cadeiras de Aeroespacial que focam em automação ou HVAC?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Prompt otimizado para o perfil de engenheiro
            full_prompt = f"""
            Contexto Técnico: Dados do 2º Semestre IST 2025/2026.
            Perfil Utilizador: Engenheiro Aeroespacial e empresário. Respostas rigorosas.
            Regra: Usar `pelicas` para referir colunas como `nome_cadeira`.
            
            DADOS IST:
            {contexto_ia}
            
            Pergunta: {prompt}
            """
            try:
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erro no processamento da IA: {e}")
