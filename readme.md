# 🌽 Projeto TCC - Pamonha Express

Este projeto é um sistema de chatbot para atendimento ao cliente de uma empresa fictícia ("Pamonharia Express"), desenvolvido como um Trabalho de Conclusão de Curso (TCC). A aplicação web permite que usuários interajam com o sistema para tirar dúvidas, fazer pedidos e avaliar o atendimento, simulando uma experiência de delivery real.

O principal diferencial do projeto é a implementação de um sistema de **atendimento híbrido**: ao iniciar uma conversa, o usuário é aleatoriamente direcionado para um de dois tipos de chatbot, permitindo uma análise comparativa de desempenho e experiência do usuário:

1.  **🤖 Chatbot Convencional:** Um sistema baseado em menus e regras, onde o usuário navega por opções pré-definidas.
2.  **🧠 Chatbot com IA:** Um sistema que utiliza a IA do Google (Gemini) para conduzir uma conversa mais fluida, natural e inteligente.

A interface do chat foi construída para ser moderna e responsiva, incluindo funcionalidades como temas claro/escuro e sincronização de histórico entre abas. O projeto também conta com um painel de visualização para análise posterior dos logs de conversas e das respostas dos questionários de satisfação.

---

## 🚀 Funcionalidades Principais

* **Interface de Chat Web:** Um front-end completo e responsivo, construído com HTML, CSS e JavaScript, que simula a interface do WhatsApp.
* **Atendimento Híbrido:** Seleção aleatória entre um chatbot baseado em regras e um com IA Generativa (Gemini) para cada nova sessão de usuário.
* **Fluxo de Pedidos:** O chatbot guia o usuário através de um fluxo completo para fazer, visualizar e modificar um pedido.
* **Persistência de Sessão:** A conversa, o histórico e as preferências de tema são mantidas no `localStorage` do navegador.
* **Troca Dinâmica de Modelos de IA:** O backend alterna entre modelos da API Gemini para otimizar o uso de cotas.
* **Visualizador de Logs:** Uma página (`logs.html`) que exibe os históricos de conversas e as respostas dos questionários.
* **Salvamento Automatizado de Logs:** O backend salva automaticamente as conversas e questionários em arquivos de texto.

---

## 🛠️ Tecnologias Utilizadas

### **Front-End**
* **HTML5**
* **CSS3** (com Flexbox e Media Queries)
* **JavaScript (ES6+)** (com API `Fetch` e `localStorage`)

### **Back-End**
* **Python 3**
* **Flask:** Micro-framework web para a API.
* **Flask-CORS:** Extensão para lidar com políticas de Cross-Origin.
* **Google Generative AI (Gemini):** API para o atendimento inteligente (modelos `gemini-1.5-flash-latest` e `gemini-2.0-flash-lite`).

### **Ferramentas e Outros**
* **ngrok:** Túnel seguro para expor o servidor local.
* **Waitress:** Servidor WSGI para produção.
* **JSON:** Formato de dados para comunicação e arquivos de índice.

---

## 📦 Estrutura do Projeto

```plaintext
tcc-chatbot/
├── 📂 Back-end/
│   ├── .env
│   ├── requirements.txt
│   ├── run.py
│   ├── app/
│   └── logs/
│
├── 📂 Front-end/
│   ├── index.html
│   ├── logs.html
│   ├── js/
│   └── style/
│
└── 📂 Analise_de_dados/
    ├── analise_consolidada.xlsx
    ├── analise_dados.py
    └── gerar_relatorio.py
    ├── relatorio_final.txt
    └── requirements.txt
````

## 🖥️ Back-End

O Back-End é responsável por toda a lógica do servidor, integração com APIs, registro de logs e armazenamento dos dados.

* **`run.py`**: Script principal para iniciar o servidor Flask.
* **`app/views.py`**: Define as rotas da API, principalmente o endpoint `/chat`.
* **`app/utils/whatsapp_utils.py`**: Contém a lógica dos chatbots, integração com Gemini e manipulação de logs.
* **`logs/`**: Diretório onde os logs e questionários são salvos.

---

## 🌐 Front-End

O Front-End é o site interativo que simula o atendimento via chat.

* **`index.html`**: Página principal do chat.
* **`logs.html`**: Visualizador de logs de conversas e questionários.
* **`js/script.js`**: Lógica do chat, envio e renderização de mensagens.
* **`js/logs.js`**: Lógica para carregar e exibir os logs.
* **`style/style.css`**: Estilos visuais da aplicação.

---

## 📊 Análise de Dados

Scripts para análise dos dados coletados durante o experimento.

* **`analise_dados.py`**: Lê os logs, extrai métricas e gera a planilha `analise_consolidada.xlsx`.
* **`gerar_relatorio.py`**: Cria um relatório de texto (`relatorio_final.txt`) com estatísticas a partir da planilha.

---

## ⚙️ Como Rodar o Projeto

### **1. Pré-requisitos**
* Python 3.10+
* Conta Google for Developers com acesso à API Gemini
* [Ngrok](https://ngrok.com/) instalado

### **2. Configuração do Back-End**
1.  **Instale as dependências:**
    ```sh
    cd tcc-chatbot/Back-end
    pip install -r requirements.txt
    ```
2.  **Crie o arquivo `.env`** com sua chave da API do Google:
    ```
    GOOGLE_API_KEY=SUA_CHAVE_API_GEMINI
    ```
3.  **Inicie o servidor:**
    ```sh
    python run.py
    ```
4.  **Exponha o servidor com Ngrok** e copie a URL gerada:
    ```sh
    ngrok http 5000
    ```

### **3. Configuração do Front-End**
1.  No arquivo `Front-end/js/script.js`, atualize a variável `BACKEND_URL` com o seu link do Ngrok:
    ```js
    const BACKEND_URL = 'https://SUA-URL-DO-NGROK.ngrok.app/chat';
    ```
2.  Abra o arquivo `Front-end/index.html` em seu navegador.

### **4. Análise de Dados**
1.  **Instale as dependências:**
    ```sh
    cd tcc-chatbot/Analise_de_dados
    pip install -r requirements.txt
    ```
2.  **Execute os scripts** para gerar a planilha e o relatório:
    ```sh
    python analise_dados.py
    python gerar_relatorio.py
    ```

---

## ⚠️ Observações Importantes

* Este projeto foi desenvolvido para fins acadêmicos. Não utilize em um ambiente de produção sem realizar as devidas adaptações de segurança.
