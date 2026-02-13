import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Explorador de Cursos IST", layout="wide")

st.title("🔍 Procura de Unidades Curriculares - IST")
st.subheader("Filtro rápido para Engenharia e Gestão")

# 1. Carregar os dados (usando cache para ser instantâneo)
@st.cache_data
def load_data():
    # O encoding utf-8-sig garante que os acentos aparecem bem
    df = pd.read_csv("todos_mestrados_ist_p3.csv", quotechar="'")
    return df

try:
    df = load_data()

    # 2. Barra Lateral para Filtros Estruturados
    st.sidebar.header("Filtros Avançados")
    
    # Filtro por Curso (Sigla)
    cursos = st.sidebar.multiselect("Filtrar por Curso:", options=sorted(df['sigla'].unique()))
    
    # Filtro por ECTS
    ects_range = st.sidebar.slider("Créditos (ECTS):", 
                                   float(df['ects'].min()), 
                                   float(df['ects'].max()), 
                                   (0.0, float(df['ects'].max())))

    # 3. Pesquisa Global (O que pediu)
    search_query = st.text_input("Pesquisa rápida (digite o nome da cadeira, sigla ou termo técnico):", "")

    # Lógica de Filtragem
    filtered_df = df.copy()
    
    if search_query:
        # Pesquisa em múltiplas colunas simultaneamente
        mask = (
            df['nome_cadeira'].str.contains(search_query, case=False, na=False) |
            df['nome_curso'].str.contains(search_query, case=False, na=False) |
            df['sigla'].str.contains(search_query, case=False, na=False)
        )
        filtered_df = filtered_df[mask]

    if cursos:
        filtered_df = filtered_df[filtered_df['sigla'].isin(cursos)]

    filtered_df = filtered_df[(filtered_df['ects'] >= ects_range[0]) & (filtered_df['ects'] <= ects_range[1])]

    # 4. Exibição dos Resultados
    st.write(f"Foram encontradas **{len(filtered_df)}** cadeiras.")
    
    # Usar o dataframe interativo do Streamlit
    st.dataframe(
        filtered_df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "id_cadeira": st.column_config.TextColumn("ID"),
            "ects": st.column_config.NumberColumn("ECTS", format="%.1f")
        }
    )

except FileNotFoundError:
    st.error("Ficheiro CSV não encontrado. Execute o script de extração primeiro.")