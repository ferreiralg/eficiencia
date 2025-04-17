import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import google.generativeai as genai

# --- Configuração da Página ---
st.set_page_config(page_title="Análise CNES Individual", layout="wide") # Config específica da página
st.title("🔬 Análise CNES Individual")

# --- Funções Auxiliares ---
excel_file_path = os.path.join(os.getcwd(), 'resultado_eficiencia.xlsx')

@st.cache_data
def load_data(file_path):
    # ... (mesma função load_data usada na página consolidada) ...
    try:
        df = pd.read_excel(file_path, dtype={'CNES': str})
        df['COMPETEN'] = pd.to_datetime(df['COMPETEN'], format='%Y%m')
        df = df.sort_values(by='COMPETEN')
        numeric_cols = ['CNES_SALAS', 'CNES_LEITOS_SUS', 'HORAS_MEDICOS', 'HORAS_ENFERMAGEM', 'SIA_SIH_VALOR', 'Eficiência']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        # Handle potential missing values if needed before returning
        # For example, fill specific columns with 0 or mean, or drop rows
        # df['HORAS_MEDICOS'] = df['HORAS_MEDICOS'].fillna(0) # Example
        return df
    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{os.path.basename(file_path)}' não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar '{os.path.basename(file_path)}': {e}")
        return None

def format_pt_br(value, precision=0, prefix=""):
    # ... (mesma função format_pt_br usada na página consolidada) ...
    if pd.isna(value):
        return '-'
    try:
        formatted = f'{value:,.{precision}f}'
        formatted_swapped = formatted.replace(',', '#').replace('.', ',').replace('#', '.')
        return prefix + formatted_swapped
    except (TypeError, ValueError):
        return value

# --- Função para chamar a API Gemini ---
@st.cache_data # Cacheia a chamada da API para evitar repetições
def gerar_analise_evolucao(cnes, periodo_inicio, periodo_fim, dados_mensais_md):
    """
    Chama a API Gemini para gerar uma análise textual da evolução dos indicadores,
    usando dados mensais detalhados e contexto DEA.
    """
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        return "Erro: Chave da API Gemini não configurada em .streamlit/secrets.toml"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro-latest') # Alterado de gemini-1.5-flash

        # Prompt detalhado com contexto DEA e dados mensais
        prompt = f"""
        **Tarefa:** Analisar a evolução da eficiência do hospital com CNES {cnes} durante o período de {periodo_inicio} a {periodo_fim}.

        **Contexto da Análise:**
        - **Métrica Principal:** Eficiência, calculada via Análise Envoltória de Dados (DEA), com score variando de 0 (menos eficiente) a 1 (mais eficiente).
        - **Fatores Considerados (Inputs DEA):** CNES_SALAS (Número de Salas), CNES_LEITOS_SUS (Número de Leitos SUS), HORAS_MEDICOS (Total de Horas Médicas), HORAS_ENFERMAGEM (Total de Horas de Enfermagem).
        - **Resultado Medido (Output DEA):** SIA_SIH_VALOR (Valor da Produção Ambulatorial e Hospitalar).
        - **Interpretação da Eficiência DEA:** A eficiência indica a capacidade do hospital em gerar produção (output) a partir dos recursos utilizados (inputs).
            - Aumento de inputs sem aumento proporcional de output -> tende a *diminuir* a eficiência.
            - Redução de inputs mantendo/aumentando output -> tende a *aumentar* a eficiência.
            - Aumento de output sem aumento proporcional de inputs -> tende a *aumentar* a eficiência.

        **Dados Mensais para Análise (Formato Markdown):**
        {dados_mensais_md}

        **Instruções para a Resposta:**
        1.  **Formato:** Gere uma análise textual concisa (aproximadamente 3 a 5 frases) em português brasileiro.
        2.  **Foco Exclusivo:** Baseie sua análise *estritamente* nos dados fornecidos na tabela (Eficiência, Leitos, Salas, Produção, Horas Médicos, Horas Enfermagem) e no período especificado.
        3.  **Conteúdo da Análise:** Descreva as principais tendências da *Eficiência* durante o período. **Verifique e comente explicitamente na análise se as variações na eficiência (aumentos, diminuições, estabilidade) são coerentes com as mudanças observadas nos inputs (Leitos, Salas, Horas) e no output (Produção), aplicando a lógica de interpretação DEA fornecida.**
        4.  **Restrição Crucial:** *Não* faça suposições sobre causas externas, não ofereça recomendações, sugestões de melhoria ou qualquer análise que extrapole a observação direta dos dados e suas correlações internas conforme a lógica DEA explicada. 
              *Não citar lógica DEA expressamente no texto final*, use a lógica apenas para seu raciocínio.

        """

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Erro ao gerar análise com Gemini: {e}"

# --- Carregar Dados ---
df = load_data(excel_file_path)

if df is not None and not df.empty:
    # --- Sidebar Filters ---
    st.sidebar.header("Filtros (Análise Individual)") # Título ajustado
    # ... (código do selectbox e slider como antes, talvez com key diferente se necessário) ...
    all_cnes = sorted(df['CNES'].unique())
    selected_cnes = st.sidebar.selectbox("Selecione o CNES:", options=all_cnes, key="select_cnes_individual")

    min_competencia = df['COMPETEN'].min().to_pydatetime()
    max_competencia = df['COMPETEN'].max().to_pydatetime()
    selected_competencia_range = st.sidebar.slider(
        "Selecione o Período (COMPETEN):",
        min_value=min_competencia,
        max_value=max_competencia,
        value=(min_competencia, max_competencia),
        format="MM/YYYY",
        key="slider_individual"
    )
    # ... (código de filtragem como antes) ...
    filtered_df = df[
        (df['CNES'] == selected_cnes) &
        (df['COMPETEN'] >= selected_competencia_range[0]) &
        (df['COMPETEN'] <= selected_competencia_range[1])
    ].copy() # Usar cópia

    st.markdown("### Indicadores Principais")
    if not filtered_df.empty:
        filtered_df_sorted = filtered_df.sort_values(by='COMPETEN')
        latest_data = filtered_df_sorted.iloc[-1]

        # --- Display KPIs (com formatação pt-BR) ---
        st.subheader(f"Indicadores para {latest_data['COMPETEN'].strftime('%m/%Y')} (CNES: {selected_cnes})")
        col1, col2 = st.columns(2)

        # KPI Eficiência
        eficiencia_latest = latest_data['Eficiência']
        eficiencia_delta_str = "N/A"
        if len(filtered_df_sorted) > 1:
            eficiencia_previous = filtered_df_sorted.iloc[-2]['Eficiência']
            if pd.notna(eficiencia_previous) and eficiencia_previous != 0:
                eficiencia_delta = ((eficiencia_latest - eficiencia_previous) / eficiencia_previous) * 100
                eficiencia_delta_str = f"{eficiencia_delta:.2f}%"
            elif pd.notna(eficiencia_previous):
                 eficiencia_delta_str = "N/A (ant=0)"
        col1.metric("Última Eficiência", format_pt_br(eficiencia_latest, 4), delta=eficiencia_delta_str)

        # KPI Produção
        producao_latest = latest_data['SIA_SIH_VALOR']
        producao_delta_str = "N/A"
        if len(filtered_df_sorted) > 1:
            producao_previous = filtered_df_sorted.iloc[-2]['SIA_SIH_VALOR']
            if pd.notna(producao_previous) and producao_previous != 0:
                producao_delta = ((producao_latest - producao_previous) / producao_previous) * 100
                producao_delta_str = f"{producao_delta:.2f}%"
            elif pd.notna(producao_previous):
                 producao_delta_str = "N/A (ant=0)"
        col2.metric("Última Produção Total", format_pt_br(producao_latest, 2, prefix="R$ "), delta=producao_delta_str)

        st.divider()

        # --- Gráfico Principal: Eficiência (com hover formatado) ---
        st.subheader(f"Evolução da Eficiência (CNES: {selected_cnes})")
        # Format hover template for pt-BR numbers
        hover_template_eficiencia_fmt = (
            "<b>Competência:</b> %{x|%m/%Y}<br>" +
            "<b>Eficiência:</b> %{y:,.4f}<br>" + # 4 decimal places, comma separator initially
            "<extra></extra>"
        )
        hover_template_eficiencia_final = hover_template_eficiencia_fmt.replace(',', '#').replace('.', ',').replace('#', '.')

        fig_eficiencia = px.line(
            filtered_df_sorted,
            x='COMPETEN',
            y='Eficiência',
            markers=True,
            labels={'COMPETEN': 'Competência', 'Eficiência': 'Valor da Eficiência'},
            # Apply hover template directly during creation if possible with px
            # Update: px.line doesn't directly take hovertemplate this way, use update_traces
        )
        # Apply formatted template using update_traces
        fig_eficiencia.update_traces(hovertemplate=hover_template_eficiencia_final)
        fig_eficiencia.update_layout(xaxis_title="Competência", yaxis_title="Eficiência", hovermode="x unified")
        st.plotly_chart(fig_eficiencia, use_container_width=True)

        # --- Análise Automática com Gemini ---
        st.subheader("🤖 Análise Automática da Evolução (IA)")

        # Verificar se temos dados suficientes (pelo menos 1 ponto)
        if not filtered_df_sorted.empty:
            try:
                # Preparar dados mensais para o prompt (tabela Markdown)
                cols_para_analise = ['COMPETEN', 'Eficiência', 'CNES_LEITOS_SUS', 'SIA_SIH_VALOR', 'HORAS_MEDICOS', 'HORAS_ENFERMAGEM']
                df_analise = filtered_df_sorted[cols_para_analise].copy()

                # Formatar data para MM/YYYY
                df_analise['COMPETEN'] = df_analise['COMPETEN'].dt.strftime('%m/%Y')

                # Renomear colunas para clareza no prompt (opcional, mas bom)
                df_analise.rename(columns={
                    'COMPETEN': 'Competência',
                    'CNES_LEITOS_SUS': 'Leitos SUS',
                    'SIA_SIH_VALOR': 'Produção Total',
                    'HORAS_MEDICOS': 'Horas Médicos',
                    'HORAS_ENFERMAGEM': 'Horas Enfermagem'
                }, inplace=True)

                # Converter para Markdown
                # Usar floatfmt para formatar números (ajuste as precisões conforme necessário)
                dados_mensais_md = df_analise.to_markdown(
                    index=False,
                    floatfmt=(".0s", ".4f", ".0f", ",.2f", ".0f", ".0f") # Formatos: Competencia, Eficiência, Leitos, Prod, HMed, HEnf
                )

                # Chamar a função cacheada com a string markdown
                with st.spinner("Gerando análise detalhada com IA... Aguarde alguns segundos."):
                    analise_texto = gerar_analise_evolucao(
                        selected_cnes,
                        selected_competencia_range[0].strftime('%m/%Y'),
                        selected_competencia_range[1].strftime('%m/%Y'),
                        dados_mensais_md # Passa a tabela markdown
                    )
                st.markdown(analise_texto)

            except Exception as e:
                st.error(f"Ocorreu um erro ao gerar a análise automática: {e}")
        else:
             st.info("Não há dados disponíveis para gerar a análise.")

        st.divider()

        # --- Subplots 2x2 (com hover formatado) ---
        st.subheader("Evolução dos Componentes")
        fig_subplots = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Leitos SUS', 'Produção Total', 'Horas Médicos', 'Horas Enfermagem'),
            vertical_spacing=0.15,
            shared_xaxes=True # Compartilhar eixo X
         )

        # Define and format templates first
        hover_leitos_fmt = (
            "<b>Competência:</b> %{x|%m/%Y}<br>"+
            "<b>Leitos SUS:</b> %{y:,.0f}<br>"+
            "<extra></extra>"
        )
        hover_leitos_final = hover_leitos_fmt.replace(',', '#').replace('.', ',').replace('#', '.')

        hover_producao_fmt = (
            "<b>Competência:</b> %{x|%m/%Y}<br>"+
            "<b>Produção Total:</b> R$ %{y:,.2f}<br>"+
            "<extra></extra>"
        )
        hover_producao_final = hover_producao_fmt.replace(',', '#').replace('.', ',').replace('#', '.')

        hover_hmed_fmt = (
            "<b>Competência:</b> %{x|%m/%Y}<br>"+
            "<b>Horas Médicos:</b> %{y:,.0f}<br>"+
            "<extra></extra>"
        )
        hover_hmed_final = hover_hmed_fmt.replace(',', '#').replace('.', ',').replace('#', '.')

        hover_henf_fmt = (
            "<b>Competência:</b> %{x|%m/%Y}<br>"+
            "<b>Horas Enfermagem:</b> %{y:,.0f}<br>"+
            "<extra></extra>"
        )
        hover_henf_final = hover_henf_fmt.replace(',', '#').replace('.', ',').replace('#', '.')

        # Adicionar traces com hover formatado aplicado diretamente
        fig_subplots.add_trace(go.Scatter(x=filtered_df_sorted['COMPETEN'], y=filtered_df_sorted['CNES_LEITOS_SUS'], mode='lines+markers', name='Leitos SUS', hovertemplate=hover_leitos_final), row=1, col=1)
        fig_subplots.add_trace(go.Scatter(x=filtered_df_sorted['COMPETEN'], y=filtered_df_sorted['SIA_SIH_VALOR'], mode='lines+markers', name='Produção Total', hovertemplate=hover_producao_final), row=1, col=2)
        fig_subplots.add_trace(go.Scatter(x=filtered_df_sorted['COMPETEN'], y=filtered_df_sorted['HORAS_MEDICOS'], mode='lines+markers', name='Horas Médicos', hovertemplate=hover_hmed_final), row=2, col=1)
        fig_subplots.add_trace(go.Scatter(x=filtered_df_sorted['COMPETEN'], y=filtered_df_sorted['HORAS_ENFERMAGEM'], mode='lines+markers', name='Horas Enfermagem', hovertemplate=hover_henf_final), row=2, col=2)

        fig_subplots.update_layout(height=600, showlegend=False, hovermode="x unified")
        fig_subplots.update_xaxes(title_text="Competência")
        fig_subplots.update_yaxes(title_text="Leitos SUS", row=1, col=1)
        fig_subplots.update_yaxes(title_text="Produção Total", row=1, col=2)
        fig_subplots.update_yaxes(title_text="Horas Médicos", row=2, col=1)
        fig_subplots.update_yaxes(title_text="Horas Enfermagem", row=2, col=2)
        st.plotly_chart(fig_subplots, use_container_width=True)

        st.divider()

        # --- Distribuição e Correlações (com hover formatado) ---
        st.subheader("Distribuição e Correlações")
        col_hist, col_scatter1, col_scatter2 = st.columns(3)

        # Histograma
        with col_hist:
            # Format hover template for pt-BR numbers
            hover_hist_fmt = (
                "<b>Faixa Eficiência:</b> %{x:,.4f}<br>"+
                "<b>Contagem:</b> %{y}<br>"+
                "<extra></extra>"
            )
            hover_hist_final = hover_hist_fmt.replace(',', '#').replace('.', ',').replace('#', '.')

            fig_hist = px.histogram(
                filtered_df_sorted, x='Eficiência', title='Distribuição da Eficiência',
                labels={'Eficiência': 'Faixa de Eficiência'}
            )
            # Apply formatted template using update_traces
            fig_hist.update_traces(hovertemplate=hover_hist_final)
            fig_hist.update_layout(yaxis_title="Contagem (meses)", xaxis_title="Eficiência")
            st.plotly_chart(fig_hist, use_container_width=True)

        # Scatter Produção vs Eficiência
        with col_scatter1:
            # Format hover template for pt-BR numbers
            hover_scatter_prod_fmt = (
                "<b>Produção:</b> R$ %{x:,.2f}<br>"+
                "<b>Eficiência:</b> %{y:,.4f}<br>"+
                "<b>Competência:</b> %{customdata[0]|%m/%Y}<br>"+
                "<extra></extra>"
            )
            hover_scatter_prod_final = hover_scatter_prod_fmt.replace(',', '#').replace('.', ',').replace('#', '.')

            fig_scatter_prod = px.scatter(
                filtered_df_sorted, x='SIA_SIH_VALOR', y='Eficiência',
                title='Produção vs Eficiência', labels={'SIA_SIH_VALOR': 'Produção Total', 'Eficiência': 'Eficiência'},
                custom_data=['COMPETEN']
            )
             # Apply formatted template using update_traces
            fig_scatter_prod.update_traces(hovertemplate=hover_scatter_prod_final)
            fig_scatter_prod.update_layout(yaxis_title="Eficiência", xaxis_title="Produção Total")
            st.plotly_chart(fig_scatter_prod, use_container_width=True)

        # Scatter Leitos vs Eficiência
        with col_scatter2:
            # Format hover template for pt-BR numbers
            hover_scatter_leitos_fmt = (
                "<b>Leitos SUS:</b> %{x:,.0f}<br>"+
                "<b>Eficiência:</b> %{y:,.4f}<br>"+
                "<b>Competência:</b> %{customdata[0]|%m/%Y}<br>"+
                "<extra></extra>"
            )
            hover_scatter_leitos_final = hover_scatter_leitos_fmt.replace(',', '#').replace('.', ',').replace('#', '.')

            fig_scatter_leitos = px.scatter(
                filtered_df_sorted, x='CNES_LEITOS_SUS', y='Eficiência',
                title='Leitos SUS vs Eficiência', labels={'CNES_LEITOS_SUS': 'Leitos SUS', 'Eficiência': 'Eficiência'},
                custom_data=['COMPETEN']
            )
            # Apply formatted template using update_traces
            fig_scatter_leitos.update_traces(hovertemplate=hover_scatter_leitos_final)
            fig_scatter_leitos.update_layout(yaxis_title="Eficiência", xaxis_title="Leitos SUS")
            st.plotly_chart(fig_scatter_leitos, use_container_width=True)

    else:
        st.warning("Não há dados para o CNES e período selecionados.")

    st.divider()

    # --- Tabela de Dados Filtrados (código inalterado) ---
    if st.checkbox("Mostrar dados filtrados", key="chk_dados_individuais"):
        st.subheader("Dados Filtrados")
        # ... (código da formatação da tabela como estava antes) ...
        df_display = filtered_df.copy()
        rename_map = {
            'CNES_SALAS': 'Salas',
            'CNES_LEITOS_SUS': 'Leitos SUS',
            'HORAS_MEDICOS': 'Horas Médicos',
            'HORAS_ENFERMAGEM': 'Horas Enfermagem',
            'SIA_SIH_VALOR': 'Produção Total',
            'COMPETEN': 'Competência'
        }
        df_display = df_display.rename(columns=rename_map)
        if 'Competência' in df_display.columns:
            df_display['Competência'] = df_display['Competência'].dt.strftime('%m/%Y')
        display_columns = [
            'CNES', 'Competência', 'Salas', 'Leitos SUS',
            'Horas Médicos', 'Horas Enfermagem', 'Produção Total', 'Eficiência'
        ]
        existing_display_columns = [col for col in display_columns if col in df_display.columns]
        df_display_final = df_display[existing_display_columns]
        def format_pt_br_table(value, precision=0):
            if pd.isna(value):
                return '-'
            try:
                formatted = f'{value:,.{precision}f}'
                formatted_swapped = formatted.replace(',', '#').replace('.', ',').replace('#', '.')
                return formatted_swapped
            except (TypeError, ValueError):
                return value
        cols_zero_decimals = ['Salas', 'Leitos SUS', 'Horas Médicos', 'Horas Enfermagem']
        for col in cols_zero_decimals:
            if col in df_display_final.columns:
                df_display_final[col] = df_display_final[col].apply(lambda x: format_pt_br_table(x, 0))
        if 'Produção Total' in df_display_final.columns:
            df_display_final['Produção Total'] = df_display_final['Produção Total'].apply(lambda x: format_pt_br_table(x, 2))
        if 'Eficiência' in df_display_final.columns:
             df_display_final['Eficiência'] = df_display_final['Eficiência'].apply(lambda x: format_pt_br_table(x, 4))
        st.dataframe(df_display_final, hide_index=True)

elif df is None:
    pass # Erro tratado em load_data
else:
    st.warning("O arquivo Excel de origem está vazio ou não pôde ser lido corretamente.") 