import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Import graph_objects
from plotly.subplots import make_subplots # Import make_subplots
import os

# Define the path to the Excel file
current_directory = os.getcwd()
excel_file_path = os.path.join(current_directory, 'resultado_eficiencia.xlsx')

# --- Page Configuration ---
st.set_page_config(page_title="Análise de Eficiência CNES", layout="wide")
st.title("Visualização da Eficiência por CNES")

# --- Load Data ---
@st.cache_data # Cache the data loading to improve performance
def load_data(file_path):
    try:
        df = pd.read_excel(file_path, dtype={'CNES': str}) # Ensure CNES is read as string
        # Convert COMPETEN (YYYYMM) to datetime objects for proper sorting and filtering
        df['COMPETEN'] = pd.to_datetime(df['COMPETEN'], format='%Y%m')
        df = df.sort_values(by='COMPETEN') # Sort by date
        return df
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{os.path.basename(file_path)}' não foi encontrado no diretório atual.")
        st.info("Certifique-se de que o arquivo existe e que você executou o script `concat_csv_to_xlsx.py` primeiro.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o arquivo Excel: {e}")
        return None

df = load_data(excel_file_path)

if df is not None and not df.empty:
    # --- Sidebar Filters ---
    st.sidebar.header("Filtros")

    # CNES Selection
    all_cnes = sorted(df['CNES'].unique())
    selected_cnes = st.sidebar.selectbox("Selecione o CNES:", options=all_cnes)

    # COMPETEN Range Slider
    min_competencia = df['COMPETEN'].min().to_pydatetime()
    max_competencia = df['COMPETEN'].max().to_pydatetime()

    selected_competencia_range = st.sidebar.slider(
        "Selecione o Período (COMPETEN):",
        min_value=min_competencia,
        max_value=max_competencia,
        value=(min_competencia, max_competencia), # Default to full range
        format="MM/YYYY" # Display format for slider
    )

    # --- Filter Data based on Selection ---
    filtered_df = df[
        (df['CNES'] == selected_cnes) &
        (df['COMPETEN'] >= selected_competencia_range[0]) &
        (df['COMPETEN'] <= selected_competencia_range[1])
    ]

    st.markdown("### Indicadores Principais") # Main Title for this section

    if not filtered_df.empty:
        # Sort filtered data by date to easily find latest/previous
        filtered_df_sorted = filtered_df.sort_values(by='COMPETEN')
        latest_data = filtered_df_sorted.iloc[-1]

        # --- Display KPIs ---
        st.subheader(f"Indicadores para {latest_data['COMPETEN'].strftime('%m/%Y')} (CNES: {selected_cnes})")
        col1, col2 = st.columns(2)

        # KPI: Eficiência
        eficiencia_latest = latest_data['Eficiência']
        eficiencia_delta = None
        if len(filtered_df_sorted) > 1:
            previous_data = filtered_df_sorted.iloc[-2]
            eficiencia_previous = previous_data['Eficiência']
            if pd.notna(eficiencia_previous) and eficiencia_previous != 0: # Avoid division by zero
                 eficiencia_delta = ((eficiencia_latest - eficiencia_previous) / eficiencia_previous) * 100 # Calculate percentage change
                 eficiencia_delta = f"{eficiencia_delta:.2f}%" # Format as percentage string
            elif pd.notna(eficiencia_previous):
                 eficiencia_delta = "N/A (anterior=0)"
        col1.metric("Última Eficiência", f"{eficiencia_latest:.4f}".replace('.', ','), delta=eficiencia_delta)

        # KPI: Produção Total
        producao_latest = latest_data['SIA_SIH_VALOR']
        producao_delta = None
        if len(filtered_df_sorted) > 1:
            previous_data = filtered_df_sorted.iloc[-2]
            producao_previous = previous_data['SIA_SIH_VALOR']
            if pd.notna(producao_previous) and producao_previous != 0:
                producao_delta = ((producao_latest - producao_previous) / producao_previous) * 100
                producao_delta = f"{producao_delta:.2f}%"
            elif pd.notna(producao_previous):
                 producao_delta = "N/A (anterior=0)"
        # Format number for pt-BR display
        producao_formatted = f"{producao_latest:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
        col2.metric("Última Produção Total", f"R$ {producao_formatted}", delta=producao_delta)

        st.divider() # Add a visual separator

        # --- Display Main Chart: Eficiência ---
        st.subheader(f"Evolução da Eficiência (CNES: {selected_cnes})")
        fig_eficiencia = px.line(
            filtered_df_sorted, # Use sorted data
            x='COMPETEN',
            y='Eficiência',
            # title=f'Evolução da Eficiência - CNES {selected_cnes}', # Title moved to subheader
            markers=True,
            labels={'COMPETEN': 'Competência', 'Eficiência': 'Valor da Eficiência'}
        )
        fig_eficiencia.update_layout(xaxis_title="Competência", yaxis_title="Eficiência")
        st.plotly_chart(fig_eficiencia, use_container_width=True)

        st.divider()

        # --- Display Subplots for Leitos, Produção, Horas ---
        st.subheader("Evolução dos Componentes")
        # Create a 2x2 subplot grid
        fig_subplots = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Leitos SUS', 'Produção Total', 'Horas Médicos', 'Horas Enfermagem'),
            vertical_spacing=0.15 # Adjust spacing if needed
         )

        # Row 1, Col 1: Leitos SUS
        fig_subplots.add_trace(go.Scatter(x=filtered_df_sorted['COMPETEN'], y=filtered_df_sorted['CNES_LEITOS_SUS'], mode='lines+markers', name='Leitos SUS'), row=1, col=1)
        # Row 1, Col 2: Produção Total
        fig_subplots.add_trace(go.Scatter(x=filtered_df_sorted['COMPETEN'], y=filtered_df_sorted['SIA_SIH_VALOR'], mode='lines+markers', name='Produção Total'), row=1, col=2)
        # Row 2, Col 1: Horas Médicos
        fig_subplots.add_trace(go.Scatter(x=filtered_df_sorted['COMPETEN'], y=filtered_df_sorted['HORAS_MEDICOS'], mode='lines+markers', name='Horas Médicos'), row=2, col=1)
        # Row 2, Col 2: Horas Enfermagem
        fig_subplots.add_trace(go.Scatter(x=filtered_df_sorted['COMPETEN'], y=filtered_df_sorted['HORAS_ENFERMAGEM'], mode='lines+markers', name='Horas Enfermagem'), row=2, col=2)

        # Update layout for subplots
        fig_subplots.update_layout(
            height=600, # Increased height for 2 rows
            showlegend=False,
            # title_text=f"Componentes - CNES {selected_cnes}" # Title moved to subheader
        )
        # Update axes titles for all subplots
        fig_subplots.update_xaxes(title_text="Competência")
        fig_subplots.update_yaxes(title_text="Leitos SUS", row=1, col=1)
        fig_subplots.update_yaxes(title_text="Produção Total", row=1, col=2)
        fig_subplots.update_yaxes(title_text="Horas Médicos", row=2, col=1)
        fig_subplots.update_yaxes(title_text="Horas Enfermagem", row=2, col=2)

        st.plotly_chart(fig_subplots, use_container_width=True)

        st.divider()

        # --- Display Histogram and Scatter Plots ---
        st.subheader("Distribuição e Correlações")
        col_hist, col_scatter1, col_scatter2 = st.columns(3)

        # Histogram: Eficiência Distribution
        with col_hist:
            fig_hist = px.histogram(
                filtered_df_sorted,
                x='Eficiência',
                title='Distribuição da Eficiência',
                labels={'Eficiência': 'Faixa de Eficiência'}
            )
            fig_hist.update_layout(yaxis_title="Contagem (meses)", xaxis_title="Eficiência")
            st.plotly_chart(fig_hist, use_container_width=True)

        # Scatter Plot 1: Produção Total vs Eficiência
        with col_scatter1:
            fig_scatter_prod = px.scatter(
                filtered_df_sorted,
                x='SIA_SIH_VALOR',
                y='Eficiência',
                title='Produção vs Eficiência',
                labels={'SIA_SIH_VALOR': 'Produção Total', 'Eficiência': 'Eficiência'},
                hover_data=['COMPETEN'] # Show date on hover
            )
            fig_scatter_prod.update_layout(yaxis_title="Eficiência", xaxis_title="Produção Total")
            st.plotly_chart(fig_scatter_prod, use_container_width=True)

        # Scatter Plot 2: Leitos SUS vs Eficiência
        with col_scatter2:
            fig_scatter_leitos = px.scatter(
                filtered_df_sorted,
                x='CNES_LEITOS_SUS',
                y='Eficiência',
                title='Leitos SUS vs Eficiência',
                labels={'CNES_LEITOS_SUS': 'Leitos SUS', 'Eficiência': 'Eficiência'},
                hover_data=['COMPETEN'] # Show date on hover
            )
            fig_scatter_leitos.update_layout(yaxis_title="Eficiência", xaxis_title="Leitos SUS")
            st.plotly_chart(fig_scatter_leitos, use_container_width=True)

    else:
        st.warning("Não há dados para o CNES e período selecionados.")

    st.divider()

    # --- Display Filtered Data Table (Optional) ---
    if st.checkbox("Mostrar dados filtrados"):
        st.subheader("Dados Filtrados")

        # --- Prepare DataFrame for Display ---
        # Create a copy for display modifications
        df_display = filtered_df.copy()

        # Rename columns for display
        rename_map = {
            'CNES_SALAS': 'Salas',
            'CNES_LEITOS_SUS': 'Leitos SUS',
            'HORAS_MEDICOS': 'Horas Médicos',
            'HORAS_ENFERMAGEM': 'Horas Enfermagem',
            'SIA_SIH_VALOR': 'Produção Total',
            'COMPETEN': 'Competência'
        }
        df_display = df_display.rename(columns=rename_map)

        # Format 'Competência' column as mm/yyyy string
        if 'Competência' in df_display.columns:
            df_display['Competência'] = df_display['Competência'].dt.strftime('%m/%Y')

        # Select and order columns before formatting numbers
        display_columns = [
            'CNES', 'Competência', 'Salas', 'Leitos SUS',
            'Horas Médicos', 'Horas Enfermagem', 'Produção Total', 'Eficiência'
        ]
        existing_display_columns = [col for col in display_columns if col in df_display.columns]
        df_display_final = df_display[existing_display_columns]

        # --- Apply Number Formatting directly to the DataFrame copy ---
        # Function to format numbers with pt-BR locale (manual swap)
        def format_pt_br(value, precision=0):
            if pd.isna(value):
                return '-' # Or None, or whatever you want for NaNs
            try:
                # Format with comma for thousands, period for decimal, then swap
                formatted = f'{value:,.{precision}f}'
                formatted_swapped = formatted.replace(',', '#').replace('.', ',').replace('#', '.')
                return formatted_swapped
            except (TypeError, ValueError):
                return value # Return original if not a number

        # Columns to format with 0 decimals
        cols_zero_decimals = ['Salas', 'Leitos SUS', 'Horas Médicos', 'Horas Enfermagem']
        for col in cols_zero_decimals:
            if col in df_display_final.columns:
                df_display_final[col] = df_display_final[col].apply(lambda x: format_pt_br(x, 0))

        # Format 'Produção Total' with 2 decimals
        if 'Produção Total' in df_display_final.columns:
            df_display_final['Produção Total'] = df_display_final['Produção Total'].apply(lambda x: format_pt_br(x, 2))

        # Format 'Eficiência' with 4 decimals (no thousands separator needed here, but use the func for consistency)
        if 'Eficiência' in df_display_final.columns:
             # Using precision 4 and letting the function handle separators if numbers were large
             df_display_final['Eficiência'] = df_display_final['Eficiência'].apply(lambda x: format_pt_br(x, 4))

        # Display the DataFrame with formatted strings, hiding the index
        st.dataframe(df_display_final, hide_index=True)

elif df is None:
    # Error messages are handled within load_data
    pass
else: # df is not None but empty
    st.warning("O arquivo Excel está vazio.") 