import streamlit as st
import pandas as pd
import requests
import os
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURAÇÕES TÉCNICAS ---
BASE_URL = "https://fenix.tecnico.ulisboa.pt/api/fenix/v1"
ANO = "2024/2025"
CSV_FILE = "todos_mestrados_ist_p3.csv"

st.set_page_config(page_title="IST Explorer - Automação", layout="wide")

# --- FUNÇÕES DE EXTRAÇÃO (BACKEND) ---
def get_json(endpoint, params=None):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def processar_curso(curso):
    sigla = curso.get('acronym', 'N/A')
    c_id = curso.get('id')
    nome_curso = curso.get('name', 'N/A')
    res_list = []
    
    cadeiras = get_json(f"degrees/{c_id}/courses", {"academicTerm": ANO})
    if cadeiras:
        for cad in cadeiras:
            term = cad.get('academicTerm', 'N/A')
            if "2º Semestre" in term or "2º semestre" in term:
                nome_cad = cad.get('name', 'N/A').replace("'", "").replace(",", ";")
                linha = f"'{nome_curso}','{sigla}','{cad.get('id')}','{nome_cad}','{cad.get('credits','0')}','{term}'"
                res_list.append(linha)
    return res_list
def gerar_base_dados():
    dados = get_json("degrees", {"academicTerm": ANO})
    if not dados:
        return False

    mestrados = [
        d for d in dados 
        if ("Master" in str(d.get('typeName', '')) or "Mestrado" in str(d.get('name', '')))
        and "Alameda" in str(d.get('campus', ''))
    ]

    total = len(mestrados)
    barra_progresso = st.progress(0)
    texto_progresso = st.empty()

    with open(CSV_FILE, "w", encoding="utf-8-sig") as f:
        f.write("'nome_curso','sigla','id_cadeira','nome_cadeira','ects','periodo'\n")
        
        # Reduzimos para 5 workers para evitar bloqueios da API do IST
        with ThreadPoolExecutor(max_workers=5) as executor:
            for i, lista in enumerate(executor.map(processar_curso, mestrados)):
                # Atualização visual para não parecer que crashou
                percentagem = (i + 1) / total
                barra_progresso.progress(percentagem)
                texto_progresso.write(f"⚙️ Processando {i+1}/{total}: {mestrados[i].get('acronym')}")
                
                if lista:
                    for linha in lista:
                        f.write(linha + "\n")
                    f.flush()
    
    # Limpa os indicadores de progresso após concluir
    barra_progresso.empty()
    texto_progresso.empty()
    return True

# --- INTERFACE (FRONTEND) ---
st.title("🔍 Explorador de Unidades Curriculares IST")

@st.cache_data(show_spinner=False)
def load_data():
    # Se o ficheiro não existe, despoleta a geração
    if not os.path.exists(CSV_FILE):
        return None
    return pd.read_csv(CSV_FILE, quotechar="'", encoding="utf-8-sig")

# Lógica de Inicialização
data = load_data()

if data is None:
    # Ecrã de "A Gerar Ficheiros"
    with st.status("🛠️ Base de dados não detetada. A aceder à API do FénixEdu...", expanded=True) as status:
        st.write("A identificar cursos de Mestrado na Alameda...")
        sucesso = gerar_base_dados()
        if sucesso:
            status.update(label="✅ Extração concluída com sucesso!", state="complete", expanded=False)
            st.rerun() # Reinicia a app para ler o novo ficheiro
        else:
            st.error("Falha ao ligar à API do IST. Verifique a ligação.")
            st.stop()

# --- INTERFACE DE PESQUISA (SÓ APARECE SE HOUVER DADOS) ---
st.sidebar.header("Filtros")
search = st.text_input("Procurar cadeira ou curso (ex: Energia, AVAC, Ambiente):", "").strip()

# Filtros e Tabela
filtered_df = data.copy()
if search:
    mask = (data['nome_cadeira'].str.contains(search, case=False, na=False) | 
            data['nome_curso'].str.contains(search, case=False, na=False))
    filtered_df = filtered_df[mask]

st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# Botão para forçar atualização se necessário
if st.sidebar.button("Forçar Atualização de Dados"):
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
    st.cache_data.clear()
    st.rerun()
