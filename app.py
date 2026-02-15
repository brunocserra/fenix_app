import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURAÇÃO IA ---
GENAI_KEY = "AIzaSyCAupRudeVbP7QSSw7v4BDjG0zJ4Y5XE-0"
genai.configure(api_key=GENAI_KEY)
model = genai.GenerativeModel('models/gemini-2.0-flash')

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def load_data():
    df = pd.read_csv("planeamento_ist_detalhado_2026.csv", encoding="utf-8-sig")
    df['id_cadeira'] = df['id_cadeira'].astype(str)
    return df

df = load_data()

st.title("🚀 IST Planner - Otimização de Quota 2.0")

# --- LÓGICA DE OTIMIZAÇÃO DE TOKENS ---
# Criamos uma base leve para a IA. O 'programa' é consultado apenas via Explorador Manual.
# Isso reduz o payload em cerca de 90%, evitando o erro 429.
df_ia = df[['sigla_curso_ref', 'nome_cadeira', 'ects', 'periodo', 'metodo_avaliacao']]
contexto_ia = df_ia.to_csv(index=False)

tab1, tab2 = st.tabs(["🔍 Explorador Detalhado", "🤖 Chat (Single Request Mode)"])

with tab1:
    st.info("Usa esta tab para ler os programas detalhados das cadeiras.")
    # ... (lógica do explorador manual que já tens no código anterior)

with tab2:
    st.header("Assistente IA")
    st.caption("Esta tab envia apenas dados estruturados para garantir estabilidade na quota.")

    # Inicializa o histórico se não existir
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostra o histórico guardado (sem fazer novos pedidos à API)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada de texto
    if prompt := st.chat_input("Como posso ajudar no teu planeamento?"):
        # Adiciona a pergunta ao estado da sessão
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Geração de resposta (Executa APENAS UMA VEZ por prompt)
        with st.chat_message("assistant"):
            full_prompt = f"""
            Contexto: IST 2º Semestre 2025/2026.
            Utilizador: Engenheiro Aeroespacial (Responde com rigor técnico).
            Regra: Referir colunas como `nome_cadeira`.
            
            DADOS:
            {contexto_ia}
            
            Pergunta: {prompt}
            """
            
            try:
                # O pedido só é feito aqui, após o input do utilizador
                response = model.generate_content(full_prompt)
                res_text = response.text
                st.markdown(res_text)
                
                # Guarda a resposta para evitar re-geração no re-run do Streamlit
                st.session_state.messages.append({"role": "assistant", "content": res_text})
            
            except Exception as e:
                st.error(f"Erro na API: {e}")
                st.info("Aguarde 60 segundos. Se o erro persistir, o volume de dados ainda é alto para a sua quota atual.")
