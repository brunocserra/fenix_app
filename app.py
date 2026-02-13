import streamlit as st
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURAÇÕES ---
BASE_URL = "https://fenix.tecnico.ulisboa.pt/api/fenix/v1"
ANO = "2024/2025"

st.set_page_config(page_title="IST API Live Explorer", layout="wide")

# --- MOTOR DE CONSULTA (API) ---
def get_json(endpoint, params=None):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def fetch_cadeiras_curso(curso):
    """Consulta as cadeiras de um curso específico"""
    c_id = curso.get('id')
    nome_curso = curso.get('name')
    sigla = curso.get('acronym')
    
    dados_cadeiras = get_json(f"degrees/{c_id}/courses", {"academicTerm": ANO})
    resultado = []
    
    if dados_cadeiras:
        for cad in dados_cadeiras:
            term = cad.get('academicTerm', '')
            # Filtramos apenas o 2º Semestre (P3/P4) conforme o seu interesse
            if "2º Semestre" in term or "2º semestre" in term:
                resultado.append({
                    "Mestrado": nome_curso,
                    "Sigla": sigla,
                    "Cadeira": cad.get('name'),
                    "ECTS": cad.get('credits', 0),
                    "ID": cad.get('id'),
                    "Período": term
                })
    return resultado

@st.cache_data(ttl=3600) # Guarda os dados na RAM por 1 hora
def carregar_dados_da_api():
    """Faz o scraping completo da API em tempo real"""
    all_data = []
    
    # 1. Obter lista de todos os cursos
    todos_cursos = get_json("degrees", {"academicTerm": ANO})
    if not todos_cursos:
        return None

    # 2. Filtrar apenas Mestrados na Alameda
    mestrados = [
        d for d in todos_cursos 
        if ("Master" in str(d.get('typeName', '')) or "Mestrado" in str(d.get('name', '')))
        and "Alameda" in str(d.get('campus', ''))
    ]

    # 3. Consultar cadeiras em paralelo (Multithreading) para ser rápido
    with ThreadPoolExecutor(max_workers=10) as executor:
        listas_por_curso = list(executor.map(fetch_cadeiras_curso, mestrados))
        for lista in listas_por_curso:
            all_data.extend(lista)
            
    return pd.DataFrame(all_data)

# --- INTERFACE ---
st.title("🌐 IST Live API Explorer")
st.markdown(f"Dados obtidos em tempo real via **FenixEdu API** para {ANO}")

# Botão para limpar cache e forçar nova leitura da API
if st.sidebar.button("🔄 Atualizar Dados (API Live)"):
    st.cache_data.clear()
    st.rerun()

with st.spinner("A consultar API do Técnico..."):
    df = carregar_dados_da_api()

if df is not None and not df.empty:
    # Filtros Rápidos
    search = st.text_input("Pesquisa rápida por termo técnico (ex: Energia, AVAC, Digital):", "")
    
    # Lógica de Pesquisa
    if search:
        df = df[df['Cadeira'].str.contains(search, case=False, na=False) | 
                df['Mestrado'].str.contains(search, case=False, na=False)]

    # Exibição
    st.metric("Total de Unidades Curriculares", len(df))
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.error("Não foi possível obter dados da API neste momento.")
