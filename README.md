# Análise de Eficiência Hospitalar com Streamlit

Este é um aplicativo Streamlit interativo para visualizar e analisar dados de eficiência hospitalar, utilizando dados de CNES (Cadastro Nacional de Estabelecimentos de Saúde).

## Funcionalidades

*   **Página Inicial:** Apresenta uma visão geral do aplicativo e instruções de uso.
*   **Análise CNES Individual:**
    *   Permite selecionar um CNES específico para análise detalhada.
    *   Exibe indicadores chave de desempenho (KPIs) para o hospital selecionado.
    *   Mostra gráficos da evolução da eficiência ao longo do tempo.
    *   Utiliza a API Google Gemini para gerar automaticamente uma análise textual da evolução da eficiência.
*   **Resultados Consolidados:**
    *   Apresenta métricas agregadas de eficiência para todos os hospitais.
    *   Visualiza a distribuição da eficiência entre os diferentes hospitais.

## Pré-requisitos

*   Python 3.8 ou superior
*   pip (gerenciador de pacotes Python)
*   Git (para clonar o repositório)

## Instalação

1.  **Clone o repositório:**
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd <NOME_DO_DIRETORIO_DO_PROJETO>
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuração

Este aplicativo utiliza a API Google Gemini para gerar análises textuais. Você precisará de uma chave de API do Google.

1.  **Obtenha sua chave de API:** Siga as instruções em [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  **Configure os segredos no Streamlit:**
    *   Se for executar localmente, crie um arquivo `.streamlit/secrets.toml` na raiz do projeto com o seguinte conteúdo:
        ```toml
        [api_keys]
        GOOGLE_API_KEY = "SUA_CHAVE_API_AQUI"
        ```
    *   **Importante:** Adicione `.streamlit/secrets.toml` ao seu arquivo `.gitignore` para não enviar sua chave para o repositório.
    *   Se for implantar no Streamlit Community Cloud, adicione a chave `GOOGLE_API_KEY` nas configurações de segredos do aplicativo no painel do Streamlit.

## Uso

1.  **Prepare os Dados:** Certifique-se de que o arquivo `resultado_eficiencia.xlsx` (gerado pelo script de pré-processamento) esteja presente no diretório raiz do projeto.
2.  **Execute o aplicativo Streamlit:**
    ```bash
    streamlit run Página_Inicial.py # Ou o nome do seu arquivo principal
    ```
3.  Abra seu navegador e acesse o endereço fornecido (geralmente `http://localhost:8501`).

## Estrutura do Projeto

```
.
├── .streamlit/
│   └── secrets.toml  # Configurações de API (NÃO ENVIAR PARA O GIT)
├── pages/
│   ├── 1_Analise_CNES_Individual.py # Código da página de análise individual
│   └── 2_Resultados_Consolidados.py # Código da página de resultados consolidados
├── Página_Inicial.py        # Script principal da aplicação (ou app.py)
├── requirements.txt         # Dependências Python
├── resultado_eficiencia.xlsx # Arquivo de dados de entrada
└── README.md                # Este arquivo
```

## Implantação

Este aplicativo pode ser implantado no [Streamlit Community Cloud](https://streamlit.io/cloud). Certifique-se de que seu repositório esteja no GitHub e configure os segredos (API Key) diretamente no painel do Streamlit Cloud. 