import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go # Adicionado para go.Scatter
import os

# --- Configuração da Página ---
st.set_page_config(page_title="Resultados Consolidados", layout="wide")
st.title("📊 Resultados Consolidados por Competência") # Título ajustado

# --- Funções Auxiliares ---
excel_file_path = os.path.join(os.getcwd(), 'resultado_eficiencia.xlsx')

@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path, dtype={'CNES': str})
        df['COMPETEN'] = pd.to_datetime(df['COMPETEN'], format='%Y%m')
        df = df.sort_values(by='COMPETEN')
        numeric_cols = ['CNES_SALAS', 'CNES_LEITOS_SUS', 'HORAS_MEDICOS', 'HORAS_ENFERMAGEM', 'SIA_SIH_VALOR', 'Eficiência']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{os.path.basename(file_path)}' não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar '{os.path.basename(file_path)}': {e}")
        return None

def format_pt_br(value, precision=0, prefix=""):
    if pd.isna(value):
        return '-'
    try:
        formatted = f'{value:,.{precision}f}'
        formatted_swapped = formatted.replace(',', '#').replace('.', ',').replace('#', '.')
        return prefix + formatted_swapped
    except (TypeError, ValueError):
        return value

# Função para cálculo seguro da média ponderada por grupo
def weighted_average(group, data_col, weight_col):
    d = group[data_col]
    w = group[weight_col]
    # Filtrar NaNs e pesos <= 0
    valid_indices = d.notna() & w.notna() & (w > 0)
    d = d[valid_indices]
    w = w[valid_indices]
    if w.sum() == 0:
        return np.nan # Ou 0, ou outra indicação
    return np.average(d, weights=w)

# --- Carregar Dados ---
df_total = load_data(excel_file_path)

if df_total is not None and not df_total.empty:
    st.sidebar.header("Filtro de Período") # Simplificado
    min_competencia_total = df_total['COMPETEN'].min().to_pydatetime()
    max_competencia_total = df_total['COMPETEN'].max().to_pydatetime()

    selected_competencia_range_total = st.sidebar.slider(
        "Selecione o Período (COMPETEN):",
        min_value=min_competencia_total,
        max_value=max_competencia_total,
        value=(min_competencia_total, max_competencia_total),
        format="MM/YYYY",
        key="slider_consolidado"
    )

    # --- Filtrar Dados baseado no Slider ---
    filtered_df_total = df_total[
        (df_total['COMPETEN'] >= selected_competencia_range_total[0]) &
        (df_total['COMPETEN'] <= selected_competencia_range_total[1])
    ].copy()

    if not filtered_df_total.empty:
        st.markdown("### Métricas Gerais (Período Selecionado)")
        # --- Calcular e Exibir Métricas Gerais ---
        col1_geral, col2_geral = st.columns(2)
        media_simples_geral = filtered_df_total['Eficiência'].mean()
        col1_geral.metric("Média Simples (Geral)", format_pt_br(media_simples_geral, 4))
        df_ponderada_geral = filtered_df_total.dropna(subset=['Eficiência', 'SIA_SIH_VALOR'])
        df_ponderada_geral = df_ponderada_geral[df_ponderada_geral['SIA_SIH_VALOR'] > 0]
        if not df_ponderada_geral.empty:
            media_ponderada_geral = np.average(df_ponderada_geral['Eficiência'], weights=df_ponderada_geral['SIA_SIH_VALOR'])
            col2_geral.metric("Média Ponderada (Geral)", format_pt_br(media_ponderada_geral, 4))
        else:
            col2_geral.metric("Média Ponderada (Geral)", "N/A")

        st.divider()

        # --- Calcular Métricas Mensais ---
        # Usar Grouper para garantir que agrupe por mês corretamente
        # Usar floor('D') para garantir que a data resultante seja o início do mês para junção consistente
        monthly_groups = filtered_df_total.groupby(pd.Grouper(key='COMPETEN', freq='ME')) # ME = Month End

        # Média simples mensal
        monthly_simple_means = monthly_groups['Eficiência'].mean().reset_index()
        monthly_simple_means.rename(columns={'Eficiência': 'media_simples'}, inplace=True)
        # Ajustar a data para o início do mês para consistência de plotagem
        monthly_simple_means['COMPETEN'] = monthly_simple_means['COMPETEN'].dt.to_period('M').dt.start_time

        # Média ponderada mensal
        monthly_weighted_means = monthly_groups.apply(
            lambda g: weighted_average(g, 'Eficiência', 'SIA_SIH_VALOR')
        ).reset_index()
        monthly_weighted_means.rename(columns={0: 'media_ponderada'}, inplace=True)
        # Ajustar a data para o início do mês
        monthly_weighted_means['COMPETEN'] = monthly_weighted_means['COMPETEN'].dt.to_period('M').dt.start_time

        # Juntar as médias mensais em um único DataFrame
        monthly_aggregates = pd.merge(monthly_simple_means, monthly_weighted_means, on='COMPETEN', how='outer')

        # --- Plotar Médias Mensais ---
        st.markdown("### Tendências Médias Mensais")
        col1_trend, col2_trend = st.columns(2)

        with col1_trend:
            st.subheader("Média Simples Mensal")
            hover_simple = "<b>Competência:</b> %{x|%m/%Y}<br><b>Média Simples:</b> %{y:,.4f}<extra></extra>".replace('.', ',')
            fig_mean_simple = px.line(
                monthly_aggregates.dropna(subset=['media_simples']), # Plotar apenas não-NaN
                x='COMPETEN',
                y='media_simples',
                markers=True,
                labels={'COMPETEN': 'Competência', 'media_simples': 'Média Simples'}
            )
            fig_mean_simple.update_traces(hovertemplate=hover_simple)
            fig_mean_simple.update_layout(yaxis_title="Média Simples Eficiência", hovermode='x unified')
            st.plotly_chart(fig_mean_simple, use_container_width=True)

        with col2_trend:
            st.subheader("Média Ponderada Mensal")
            hover_weighted = "<b>Competência:</b> %{x|%m/%Y}<br><b>Média Ponderada:</b> %{y:,.4f}<extra></extra>".replace('.', ',')
            fig_mean_weighted = px.line(
                monthly_aggregates.dropna(subset=['media_ponderada']), # Plotar apenas não-NaN
                x='COMPETEN',
                y='media_ponderada',
                markers=True,
                labels={'COMPETEN': 'Competência', 'media_ponderada': 'Média Ponderada (Produção)'}
            )
            fig_mean_weighted.update_traces(hovertemplate=hover_weighted)
            fig_mean_weighted.update_layout(yaxis_title="Média Pond. Eficiência", hovermode='x unified')
            st.plotly_chart(fig_mean_weighted, use_container_width=True)

        st.divider()

        # --- Exibir Box Plot Mensal ---
        st.subheader("Distribuição Mensal da Eficiência entre CNES")
        # Formatar hover do boxplot
        hover_boxplot = (
            "<b>%{yaxis.title.text}:</b> %{y:,.4f}<br>" +
            "<extra></extra>"
        ).replace('.', ',')

        # Criar uma cópia para não alterar o df original filtrado
        df_boxplot = filtered_df_total.copy()
        # Garantir que a coluna COMPETEN é datetime64[ns] se não for já
        df_boxplot['COMPETEN'] = pd.to_datetime(df_boxplot['COMPETEN'])
        # Formatar a coluna de competência para o eixo X (MM/YYYY)
        # Plotly pode lidar com datetime diretamente, mas formatar pode ser mais explícito
        # df_boxplot['Competencia_Str'] = df_boxplot['COMPETEN'].dt.strftime('%m/%Y')
        # Ordenar pelos meses para o gráfico fazer sentido
        df_boxplot = df_boxplot.sort_values('COMPETEN')

        fig_box = px.box(
            df_boxplot,
            x='COMPETEN', # Usar a coluna datetime
            y='Eficiência',
            title="Box Plot Mensal da Eficiência (Todos os CNES)",
            points='outliers',
            labels={'COMPETEN': 'Competência'}
        )
        fig_box.update_traces(hovertemplate=hover_boxplot)
        fig_box.update_layout(yaxis_title="Eficiência", xaxis_title="Competência")
        # Formatar eixo X para mostrar MM/YYYY e ticks mensais
        fig_box.update_xaxes(dtick="M1", tickformat="%m/%Y", tickangle=45)
        st.plotly_chart(fig_box, use_container_width=True)

    else:
        st.warning("Não há dados para o período selecionado.")

elif df_total is None:
    pass
else:
    st.warning("O arquivo Excel de origem está vazio ou não pôde ser lido corretamente.") 