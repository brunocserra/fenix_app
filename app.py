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
        df = pd.read_csv("planeamento_ist_detalhado_2026.csv", encoding="utf-8-sig")
        df['id_cadeira'] = df['id_cadeira'].astype(str)
        # Garantir que num_alunos é tratado como numérico
        df['num_alunos'] = pd.to_numeric(df['num_alunos'], errors='coerce').fillna(0).astype(int)
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
    search_query = st.sidebar.text_input("Procurar por Nome, Sigla ou ID:", "").lower()
    
    periodos = ["Todos"] + sorted(df['periodo'].dropna().unique().tolist())
    periodo_sel = st.sidebar.selectbox("Filtrar por Período:", periodos)

    # --- LÓGICA DE FILTRAGEM ---
    mask = (
        df['sigla_curso_ref'].str.lower().str.contains(search_query, na=False) | 
        df['nome_cadeira'].str.lower().str.contains(search_query, na=False) |
        df['id_cadeira'].str.contains(search_query, na=False)
    )
    
    if periodo_sel != "Todos":
        mask = mask & (df['periodo'] == periodo_sel)
    
    df_filtered = df[mask].copy()

    # --- EXIBIÇÃO EM TABELA ---
    if not df_filtered.empty:
        st.write(f"### Lista de Disciplinas ({len(df_filtered)})")
        st.caption("Clica numa linha da tabela para ver os detalhes completos abaixo.")

        # Selecionar colunas para a vista de tabela (tipo Excel)
        cols_to_show = ['sigla_curso_ref', 'id_cadeira', 'nome_cadeira', 'ects', 'periodo', 'num_alunos']
        
        # Interface de seleção na tabela
        event = st.dataframe(
            df_filtered[cols_to_show],
            use_container_width=True,
            hide_index=True,
            selection_mode="single_row",
            on_select="rerun"
        )

        # Verificação de seleção
        selected_rows = event.selection.rows
        
        if selected_rows:
            # Obter os dados da linha selecionada
            idx = selected_rows[0]
            row = df_filtered.iloc[idx]
            
            st.divider()
            
            # --- DETALHES (EXIBIÇÃO ESTRUTURADA) ---
            st.markdown(f"## Detalhes: {row['nome_cadeira']}")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📖 Programa Detalhado")
                st.write(row['programa'] if pd.notna(row['programa']) else "Informação não disponível.")
                
                st.subheader("📝 Método de Avaliação")
                st.info(row['metodo_avaliacao'] if pd.notna(row['metodo_avaliacao']) else "Detalhes não especificados.")
            
            with col2:
                # Métricas em destaque
                st.metric("Alunos Inscritos", f"{row['num_alunos']}")
                st.metric("Créditos ECTS", f"{row['ects']} ECTS")
                st.metric("Período Letivo", row['periodo'])
                
                st.markdown("**👨‍🏫 Corpo Docente:**")
                docentes = str(row['docentes']).split(" | ") if pd.notna(row['docentes']) else ["Não listados"]
                for d in docentes:
                    st.write(f"- {d}")
                
                st.divider()
                st.link_button("🌐 Página Oficial Fénix", row['url_curso'], use_container_width=True)
        else:
            st.info("💡 Seleciona uma linha na tabela acima para expandir os detalhes técnicos.")
                
    else:
        st.warning("Nenhuma disciplina encontrada com os filtros aplicados.")

else:
    st.error("Erro crítico: Base de dados CSV não encontrada ou vazia.")

st.markdown("---")
st.caption("Fénix Data Explorer | 2026")
