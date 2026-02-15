import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURAÇÃO IA ---
# Chave: AIzaSyCAupRudeVbP7QSSw7v4BDjG0zJ4Y5XE-0
GENAI_KEY = "AIzaSyCAupRudeVbP7QSSw7v4BDjG0zJ4Y5XE-0"
genai.configure(api_key=GENAI_KEY)

# Configuração para o modelo Flash (Gratuito)
# Nota: Se gemini-1.5-flash der 404, a biblioteca precisa de ser atualizada no requirements.txt
model = genai.GenerativeModel('gemini-1.5-flash')

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

st.title("🚀 IST Smart Planner & AI Assistant")
st.markdown("---")

tab_explorador, tab_chat = st.tabs(["🔍 Explorador Manual", "🤖 Assistente IA (Flash)"])

# --- TAB 1: EXPLORADOR MANUAL ---
with tab_explorador:
    st.sidebar.header("Filtros")
    search = st.sidebar.text_input("Procurar (Cadeira, Sigla ou ID)", "").lower()
    
    mask = (df['sigla_curso_ref'].str.lower().str.contains(search, na=False) | 
            df['nome_cadeira'].str.lower().str.contains(search, na=False) |
            df['id_cadeira'].str.contains(search, na=False))
    
    df_filtered = df[mask]
    
    if not df_filtered.empty:
        df_filtered['label'] = "[" + df_filtered['sigla_curso_ref'] + "] " + df_filtered['nome_cadeira']
        escolha = st.selectbox("Selecione uma UC:", ["-- Selecione --"] + sorted(df_filtered['label'].tolist()))
        
        if escolha != "-- Selecione --":
            row = df_filtered[df_filtered['label'] == escolha].iloc[0]
            c1, c2 = st.columns([2, 1])
            with c1:
                st.header(row['nome_cadeira'])
                st.subheader("📖 Programa")
                st.write(row['programa'] if pd.notna(row['programa']) else "N/A")
                st.subheader("📝 Avaliação")
                st.info(row['metodo_avaliacao'] if pd.notna(row['metodo_avaliacao']) else "N/A")
            with c2:
                st.metric("ECTS", row['ects'])
                st.metric("Período", row['periodo'])
                st.write("**Docentes:**", row['docentes'])
                st.link_button("🌐 Fénix", row['url_curso'])

# --- TAB 2: ASSISTENTE IA (CHAT) ---
with tab_chat:
    st.header("🤖 Chat com o Gemini Flash")
    
    # Contexto em CSV (Mais eficiente e evita erros de biblioteca markdown)
    contexto_ia = df[['sigla_curso_ref', 'nome_cadeira', 'ects', 'periodo', 'metodo_avaliacao', 'programa']].to_csv(index=False)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ex: Quais as cadeiras com projetos no P4?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            full_prompt = f"""
            Contexto: Dados do 2º Semestre IST 2025/2026.
            Instrução: Responde apenas com base no CSV fornecido.
            Utilizador: Engenheiro Aeroespacial/Empresário (Sê direto e técnico).
            Regra: Usa `pelicas` para nomes de colunas como `nome_cadeira`.

            DADOS:
            {contexto_ia}

            Pergunta: {prompt}
            """
            
            try:
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erro na API: {e}")
                st.info("💡 Dica de Engenharia: Atualiza o teu requirements.txt para 'google-generativeai>=0.7.2'")
