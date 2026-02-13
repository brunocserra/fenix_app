import streamlit as st
import pandas as pd
import os

# Configuração de Engenharia da Página
st.set_page_config(page_title="IST Explorer - Engenharia & Energia", layout="wide")

CSV_FILE = "todos_mestrados_ist_p3.csv"

st.title("🔍 Explorador de Unidades Curriculares IST")
st.markdown(f"**Ano Letivo:** 2024/2025 | **Foco:** 2º Semestre / P3")

@st.cache_data
def load_data():
    if os.path.exists(CSV_FILE):
        # quotechar="'" para lidar com as pelicas que definimos
        return pd.read_csv(CSV_FILE, quotechar="'", encoding="utf-8-sig")
    return None

df = load_data()

if df is not None:
    # Barra Lateral de Filtros
    st.sidebar.header("Parâmetros de Pesquisa")
    
    # Filtro por Curso
    lista_cursos = sorted(df['nome_curso'].unique())
    curso_selecionado = st.sidebar.multiselect("Filtrar por Mestrado:", options=lista_cursos)
    
    # Filtro por ECTS
    ects_max = float(df['ects'].max())
    ects_range = st.sidebar.slider("Intervalo de Créditos (ECTS):", 0.0, ects_max, (0.0, ects_max))

    # Pesquisa de Texto (Input Principal)
    search = st.text_input("Pesquisa rápida (ex: Climatização, Energia, Programação):", "").strip()

    # Lógica de Filtro Dinâmico
    filtered_df = df.copy()

    if search:
        mask = (
            df['nome_cadeira'].str.contains(search, case=False, na=False) |
            df['sigla'].str.contains(search, case=False, na=False)
        )
        filtered_df = filtered_df[mask]

    if curso_selecionado:
        filtered_df = filtered_df[filtered_df['nome_curso'].isin(curso_selecionado)]

    filtered_df = filtered_df[(filtered_df['ects'] >= ects_range[0]) & (filtered_df['ects'] <= ects_range[1])]

    # Exibição de Resultados
    st.metric("Cadeiras encontradas", len(filtered_df))
    
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id_cadeira": st.column_config.TextColumn("ID Fénix"),
            "ects": st.column_config.NumberColumn("ECTS", format="%.1f"),
            "periodo": st.column_config.TextColumn("Semestre/Período")
        }
    )
else:
    st.error("⚠️ Erro: Ficheiro de dados não encontrado no repositório.")
    st.info("Certifique-se de que fez 'git add' e 'push' do ficheiro 'todos_mestrados_ist_p3.csv'.")
