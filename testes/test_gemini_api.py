import streamlit as st
import google.generativeai as genai
# Remover importação de Tool
# from google.generativeai.types import Tool # Removido
# Importar GenerationConfig
from google.generativeai.types import GenerationConfig
# Remover GenerateContentConfig e GoogleSearch
import os

st.set_page_config(page_title="Consulta Hospital", layout="centered")
st.title("🏥 Consulta Informações do Hospital")

# Tenta carregar a chave da API dos segredos do Streamlit
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Chave da API Gemini não encontrada! Por favor, configure-a em .streamlit/secrets.toml")
    st.code("""
# .streamlit/secrets.toml
GEMINI_API_KEY="SUA_CHAVE_DE_API_AQUI"
""", language="toml")
    st.stop()

try:
    # Configura a API
    genai.configure(api_key=api_key)

    # Usa a interface GenerativeModel
    model_name = 'gemini-2.5-pro-exp-03-25' # Modelo base sem grounding explícito
    model = genai.GenerativeModel(model_name)
    # Exibe o nome do modelo na interface
    st.caption(f"Modelo em uso: {model_name}")

    # Remove a definição da ferramenta de busca
    # search_tool = Tool(google_search_retrieval={}) # Removido

    st.success("API Key configurada e modelo pronto para consulta.") # Mensagem atualizada

    # Altera o input para pedir o NOME do hospital
    hospital_name_input = st.text_input("Digite o nome do hospital:", placeholder="Ex: Hospital Sírio-Libanês")

    # Altera o botão e a lógica
    if st.button("Consultar Informações"):
        if hospital_name_input:
            # Validação ajustada para NOME (não pode ser só números)
            if hospital_name_input.isdigit():
                st.warning("Por favor, digite um nome de hospital válido (não apenas números).")
            else:
                # Cria o prompt específico para a tarefa (sem menção à busca)
                prompt = f"""
    Com base no nome do hospital a seguir: {hospital_name_input}

    Usando seu conhecimento interno, realize as seguintes tarefas:
    1.  Identifique o nome completo do estabelecimento de saúde (hospital, clínica, etc.) associado a este nome.
    2.  Identifique o nome do município e o estado onde este estabelecimento está localizado.
    3.  Forneça um breve resumo sobre o município identificado (ex: população estimada, principal atividade econômica, localização geral, indicadores de saúde, indicadores sociais).
    4.  Busque em seus dados por informações sobre a qualidade dos serviços ou atendimento do estabelecimento de saúde identificado.
    5.  Forneça um resumo da rede pública de saúde do município identificado (ex: quantidade de unidades de saúde para cada tipo de unidade).
    6.  Se houver outros hospiais na região, identificar se são gerais ou especializados.

    Apresente a resposta de forma clara e organizada, separando cada um dos 5 itens solicitados. Se alguma informação não estiver disponível em seus dados, indique isso explicitamente.
    """
                try:
                    # Define a configuração de geração com baixa temperatura
                    generation_config = GenerationConfig(
                        temperature=0.2
                    )

                    # Remove menção à busca no spinner
                    with st.spinner("Consultando o Gemini (GenerativeModel API)..."):
                        # Chama a API usando GenerativeModel SEM a ferramenta de busca e com config
                        response = model.generate_content(
                            prompt,
                            generation_config=generation_config # Adiciona config
                            # tools=[search_tool] # Removido
                        )
                    st.subheader("Resultado da Consulta:")

                    # Extrai o texto da resposta (estrutura simples)
                    st.markdown(response.text)

                    # Remove toda a seção de metadados de grounding
                    # try:
                    #    # Verifica a existência de grounding_metadata diretamente no objeto response
                    #    if hasattr(response, 'grounding_metadata') and response.grounding_metadata:
                    #        st.subheader("Fontes Consultadas (Metadados de Grounding):")
                    #        metadata = response.grounding_metadata
                    #        ... (código removido) ...
                    #    # else:
                    #    #     st.caption("Nenhum metadado de grounding retornado.")
                    # except AttributeError:
                    #     st.caption("Não foi possível acessar os metadados de grounding (atributo não encontrado na resposta).")
                    # except Exception as meta_e:
                    #      st.warning(f"Erro ao processar metadados de grounding: {meta_e}")

                except Exception as e:
                    st.error(f"Erro ao chamar a API Gemini: {e}")
                    # Tratamento de erros específicos...
                    if "API key not valid" in str(e):
                        st.warning("Verifique se a API Key em .streamlit/secrets.toml está correta e se a API Generative AI está habilitada no seu projeto Google Cloud.")
                    # Remove erro específico da busca
                    # elif "GoogleSearchRetrieval" in str(e) or "grounding is not supported" in str(e):
                    #      st.warning("Ocorreu um erro relacionado à ferramenta de busca. Verifique se o modelo suporta grounding ou se há restrições na API Key.") # Removido
                    elif "exceeded your current quota" in str(e) or "429" in str(e):
                         st.warning("Você atingiu o limite de requisições da API (quota). Tente novamente mais tarde.")
                    else:
                        st.warning(f"Erro inesperado: {e}")
        else:
            st.warning("Por favor, digite o nome do hospital.")

except Exception as e:
    st.error(f"Ocorreu um erro inesperado ao configurar a API: {e}")
    st.stop()

st.markdown("---")
# Atualiza caption final
st.caption("Aplicação para consultar informações de estabelecimentos de saúde usando nome e a API Gemini.")

# Remover a seção de código relacionada ao CNES 