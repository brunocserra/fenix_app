import streamlit as st
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="IST Gallery Planner", layout="wide")

# --- ESTILO CSS PARA OS CARDS (Visual de PowerApps) ---
st.markdown("""
    <style>
    .main-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #007bff;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("planeamento_ist_detalhado_2026.csv", encoding="utf-8-sig")
        df['id_cadeira'] = df['id_cadeira'].astype(str)
        df['num_alunos'] = pd.to_numeric(df['num_alunos'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"Erro: {e}")
        return pd.DataFrame()

df = load_data()

# --- INTERFACE ---
st.title("🎓 IST Vertical Gallery")

# Sidebar para filtros (como os filtros no topo de uma PowerApp)
st.sidebar.header("🔍 Filtros")
search = st.sidebar.text_input("Pesquisar disciplina:", "").lower()
periodo_sel = st.sidebar.selectbox("Período:", ["Todos"] + sorted(df['periodo'].unique().tolist()))

# Filttragem
mask = (df['nome_cadeira'].str.lower().str.contains(search, na=False) | 
        df['sigla_curso_ref'].str.lower().str.contains(search, na=False))
if periodo_sel != "Todos":
    mask = mask & (df['periodo'] == periodo_sel)

df_filtered = df[mask]

# --- LAYOUT DE GALERIA ---
col_list, col_details = st.columns([1.2, 1.8])

with col_list:
    st.write(f"**Resultados: {len(df_filtered)}**")
    
    # Criar a "Gallery" vertical
    # Usamos um container com altura fixa se houver muitos itens
    container = st.container(height=600)
    
    with container:
        for index, row in df_filtered.iterrows():
            # Cada item da galeria
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{row['nome_cadeira']}**")
                    st.caption(f"{row['sigla_curso_ref']} | {row['periodo']} | {row['num_alunos']} Alunos")
                with c2:
                    # O botão que "seleciona" o item para o painel lateral
                    if st.button("➡️", key=f"btn_{row['id_cadeira']}"):
                        st.session_state.selected_id = row['id_cadeira']

# --- PAINEL DE DETALHES LATERAL ---
with col_details:
    if "selected_id" in st.session_state:
        # Procurar a linha selecionada
        selected_row = df[df['id_cadeira'] == st.session_state.selected_id].iloc[0]
        
        st.header(selected_row['nome_cadeira'])
        
        # Métricas rápidas estilo Dashboard
        m1, m2, m3 = st.columns(3)
        m1.metric("Inscritos", selected_row['num_alunos'])
        m2.metric("ECTS", selected_row['ects'])
        m3.metric("Período", selected_row['periodo'])
        
        st.divider()
        
        tab_prog, tab_aval, tab_doc = st.tabs(["📖 Programa", "📝 Avaliação", "👨‍🏫 Docentes"])
        
        with tab_prog:
            st.write(selected_row['programa'] if pd.notna(selected_row['programa']) else "Sem dados.")
        
        with tab_aval:
            st.info(selected_row['metodo_avaliacao'] if pd.notna(selected_row['metodo_avaliacao']) else "Sem dados.")
            
        with tab_doc:
            docentes = str(selected_row['docentes']).split(" | ") if pd.notna(selected_row['docentes']) else ["N/A"]
            for d in docentes:
                st.write(f"- {d}")
        
        st.divider()
        st.link_button("🌐 Ver no Fénix", selected_row['url_curso'], use_container_width=True)
    else:
        st.info("💡 Seleciona uma disciplina na galeria à esquerda para ver os detalhes técnicos.")
