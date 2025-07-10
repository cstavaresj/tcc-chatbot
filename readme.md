# Projeto TCC - Pamonha Express

Este projeto é um sistema de chatbot para atendimento ao cliente de uma empresa fictícia ("Pamonharia Express"), desenvolvido como um Trabalho de Conclusão de Curso (TCC). A aplicação web permite que usuários interajam com o sistema para tirar dúvidas, fazer pedidos e avaliar o atendimento, simulando uma experiência de delivery real.

O principal diferencial do projeto é a implementação de um sistema de **atendimento híbrido**: ao iniciar uma conversa, o usuário é aleatoriamente direcionado para um de dois tipos de chatbot, permitindo uma análise comparativa de desempenho e experiência do usuário:
1.  **Chatbot Convencional:** Um sistema baseado em menus e regras, onde o usuário navega por opções pré-definidas.
2.  **Chatbot com IA:** Um sistema que utiliza a IA do Google (Gemini) para conduzir uma conversa mais fluida, natural e inteligente.

A interface do chat foi construída para ser moderna e responsiva, incluindo funcionalidades como temas claro/escuro e sincronização de histórico entre abas. O projeto também conta com um painel de visualização para análise posterior dos logs de conversas e das respostas dos questionários de satisfação.

## Funcionalidades Principais

* **Interface de Chat Web:** Um front-end completo e responsivo, construído com HTML, CSS e JavaScript, que simula a interface do WhatsApp.
* **Atendimento Híbrido:** Seleção aleatória entre um chatbot baseado em regras e um chatbot com IA Generativa (Gemini) para cada nova sessão de usuário.
* **Fluxo de Pedidos:** O chatbot convencional guia o usuário através de um fluxo completo para fazer, visualizar e modificar um pedido.
* **Persistência de Sessão:** A conversa, o histórico e as preferências de tema do usuário são mantidas entre abas e atualizações de página usando o `localStorage` do navegador.
* **Troca Dinâmica de Modelos de IA:** O backend possui uma lógica para alternar entre diferentes modelos da API Gemini com base na contagem de requisições, otimizando o uso de cotas.
* **Visualizador de Logs:** Uma página dedicada (`logs.html`) que permite visualizar os históricos de conversas e as respostas dos questionários que foram salvos em arquivos `.txt`.
* **Salvamento Automatizado de Logs:** O backend salva automaticamente o histórico completo das conversas e as respostas dos questionários em arquivos de texto, atualizando um índice `JSON` para o visualizador.

## Tecnologias Utilizadas

### Front-End
* **HTML5**
* **CSS3** (com Flexbox para layout e Media Queries para responsividade)
* **JavaScript (ES6+)** (com API `Fetch` para comunicação e `localStorage` para persistência)

### Back-End
* **Python 3**
* **Flask:** Micro-framework web para criar a API que recebe as mensagens do front-end.
* **Flask-CORS:** Extensão para lidar com as políticas de Cross-Origin Resource Sharing.
* **Google Generative AI (Gemini):** API utilizada para o fluxo de atendimento inteligente. Os modelos utilizados incluem `gemini-1.5-flash-latest` e `gemini-2.0-flash-lite`.

### Ferramentas e Outros
* **ngrok:** Utilizado para criar um túnel seguro e expor o servidor Flask local na internet, permitindo a comunicação com o front-end hospedado.
* **Waitress:** Servidor WSGI utilizado para rodar a aplicação Flask em produção.
* **JSON:** Formato de dados utilizado para a comunicação entre front-end e back-end e para os arquivos de índice dos logs.


O projeto está dividido em três grandes partes: **Back-End**, **Front-End** e **Análise de Dados**.

---

## 📦 Estrutura do Projeto

````plaintext
tcc-chatbot/
├── Back-end/
│   ├── .env
│   ├── requirements.txt
│   ├── run.py
│   └── app/
│       ├── __init__.py
│       ├── config.py
│       ├── views.py
│       └── utils/
│           └── whatsapp_utils.py
│   └── logs/
│
├── Front-end/
│   ├── index.html
│   ├── logs.html
│   ├── politica-de-privacidade.html
│   ├── sobre.html
│   ├── termos-de-uso.html
│   ├── js/
│   │   ├── script.js
│   │   └── logs.js
│   └── style/
│       ├── style.css
│       └── logs.css
│
├── Analise_de_dados/
│   ├── .env
│   ├── analise_consolidada.xlsx
│   ├── analise_dados.py
│   ├── gerar_relatorio.py
│   ├── relatorio_final.txt
│   └── requirements.txt
````

## 🖥️ Back-End

O Back-End é responsável por toda a lógica do servidor, integração com APIs externas, registro de logs e armazenamento dos dados das conversas e questionários.

### Principais arquivos:

- **.env**  
  Armazena variáveis de ambiente sensíveis, como chaves de API.

- **requirements.txt**  
  Lista as dependências Python necessárias para rodar o servidor.

- **run.py**  
  Script principal para iniciar o servidor Flask.

- **app/__init__.py**  
  Inicializa a aplicação Flask e configura CORS.

- **app/config.py**  
  Carrega configurações e logging.

- **app/views.py**  
  Define as rotas da API, principalmente o endpoint `/chat` que recebe mensagens do Front-End.

- **app/utils/whatsapp_utils.py**  
  Contém toda a lógica de fluxo dos chatbots (convencional e com IA), integração com Gemini, manipulação de logs e questionários.

- **logs/**  
  Diretório onde são salvos os logs das conversas e respostas dos questionários.

---

## 🌐 Front-End

O Front-End é um site interativo que simula o atendimento via chat, permitindo ao usuário interagir com o chatbot, visualizar logs e responder ao questionário.

### Principais arquivos:

- **index.html**  
  Página principal do chat.

- **logs.html**  
  Visualizador de logs de conversas e questionários salvos.

- **politica-de-privacidade.html / termos-de-uso.html / sobre.html**  
  Páginas institucionais sobre o projeto.

- **js/script.js**  
  Lógica do chat, envio de mensagens para o Back-End, renderização de mensagens e botões.

- **js/logs.js**  
  Lógica para carregar e exibir logs de conversas e questionários.

- **style/style.css / style/logs.css**  
  Estilos visuais do chat e do visualizador de logs.

---

## 📊 Analise de Dados

Scripts e arquivos para análise dos dados coletados durante o experimento.

### Principais arquivos:

- **analise_dados.py**  
  Lê os logs das conversas e questionários, extrai métricas e gera uma planilha consolidada (`analise_consolidada.xlsx`).

- **gerar_relatorio.py**  
  Gera um relatório de texto (`relatorio_final.txt`) com estatísticas e análises a partir da planilha consolidada.

- **analise_consolidada.xlsx**  
  Planilha gerada automaticamente com os dados tratados.

- **relatorio_final.txt**  
  Relatório final gerado automaticamente para discussão dos resultados.

---

## ⚙️ Como Rodar o Projeto na Sua Máquina

### 1. Pré-requisitos

- Python 3.10+ instalado
- Conta Google for Developers com acesso à API Gemini
- [Ngrok](https://ngrok.com/) para expor o servidor local

### 2. Configuração do Back-End

1. **Instale as dependências:**
    ```sh
    cd tcc-chatbot//Back-end
    pip install -r requirements.txt
    ```

2. **Crie o arquivo `.env`** com suas chaves:
    ```
    GOOGLE_API_KEY=SEU_TOKEN_GEMINI
    OUTRAS_VARIAVEIS=...
    ```

3. **Adicione o arquivo de credenciais do Google** (ex: `credenciais_google.json`) em `Back-end/app/utils/` e configure a variável de ambiente `GOOGLE_APPLICATION_CREDENTIALS` no `.env`.

4. **Inicie o servidor:**
    ```sh
    python run.py
    ```

5. **Exponha o servidor com Ngrok:**
    ```sh
    ngrok http 5000
    ```
    Copie o endereço gerado (ex: `https://xxxxxx.ngrok.app`) e use no Front-End.

### 3. Configuração do Front-End

1. **Altere o domínio do Back-End** em [script.js](http://_vscodecontentref_/17):
    ```js
    const BACKEND_URL = 'https://SEU-DOMINIO-DO-NGROK.app/chat';
    ```
2. **Abra o arquivo [index.html](http://_vscodecontentref_/18)** no navegador ou hospede em um servidor web.

### 4. Análise de Dados

1. **Instale as dependências:**
    ```sh
    cd tcc-chatbot/Analise_de_dados
    pip install -r requirements.txt
    ```

2. **Execute os scripts de análise:**
    - Para gerar a planilha consolidada:
      ```sh
      python analise_dados.py
      ```
    - Para gerar o relatório final:
      ```sh
      python gerar_relatorio.py
      ```

---

## ⚠️ Observações Importantes

- O projeto foi desenvolvido para fins acadêmicos e não deve ser usado em produção sem adaptações de segurança.

---
