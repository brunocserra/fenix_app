import streamlit as st
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="IST Planner 2026",
    layout="wide",
    page_icon="🚀"
)

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def load_data():
    try:
        # Carregamento do ficheiro CSV
        df = pd.read_csv("planeamento_ist_detalhado_2026.csv", encoding="utf-8-sig")
        # Tratamento de tipos de dados para evitar formatação indesejada
        df['id_cadeira'] = df['id_cadeira'].astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o ficheiro CSV: {e}")
        return pd.DataFrame()

df = load_data()

# --- INTERFACE ---
st.title("🎓 IST Academic Planner 2026")
st.subheader("Gestão Técnica de Unidades Curriculares - 2º Semestre")

if not df.empty:
    # --- FILTROS (SIDEBAR) ---
    st.sidebar.header("Filtros de Pesquisa")
    
    # Pesquisa por texto
    search_query = st.sidebar.text_input("Procurar por Nome, Sigla ou ID:", "").lower()
    
    # Filtro por Período
    periodos = ["Todos"] + sorted(df['periodo'].dropna().unique().tolist())
    periodo_sel = st.sidebar.selectbox("Filtrar por Período:", periodos)

    # --- LÓGICA DE FILTRAGEM ---
    # Aplica as preferências de pesquisa
    mask = (
        df['sigla_curso_ref'].str.lower().str.contains(search_query, na=False) | 
        df['nome_cadeira'].str.lower().str.contains(search_query, na=False) |
        df['id_cadeira'].str.contains(search_query, na=False)
    )
    
    if periodo_sel != "Todos":
        mask = mask & (df['periodo'] == periodo_sel)
    
    df_filtered = df[mask]

    # --- EXIBIÇÃO ---
    if not df_filtered.empty:
        # Formatação do seletor utilizando os nomes técnicos (pelicas)
        df_filtered['display_name'] = "[" + df_filtered['sigla_curso_ref'] + "] " + df_filtered['nome_cadeira']
        
        selected_label = st.selectbox(
            f"Disciplinas encontradas ({len(df_filtered)}):", 
            ["-- Selecione uma opção --"] + sorted(df_filtered['display_name'].tolist())
        )
        
        if selected_label != "-- Selecione uma opção --":
            # Obter dados da linha selecionada
            row = df_filtered[df_filtered['display_name'] == selected_label].iloc[0]
            
            st.divider()
            
            # Layout em colunas para análise de engenharia
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.header(row['nome_cadeira'])
                st.write(f"**Identificador (`id_cadeira`):** `{row['id_cadeira']}`")
                
                st.subheader("📖 Programa Detalhado")
                st.write(row['programa'] if pd.notna(row['programa']) else "Informação não disponível.")
                
                st.subheader("📝 Método de Avaliação")
                st.info(row['metodo_avaliacao'] if pd.notna(row['metodo_avaliacao']) else "Detalhes não especificados.")
            
            with col2:
                # Métricas de desempenho/carga
                st.metric("Créditos ECTS", f"{row['ects']} ECTS")
                st.metric("Período Letivo", row['periodo'])
                
                st.write("**👨‍🏫 Corpo Docente:**")
                # Split de docentes se estiverem separados por pipe no CSV
                docentes = str(row['docentes']).split(" | ") if pd.notna(row['docentes']) else ["Não listados"]
                for d in docentes:
                    st.write(f"- {d}")
                
                st.divider()
                st.link_button("🌐 Página Oficial Fénix", row['url_curso'], use_container_width=True)
                
    else:
        st.warning("Nenhuma disciplina encontrada com os filtros aplicados.")

else:
    st.error("Erro crítico: Base de dados CSV não encontrada ou vazia.")

# --- RODAPÉ ---
st.markdown("---")
st.caption("Fénix Data Explorer | 2026")
