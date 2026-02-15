import streamlit as st
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IST Gallery Pro", layout="wide", page_icon="🚀")

# --- CACHE DE DADOS (CRÍTICO) ---
@st.cache_data
def load_and_prep():
    try:
        df = pd.read_csv("planeamento_ist_detalhado_2026.csv", encoding="utf-8-sig")
        df['id_cadeira'] = df['id_cadeira'].astype(str)
        df['num_alunos'] = pd.to_numeric(df['num_alunos'], errors='coerce').fillna(0).astype(int)
        # Criar uma coluna de pesquisa combinada para acelerar o filtro
        df['search_index'] = (df['nome_cadeira'] + " " + df['sigla_curso_ref']).str.lower()
        return df
    except:
        return pd.DataFrame()

df = load_and_prep()

# --- INTERFACE ---
st.title("🎓 IST Gallery - High Performance")

# Sidebar - Filtros rápidos
st.sidebar.header("🔍 Filtros")
search = st.sidebar.text_input("Pesquisar:", "").lower()
periodo_sel = st.sidebar.selectbox("Período:", ["Todos"] + sorted(df['periodo'].unique().tolist()))

# Filtragem ultra-rápida via vetorização
df_filtered = df[df['search_index'].str.contains(search, na=False)]
if periodo_sel != "Todos":
    df_filtered = df_filtered[df_filtered['periodo'] == periodo_sel]

# --- LAYOUT MASTER-DETAIL ---
col_list, col_details = st.columns([1.2, 1.8])

with col_list:
    # Paginação manual para evitar o "loading" infinito
    total_results = len(df_filtered)
    st.write(f"**Exibindo 20 de {total_results} resultados**")
    
    container = st.container(height=650)
    
    with container:
        # Limitamos a exibição aos primeiros 20 resultados para performance fluida
        # O utilizador usa a pesquisa para filtrar o que quer
        for index, row in df_filtered.head(20).iterrows():
            u_key = f"btn_{row['id_cadeira']}_{index}"
            
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    # Usamos markdown simples para evitar sobrecarga de componentes
                    st.markdown(f"**{row['nome_cadeira']}**")
                    st.caption(f"{row['sigla_curso_ref']} | {row['num_alunos']} Alunos")
                with c2:
                    if st.button("➡️", key=u_key):
                        st.session_state["selected_id"] = row['id_cadeira']
                        st.session_state["selected_curso"] = row['sigla_curso_ref']
                        st.rerun()

# --- PAINEL LATERAL (RENDERIZAÇÃO CONDICIONAL) ---
with col_details:
    if "selected_id" in st.session_state:
        # Busca direta por index (mais rápido que filtro de string)
        res = df[(df['id_cadeira'] == st.session_state["selected_id"]) & 
                 (df['sigla_curso_ref'] == st.session_state["selected_curso"])]
        
        if not res.empty:
            row = res.iloc[0]
            st.header(row['nome_cadeira'])
            
            # Layout de métricas compacto
            m1, m2, m3 = st.columns(3)
            m1.metric("Inscritos", row['num_alunos'])
            m2.metric("Créditos", row['ects'])
            m3.metric("Período", row['periodo'])
            
            st.divider()
            
            # Tabs são mais leves que múltiplos expanders
            t1, t2, t3 = st.tabs(["📖 Programa", "📝 Avaliação", "👨‍🏫 Docentes"])
            with t1: st.write(row['programa'])
            with t2: st.info(row['metodo_avaliacao'])
            with t3: st.write(row['docentes'])
            
            st.link_button("🌐 Ver no Fénix", row['url_curso'], use_container_width=True)
    else:
        st.info("💡 Seleciona uma cadeira à esquerda. Pesquisa por sigla (ex: MEAer) para filtrar resultados.")
