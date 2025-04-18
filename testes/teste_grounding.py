import os
import google.generativeai as genai
import tenacity
import streamlit as st
import json
from google.api_core.exceptions import (
    TooManyRequests,
    ResourceExhausted,
    Aborted,
    DeadlineExceeded,
    ServiceUnavailable,
    InternalServerError
)

from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

# --- Configuração Inicial ---

def get_api_key(config_file="../config.json"):
    """Tries to get the Gemini API key first from Streamlit secrets, then from a JSON config file."""
    try:
        # Try getting from Streamlit secrets first
        api_key = st.secrets["GEMINI_API_KEY"]
        if api_key: # Check if the key is not empty
            return api_key
    except (AttributeError, KeyError):
        # st.secrets not available or key not found in secrets
        pass # Proceed to try the config file

    try:
        # Fallback to reading from config file
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config['API_KEYS']['gemini_api_key']
    except (FileNotFoundError, KeyError, TypeError):
        # Config file not found, key not in config, or config structure is wrong
        return None

# 1. Obtenha sua API Key:
#    - Acesse https://aistudio.google.com/app/apikey para criar uma.
#    - É altamente recomendável usar variáveis de ambiente ou um gerenciador de segredos
#      em vez de colocar a chave diretamente no código.
# Exemplo usando variável de ambiente:
# os.environ['GOOGLE_API_KEY'] = 'SUA_API_KEY_AQUI'

# NOTE: You need to define the get_api_key() function elsewhere in your project
# Example definition (replace with your actual implementation):
# def get_api_key():
#     try:
#         # Attempt to get from Streamlit secrets
#         return st.secrets["GEMINI_API_KEY"]
#     except KeyError:
#         # Attempt to get from environment variable
#         return os.environ.get("GOOGLE_API_KEY")
#     except Exception:
#         # Handle other potential errors (e.g., config file)
#         return None

api_key=get_api_key() # Replace previous try/except block
genai.configure(api_key=api_key)
if api_key is None:
    raise ValueError("GEMINI_API_KEY not found. Check your configuration (e.g., secrets, env vars, config file).")

# --- Definindo a Ferramenta de Grounding (Google Search) ---

# O grounding é habilitado passando a ferramenta GoogleSearchRetrieval na lista de 'tools'.
# A forma mais simples e atual de habilitar a busca padrão é com um dicionário vazio.
# grounding_tool = Tool(google_search_retrieval={}) # Keep commented or remove

# --- Configurando o Modelo Gemini ---

generation_config = {"temperature": 0.7} # Add generation config

# Use o identificador do modelo desejado.
# 'gemini-1.5-pro-latest' é geralmente recomendado para ter acesso aos recursos mais recentes.
# Embora você tenha mencionado "2.5 Pro", o identificador público e estável
# mais recente que suporta grounding via API é geralmente 'gemini-1.5-pro-latest'.
# A nomenclatura exata pode mudar conforme novos modelos são lançados ou entram em preview.
# Verifique a documentação oficial para os identificadores mais recentes.
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    # Passa a ferramenta de grounding para o modelo diretamente como um dicionário
    tools=[{"google_search_retrieval": {}}],
    generation_config=generation_config # Add generation_config here
)

# --- Gerando Conteúdo com Grounding ---

# Seu prompt para o modelo
prompt = "Quais são as últimas novidades sobre a exploração espacial da NASA em Marte?"

print(f"Enviando prompt: {prompt}\n")

# Faz a chamada para a API. O modelo usará o Google Search (se julgar necessário)
# para basear e verificar sua resposta.
try:
    response = model.generate_content(prompt)

    # --- Exibindo a Resposta e Metadados de Grounding ---

    print("--- Resposta do Modelo ---")
    print(response.text)
    print("-" * 25)

    # Verifica se existem metadados de grounding (citações)
    if hasattr(response, 'grounding_metadata') and response.grounding_metadata:
        print("\n--- Citações (Grounding Metadata) ---")
        if hasattr(response.grounding_metadata, 'web_search_queries') and response.grounding_metadata.web_search_queries:
            print("Consultas de busca realizadas:")
            for query in response.grounding_metadata.web_search_queries:
                print(f"- {query}")

        if hasattr(response.grounding_metadata, 'grounding_attributions') and response.grounding_metadata.grounding_attributions:
            print("\nFontes usadas para grounding:")
            for attribution in response.grounding_metadata.grounding_attributions:
                 # O objeto attribution pode ter .url, .title, .publication_date etc.
                 # A estrutura exata pode variar, consulte a documentação ou explore o objeto.
                 print(f"- Segmento: \"{attribution.segment}\"") # Trecho da resposta associado
                 if hasattr(attribution.web, 'title') and attribution.web.title:
                     print(f"  Título: {attribution.web.title}")
                 if hasattr(attribution.web, 'uri') and attribution.web.uri:
                     print(f"  URL: {attribution.web.uri}")
                 # print(f"  Confiança: {attribution.confidence_score}") # Pode existir em algumas versões/modelos
                 print("-" * 10)
        else:
             print("Nenhuma atribuição de grounding específica encontrada na resposta.")

    else:
        print("\nNenhum metadado de grounding retornado para esta resposta.")
        print("(O modelo pode não ter precisado usar busca externa ou o grounding não foi ativado)")

except Exception as e:
    print(f"\nOcorreu um erro ao chamar a API Gemini: {e}")


