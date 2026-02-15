import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURAÇÃO IA ---
# Chave fornecida: AIzaSyCAupRudeVbP7QSSw7v4BDjG0zJ4Y5XE-0
GENAI_KEY = "AIzaSyCAupRudeVbP7QSSw7v4BDjG0zJ4Y5XE-0"
genai.configure(api_key=GENAI_KEY)

# Configuração rigorosa do Modelo Flash para evitar Erro 404
# O prefixo 'models/' é essencial em algumas versões da biblioteca
model = genai.GenerativeModel('models/gemini-1.5-flash')

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IST Planner GPT", layout="wide", page_icon="🎓")

@st.cache_data
def load_data():
    try:
        # Carregamento do ficheiro gerado pelo script anterior
        df = pd.read_csv("planeamento_ist_detalhado_2026.csv", encoding="utf-8-sig")
        # Garantir que IDs não apareçam com vírgulas de milhar
        df['id_cadeira'] = df['id_cadeira'].astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar ficheiro CSV: {e}")
        return pd.DataFrame()

df = load_data()

# --- INTERFACE ---
st.title("🚀 IST Smart Planner & AI Assistant")
st.markdown("---")

# Abas para separação de funções
tab_explorador, tab_chat = st.tabs(["🔍 Explorador de Disciplinas", "🤖 Assistente IA (Chat)"])

# --- TAB 1: EXPLORADOR MANUAL ---
with tab_explorador:
    st.sidebar.header("Filtros de Procura")
    # Filtro por texto (Nome, Sigla ou ID)
    search = st.sidebar.text_input("Procurar (Ex: MEGE, Aero, 3379...)", "").lower()
    
    # Filtro por Período
    periodos = ["Todos"] + sorted(df['periodo'].dropna().unique().tolist())
    periodo_sel = st.sidebar.selectbox("Filtrar por Período", periodos)

    mask = (df['sigla_curso_ref'].str.lower().str.contains(search, na=False) | 
            df['nome_cadeira'].str.lower().str.contains(search, na=False) |
            df['id_cadeira'].str.contains(search, na=False))
    
    if periodo_sel != "Todos":
        mask = mask & (df['periodo'] == periodo_sel)
    
    df_filtered = df[mask]
    
    if not df_filtered.empty:
        # Formatação de etiquetas usando pelicas conforme as preferências
        df_filtered['label'] = "[" + df_filtered['sigla_curso_ref'] + "] " + df_filtered['nome_cadeira']
        
        escolha = st.selectbox("Selecione uma disciplina para detalhes:", ["-- Selecione --"] + sorted(df_filtered['label'].tolist()))
        
        if escolha != "-- Selecione --":
            row = df_filtered[df_filtered['label'] == escolha].iloc[0]
            
            c1, c2 = st.columns([2, 1])
            with c1:
                st.header(row['nome_cadeira'])
                st.subheader("📖 Programa")
                st.write(row['programa'] if pd.notna(row['programa']) else "Informação não disponível.")
                
                st.subheader("📝 Método de Avaliação")
                st.info(row['metodo_avaliacao'] if pd.notna(row['metodo_avaliacao']) else "Detalhes não especificados.")
            
            with c2:
                st.metric("Créditos ECTS", row['ects'])
                st.metric("Período Letivo", row['periodo'])
                st.write("**👨‍🏫 Corpo Docente:**")
                docentes = str(row['docentes']).split(" | ") if pd.notna(row['docentes']) else ["Não listados"]
                for d in docentes:
                    st.write(f"- {d}")
                st.divider()
                st.link_button("🌐 Ver no Fénix", row['url_curso'])
    else:
        st.warning("Nenhuma disciplina encontrada com os critérios atuais.")

# --- TAB 2: ASSISTENTE IA (CHAT) ---
with tab_chat:
    st.header("🤖 Inteligência Artificial sobre o IST")
    st.info("O assistente utiliza o modelo **Gemini 1.5 Flash** e tem acesso a toda a tabela CSV.")

    # Preparação do contexto: CSV é mais eficiente que Markdown para o Flash
    # Enviamos apenas colunas essenciais para poupar tokens e manter a precisão
    contexto_ia = df[['sigla_curso_ref', 'nome_cadeira', 'ects', 'periodo', 'metodo_avaliacao', 'programa']].to_csv(index=False)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Histórico de conversação
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Pergunte algo (ex: Quais as cadeiras de P4 com exame em MEGE?)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Prompt de Engenharia para o Gemini
            full_prompt = f"""
            Tu és um consultor de planeamento académico do IST.
            O teu utilizador é um Engenheiro Aeroespacial e empresário. Responde de forma estruturada.
            
            Usa APENAS os dados abaixo para responder:
            {contexto_ia}
            
            Regra: Ao referir nomes de colunas como sigla_curso_ref ou nome_cadeira, usa sempre `pelicas`.
            Pergunta: {prompt}
            """
            
            try:
                # Geração da resposta
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erro na API Gemini: {e}")
                st.write("Dica: Verifica se instalaste a versão mais recente da biblioteca: pip install -U google-generativeai")
