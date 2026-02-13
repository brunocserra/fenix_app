import streamlit as st
import pandas as pd
import requests
import os

# --- PARÂMETROS TÉCNICOS ---
BASE_URL = "https://fenix.tecnico.ulisboa.pt/api/fenix/v1"
ANO = "2024/2025"
CSV_FILE = "dados_live.csv"

st.set_page_config(page_title="IST Real-Time Generator", layout="wide")

def get_json(endpoint):
    try:
        # Timeout longo para evitar o "Loading" infinito
        r = requests.get(f"{BASE_URL}/{endpoint}", params={"academicTerm": ANO}, timeout=30)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def gerar_dados_na_hora():
    container = st.container()
    dados_final = []
    
    # 1. Obter cursos
    cursos = get_json("degrees")
    if not cursos:
        st.error("A API do IST não respondeu ao pedido inicial.")
        return None

    mestrados = [d for d in cursos if "Mestrado" in d.get('name', '') and "Alameda" in d.get('campus', '')]
    total = len(mestrados)
    
    progresso = st.progress(0)
    status_msg = st.empty()

    # 2. Extração Sequencial (Mais lenta, mas não bloqueia)
    for i, m in enumerate(mestrados):
        sigla = m.get('acronym')
        status_msg.write(f"📥 A ler curso {i+1}/{total}: **{sigla}**")
        
        cadeiras = get_json(f"degrees/{m.get('id')}/courses")
        if cadeiras:
            for c in cadeiras:
                term = str(c.get('academicTerm', ''))
                if "2º Semestre" in term or "2.º Semestre" in term:
                    dados_final.append({
                        "Mestrado": m.get('name'),
                        "Sigla": sigla,
                        "Cadeira": c.get('name'),
                        "ECTS": c.get('credits', 0),
                        "Periodo": term
                    })
        progresso.progress((i + 1) / total)
    
    status_msg.success("Extração finalizada!")
    return pd.DataFrame(dados_final)

# --- INTERFACE ---
st.title("🚀 Gerador de Dados IST em Tempo Real")

if "meu_df" not in st.session_state:
    st.session_state.meu_df = None

if st.button("Gerar/Atualizar Dados Agora"):
    st.session_state.meu_df = gerar_dados_na_hora()

if st.session_state.meu_df is not None:
    df = st.session_state.meu_df
    st.metric("Cadeiras encontradas", len(df))
    
    busca = st.text_input("Filtrar por nome:")
    if busca:
        df = df[df['Cadeira'].str.contains(busca, case=False, na=False)]
    
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Clique no botão acima para iniciar a comunicação direta com o Fénix.")
