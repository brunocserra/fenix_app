import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURAÇÃO IA ---
# Integrando a chave que forneceste
GENAI_KEY = "AIzaSyCAupRudeVbP7QSSw7v4BDjG0zJ4Y5XE-0"
genai.configure(api_key=GENAI_KEY)
# Usamos o modelo Flash para respostas rápidas e baixo consumo de tokens
model = genai.GenerativeModel('gemini-1.5-flash')

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IST Planner GPT", layout="wide", page_icon="🚀")

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

# Tabs para separar as funcionalidades
tab_explorador, tab_chat = st.tabs(["🔍 Explorador Manual", "🤖 Assistente IA"])

# --- TAB 1: EXPLORADOR MANUAL ---
with tab_explorador:
    st.sidebar.header("Filtros")
    search = st.sidebar.text_input("Procurar (Sigla ou Cadeira)", "").lower()
    
    mask = (df['sigla_curso_ref'].str.lower().str.contains(search, na=False) | 
            df['nome_cadeira'].str.lower().str.contains(search, na=False))
    
    df_filtered = df[mask]
    
    if not df_filtered.empty:
        df_filtered['label'] = "[" + df_filtered['sigla_curso_ref'] + "] " + df_filtered['nome_cadeira']
        escolha = st.selectbox("Escolha uma disciplina:", ["-- Selecione --"] + sorted(df_filtered['label'].tolist()))
        
        if escolha != "-- Selecione --":
            detalhe = df_filtered[df_filtered['label'] == escolha].iloc[0]
            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader(detalhe['nome_cadeira'])
                st.markdown(f"**Programa:**\n{detalhe['programa']}")
                st.markdown(f"**Avaliação:**\n{detalhe['metodo_avaliacao']}")
            with c2:
                st.metric("ECTS", detalhe['ects'])
                st.metric("Período", detalhe['periodo'])
                st.write("**Docentes:**", detalhe['docentes'])
    else:
        st.warning("Nenhum dado encontrado com os filtros atuais.")

# --- TAB 2: ASSISTENTE IA (CHAT) ---
with tab_chat:
    st.header("Chat com os Dados do IST")
    st.write("Exemplo: 'Quais as cadeiras de MEGE que têm exame?' ou 'Resume o programa de Física I.'")

    # Preparar contexto reduzido para o Chat (otimização de tokens)
    # Enviamos apenas o essencial para a IA conseguir responder
    contexto_csv = df[['sigla_curso_ref', 'nome_cadeira', 'ects', 'metodo_avaliacao', 'programa']].to_string(index=False)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostrar histórico
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Como posso ajudar no teu planeamento?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Prompt estruturado para evitar alucinações
            full_prompt = f"""
            Tu és o 'Gemini IST Advisor', um assistente técnico para alunos do Instituto Superior Técnico.
            O teu conhecimento baseia-se EXCLUSIVAMENTE nesta tabela de dados do 2º Semestre 2025/2026:
            
            {contexto_csv}
            
            Regras:
            1. Responde apenas com base nos dados fornecidos.
            2. Se a informação não estiver na tabela, diz educadamente que não tens esses detalhes.
            3. Usa bullet points para listas de cadeiras.
            4. Sê rigoroso com as siglas dos cursos.
            
            Pergunta do Bruno (Engenheiro Aeroespacial): {prompt}
            """
            
            try:
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erro na API Gemini: {e}")
