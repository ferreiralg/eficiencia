import streamlit as st

st.set_page_config(
    page_title="Análise de Eficiência Hospitalar",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Análise de Eficiência Hospitalar")

st.sidebar.success("Selecione uma análise acima.")

st.markdown(
    """
    Bem-vindo à ferramenta de análise de eficiência hospitalar.

    **👈 Selecione uma das páginas na barra lateral** para começar:

    - **Análise CNES Individual:** Explore os indicadores e a evolução da eficiência para um hospital específico (CNES).
    - **Resultados Consolidados:** Veja métricas agregadas e a distribuição da eficiência entre todos os hospitais.

    Os dados são do período de Jan/2019 a Mar/2024.
    """
) 