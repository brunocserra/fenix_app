import streamlit as st
import pandas as pd
import requests
import os
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURAÇÕES TÉCNICAS ---
BASE_URL = "https://fenix.tecnico.ulisboa.pt/api/fenix/v1"
ANO = "2024/2025"
CSV_FILE = "dados_ist_automacao.csv"  # Ficheiro gerado na raiz

st.set_page_config(page_title="IST Explorer | Automação", layout="wide")

# --- MOTOR DE EXTRAÇÃO (API -> CSV) ---
def get_json(endpoint, params=None):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=20)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def processar_curso(curso):
    c_id = curso.get('id')
    sigla = curso.get('acronym', 'N/A')
    nome_curso = curso.get('name', 'N/A')
    res_list = []
    
    cadeiras = get_json(f"degrees/{c_id}/courses", {"academicTerm": ANO})
    if cadeiras:
        for cad in cadeiras:
            term = cad.get('academicTerm', 'N/A')
            if "2º Semestre" in term or "2º semestre" in term:
                # Sanitização para CSV: remover vírgulas e aspas
                nome_cad = str(cad.get('name', 'N/A')).replace("'", "").replace(",", ";")
                linha = f"'{nome_curso}','{sigla}','{cad.get('id')}','{nome_cad}','{cad.get('credits','0')}','{term}'"
                res_list.append(linha)
    return res_list

def gerar_base_dados():
    """Varre a API e cria o ficheiro CSV na raiz do servidor"""
    dados = get_json("degrees", {"academicTerm": ANO})
    if not dados:
        return False

    # Filtro de Mestrados Alameda
    mestrados = [
        d for d in dados 
        if ("Master" in str(d.get('typeName', '')) or "Mestrado" in str(d.get('name', '')))
        and "Alameda" in str(d.get('campus', ''))
    ]

    total = len(mestrados)
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        with open(CSV_FILE, "w", encoding="utf-8-sig") as f:
            f.write("'nome_curso','sigla','id_cadeira','nome_cadeira','ects','periodo'\n")
            
            # 5 workers para estabilidade na Cloud
            with ThreadPoolExecutor(max_workers=5) as executor:
                for i, lista in enumerate(executor.map(processar_curso, mestrados)):
                    status_text.write(f"⚙️ A extrair {i+1}/{total}: {mestrados[i].get('acronym')}")
                    progress_bar.progress((i + 1) / total)
                    if lista:
                        for linha in lista:
                            f.write(linha + "\n")
                        f.flush()
        return True
    except Exception as e:
        st.error(f"Erro ao escrever ficheiro: {e}")
        return False

# --- LOGICA DE CARREGAMENTO ---
@st.cache_data(show_spinner=False)
def get_data():
    # Se o ficheiro não existe, retorna None para despoletar a criação
    if not os.path.exists(CSV_FILE):
        return None
    return pd.read_csv(CSV_FILE, quotechar="'", encoding="utf-8-sig")

# --- INTERFACE ---
st.title("🔍 IST Explorer Automático")

df = get_data()

if df is None:
    # Este bloco só corre se o ficheiro não existir
    with st.status("🚀 Base de dados local não encontrada. A iniciar extração...", expanded=True) as status:
        if gerar_base_dados():
            status.update(label="✅ Extração concluída!", state="complete")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("Não foi possível gerar os dados. Verifique os logs.")
            st.stop()

# --- DASHBOARD (SÓ APARECE COM DADOS) ---
st.sidebar.header("Gestão de Dados")
if st.sidebar.button("🔄 Forçar Nova Extração"):
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
    st.cache_data.clear()
    st.rerun()

# Pesquisa e Tabela
search = st.text_input("Pesquisar (ex: AVAC, Energia, Gestão):", "").strip()

filtered_df = df.copy()
if search:
    mask = (df['nome_cadeira'].str.contains(search, case=False, na=False) | 
            df['nome_curso'].str.contains(search, case=False, na=False))
    filtered_df = filtered_df[mask]

st.metric("Cadeiras Disponíveis", len(filtered_df))
st.dataframe(filtered_df, use_container_width=True, hide_index=True)
