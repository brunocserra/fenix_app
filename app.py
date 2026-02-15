import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURAÇÃO IA ---
# Chave fornecida pelo utilizador
GENAI_KEY = "AIzaSyCAupRudeVbP7QSSw7v4BDjG0zJ4Y5XE-0"
genai.configure(api_key=GENAI_KEY)

# Configuração do Modelo Flash (Escalão Gratuito: 15 RPM / 1500 RPD)
generation_config = {
  "temperature": 0.2, # Menor temperatura = Respostas mais técnicas e menos criativas
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 2048,
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IST Planner GPT - Full Context", layout="wide", page_icon="🎓")

@st.cache_data
def load_data():
    try:
        # Carregamento do ficheiro detalhado gerado pelo script anterior
        df = pd.read_csv("planeamento_ist_detalhado_2026.csv", encoding="utf-8-sig")
        df['id_cadeira'] = df['id_cadeira'].astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar ficheiro CSV: {e}")
        return pd.DataFrame()

df = load_data()

# --- INTERFACE ---
st.title("🚀 IST Smart Planner & AI Assistant")
st.markdown("---")

# Separação por Tabs: Navegação Clássica vs. Inteligência Artificial
tab_explorador, tab_chat = st.tabs(["🔍 Explorador de Disciplinas", "🤖 Assistente IA (Contexto Total)"])

# --- TAB 1: EXPLORADOR MANUAL ---
with tab_explorador:
    st.sidebar.header("Filtros de Procura")
    search = st.sidebar.text_input("Procurar por Nome, Sigla ou ID", "").lower()
    
    # Lógica de filtragem rápida para a interface manual
    mask = (df['sigla_curso_ref'].str.lower().str.contains(search, na=False) | 
            df['nome_cadeira'].str.lower().str.contains(search, na=False) |
            df['id_cadeira'].str.contains(search, na=False))
    
    df_filtered = df[mask]
    
    if not df_filtered.empty:
        # Seletor formatado com pelicas conforme solicitado no perfil
        df_filtered['label'] = "[" + df_filtered['sigla_curso_ref'] + "] " + df_filtered['nome_cadeira']
        
        escolha = st.selectbox("Selecione uma Unidade Curricular:", ["-- Escolha uma opção --"] + sorted(df_filtered['label'].tolist()))
        
        if escolha != "-- Escolha uma opção --":
            row = df_filtered[df_filtered['label'] == escolha].iloc[0]
            
            c1, c2 = st.columns([2, 1])
            with c1:
                st.header(row['nome_cadeira'])
                st.subheader("📖 Programa")
                st.write(row['programa'] if pd.notna(row['programa']) else "N/A")
                st.subheader("📝 Método de Avaliação")
                st.info(row['metodo_avaliacao'] if pd.notna(row['metodo_avaliacao']) else "N/A")
            
            with c2:
                st.metric("ECTS", row['ects'])
                st.metric("Período", row['periodo'])
                st.write("**👨‍🏫 Docentes:**")
                for d in str(row['docentes']).split(" | "):
                    st.write(f"- {d}")
                st.link_button("🌐 Abrir no Fénix", row['url_curso'])
    else:
        st.warning("Nenhuma disciplina encontrada.")

# --- TAB 2: ASSISTENTE IA (CHAT) ---
with tab_chat:
    st.header("🤖 Conversar com os Dados do IST")
    st.caption("O Gemini Flash está a ler o teu ficheiro completo para responder.")

    # Preparação do Contexto para a IA (Enviando a tabela completa sem filtros)
    # Convertemos para Markdown para a IA entender melhor a estrutura de tabela
    contexto_ia = df[['sigla_curso_ref', 'nome_cadeira', 'ects', 'periodo', 'metodo_avaliacao', 'programa']].to_markdown(index=False)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Exibição das mensagens do histórico
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada do Chat
    if prompt := st.chat_input("Ex: Quais as cadeiras de Aeroespacial com projetos em grupo no P4?"):
        # Adicionar pergunta do utilizador ao histórico
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Prompt de Sistema para garantir rigor técnico
            full_prompt = f"""
            Contexto: Tu és um consultor de planeamento académico do Instituto Superior Técnico.
            Estás a analisar os dados do 2º Semestre de 2025/2026.
            O utilizador é um Engenheiro Aeroespacial e empresário que valoriza rigor e dados estruturados.
            
            Instrução: Responde à pergunta usando EXCLUSIVAMENTE os dados fornecidos abaixo. 
            Se a resposta envolver fórmulas ou referências a colunas, usa pelicas (ex: `nome_cadeira`).
            
            DADOS (CSV/Markdown):
            {contexto_ia}
            
            Pergunta: {prompt}
            """
            
            try:
                # Gerar resposta via API
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                # Guardar resposta no histórico
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erro na comunicação com o Gemini: {e}")
