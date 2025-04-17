import streamlit as st
import google.generativeai as genai
import os

st.set_page_config(page_title="Teste API Gemini", layout="centered")
st.title("🧪 Teste da API Google Gemini")

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

    # Escolhe o modelo
    # Lista modelos disponíveis (opcional):
    # for m in genai.list_models():
    #   if 'generateContent' in m.supported_generation_methods:
    #     print(m.name)
    model = genai.GenerativeModel('gemini-1.5-flash') # Ou 'gemini-pro'

    st.success("API Key configurada com sucesso!")

    prompt = st.text_area("Digite seu prompt para o Gemini:", "Qual a capital do Brasil?")

    if st.button("Enviar para Gemini"):
        if prompt:
            try:
                with st.spinner("Aguardando resposta do Gemini..."):
                    response = model.generate_content(prompt)
                st.subheader("Resposta do Gemini:")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Erro ao chamar a API Gemini: {e}")
                # Tenta fornecer mais detalhes se for um erro de API Key inválida
                if "API key not valid" in str(e):
                    st.warning("Verifique se a API Key em .streamlit/secrets.toml está correta e se a API Generative AI está habilitada no seu projeto Google Cloud.")
        else:
            st.warning("Por favor, digite um prompt.")

except Exception as e:
    st.error(f"Ocorreu um erro inesperado ao configurar a API: {e}")
    st.stop()

st.markdown("---")
st.caption("Script simples para testar a conectividade com a API Gemini.") 