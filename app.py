import streamlit as st
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IST Planner 2026", layout="wide")

@st.cache_data
def load_data():
    try:
        # Carregamos o CSV que geraste
        df = pd.read_csv("planeamento_ist_detalhado_2026.csv", encoding="utf-8-sig")
        
        # Engenharia de dados: garantir que IDs e ECTS são strings ou floats limpos
        df['id_cadeira'] = df['id_cadeira'].astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar ficheiro: {e}")
        return pd.DataFrame()

# --- INTERFACE PRINCIPAL ---
st.title("🚀 IST Course Explorer & Planner 2026")

df = load_data()

if not df.empty:
    # --- FILTROS NA SIDEBAR ---
    st.sidebar.header("🔍 Filtros de Procura")
    
    # Termo de pesquisa (Sigla, Nome da Cadeira ou ID)
    search_term = st.sidebar.text_input("Procurar (Sigla, Cadeira ou ID)", "").lower()
    
    # Filtro por Período (P3, P4, Semestral)
    periodos = ["Todos"] + sorted(df['periodo'].dropna().unique().tolist())
    periodo_sel = st.sidebar.selectbox("Filtrar por Período", periodos)

    # --- LÓGICA DE FILTRAGEM ---
    # Usamos .str.contains com na=False para evitar erros com valores nulos
    mask = (
        df['sigla_curso_ref'].str.lower().str.contains(search_term, na=False) | 
        df['nome_cadeira'].str.lower().str.contains(search_term, na=False) |
        df['id_cadeira'].str.contains(search_term, na=False)
    )
    
    if periodo_sel != "Todos":
        mask = mask & (df['periodo'] == periodo_sel)
    
    df_filtered = df[mask]

    # --- LISTAGEM ---
    st.subheader(f"Resultados ({len(df_filtered)} entradas)")
    
    # Criar uma label amigável para o dropdown
    # Formato: [SIGLA] Nome da Cadeira
    df_filtered['selector_label'] = "[" + df_filtered['sigla_curso_ref'] + "] " + df_filtered['nome_cadeira']
    
    lista_opcoes = ["-- Selecione uma disciplina --"] + sorted(df_filtered['selector_label'].tolist())
    escolha = st.selectbox("Detalhes da Unidade Curricular:", lista_opcoes)

    if escolha != "-- Selecione uma disciplina --":
        # Extraímos a linha correspondente
        detalhe = df_filtered[df_filtered['selector_label'] == escolha].iloc[0]
        
        st.divider()
        
        # Layout de Engenharia: Detalhes à esquerda, Métricas à direita
        col_main, col_stats = st.columns([2, 1])
        
        with col_main:
            st.header(detalhe['nome_cadeira'])
            st.caption(f"ID Fénix: {detalhe['id_cadeira']} | Sigla Curso: {detalhe['sigla_curso_ref']}")
            
            with st.expander("📖 Programa Detalhado", expanded=True):
                prog = detalhe['programa']
                st.write(prog if pd.notna(prog) and str(prog).strip() != "" else "Sem programa disponível.")
            
            with st.expander("📝 Método de Avaliação", expanded=True):
                aval = detalhe['metodo_avaliacao']
                st.write(aval if pd.notna(aval) and str(aval).strip() != "" else "Método não especificado.")

        with col_stats:
            st.metric("Créditos ECTS", detalhe['ects'])
            st.metric("Período Letivo", detalhe['periodo'])
            st.metric("Alunos Estimados", detalhe['num_alunos'])
            
            st.subheader("👨‍🏫 Docentes")
            docentes = str(detalhe['docentes']).split(" | ") if pd.notna(detalhe['docentes']) else ["Não listados"]
            for d in docentes:
                st.write(f"• {d}")
            
            st.divider()
            st.link_button("🌐 Abrir no Fénix", detalhe['url_curso'])

    # Vista de Tabela para análise de dados rápida
    with st.expander("📊 Vista de Tabela Global"):
        st.dataframe(df_filtered[['sigla_curso_ref', 'nome_cadeira', 'ects', 'periodo', 'num_alunos']], use_container_width=True)

else:
    st.info("💡 Carrega o ficheiro CSV na pasta do projeto para visualizar os dados.")
