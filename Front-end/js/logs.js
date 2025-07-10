document.addEventListener('DOMContentLoaded', () => {

    const mainContainer = document.querySelector('.main-container');
    if (!mainContainer) { return; }

    // --- ELEMENTOS DO DOM ---
    const logSelector = document.getElementById('log-selector');
    const viewButtons = document.querySelectorAll('.view-button');
    const searchBox = document.getElementById('search-box');
    const listTitle = document.getElementById('list-title');
    const chatViewer = document.getElementById('chat-viewer');
    const chatMessages = document.getElementById('chat-messages');
    const summaryInfo = document.getElementById('chat-summary-info');
    const tipoAtendimentoEl = document.getElementById('atendimento-tipo');
    const tempoInteracaoEl = document.getElementById('atendimento-tempo');

    // --- ESTADO DA APLICAÇÃO ---
    let allLogs = []; // Array único para guardar todos os logs carregados
    let currentView = 'conversas';

    // --- FUNÇÕES DE RENDERIZAÇÃO ---

    function formatTextToHTML(text) {
        if (typeof text !== 'string') return '';
        return text.replace(/\n/g, '<br>').replace(/\*(.*?)\*/g, '<strong>$1</strong>').replace(/\_(.*?)\_/g, '<em>$1</em>');
    }

    function displayMessage(messageData) {
        const { text, type, time = '' } = messageData;
        if (!text || typeof text !== 'string' || text.trim() === '') return;
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', type);
        const contentP = document.createElement('p');
        contentP.innerHTML = formatTextToHTML(text);
        messageDiv.appendChild(contentP);
        if (time) {
            const metaDiv = document.createElement('div');
            metaDiv.classList.add('message-meta');
            const timeSpan = document.createElement('span');
            timeSpan.textContent = time;
            metaDiv.appendChild(timeSpan);
            messageDiv.appendChild(metaDiv);
        }
        chatMessages.appendChild(messageDiv);
    }
        
    function parseLogContent(logContent, logType) {
        const lines = logContent.split('\n');
        const summary = { tipoAtendimento: 'Não informado', tempoInteracao: 'N/D' };
        const messages = [];

        if (logType === 'conversas') {
            let startTime = null, endTime = null, currentMessageObject = null;
            const tipoRegex = /^Tipo de Atendimento:\s(.*)/;
            const inicioRegex = /---\sInício da interação:\s(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\s---/;
            const fimRegex = /---\sFim da interação:\s(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\s---/;
            const messageRegex = /\[(?:\d{4}-\d{2}-\d{2}\s)?(\d{2}:\d{2}:\d{2})\]\s(Usuário|Bot):\s(.*)/;

            for (const line of lines) {
                let match;
                if ((match = line.match(tipoRegex))) { summary.tipoAtendimento = match[1];
                } else if ((match = line.match(inicioRegex))) { startTime = new Date(match[1].replace(' ', 'T'));
                } else if ((match = line.match(fimRegex))) { endTime = new Date(match[1].replace(' ', 'T'));
                } else if ((match = line.match(messageRegex))) {
                    if (currentMessageObject) { messages.push(currentMessageObject); }
                    currentMessageObject = { time: match[1], text: match[3], type: (match[2] === 'Usuário' ? 'received' : 'sent') };
                } else if (currentMessageObject && line.trim() !== '') { currentMessageObject.text += '\n' + line; }
            }
            if (currentMessageObject) { messages.push(currentMessageObject); }
            if (startTime && endTime) {
                const diffSeconds = Math.round((endTime - startTime) / 1000);
                summary.tempoInteracao = `${Math.floor(diffSeconds / 60)} min e ${diffSeconds % 60} seg`;
            }
        } else { 
            let ultimaPergunta = '';
            const tipoRegex = /^Tipo de Atendimento:\s(.*)/;
            const perguntaRegex = /^(Pergunta \d.*)/;
            const respostaRegex = /^Resposta:\s(.*)/;
            for (const line of lines) {
                let match;
                if ((match = line.match(tipoRegex))) { summary.tipoAtendimento = match[1];
                } else if ((match = line.match(perguntaRegex))) { ultimaPergunta = match[1];
                } else if ((match = line.match(respostaRegex))) {
                    if (ultimaPergunta) {
                        messages.push({ text: `<strong>${ultimaPergunta}</strong>`, type: 'received' });
                        messages.push({ text: match[1], type: 'sent' });
                        ultimaPergunta = '';
                    }
                }
            }
            summary.tempoInteracao = 'N/A';
        }
        return { summary, messages };
    }

    // --- LÓGICA PRINCIPAL ---

    function filterAndDisplayList() {
        const searchTerm = searchBox.value.toLowerCase();
        const filteredLogs = allLogs.filter(log => {
            if (log.type !== currentView) return false;
            if (searchTerm === '') return true;
            const filenameMatch = log.filename.toLowerCase().includes(searchTerm);
            const contentMatch = log.rawContent.toLowerCase().includes(searchTerm);
            return filenameMatch || contentMatch;
        });

        logSelector.innerHTML = '';
        if (filteredLogs.length === 0) {
            logSelector.innerHTML = `<option>Nenhum resultado encontrado.</option>`;
        } else {
            filteredLogs.forEach(log => {
                const option = document.createElement('option');
                option.value = log.filename;
                option.textContent = log.filename;
                logSelector.appendChild(option);
            });
        }
        displaySelectedFile();
    }

    async function loadAllData() {
        currentView = document.querySelector('.view-button.active').dataset.view;
        listTitle.textContent = currentView === 'conversas' ? 'Conversas Salvas' : 'Questionários Salvos';
        const listUrl = currentView === 'conversas' ? '../Back-end/logs/log-list.json' : '../Back-end/logs/questionario-list.json';
        const baseUrl = currentView === 'conversas' ? '../Back-end/logs/conversations/' : '../Back-end/logs/questionarios/';

        logSelector.innerHTML = '<option>Carregando e analisando todos os logs...</option>';
        displaySelectedFile();
        
        try {
            const listResponse = await fetch(listUrl);
            if (!listResponse.ok) throw new Error('Arquivo de índice não encontrado');
            const filenames = await listResponse.json();

            if (filenames.length === 0) {
                allLogs = allLogs.filter(log => log.type !== currentView); // Limpa os dados do tipo atual
                filterAndDisplayList();
                return;
            }

            const fetchPromises = filenames.map(file => 
                fetch(baseUrl + file)
                    .then(res => res.ok ? res.text() : "Erro ao carregar conteúdo")
                    .then(content => {
                        const parsedData = parseLogContent(content, currentView);
                        return { 
                            filename: file, 
                            rawContent: content, // Guarda o texto bruto para a pesquisa
                            type: currentView,
                            ...parsedData // Adiciona .summary e .messages
                        };
                    })
            );

            const results = await Promise.all(fetchPromises);
            // Remove os logs antigos do tipo atual e adiciona os novos
            allLogs = allLogs.filter(log => log.type !== currentView).concat(results);
            filterAndDisplayList();

        } catch (error) {
            console.error(`Erro ao carregar dados:`, error);
            logSelector.innerHTML = `<option>Erro ao carregar.</option>`;
        }
    }

    function displaySelectedFile() {
        const selectedFile = logSelector.value;
        summaryInfo.classList.toggle('hidden', currentView !== 'conversas');
        chatMessages.innerHTML = ''; // Limpa a tela
        
        if (!selectedFile || logSelector.options.length === 0 || logSelector.options[0].textContent.includes('Nenhum')) {
            chatMessages.innerHTML = `<div class="message received"><p>Selecione ou pesquise por um item na lista.</p></div>`;
            return;
        }
        
        const logData = allLogs.find(log => log.filename === selectedFile);

        if (logData) {
            if (currentView === 'conversas') {
                tipoAtendimentoEl.textContent = logData.summary.tipoAtendimento;
                tempoInteracaoEl.textContent = logData.summary.tempoInteracao;
            }
            logData.messages.forEach(msg => displayMessage(msg));
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // --- EVENT LISTENERS E INICIALIZAÇÃO ---
    viewButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            if (e.target.classList.contains('active')) return;
            viewButtons.forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            // Recarrega os dados apenas se eles ainda não foram carregados
            const currentData = allLogs.filter(log => log.type === e.target.dataset.view);
            if(currentData.length === 0) {
                loadAllData();
            } else {
                currentView = e.target.dataset.view;
                listTitle.textContent = currentView === 'conversas' ? 'Conversas Salvas' : 'Questionários Salvos';
                filterAndDisplayList();
            }
        });
    });

    searchBox.addEventListener('input', filterAndDisplayList);
    logSelector.addEventListener('change', displaySelectedFile);
    
    loadAllData(); // Carrega os dados iniciais
});