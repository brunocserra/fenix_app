import streamlit as st
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="IST Planner 2026",
    layout="wide",
    page_icon="🚀"
)

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("planeamento_ist_detalhado_2026.csv", encoding="utf-8-sig")
        df['id_cadeira'] = df['id_cadeira'].astype(str)
        df['num_alunos'] = pd.to_numeric(df['num_alunos'], errors='coerce').fillna(0).astype(int)
        # Criamos uma coluna auxiliar para a seleção
        df.insert(0, "Selecionar", False)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o ficheiro CSV: {e}")
        return pd.DataFrame()

df_raw = load_data()

# --- INTERFACE ---
st.title("🎓 IST Academic Planner 2026")

if not df_raw.empty:
    # --- SIDEBAR FILTROS ---
    st.sidebar.header("🔍 Filtros")
    search = st.sidebar.text_input("Procurar:", "").lower()
    
    # Filtragem
    mask = (
        df_raw['sigla_curso_ref'].str.lower().str.contains(search, na=False) | 
        df_raw['nome_cadeira'].str.lower().str.contains(search, na=False)
    )
    df_filtered = df_raw[mask].copy()

    # --- TABELA DINÂMICA (EDITOR) ---
    st.write("### Lista de Unidades Curriculares")
    st.caption("Ativa a caixa 'Selecionar' na linha desejada para abrir os detalhes.")

    # Colunas que aparecem na tabela estilo Excel
    cols_excel = ['Selecionar', 'sigla_curso_ref', 'nome_cadeira', 'ects', 'periodo', 'num_alunos']
    
    # Data Editor permite interação dinâmica
    edited_df = st.data_editor(
        df_filtered[cols_excel],
        hide_index=True,
        use_container_width=True,
        disabled=['sigla_curso_ref', 'nome_cadeira', 'ects', 'periodo', 'num_alunos'] # Apenas 'Selecionar' é editável
    )

    # Identificar qual linha foi selecionada
    selected_row = edited_df[edited_df["Selecionar"] == True]

    if not selected_row.empty:
        # Obter os dados completos da linha selecionada (incluindo programa e docentes)
        # Fazemos o match pelo nome da cadeira (assumindo nomes únicos no filtro atual)
        target_name = selected_row.iloc[0]['nome_cadeira']
        full_row = df_filtered[df_filtered['nome_cadeira'] == target_name].iloc[0]

        st.divider()
        
        # --- PAINEL DE DETALHES (LAYOUT LATERAL) ---
        col_main, col_side = st.columns([2, 1])
        
        with col_main:
            st.header(f"📘 {full_row['nome_cadeira']}")
            st.subheader("Programa")
            st.write(full_row['programa'] if pd.notna(full_row['programa']) else "N/A")
            
            st.subheader("Método de Avaliação")
            st.info(full_row['metodo_avaliacao'] if pd.notna(full_row['metodo_avaliacao']) else "N/A")

        with col_side:
            st.subheader("📊 Ficha Técnica")
            st.metric("Inscritos", f"{full_row['num_alunos']}")
            st.metric("ECTS", f"{full_row['ects']}")
            st.metric("Período", full_row['periodo'])
            
            st.markdown("**👨‍🏫 Docentes:**")
            docentes = str(full_row['docentes']).split(" | ") if pd.notna(full_row['docentes']) else ["N/A"]
            for d in docentes:
                st.write(f"- {d}")
            
            st.divider()
            st.link_button("🌐 Abrir no Fénix", full_row['url_curso'], use_container_width=True)
    else:
        st.info("💡 Ativa a checkbox na tabela acima para analisar os detalhes técnicos da UC.")

else:
    st.error("CSV não encontrado.")

st.markdown("---")
st.caption("IST Planner v2.2 | Foco em Performance Humana e Dados")
