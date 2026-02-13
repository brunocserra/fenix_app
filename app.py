import streamlit as st
import pandas as pd
import requests
import os
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://fenix.tecnico.ulisboa.pt/api/fenix/v1"
ANO = "2024/2025"
CSV_FILE = "dados_ist_automacao.csv"

st.set_page_config(page_title="IST Explorer | Diagnóstico", layout="wide")

def get_json(endpoint, params=None):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=20)
        return r.json() if r.status_code == 200 else None
    except: return None

def processar_curso(curso):
    c_id = curso.get('id')
    sigla = curso.get('acronym', 'N/A')
    nome_curso = curso.get('name', 'N/A')
    res_list = []
    
    cadeiras = get_json(f"degrees/{c_id}/courses", {"academicTerm": ANO})
    if cadeiras:
        for cad in cadeiras:
            term = str(cad.get('academicTerm', 'N/A'))
            # FILTRO RELAXADO: Se tiver '2' e 'Sem', nós aceitamos
            if "2" in term and ("Sem" in term or "sem" in term):
                nome_cad = str(cad.get('name', 'N/A')).replace("'", "").replace(",", ";")
                linha = f"'{nome_curso}','{sigla}','{cad.get('id')}','{nome_cad}','{cad.get('credits','0')}','{term}'"
                res_list.append(linha)
    return res_list

def gerar_base_dados():
    dados = get_json("degrees", {"academicTerm": ANO})
    if not dados: return False

    mestrados = [d for d in dados if ("Master" in str(d.get('typeName', '')) or "Mestrado" in str(d.get('name', ''))) and "Alameda" in str(d.get('campus', ''))]
    
    total = len(mestrados)
    progress_bar = st.progress(0)
    
    with open(CSV_FILE, "w", encoding="utf-8-sig") as f:
        f.write("'nome_curso','sigla','id_cadeira','nome_cadeira','ects','periodo'\n")
        with ThreadPoolExecutor(max_workers=5) as executor:
            for i, lista in enumerate(executor.map(processar_curso, mestrados)):
                progress_bar.progress((i + 1) / total)
                if lista:
                    for linha in lista:
                        f.write(linha + "\n")
                    f.flush()
    return True

@st.cache_data(show_spinner=False)
def load_data():
    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) < 80: # Se ficheiro é só o cabeçalho
        return None
    return pd.read_csv(CSV_FILE, quotechar="'", encoding="utf-8-sig")

st.title("🔍 IST Explorer - Diagnóstico de Dados")

df = load_data()

if df is None:
    with st.status("🚀 Gerando dados pela primeira vez...", expanded=True):
        if gerar_base_dados():
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("Falha ao contactar a API.")
            st.stop()

# --- INTERFACE DE PESQUISA ---
st.sidebar.button("🔄 Forçar Nova Extração", on_click=lambda: [os.remove(CSV_FILE) if os.path.exists(CSV_FILE) else None, st.cache_data.clear()])

search = st.text_input("Filtrar por nome (ex: Energia):", "").strip()

# Se o DF estiver vazio, vamos tentar ler sem filtros para ver o que lá está
if df is not None and len(df) == 0:
    st.warning("⚠️ O ficheiro foi gerado mas não contém cadeiras do 2º semestre. A tentar extração total...")
    # Se chegámos aqui, o filtro de semestre falhou. Vamos apagar e tentar de novo sem filtro de semestre.
    if st.button("Remover filtro de semestre e tentar de novo"):
        os.remove(CSV_FILE)
        st.rerun()

if df is not None:
    filtered_df = df.copy()
    if search:
        filtered_df = df[df['nome_cadeira'].str.contains(search, case=False, na=False)]
    
    st.metric("Cadeiras Encontradas", len(filtered_df))
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
