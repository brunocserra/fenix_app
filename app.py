import streamlit as st
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IST Gallery Planner", layout="wide", page_icon="🚀")

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("planeamento_ist_detalhado_2026.csv", encoding="utf-8-sig")
        df['id_cadeira'] = df['id_cadeira'].astype(str)
        df['num_alunos'] = pd.to_numeric(df['num_alunos'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar CSV: {e}")
        return pd.DataFrame()

df = load_data()

# --- INTERFACE ---
st.title("🎓 IST Vertical Gallery")

# Sidebar para filtros
st.sidebar.header("🔍 Filtros de Pesquisa")
search = st.sidebar.text_input("Pesquisar (Nome ou Sigla):", "").lower()
periodo_sel = st.sidebar.selectbox("Período:", ["Todos"] + sorted(df['periodo'].unique().tolist()))

# Lógica de filtragem (respeitando as `pelicas`)
mask = (df['nome_cadeira'].str.lower().str.contains(search, na=False) | 
        df['sigla_curso_ref'].str.lower().str.contains(search, na=False))
if periodo_sel != "Todos":
    mask = mask & (df['periodo'] == periodo_sel)

df_filtered = df[mask]

# --- LAYOUT DE GALERIA ---
col_list, col_details = st.columns([1.2, 1.8])

with col_list:
    st.write(f"**Resultados: {len(df_filtered)}**")
    container = st.container(height=650)
    
    with container:
        for index, row in df_filtered.iterrows():
            # Chave única para evitar DuplicateElementKey
            unique_key = f"btn_{row['id_cadeira']}_{row['sigla_curso_ref']}_{index}"
            
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{row['nome_cadeira']}**")
                    st.caption(f"{row['sigla_curso_ref']} | {row['periodo']} | {row['num_alunos']} Alunos")
                with c2:
                    if st.button("➡️", key=unique_key):
                        # Atribuição segura ao Session State
                        st.session_state["selected_id"] = row['id_cadeira']
                        st.session_state["selected_curso"] = row['sigla_curso_ref']
                        # Forçar recarregamento para atualizar o painel lateral
                        st.rerun()

# --- PAINEL DE DETALHES LATERAL (VALIDADO) ---
with col_details:
    # Verificação de segurança: Só avança se AMBAS as chaves existirem
    if "selected_id" in st.session_state and "selected_curso" in st.session_state:
        
        # Filtro rigoroso usando as chaves guardadas
        selection = df[
            (df['id_cadeira'] == st.session_state["selected_id"]) & 
            (df['sigla_curso_ref'] == st.session_state["selected_curso"])
        ]
        
        if not selection.empty:
            row = selection.iloc[0]
            st.header(row['nome_cadeira'])
            
            # Dashboard de métricas
            m1, m2, m3 = st.columns(3)
            m1.metric("Inscritos", f"{row['num_alunos']}")
            m2.metric("Créditos", f"{row['ects']} ECTS")
            m3.metric("Período", row['periodo'])
            
            st.divider()
            
            # Organização por Tabs para eficiência de leitura
            t1, t2, t3 = st.tabs(["📖 Programa", "📝 Avaliação", "👨‍🏫 Docentes"])
            
            with t1:
                st.write(row['programa'] if pd.notna(row['programa']) else "N/A")
            
            with t2:
                # Destaque para o método de avaliação (foco em exames)
                st.info(row['metodo_avaliacao'] if pd.notna(row['metodo_avaliacao']) else "N/A")
                
            with t3:
                docentes = str(row['docentes']).split(" | ") if pd.notna(row['docentes']) else ["N/A"]
                for d in docentes:
                    st.write(f"- {d}")
            
            st.divider()
            st.link_button("🌐 Ver no Fénix", row['url_curso'], use_container_width=True)
    else:
        # Estado inicial (Idle)
        st.info("💡 Seleciona uma disciplina na galeria à esquerda para analisar o dossier técnico.")
        # Opcional: Mostrar um gráfico ou estatística geral aqui enquanto nada está selecionado
