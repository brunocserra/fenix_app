import streamlit as st
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IST Planner 2026", layout="wide")

@st.cache_data
def load_data():
    # Carrega o CSV gerado pelo script Turbo
    try:
        df = pd.read_csv("planeamento_ist_detalhado_2026.csv", encoding="utf-8-sig")
        # Garantir que o ID é tratado como string para não aparecer com vírgulas
        df['id_cadeira'] = df['id_cadeira'].astype(str)
        return df
    except FileNotFoundError:
        st.error("Ficheiro 'planeamento_ist_detalhado_2026.csv' não encontrado. Corre o script de extração primeiro.")
        return pd.DataFrame()

# --- INTERFACE PRINCIPAL ---
st.title("🚀 IST Course Explorer & Planner 2026")

df = load_data()

if not df.empty:
    # --- FILTROS NO ECRA INICIAL ---
    st.sidebar.header("🔍 Filtros de Procura")
    
    # Procura por Nome ou Sigla do Curso
    search_term = st.sidebar.text_input("Procurar por Curso ou Sigla", "").lower()
    
    # Filtro por Período
    periodos = ["Todos"] + sorted(df['periodo'].unique().tolist())
    periodo_sel = st.sidebar.selectbox("Filtrar por Período", periodos)

    # Aplicação dos filtros
    mask = (
        (df['nome_curso'].str.lower().contains(search_term) | 
         df['sigla_curso_ref'].str.lower().contains(search_term) |
         df['nome_cadeira'].str.lower().contains(search_term))
    )
    
    if periodo_sel != "Todos":
        mask = mask & (df['periodo'] == periodo_sel)
    
    df_filtered = df[mask]

    # --- LISTAGEM E SELEÇÃO ---
    st.subheader(f"Resultados ({len(df_filtered)} cadeiras encontradas)")
    
    # Criar uma coluna combinada para a seleção
    df_filtered['display_name'] = df_filtered['sigla_curso_ref'] + " - " + df_filtered['nome_cadeira']
    
    escolha = st.selectbox("Selecione uma Unidade Curricular para ver detalhes:", 
                          ["-- Selecione --"] + df_filtered['display_name'].tolist())

    if escolha != "-- Selecione --":
        # Extrair detalhes da linha selecionada
        detalhe = df_filtered[df_filtered['display_name'] == escolha].iloc[0]
        
        st.divider()
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header(detalhe['nome_cadeira'])
            st.caption(f"ID: {detalhe['id_cadeira']} | Curso: {detalhe['nome_curso']} ({detalhe['sigla_curso_ref']})")
            
            st.subheader("📖 Programa")
            st.info(detalhe['programa'] if pd.notna(detalhe['programa']) else "Programa não disponível.")
            
            st.subheader("📝 Método de Avaliação")
            st.warning(detalhe['metodo_avaliacao'] if pd.notna(detalhe['metodo_avaliacao']) else "Detalhes de avaliação não especificados.")

        with col2:
            st.metric("Créditos ECTS", detalhe['ects'])
            st.metric("Período", detalhe['periodo'])
            st.metric("Alunos Inscritos", detalhe['num_alunos'])
            
            st.subheader("👨‍🏫 Corpo Docente")
            # Converter a string de professores (separada por |) numa lista
            profs = detalhe['docentes'].split(" | ") if pd.notna(detalhe['docentes']) else []
            for p in profs:
                st.write(f"- {p}")
            
            st.markdown(f"[🔗 Abrir no Fénix]({detalhe['url_curso']})")

    # Tabela Geral (opcional, para visão rápida)
    with st.expander("Ver Tabela Completa"):
        st.dataframe(df_filtered[['sigla_curso_ref', 'nome_cadeira', 'ects', 'periodo', 'num_alunos']], use_container_width=True)

else:
    st.warning("Aguardando carregamento de dados...")
