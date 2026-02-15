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
        # Garantir integridade da coluna num_alunos
        df['num_alunos'] = pd.to_numeric(df['num_alunos'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o ficheiro CSV: {e}")
        return pd.DataFrame()

df = load_data()

# --- INTERFACE ---
st.title("🎓 IST Academic Planner 2026")
st.subheader("Dashboard de Unidades Curriculares - 2º Semestre")

if not df.empty:
    # --- FILTROS (SIDEBAR) ---
    st.sidebar.header("🔍 Filtros de Engenharia")
    search_query = st.sidebar.text_input("Procurar (Cadeira, Sigla ou ID):", "").lower()
    
    periodos = ["Todos"] + sorted(df['periodo'].dropna().unique().tolist())
    periodo_sel = st.sidebar.selectbox("Filtrar Período:", periodos)

    # --- LÓGICA DE FILTRAGEM ---
    mask = (
        df['sigla_curso_ref'].str.lower().str.contains(search_query, na=False) | 
        df['nome_cadeira'].str.lower().str.contains(search_query, na=False) |
        df['id_cadeira'].str.contains(search_query, na=False)
    )
    if periodo_sel != "Todos":
        mask = mask & (df['periodo'] == periodo_sel)
    
    df_filtered = df[mask].copy()

    # --- EXIBIÇÃO ---
    if not df_filtered.empty:
        # 1. VISÃO TABULAR (ESTILO EXCEL)
        st.write(f"### Resultados da Pesquisa ({len(df_filtered)})")
        # Reintroduzindo num_alunos na visualização principal
        cols_view = ['sigla_curso_ref', 'id_cadeira', 'nome_cadeira', 'ects', 'periodo', 'num_alunos']
        st.dataframe(df_filtered[cols_view], use_container_width=True, hide_index=True)

        # 2. SELEÇÃO PARA DETALHES (SUBSTITUI O CLIQUE NA TABELA PARA EVITAR ERROS)
        st.divider()
        df_filtered['label'] = "[" + df_filtered['sigla_curso_ref'] + "] " + df_filtered['nome_cadeira']
        
        col_sel, _ = st.columns([1, 1])
        with col_sel:
            escolha = st.selectbox(
                "🎯 Selecione a cadeira para abrir o Dossiê Técnico:",
                ["-- Escolha uma opção --"] + sorted(df_filtered['label'].tolist())
            )

        # 3. DETALHES COM SEPARADOR LATERAL (COLUNAS)
        if escolha != "-- Escolha uma opção --":
            row = df_filtered[df_filtered['label'] == escolha].iloc[0]
            
            st.markdown(f"## {row['nome_cadeira']}")
            
            # Layout: Esquerda (Conteúdo pesado) | Direita (Métricas e Docentes)
            col_main, col_side = st.columns([2, 1])
            
            with col_main:
                with st.expander("📖 Programa e Conteúdos Curriculares", expanded=True):
                    st.write(row['programa'] if pd.notna(row['programa']) else "N/A")
                
                with st.expander("📝 Critérios de Avaliação", expanded=True):
                    st.info(row['metodo_avaliacao'] if pd.notna(row['metodo_avaliacao']) else "N/A")
            
            with col_side:
                st.subheader("📊 Ficha Técnica")
                # Exibição de num_alunos conforme pedido
                st.metric("Inscritos", f"{row['num_alunos']} alunos")
                st.metric("Créditos", f"{row['ects']} ECTS")
                st.metric("Período", row['periodo'])
                
                st.markdown("**👨‍🏫 Corpo Docente:**")
                docentes = str(row['docentes']).split(" | ") if pd.notna(row['docentes']) else ["N/A"]
                for d in docentes:
                    st.write(f"- {d}")
                
                st.divider()
                st.link_button("🌐 Página Oficial Fénix", row['url_curso'], use_container_width=True)
    else:
        st.warning("Nenhuma correspondência encontrada.")
else:
    st.error("Erro: O ficheiro CSV está vazio ou não foi carregado.")

st.markdown("---")
st.caption("IST Planner v2.1 | Engenharia Aeroespacial | Açores")
